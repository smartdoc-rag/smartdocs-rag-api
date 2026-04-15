from src.models.user import User
from src.models.department import Department
from src.repositories.user_repository import UserRepository
from src.repositories.department_repository import DepartmentRepository
from src.core.exceptions import NotFoundException, BadRequestException
from src.core.pagination import build_pagination_meta


class DepartmentService:
    def __init__(
        self, department_repo: DepartmentRepository, user_repo: UserRepository
    ):
        self.department_repo = department_repo
        self.user_repo = user_repo

    def get_all(self, page: int = 1, page_size: int = 20) -> dict:
        item, total = self.department_repo.get_all(
            skip=(page - 1) * page_size, limit=page_size
        )
        return {"items": item, "meta": build_pagination_meta(page, page_size, total)}

    def get_by_id(
        self, department_id: int, related_load: bool = True
    ) -> tuple[Department, list[User]]:
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise NotFoundException("Không tìm thấy phòng ban")
        users, _ = (
            self.user_repo.get_all(department_id=department_id)
            if related_load
            else None
        )
        return department, users

    def create(self, name: str) -> Department:
        if self.department_repo.exists(name=name):
            raise BadRequestException(f"Phòng {name} đã tồn tại")
        return self.department_repo.create(Department(name=name))

    def update(self, department_id: int, name: str) -> Department:
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise NotFoundException(f"Không tìm thấy phòng {name}")
        if name == department.name:
            raise BadRequestException(f"Tên phòng mới trùng với tên phòng cũ")
        if self.department_repo.exists(name=name):
            raise BadRequestException(f"Phòng {name} đã tồn tại")
        department.name = name
        return self.department_repo.update(department)

    def delete(self, department_id: int) -> None:
        department = self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundException(f"Không tìm thấy phòng cần xóa")
        self.department_repo.delete(department)
