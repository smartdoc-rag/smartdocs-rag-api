from src.models.chunk import Chunk
from src.repositories.base import BaseRepository

class ChunkRepository(BaseRepository[Chunk]):
    model_class = Chunk

    def get_by_conversation(self, conversation_id: int, skip: int = 0, limit: int = 20) -> tuple[list[Chunk], int]:
        """Lấy danh sách chunk theo conversation_id"""
        return self.get_all(skip=skip, limit=limit, conversation_id=conversation_id)

    def get_by_file(self, file_id: int, skip: int = 0, limit: int = 20) -> tuple[list[Chunk], int]:
        """Lấy danh sách chunk theo file_id"""
        return self.get_all(skip=skip, limit=limit, file_id=file_id)

    def delete_by_conversation(self, conversation_id: int) -> None:
        """Xóa tất cả chunk của một conversation"""
        self.model_class.objects.filter(conversation_id=conversation_id).delete()