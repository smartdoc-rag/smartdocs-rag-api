from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from .base import TimestampModel


class User(TimestampModel):
    email = models.EmailField(unique=True, db_index=True, null=False)
    password_hash = models.CharField(max_length=255, null=False)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        db_table = "users"
