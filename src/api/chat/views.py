from rest_framework.views import APIView
from rest_framework.response import Response
from src.core.auth import require_auth
from src.services.chat_service import ChatService

class ChatAskView(APIView):
    @require_auth
    def post(self, request, conversation_id):
        service = ChatService()
        question = request.data.get('question')
        if not question:
            return Response({"error": "Missing question"}, status=400)
        selected_file_ids = request.data.get('selected_file_ids', [])
        response_type = request.data.get('response_type', 'rag')
        try:
            result = service.ask(conversation_id, request.user_id, question, selected_file_ids, response_type)
            return Response(result, status=200)
        except PermissionError as e:
            return Response({"error": str(e)}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ChatHistoryView(APIView):
    @require_auth
    def get(self, request, conversation_id):
        service = ChatService()
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 50))
        try:
            history, total = service.get_history(conversation_id, request.user_id, skip, limit)
            return Response({"history": history, "total": total}, status=200)
        except PermissionError:
            return Response({"error": "Access denied"}, status=403)

class ClearHistoryView(APIView):
    @require_auth
    def delete(self, request, conversation_id):
        service = ChatService()
        try:
            service.clear_history(conversation_id, request.user_id)
            return Response(status=204)
        except PermissionError:
            return Response({"error": "Access denied"}, status=403)