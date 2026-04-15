from django.db import models
from src.models.base import TimestampModel


class Department(TimestampModel):
    """Phòng ban"""

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "departments"
