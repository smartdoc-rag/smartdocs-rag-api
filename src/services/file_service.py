import logging
import os
import uuid
from typing import List, Tuple
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.vectorstores import FAISS

from src.services.redis_service import RedisService
from src.repositories.chunk_repository import ChunkRepository
from src.models.chunk import Chunk
from src.models.files import File
from src.repositories.file_repository import FileRepository
from src.repositories.conversation_repository import ConversationRepository
from src.services.rag.file_ingestion_service import FileIngestionService
from src.services.rag.graph_ingestion_service import GraphIngestionService
from src.core.rag.embedding_provider import get_embedding
from src.core.exceptions import ForbiddenException
from urllib.parse import quote

MEDIA_ROOT = os.path.join(settings.BASE_DIR, "media", "files")
VECTOR_DB_ROOT = os.path.join(settings.BASE_DIR, "vector_db")
SUPPORTED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx"}


class FileService:
    def __init__(
        self,
        file_repo=FileRepository(),
        conversation_repo=ConversationRepository(),
        chunk_repo=ChunkRepository(),
        ingestion_service=FileIngestionService(),
        graph_ingestion_service: GraphIngestionService = None,
    ):
        self.file_repo = file_repo
        self.conversation_repo = conversation_repo
        self.chunk_repo = chunk_repo
        self.ingestion_service = ingestion_service
        self.graph_ingestion_service = graph_ingestion_service
        self.embedding = get_embedding()
        self.redis_service = RedisService()

    def _get_vector_store_path(self, conversation_id: int) -> str:
        return os.path.join(VECTOR_DB_ROOT, f"conv_{conversation_id}")

    def _load_vectorstore(self, conversation_id: int):
        path = self._get_vector_store_path(conversation_id)
        if os.path.exists(path):
            return FAISS.load_local(
                path, self.embedding, allow_dangerous_deserialization=True
            )
        return None

    def _save_vectorstore(self, vectorstore, conversation_id: int):
        path = self._get_vector_store_path(conversation_id)
        os.makedirs(path, exist_ok=True)
        vectorstore.save_local(path)

    def _extract_documents(
        self, file_path: str, file_type: str, chunk_size: int, chunk_overlap: int
    ) -> list:
        if file_type == "pdf":
            loader = PyPDFLoader(file_path)
        else:
            loader = Docx2txtLoader(file_path)
        docs = loader.load()
        if not docs:
            raise ValueError("Định dạng file không được hỗ trợ")
        return self.ingestion_service.text_splitter(
            docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    @transaction.atomic
    def upload_file(
        self,
        conversation_id: int,
        user_id: int,
        uploaded_file: UploadedFile,
        scope="private",
    ):
        # Kiểm tra quyền
        conversation = self.conversation_repo.get_user_conversation_by_id(
            user_id, conversation_id
        )
        if not conversation:
            raise ForbiddenException(
                "Cuộc hội thoại không tồn tại hoặc không có quyền truy cập"
            )

        existing_file = self.file_repo.get_one(
            conversation_id=conversation_id,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
        )

        if existing_file:
            # Bỏ qua, trả về file cũ (không tạo mới)
            return existing_file
        # Validate
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError("Định dạng này không được hỗ trợ")
        file_type = SUPPORTED_EXTENSIONS[ext]

        # Lưu file vật lý
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        saved_name = f"{uuid.uuid4()}_{uploaded_file.name}"
        saved_path = os.path.join(MEDIA_ROOT, saved_name)
        with open(saved_path, "wb+") as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        try:
            # Lấy chunk config từ conversation
            chunk_size = conversation.chunk_size
            chunk_overlap = conversation.chunk_overlap

            # Split documents với config chunk_size và chunk overlap
            split_docs = self._extract_documents(
                saved_path, file_type, chunk_size, chunk_overlap
            )

            # Tạo DB record
            file_obj = File(
                conversation=conversation,
                file_name=uploaded_file.name,
                file_path=saved_path,
                file_size=uploaded_file.size,
                file_type=file_type,
                scope=scope,
            )
            file_obj = self.file_repo.create(file_obj)

            # Gắn metadata
            for doc in split_docs:
                doc.metadata["file_id"] = str(file_obj.id)
                doc.metadata["file_name"] = file_obj.file_name
                doc.metadata["conversation_id"] = conversation_id

                chunk = Chunk(
                    conversation=conversation,
                    file=file_obj,
                    text=doc.page_content,
                    page_number=doc.metadata.get("page"),
                    start_index=doc.metadata.get("start_index"),
                    metadata=doc.metadata,
                )
                self.chunk_repo.create(chunk)

            # Ingest vào Neo4j graph nếu có service
            neo4j_result = {}
            if self.graph_ingestion_service:
                try:
                    neo4j_result = self.graph_ingestion_service.hybrid_ingest(
                        split_docs, vector_index_name=f"conv_{conversation_id}"
                    )
                    print(neo4j_result)
                except Exception as e:
                    neo4j_result = {"error": str(e)}
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to ingest to Neo4j: {e}")

            # Ingest vào vector store
            vectorstore = self._load_vectorstore(conversation_id)
            new_vs = FAISS.from_documents(split_docs, self.embedding)
            if vectorstore:
                vectorstore.merge_from(new_vs)
                self._save_vectorstore(vectorstore, conversation_id)
            else:
                self._save_vectorstore(new_vs, conversation_id)

            # Tự động thêm vào Redis selected files
            current_ids = self.redis_service.get_selected_files(conversation_id)
            if file_obj.id not in current_ids:
                current_ids.append(file_obj.id)
                self.redis_service.set_selected_files(conversation_id, current_ids)
            return file_obj
        except Exception:
            if os.path.exists(saved_path):
                os.remove(saved_path)
            raise

    def get_files(
        self, conversation_id: int, user_id: int, skip=0, limit=20
    ) -> Tuple[List[File], int]:
        return self.file_repo.get_by_conversation_and_user(
            conversation_id, user_id, skip, limit
        )

    def delete_file(self, file_id: int, user_id: int) -> bool:
        file_obj = self.file_repo.get_one(id=file_id)
        if not file_obj:
            return False
        conversation_id = file_obj.conversation_id

        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, conversation_id
        )
        if not conv:
            return False

        # 1. Xóa file vật lý
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)

        # 2. Xóa record (cascade sẽ tự xóa các Chunk trong DB)
        self.file_repo.delete(file_obj)

        # 3. Xóa các node Neo4j liên quan
        if self.graph_ingestion_service:
            try:
                self.graph_ingestion_service.delete_file_graph(conversation_id, file_id)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Failed to delete Neo4j nodes for file {file_id}: {e}"
                )

        # 4. Cập nhật Redis selected files (bỏ file_id)
        try:
            current_ids = self.redis_service.get_selected_files(conversation_id)
            if file_id in current_ids:
                current_ids.remove(file_id)
                self.redis_service.set_selected_files(conversation_id, current_ids)
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Failed to update Redis selected files: {e}"
            )

        # 5. Rebuild vector store để loại bỏ các chunk của file đã xóa
        self._rebuild_vectorstore(conversation_id)

        return True

    def clear_all_files(self, conversation_id: int, user_id: int) -> bool:
        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, conversation_id
        )
        if not conv:
            return False

        # 1. Xóa Neo4j graph nếu có service
        if self.graph_ingestion_service:
            try:
                self.graph_ingestion_service.delete_conversation_graph(conversation_id)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to delete Neo4j graph for conv {conversation_id}: {e}"
                )

        # 2. Xóa file vật lý + record DB (giữ nguyên logic cũ)
        files, _ = self.file_repo.get_by_conversation_and_user(
            conversation_id, user_id, limit=10000
        )
        for f in files:
            if os.path.exists(f.file_path):
                os.remove(f.file_path)
            self.file_repo.delete(f)

        # 3. Xóa vector store (FAISS)
        vs_path = self._get_vector_store_path(conversation_id)
        if os.path.exists(vs_path):
            import shutil
            shutil.rmtree(vs_path)

        # 4. Xóa Redis selected files
        try:
            self.redis_service.delete_selected_files(conversation_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to delete Redis key for conv {conversation_id}: {e}"
            )

        return True

    def _rebuild_vectorstore(self, conversation_id: int):
        """Xóa vector store cũ và tạo lại từ tất cả chunk còn lại trong DB."""
        from langchain_core.documents import Document
        from langchain_community.vectorstores import FAISS

        vs_path = self._get_vector_store_path(conversation_id)
        if os.path.exists(vs_path):
            import shutil
            shutil.rmtree(vs_path)

        chunks = Chunk.objects.filter(conversation_id=conversation_id)
        if not chunks:
            return

        documents = [
            Document(page_content=chunk.text, metadata=chunk.metadata)
            for chunk in chunks
        ]

        vectorstore = FAISS.from_documents(documents, self.embedding)
        self._save_vectorstore(vectorstore, conversation_id)



    def get_file_url_by_id(self, file_id: int, user_id: int, request):
        file_obj = self.file_repo.get_one(id=file_id)
        if not file_obj:
            return None

        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, file_obj.conversation_id
        )
        if not conv:
            raise ForbiddenException("Không có quyền truy cập file")

        filename = os.path.basename(file_obj.file_path)

        return {
            "id": file_obj.id,
            "file_name": file_obj.file_name,
            "url": f"{request.scheme}://{request.get_host()}/media/files/{quote(filename)}",
            "file_type": file_obj.file_type,
            "file_size": file_obj.file_size,
        }