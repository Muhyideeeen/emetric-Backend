from math import ceil
from rest_framework import status, pagination
from rest_framework.response import Response

from core.utils import response_data
from e_metric_api.settings import REST_FRAMEWORK


class CustomPagination(pagination.PageNumberPagination):
    page_size = REST_FRAMEWORK.get("PAGE_SIZE")
    page_size_query_param = "page_size"
    # max_page_size = 50
    page_query_param = "page"

    def get_paginated_response(self, data):
        data = response_data(200, "All data", data)
        data["count"] = self.page.paginator.count
        data["next"] = self.get_next_link()
        data["previous"] = self.get_previous_link()
        data["page_count"] = ceil(data["count"] / self.page_size)
        return Response(data, status=status.HTTP_200_OK)
