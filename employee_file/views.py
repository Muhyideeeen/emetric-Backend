import django_filters
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from core.utils import (
    CustomPagination,
    NestedMultipartParser,
    response_data,
    permissions,
)
from employee_file.models import EmployeeFile, EmployeeFileName
from employee_file.serializers import (
    EmployeeFileSerializer,
    EmployeeFileNameSerializer,
)


class EmployeeFileFilter(django_filters.FilterSet):
    """Employee File Filter"""

    employee_id = django_filters.UUIDFilter(
        field_name="employee__uuid",
    )

    class Meta:
        model = EmployeeFile
        fields = [
            "employee_id",
        ]


class EmployeeFileViewSet(viewsets.ModelViewSet):
    """Employee file viewset"""

    serializer_class = EmployeeFileSerializer
    permissions_classes = [IsAuthenticated]
    queryset = EmployeeFile.objects.all()
    parser_classes = (NestedMultipartParser, JSONParser)
    pagination_class = CustomPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = EmployeeFileFilter
    http_method_names = ["get", "post", "delete"]
    lookup_field = "uuid"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "Employee file has been added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Employee file retrieved successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Employee file list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(204, "Employee file deleted successfully", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        employee_file_queryset = cache.get("employee_file_queryset")

        if employee_file_queryset == None:
            employee_file_queryset = self.queryset
            cache.set("employee_file_queryset", employee_file_queryset)
        return employee_file_queryset

class EmployeeFileNameViewSet(viewsets.ModelViewSet):
    """Employee file name viewset"""

    serializer_class = EmployeeFileNameSerializer
    permissions_classes = [permissions.IsAdminOrSuperAdminOrReadOnly]
    queryset = EmployeeFileName.objects.all()
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201,
            "Employee file name has been added successfully",
            serializer.data,
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Employee file name retrieved successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Employee file name list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(
            204, "Employee file name deleted successfully", []
        )
        return Response(data, status=status.HTTP_204_NO_CONTENT)
