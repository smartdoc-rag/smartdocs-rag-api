from django.db import models
from .base import TimestampModel


class ResponseMessage(TimestampModel):
    """Tin nhắn trả lời từ hệ thống"""

    request_message = models.OneToOneField(
        "RequestMessage",
        on_delete=models.CASCADE,
        related_name="response_message"
    )
    content = models.TextField()
    type = models.CharField(
        max_length=10,
        choices=[("rag", "RAG"), ("graphrag", "GraphRAG")],
        default="rag"
    )

    def __str__(self):
        return f"ResponseMessage {self.id} - {self.content[:50]}..."

    class Meta:
        db_table = "response_messages"