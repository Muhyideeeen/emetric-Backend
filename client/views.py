from django.shortcuts import render
from rest_framework import viewsets,status
from account.views.user import check_object
from core.utils.permissions import IsSuperAdminUserOnly
from .models import Client
from . import serializer
from rest_framework.response import Response
from core.utils import response_data, CustomPagination




class ClientMangerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperAdminUserOnly]
    queryset = Client.objects.all()
    serializer_class = serializer.ClientMangerCleanerSerialzer
    pagination_class = CustomPagination
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

    def create(self, request, *args, **kwargs):
        return None
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "All organisation", serializer.data)
        return Response(data, status=status.HTTP_200_OK)


    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(
            instance, data=request.data
        )        
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        data = response_data(
            200, "Organisation updated successfully", serializer.data
        )
        return Response(data, status=status.HTTP_200_OK)