from datetime import datetime, timedelta, timezone
import jwt
import secrets
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from src.models.user import User
from src.models.refresh_token import RefreshToken
from src.repositories.user_repository import UserRepository
from src.repositories.token_repository import TokenRepository
from src.core.exceptions import (
    UnauthorizedException,
    BadRequestException,
    NotFoundException,
    ForbiddenException,
)


class AuthService:
    def __init__(self, user_repo: UserRepository, token_repo: TokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    def _hash_password(self, password: str) -> str:
        return make_password(password)

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return check_password(password, hashed_password)

    def _create_access_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        return jwt.encode(
            {"user_id": user_id, "exp": expire}, settings.SECRET_KEY, algorithm="HS256"
        )

    def _create_raw_refresh(self) -> str:
        return secrets.token_urlsafe(64)

    def register(self, data: dict[str, str]) -> User:
        if self.user_repo.exists(email=data["email"]):
            raise BadRequestException("Email đã được sử dụng")
        return self.user_repo.create(
            User(
                email=data["email"],
                hashed_password=self._hash_password(data["password"]),
                full_name=data["full_name"],
            )
        )

    def login(self, data: dict[str, str]) -> dict:
        user = self.user_repo.get_by_email(data["email"])
        if not user or not self._verify_password(
            data["password"], user.hashed_password
        ):
            raise UnauthorizedException("Tài khoản hoặc mật khẩu không đúng")

        if not user.is_active:
            raise ForbiddenException("Tài khoản của bạn bị vô hiệu hóa")

        raw_refresh = self._create_raw_refresh()
        self.token_repo.create(
            RefreshToken(
                token=raw_refresh,
                user_id=user.id,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )

        return {
            "access_token": self._create_access_token(user.id),
            "refresh_token": raw_refresh,
            "user": user,
        }

    def refresh_access_token(self, raw_refresh: str) -> dict:
        token_obj = self.token_repo.get_valid_token(raw_refresh)
        if not token_obj:
            raise UnauthorizedException("Refresh token không hợp lệ hoặc đã hết hạn")

        self.token_repo.revoke_token(token_obj)
        new_raw = self._create_raw_refresh()
        self.token_repo.create(
            RefreshToken(
                token=new_raw,
                user_id=token_obj.user_id,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )
        return {
            "access_token": self._create_access_token(token_obj.user_id),
            "refresh_token": new_raw,
        }

    def logout(self, raw_refresh: str) -> None:
        token_obj = self.token_repo.get_valid_token(raw_refresh)
        if token_obj:
            self.token_repo.revoke_token(token_obj)

    def reset_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        if not self._verify_password(old_password, user.hashed_password):
            raise BadRequestException("Mật khẩu hiện tại không đúng")
        user.hashed_password = self._hash_password(new_password)
        self.user_repo.update(user)
