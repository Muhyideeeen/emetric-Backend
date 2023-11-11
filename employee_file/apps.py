from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class EmployeeFileConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "employee_file"

    def ready(self):
        from employee_file.models import EmployeeFile
        from employee_file.signals import (
            post_save_employee_file_receiver,
            post_delete_employee_file_receiver,
        )

        post_delete.connect(
            post_save_employee_file_receiver, sender=EmployeeFile
        )
        post_save.connect(
            post_delete_employee_file_receiver, sender=EmployeeFile
        )
