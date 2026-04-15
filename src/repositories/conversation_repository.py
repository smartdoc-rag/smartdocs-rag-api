from typing import Optional, List, Tuple
from django.db.models import Prefetch
from src.models.conversation import Conversation
from src.models.conversation_message import ConversationMessage
from src.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    model_class = Conversation

    def get_by_id_with_messages(self, conversation_id: int) -> Optional[Conversation]:
        """Lấy conversation kèm danh sách messages (eager load)."""
        try:
            return Conversation.objects.prefetch_related(
                Prefetch(
                    "messages",
                    queryset=ConversationMessage.objects.all().order_by("created_at")
                )
            ).get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None

    def get_user_conversations(
        self, user_id: int, skip: int = 0, limit: int = 20, active_only: bool = True
    ) -> Tuple[List[Conversation], int]:
        """Lấy danh sách conversations của user."""
        queryset = Conversation.objects.filter(user_id=user_id)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.order_by("-updated_at")
        total = queryset.count()
        items = list(queryset[skip:skip + limit])
        return items, total

    def get_conversations_by_document(
        self, document_id: int, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Conversation], int]:
        """Lấy danh sách conversations liên quan đến document."""
        queryset = Conversation.objects.filter(
            document_id=document_id,
            is_active=True
        ).order_by("-updated_at")
        
        total = queryset.count()
        items = list(queryset[skip:skip + limit])
        return items, total