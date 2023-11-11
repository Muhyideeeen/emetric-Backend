import uuid
from django.core.cache import cache
from django.db import models

from core.models import BaseModel
from employee.models import Employee
from organization.models import (
    Unit,
    Department,
    Group,
    Division,
    CorporateLevel,
)


class DesignationManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)
        cache.delete("designation_queryset")
        return result


class Designation(BaseModel):
    designation_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )

    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, null=True, blank=True
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, null=True, blank=True
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, null=True, blank=True
    )
    division = models.ForeignKey(
        Division, on_delete=models.CASCADE, null=True, blank=True
    )
    corporate_level = models.ForeignKey(
        CorporateLevel, on_delete=models.CASCADE, null=True, blank=True
    )

    objects = DesignationManager()

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name}"
