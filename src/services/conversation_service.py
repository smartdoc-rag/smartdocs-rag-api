import logging
import os
import shutil

from src.models.files import File
from django.conf import settings
from src.services.rag import graph_rag_service
from src.repositories import FileRepository
from src.services.redis_service import RedisService
from src.repositories.conversation_repository import ConversationRepository
from src.models.conversations import Conversation
from django.utils import timezone
from src.core.exceptions import NotFoundException, ForbiddenException

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self):
        self.conversation_repo = ConversationRepository()
        self.file_repo = FileRepository()
        self.redis_service = RedisService()
        if graph_rag_service:
            self.graph_service = graph_rag_service
        else:
            # Thử import và khởi tạo (có thể không có Neo4j)
            try:
                from src.services.rag.graph_ingestion_service import GraphIngestionService
                self.graph_service = GraphIngestionService()
            except Exception:
                self.graph_service = None
                logger.warning("GraphIngestionService not available")


    # tao session cua user
    def create_conversation(self, user_id: int, title: str = None) -> Conversation:
        if not user_id:
            raise ValueError("không tìm thấy người dùng")
        conv = Conversation(user_id=user_id, title=title, last_chat_at=timezone.now())
        return self.conversation_repo.create(conv)

    def get_user_conversations(self, user_id: int, cursor=None, limit=20):
        convs = self.conversation_repo.get_by_user_with_cursor(
            user_id=user_id,
            cursor=cursor,
            limit=limit + 1,  # lấy dư 1
        )

        has_next = len(convs) > limit

        if has_next:
            convs = convs[:limit]

        next_cursor = None
        if convs:
            last = convs[-1]

            sort_time = last.last_chat_at or last.created_at
            next_cursor = f"{sort_time.isoformat()}_{last.id}"

        return convs, next_cursor, has_next

    # update title
    def update_conversation(
        self, user_id: int, conversation_id: int, title: str = None
    ) -> Conversation:
        if not user_id or not conversation_id:
            raise ValueError("user_id and conversation_id are required")

        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, conversation_id
        )
        if not conv:
            raise ("Conversation not found")

        conv.title = title
        return self.conversation_repo.update(conv)

    # update last_chat
    def update_last_chat(
        self, user_id: int, conversation_id: int, title: str = None
    ) -> Conversation:
        if not user_id or not conversation_id:
            raise ValueError("user_id and conversation_id are required")

        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, conversation_id
        )
        if not conv:
            raise NotFoundException("Không tìm tìm thấy đoạn chat")

        conv.last_chat_at = timezone.now()
        return self.conversation_repo.update(conv)

    def delete_conversation(self, user_id: int, conversation_id: int) -> bool:
        if not user_id:
            raise ValueError("user_id is required")
        if not conversation_id:
            raise ValueError("conversation_id is required")

        conv = self.conversation_repo.get_user_conversation_by_id(user_id, conversation_id)
        if not conv:
            raise NotFoundException("Không tìm thấy đoạn chat")

        # 1. Dọn dẹp tất cả file, vector store, graph, redis
        #    (sử dụng FileService, tự khởi tạo hoặc inject)
        from src.services.file_service import FileService  # nếu chưa import
        file_svc = FileService()  # có thể tái sử dụng instance nếu đã có, nhưng tạo mới cũng ok
        file_svc.clear_all_files(conversation_id, user_id)

        # 2. Xóa conversation (cascade xóa hết request, response, citation, stat, chunk, file records còn sót)
        conv.delete()

        return True

    # lay session theo id cua user
    def get_conversation_by_id(
        self, conversation_id: int, user_id: int
    ) -> Conversation:
        conv = self.conversation_repo.get_user_conversation_by_id(
            user_id, conversation_id
        )
        if not conv:
            raise ForbiddenException(
                "Cuộc hội thoại không tồn tại hoặc không có quyền truy cập"
            )
        return conv
