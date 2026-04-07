from functools import wraps
from src.core.exceptions import UnauthorizedException


def require_auth(view_func):
    """Decorator bảo vệ endpoint — throw 401 nếu chưa đăng nhập."""

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not getattr(request, "user_id", None):
            raise UnauthorizedException("Vui lòng đăng nhập để tiếp tục")
        return view_func(self, request, *args, **kwargs)

    return wrapper
