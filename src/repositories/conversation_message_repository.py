from typing import Optional, List, Tuple
from src.models.conversation_message import ConversationMessage
from src.repositories.base import BaseRepository


class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    model_class = ConversationMessage

    def get_messages_by_conversation(
        self, conversation_id: int, skip: int = 0, limit: int = 50
    ) -> Tuple[List[ConversationMessage], int]:
        """Lấy danh sách messages của conversation."""
        queryset = ConversationMessage.objects.filter(
            conversation_id=conversation_id
        ).order_by("created_at")
        
        total = queryset.count()
        items = list(queryset[skip:skip + limit])
        return items, total

    def get_last_message(self, conversation_id: int) -> Optional[ConversationMessage]:
        """Lấy message cuối cùng của conversation."""
        try:
            return ConversationMessage.objects.filter(
                conversation_id=conversation_id
            ).order_by("-created_at").first()
        except ConversationMessage.DoesNotExist:
            return None

    def count_messages_by_conversation(self, conversation_id: int) -> int:
        """Đếm số lượng messages trong conversation."""
        return ConversationMessage.objects.filter(
            conversation_id=conversation_id
        ).count()