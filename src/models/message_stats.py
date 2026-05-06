from django.db import models
from .base import TimestampModel


class MessageStat(TimestampModel):
    """Thống kê cho tin nhắn trả lời"""

    message = models.ForeignKey(
        "ResponseMessage",
        on_delete=models.CASCADE,
        related_name="stats",
        null=False
    )
    word_count = models.IntegerField()

    def __str__(self):
        return f"MessageStat {self.id} - {self.word_count} words"

    class Meta:
        db_table = "message_stats"