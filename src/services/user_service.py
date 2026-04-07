from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.core.exceptions import NotFoundException
from src.core.pagination import build_pagination_meta


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_me(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        return user

    def get_users(self, page: int = 1, page_size: int = 20) -> dict:
        items, total = self.user_repo.get_all(
            skip=(page - 1) * page_size, limit=page_size
        )
        return {
            "items": items,
            "meta": build_pagination_meta(page, page_size, total),
        }

    def update_user(self, user_id: int, full_name: str | None = None) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        if full_name is not None:
            user.full_name = full_name

    def delete_user(self, user_id: int) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        self.user_repo.delete(user_id)
