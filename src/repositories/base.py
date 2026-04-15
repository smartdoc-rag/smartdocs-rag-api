from typing import Generic, TypeVar, Type
from django.db import models

ModelType = TypeVar("ModelType", bound=models.Model)


class BaseRepository(Generic[ModelType]):
    model_class: Type[ModelType]

    def __init__(self):
        pass

    def get_one(self, **filters) -> ModelType | None:
        return self.model_class.objects.filter(**filters).first()

    def get_by_id(self, id: int) -> ModelType | None:
        return self.get_one(id=id)

    def get_all(
        self, skip: int = 0, limit: int = 20, **filters
    ) -> tuple[list[ModelType], int]:
        queryset = self.model_class.objects.filter(**filters).all()
        total = queryset.count()
        items = list(queryset[skip : skip + limit])
        return items, total

    def exists(self, **filters) -> bool:
        return self.model_class.objects.filter(**filters).exists()

    def create(self, obj: ModelType) -> ModelType:
        obj.save()
        return obj

    def update(self, obj: ModelType) -> ModelType:
        obj.save()
        return obj

    def delete(self, obj: ModelType) -> None:
        obj.delete()
