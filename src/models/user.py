from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from .base import TimestampModel


class User(TimestampModel):
    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    role = models.CharField(
        max_length=20,
        choices=[("user", "User"), ("manager", "Manager"), ("admin", "Admin")],
        default="user"
    )
    department = models.ForeignKey(
        "Department",
        on_delete=models.CASCADE,
        related_name="users",
    )

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        db_table = "users"
