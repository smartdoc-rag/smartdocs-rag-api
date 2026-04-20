import jwt
import logging
from django.conf import settings
from src.core.response import error_response

logger = logging.getLogger(__name__)


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
            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                request.user_id = payload.get("user_id")
            except jwt.ExpiredSignatureError:
                logger.warning(f"[JWT] Token EXPIRED for path={request.path}")
            except jwt.InvalidTokenError as e:
                logger.warning(f"[JWT] Token INVALID: {e} for path={request.path}")
        else:
            logger.debug(
                f"[JWT] No Bearer header found. Keys: {[k for k in request.META if 'AUTH' in k]}"
            )

        return self.get_response(request)
