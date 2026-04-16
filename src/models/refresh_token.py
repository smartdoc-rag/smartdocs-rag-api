from django.db import models
from django.utils import timezone
from .base import TimestampModel


class RefreshToken(TimestampModel):
    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, related_name="refresh_token", null=False
    )
    token = models.CharField(max_length=512, null=False)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    def is_valid(self) -> bool:
        return not self.is_revoked and self.expires_at > timezone.now()

    def __str__(self):
        return f"RefreshToken {self.id} for {self.user.email}"

    class Meta:
        db_table = "refresh_tokens"
