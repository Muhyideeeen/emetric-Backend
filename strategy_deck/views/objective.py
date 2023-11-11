import django_filters
from django.core.cache import cache
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from core.utils import CustomPagination, response_data
from core.utils.permissions import (
    IsSuperAdminUserOnly,
    IsAdminUserOnly,
    IsAdminOrSuperAdminOrReadOnly,
)
from strategy_deck.models import Objective
from strategy_deck.serializers import ObjectiveSerializer
from strategy_deck.serializers.objective import (
    ObjectiveImportSerializer,
    MultipleObjectiveSerializer,
)


class ObjectiveFilter(django_filters.FilterSet):
    objective_status = django_filters.MultipleChoiceFilter(
        field_name="objective_status",
        choices=Objective.OBJECTIVE_STATUS_CHOICES,
    )
    start_date = django_filters.DateFromToRangeFilter(field_name="start_date")

    class Meta:
        model = Objective
        fields = ["objective_status", "start_date"]


class ObjectiveListCreateView(generics.ListCreateAPIView):
    serializer_class = ObjectiveSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdminOrReadOnly]
    queryset = Objective.objects.all()
    pagination_class = CustomPagination
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ObjectiveFilter
    search_fields = ("name",)
    ordering_fields = (
        "name",
        "start_date",
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "objective list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "objective added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        objective_queryset = cache.get("objective_queryset")

        if objective_queryset == None:
            objective_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("objective_queryset", objective_queryset)
        return objective_queryset


class ObjectiveDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ObjectiveSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdminOrReadOnly]
    queryset = Objective.objects.all()
    lookup_field = "objective_id"

    def patch(self, request, *args, **kwargs):
        data = response_data(
            405, "This method is not allowed for this resource", []
        )
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Objective retrieved successfully", serializer.data
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
                "Objective and recurring Objectives updated successfully",
                serializer.data,
            )
        else:
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = response_data(
                200, "Objective updated successfully", serializer.data
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
                204,
                "Objective and recurring Objectives deleted successfully",
                [],
            )
        else:
            self.perform_destroy(instance)
            data = response_data(204, "Objective deleted successfully", [])

        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy_all(self, instance):
        """Perform delete all recurring objectives"""
        objectives = Objective.objects.filter(
            name=instance.name,
            start_date__gte=instance.start_date,
            objective_status=Objective.PENDING,
        )
        objectives.delete()


class ObjectiveImportView(generics.CreateAPIView):
    serializer_class = ObjectiveImportSerializer
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminUserOnly | IsAdminUserOnly,
    ]
    queryset = Objective.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201, "Objectives have been added from excel sheet successfully", []
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        objective_queryset = cache.get("objective_queryset")

        if objective_queryset == None:
            objective_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("objective_queryset", objective_queryset)
        return objective_queryset


class MultipleObjectiveDeleteView(generics.GenericAPIView):
    """The view for deleting multiple objectives"""

    serializer_class = MultipleObjectiveSerializer
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminUserOnly | IsAdminUserOnly,
    ]
    queryset = Objective.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_multiple_delete(serializer)
        data = response_data(200, "Objective deleted successfully")
        return Response(data, status=status.HTTP_200_OK)

    def perform_multiple_delete(self, serializer):
        objectives = serializer.validated_data["objective"]
        for objective in objectives:
            objective.delete()
