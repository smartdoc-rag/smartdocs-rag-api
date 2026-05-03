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

    def get_recent(self, conversation_id: int, limit: int = 5) -> list[RequestMessage]:
        """Lấy limit request gần nhất (theo thời gian giảm dần)"""
        return list(self.model_class.objects.filter(
            conversation_id=conversation_id
        ).order_by('-id')[:limit])

    def count_by_conversation(self, conversation_id: int) -> int:
        return self.model_class.objects.filter(conversation_id=conversation_id).count()

    def get_paginated(self, conversation_id: int, skip: int, limit: int):
        return self.model_class.objects.filter(
            conversation_id=conversation_id
        ).order_by('-created_at')[skip:skip + limit]

    def delete_by_conversation(self, conversation_id: int):
        self.model_class.objects.filter(conversation_id=conversation_id).delete()
