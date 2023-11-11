from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from career_path.models import CareerPath
from career_path.serializers import (
    CareerPathSerializer,
    CareerPathImportSerializer,
    MultipleCareerPathSerializer,
)
from core.utils import CustomPagination, response_data
from core.utils.permissions import IsAdminOrHRAdminOrReadOnly


class CareerPathCreateListView(generics.ListCreateAPIView):
    serializer_class = CareerPathSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = CareerPath.objects.all()
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "career path list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "career path added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        career_path_queryset = cache.get("career_path_queryset")

        if career_path_queryset == None:
            career_path_queryset = CareerPath.objects.all()
            cache.set("career_path_queryset", career_path_queryset)
        return career_path_queryset


class CareerPathDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CareerPathSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = CareerPath.objects.all()
    lookup_field = "career_path_id"

    def patch(self, request, *args, **kwargs):
        data = response_data(
            405, "This method is not allowed for this resource", []
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "career path retrieved successfully", serializer.data
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
            200, "career path updated successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(204, "career path deleted successfully", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        career_path_queryset = cache.get("career_path_queryset")

        if career_path_queryset == None:
            career_path_queryset = CareerPath.objects.all()
            cache.set("career_path_queryset", career_path_queryset)
        return career_path_queryset


class CareerPathImportView(generics.CreateAPIView):
    serializer_class = CareerPathImportSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = CareerPath.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201,
            "Career Path have been added from excel sheet successfully",
            [],
        )
        return Response(data, status=status.HTTP_201_CREATED)


class MultipleCareerPathDeleteView(generics.GenericAPIView):
    """The view for deleting multiple career paths"""

    serializer_class = MultipleCareerPathSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = CareerPath.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_multiple_delete(serializer)
        data = response_data(200, "CareerPath deleted successfully")
        return Response(data, status=status.HTTP_200_OK)

    def perform_multiple_delete(self, serializer):
        career_paths = serializer.validated_data["career_path"]
        for career_path in career_paths:
            career_path.delete()
