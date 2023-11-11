from django.db import models


class BaseModel(models.Model):
    name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True, unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering = ["-id"]
        abstract = True

    def __str__(self):
        return f"{self.name}"
