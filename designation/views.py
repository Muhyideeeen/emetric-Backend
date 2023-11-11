from django.core.cache import cache
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from core.utils import CustomPagination, response_data
from core.utils.permissions import IsAdminOrHRAdminOrReadOnly
from designation.models import Designation
from designation.serializers import (
    DesignationSerializer,
    DesignationImportSerializer,
    MultipleDesignationSerializer,
)


class DesignationCreateListView(generics.ListCreateAPIView):
    serializer_class = DesignationSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Designation.objects.all()
    pagination_class = CustomPagination
    filter_backends = [
        filters.SearchFilter,
    ]
    search_fields = [
        "=corporate_level__uuid",
        "=corporate_level__slug",
        "=department__uuid",
        "=department__slug",
        "=division__uuid",
        "=division__slug",
        "=group__uuid",
        "=group__slug",
        "=unit__uuid",
        "=unit__slug",
    ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Designation list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "Designation added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        designation_queryset = cache.get("designation_queryset")

        if designation_queryset == None:
            designation_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("designation_queryset", designation_queryset)
        return designation_queryset


class DesignationDetailUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = DesignationSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Designation.objects.all()
    lookup_field = "designation_id"

    def patch(self, request, *args, **kwargs):
        data = response_data(
            405, "This method is not allowed for this resource", []
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Designation retrieved successfully", serializer.data
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
            200, "Designation updated successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(204, "Designation deleted successfully", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        designation_queryset = cache.get("designation_queryset")

        if designation_queryset == None:
            designation_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("designation_queryset", designation_queryset)
        return designation_queryset


class DesignationImportView(generics.CreateAPIView):
    serializer_class = DesignationImportSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Designation.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201,
            "Designations have been added from excel sheet successfully",
            [],
        )
        return Response(data, status=status.HTTP_201_CREATED)


class MultipleDesignationDeleteView(generics.GenericAPIView):
    """The view for deleting multiple designations"""

    serializer_class = MultipleDesignationSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Designation.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_multiple_delete(serializer)
        data = response_data(200, "Designations deleted successfully")
        return Response(data, status=status.HTTP_200_OK)

    def perform_multiple_delete(self, serializer):
        designations = serializer.validated_data["designation"]
        for designation in designations:
            designation.delete()
