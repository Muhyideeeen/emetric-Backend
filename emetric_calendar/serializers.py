from django.utils import timezone
from rest_framework import serializers
from core.serializers.nested import (
    NestedTaskSerializer,
    NestedUserSerializer,
)

from emetric_calendar.models import Holiday, UserScheduledEventCalendar


class HolidaySerializer(serializers.ModelSerializer):
    """Holiday serializer"""

    class Meta:
        model = Holiday
        fields = ["name", "date"]

    def validate_date(self, value: str):
        if timezone.now().date() > value:
            raise serializers.ValidationError(
                {"date": "date cannot be in the past"}
            )
        return value


class UserScheduledEventCalendarSerializer(serializers.ModelSerializer):
    """User scheduled event calendar serializer"""

    user = NestedUserSerializer(read_only=True)
    task = NestedTaskSerializer(read_only=True)

    class Meta:
        model = UserScheduledEventCalendar
        fields = ["user", "task", "start_time", "end_time"]


class DateRangeSerializer(serializers.Serializer):
    """Date range serializer"""

    date_after = serializers.DateField()
    date_before = serializers.DateField()

    def validate(self, data):
        if data["date_after"] > data["date_before"]:
            raise serializers.ValidationError(
                {"date_after": "date_after cannot be greater than date_before"}
            )
        return data


class CalendarDashboardSerializer(serializers.Serializer):
    """Calendar dashboard serializer"""

    active_hours = serializers.IntegerField(read_only=True)
    in_active_hours = serializers.IntegerField(read_only=True)
    active_days = serializers.IntegerField(read_only=True)
    in_active_days = serializers.IntegerField(read_only=True)
