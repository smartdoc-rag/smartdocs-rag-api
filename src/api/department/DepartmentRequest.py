from rest_framework import serializers
from src.core.serializers import CustomSerializer


class DepartmentRequest(CustomSerializer, serializers.Serializer):
    name = serializers.CharField(max_length=255)
