"""
Career path setup url config
"""
from django.urls import path

from career_path.views import (
    CareerPathCreateListView,
    CareerPathDetailUpdateDestroyView,
    CareerPathImportView,
    MultipleCareerPathDeleteView,
)

app_name = "career_path"

urlpatterns = [
    path(
        "", CareerPathCreateListView.as_view(), name="career_Path-create-list"
    ),
    path(
        "bulk-add/",
        CareerPathImportView.as_view(),
        name="career_Path-bulk-add",
    ),
    path(
        "bulk-delete/",
        MultipleCareerPathDeleteView.as_view(),
        name="career_Path-delete",
    ),
    path(
        "<str:career_path_id>/",
        CareerPathDetailUpdateDestroyView.as_view(),
        name="career_path-retrieve",
    ),
]
