from rest_framework import serializers
from src.core.serializers import ViSerializerMixin


class CreateConversationRequest(ViSerializerMixin, serializers.Serializer):
    """Request tạo conversation mới."""
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    document_id = serializers.IntegerField(required=False, allow_null=True)


class UpdateConversationRequest(ViSerializerMixin, serializers.Serializer):
    """Request cập nhật conversation."""
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)


class AddMessageRequest(ViSerializerMixin, serializers.Serializer):
    """Request thêm message vào conversation."""
    content = serializers.CharField()
    is_from_user = serializers.BooleanField(default=True, required=False)
    metadata = serializers.JSONField(required=False, default=dict)