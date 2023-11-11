import uuid

from django.contrib.auth import get_user_model
from django.db import models

from strategy_deck.models.perspective import Perspective
from strategy_deck.models.objective import Objective

User = get_user_model()


class ObjectivePerspectiveSpread(models.Model):
    objective_perspective_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        db_index=True,
        to_field="objective_id",
        blank=True,
        null=True,
        related_name="objective_objective_perspective_spread",
    )
    perspective = models.ForeignKey(
        Perspective,
        on_delete=models.CASCADE,
        db_index=True,
        to_field="perspective_id",
        blank=True,
        null=True,
        related_name="perspective_objective_perspective_spread",
    )
    relative_point = models.DecimalField(decimal_places=2, max_digits=18)
    objective_perspective_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.objective_perspective_id
