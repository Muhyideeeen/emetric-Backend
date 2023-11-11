import django_filters
from typing import List
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.utils import translate_validation
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from core.utils.permissions import (
    has_access_to_initiative_report,
    has_access_to_objective_report,
    has_access_to_team,
    has_access_to_user,
)
from core.utils import response_data
from core.utils.process_levels import process_level_by_uuid
from core.utils.process_report import (
    get_initiatives,
    process_tasks_for_report,
)
from strategy_deck.models import Initiative, Objective
from strategy_deck.views.objective import ObjectiveFilter
from tasks.models.detail import Task
from tasks.serializers import (
    TaskReportSerializer,
    InitiativeReportSerializer,
    ObjectiveReportSerializer,
)
from tasks.filter import TaskFilter
from core.utils.custom_pagination import CustomPagination


User = get_user_model()


@api_view(
    [
        "GET",
    ]
)
@permission_classes(
    [
        IsAuthenticated,
    ]
)
def user_task_report(request, user_id):
    # validates user id
    try:
        user = get_object_or_404(User, user_id=user_id)
    except ValidationError:
        raise Http404

    if not has_access_to_user(user, request):
        raise PermissionDenied(
            {"user_id": "Permission denied to view user's report"}
        )

    paginator = CustomPagination()

    # gets all closed tasks for owner
    queryset = Task.objects.filter(
        task_status=Task.CLOSED, upline_initiative__owner=user
    )

    dashboard_report = request.GET.get("dashboard_report")
    filterset = TaskFilter(request.GET, queryset=queryset)

    if not filterset.is_valid():
        raise translate_validation(filterset.errors)

    # Loops through tasks for cumulative calculations
    tasks = process_tasks_for_report(filterset.qs)

    # sends unpaginated response of the last element for dashboard purpose
    if dashboard_report == "True":
        serializer = TaskReportSerializer(tasks, many=True)
        data = response_data(200, "dashboard report", serializer.data[-1:])
        return Response(data, status=status.HTTP_200_OK)

    page = paginator.paginate_queryset(tasks, request)
    serializer = TaskReportSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(
    [
        "GET",
    ]
)
@permission_classes(
    [
        IsAuthenticated,
    ]
)
def team_task_report(request, team_id):
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

    if not has_access_to_team(current_level, request):
        raise PermissionDenied(
            {"team_id": "Permission denied to view team's report"}
        )
    paginator = CustomPagination()

    queryset = Task.objects.filter(
        task_status=Task.CLOSED,
        upline_initiative__corporate_level=corporate_level_obj,
        upline_initiative__division=division_level_obj,
        upline_initiative__group=group_level_obj,
        upline_initiative__department=department_level_obj,
        upline_initiative__unit=unit_level_obj,
    )
    dashboard_report = request.GET.get("dashboard_report")
    filterset = TaskFilter(request.GET, queryset=queryset)

    if not filterset.is_valid():
        raise translate_validation(filterset.errors)

    tasks: List[Task] = filterset.qs

    # Loops through tasks for cumulative calculations
    tasks = process_tasks_for_report(filterset.qs)

    # sends unpaginated response of the last element for dashboard purpose
    if dashboard_report == "True":
        serializer = TaskReportSerializer(tasks, many=True)
        data = response_data(200, "dashboard report", serializer.data[-1:])
        return Response(data, status=status.HTTP_200_OK)

    page = paginator.paginate_queryset(tasks, request)
    serializer = TaskReportSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


class TeamInitiativeReport(generics.ListAPIView):
    serializer_class = InitiativeReportSerializer
    queryset = Initiative.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
    lookup_field = "team_id"

    def get_queryset(self):
        if self.lookup_field is None:
            raise Http404

        team_id = self.kwargs[self.lookup_field]

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

        if not has_access_to_team_report(current_level, self.request):
            raise PermissionDenied(
                {"team_id": "Permission denied to view team's report"}
            )

        initiatives = Initiative.objects.filter(
            initiative_status__in=[Initiative.CLOSED, Initiative.ACTIVE],
            corporate_level=corporate_level_obj,
            division=division_level_obj,
            group=group_level_obj,
            department=department_level_obj,
            unit=unit_level_obj,
        )
        return initiatives

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "initiative report list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)


@api_view(
    [
        "GET",
    ]
)
@permission_classes(
    [
        IsAuthenticated,
    ]
)
def initiative_task_report(request, initiative_id):
    try:
        initiative = get_object_or_404(Initiative, initiative_id=initiative_id)
    except ValidationError:
        raise Http404

    if not has_access_to_initiative_report(request, initiative.owner):
        raise PermissionDenied(
            {"initiative_id": "Permission denied to view initiative report"}
        )

    initiatives = get_initiatives(initiative)

    paginator = CustomPagination()
    queryset = Task.objects.filter(
        task_status=Task.CLOSED,
        upline_initiative__in=initiatives,
    )
    dashboard_report = request.GET.get("dashboard_report")
    filterset = TaskFilter(request.GET, queryset=queryset)

    if not filterset.is_valid():
        raise translate_validation(filterset.errors)

    tasks: List[Task] = filterset.qs

    # Loops through tasks for cumulative calculations
    tasks = process_tasks_for_report(filterset.qs)

    # sends unpaginated response of the last element for dashboard purpose
    if dashboard_report == "True":
        serializer = TaskReportSerializer(tasks, many=True)
        data = response_data(200, "dashboard report", serializer.data[-1:])
        return Response(data, status=status.HTTP_200_OK)

    page = paginator.paginate_queryset(tasks, request)
    serializer = TaskReportSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(
    [
        "GET",
    ]
)
@permission_classes(
    [
        IsAuthenticated,
    ]
)
def objective_task_report(request, objective_id):
    try:
        objective = get_object_or_404(Objective, objective_id=objective_id)
    except ValidationError:
        raise Http404

    if not has_access_to_objective_report(request):
        raise PermissionDenied(
            {"objective_id": "Permission denied to view objective report"}
        )

    initiatives = get_initiatives(objective)  # downline initiatives

    paginator = CustomPagination()
    queryset = Task.objects.filter(
        task_status=Task.CLOSED,
        upline_initiative__in=initiatives,
    )
    dashboard_report = request.GET.get("dashboard_report")
    filterset = TaskFilter(request.GET, queryset=queryset)

    if not filterset.is_valid():
        raise translate_validation(filterset.errors)

    tasks: List[Task] = filterset.qs

    # Loops through tasks for cumulative calculations
    tasks = process_tasks_for_report(filterset.qs)

    # sends unpaginated response of the last element for dashboard purpose
    if dashboard_report == "True":
        serializer = TaskReportSerializer(tasks, many=True)
        data = response_data(200, "dashboard report", serializer.data[-1:])
        return Response(data, status=status.HTTP_200_OK)

    page = paginator.paginate_queryset(tasks, request)
    serializer = TaskReportSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


class ObjectiveReport(generics.ListAPIView):
    """Returns a report based on objectives"""

    serializer_class = ObjectiveReportSerializer
    queryset = Objective.objects.all()
    pagination_class = CustomPagination
    permission_classes = [
        IsAuthenticated,
    ]
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
    ]
    filterset_class = ObjectiveFilter

    def get_queryset(self):
        if not has_access_to_objective_report(self.request):
            raise PermissionDenied(
                {"Permission denied to view objective report"}
            )

        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Objective report list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)
