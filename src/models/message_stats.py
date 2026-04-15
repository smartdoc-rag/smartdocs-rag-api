from django.db import models
from .base import TimestampModel


class MessageStat(TimestampModel):
    """Thống kê cho tin nhắn trả lời"""

    message = models.OneToOneField(
        "ResponseMessage",
        on_delete=models.CASCADE,
        related_name="stat"
    )
    word_count = models.IntegerField(default=0)

    def __str__(self):
        return f"MessageStat {self.id} - {self.word_count} words"

    class Meta:
        db_table = "message_stats"