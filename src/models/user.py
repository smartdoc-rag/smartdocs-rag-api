from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from .base import TimestampModel


class User(TimestampModel):
    email = models.EmailField(unique=True, db_index=True)
    hashed_password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'User')], default='user')

    def set_password(self, raw_password):
        self.hashed_password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.hashed_password)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        db_table = "users"
