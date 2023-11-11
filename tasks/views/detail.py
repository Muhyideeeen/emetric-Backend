import django_filters
from django.core.cache import cache
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from core.utils import CustomPagination, response_data
from core.utils.custom_parser import NestedMultipartParser
from core.utils.permissions import (
    IsTaskAssignorOrAdminOrReadOnly,
    IsTeamLeadOrAdminOrReadOnly,
)
from tasks.models import Task
from tasks.serializers import (
    TaskSerializer,
    TaskImportSerializer,
    MultipleTaskSerializer,
)
from tasks.filter import TaskFilter


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsTeamLeadOrAdminOrReadOnly]
    queryset = Task.objects.all()
    pagination_class = CustomPagination
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    parser_classes = (NestedMultipartParser, JSONParser)
    filterset_class = TaskFilter
    search_fields = (
        "name",
        "upline_initiative__name",
    )
    ordering_fields = (
        "name",
        "task_type",
        "start_date",
        "start_time",
        "routine_option",
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Task list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(201, "Task added successfully", serializer.data)
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        task_queryset = cache.get("task_queryset")

        if task_queryset == None:
            task_queryset = self.get_serializer_class().setup_eager_loading(
                self.queryset
            )
            cache.set("task_queryset", task_queryset)
        return task_queryset


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [
        IsTaskAssignorOrAdminOrReadOnly,
    ]
    queryset = Task.objects.all()
    parser_classes = (NestedMultipartParser, JSONParser)
    lookup_field = "task_id"

    def patch(self, request, *args, **kwargs):
        data = response_data(
            405, "This method is not allowed for this resource", []
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Task retrieved successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        recurring = request.query_params.get("recurring", False) == "True"
        if recurring:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_destroy_all(instance)
            serializer.save()
            data = response_data(
                200,
                "Task and recurring Tasks updated successfully",
                serializer.data,
            )
        else:
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = response_data(
                200, "Task updated successfully", serializer.data
            )

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        recurring = request.query_params.get("recurring", False) == "True"
        instance = self.get_object()
        if recurring:
            self.perform_destroy_all(instance)
            data = response_data(
                200, "Task and recurring Tasks deleted successfully", []
            )
        else:
            self.perform_destroy(instance)
            data = response_data(204, "Task deleted successfully", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy_all(self, instance):
        """Perform delete all recurring tasks"""
        tasks = Task.objects.filter(
            name=instance.name,
            start_date__gte=instance.start_date,
            task_status=Task.PENDING,
        )
        tasks.delete()

    def get_queryset(self):
        task_queryset = cache.get("task_queryset")

        if task_queryset == None:
            task_queryset = self.get_serializer_class().setup_eager_loading(
                self.queryset
            )
            cache.set("task_queryset", task_queryset)
        return task_queryset


class TaskImportView(generics.CreateAPIView):
    serializer_class = TaskImportSerializer
    permission_classes = [IsTeamLeadOrAdminOrReadOnly]
    queryset = Task.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201, "Tasks have been added from excel sheet successfully", []
        )
        return Response(data, status=status.HTTP_201_CREATED)


class MultipleTaskDeleteView(generics.GenericAPIView):
    """The view for deleting multiple objectives"""

    serializer_class = MultipleTaskSerializer
    permission_classes = permission_classes = [IsTeamLeadOrAdminOrReadOnly]
    queryset = Task.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_multiple_delete(serializer)
        data = response_data(200, "Task deleted successfully")
        return Response(data, status=status.HTTP_200_OK)

    def perform_multiple_delete(self, serializer):
        tasks = serializer.validated_data["task"]
        for task in tasks:
            task.delete()
