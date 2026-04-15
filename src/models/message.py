from django.db import models
from src.models.base import TimestampModel
from src.models.conversation import Conversation
from src.models.user import User


class Message(TimestampModel):
    """
    Model lưu trữ từng message trong conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    content = models.TextField()
    role = models.CharField(
        max_length=20,
        choices=[
            ("user", "User"),
            ("assistant", "Assistant"),
            ("system", "System")
        ]
    )
    
    def __str__(self):
        return f"Message {self.id} - {self.role} - {self.content[:50]}..."
    
    class Meta:
        db_table = "messages"
        ordering = ["created_at"]