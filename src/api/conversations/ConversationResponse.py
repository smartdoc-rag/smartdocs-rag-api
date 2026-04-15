from rest_framework import serializers
from datetime import datetime


class _MessageResponse(serializers.Serializer):
    """Response cho một message."""
    id = serializers.IntegerField()
    content = serializers.CharField()
    is_from_user = serializers.BooleanField()
    metadata = serializers.JSONField(default=dict)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ConversationResponse(serializers.Serializer):
    """Response cho một conversation."""
    id = serializers.IntegerField()
    title = serializers.CharField(allow_null=True)
    user_id = serializers.IntegerField()
    document_id = serializers.IntegerField(allow_null=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    messages = _MessageResponse(many=True, required=False, default=[])

    @classmethod
    def from_model(cls, conversation) -> dict:
        """Convert Conversation model thành dict response."""
        return cls(conversation).data

    @classmethod
    def from_list(cls, conversations) -> list[dict]:
        """Convert list Conversation models thành list dict response."""
        return cls(conversations, many=True).data


class ConversationListResponse(serializers.Serializer):
    """Response cho danh sách conversations."""
    id = serializers.IntegerField()
    title = serializers.CharField(allow_null=True)
    user_id = serializers.IntegerField()
    document_id = serializers.IntegerField(allow_null=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    message_count = serializers.IntegerField(required=False)
    last_message = serializers.CharField(required=False, allow_null=True)

    @classmethod
    def from_model(cls, conversation, message_count: int = 0, last_message: str = None) -> dict:
        """Convert Conversation model với thông tin bổ sung."""
        data = cls(conversation).data
        data["message_count"] = message_count
        data["last_message"] = last_message
        return data