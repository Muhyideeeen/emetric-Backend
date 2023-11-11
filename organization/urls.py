"""
organization setup url config
"""
from django.urls import path

from organization.views import (
    # corporate Level
    CorporateLevelView,
    GetAllCorporateLevelView,
    UpdateRetrieveCorporateLevelView,
    MultipleCorporateLevelDeleteView,
    CorporateLevelExportView,
    # Divisional Level
    DivisionalLevelView,
    GetAllDivisionalLevelView,
    UpdateRetrieveDivisionalLevelView,
    MultipleDivisionDeleteView,
    DivisionalLevelExportView,
    # Group Level
    GroupLevelView,
    GetAllGroupLevelView,
    UpdateRetrieveGroupLevelView,
    MultipleGroupDeleteView,
    GroupLevelExportView,
    # Departmental Level
    DepartmentalLevelView,
    GetAllDepartmentalLevelView,
    UpdateRetrieveDepartmentalLevelView,
    MultipleDepartmentDeleteView,
    DepartmentalLevelExportView,
    # Unit Level
    UnitLevelView,
    GetAllUnitLevelView,
    UpdateRetrieveUnitLevelView,
    MultipleUnitDeleteView,
    UnitLevelExportView,
    #  Bulk update
    OrganisationImportView,
)

app_name = "organization"

urlpatterns = [
    # corporate Level
    path(
        "corporate-level/create/",
        CorporateLevelView.as_view(),
        name="corporate_level-create",
    ),
    path(
        "corporate-level/detail/<str:organisation_short_name>/<str:uuid>/",
        UpdateRetrieveCorporateLevelView.as_view(),
        name="corporate_level-detail",
    ),
    path(
        "corporate-level/list/<str:organisation_short_name>/",
        GetAllCorporateLevelView.as_view(),
        name="corporate_level-list",
    ),
    path(
        "corporate-level/delete/<str:organisation_short_name>/",
        MultipleCorporateLevelDeleteView.as_view(),
        name="corporate_level-delete",
    ),
    path(
        "corporate-level/export/<str:organisation_short_name>/",
        CorporateLevelExportView.as_view(),
        name="corporate_level-export",
    ),
    # Divisional Level
    path(
        "divisional-level/create/",
        DivisionalLevelView.as_view(),
        name="divisional_level",
    ),
    path(
        "divisional-level/detail/<str:organisation_short_name>/<str:uuid>/",
        UpdateRetrieveDivisionalLevelView.as_view(),
        name="divisional_level-detail",
    ),
    path(
        "divisional-level/list/<str:organisation_short_name>/",
        GetAllDivisionalLevelView.as_view(),
        name="divisional_level-list",
    ),
    path(
        "divisional-level/delete/<str:organisation_short_name>/",
        MultipleDivisionDeleteView.as_view(),
        name="divisional_level-delete",
    ),
    path(
        "divisional-level/export/<str:organisation_short_name>/",
        DivisionalLevelExportView.as_view(),
        name="divisional_level-export",
    ),
    # Group Level
    path("group-level/create/", GroupLevelView.as_view(), name="group_level"),
    path(
        "group-level/detail/<str:organisation_short_name>/<str:uuid>/",
        UpdateRetrieveGroupLevelView.as_view(),
        name="group_level-detail",
    ),
    path(
        "group-level/list/<str:organisation_short_name>/",
        GetAllGroupLevelView.as_view(),
        name="group_level-list",
    ),
    path(
        "group-level/delete/<str:organisation_short_name>/",
        MultipleGroupDeleteView.as_view(),
        name="group_level-delete",
    ),
    path(
        "group-level/export/<str:organisation_short_name>/",
        GroupLevelExportView.as_view(),
        name="group_level-export",
    ),
    # Departmental Level
    path(
        "departmental-level/create/",
        DepartmentalLevelView.as_view(),
        name="department_level",
    ),
    path(
        "departmental-level/detail/<str:organisation_short_name>/<str:uuid>/",
        UpdateRetrieveDepartmentalLevelView.as_view(),
        name="departmental_level-detail",
    ),
    path(
        "departmental-level/list/<str:organisation_short_name>/",
        GetAllDepartmentalLevelView.as_view(),
        name="departmental_level-list",
    ),
    path(
        "departmental-level/delete/<str:organisation_short_name>/",
        MultipleDepartmentDeleteView.as_view(),
        name="departmental_level-delete",
    ),
    path(
        "departmental-level/export/<str:organisation_short_name>/",
        DepartmentalLevelExportView.as_view(),
        name="departmental_level-export",
    ),
    # Unit level
    path("unit-level/create/", UnitLevelView.as_view(), name="unit_level"),
    path(
        "unit-level/detail/<str:organisation_short_name>/<str:uuid>/",
        UpdateRetrieveUnitLevelView.as_view(),
        name="unit_level-detail",
    ),
    path(
        "unit-level/list/<str:organisation_short_name>/",
        GetAllUnitLevelView.as_view(),
        name="unit_level-list",
    ),
    path(
        "unit-level/delete/<str:organisation_short_name>/",
        MultipleUnitDeleteView.as_view(),
        name="unit_level-delete",
    ),
    path(
        "unit-level/export/<str:organisation_short_name>/",
        UnitLevelExportView.as_view(),
        name="unit_level-export",
    ),
    # bulk update
    path(
        "bulk-add/",
        OrganisationImportView.as_view(),
        name="organisation-bulk-add",
    ),
]
