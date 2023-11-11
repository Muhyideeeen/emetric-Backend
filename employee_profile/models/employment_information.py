import uuid

from django.contrib.auth import get_user_model
from django.db import models

from employee.models import Employee

User = get_user_model()


class EmploymentInformation(models.Model):
    
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"
    ABSENT = "absent"
    DISMISSED = "dismissed"
    RESIGNED = "resigned"
    
    EMPLOYEE_TYPE_CHOICES = (
        (ACTIVE, "Active"),
        (ON_LEAVE, "On Leave"),
        (SUSPENDED, "Suspended"),
        (ABSENT, "Absent"),
        (DISMISSED, "Dismissed"),
        (RESIGNED, "Resigned"),
    )
    
    employee = models.OneToOneField(
        Employee,
        to_field="uuid",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="employee_employmentinformation",
    )
    employment_information_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    date_employed = models.DateField(blank=True, null=True)
    date_of_last_promotion = models.DateField(blank=True, null=True)
    upline = models.ForeignKey(
        User,
        to_field="user_id",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    
    status = models.CharField(
        max_length=255,
        choices=EMPLOYEE_TYPE_CHOICES,
        default=ACTIVE,
        db_index=True,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return (
            f"{self.employee.user.first_name} {self.employee.user.last_name}"
        )
