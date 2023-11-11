from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class EmployeeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "employee"

    def ready(self):
        from employee.models import Employee
        from employee.signals import (
            post_save_employee_created_receiver,
            post_delete_employee_receiver,
        )

        post_save.connect(post_save_employee_created_receiver, sender=Employee)

        post_delete.connect(post_delete_employee_receiver, sender=Employee)
