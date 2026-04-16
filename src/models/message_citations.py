from django.db import models
from .base import TimestampModel


class MessageCitation(TimestampModel):
    """Trích dẫn từ file cho tin nhắn trả lời"""

    file = models.ForeignKey(
        "File",
        on_delete=models.CASCADE,
        related_name="citations",
        null=False
    )
    response_message = models.ForeignKey(
        "ResponseMessage",
        on_delete=models.CASCADE,
        related_name="citations",
        null=False
    )
    page_number = models.IntegerField()
    content_chunk = models.TextField()
    relevance_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Citation {self.id} - Page {self.page_number}"

    class Meta:
        db_table = "message_citations"