from functools import wraps
from src.core.exceptions import UnauthorizedException, ForbiddenException
from src.api.deps import user_service


def require_auth(view_func):
    """Decorator bảo vệ endpoint — throw 401 nếu chưa đăng nhập."""

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not getattr(request, "user_id", None):
            raise UnauthorizedException("Vui lòng đăng nhập để tiếp tục")
        # Fetch user object and attach to request
        user = user_service().get_me(request.user_id)
        request.user_obj = user
        return view_func(self, request, *args, **kwargs)

    return wrapper


def require_role(allowed_roles):
    """Decorator kiểm tra role của user.
    allowed_roles: list các role được phép, ví dụ ['admin'] hoặc ['user', 'admin']
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Ensure user is authenticated and user_obj exists
            if not hasattr(request, 'user_obj'):
                # Fallback: fetch user
                if not getattr(request, "user_id", None):
                    raise UnauthorizedException("Vui lòng đăng nhập để tiếp tục")
                user = user_service().get_me(request.user_id)
                request.user_obj = user
            # Check role
            if request.user_obj.role not in allowed_roles:
                raise ForbiddenException("Bạn không có quyền truy cập chức năng này")
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator
