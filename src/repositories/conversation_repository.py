from src.models.conversations import Conversation
from src.repositories.base import BaseRepository
from django.db.models import F, Func

def get_all_with_order(self, skip: int = 0, limit: int = 20):
    queryset = (
        self.model_class.objects
        .annotate(
            sort_time=Func(
                F("last_chat_at"), 
                F("created_at"), 
                function="COALESCE"
            )
        )
        .order_by("-sort_time")
    )
    
    total = queryset.count()
    items = list(queryset[skip:skip + limit])
    
    return items, total

class ConversationRepository(BaseRepository[Conversation]):
    model_class = Conversation

    def get_by_user_id_with_order(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[Conversation], int]:
        """Lấy danh sách conversation theo user_id với phân trang và sắp xếp"""
        queryset = (
            self.model_class.objects
            .filter(user_id=user_id)
            .annotate(
                sort_time=Func(
                    F("last_chat_at"), 
                    F("created_at"), 
                    function="COALESCE"
                )
            )
            .order_by("-sort_time")
        )
        
        total = queryset.count()
        items = list(queryset[skip:skip + limit])
        
        return items, total

    def get_user_conversation_by_id(
        self, user_id: int, conversation_id: int
    ) -> Conversation | None:
        """Lấy conversation theo ID và user_id (đảm bảo user sở hữu conversation)"""
        return self.get_one(id=conversation_id, user_id=user_id)
