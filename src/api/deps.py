from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.department_service import DepartmentService
from src.repositories.user_repository import UserRepository
from src.repositories.token_repository import TokenRepository
from src.repositories.department_repository import DepartmentRepository


def auth_service() -> AuthService:
    return AuthService(user_repo=UserRepository(), token_repo=TokenRepository())


def user_service() -> UserService:
    return UserService(user_repo=UserRepository())


def department_service() -> DepartmentService:
    return DepartmentService(
        department_repo=DepartmentRepository(), user_repo=UserRepository()
    )
