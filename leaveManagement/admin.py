from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from . import models
# Register your models here.


# @admin.register(models.Leave)
# class LeaveDashboard( admin.ModelAdmin):
#     pass

admin.site.register(models.EmployeeLeaveApplication)
admin.site.register(models.Leave)