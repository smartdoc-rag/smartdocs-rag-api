from src.models.conversation import Conversation
from src.models.message import Message
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.user_repository import UserRepository
from core.exceptions import NotFoundException, BadRequestException
from core.pagination import build_pagination_meta


class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        user_repo: UserRepository
    ):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.user_repo = user_repo

    def create_conversation(self, user_id: int, title: str = None) -> Conversation:
        """Tạo conversation mới."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        
        conversation = Conversation(
            title=title,
            user_id=user_id,
            is_active=True
        )
        return self.conversation_repo.create(conversation)

    def get_user_conversations(self, user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """Lấy danh sách conversations của user."""
        skip = (page - 1) * page_size
        items, total = self.conversation_repo.get_user_conversations(
            user_id=user_id,
            skip=skip,
            limit=page_size
        )
        return {"items": items, "meta": build_pagination_meta(page, page_size, total)}

    def get_conversation(self, conversation_id: int, user_id: int) -> Conversation:
        """Lấy conversation và kiểm tra quyền truy cập."""
        conversation = self.conversation_repo.get_conversation_with_user_check(
            conversation_id=conversation_id,
            user_id=user_id
        )
        if not conversation:
            raise NotFoundException("Không tìm thấy hội thoại hoặc không có quyền truy cập")
        return conversation

    def get_conversation_with_messages(self, conversation_id: int, user_id: int) -> Conversation:
        """Lấy conversation kèm messages."""
        conversation = self.get_conversation(conversation_id, user_id)
        # Eager load messages
        return self.conversation_repo.get_by_id_with_messages(conversation_id)

    def update_conversation_title(
        self, conversation_id: int, user_id: int, title: str
    ) -> Conversation:
        """Cập nhật tiêu đề conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        conversation.title = title
        return self.conversation_repo.update(conversation)

    def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """Xóa conversation (soft delete bằng cách đánh dấu is_active=False)."""
        conversation = self.get_conversation(conversation_id, user_id)
        conversation.is_active = False
        self.conversation_repo.update(conversation)

    def add_message(
        self, conversation_id: int, user_id: int, content: str, role: str = "user"
    ) -> Message:
        """Thêm message vào conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        
        if role not in ["user", "assistant", "system"]:
            raise BadRequestException("Role không hợp lệ")
        
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=role
        )
        return self.message_repo.create(message)

    def get_conversation_messages(
        self, conversation_id: int, user_id: int, page: int = 1, page_size: int = 50
    ) -> dict:
        """Lấy danh sách messages của conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        skip = (page - 1) * page_size
        items, total = self.message_repo.get_conversation_messages(
            conversation_id=conversation_id,
            skip=skip,
            limit=page_size
        )
        return {"items": items, "meta": build_pagination_meta(page, page_size, total)}