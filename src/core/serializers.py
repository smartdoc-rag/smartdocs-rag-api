from rest_framework.fields import (
    EmailField,
    IntegerField,
    FloatField,
    CharField,
    BooleanField,
)

_CUSTOM_MESSAGE: dict[str, str] = {
    "required": "Trường này là bắt buộc.",
    "blank": "Trường này không được để trống.",
    "null": "Trường này không được để trống.",
    "invalid": "Giá trị không hợp lệ.",
    "invalid_choice": "Lựa chọn không hợp lệ.",
    "max_length": "Không được vượt quá {max_length} ký tự.",
    "min_length": "Phải có ít nhất {min_length} ký tự.",
    "max_value": "Giá trị không được lớn hơn {max_value}.",
    "min_value": "Giá trị không được nhỏ hơn {min_value}.",
    "max_string_length": "Chuỗi quá dài.",
    "does_not_exist": "Không tìm thấy dữ liệu tương ứng.",
    "incorrect_type": "Kiểu dữ liệu không chính xác.",
    "unique": "Giá trị này đã tồn tại.",
}

_MESSAGES_BY_TYPE: dict[type, dict[str, str]] = {
    EmailField: {"invalid": "Vui lòng nhập địa chỉ email hợp lệ."},
    IntegerField: {"invalid": "Vui lòng nhập số nguyên hợp lệ."},
    FloatField: {"invalid": "Vui lòng nhập số thực hợp lệ."},
    CharField: {"blank": "Trường này không được để trống."},
    BooleanField: {"invalid": "Vui lòng nhập giá trị đúng hoặc sai."},
}


class CustomSerializer:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            for code, msg in _CUSTOM_MESSAGE.items():
                if code in field.error_messages:
                    field.error_messages[code] = msg
            for field_type, messages in _MESSAGES_BY_TYPE.items():
                if isinstance(field, field_type):
                    for code, msg in messages.items():
                        field.error_messages[code] = msg

            for validator in getattr(field, "validators", []):
                code = getattr(validator, "code", None)
                if code in _CUSTOM_MESSAGE:
                    if hasattr(validator, "limit_value"):
                        validator.message = _CUSTOM_MESSAGE[code].format(
                            **{code: validator.limit_value}
                        )
                    else:
                        validator.message = _CUSTOM_MESSAGE[code]

                for field_type, messages in _MESSAGES_BY_TYPE.items():
                    if isinstance(field, field_type) and code in messages:
                        validator.message = messages[code]
