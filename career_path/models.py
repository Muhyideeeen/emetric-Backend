import uuid
from django.core.cache import cache
from django.db import models


class CareerPathManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)
        cache.delete("career_path_queryset")
        return result


class CareerPath(models.Model):

    career_path_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    name = models.CharField(
        max_length=128, unique=True, db_index=True, blank=True, null=True
    )
    level = models.PositiveIntegerField(
        unique=True, db_index=True, blank=True, null=True
    )
    educational_qualification = models.CharField(max_length=255, db_index=True)
    years_of_experience_required = models.IntegerField(
        db_index=True, blank=True, null=True
    )
    min_age = models.IntegerField(db_index=True)
    max_age = models.IntegerField(db_index=True)
    position_lifespan = models.IntegerField(db_index=True)
    slots_available = models.IntegerField(db_index=True, default=1)
    annual_package = models.IntegerField(db_index=True, default=1)

    objects = CareerPathManager()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name}"
