from datetime import date, datetime, timedelta
from math import ceil
from typing import List, Union
import django_filters
from django.core.cache import cache
from django.forms import ValidationError
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db import connection
from django.db.models import Count, F, Sum, QuerySet
from django.db.models.functions import TruncDate
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from core.utils.permissions import (
    has_access_to_user,
    has_access_to_team,
)
from core.utils import response_data, permissions
from core.utils.process_levels import process_level_by_uuid
from emetric_calendar.models import Holiday, UserScheduledEventCalendar
from emetric_calendar.serializers import (
    HolidaySerializer,
    UserScheduledEventCalendarSerializer,
    DateRangeSerializer,
)
from emetric_calendar.filter import (
    HolidayFilter,
    UserScheduledEventCalendarFilter,
)


User = get_user_model()


class HolidayViewsets(viewsets.ModelViewSet):
    """Holiday viewsets"""

    serializer_class = HolidaySerializer
    permissions_classes = [permissions.IsAdminOrSuperAdminOrReadOnly]
    queryset = Holiday.objects.all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = HolidayFilter
    lookup_field = "date"
    pagination_class = None
    http_method_names = ["get", "post", "delete"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "Holiday has been added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        data = response_data(
            405, "Retrieve function is not offered in this path."
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(200, "Holiday has been deleted successfully", {})
        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = cache.get("holiday_queryset")

        if queryset == None:
            queryset = Holiday.objects.all()
            cache.set("holiday_queryset", queryset)
        return queryset


class UserScheduledEventCalendarView(generics.ListAPIView):
    serializer_class = UserScheduledEventCalendarSerializer
    queryset = UserScheduledEventCalendar.objects.all()
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = UserScheduledEventCalendarFilter
    lookup_field = "user_id"

    def get_queryset(self):
        if self.lookup_field is None:
            raise Http404

        user_id = self.kwargs.get(self.lookup_field)

        try:
            user = get_object_or_404(User, user_id=user_id)
        except ValidationError:
            raise Http404

        if not has_access_to_user(user, self.request):
            raise PermissionDenied(
                {"user_id": "Permission denied to view user's calendar"}
            )
        return UserScheduledEventCalendar.objects.filter(
            user__user_id=user_id, is_free=False
        ).order_by("start_time")

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TeamScheduledEventCalendarView(generics.ListAPIView):
    serializer_class = UserScheduledEventCalendarSerializer
    queryset = UserScheduledEventCalendar.objects.all()
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = UserScheduledEventCalendarFilter
    lookup_field = "team_id"

    def get_queryset(self):
        if self.lookup_field is None:
            raise Http404

        team_id = self.kwargs.get(self.lookup_field)

        try:
            (
                corporate_level_obj,
                division_level_obj,
                group_level_obj,
                department_level_obj,
                unit_level_obj,
            ) = process_level_by_uuid(team_id)
        except ValidationError:
            raise Http404

        current_level = (
            corporate_level_obj
            or division_level_obj
            or group_level_obj
            or department_level_obj
            or unit_level_obj
        )

        if not current_level:
            raise Http404

        if not has_access_to_team(current_level, self.request):
            raise PermissionDenied(
                {"team_id": "Permission denied to view team's report"}
            )

        return UserScheduledEventCalendar.objects.filter(
            task__upline_initiative__corporate_level=corporate_level_obj,
            task__upline_initiative__division=division_level_obj,
            task__upline_initiative__group=group_level_obj,
            task__upline_initiative__department=department_level_obj,
            task__upline_initiative__unit=unit_level_obj,
            is_free=False,
        ).order_by("start_time")

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CalendarDashboardMixins:
    """Mixins for calendar dashboard"""

    @classmethod
    def retrieve_calendar_dashboard(
        cls,
        queryset: Union[QuerySet, List[UserScheduledEventCalendar]],
        date_after: datetime,
        date_before: datetime,
        *args,
        **kwargs
    ):
        scheduled_dates = list(
            queryset.annotate(date=TruncDate("start_time"))
            .values_list("date", flat=True)
            .distinct()
        )
        holidays = list(
            Holiday.objects.filter(date__gte=date_after, date__lte=date_before)
            .values_list("date", flat=True)
            .distinct()
        )

        tenant = connection.tenant
        org_working_days = list(tenant.work_days)

        possible_work_dates = []
        for x in range((date_before - date_after).days + 1):
            current_date: datetime = date_after + timedelta(days=x)
            if str(current_date.weekday()) in org_working_days:
                possible_work_dates.append(date_after + timedelta(days=x))

        available_dates = set(possible_work_dates) - set(holidays)
        inactive_days = available_dates - set(scheduled_dates)

        available_work_time: timedelta = (
            datetime.combine(date.today(), tenant.work_stop_time)
            - datetime.combine(date.today(), tenant.work_start_time)
            - (
                datetime.combine(date.today(), tenant.work_break_stop_time)
                - datetime.combine(date.today(), tenant.work_break_start_time)
            )
        )

        available_hours = ceil(
            len(available_dates) * available_work_time.total_seconds() / 3600
        )

        active_timedelta: timedelta = queryset.aggregate(
            duration=Sum(F("end_time") - F("start_time"))
        )["duration"]

        active_hours = ceil(
            active_timedelta.total_seconds() / 3600 if active_timedelta else 0
        )

        return {
            "active_days": queryset.annotate(date=TruncDate("start_time"))
            .values("date")
            .distinct()
            .aggregate(dates=Count("date"))["dates"],
            "active hours": active_hours,
            "inactive_days": len(inactive_days),
            "inactive_hours": available_hours - active_hours,
        }


class UserCalendarDashboardView(
    generics.GenericAPIView, CalendarDashboardMixins
):
    """User calendar dashboard view"""

    serializer_class = UserScheduledEventCalendarSerializer
    queryset = UserScheduledEventCalendar.objects.all()
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = UserScheduledEventCalendarFilter
    lookup_field = "user_id"

    def get_queryset(self):
        if self.lookup_field is None:
            raise Http404

        user_id = self.kwargs.get(self.lookup_field)

        try:
            user = get_object_or_404(User, user_id=user_id)
        except ValidationError:
            raise Http404

        if not has_access_to_user(user, self.request):
            raise PermissionDenied(
                {"user_id": "Permission denied to view user's calendar"}
            )
        return UserScheduledEventCalendar.objects.filter(
            user__user_id=user_id, is_free=False
        ).order_by("start_time")

    def get(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())
        date_after = request.query_params.get("date_after")
        date_before = request.query_params.get("date_before")
        data = dict(
            date_after=date_after,
            date_before=date_before,
        )
        serialized_data = DateRangeSerializer(data=data)
        serialized_data.is_valid(raise_exception=True)
        date_after = serialized_data.validated_data.get("date_after")
        date_before = serialized_data.validated_data.get("date_before")

        detail = self.retrieve_calendar_dashboard(
            queryset, date_after, date_before
        )
        data = response_data(200, "Calendar dashboard details", detail)
        return Response(data, status=status.HTTP_200_OK)


class TeamCalendarDashboardView(
    generics.GenericAPIView, CalendarDashboardMixins
):
    """Team calendar dashboard view"""

    serializer_class = UserScheduledEventCalendarSerializer
    queryset = UserScheduledEventCalendar.objects.all()
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = UserScheduledEventCalendarFilter
    lookup_field = "team_id"

    def get_queryset(self):
        if self.lookup_field is None:
            raise Http404

        team_id = self.kwargs.get(self.lookup_field)

        try:
            (
                corporate_level_obj,
                division_level_obj,
                group_level_obj,
                department_level_obj,
                unit_level_obj,
            ) = process_level_by_uuid(team_id)
        except ValidationError:
            raise Http404

        current_level = (
            corporate_level_obj
            or division_level_obj
            or group_level_obj
            or department_level_obj
            or unit_level_obj
        )

        if not current_level:
            raise Http404

        if not has_access_to_team(current_level, self.request):
            raise PermissionDenied(
                {"team_id": "Permission denied to view team's report"}
            )

        return UserScheduledEventCalendar.objects.filter(
            task__upline_initiative__corporate_level=corporate_level_obj,
            task__upline_initiative__division=division_level_obj,
            task__upline_initiative__group=group_level_obj,
            task__upline_initiative__department=department_level_obj,
            task__upline_initiative__unit=unit_level_obj,
            is_free=False,
        ).order_by("start_time")

    def get(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())
        date_after = request.query_params.get("date_after")
        date_before = request.query_params.get("date_before")
        data = dict(
            date_after=date_after,
            date_before=date_before,
        )
        serialized_data = DateRangeSerializer(data=data)
        serialized_data.is_valid(raise_exception=True)
        date_after = serialized_data.validated_data.get("date_after")
        date_before = serialized_data.validated_data.get("date_before")

        detail = self.retrieve_calendar_dashboard(
            queryset, date_after, date_before
        )
        data = response_data(200, "Calendar dashboard details", detail)
        return Response(data, status=status.HTTP_200_OK)
