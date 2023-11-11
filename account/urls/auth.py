"""
user auth url config
"""
from django.urls import path

from account.urls.shared import shared_auth_url
from account.views.auth import (
    RegisterView,
    RegisterAdminView,
    EmailValidateView,
)

app_name = "public-auth"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "register/admin/", RegisterAdminView.as_view(), name="register-admin"
    ),
    path(
        "validate-email/", EmailValidateView.as_view(), name="email-validate"
    ),
] + shared_auth_url
