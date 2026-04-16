from src.models.request_messages import RequestMessage
from src.repositories.base import BaseRepository


class RequestMessageRepository(BaseRepository[RequestMessage]):
    model_class = RequestMessage

    def get_by_conversation_id(
        self, conversation_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[RequestMessage], int]:
        """Lấy danh sách request message theo conversation_id với phân trang"""
        return self.get_all(skip=skip, limit=limit, conversation_id=conversation_id)

    def get_conversation_request_by_id(
        self, conversation_id: int, request_id: int
    ) -> RequestMessage | None:
        """Lấy request message theo ID và conversation_id"""
        return self.get_one(id=request_id, conversation_id=conversation_id)

    def get_by_conversation_and_user(
        self, conversation_id: int, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[RequestMessage], int]:
        """Lấy danh sách request message theo conversation_id và user_id (qua conversation)"""
        queryset = self.model_class.objects.filter(
            conversation_id=conversation_id, conversation__user_id=user_id
        )
        total = queryset.count()
        items = list(queryset[skip : skip + limit])
        return items, total
