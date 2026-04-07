from rest_framework import serializers
from src.core.serializers import CustomSerializer


class RegisterRequest(CustomSerializer, serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=100)
