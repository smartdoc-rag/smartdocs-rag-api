from src.core.auth import require_auth
from rest_framework.views import APIView
from src.api._helper import validate_request
from src.api.deps import department_service
from src.api.department.DepartmentRequest import DepartmentRequest
from src.api.department.DepartmentResponse import DepartmentResponse
from src.core.response import (
    created_response,
    deleted_response,
    fetched_response,
    updated_response,
)


class DepartmentView(APIView):
    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        result = department_service().get_all(page, page_size)
        return fetched_response(
            data=DepartmentResponse.from_list(result["items"]), meta=result["meta"]
        )

    @require_auth
    def post(self, request):
        validated_data = validate_request(DepartmentRequest, request.data)
        department = department_service().create(**validated_data)
        return created_response(data=DepartmentResponse.from_model(department))


class DepartmentDetail(APIView):
    @require_auth
    def get(self, request, department_id: int):
        department, _ = department_service().get_by_id(department_id)
        return fetched_response(data=DepartmentResponse.from_model(department))

    @require_auth
    def patch(self, request, department_id: int):
        validate_data = validate_request(DepartmentRequest, request.data)
        department = department_service().update(department_id, **validate_data)
        return updated_response(data=DepartmentResponse.from_model(department))

    @require_auth
    def delete(self, request, department_id: int):
        department_service().delete(department_id)
        return deleted_response()
