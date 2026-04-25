import os
import uuid
import logging
import threading
from typing import List, Tuple, Optional
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.vectorstores import FAISS

from src.services.redis_service import RedisService
from src.services.thread_pool_service import ThreadPoolService, get_thread_pool
from src.repositories.chunk_repository import ChunkRepository
from src.models.chunk import Chunk
from src.models.files import File
from src.repositories.file_repository import FileRepository
from src.repositories.conversation_repository import ConversationRepository
from src.services.rag.file_ingestion_service import FileIngestionService
from src.services.rag.graph_ingestion_service import GraphIngestionService
from src.core.rag.embedding_provider import get_embedding
from src.core.exceptions import ForbiddenException

logger = logging.getLogger(__name__)

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
        thread_pool_service: Optional[ThreadPoolService] = None,
    ):
        self.file_repo = file_repo
        self.conversation_repo = conversation_repo
        self.chunk_repo = chunk_repo
        self.ingestion_service = ingestion_service
        self.graph_ingestion_service = graph_ingestion_service
        self.thread_pool = thread_pool_service or get_thread_pool()
        self.embedding = get_embedding()
        self.redis_service = RedisService()

    # Lock per conversation để tránh race condition khi nhiều file upload song song
    _faiss_locks: dict = {}
    _faiss_locks_lock = threading.Lock()

    @classmethod
    def _get_faiss_lock(cls, conversation_id: int) -> threading.Lock:
        with cls._faiss_locks_lock:
            if conversation_id not in cls._faiss_locks:
                cls._faiss_locks[conversation_id] = threading.Lock()
            return cls._faiss_locks[conversation_id]

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

            # Chạy song song: (1) Neo4j graph ingestion và (2) FAISS vector store ingestion
            ingestion_tasks = []

            # Task 1: Neo4j hybrid ingestion
            if self.graph_ingestion_service:

                def _neo4j_task(docs=split_docs, cid=conversation_id):
                    return self.graph_ingestion_service.hybrid_ingest(
                        docs, vector_index_name=f"conv_{cid}"
                    )

                ingestion_tasks.append(_neo4j_task)

            # Task 2: FAISS vector store ingestion
            def _faiss_task(docs=split_docs, cid=conversation_id):
                # Lọc documents rỗng — một số PDF không trích xuất được text
                valid_docs = [d for d in docs if (d.page_content or "").strip()]
                if not valid_docs:
                    return True

                # FAISS load-merge-save không thread-safe — dùng lock per conversation
                with self._get_faiss_lock(cid):
                    new_vs = FAISS.from_documents(valid_docs, self.embedding)
                    vectorstore = self._load_vectorstore(cid)
                    if vectorstore:
                        vectorstore.merge_from(new_vs)
                        self._save_vectorstore(vectorstore, cid)
                    else:
                        self._save_vectorstore(new_vs, cid)
                return True

            ingestion_tasks.append(_faiss_task)

            # Thực thi song song
            task_results = self.thread_pool.run_parallel(ingestion_tasks)

            # Ghi log kết quả
            task_idx = 0
            if self.graph_ingestion_service:
                neo4j_result = task_results[task_idx]
                if isinstance(neo4j_result, Exception):
                    import logging

                    logging.getLogger(__name__).warning(
                        "Neo4j ingestion failed (non-blocking): %s", neo4j_result
                    )
                else:
                    import logging

                    logging.getLogger(__name__).info(
                        "Neo4j ingestion result: %s", neo4j_result
                    )
                task_idx += 1

            faiss_result = task_results[task_idx]
            if isinstance(faiss_result, Exception):
                import logging

                logging.getLogger(__name__).error(
                    "FAISS ingestion failed: %s", faiss_result
                )
                raise faiss_result

            # Tự động thêm vào Redis selected files (atomic)
            self.redis_service.add_selected_file(conversation_id, file_obj.id)
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
        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, file_obj.conversation_id
        )
        if not conv:
            return False
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)
        self.file_repo.delete(file_obj)
        # Note: Xóa khỏi vector store cần rebuild; tạm thời bỏ qua
        return True

    def clear_all_files(self, conversation_id: int, user_id: int) -> bool:
        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, conversation_id
        )
        if not conv:
            return False
        files, _ = self.file_repo.get_by_conversation_and_user(
            conversation_id, user_id, limit=10000
        )
        for f in files:
            if os.path.exists(f.file_path):
                os.remove(f.file_path)
            self.file_repo.delete(f)
        vs_path = self._get_vector_store_path(conversation_id)
        if os.path.exists(vs_path):
            import shutil

            shutil.rmtree(vs_path)
        return True
