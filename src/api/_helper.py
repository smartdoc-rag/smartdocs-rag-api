import json
from src.core.exceptions import ValidationException


def validate_request(request_class, data: dict) -> dict:
    """
    Validate data qua request_class (ViSerializerMixin + Serializer).
    Throw ValidationException với list lỗi theo field nếu không hợp lệ.
    Dùng chung cho mọi view — không lặp lại.
    """
    s = request_class(data=data)
    if not s.is_valid():
        errors = [
            {"field": field, "message": msgs[0]} for field, msgs in s.errors.items()
        ]
        raise ValidationException(errors=errors)
    return s.validated_data

def get_body(request) -> dict:
    """
    Hàm hỗ trợ lấy body từ request. Mặc định xử lý JSON.
    Nếu body rỗng hoặc lỗi parse, trả về dict rỗng.
    """
    try:
        if request.body:
            return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return {}
