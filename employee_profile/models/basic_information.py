import uuid

from django.contrib.auth import get_user_model
from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage

from designation.models import Designation
from employee.models import Employee
from core.utils.base_upload import Upload


User = get_user_model()
BASE_FILE_PATH = "employee_basic_information/"


class EducationDetail(models.Model):
    institution = models.CharField(max_length=255)
    year = models.PositiveIntegerField()
    qualification = models.CharField(max_length=255)

    class Meta:
        ordering = ["-id"]


class BasicInformation(models.Model):
    employee = models.OneToOneField(
        Employee,
        to_field="uuid",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="employee_basic_infomation",
    )
    designation = models.ForeignKey(
        Designation,
        to_field="designation_id",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    basic_information_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    profile_picture = models.ImageField(
        upload_to=Upload(BASE_FILE_PATH),
        null=True,
        blank=True,
        storage=RawMediaCloudinaryStorage(),
    )
    date_of_birth = models.DateField(blank=True, null=True)
    brief_description = models.TextField(blank=True, null=True)
    education_details = models.ManyToManyField(
        EducationDetail,
        blank=True,
        related_name="education_details_basic_infomation",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def save(self, *args, **kwargs):
        from core.utils.image_compress import compressImage

        if (not self.id and self.profile_picture) or (
            self.profile_picture and self.profile_picture.width > 200
        ):
            self.profile_picture = compressImage(self.profile_picture)

        super(BasicInformation, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return (
            f"{self.employee.user.first_name} {self.employee.user.last_name}"
        )
