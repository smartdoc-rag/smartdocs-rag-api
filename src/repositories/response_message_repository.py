from src.models.response_messages import ResponseMessage
from src.repositories.base import BaseRepository


class ResponseMessageRepository(BaseRepository[ResponseMessage]):
    model_class = ResponseMessage

    def get_by_request_message_id(
        self, request_message_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[ResponseMessage], int]:
        """Lấy danh sách response message theo request_message_id với phân trang"""
        return self.get_all(
            skip=skip, limit=limit, request_message_id=request_message_id
        )

    def get_by_conversation_id(
        self, conversation_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[ResponseMessage], int]:
        """Lấy danh sách response message theo conversation_id (qua request_message)"""
        queryset = self.model_class.objects.filter(
            request_message__conversation_id=conversation_id
        )
        total = queryset.count()
        items = list(queryset[skip : skip + limit])
        return items, total

    def get_by_type(
        self, type: str, skip: int = 0, limit: int = 20
    ) -> tuple[list[ResponseMessage], int]:
        """Lấy danh sách response message theo loại (rag/graphrag)"""
        return self.get_all(skip=skip, limit=limit, type=type)

    def get_request_response_by_id(
        self, request_message_id: int, response_id: int
    ) -> ResponseMessage | None:
        """Lấy response message theo ID và request_message_id"""
        return self.get_one(id=response_id, request_message_id=request_message_id)

    def delete_by_request_message_id(self, request_message_id: int):
        self.model_class.objects.filter(request_message_id=request_message_id).delete()

    def get_by_request(self, request_message_id: int):
        return self.model_class.objects.filter(
            request_message_id=request_message_id
        ).order_by('created_at')
