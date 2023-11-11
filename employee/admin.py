from django.contrib import admin

from employee.models import Employee
from organization.admin import BaseOrganizationAdmin


@admin.register(Employee)
class EmployeeAdmin(BaseOrganizationAdmin):
    list_display = [*BaseOrganizationAdmin.list_display, 'unit']

    def unit(self, obj):
        return obj.get_parent()
