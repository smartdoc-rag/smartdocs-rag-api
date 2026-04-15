from django.db import models
from src.models.base import TimestampModel
from src.models.user import User


class Document(TimestampModel):
    """
    Tài liệu được upload bởi người dùng.
    """
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)  # Đường dẫn file trên server
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # Kích thước file tính bằng bytes
    file_type = models.CharField(max_length=50)  # pdf, docx, txt, etc.
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    is_processed = models.BooleanField(default=False)  # Đã được xử lý embedding chưa
    metadata = models.JSONField(default=dict, blank=True)  # Thông tin bổ sung

    def __str__(self):
        return f"{self.title} ({self.file_type})"

    class Meta:
        db_table = "documents"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["is_processed"]),
        ]