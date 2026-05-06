from rest_framework.views import APIView
from src.api.user.UserRequest import UpdateUserRequest
from src.api.user.UserResponse import UserResponse
from src.api._helper import validate_request
from src.api.deps import user_service
from src.core.response import (
    fetched_response,
    updated_response,
    deleted_response,
    success_response,
)
from src.core.auth import require_auth, require_role
from src.core.pagination import PaginationParams, build_pagination_meta


class UserListView(APIView):
    @require_auth
    @require_role(["user"])
    def get(self, request):
        params = PaginationParams.from_request(request, default_page_size=20)
        items, total = user_service().get_all(skip=params.skip, limit=params.limit)
        return fetched_response(
            data=UserResponse.from_list(items),
            meta=build_pagination_meta(params.page, params.page_size, total),
        )


class UserDetailView(APIView):
    @require_auth
    @require_role(["user"])
    def get(self, request, user_id: int):
        user = user_service().get_me(user_id)
        return fetched_response(data=UserResponse.from_model(user))

    @require_auth
    @require_role(["user"])
    def patch(self, request, user_id: int):
        data = validate_request(UpdateUserRequest, request.data)
        user = user_service().update_user(user_id=user_id, **data)
        return updated_response(data=UserResponse.from_model(user))

    @require_auth
    @require_role(["user"])
    def delete(self, request, user_id: int):
        user_service().delete_user(user_id)
        return deleted_response()


class BlockUserView(APIView):
    @require_auth
    @require_role(["admin"])
    def post(self, request, user_id: int):
        # Toggle is_active or set to False? We'll set is_active=False
        user = user_service().block_user(user_id)
        return success_response(
            data=UserResponse.from_model(user),
            message=f"Đã khóa tài khoản người dùng {user.email}",
        )
