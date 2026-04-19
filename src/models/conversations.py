from django.db import models
from .base import TimestampModel


class Conversation(TimestampModel):
    """Cuộc hội thoại giữa người dùng và hệ thống"""

    title = models.CharField(max_length=255, blank=True, null=True)
    chunk_size = models.IntegerField(default=1500)
    chunk_overlap = models.IntegerField(default=200)
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    last_chat_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Conversation {self.id} - {self.title or 'No title'}"

    class Meta:
        db_table = "conversations"