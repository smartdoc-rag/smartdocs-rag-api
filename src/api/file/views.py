from rest_framework.views import APIView
from src.core.response import success_response, error_response
from src.core.auth import require_auth, require_role
from src.services.file_service import FileService


class FileUploadView(APIView):
    @require_auth
    @require_role("user")
    def post(self, request, conversation_id):
        service = FileService()
        files = request.FILES.getlist('files')  # Lấy danh sách file với key 'files'
        if not files:
            return error_response({"error": "No files provided"}, code=400)

        scope = request.data.get('scope', 'private')
        results = []
        errors = []

        for uploaded_file in files:
            try:
                file_obj = service.upload_file(conversation_id, request.user_id, uploaded_file, scope)
                results.append({
                    "id": file_obj.id,
                    "file_name": file_obj.file_name,
                    "file_size": file_obj.file_size,
                    "file_type": file_obj.file_type,
                })
            except PermissionError as e:
                errors.append({"file": uploaded_file.name, "error": str(e)})
            except Exception as e:
                errors.append({"file": uploaded_file.name, "error": str(e)})

        if errors:
            return error_response({"uploaded": results, "errors": errors}, code=207)
        return success_response({"uploaded": results}, code=201)

class FileListView(APIView):
    @require_auth
    @require_role("user")
    def get(self, request, conversation_id):
        service = FileService()
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 20))
        files, total = service.get_files(conversation_id, request.user_id, skip, limit)
        data = [{"id": f.id, "file_name": f.file_name, "file_size": f.file_size, "file_type": f.file_type, "scope": f.scope} for f in files]
        return success_response({"items": data, "total": total})

class FileDeleteView(APIView):
    @require_auth
    @require_role("user")
    def delete(self, request, conversation_id, file_id):
        service = FileService()
        try:
            service.delete_file(file_id, request.user_id)
            return success_response(code=204)
        except PermissionError:
            return error_response({"error": "Access denied"}, code=403)

class ClearFilesView(APIView):
    @require_auth
    @require_role("user")
    def delete(self, request, conversation_id):
        service = FileService()
        try:
            service.clear_all_files(conversation_id, request.user_id)
            return success_response(code=204)
        except PermissionError:
            return error_response({"error": "Access denied"}, code=403)