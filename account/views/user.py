from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from django.db import connection

from account.models import Role, EmailInvitation
from account.serializers import (
    OrganisationSerializer,
    UserRoleSerializer,
    ResendActivationMailSerializer,
)
from client.models import Client
from core.utils import response_data, CustomPagination
from core.utils.permissions import (
    IsOrganisationOwnerOrReadOnly,
    IsSuperAdminUserOnly,
    IsAdminUserOnly,
    IsAdminOrSuperAdminOrReadOnly,
)
from core.utils.custom_parser import NestedMultipartParser
from core.utils.tenant_management import delete_client


User = get_user_model()


def check_object(
    get_queryset,
    filter_queryset,
    lookup_url_kwarg,
    lookup_field,
    kwargs,
    klass,
    request,
    check_object_permissions,
    value_to_look_up,
):
    queryset = filter_queryset(get_queryset())
    # Perform the lookup filtering.
    lookup_url_kwarg = lookup_url_kwarg or lookup_field
    assert lookup_url_kwarg in kwargs, (
        "Expected view %s to be called with a URL keyword argument "
        'named "%s". Fix your URL conf, or set the `.lookup_field` '
        "attribute on the view correctly." % (klass.__name__, lookup_url_kwarg)
    )
    filter_kwargs = {value_to_look_up: kwargs[lookup_url_kwarg]}
    obj = get_object_or_404(queryset, **filter_kwargs)
    # May raise a permission denied
    check_object_permissions(request, obj)
    return obj


class GetAllOrganisationsView(generics.ListAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsSuperAdminUserOnly]
    queryset = Client.objects.all()
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "All organisation", serializer.data)
        return Response(data, status=status.HTTP_200_OK)


class GetAllOrganisationsForAdminsView(generics.ListAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAdminUserOnly]
    queryset = Client.objects.all()
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Get the list of items for this view.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.

        This method should always be used rather than accessing `self.queryset`
        directly, as `self.queryset` gets evaluated only once, and those results
        are cached for all subsequent requests.

        You may want to override this if you need to provide different
        querysets depending on the incoming request.

        (Eg. return a list of items that is specific to the user)
        """
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )

        queryset = Client.objects.filter(owner_email=self.request.user.email)
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "All organisation", serializer.data)
        return Response(data, status=status.HTTP_200_OK)


class CreateOrganisationView(generics.CreateAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Client.objects.all()
    parser_classes = (NestedMultipartParser, JSONParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = response_data(
            201, "Organisation Creation Successful", serializer.data
        )
        return Response(data, status=status.HTTP_201_CREATED)


class GetOrganisationView(generics.RetrieveAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsOrganisationOwnerOrReadOnly]
    queryset = Client.objects.all()
    lookup_field = "company_short_name"

    def get_object(self):
        obj = check_object(
            get_queryset=self.get_queryset,
            filter_queryset=self.filter_queryset,
            lookup_url_kwarg=self.lookup_url_kwarg,
            lookup_field=self.lookup_field,
            kwargs=self.kwargs,
            klass=self.__class__,
            request=self.request,
            check_object_permissions=self.check_object_permissions,
            value_to_look_up="schema_name",
        )
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = response_data(
            200, "Organisation retrieved successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)


class UpdateOrganisationView(generics.UpdateAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsOrganisationOwnerOrReadOnly]
    queryset = Client.objects.all()
    lookup_field = "company_short_name"
    parser_classes = (NestedMultipartParser, JSONParser)

    def get_object(self):
        obj = check_object(
            get_queryset=self.get_queryset,
            filter_queryset=self.filter_queryset,
            lookup_url_kwarg=self.lookup_url_kwarg,
            lookup_field=self.lookup_field,
            kwargs=self.kwargs,
            klass=self.__class__,
            request=self.request,
            check_object_permissions=self.check_object_permissions,
            value_to_look_up="schema_name",
        )
        return obj

    def patch(self, request, *args, **kwargs):
        data = response_data(405, "Method not allowed, use PUT instead", [])
        return Response(data, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        data = response_data(
            200, "Organisation updated successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)


class DeleteOrganisationView(generics.DestroyAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsOrganisationOwnerOrReadOnly]
    queryset = Client.objects.all()
    lookup_field = "company_short_name"

    def get_object(self):
        obj = check_object(
            get_queryset=self.get_queryset,
            filter_queryset=self.filter_queryset,
            lookup_url_kwarg=self.lookup_url_kwarg,
            lookup_field=self.lookup_field,
            kwargs=self.kwargs,
            klass=self.__class__,
            request=self.request,
            check_object_permissions=self.check_object_permissions,
            value_to_look_up="schema_name",
        )
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_client(instance)
        data = response_data(204, "client deleted successful", [])
        return Response(data, status=status.HTTP_204_NO_CONTENT)


class GetCurrentOrganisationView(generics.RetrieveAPIView):
    serializer_class = OrganisationSerializer
    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated]

    def get_object(self):
        client = connection.tenant
        return client


class GetUsersByRoleView(generics.ListAPIView):
    serializer_class = UserRoleSerializer
    pagination_class = CustomPagination
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminUserOnly | IsAdminUserOnly,
    ]
    queryset = User.objects.all()
    lookup_field = "role_name"

    def get_queryset(self):

        try:
            if self.lookup_field is None:
                return None
            request_role = self.kwargs[self.lookup_field]
            role_qs = Role.objects.filter(role=request_role)
            if role_qs.exists():
                role = role_qs.first()
            else:
                return None
            return User.objects.filter(user_role=role)
        except User.DoesNotExist:
            return None


class ResendActivationMailView(generics.GenericAPIView):
    serializer_class = ResendActivationMailSerializer
    permission_classes = [IsAdminOrSuperAdminOrReadOnly]
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_resend(serializer)
        data = response_data(
            200, "Activation mail has been resent successfully"
        )
        return Response(data, status=status.HTTP_200_OK)

    def perform_resend(self, serializer):
        users = serializer.validated_data["user"]

        email_activation_objs = EmailInvitation.objects.filter(user__in=users)
        email_activation_objs.update(timestamp=timezone.now())

        for email_activation_obj in email_activation_objs:
            email_activation_obj.send_invitation()
