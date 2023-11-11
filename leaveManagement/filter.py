import django_filters
from   .  import models


class EmployeeLeaveApplicationFilter(django_filters.FilterSet):
    corporate_level__uuid = django_filters.UUIDFilter(
        field_name="employee__corporate_level__uuid"
    )
    division__uuid = django_filters.UUIDFilter(
        field_name="employee__division__uuid"
    )
    group__uuid = django_filters.UUIDFilter(
        field_name="employee__group__uuid"
    )
    department__uuid = django_filters.UUIDFilter(
        field_name="employee__department__uuid"
    )
    unit__uuid = django_filters.UUIDFilter(
        field_name="employee__unit__uuid"
    )
    is_team_lead_can_see =django_filters.BooleanFilter(field_name='is_team_lead_can_see')
    is_hradmin_can_see =django_filters.BooleanFilter(field_name='is_hradmin_can_see')
    start_date = django_filters.DateFilter(field_name='start_date')
    team_lead_approve = django_filters.CharFilter(field_name='team_lead_approve')
    hradmin_lead_approve = django_filters.CharFilter(field_name='hradmin_lead_approve')

    class Meta:
        model = models.EmployeeLeaveApplication
        fields =[
            'employee',
            'is_team_lead_can_see',
            'is_hradmin_can_see',
            'team_lead_approve',
            'hradmin_lead_approve','start_date'
        ]