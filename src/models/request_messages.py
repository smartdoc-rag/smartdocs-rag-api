from django.db import models
from .base import TimestampModel


class RequestMessage(TimestampModel):
    """Tin nhắn từ người dùng (câu hỏi)"""

    conversation = models.ForeignKey(
        "Conversation",
        on_delete=models.CASCADE,
        related_name="request_messages"
    )
    content = models.TextField()

    def __str__(self):
        return f"RequestMessage {self.id} - {self.content[:50]}..."

    class Meta:
        db_table = "request_messages"