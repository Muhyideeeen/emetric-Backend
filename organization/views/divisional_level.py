from django.db import connection
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response

from client.models import Client
from core.utils import response_data, CustomPagination
from core.utils.mixins import ExportMixin
from core.utils.permissions import IsAdminOrHRAdminOrReadOnly
from organization.models import Division
from organization.resources.division import DivisionResource
from organization.serializers import (
    DivisionLevelSerializer,
    MultipleDivisionSerializer,
)


class DivisionalLevelView(generics.CreateAPIView):
    serializer_class = DivisionLevelSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Division.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "Divisional level created Successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)


class GetAllDivisionalLevelView(generics.ListAPIView):
    serializer_class = DivisionLevelSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Division.objects.all()
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
            queryset = Division.objects.filter(
                organisation_short_name=request_organisation_short_name
            )
            val = self.get_serializer_class().setup_eager_loading(queryset)
            return val
        except Division.DoesNotExist:
            return []

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "All Divisional level", serializer.data)
        return Response(data, status=status.HTTP_200_OK)


class UpdateRetrieveDivisionalLevelView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DivisionLevelSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Division.objects.all()
    lookup_fields = ["organisation_short_name", "uuid"]

    def get_object(self):
        request_organisation_short_name = None
        for field in self.lookup_fields:
            if field == "organisation_short_name":
                request_organisation_short_name = self.kwargs[field]

        if not Client.objects.filter(
            schema_name=request_organisation_short_name
        ).exists():
            raise Http404(
                "No matches for organisation name with %s"
                % request_organisation_short_name
            )
        connection.set_schema(schema_name=request_organisation_short_name)

        queryset = self.get_queryset()  # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter_input = {}
        for field in self.lookup_fields:
            try:  # Get the result with one or more fields.
                filter_input[field] = self.kwargs[field]
            except (Exception, KeyError):
                pass
        return get_object_or_404(queryset, **filter_input)

    def patch(self, request, *args, **kwargs):
        data = response_data(
            405, "This method is not allowed for this resource", []
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(200, "Division detail", serializer.data)
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

        data = response_data(200, "Division update", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(204, "Division delete", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)


class MultipleDivisionDeleteView(generics.CreateAPIView):
    """The view for deleting multiple divisions"""

    serializer_class = MultipleDivisionSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Division.objects.all()
    lookup_field = "organisation_short_name"

    def post(self, request, *args, **kwargs):
        if self.lookup_field is None:
            return 404
        request_organisation_short_name = self.kwargs[self.lookup_field]
        if not Client.objects.filter(
            schema_name=request_organisation_short_name
        ).exists():
            return []
        connection.set_schema(schema_name=request_organisation_short_name)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_multiple_delete(serializer)
        data = response_data(200, "Division deleted successfully")
        return Response(data, status=status.HTTP_200_OK)

    def perform_multiple_delete(self, serializer):
        divisions = serializer.validated_data["division"]
        for division in divisions:
            division.delete()


class DivisionalLevelExportView(ExportMixin, generics.GenericAPIView):
    serializer_class = DivisionLevelSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Division.objects.all()
    resource_class = DivisionResource
    lookup_field = "organisation_short_name"
    export_filename = "division_export"

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
            queryset = Division.objects.filter(
                organisation_short_name=request_organisation_short_name
            )
            val = self.get_serializer_class().setup_eager_loading(queryset)
            return val
        except Division.DoesNotExist:
            return []

    def get(self, request, *args, **kwargs):
        return self.export(request, *args, **kwargs)
