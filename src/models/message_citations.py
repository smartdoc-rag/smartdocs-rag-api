from django.db import models
from .base import TimestampModel


class MessageCitation(TimestampModel):
    """Trích dẫn từ file cho tin nhắn trả lời"""

    file = models.ForeignKey(
        "File",
        on_delete=models.CASCADE,
        related_name="citations",
        null=True,
        blank=True
    )
    response_message = models.ForeignKey(
        "ResponseMessage",
        on_delete=models.CASCADE,
        related_name="citations",
        null=False
    )
    page_number = models.IntegerField(null=True, blank=True)
    content_chunk = models.TextField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    start_line = models.IntegerField(null=True, blank=True)
    end_line = models.IntegerField(null=True, blank=True)
    citation_marker = models.TextField(blank=True, help_text="Ví dụ: 【1†L5-L8】")

    #Các trường cho GraphRAG
    graph_entity_id = models.TextField(null=True, blank=True)
    graph_entity_name = models.TextField(null=True, blank=True)
    graph_entity_type = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Citation {self.id} - Page {self.page_number}"

    class Meta:
        db_table = "message_citations"