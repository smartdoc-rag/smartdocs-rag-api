from rest_framework.views import APIView
from rest_framework.request import Request
from src.api.deps import get_conversation_service
from src.api.conversations.ConversationRequest import (
    CreateConversationRequest,
    UpdateConversationRequest,
    AddMessageRequest,
)
from src.api.conversations.ConversationResponse import (
    ConversationResponse,
    ConversationListResponse,
    _MessageResponse,
)
from src.api._helpers import validate_request
from src.core.response import (
    created_response,
    fetched_response,
    updated_response,
    deleted_response,
)
from src.core.auth import require_auth
from src.core.exceptions import NotFoundException


class ConversationListView(APIView):
    """API quản lý danh sách conversations của user."""

    @require_auth
    def get(self, request: Request):
        """Lấy danh sách conversations của user hiện tại."""
        service = get_conversation_service()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        result = service.get_user_conversations(
            user_id=request.user_id,
            page=page,
            page_size=page_size,
            active_only=active_only
        )

        # Thêm thông tin message count và last message
        conversations_with_extra = []
        for conv in result["items"]:
            message_count = service.message_repo.count_messages_by_conversation(conv.id)
            last_msg = service.message_repo.get_last_message(conv.id)
            last_message_content = last_msg.content[:100] + "..." if last_msg and len(last_msg.content) > 100 else (
                last_msg.content if last_msg else None
            )
            
            conversations_with_extra.append(
                ConversationListResponse.from_model(
                    conv,
                    message_count=message_count,
                    last_message=last_message_content
                )
            )

        return fetched_response(
            data=conversations_with_extra,
            meta=result["meta"]
        )

    @require_auth
    def post(self, request: Request):
        """Tạo conversation mới."""
        validated = validate_request(CreateConversationRequest, request.data)
        service = get_conversation_service()

        conversation = service.create_conversation(
            user_id=request.user_id,
            title=validated.get("title"),
            document_id=validated.get("document_id")
        )

        return created_response(
            data=ConversationResponse.from_model(conversation),
            message="Tạo hội thoại thành công"
        )


class ConversationDetailView(APIView):
    """API quản lý chi tiết conversation."""

    @require_auth
    def get(self, request: Request, conversation_id: int):
        """Lấy thông tin chi tiết conversation."""
        service = get_conversation_service()
        conversation = service.get_conversation(conversation_id, request.user_id)
        return fetched_response(
            data=ConversationResponse.from_model(conversation)
        )

    @require_auth
    def put(self, request: Request, conversation_id: int):
        """Cập nhật thông tin conversation."""
        validated = validate_request(UpdateConversationRequest, request.data)
        service = get_conversation_service()

        conversation = service.update_conversation(
            conversation_id=conversation_id,
            user_id=request.user_id,
            title=validated.get("title")
        )

        return updated_response(
            data=ConversationResponse.from_model(conversation),
            message="Cập nhật hội thoại thành công"
        )

    @require_auth
    def delete(self, request: Request, conversation_id: int):
        """Xóa conversation (soft delete)."""
        service = get_conversation_service()
        service.delete_conversation(conversation_id, request.user_id)
        return deleted_response(message="Đã đóng hội thoại")


class ConversationMessagesView(APIView):
    """API quản lý messages trong conversation."""

    @require_auth
    def get(self, request: Request, conversation_id: int):
        """Lấy danh sách messages của conversation."""
        service = get_conversation_service()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))

        result = service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=request.user_id,
            page=page,
            page_size=page_size
        )

        return fetched_response(
            data=_MessageResponse(result["items"], many=True).data,
            meta=result["meta"]
        )

    @require_auth
    def post(self, request: Request, conversation_id: int):
        """Thêm message vào conversation."""
        validated = validate_request(AddMessageRequest, request.data)
        service = get_conversation_service()

        message = service.add_message(
            conversation_id=conversation_id,
            user_id=request.user_id,
            content=validated["content"],
            is_from_user=validated.get("is_from_user", True),
            metadata=validated.get("metadata", {})
        )

        return created_response(
            data=_MessageResponse(message).data,
            message="Đã gửi tin nhắn"
        )