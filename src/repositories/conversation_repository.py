from typing import Optional, List, Tuple
from django.db.models import Prefetch, Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
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
        """Lấy danh sách conversations của user với message count."""
        # Subquery để lấy message count cho mỗi conversation
        message_count_subquery = ConversationMessage.objects.filter(
            conversation_id=OuterRef('id')
        ).values('conversation_id').annotate(count=Count('id')).values('count')
        
        # Subquery để lấy last message content
        last_message_subquery = ConversationMessage.objects.filter(
            conversation_id=OuterRef('id')
        ).order_by('-created_at').values('content')[:1]
        
        queryset = Conversation.objects.filter(user_id=user_id)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        # Annotate với message count và last message
        queryset = queryset.annotate(
            message_count=Coalesce(Subquery(message_count_subquery), 0),
            last_message_content=Subquery(last_message_subquery)
        ).order_by("-updated_at")
        
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