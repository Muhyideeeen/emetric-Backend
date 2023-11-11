"""
initiative setup url config
"""
from django.urls import path

from strategy_deck.views import (
    InitiativeDetailView,
    InitiativeListCreateView,
    InitiativeImportView,
    MultipleInitiativeDeleteView,
)

app_name = "initiative"

urlpatterns = [
    path(
        "", InitiativeListCreateView.as_view(), name="initiative-create-list"
    ),
    path(
        "bulk-add/", InitiativeImportView.as_view(), name="initiative-bulk-add"
    ),
    path(
        "bulk-delete/",
        MultipleInitiativeDeleteView.as_view(),
        name="initiative-bulk-delete",
    ),
    path(
        "<str:initiative_id>/",
        InitiativeDetailView.as_view(),
        name="initiative-detail",
    ),
]
