from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.repositories.user_repository import UserRepository
from src.repositories.token_repository import TokenRepository


def auth_service() -> AuthService:
    return AuthService(user_repo=UserRepository(), token_repo=TokenRepository())


def user_service() -> UserService:
    return UserService(user_repo=UserRepository())
