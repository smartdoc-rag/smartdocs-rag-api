from src.models.conversations import Conversation
from src.repositories.base import BaseRepository
from django.db.models import F, Func, Q
from django.utils.dateparse import parse_datetime


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

    def get_by_user_with_cursor(
        self, user_id: int, cursor: str | None = None, limit: int = 20
    ) -> list[Conversation]:

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
        )

        if cursor:
            try:
                time_str, id_str = cursor.split("_")
                cursor_time = parse_datetime(time_str)
                
                cursor_id = int(id_str)
                print(cursor)
                print(cursor_time, cursor_id)
                queryset = queryset.filter(
                    Q(sort_time__lt=cursor_time) |
                    Q(sort_time=cursor_time, id__lt=cursor_id)
                )
            except Exception:
                pass  

        queryset = queryset.order_by("-sort_time", "-id")

        return list(queryset[:limit])

    def get_user_conversation_by_id(
        self, user_id: int, conversation_id: int
    ) -> Conversation | None:
        return self.get_one(id=conversation_id, user_id=user_id)
