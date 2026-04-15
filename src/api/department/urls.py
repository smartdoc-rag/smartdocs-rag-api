from django.urls import path
from src.api.department.views import DepartmentDetail

urlpatterns = [
    path("<int:department_id>", DepartmentDetail.as_view()),
]
