from datetime import date
from email.policy import default
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django_tenants_celery_beat.models import TenantTimezoneMixin
from multiselectfield import MultiSelectField
from django_tenants_celery_beat.models import PeriodicTaskTenantLinkMixin
from cloudinary_storage.storage import RawMediaCloudinaryStorage

from core.utils.base_upload import Upload

BASE_FILE_PATH = "company_logo/"


class Client(TenantTimezoneMixin, TenantMixin):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    DAY_CHOICES = (
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    )

    company_name = models.CharField(max_length=255)
    company_logo = models.ImageField(
        upload_to=Upload(BASE_FILE_PATH),
        null=True,
        blank=True,
        storage=RawMediaCloudinaryStorage(),
    )
    owner_email = models.EmailField(max_length=255, db_index=True)
    owner_first_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    owner_last_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    owner_phone_number = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    work_start_time = models.TimeField()
    work_stop_time = models.TimeField()
    work_break_start_time = models.TimeField()
    work_break_stop_time = models.TimeField()
    work_days = MultiSelectField(
        choices=DAY_CHOICES, min_choices=1, default="0,1,2,3,4"
    )
    employee_limit = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # lincence is in years
    lincence = models.IntegerField(default=0)
    start_date = models.DateField(blank=True,null=True,default=None)
    end_date = models.DateField(blank=True,null=True,default=None)
    # poc is in days meaning the grace period before we end a subscription
    activate = models.BooleanField(default=False)

    poc     =   models.IntegerField(default=3)
    addresse = models.TextField(default='.')

    name_of_account_manager = models.CharField(
        max_length=255, blank=True, null=True, 
    )

    tel_of_account_manager = models.CharField(
        max_length=255, blank=True, null=True, 
    )
    email_of_account_manager = models.EmailField(
        blank=True, null=True, 
    )

    name_of_account_HRmanager = models.CharField(
        max_length=255, blank=True, null=True, 
    )

    tel_of_account_HRmanager = models.CharField(
        max_length=255, blank=True, null=True, 
    )
    email_of_account_HRmanager = models.EmailField(
        blank=True, null=True, 
    )

    def save(self, *args, **kwargs):
        from core.utils.image_compress import compressImage

        # compress image during create
        if (not self.id and self.company_logo) or (
            self.company_logo and self.company_logo.width > 200
        ):
            self.company_logo = compressImage(self.company_logo)

        super(Client, self).save(*args, **kwargs)

    def is_work_day(self, selected_date: date) -> bool:
        """Checks if weekday is a in work days"""
        if str(selected_date.weekday()) in self.work_days:
            return True
        return False

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.schema_name


class Domain(DomainMixin):
    pass




class PeriodicTaskTenantLink(PeriodicTaskTenantLinkMixin):
    pass