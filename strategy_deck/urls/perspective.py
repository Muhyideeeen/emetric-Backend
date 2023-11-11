"""
perspective setup url config
"""
from django.urls import path

from strategy_deck.views import (
    PerspectiveListCreateView,
    PerspectiveDetailView,
    PerspectiveImportView,
)

app_name = "perspective"

urlpatterns = [
    path(
        "", PerspectiveListCreateView.as_view(), name="perspective-create-list"
    ),
    path(
        "bulk-add/",
        PerspectiveImportView.as_view(),
        name="perspective-bulk-add",
    ),
    path(
        "<str:perspective_id>/",
        PerspectiveDetailView.as_view(),
        name="perspective-detail",
    ),
]
