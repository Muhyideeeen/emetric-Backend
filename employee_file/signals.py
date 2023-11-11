from django.core.cache import cache

from employee_file.models import EmployeeFile


def post_save_employee_file_receiver(
    sender, instance: EmployeeFile, created, **kwargs
):
    """Signal for EmployeeFile post save"""
    cache.delete("employee_file_queryset")


def post_delete_employee_file_receiver(
    sender, instance: EmployeeFile, **kwargs
):
    """Delete all connected elements"""

    cache.delete("employee_file_queryset")
