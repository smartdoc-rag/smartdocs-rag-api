from typing import Optional, Dict, Any
from src.models.conversation import Conversation
from src.models.conversation_message import ConversationMessage
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.conversation_message_repository import ConversationMessageRepository
from src.repositories.user_repository import UserRepository
from src.repositories.document_repository import DocumentRepository
from src.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from src.core.pagination import build_pagination_meta


class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: ConversationMessageRepository,
        user_repo: UserRepository,
        document_repo: DocumentRepository
    ):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.user_repo = user_repo
        self.document_repo = document_repo

    def create_conversation(
        self, user_id: int, title: Optional[str] = None, document_id: Optional[int] = None
    ) -> Conversation:
        """Tạo conversation mới."""
        # Kiểm tra user tồn tại
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")

        # Kiểm tra document nếu có
        if document_id:
            document = self.document_repo.get_by_id(document_id)
            if not document:
                raise NotFoundException("Không tìm thấy tài liệu")
            if document.user_id != user_id:
                raise ForbiddenException("Không có quyền truy cập tài liệu này")

        # Tạo conversation
        conversation = Conversation(
            title=title,
            user_id=user_id,
            document_id=document_id,
            is_active=True
        )
        return self.conversation_repo.create(conversation)

    def get_conversation(self, conversation_id: int, user_id: int) -> Conversation:
        """Lấy conversation theo ID (kiểm tra quyền)."""
        conversation = self.conversation_repo.get_by_id_with_messages(conversation_id)
        if not conversation:
            raise NotFoundException("Không tìm thấy hội thoại")
        
        if conversation.user_id != user_id:
            raise ForbiddenException("Không có quyền truy cập hội thoại này")
        
        return conversation

    def get_user_conversations(
        self, user_id: int, page: int = 1, page_size: int = 20, active_only: bool = True
    ) -> Dict[str, Any]:
        """Lấy danh sách conversations của user."""
        skip = (page - 1) * page_size
        items, total = self.conversation_repo.get_user_conversations(
            user_id, skip=skip, limit=page_size, active_only=active_only
        )
        return {"items": items, "meta": build_pagination_meta(page, page_size, total)}

    def update_conversation(
        self, conversation_id: int, user_id: int, title: Optional[str] = None
    ) -> Conversation:
        """Cập nhật thông tin conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        
        if title is not None:
            conversation.title = title
        
        return self.conversation_repo.update(conversation)

    def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """Xóa conversation (soft delete bằng cách đánh dấu không active)."""
        conversation = self.get_conversation(conversation_id, user_id)
        conversation.is_active = False
        self.conversation_repo.update(conversation)

    def add_message(
        self,
        conversation_id: int,
        user_id: int,
        content: str,
        is_from_user: bool = True,
        metadata: Optional[Dict] = None
    ) -> ConversationMessage:
        """Thêm message vào conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        
        # Kiểm tra conversation còn active không
        if not conversation.is_active:
            raise BadRequestException("Hội thoại đã bị đóng")

        # Tạo message
        message = ConversationMessage(
            conversation=conversation,
            content=content,
            is_from_user=is_from_user,
            metadata=metadata or {}
        )
        
        # Cập nhật thời gian updated_at của conversation
        conversation.save()  # Tự động cập nhật updated_at
        
        return self.message_repo.create(message)

    def get_conversation_messages(
        self, conversation_id: int, user_id: int, page: int = 1, page_size: int = 50
    ) -> Dict[str, Any]:
        """Lấy danh sách messages của conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        
        skip = (page - 1) * page_size
        items, total = self.message_repo.get_messages_by_conversation(
            conversation_id, skip=skip, limit=page_size
        )
        return {"items": items, "meta": build_pagination_meta(page, page_size, total)}