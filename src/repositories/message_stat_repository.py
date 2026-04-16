from src.models.message_stats import MessageStat
from src.repositories.base import BaseRepository


class MessageStatRepository(BaseRepository[MessageStat]):
    model_class = MessageStat

    def get_by_message_id(
        self, message_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[MessageStat], int]:
        """Lấy danh sách message stat theo message_id với phân trang"""
        return self.get_all(skip=skip, limit=limit, message_id=message_id)

    def get_message_stat_by_id(
        self, message_id: int, stat_id: int
    ) -> MessageStat | None:
        """Lấy message stat theo ID và message_id"""
        return self.get_one(id=stat_id, message_id=message_id)
