import os
import uuid
from typing import List, Tuple
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.vectorstores import FAISS
from src.models.files import File
from src.repositories.file_repository import FileRepository
from src.repositories.conversation_repository import ConversationRepository
from src.services.rag.file_ingestion_service import FileIngestionService
from src.core.rag.embedding_provider import get_embedding

MEDIA_ROOT = os.path.join(settings.BASE_DIR, "media", "files")
VECTOR_DB_ROOT = os.path.join(settings.BASE_DIR, "vector_db")
SUPPORTED_EXTENSIONS = {'.pdf': 'pdf', '.docx': 'docx'}

class FileService:
    def __init__(self):
        self.file_repo = FileRepository()
        self.conversation_repo = ConversationRepository()
        self.ingestion_service = FileIngestionService()
        self.embedding = get_embedding()

    def _get_vector_store_path(self, conversation_id: int) -> str:
        return os.path.join(VECTOR_DB_ROOT, f"conv_{conversation_id}")

    def _load_vectorstore(self, conversation_id: int):
        path = self._get_vector_store_path(conversation_id)
        if os.path.exists(path):
            return FAISS.load_local(path, self.embedding, allow_dangerous_deserialization=True)
        return None

    def _save_vectorstore(self, vectorstore, conversation_id: int):
        path = self._get_vector_store_path(conversation_id)
        os.makedirs(path, exist_ok=True)
        vectorstore.save_local(path)

    def _extract_documents(self, file_path: str, file_type: str) -> list:
        if file_type == 'pdf':
            loader = PyPDFLoader(file_path)
        else:
            loader = Docx2txtLoader(file_path)
        docs = loader.load()
        if not docs:
            raise ValueError("Cannot extract text from file")
        return self.ingestion_service.text_splitter(docs)

    @transaction.atomic
    def upload_file(self, conversation_id: int, user_id: int, uploaded_file: UploadedFile, scope='private'):
        # Kiểm tra quyền
        conversation = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conversation:
            raise PermissionError("Access denied")

        # Validate
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file type")
        file_type = SUPPORTED_EXTENSIONS[ext]

        # Lưu file vật lý
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        saved_name = f"{uuid.uuid4()}_{uploaded_file.name}"
        saved_path = os.path.join(MEDIA_ROOT, saved_name)
        with open(saved_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        try:
            # Split documents
            split_docs = self._extract_documents(saved_path, file_type)

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
                doc.metadata['file_id'] = file_obj.id
                doc.metadata['file_name'] = file_obj.file_name
                doc.metadata['conversation_id'] = conversation_id

            # Ingest vào vector store
            vectorstore = self._load_vectorstore(conversation_id)
            new_vs = FAISS.from_documents(split_docs, self.embedding)
            if vectorstore:
                vectorstore.merge_from(new_vs)
                self._save_vectorstore(vectorstore, conversation_id)
            else:
                self._save_vectorstore(new_vs, conversation_id)

            return file_obj
        except Exception:
            if os.path.exists(saved_path):
                os.remove(saved_path)
            raise

    def get_files(self, conversation_id: int, user_id: int, skip=0, limit=20) -> Tuple[List[File], int]:
        return self.file_repo.get_by_conversation_and_user(conversation_id, user_id, skip, limit)

    def delete_file(self, file_id: int, user_id: int) -> bool:
        file_obj = self.file_repo.get_one(id=file_id)
        if not file_obj:
            return False
        conv = self.conversation_repo.get_user_conversation_by_id(user_id, file_obj.conversation_id)
        if not conv:
            return False
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)
        self.file_repo.delete(file_obj)
        # Note: Xóa khỏi vector store cần rebuild; tạm thời bỏ qua
        return True

    def clear_all_files(self, conversation_id: int, user_id: int) -> bool:
        conv = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            return False
        files, _ = self.file_repo.get_by_conversation_and_user(conversation_id, user_id, limit=10000)
        for f in files:
            if os.path.exists(f.file_path):
                os.remove(f.file_path)
            self.file_repo.delete(f)
        vs_path = self._get_vector_store_path(conversation_id)
        if os.path.exists(vs_path):
            import shutil
            shutil.rmtree(vs_path)
        return True