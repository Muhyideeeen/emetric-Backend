import uuid

from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage

from employee.models import Employee


BASE_FILE_PATH = "employee_file/"


class EmployeeFileName(models.Model):
    """Employee file name model"""

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-name"]


class EmployeeFile(models.Model):
    """Employee file model to store an employee's file"""

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    name = models.CharField(max_length=255, db_index=True)
    value = models.PositiveSmallIntegerField(default=1)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employee_employee_file",
    )
    file = models.FileField(
        upload_to=BASE_FILE_PATH, storage=RawMediaCloudinaryStorage()
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.value}"

    class Meta:
        ordering = ["-created_at"]
