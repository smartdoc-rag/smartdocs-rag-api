from rest_framework import serializers
from core.serializers import ViSerializerMixin


class CreateConversationRequest(ViSerializerMixin, serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)


class UpdateConversationRequest(ViSerializerMixin, serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)


class AddMessageRequest(ViSerializerMixin, serializers.Serializer):
    content = serializers.CharField(required=True)
    role = serializers.CharField(
        required=False,
        default="user",
        choices=["user", "assistant", "system"]
    )