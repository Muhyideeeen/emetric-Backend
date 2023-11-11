from decimal import Decimal
import uuid
import json

from datetime import datetime
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, models
from django_celery_beat.models import ClockedSchedule, PeriodicTask

from core.utils.process_durations import get_localized_time
from organization.models import CorporateLevel

User = get_user_model()


class ObjectiveManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)
        cache.delete("objective_queryset")
        # manually send signals for objectives
        for obj in objs:
            obj.create_change_to_active_task()
            obj.create_change_to_closed_task()
        return result


class Objective(models.Model):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    YEARLY = "yearly"
    ONCE = "once"

    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"

    ROUTINE_TYPE_CHOICES = (
        (MONTHLY, "Monthly"),
        (QUARTERLY, "Quarterly"),
        (HALF_YEARLY, "Half Yearly"),
        (YEARLY, "Yearly"),
        (ONCE, "Once"),
    )

    OBJECTIVE_STATUS_CHOICES = (
        (PENDING, "pending"),
        (ACTIVE, "active"),
        (CLOSED, "closed"),
    )

    name = models.CharField(max_length=255, db_index=True)
    corporate_level = models.ForeignKey(
        CorporateLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="corporate_level_objective",
    )
    objective_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    objective_status = models.CharField(
        max_length=255,
        choices=OBJECTIVE_STATUS_CHOICES,
        default=PENDING,
        db_index=True,
    )
    routine_option = models.CharField(
        max_length=255, choices=ROUTINE_TYPE_CHOICES
    )
    routine_round = models.PositiveIntegerField(default=1)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    after_occurrence = models.PositiveSmallIntegerField(null=True, blank=True)

    target_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ObjectiveManager()

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Objective, self).save(*args, **kwargs)

    class Meta:
        ordering = ["start_date", "-id"]

    def __str__(self):
        return self.name

    def create_change_to_active_task(self):
        """create a periodic task that changes objective to active at start time"""
        tenant = connection.tenant
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.start_date, datetime.min.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"{str(self.objective_id)} active",  # task name
            task="strategy_deck.tasks.objective.change_objective_status_to_active",  # task.
            args=json.dumps(
                [
                    self.id,
                ]
            ),  # arguments
            description="this changes the objective status to active at start time",
            one_off=True,
            headers=json.dumps(
                {
                    "_schema_name": tenant.schema_name,
                    "_use_tenant_timezone": True,
                }
            ),
        )

    def modify_change_to_active_task(self):
        """Modifies a periodic task that changes objective to active at start time"""
        tenant = connection.tenant
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.start_date, datetime.min.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.filter(
            name=f"{str(self.objective_id)} active"
        ).update(clocked=clocked)

    def create_change_to_closed_task(self):
        """create a periodic task that changes objective to closed at end time"""
        tenant = connection.tenant

        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.end_date, datetime.max.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"{str(self.objective_id)} closed",  # task name
            task="strategy_deck.tasks.objective.change_objective_status_to_closed",
            args=json.dumps(
                [
                    self.id,
                ]
            ),  # arguments
            description="this changes the objective status to over due at end time time",
            one_off=True,
            headers=json.dumps(
                {
                    "_schema_name": tenant.schema_name,
                    "_use_tenant_timezone": True,
                }
            ),
        )

    def modify_change_to_closed_task(self):
        """Modifies a periodic task that changes objective to closed at end time"""
        tenant = connection.tenant

        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.end_date, datetime.max.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.filter(
            name=f"{str(self.objective_id)} closed"
        ).update(clocked=clocked)

    def update_target_point(self, point: Decimal):
        """Updates objective target point based on downline change"""
        self.target_point += Decimal(point)
        self.save()
     
