"""
Employee setup url config
"""
from django.urls import path

from employee.views import (
    EmployeeListCreateView,
    EmployeeImportView,
    EmployeeDetailUpdateDestroyView,
    MultipleEmployeeDeleteView,
    EmployeeExportView,
)

app_name = "employee"

urlpatterns = [
    path("", EmployeeListCreateView.as_view(), name="employee-create-list"),
    path("bulk-add/", EmployeeImportView.as_view(), name="employee-invite"),
    path(
        "bulk-delete/",
        MultipleEmployeeDeleteView.as_view(),
        name="employee-delete",
    ),
    path("export/", EmployeeExportView.as_view(), name="employee-export"),
    path(
        "<str:uuid>/",
        EmployeeDetailUpdateDestroyView.as_view(),
        name="employee-retrieve",
    ),
]
