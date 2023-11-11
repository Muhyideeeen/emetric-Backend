from django.contrib import admin

from employee_profile.models import BasicInformation, ContactInformation, EmploymentInformation

admin.site.register(BasicInformation)
admin.site.register(ContactInformation)
admin.site.register(EmploymentInformation)
