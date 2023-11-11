from decimal import Decimal
import uuid
import json

from celery import current_app
from datetime import datetime
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db import connection, models
from django_celery_beat.models import ClockedSchedule, PeriodicTask
from cloudinary_storage.storage import RawMediaCloudinaryStorage

from core.utils import Upload
from core.utils.process_durations import get_localized_time
from organization.models import (
    Unit,
    Department,
    Group,
    Division,
    CorporateLevel,
)
from strategy_deck.models.objective import Objective


User = get_user_model()
BASE_FILE_PATH = "initiative_brief/"


class InitiativeManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)
        cache.delete("initiative_queryset")
        # manually send signals for initiatives
        for obj in objs:
            obj.create_change_to_active_task()
            obj.create_change_to_closed_task()
        return result


class Initiative(models.Model):
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    YEARLY = "yearly"
    ONCE = "once"

    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"

    ROUTINE_TYPE_CHOICES = (
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (FORTNIGHTLY, "Fortnightly"),
        (MONTHLY, "Monthly"),
        (QUARTERLY, "Quarterly"),
        (HALF_YEARLY, "Half Yearly"),
        (YEARLY, "Yearly"),
        (ONCE, "Once"),
    )

    INITIATIVE_STATUS_CHOICES = (
        (PENDING, "pending"),
        (ACTIVE, "active"),
        (CLOSED, "closed"),
    )

    initiative_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    name = models.CharField(max_length=255, db_index=True)
    upline_objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        db_index=True,
        to_field="objective_id",
        blank=True,
        null=True,
        related_name="objective_initiative",
    )
    upline_initiative = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        db_index=True,
        to_field="initiative_id",
        blank=True,
        null=True,
        related_name="initiative_initiative",
    )

    # Teams
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="unit_initiative",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_initiative",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_initiative",
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="division_initiative",
    )
    corporate_level = models.ForeignKey(
        CorporateLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corporate_level_initiative",
    )

    assignor = models.ForeignKey(
        User,
        db_index=True,
        to_field="user_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assignor_initiative",
    )
    owner = models.ForeignKey(
        User,
        db_index=True,
        to_field="user_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owner_initiative",
    )

    routine_option = models.CharField(
        max_length=255, choices=ROUTINE_TYPE_CHOICES
    )
    routine_round = models.PositiveIntegerField(default=1)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    after_occurrence = models.PositiveSmallIntegerField(null=True, blank=True)

    initiative_status = models.CharField(
        max_length=255,
        choices=INITIATIVE_STATUS_CHOICES,
        default=PENDING,
        db_index=True,
    )

    initiative_brief = models.FileField(
        null=True,
        blank=True,
        upload_to=Upload(BASE_FILE_PATH),
        storage=RawMediaCloudinaryStorage(),
    )

    target_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = InitiativeManager()

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Initiative, self).save(*args, **kwargs)

    class Meta:
        ordering = ["start_date", "-id"]

    def __str__(self):
        return self.name

    def create_change_to_active_task(self):
        """create a periodic task that changes initiative to active at start time"""
        tenant = connection.tenant
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.start_date, datetime.min.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"{str(self.initiative_id)} active",  # task name
            task="strategy_deck.tasks.initiative.change_initiative_status_to_active",  # task.
            args=json.dumps(
                [
                    self.id,
                ]
            ),  # arguments
            description="this changes the initiative status to active at start time",
            one_off=True,
            headers=json.dumps(
                {
                    "_schema_name": tenant.schema_name,
                    "_use_tenant_timezone": True,
                }
            ),
        )

    def modify_change_to_active_task(self):
        """Modifies a periodic task that changes initiative to active at start time"""
        tenant = connection.tenant
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.start_date, datetime.min.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.filter(
            name=f"{str(self.initiative_id)} active"
        ).update(clocked=clocked)

    def create_change_to_closed_task(self):
        """create a periodic task that changes initiative to closed at end time"""
        tenant = connection.tenant
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.end_date, datetime.max.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"{str(self.initiative_id)} closed",  # task name
            task="strategy_deck.tasks.initiative.change_initiative_status_to_closed",
            args=json.dumps(
                [
                    self.id,
                ]
            ),  # arguments
            description="this changes the initiative status to over due at end time time",
            one_off=True,
            headers=json.dumps(
                {
                    "_schema_name": tenant.schema_name,
                    "_use_tenant_timezone": True,
                }
            ),
        )

    def modify_change_to_closed_task(self):
        """Modifies a periodic task that changes initiative to closed at end time"""
        tenant = connection.tenant
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=get_localized_time(
                self.end_date, datetime.max.time(), tenant.timezone
            )
        )
        PeriodicTask.objects.filter(
            name=f"{str(self.initiative_id)} closed"
        ).update(clocked=clocked)

    def update_target_point(self, point: Decimal):
        """Updates initiative target point based on downline change"""
        self.target_point += Decimal(point)
        self.save()
