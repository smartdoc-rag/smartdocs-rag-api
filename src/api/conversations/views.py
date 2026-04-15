from rest_framework.views import APIView
from rest_framework.request import Request

from core.auth import require_auth
from core.response import (
    created_response, fetched_response, updated_response, deleted_response
)
from core.exceptions import NotFoundException

from api.deps import get_conversation_service
from api._helper import validate_request
from .ConversationRequest import (
    CreateConversationRequest,
    UpdateConversationRequest,
    AddMessageRequest,
)
from .ConversationResponse import ConversationResponse, MessageResponse


class ConversationListView(APIView):
    """API quản lý danh sách conversations của user."""

    @require_auth
    def get(self, request: Request):
        """Lấy danh sách conversations của user hiện tại."""
        service = get_conversation_service()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        
        result = service.get_user_conversations(
            user_id=request.user_id,
            page=page,
            page_size=page_size
        )
        return fetched_response(
            data=ConversationResponse.from_list(result["items"]),
            meta=result["meta"]
        )

    @require_auth
    def post(self, request: Request):
        """Tạo conversation mới."""
        data = validate_request(CreateConversationRequest, request.data)
        service = get_conversation_service()
        
        conversation = service.create_conversation(
            user_id=request.user_id,
            title=data.get("title")
        )
        return created_response(
            data=ConversationResponse.from_model(conversation),
            message="Tạo hội thoại thành công"
        )


class ConversationDetailView(APIView):
    """API quản lý chi tiết conversation."""

    @require_auth
    def get(self, request: Request, conversation_id: int):
        """Lấy thông tin chi tiết conversation kèm messages."""
        service = get_conversation_service()
        
        conversation = service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=request.user_id
        )
        return fetched_response(
            data=ConversationResponse.from_model(conversation)
        )

    @require_auth
    def put(self, request: Request, conversation_id: int):
        """Cập nhật tiêu đề conversation."""
        data = validate_request(UpdateConversationRequest, request.data)
        service = get_conversation_service()
        
        conversation = service.update_conversation_title(
            conversation_id=conversation_id,
            user_id=request.user_id,
            title=data["title"]
        )
        return updated_response(
            data=ConversationResponse.from_model(conversation),
            message="Cập nhật hội thoại thành công"
        )

    @require_auth
    def delete(self, request: Request, conversation_id: int):
        """Xóa conversation (soft delete)."""
        service = get_conversation_service()
        service.delete_conversation(
            conversation_id=conversation_id,
            user_id=request.user_id
        )
        return deleted_response(message="Xóa hội thoại thành công")


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
            data=MessageResponse.from_list(result["items"]),
            meta=result["meta"]
        )

    @require_auth
    def post(self, request: Request, conversation_id: int):
        """Thêm message vào conversation."""
        data = validate_request(AddMessageRequest, request.data)
        service = get_conversation_service()
        
        message = service.add_message(
            conversation_id=conversation_id,
            user_id=request.user_id,
            content=data["content"],
            role=data.get("role", "user")
        )
        return created_response(
            data=MessageResponse.from_model(message),
            message="Thêm tin nhắn thành công"
        )