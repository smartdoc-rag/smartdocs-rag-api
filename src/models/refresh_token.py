from django.db import models
from django.utils import timezone
from .base import TimestampModel


class RefreshToken(TimestampModel):

    token = models.CharField(max_length=512, unique=True, db_index=True)
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    def is_valid(self) -> bool:
        return not self.is_revoked and self.expires_at > timezone.now()

    def __str__(self):
        return f"RefreshToken {self.id} for {self.user.email}"

    class Meta:
        db_table = "refresh_tokens"
