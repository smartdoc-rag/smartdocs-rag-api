from src.models.conversations import Conversation
from src.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    model_class = Conversation

    def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[Conversation], int]:
        """Lấy danh sách conversation theo user_id với phân trang"""
        return self.get_all(skip=skip, limit=limit, user_id=user_id)

    def get_user_conversation_by_id(
        self, user_id: int, conversation_id: int
    ) -> Conversation | None:
        """Lấy conversation theo ID và user_id (đảm bảo user sở hữu conversation)"""
        return self.get_one(id=conversation_id, user_id=user_id)
