from rest_framework.views import APIView
from rest_framework.response import Response

from src.core.auth import require_auth, require_role
from src.services.conversation_service import ConversationService

class ConversationCreateView(APIView):
    @require_auth
    @require_role("user")
    def post(self, request):
        service = ConversationService()
        title = request.data.get('title')
        conv = service.create_conversation(request.user_id, title)
        return Response({"id": conv.id, "title": conv.title, "created_at": conv.created_at}, status=201)

class ConversationListView(APIView):
    @require_auth
    @require_role("user")
    def get(self, request):
        service = ConversationService()
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 20))
        convs, total = service.get_user_conversations(request.user_id, skip, limit)
        data = [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs]
        return Response({"items": data, "total": total})