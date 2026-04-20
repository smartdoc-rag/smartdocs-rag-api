from rest_framework.views import APIView

from src.core.response import success_response, error_response
from src.core.auth import require_auth, require_role
from src.services.conversation_service import ConversationService
from django.forms.models import model_to_dict

class ConversationCreateView(APIView):
    @require_auth
    @require_role("user")
    def post(self, request):
        service = ConversationService()
        title = request.data.get('title')
        conv = service.create_conversation(request.user_id, title)
        data = model_to_dict(conv, exclude=['user'])
        return success_response(data, code=201)

class ConversationListView(APIView):
    @require_auth
    @require_role("user")
    def get(self, request):
        service = ConversationService()
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 20))
        convs, total = service.get_user_conversations(request.user_id, skip, limit)
        data = [model_to_dict(c, exclude=['user']) for c in convs]
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
        data = model_to_dict(conv, exclude=['user'])
        return success_response(data, code=200)
    
    
class ConversationUpdateView(APIView):
    @require_auth
    @require_role("user")
    def put(self, request, conversation_id):
        service = ConversationService()
        title = request.data.get('title')
        conv = service.update_conversation(request.user_id, conversation_id, title)
        data = model_to_dict(conv, exclude=['user'])
        return success_response(data, code=200)
    
    

class ConversationPatchView(APIView):
    @require_auth
    @require_role("user")
    def patch(self, request, conversation_id):
        service = ConversationService()
        conv = service.update_last_chat(request.user_id, conversation_id)
        data = model_to_dict(conv, exclude=['user'])
        return success_response(data, code=200)

class ConversationDeleteView(APIView):
    @require_auth
    @require_role("user")
    def delete(self, request, conversation_id):
        try:
            service = ConversationService()
            success = service.delete_conversation(request.user_id, conversation_id)
            
            if success:
                return success_response(
                    {'message': "Xóa hội thoại thành công", 'conversation_id': conversation_id},
                    code=200
                )
            else:
                return error_response(
                    {'message': "Có lỗi xảy ra khi xóa hội thoại", 'conversation_id': conversation_id},
                    code=500
                )
                
        except ValueError as e:
            return error_response(
                {'message': str(e), 'conversation_id': conversation_id},
                code=400
            )
            
        except Exception as e:
            return error_response(
                {'message': "Đã xảy ra lỗi hệ thống", 'conversation_id': conversation_id},
                code=500
            )
            
class ConversationGetByIdView(APIView):
    @require_auth
    @require_role("user")
    def get(self, request, conversation_id):
        service = ConversationService()
        conv = service.get_conversation_by_id(conversation_id, request.user_id)
        data = model_to_dict(conv, exclude=['user'])
        return success_response(data, code=201)