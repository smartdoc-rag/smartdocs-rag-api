from rest_framework.views import APIView
from src.api.deps import conversation_service
from src.core.response import success_response, error_response
from src.core.auth import require_auth, require_role


class ConversationCreateView(APIView):
    @require_auth
    @require_role(["user"])
    def post(self, request):
        title = request.data.get("title")
        conv = conversation_service().create_conversation(request.user_id, title)
        return success_response(
            {"id": conv.id, "title": conv.title, "created_at": conv.created_at},
            code=201,
        )


class ConversationListView(APIView):
    @require_auth
    @require_role(["user"])
    def get(self, request):
        skip = int(request.GET.get("skip", 0))
        limit = int(request.GET.get("limit", 20))
        convs, total = conversation_service().get_user_conversations(
            request.user_id, skip, limit
        )
        data = [
            {"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs
        ]
        return success_response({"items": data, "total": total})


class ConversationChunkConfigView(APIView):
    @require_auth
    @require_role(["user"])
    def patch(self, request, conversation_id):
        conv = conversation_service().get_conversation_by_id(
            conversation_id, request.user_id
        )

        chunk_size = request.data.get("chunk_size")
        chunk_overlap = request.data.get("chunk_overlap")

        if chunk_size is not None:
            if not isinstance(chunk_size, int) or chunk_size < 100:
                return error_response(
                    {"error": "chunk_size must be integer >= 100"}, code=400
                )
            conv.chunk_size = chunk_size
        if chunk_overlap is not None:
            if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
                return error_response(
                    {"error": "chunk_overlap must be integer >= 0"}, code=400
                )
            conv.chunk_overlap = chunk_overlap

        conv.save()
        return success_response(
            {
                "conversation_id": conv.id,
                "chunk_size": conv.chunk_size,
                "chunk_overlap": conv.chunk_overlap,
            }
        )


class ConversationUpdateView(APIView):
    @require_auth
    @require_role(["user"])
    def put(self, request, conversation_id):
        title = request.data.get("title")
        conv = conversation_service().update_conversation(
            request.user_id, conversation_id, title
        )
        return success_response(
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at,
                "last_chat_at": conv.last_chat_at,
            },
            status=200,
        )


class ConversationPatchView(APIView):
    @require_auth
    @require_role(["user"])
    def patch(self, request, conversation_id):
        conv = conversation_service().update_last_chat(request.user_id, conversation_id)
        return success_response(
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at,
                "last_chat_at": conv.last_chat_at,
            },
            status=200,
        )


class ConversationDeleteView(APIView):
    @require_auth
    @require_role(["user"])
    def delete(self, request, conversation_id):
        try:
            success = conversation_service().delete_conversation(
                request.user_id, conversation_id
            )

            if success:
                return success_response(
                    {
                        "message": "Xóa hội thoại thành công",
                        "conversation_id": conversation_id,
                    },
                    status=200,
                )
            else:
                return error_response(
                    {
                        "message": "Có lỗi xảy ra khi xóa hội thoại",
                        "conversation_id": conversation_id,
                    },
                    status=500,
                )

        except ValueError as e:
            return error_response(
                {"message": str(e), "conversation_id": conversation_id}, status=400
            )

        except Exception as e:
            return error_response(
                {
                    "message": "Đã xảy ra lỗi hệ thống",
                    "conversation_id": conversation_id,
                },
                status=500,
            )
