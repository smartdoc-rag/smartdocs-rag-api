from rest_framework.views import APIView
from src.core.response import error_response, success_response
from src.core.auth import require_auth, require_role
from src.core.pagination import PaginationParams, build_pagination_meta
from src.api.deps import chat_service


class ChatAskView(APIView):
    @require_auth
    @require_role("user")
    def post(self, request, conversation_id):
        question = request.data.get("question")
        if not question:
            return error_response(
                {"error": "Tham số truyền vào không hợp lệ"}, code=400
            )

        search_type = request.data.get("search_type", "vector")
        selected_file_ids = request.data.get("selected_file_ids", [])
        response_type = request.data.get("response_type", "rag")
        use_reranking = request.data.get("use_reranking", False)
        top_k = request.data.get("top_k", 5)
        use_self_rag = request.data.get("use_self_rag", False)
        try:
            result = chat_service().ask(
                conversation_id,
                request.user_id,
                question,
                selected_file_ids=selected_file_ids,
                response_type=response_type,
                search_type=search_type,
                use_reranking=use_reranking,
                top_k=top_k,
                use_self_rag=use_self_rag,
            )
            return success_response(result, code=200)
        except PermissionError as e:
            return error_response({"error": str(e)}, code=403)
        except Exception as e:
            return error_response({"error": str(e)}, code=500)


class ChatHistoryView(APIView):
    @require_auth
    @require_role("user")
    def get(self, request, conversation_id):
        params = PaginationParams.from_request(request, default_page_size=20)
        history, total = chat_service().get_history(
            conversation_id, request.user_id, params.skip, params.limit
        )
        return success_response(
            data={"history": history},
            meta=build_pagination_meta(params.page, params.page_size, total),
            code=200,
        )


class ClearHistoryView(APIView):
    @require_auth
    @require_role("user")
    def delete(self, request, conversation_id):
        chat_service().clear_history(conversation_id, request.user_id)
        return success_response(code=204)
