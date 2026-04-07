from rest_framework.views import APIView
from src.api.user.UserRequest import UpdateUserRequest
from src.api.user.UserResponse import UserResponse
from src.api._helper import validate_request
from src.api.deps import user_service
from src.core.response import fetched_response, updated_response, deleted_response
from src.core.auth import require_auth


class UserListView(APIView):
    @require_auth
    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        result = user_service().get_users(page=page, page_size=page_size)
        return fetched_response(
            data=UserResponse.from_list(result["items"]),
            meta=result["meta"],
        )


class UserDetailView(APIView):
    @require_auth
    def get(self, request, user_id: int):
        user = user_service().get_me(user_id)
        return fetched_response(data=UserResponse.from_model(user))

    @require_auth
    def patch(self, request, user_id: int):
        data = validate_request(UpdateUserRequest, request.data)
        user = user_service().update_user(user_id=user_id, **data)
        return updated_response(data=UserResponse.from_model(user))

    @require_auth
    def delete(self, request, user_id: int):
        user_service().delete_user(user_id)
        return deleted_response()
