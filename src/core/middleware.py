import jwt
from django.conf import settings


class JWTAuthMiddleware:
    """
    Đọc Access Token từ header: Authorization: Bearer <token>.
    Inject request.user_id nếu hợp lệ, None nếu không.
    Không throw lỗi tại đây — để view tự kiểm tra qua @require_auth.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id = None
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                request.user_id = payload.get("user_id")
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass
        return self.get_response(request)
