from django.db import models
from src.models.base import TimestampModel


class ConversationMessage(TimestampModel):
    """
    Tin nhắn trong một conversation.
    Mỗi message thuộc về một conversation và có thể là từ user hoặc AI.
    """
    conversation = models.ForeignKey(
        "Conversation",  # String reference to avoid circular import
        on_delete=models.CASCADE,
        related_name="messages"
    )
    content = models.TextField()
    is_from_user = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)  # Lưu thông tin bổ sung như citations, sources

    def __str__(self):
        sender = "User" if self.is_from_user else "AI"
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{sender}: {preview}"

    class Meta:
        db_table = "conversation_messages"
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]
        ordering = ["created_at"]