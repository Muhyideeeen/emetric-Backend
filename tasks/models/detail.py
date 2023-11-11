from decimal import Decimal
import uuid
import json

from celery import current_app
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db import models, connection
from django.apps import apps
from django_celery_beat.models import ClockedSchedule, PeriodicTask
from multiselectfield.db.fields import MultiSelectField
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from textblob import TextBlob
from pdfminer import high_level
from pysimilar import compare

from core.utils.base_upload import Upload
from core.utils.process_durations import (
    get_localized_time,
    process_end_date_time,
)
from strategy_deck.models import Initiative


User = get_user_model()
BASE_FILE_PATH = "task_brief/"


class TaskManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)
        cache.delete("task_queryset")

        # manually send signals for task
        for obj in objs:
            obj.create_scheduled_event_for_task()
            obj.create_change_to_active_task()
            obj.create_change_to_over_due()
            current_app.send_task(
                "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
                (obj.upline_initiative.pk, obj.target_point),
            )
        return result


class Task(models.Model):

    QUALITATIVE = "qualitative"
    QUANTITATIVE = "quantitative"
    QUANTITATIVE_AND_QUALITATIVE = "quantitative_and_qualitative"

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONCE = "once"

    PENDING = "pending"
    ACTIVE = "active"
    OVER_DUE = "over_due"
    AWAITING_RATING = "awaiting_rating"
    REWORK = "rework"
    REWORK_OVER_DUE = "rework_over_due"
    CLOSED = "closed"

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    FIRST = "first"
    SECOND = "second"
    THIRD = "third"
    FOURTH = "fourth"
    LAST = "last"

    TASK_TYPE_CHOICES = (
        (QUALITATIVE, "Qualitative"),
        (QUANTITATIVE, "Quantitative"),
        (QUANTITATIVE_AND_QUALITATIVE, "Quantitative And Qualitative"),
    )

    ROUTINE_TYPE_CHOICES = (
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
        (ONCE, "Once"),
    )

    TASK_STATUS_CHOICES = (
        (PENDING, "pending"),
        (ACTIVE, "active"),
        (OVER_DUE, "over due"),
        (AWAITING_RATING, "awaiting rating"),
        (REWORK, "rework"),
        (REWORK_OVER_DUE, "rework over due"),
        (CLOSED, "closed"),
    )

    DAY_CHOICES = (
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    )

    DAY_POSITION_CHOICES = (
        (FIRST, "First"),
        (SECOND, "Second"),
        (THIRD, "Third"),
        (FOURTH, "Fourth"),
        (LAST, "Last"),
    )

    task_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    name = models.CharField(max_length=255, db_index=True)
    upline_initiative = models.ForeignKey(
        Initiative,
        on_delete=models.CASCADE,
        db_index=True,
        to_field="initiative_id",
        blank=True,
        null=True,
        related_name="initiative_task",
    )

    task_type = models.CharField(max_length=255, choices=TASK_TYPE_CHOICES)

    routine_round = models.PositiveIntegerField(default=1)

    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    duration = models.DurationField(default=timedelta())
    routine_option = models.CharField(
        max_length=255, choices=ROUTINE_TYPE_CHOICES
    )
    repeat_every = models.PositiveSmallIntegerField(null=True, blank=True)
    occurs_days = MultiSelectField(
        choices=DAY_CHOICES, min_choices=1, null=True, blank=True
    )
    occurs_month_day_number = models.PositiveSmallIntegerField(
        null=True, blank=True
    )
    occurs_month_day_position = models.CharField(
        max_length=255, choices=DAY_POSITION_CHOICES, null=True, blank=True
    )
    occurs_month_day = models.CharField(
        max_length=255, choices=DAY_CHOICES, null=True, blank=True
    )
    end_date = models.DateField(null=True, blank=True)
    after_occurrence = models.PositiveSmallIntegerField(null=True, blank=True)

    task_status = models.CharField(
        max_length=255,
        choices=TASK_STATUS_CHOICES,
        default=PENDING,
        db_index=True,
    )

    target_brief = models.FileField(
        null=True,
        blank=True,
        upload_to=Upload(BASE_FILE_PATH),
        storage=RawMediaCloudinaryStorage(),
    )

    turn_around_time_target_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    turn_around_time_target_point_achieved = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )

    rework_limit = models.PositiveIntegerField(default=0)
    rework_remark = models.TextField(blank=True, null=True)
    rework_end_time = models.TimeField(blank=True, null=True)
    rework_end_date = models.DateField(blank=True, null=True)

    quantity_target_unit = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    quantity_target_unit_achieved = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )

    quantity_target_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    quantity_target_point_achieved = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )

    quality_target_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    quality_target_point_achieved = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )

    target_point = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    target_point_achieved = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )

    sensitivity_score = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    plagiarism_score = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    average_system_based_score = models.DecimalField(
        decimal_places=2, max_digits=18, default=0.00
    )
    rating_remark = models.TextField(blank=True, null=True)

    use_owner_submission = models.BooleanField(default=True)

    objects = TaskManager()

    class Meta:
        ordering = ["start_date", "start_time", "-id"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        # if self.task_type == Task.QUANTITATIVE:
        #     self.rework_limit = 0
        #     self.quality_target_point = 0
        #     self.quality_target_point_achieved = 0

        # if self.task_type == Task.QUALITATIVE:
        #     self.quantity_target_point = 0
        #     self.quantity_target_unit = 0
        #     self.quantity_target_unit_achieved = 0

        # self.target_point = (
        #     self.turn_around_time_target_point
        #     + self.quality_target_point
        #     + self.quantity_target_point
        # )

        if self.task_status == Task.CLOSED:
            self.generate_points_from_submission()
        super(Task, self).save(*args, **kwargs)

    def is_qualitative_task(self) -> bool:
        """Check if task is a qualitative type of task"""
        return (
            self.task_type == self.QUALITATIVE
            or self.task_type == self.QUANTITATIVE_AND_QUALITATIVE
        )

    def is_quantitative_task(self) -> bool:
        """Check if task is a quantitative type of task"""
        return (
            self.task_type == self.QUANTITATIVE
            or self.task_type == self.QUANTITATIVE_AND_QUALITATIVE
        )

    def is_task_owner(self, user: User) -> bool:
        """Checks if user is owner of task
        Args:
            user (User): [description]
        """
        return self.upline_initiative.owner == user

    def is_task_assignor(self, user: User) -> bool:
        """Checks if user is assignor of task
        Args:
            user (User): [description]
        """
        return self.upline_initiative.assignor == user

    def is_rework_limit_zero(self) -> bool:
        """Check if rework limit is zero"""
        return self.rework_limit == 0

    def is_quantity_target_unit_achieved_valid(self, value) -> bool:
        """Checks if quantity target unit achieved is valid"""
        return 0 <= value

    def is_quality_target_point_achieved_valid(self, value) -> bool:
        """
        Checks if quality target point achieved valid is valid
        """
        return 0 <= value <= self.quality_target_point

    def is_end_date_time_passed(self) -> bool:
        """
        Checks if end time has passed
        """
        tenant = connection.tenant
        if self.rework_end_date:
            end_date_time = get_localized_time(
                self.rework_end_date, self.rework_end_time, tenant.timezone
            )
            return end_date_time < timezone.now()
        else:
            end_date_time = process_end_date_time(
                self.start_date, self.start_time, self.duration, tenant
            )
            return end_date_time < timezone.now()

    def is_owner_allowed_to_make_submission(self):
        """Return true if owner is allowed to make task submission"""
        if (
            self.task_status == self.ACTIVE
            or self.task_status == self.OVER_DUE
            or self.task_status == self.REWORK
            or self.task_status == self.REWORK_OVER_DUE
        ):
            return True

        return False

    def is_assignor_allowed_to_rate(self) -> bool:
        """Returns true is assignor is allowed to rate"""
        if self.task_status == Task.AWAITING_RATING:
            return True

        return False

    # calculations

    def generate_points_from_submission(self):
        """
        Calculates points from owner's most recent submission after rating
        has been made.
        """
        submissions = self.task_submission.all()  # get all submissions

        # calculate turn around point achieved
        tenant = connection.tenant
        end_date_time = process_end_date_time(
            self.start_date, self.start_time, self.duration, tenant
        )

        # assign target point if owner submission was made before end time
        if submissions.filter(
            created__lte=end_date_time, user=self.upline_initiative.owner
        ).exists():
            self.turn_around_time_target_point_achieved = (
                self.turn_around_time_target_point
            )

        # sets quantity_target_unit_achieved to last assignor's or owner's
        # target unit submission
        self.quantity_target_unit_achieved = (
            self.__get_quantity_target_unit_achieved(submissions)
        )

        self.quantity_target_point_achieved = (
            self.__calculate_quantity_target_point_achieved()
        )

        self.target_point_achieved = (
            self.turn_around_time_target_point_achieved
            + self.quality_target_point_achieved
            + self.quantity_target_point_achieved
        )

    def __get_quantity_target_unit_achieved(self, submissions) -> Decimal:
        """Returns target unit achieved from assignor's submission or
        owner's submission"""
        # assignor_submissions = submissions.filter(
        #     user=self.upline_initiative.assignor
        # )
        # owner_submissions = submissions.filter(
        #     user=self.upline_initiative.owner
        # )

        # if (
        #     assignor_submissions.exists()
        #     and assignor_submissions[0].quantity_target_unit_achieved != None
        # ):
        #     return assignor_submissions[0].quantity_target_unit_achieve
        # else:
        #     return owner_submissions[0].quantity_target_unit_achieved
        return submissions.first().quantity_target_unit_achieved

    def __calculate_quantity_target_point_achieved(self) -> Decimal:
        """calculates quantity_target_point_achieved"""
        if self.quantity_target_unit != 0:
            # if self.quantity_target_unit_achieved > self.quantity_target_unit:
            #     return self.quantity_target_point

            return (
                self.quantity_target_point
                * self.quantity_target_unit_achieved
                / self.quantity_target_unit
            )
        else:
            return Decimal(0)

    def create_change_to_active_task(self):
        """create a periodic task that changes task to active at start time"""
        tenant = connection.tenant
        localized_time = get_localized_time(
            self.start_date, self.start_time, tenant.timezone
        )

        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=localized_time
        )
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"{str(self.task_id)} active",  # task name
            task="tasks.tasks.detail.change_task_status_to_active",  # task.
            args=json.dumps(
                [
                    self.id,
                ]
            ),  # arguments
            description="this changes the task status to active at start time",
            one_off=True,
            headers=json.dumps(
                {
                    "_schema_name": tenant.schema_name,
                    "_use_tenant_timezone": True,
                }
            ),
        )

    def modify_change_to_active_task(self):
        """Modify a periodic task that changes task to active at start time"""
        tenant = connection.tenant
        localized_time = get_localized_time(
            self.start_date, self.start_time, tenant.timezone
        )

        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=localized_time
        )
        PeriodicTask.objects.filter(name=f"{str(self.task_id)} active").update(
            clocked=clocked
        )

    def create_change_to_over_due(self):
        """create a periodic task that changes task to over due at end time"""
        tenant = connection.tenant
        end_date_time = process_end_date_time(
            self.start_date, self.start_time, self.duration, tenant
        )
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=end_date_time
        )
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"{str(self.task_id)} over_due",  # task name
            task="tasks.tasks.detail.change_task_status_to_over_due",
            args=json.dumps(
                [
                    self.id,
                ]
            ),  # arguments
            description="this changes the task status to over due at end time",
            one_off=True,
            headers=json.dumps(
                {
                    "_schema_name": tenant.schema_name,
                    "_use_tenant_timezone": True,
                }
            ),
        )

    def modify_change_to_over_due(self):
        """Modify a periodic task that changes task to over due at end time"""
        tenant = connection.tenant
        end_date_time = process_end_date_time(
            self.start_date, self.start_time, self.duration, tenant
        )
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=end_date_time
        )
        PeriodicTask.objects.filter(
            name=f"{str(self.task_id)} over_due"
        ).update(clocked=clocked)

    def create_change_to_rework_over_due_task(self):
        """create a periodic task that changes task to rework over due at end time"""
        tenant = connection.tenant
        end_date_time = get_localized_time(
            self.rework_end_date, self.rework_end_time, tenant.timezone
        )

        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=end_date_time
        )
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"{str(self.task_id)} rework({self.rework_limit}) over_due",  # task name
            task="tasks.tasks.detail.change_task_status_to_rework_over_due",  # task.
            args=json.dumps(
                [
                    self.id,
                ]
            ),  # arguments
            description="this changes the task status to rework over due at end time time",
            one_off=True,
            headers=json.dumps(
                {
                    "_schema_name": tenant.schema_name,
                    "_use_tenant_timezone": True,
                }
            ),
        )

    def create_scheduled_event_for_task(self):
        """Creates an event on the calender for the task"""
        name = self.name
        tenant = connection.tenant
        start_date = self.start_date
        start_time = self.start_time
        duration = self.duration
        end_date_time = process_end_date_time(
            start_date, start_time, duration, tenant
        )
        start_date_time = get_localized_time(
            start_date, start_time, tenant.timezone
        )

        upline_initiative = self.upline_initiative
        owner = upline_initiative.owner
        UserScheduledEventCalendar = apps.get_model(
            "emetric_calendar.UserScheduledEventCalendar"
        )
        UserScheduledEventCalendar.objects.create(
            name=name,
            user=owner,
            start_time=start_date_time,
            end_time=end_date_time,
            task=self,
        )

    def modify_scheduled_event_for_task(self):
        """Modifies an event on the calender for the task"""
        name = self.name
        tenant = connection.tenant
        start_date = self.start_date
        start_time = self.start_time
        duration = self.duration
        end_date_time = process_end_date_time(
            start_date, start_time, duration, tenant
        )

        start_date_time = get_localized_time(
            start_date, start_time, tenant.timezone
        )

        upline_initiative = self.upline_initiative
        owner = upline_initiative.owner
        UserScheduledEventCalendar = apps.get_model(
            "emetric_calendar.UserScheduledEventCalendar"
        )
        UserScheduledEventCalendar.objects.filter(task=self).update(
            name=name,
            user=owner,
            start_time=start_date_time,
            end_time=end_date_time,
        )

    def generate_system_based_rating_for_task(self):
        submissions = self.task_submission.all()  # cache all submissions

        non_owner_submissions = submissions.exclude(
            user=self.upline_initiative.owner
        )
        owner_submissions = submissions.filter(
            user=self.upline_initiative.owner
        )

        plagiarism_score = 100
        sensitivity_score = 100

        if not self.use_owner_submission and self.is_qualitative_task():
            owner_pdf = owner_submissions.first().submission
            non_owner_pdf = non_owner_submissions.first().submission

            owner_pdf_extract = high_level.extract_text(owner_pdf.path)
            non_owner_pdf_extract = high_level.extract_text(non_owner_pdf.path)

            # calculate the percentage similarity in the text
            try:
                plagiarism_score = (
                    compare(owner_pdf_extract, non_owner_pdf_extract) * 100
                )
            except ValueError:
                plagiarism_score = 0.0

            # calculate the percentage similarity in the subjectivity
            analysis1 = TextBlob(owner_pdf_extract)
            analysis2 = TextBlob(non_owner_pdf_extract)

            s1 = analysis1.sentiment.subjectivity
            s2 = analysis2.sentiment.subjectivity

            try:
                sensitivity_score = 100 - (abs(s2 - s1) / (s2 + s1) * 100)
            except ZeroDivisionError:
                sensitivity_score = 0

        self.plagiarism_score = plagiarism_score
        self.sensitivity_score = sensitivity_score
        self.average_system_based_score = (
            plagiarism_score + sensitivity_score
        ) / 2

        self.save()
