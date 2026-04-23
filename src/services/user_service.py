from typing import Tuple, List
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.core.exceptions import NotFoundException, ForbiddenException


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_me(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        return user

    def get_all(self, skip: int = 0, limit: int = 20) -> Tuple[List[User], int]:
        return self.user_repo.get_all(skip=skip, limit=limit)

    def update_user(self, user_id: int, full_name: str | None = None) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        if full_name is not None:
            user.full_name = full_name
        self.user_repo.update(user)
        return user

    def delete_user(self, user_id: int) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        self.user_repo.delete(user)

    def block_user(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        if user.role == "admin":
            raise ForbiddenException("Không thể khóa tài khoản admin")
        user.is_active = False
        self.user_repo.update(user)
        return user
