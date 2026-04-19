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
        return Response({"id": conv.id, "title": conv.title, "created_at": conv.created_at, "last_chat_at": conv.last_chat_at}, status=201)

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
    
    
class ConversationUpdateView(APIView):
    @require_auth
    @require_role("user")
    def put(self, request, conversation_id):
        service = ConversationService()
        title = request.data.get('title')
        conv = service.update_conversation(request.user_id, conversation_id, title)
        return Response({"id": conv.id, "title": conv.title, "created_at": conv.created_at, "last_chat_at": conv.last_chat_at}, status=200)
    
    
    
class ConversationUpdateView(APIView):
    @require_auth
    @require_role("user")
    def put(self, request, conversation_id):
        service = ConversationService()
        title = request.data.get('title')
        conv = service.update_conversation(request.user_id, conversation_id, title)
        return Response({"id": conv.id, "title": conv.title, "created_at": conv.created_at, "last_chat_at": conv.last_chat_at}, status=200)
    
    
    
class ConversationUpdateView(APIView):
    @require_auth
    @require_role("user")
    def put(self, request, conversation_id):
        service = ConversationService()
        title = request.data.get('title')
        conv = service.update_conversation(request.user_id, conversation_id, title)
        return Response({"id": conv.id, "title": conv.title, "created_at": conv.created_at, "last_chat_at": conv.last_chat_at}, status=200)
    
    
    
class ConversationPatchView(APIView):
    @require_auth
    @require_role("user")
    def patch(self, request, conversation_id):
        service = ConversationService()
        conv = service.update_last_chat(request.user_id, conversation_id)
        return Response({"id": conv.id, "title": conv.title, "created_at": conv.created_at, "last_chat_at": conv.last_chat_at}, status=200)
    
class ConversationDeleteView(APIView):
    @require_auth
    @require_role("user")
    def delete(self, request, conversation_id):
        try:
            service = ConversationService()
            success = service.delete_conversation(request.user_id, conversation_id)
            
            if success:
                return Response(
                    {'message': "Xóa hội thoại thành công", 'conversation_id': conversation_id},
                    status=200
                )
            else:
                return Response(
                    {'message': "Có lỗi xảy ra khi xóa hội thoại", 'conversation_id': conversation_id},
                    status=500
                )
                
        except ValueError as e:
            return Response(
                {'message': str(e), 'conversation_id': conversation_id},
                status=400
            )
            
        except Exception as e:
            return Response(
                {'message': "Đã xảy ra lỗi hệ thống", 'conversation_id': conversation_id},
                status=500
            )