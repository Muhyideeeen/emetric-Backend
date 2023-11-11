"""
Designation setup url config
"""
from django.urls import path

from designation.views import (
    DesignationCreateListView,
    DesignationDetailUpdateDestroyView,
    DesignationImportView,
    MultipleDesignationDeleteView,
)

app_name = "designation"

urlpatterns = [
    path(
        "", DesignationCreateListView.as_view(), name="designation-create-list"
    ),
    path(
        "bulk-add/",
        DesignationImportView.as_view(),
        name="designation-bulk-add",
    ),
    path(
        "bulk-delete/",
        MultipleDesignationDeleteView.as_view(),
        name="designation-delete",
    ),
    path(
        "<str:designation_id>/",
        DesignationDetailUpdateDestroyView.as_view(),
        name="designation-retrieve",
    ),
]
