from decimal import Decimal
import uuid
from django.core.cache import cache
from django.db import models


class PerspectiveManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)
        cache.delete("perspective_queryset")
        return result


class Perspective(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    perspective_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    target_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PerspectiveManager()

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Perspective, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name

    def update_target_point(self, point: Decimal):
        """Updates perspective target point based on downline change"""
        self.target_point += Decimal(point)
        self.save()
