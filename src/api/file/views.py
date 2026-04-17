from rest_framework.views import APIView
from rest_framework.response import Response
from src.core.auth import require_auth
from src.services.file_service import FileService

class FileUploadView(APIView):
    @require_auth
    def post(self, request, conversation_id):
        service = FileService()
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({"error": "No file"}, status=400)
        scope = request.data.get('scope', 'private')
        try:
            file_obj = service.upload_file(conversation_id, request.user_id, uploaded, scope)
            return Response({"id": file_obj.id, "file_name": file_obj.file_name, "file_size": file_obj.file_size}, status=201)
        except PermissionError as e:
            return Response({"error": str(e)}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class FileListView(APIView):
    @require_auth
    def get(self, request, conversation_id):
        service = FileService()
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 20))
        files, total = service.get_files(conversation_id, request.user_id, skip, limit)
        data = [{"id": f.id, "file_name": f.file_name, "file_size": f.file_size, "file_type": f.file_type, "scope": f.scope} for f in files]
        return Response({"items": data, "total": total})

class FileDeleteView(APIView):
    @require_auth
    def delete(self, request, conversation_id, file_id):
        service = FileService()
        try:
            service.delete_file(file_id, request.user_id)
            return Response(status=204)
        except PermissionError:
            return Response({"error": "Access denied"}, status=403)

class ClearFilesView(APIView):
    @require_auth
    def delete(self, request, conversation_id):
        service = FileService()
        try:
            service.clear_all_files(conversation_id, request.user_id)
            return Response(status=204)
        except PermissionError:
            return Response({"error": "Access denied"}, status=403)