from src.models.refresh_token import RefreshToken
from src.repositories.base import BaseRepository


class TokenRepository(BaseRepository[RefreshToken]):
    model_class = RefreshToken

    def get_valid_token(self, token: str) -> RefreshToken | None:
        token_obj = self.model_class.objects.filter(token=token).first()
        if token_obj and token_obj.is_valid():
            return token_obj
        return None

    def revoke_token(self, token_obj: RefreshToken) -> None:
        token_obj.is_revoked = True
        token_obj.save()

    def revoke_all_user_tokens(self, user_id: int) -> None:
        RefreshToken.objects.filter(
            user_id=user_id,
            is_revoked=False,
        ).update(is_revoked=True)
