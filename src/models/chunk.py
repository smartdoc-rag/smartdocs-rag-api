from django.db import models
from .base import TimestampModel

class Chunk(TimestampModel):
    conversation = models.ForeignKey("Conversation", on_delete=models.CASCADE, related_name="chunks")
    file = models.ForeignKey("File", on_delete=models.CASCADE, related_name="chunks")
    text = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    start_index = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict)  # lưu thêm các metadata khác

    class Meta:
        db_table = "chunks"