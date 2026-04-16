from django.db import models
from .base import TimestampModel


class ResponseMessage(TimestampModel):
    """Tin nhắn trả lời từ hệ thống"""

    request_message = models.ForeignKey(
        "RequestMessage",
        on_delete=models.CASCADE,
        related_name="response_messages",
        null=False
    )
    content = models.TextField(null=False)
    type = models.CharField(
        max_length=10,
        choices=[("rag", "RAG"), ("graphrag", "GraphRAG")],
        default="rag",
        null=False
    )

    def __str__(self):
        return f"ResponseMessage {self.id} - {self.content[:50]}..."

    class Meta:
        db_table = "response_messages"