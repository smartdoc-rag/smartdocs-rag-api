from rest_framework.views import APIView

from src.core.response import success_response, error_response
from src.core.auth import require_auth, require_role
from src.services.conversation_service import ConversationService

class ConversationCreateView(APIView):
    @require_auth
    @require_role("user")
    def post(self, request):
        service = ConversationService()
        title = request.data.get('title')
        conv = service.create_conversation(request.user_id, title)
        return success_response({"id": conv.id, "title": conv.title, "created_at": conv.created_at}, code=201)

class ConversationListView(APIView):
    @require_auth
    @require_role("user")
    def get(self, request):
        service = ConversationService()
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 20))
        convs, total = service.get_user_conversations(request.user_id, skip, limit)
        data = [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs]
        return success_response({"items": data, "total": total})

class ConversationChunkConfigView(APIView):
    @require_auth
    @require_role("user")
    def patch(self, request, conversation_id):
        service = ConversationService()
        try:
            conv = service.get_conversation_by_id(conversation_id, request.user_id)
        except PermissionError as e:
            return error_response({"error": str(e)}, code=404)

        chunk_size = request.data.get('chunk_size')
        chunk_overlap = request.data.get('chunk_overlap')

        if chunk_size is not None:
            if not isinstance(chunk_size, int) or chunk_size < 100:
                return error_response({"error": "chunk_size must be integer >= 100"}, code=400)
            conv.chunk_size = chunk_size
        if chunk_overlap is not None:
            if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
                return error_response({"error": "chunk_overlap must be integer >= 0"}, code=400)
            conv.chunk_overlap = chunk_overlap

        conv.save()
        return success_response({
            "conversation_id": conv.id,
            "chunk_size": conv.chunk_size,
            "chunk_overlap": conv.chunk_overlap
        })