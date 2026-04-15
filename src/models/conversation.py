from django.db import models
from src.models.base import TimestampModel
from src.models.user import User
from src.models.document import Document


class Conversation(TimestampModel):
    """
    Hội thoại giữa người dùng và AI.
    Mỗi conversation thuộc về một user và có thể liên kết với một document.
    """
    title = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Conversation {self.id} - {self.title or 'Untitled'}"

    class Meta:
        db_table = "conversations"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["is_active"]),
        ]