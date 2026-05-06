from src.models.files import File
from src.repositories.base import BaseRepository


class FileRepository(BaseRepository[File]):
    model_class = File

    def get_by_conversation_id(
        self, conversation_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[File], int]:
        """Lấy danh sách file theo conversation_id với phân trang"""
        return self.get_all(skip=skip, limit=limit, conversation_id=conversation_id)

    def get_by_conversation_and_user(
        self, conversation_id: int, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[File], int]:
        """Lấy danh sách file theo conversation_id và user_id (qua conversation)"""
        queryset = self.model_class.objects.filter(
            conversation_id=conversation_id, conversation__user_id=user_id
        )
        total = queryset.count()
        items = list(queryset[skip : skip + limit])
        return items, total

    def get_conversation_file_by_id(
        self, conversation_id: int, file_id: int
    ) -> File | None:
        """Lấy file theo ID và conversation_id"""
        return self.get_one(id=file_id, conversation_id=conversation_id)
    
    def get_by_id(self, file_id: int) -> File | None:
     return self.get_one(id=file_id)
