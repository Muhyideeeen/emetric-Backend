from django.contrib.auth import get_user_model
from django.db import models

from career_path.models import CareerPath
from organization.models import (
    Structure,
    Unit,
    Department,
    Group,
    Division,
    CorporateLevel,
)


User = get_user_model()


class Employee(Structure):
    name = None
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="unit_employee",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="department_employee",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="group_employee",
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="division_employee",
    )
    corporate_level = models.ForeignKey(
        CorporateLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="corporate_level_employee",
    )
    career_path = models.ForeignKey(
        CareerPath, on_delete=models.SET_NULL, null=True, blank=True
    )

    def parent_name(self):
        return self.unit

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        ordering = ["user"]

    def is_available(self):
        """Returns True if the employee is available, False otherwise."""
        return self.employee_employmentinformation.status in (
            "active",
            "absent",
        )
