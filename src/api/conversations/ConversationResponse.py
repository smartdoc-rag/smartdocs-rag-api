from rest_framework import serializers


class _MessageInConversation(serializers.Serializer):
    id = serializers.IntegerField()
    content = serializers.CharField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()


class ConversationResponse(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(allow_null=True)
    user_id = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    messages = _MessageInConversation(many=True, required=False, default=[])

    @classmethod
    def from_model(cls, conversation) -> dict:
        return cls(conversation).data

    @classmethod
    def from_list(cls, conversations) -> list[dict]:
        return cls(conversations, many=True).data


class MessageResponse(serializers.Serializer):
    id = serializers.IntegerField()
    conversation_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    content = serializers.CharField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    @classmethod
    def from_model(cls, message) -> dict:
        return cls(message).data

    @classmethod
    def from_list(cls, messages) -> list[dict]:
        return cls(messages, many=True).data