from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from core.utils import CustomPagination, response_data
from core.utils.permissions import (
    IsSuperAdminUserOnly,
    IsAdminUserOnly,
    IsAdminOrSuperAdminOrReadOnly,
)
from strategy_deck.models import Perspective
from strategy_deck.serializers import (
    PerspectiveSerializer,
    PerspectiveImportSerializer,
)


class PerspectiveListCreateView(generics.ListCreateAPIView):
    serializer_class = PerspectiveSerializer
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminUserOnly | IsAdminUserOnly,
    ]
    queryset = Perspective.objects.all()
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "perspective list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "perspective added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        perspective_queryset = cache.get("perspective_queryset")

        if perspective_queryset == None:
            perspective_queryset = Perspective.objects.all()
            cache.set("perspective_queryset", perspective_queryset)
        return perspective_queryset


class PerspectiveDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PerspectiveSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdminOrReadOnly]
    queryset = Perspective.objects.all()
    lookup_field = "perspective_id"

    def patch(self, request, *args, **kwargs):
        data = response_data(
            405, "This method is not allowed for this resource", []
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Perspective retrieved successfully", serializer.data
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
            200, "Perspective updated successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        data = response_data(204, "Perspective deleted successfully", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        perspective_queryset = cache.get("perspective_queryset")

        if perspective_queryset == None:
            perspective_queryset = Perspective.objects.all()
            cache.set("perspective_queryset", perspective_queryset)
        return perspective_queryset


class PerspectiveImportView(generics.CreateAPIView):
    serializer_class = PerspectiveImportSerializer
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminUserOnly | IsAdminUserOnly,
    ]
    queryset = Perspective.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201,
            "Perspectives have been added from excel sheet successfully",
            [],
        )
        return Response(data, status=status.HTTP_201_CREATED)
