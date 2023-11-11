from django.contrib import admin

from .models import (
    CorporateLevel,
    Department,
    Group,
    Unit,
    Division,
)


class BaseOrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization_short_name']

    def organization_short_name(self, obj):
        return obj.organization_short_name.schema_name


@admin.register(CorporateLevel)
class CorporateLevelAdmin(BaseOrganizationAdmin):
    pass


@admin.register(Division)
class DivisionAdmin(BaseOrganizationAdmin):
    list_display = [*BaseOrganizationAdmin.list_display, 'corporate_level']

    def corporate_level(self, obj):
        return obj.get_parent()


@admin.register(Group)
class GroupAdmin(BaseOrganizationAdmin):
    list_display = [*BaseOrganizationAdmin.list_display, 'division']

    def division(self, obj):
        return obj.get_parent()


@admin.register(Department)
class DepartmentAdmin(BaseOrganizationAdmin):
    list_display = [*BaseOrganizationAdmin.list_display, 'group']

    def group(self, obj):
        return obj.get_parent()


@admin.register(Unit)
class UnitAdmin(BaseOrganizationAdmin):
    list_display = [*BaseOrganizationAdmin.list_display, 'department']

    def department(self, obj):
        return self.get_parent()
