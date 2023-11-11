from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from account.models import Role
from account.serializers import RoleSerializer
from core.utils import CustomPagination, response_data


class RoleListView(generics.ListAPIView):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all()
    pagination_class = CustomPagination

    @method_decorator(cache_page(60 * 60 * 2))
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = response_data(200, "Roles list", serializer.data)
        return Response(data, status=status.HTTP_200_OK)
