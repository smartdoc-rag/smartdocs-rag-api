from rest_framework import serializers
from src.core.serializers import CustomSerializer


class ResetPasswordRequest(CustomSerializer, serializers.Serializer):
    old_password = serializers.CharField(min_length=8, write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)
