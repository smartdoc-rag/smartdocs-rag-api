from src.models.message_citations import MessageCitation
from src.repositories.base import BaseRepository


class MessageCitationRepository(BaseRepository[MessageCitation]):
    model_class = MessageCitation

    def get_by_response_message_id(
        self, response_message_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[MessageCitation], int]:
        """Lấy danh sách citation theo response_message_id với phân trang"""
        return self.get_all(
            skip=skip, limit=limit, response_message_id=response_message_id
        )

    def get_by_file_id(
        self, file_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[MessageCitation], int]:
        """Lấy danh sách citation theo file_id với phân trang"""
        return self.get_all(skip=skip, limit=limit, file_id=file_id)

    def get_response_citation_by_id(
        self, response_message_id: int, citation_id: int
    ) -> MessageCitation | None:
        """Lấy citation theo ID và response_message_id"""
        return self.get_one(id=citation_id, response_message_id=response_message_id)
