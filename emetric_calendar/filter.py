import django_filters

from emetric_calendar.models import Holiday, UserScheduledEventCalendar


class HolidayFilter(django_filters.FilterSet):
    """Holiday Filter"""

    date = django_filters.DateFromToRangeFilter(field_name="date")

    class Meta:
        model = Holiday
        fields = ["date"]


class UserScheduledEventCalendarFilter(django_filters.FilterSet):
    """User Scheduled Event Calendar Filter"""

    date_after = django_filters.DateFilter(
        field_name="start_time", lookup_expr=("gte")
    )
    date_before = django_filters.DateFilter(
        field_name="end_time",
        lookup_expr=("lte"),
    )

    class Meta:
        model = UserScheduledEventCalendar
        fields = ["date_after", "date_before"]
