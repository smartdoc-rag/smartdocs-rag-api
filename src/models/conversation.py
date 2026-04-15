from django.db import models
from src.models.base import TimestampModel
from src.models.user import User


class Conversation(TimestampModel):
    """
    Model lưu trữ hội thoại giữa người dùng và hệ thống.
    Mỗi conversation có thể có nhiều message.
    """
    title = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Conversation {self.id} - {self.title or 'No title'}"
    
    class Meta:
        db_table = "conversations"
        ordering = ["-created_at"]