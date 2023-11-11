import django_filters
from django.core.cache import cache
from django.db import connection
from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from account.models.roles import Role
from client.models import Client

from core.utils import CustomPagination, response_data, NestedMultipartParser
from employee.resources import EmployeeResource
from core.utils.mixins import ExportMixin
from employee.models import Employee
from employee.serializers import (
    EmployeeSerializer,
    EmployeeImportSerializer,
    MultipleEmployeeSerializer,
)
from employee_profile.models.employment_information import (
    EmploymentInformation,
)
from core.utils.permissions import (
    IsAdminOrHRAdminOrReadOnly,
    IsAdminOrHRAdminOrEmployeeOrReadOnly,
)


class EmployeeFilter(FilterSet):
    user__user_role = django_filters.MultipleChoiceFilter(
        field_name="user__user_role__role", choices=Role.ROLE_CHOICES
    )
    upline__email = django_filters.CharFilter(
        field_name="employee_employmentinformation__upline__email"
    )
    designation = django_filters.UUIDFilter(
        field_name="employee_basic_infomation__designation__designation_id"
    )
    status = django_filters.MultipleChoiceFilter(
        field_name="employee_employmentinformation__status",
        choices=EmploymentInformation.EMPLOYEE_TYPE_CHOICES,
    )

    class Meta:
        model = Employee
        fields = [
            "user__user_role",
            "user__email",
            "user__user_id",
            "corporate_level__uuid",
            "division__uuid",
            "group__uuid",
            "department__uuid",
            "unit__uuid",
            "upline__email",
            "designation",
            "status",
        ]


class EmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Employee.objects.all()
    pagination_class = CustomPagination
    parser_classes = (NestedMultipartParser, JSONParser)
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "employee_basic_infomation__designation__name",
        "corporate_level__name",
        "division__name",
        "group__name",
        "department__name",
        "unit__name",
    )
    ordering_fields = (
        "updated_at",
        "user__first_name",
        "user__last_name",
        "employee_basic_infomation__designation__name",
    )
    ordering = ("-updated_at",)
    filterset_class = EmployeeFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Employee list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "Employee added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        employee_queryset = cache.get("employee_queryset")

        if employee_queryset == None:
            employee_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("employee_queryset", employee_queryset)
        return employee_queryset


class EmployeeImportView(generics.CreateAPIView):
    serializer_class = EmployeeImportSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Employee.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201, "Employees added from excel sheet successfully", []
        )
        return Response(data, status=status.HTTP_201_CREATED)


class GetAllEmployeeView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Employee.objects.all()
    pagination_class = CustomPagination
    lookup_field = "organisation_short_name"

    def get_queryset(self):
        try:
            if self.lookup_field is None:
                return []
            request_organisation_short_name = self.kwargs[self.lookup_field]
            if not Client.objects.filter(
                schema_name=request_organisation_short_name
            ).exists():
                return []
            connection.set_schema(schema_name=request_organisation_short_name)
            val = Employee.objects.filter(
                organisation_short_name=request_organisation_short_name
            )
            return val
        except Employee.DoesNotExist:
            return []

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Employee list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)


class EmployeeDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrHRAdminOrEmployeeOrReadOnly]
    queryset = Employee.objects.all()
    lookup_field = "uuid"
    parser_classes = (NestedMultipartParser, JSONParser)

    def patch(self, request, *args, **kwargs):
        data = response_data(
            405, "This method is not allowed for this resource", []
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Employee retrieved successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        data = response_data(
            200, "Employee updated successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(204, "Employee deleted successfully", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        employee_queryset = cache.get("employee_queryset")

        if employee_queryset == None:
            employee_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("employee_queryset", employee_queryset)
        return employee_queryset


class MultipleEmployeeDeleteView(generics.GenericAPIView):
    """The view for deleting multiple employees"""

    serializer_class = MultipleEmployeeSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Employee.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_multiple_delete(serializer)
        data = response_data(200, "Employees deleted successfully")
        return Response(data, status=status.HTTP_200_OK)

    def perform_multiple_delete(self, serializer):
        employees = serializer.validated_data["employee"]
        for employee in employees:
            employee.delete()


class EmployeeExportView(ExportMixin, generics.GenericAPIView):
    """Exports a file from the employee model"""

    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Employee.objects.all()
    resource_class = EmployeeResource
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeFilter
    export_filename = "employee_export"

    def get(self, request, *args, **kwargs):
        return self.export(request, *args, **kwargs)

    def get_queryset(self):
        employee_queryset = cache.get("employee_queryset")

        if employee_queryset == None:
            employee_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("employee_queryset", employee_queryset)
        return employee_queryset
