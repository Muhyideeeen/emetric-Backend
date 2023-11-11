"""
user auth url config
"""
from django.urls import path

from account.views.user import (
    CreateOrganisationView,
    GetOrganisationView,
    UpdateOrganisationView,
    GetAllOrganisationsView,
    GetAllOrganisationsForAdminsView,
    DeleteOrganisationView,
)

app_name = "user"

urlpatterns = [
    path(
        "organisation/all/",
        GetAllOrganisationsView.as_view(),
        name="organisation-list",
    ),
    path(
        "organisation/client/all/",
        GetAllOrganisationsForAdminsView.as_view(),
        name="organisation-client-list",
    ),
    path(
        "organisation/create/",
        CreateOrganisationView.as_view(),
        name="organisation-create",
    ),
    path(
        "organisation/retrieve/<str:company_short_name>/",
        GetOrganisationView.as_view(),
        name="organisation-retrieve",
    ),
    path(
        "organisation/update/<str:company_short_name>/",
        UpdateOrganisationView.as_view(),
        name="organisation-update",
    ),
    path(
        "organisation/delete/<str:company_short_name>/",
        DeleteOrganisationView.as_view(),
        name="organisation-delete",
    ),
]
