import uuid

from django.contrib.auth import get_user_model
from django.db import models

from cloudinary_storage.storage import RawMediaCloudinaryStorage

from employee.models import Employee


User = get_user_model()
BASE_FILE_PATH = "employee_contact_information/"


class ContactInformation(models.Model):
    employee = models.OneToOneField(
        Employee,
        to_field="uuid",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="employee_contact_infomation",
    )
    contact_information_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    personal_email = models.EmailField(
        max_length=255, unique=True, db_index=True, blank=True, null=True
    )
    official_email = models.EmailField(
        max_length=255, unique=True, db_index=True, blank=True, null=True
    )
    phone_number = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    address = models.TextField(blank=True, null=True)

    guarantor_one_first_name = models.CharField(
        max_length=255, blank=True, null=True
    )
    guarantor_one_last_name = models.CharField(
        max_length=255, blank=True, null=True
    )
    guarantor_one_address = models.TextField(blank=True, null=True)
    guarantor_one_occupation = models.CharField(
        max_length=255, blank=True, null=True
    )
    guarantor_one_age = models.PositiveSmallIntegerField(blank=True, null=True)
    guarantor_one_id_card = models.FileField(
        upload_to=BASE_FILE_PATH,
        null=True,
        blank=True,
        storage=RawMediaCloudinaryStorage(),
    )
    guarantor_one_passport = models.FileField(
        upload_to=BASE_FILE_PATH,
        null=True,
        blank=True,
        storage=RawMediaCloudinaryStorage(),
    )

    guarantor_two_first_name = models.CharField(
        max_length=255, blank=True, null=True
    )
    guarantor_two_last_name = models.CharField(
        max_length=255, blank=True, null=True
    )
    guarantor_two_address = models.TextField(blank=True, null=True)
    guarantor_two_age = models.PositiveSmallIntegerField(blank=True, null=True)
    guarantor_two_occupation = models.CharField(
        max_length=255, blank=True, null=True
    )
    guarantor_two_id_card = models.FileField(
        upload_to=BASE_FILE_PATH,
        null=True,
        blank=True,
        storage=RawMediaCloudinaryStorage(),
    )
    guarantor_two_passport = models.FileField(
        upload_to=BASE_FILE_PATH,
        null=True,
        blank=True,
        storage=RawMediaCloudinaryStorage(),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    # sets official email to user email
    def save(self, *args, **kwargs):
        self.official_email = self.employee.user.email
        return super(ContactInformation, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return (
            f"{self.employee.user.first_name} {self.employee.user.last_name}"
        )
