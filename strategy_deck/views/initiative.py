import django_filters
from django.core.cache import cache
from rest_framework import generics, status, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils import CustomPagination, response_data, NestedMultipartParser
from core.utils.permissions import (
    IsAdminOrSuperAdminOrReadOnly,
    IsAdminOrHRAdminOrReadOnly,
)
from strategy_deck.models import Initiative
from strategy_deck.serializers import (
    InitiativeSerializer,
    InitiativeImportSerializer,
    MultipleInitiativeSerializer,
)


class InitiativeFilter(django_filters.FilterSet):
    owner_user_id = django_filters.UUIDFilter(
        field_name="owner__user_id",
    )
    assignor_user_id = django_filters.UUIDFilter(
        field_name="assignor__user_id",
    )
    owner_email = django_filters.CharFilter(
        field_name="owner__email",
    )
    assignor_email = django_filters.CharFilter(
        field_name="assignor__email",
    )
    initiative_id = django_filters.UUIDFilter(field_name="initiative_id")
    initiative_status = django_filters.MultipleChoiceFilter(
        field_name="initiative_status",
        choices=Initiative.INITIATIVE_STATUS_CHOICES,
    )
    upline_objective_id = django_filters.UUIDFilter(
        field_name="upline_objective__objective_id"
    )
    upline_initiative_id = django_filters.UUIDFilter(
        field_name="upline_initiative__initiative_id"
    )
    is_objective_downline = django_filters.BooleanFilter(
        method="filter_is_objective_downline"
    )
    start_date = django_filters.DateFromToRangeFilter(field_name="start_date")

    class Meta:
        model = Initiative
        fields = [
            "owner_user_id",
            "assignor_user_id",
            "owner_email",
            "assignor_email",
            "initiative_id",
            "initiative_status",
            "upline_initiative_id",
            "upline_objective_id",
            "is_objective_downline",
            "start_date",
            "corporate_level__uuid",
            "division__uuid",
            "group__uuid",
            "department__uuid",
            "unit__uuid",
        ]

    def filter_is_objective_downline(self, queryset, name, value):
        """Return initiative that are connected to objectives"""
        return queryset.filter(upline_objective__isnull=not (value))


class InitiativeListCreateView(generics.ListCreateAPIView):
    serializer_class = InitiativeSerializer
    permission_classes = [IsAuthenticated]
    queryset = Initiative.objects.all()
    pagination_class = CustomPagination
    parser_classes = (NestedMultipartParser, JSONParser)
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = InitiativeFilter
    # filter_fields = {
    #     "initiative_status": ["in", "exact"],
    # }
    search_fields = (
        "name",
        "upline_initiative__name",
        "upline_objective__name",
    )
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
        data = response_data(200, "initiative list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "initiative added successfully", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        initiative_queryset = cache.get("initiative_queryset")

        if initiative_queryset == None:
            initiative_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("initiative_queryset", initiative_queryset)
        return initiative_queryset


class InitiativeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InitiativeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdminOrReadOnly]
    queryset = Initiative.objects.all()
    lookup_field = "initiative_id"
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
            200, "Initiative retrieved successfully", serializer.data
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
                "Initiative and recurring Initiatives updated successfully",
                serializer.data,
            )
        else:
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = response_data(
                200, "Initiative updated successfully", serializer.data
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
                "Initiative and recurring Initiatives deleted successfully",
                [],
            )
        else:
            self.perform_destroy(instance)
            data = response_data(204, "Initiative deleted successfully", [])

        return Response(data, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy_all(self, instance):
        """Perform delete all recurring initiatives"""
        initiatives = Initiative.objects.filter(
            name=instance.name,
            start_date__gte=instance.start_date,
            initiative_status=Initiative.PENDING,
        )
        initiatives.delete()

    def get_queryset(self):
        initiative_queryset = cache.get("initiative_queryset")

        if initiative_queryset == None:
            initiative_queryset = (
                self.get_serializer_class().setup_eager_loading(self.queryset)
            )
            cache.set("initiative_queryset", initiative_queryset)
        return initiative_queryset


class InitiativeImportView(generics.CreateAPIView):
    serializer_class = InitiativeImportSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Initiative.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201,
            "Initiatives have been added from excel sheet successfully",
            [],
        )
        return Response(data, status=status.HTTP_201_CREATED)


class MultipleInitiativeDeleteView(generics.GenericAPIView):
    """The view for deleting multiple initiatives"""

    serializer_class = MultipleInitiativeSerializer
    permission_classes = [IsAdminOrHRAdminOrReadOnly]
    queryset = Initiative.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_multiple_delete(serializer)
        data = response_data(200, "Initiative deleted successfully")
        return Response(data, status=status.HTTP_200_OK)

    def perform_multiple_delete(self, serializer):
        initiatives = serializer.validated_data["initiative"]
        for initiative in initiatives:
            initiative.delete()
