from rest_framework import serializers
from src.core.serializers import CustomSerializer


class UpdateUserRequest(CustomSerializer, serializers.Serializer):
    full_name = serializers.CharField(max_length=100, required=False)
