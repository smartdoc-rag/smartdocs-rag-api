from django.db import models
from .base import TimestampModel


class File(TimestampModel):
    """File tài liệu"""

    conversation = models.ForeignKey(
        "Conversation",
        on_delete=models.CASCADE,
        related_name="files",
        null=False
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField()
    file_type = models.CharField(
        max_length=10,
        choices=[("pdf", "PDF"), ("docx", "DOCX")]
    )
    scope = models.CharField(
        max_length=10,
        choices=[("public", "Public"), ("private", "Private")],
        default="private"
    )

    def __str__(self):
        return f"File {self.id} - {self.file_name}"

    class Meta:
        db_table = "files"