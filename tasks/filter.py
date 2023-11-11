import django_filters

from tasks.models import Task


class TaskFilter(django_filters.FilterSet):
    owner_user_id = django_filters.UUIDFilter(
        field_name="upline_initiative__owner__user_id",
    )

    assignor_user_id = django_filters.UUIDFilter(
        field_name="upline_initiative__assignor__user_id",
    )
    owner_email = django_filters.CharFilter(
        field_name="upline_initiative__owner__email",
    )
    assignor_email = django_filters.CharFilter(
        field_name="upline_initiative__assignor__email",
    )
    task_status = django_filters.MultipleChoiceFilter(
        field_name="task_status", choices=Task.TASK_STATUS_CHOICES
    )
    upline_initiative_id = django_filters.UUIDFilter(
        field_name="upline_initiative__initiative_id"
    )
    corporate_level__uuid = django_filters.UUIDFilter(
        field_name="upline_initiative__corporate_level__uuid"
    )
    division__uuid = django_filters.UUIDFilter(
        field_name="upline_initiative__division__uuid"
    )
    group__uuid = django_filters.UUIDFilter(
        field_name="upline_initiative__group__uuid"
    )
    department__uuid = django_filters.UUIDFilter(
        field_name="upline_initiative__department__uuid"
    )
    unit__uuid = django_filters.UUIDFilter(
        field_name="upline_initiative__unit__uuid"
    )
    start_date = django_filters.DateFromToRangeFilter(field_name="start_date")

    class Meta:
        model = Task
        fields = [
            "owner_user_id",
            "assignor_user_id",
            "owner_email",
            "assignor_email",
            "task_status",
            "upline_initiative_id",
            "corporate_level__uuid",
            "division__uuid",
            "group__uuid",
            "department__uuid",
            "unit__uuid",
            "start_date",
        ]
