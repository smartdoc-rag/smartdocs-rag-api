from rest_framework import status
from src.core.response import error_response
from rest_framework.views import exception_handler as drf_exception_handler


class BaseException(Exception):
    """Base exception — mọi custom exception kế thừa lớp này."""

    code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Lỗi hệ thống"

    def __init__(self, message: str | None = None, errors=None):
        self.message = message or self.message
        self.errors = errors
        super().__init__(self.message)


class BadRequestException(BaseException):
    code = status.HTTP_400_BAD_REQUEST
    message = "Yêu cầu không hợp lệ"


class UnauthorizedException(BaseException):
    code = status.HTTP_401_UNAUTHORIZED
    message = "Chưa xác thực"


class ForbiddenException(BaseException):
    code = status.HTTP_403_FORBIDDEN
    message = "Không có quyền truy cập"


class NotFoundException(BaseException):
    code = status.HTTP_404_NOT_FOUND
    message = "Không tìm thấy đường dẫn"


class ValidationException(BaseException):
    code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Dữ liệu không hợp lệ"


class ThrottleException(BaseException):
    code = status.HTTP_429_TOO_MANY_REQUESTS
    message = "Quá nhiều yêu cầu, vui lòng thử lại sau"


def global_exception_handler(exc, context):
    """Hàm xử lý ngoại lệ toàn cục."""
    if isinstance(exc, BaseException):
        return error_response(message=exc.message, errors=exc.errors, code=exc.code)

    if isinstance(exc, ValueError):
        return error_response(
            message=str(exc) or "Giá trị không hợp lệ",
            code=status.HTTP_400_BAD_REQUEST,
        )

    errorSystem = drf_exception_handler(exc, context)
    if errorSystem is not None:
        return error_response(
            message=errorSystem.data.get("detail", "Lỗi hệ thống"),
            errors=errorSystem.data,
            code=errorSystem.status_code,
        )

    return error_response(
        message="Lỗi hệ thống", code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
