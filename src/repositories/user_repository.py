from src.models.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model_class = User

    def get_by_email(self, email: str) -> User | None:
        return self.get_one(email=email)
