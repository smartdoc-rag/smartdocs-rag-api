from rest_framework import serializers


class UserResponse(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    is_active = serializers.BooleanField()

    @classmethod
    def from_model(cls, user) -> dict:
        return cls(user).data

    @classmethod
    def from_list(cls, users) -> list[dict]:
        return cls(users, many=True).data
