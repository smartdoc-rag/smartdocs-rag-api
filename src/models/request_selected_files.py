from django.db import models
from .base import TimestampModel


class RequestSelectedFile(TimestampModel):
    """File được chọn cho request message"""

    file = models.ForeignKey(
        "File",
        on_delete=models.CASCADE,
        related_name="selected_for_requests",
        null=False
    )
    request_message = models.ForeignKey(
        "RequestMessage",
        on_delete=models.CASCADE,
        related_name="selected_files",
        null=False
    )

    def __str__(self):
        return f"RequestSelectedFile {self.id} - File {self.file.id} for Request {self.request_message.id}"

    class Meta:
        db_table = "request_selected_files"
        constraints = [
            models.UniqueConstraint(
                fields=['request_message', 'file'],
                name='unique_request_file'
            )
        ]