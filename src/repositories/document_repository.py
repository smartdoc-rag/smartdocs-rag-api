from typing import Optional, List, Tuple
from src.models.document import Document
from src.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model_class = Document

    def get_user_documents(
        self, user_id: int, skip: int = 0, limit: int = 20, processed_only: bool = False
    ) -> Tuple[List[Document], int]:
        """Lấy danh sách documents của user."""
        queryset = Document.objects.filter(user_id=user_id)
        
        if processed_only:
            queryset = queryset.filter(is_processed=True)
        
        queryset = queryset.order_by("-created_at")
        total = queryset.count()
        items = list(queryset[skip:skip + limit])
        return items, total

    def get_by_file_hash(self, file_hash: str) -> Optional[Document]:
        """Tìm document bằng file hash (nếu có trong metadata)."""
        try:
            return Document.objects.get(metadata__file_hash=file_hash)
        except Document.DoesNotExist:
            return None