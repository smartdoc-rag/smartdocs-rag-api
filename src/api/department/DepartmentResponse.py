from rest_framework import serializers


class DepartmentResponse(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    @classmethod
    def from_model(cls, department) -> dict:
        return cls(instance=department).data

    @classmethod
    def from_list(cls, department) -> list[dict]:
        return cls(instance=department, many=True).data
