from rest_framework.response import Response


def success_response(data=None, message="Thành công", code=200, meta=None) -> Response:
    return Response(
        {"success": True, "code": code, "message": message, "data": data, "meta": meta},
        status=code,
    )


def error_response(message="Lỗi", code=400, errors=None) -> Response:
    return Response(
        {"success": False, "code": code, "message": message, "errors": errors},
        status=code,
    )


def created_response(data=None, message="Tạo mới thành công", meta=None) -> Response:
    return success_response(data=data, message=message, code=201, meta=meta)


def fetched_response(
    data=None, message="Lấy dữ liệu thành công", meta=None
) -> Response:
    return success_response(data=data, message=message, code=200, meta=meta)


def updated_response(data=None, message="Cập nhật thành công", meta=None) -> Response:
    return success_response(data=data, message=message, code=200, meta=meta)


def deleted_response(message="Xóa thành công") -> Response:
    return success_response(data=None, message=message, code=204)
