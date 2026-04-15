from src.models.message import Message
from src.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model_class = Message

    def get_conversation_messages(
        self, conversation_id: int, skip: int = 0, limit: int = 50
    ) -> tuple[list[Message], int]:
        """Lấy danh sách messages của conversation."""
        queryset = Message.objects.filter(
            conversation_id=conversation_id
        ).order_by("created_at")
        total = queryset.count()
        items = list(queryset[skip:skip + limit])
        return items, total

    def create_message_batch(self, messages: list[Message]) -> list[Message]:
        """Tạo nhiều messages cùng lúc."""
        return Message.objects.bulk_create(messages)