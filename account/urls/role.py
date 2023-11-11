"""
role url config
"""
from django.urls import path

from account.views.role import RoleListView

app_name = "role"

urlpatterns = [
    path("", RoleListView.as_view(), name="roles-list"),
]
