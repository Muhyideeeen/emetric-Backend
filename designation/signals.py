from typing import Dict

from django.core.cache import cache

from designation.models import Designation
from employee.models import Employee
from employee_profile.models import BasicInformation


def post_save_designation_receiver(
    sender, instance: Designation, created, **kwargs
):
    """Signal for designation post save"""
    cache.delete("designation_queryset")  # clear designation queryset cache


def post_delete_designation_receiver(
    sender, instance: Designation, **kwargs: Dict
):
    """Delete all connected elements"""
    cache.delete("designation_queryset")
    
    Employee.objects.filter(
        employee_basic_infomation__in=BasicInformation.objects.filter(
            designation=instance
        )
    ).delete()
