from django.db.models import Prefetch
from src.models.conversation import Conversation
from src.models.message import Message
from src.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    model_class = Conversation

    def get_by_id_with_messages(self, conversation_id: int) -> Conversation | None:
        """Eager load messages trong 1 query — tránh N+1."""
        try:
            return Conversation.objects.prefetch_related(
                Prefetch("messages", queryset=Message.objects.all())
            ).get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None

    def get_user_conversations(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[Conversation], int]:
        """Lấy danh sách conversations của user."""
        queryset = Conversation.objects.filter(
            user_id=user_id,
            is_active=True,
        ).order_by("-created_at")
        total = queryset.count()
        items = list(queryset[skip:skip + limit])
        return items, total

    def get_conversation_with_user_check(
        self, conversation_id: int, user_id: int
    ) -> Conversation | None:
        """Lấy conversation và kiểm tra xem user có quyền truy cập không."""
        try:
            return Conversation.objects.get(id=conversation_id, user_id=user_id)
        except Conversation.DoesNotExist:
            return None