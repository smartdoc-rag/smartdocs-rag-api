from src.models.user import User
from src.models.department import Department
from src.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    model_class = Department
