"""
objective setup url config
"""
from django.urls import path

from strategy_deck.views import (
    ObjectiveListCreateView,
    ObjectiveDetailView,
    ObjectiveImportView,
    MultipleObjectiveDeleteView,
)

app_name = "objective"

urlpatterns = [
    path("", ObjectiveListCreateView.as_view(), name="objective-create-list"),
    path(
        "bulk-add/", ObjectiveImportView.as_view(), name="objective-bulk-add"
    ),
    path(
        "bulk-delete/",
        MultipleObjectiveDeleteView.as_view(),
        name="objective-bulk-delete",
    ),
    path(
        "<str:objective_id>/",
        ObjectiveDetailView.as_view(),
        name="objective-detail",
    ),
]
