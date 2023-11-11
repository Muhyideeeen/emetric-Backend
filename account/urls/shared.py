from django.urls import path

from account.views.auth import (
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    RequestPasswordResetEmailView,
    PasswordTokenCheckView,
    SetNewPasswordFromResetPasswordEmailView,
    ChangePasswordView,
    RegisterAdminSerializer,
)

shared_auth_url = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "refresh/token/",
        CustomTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "request-password-reset-email/",
        RequestPasswordResetEmailView.as_view(),
        name="request-password-reset-email",
    ),
    path(
        "password-reset-confirm/<str:uid_base64>/<str:token>/",
        PasswordTokenCheckView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "password-reset/",
        SetNewPasswordFromResetPasswordEmailView.as_view(),
        name="password-reset",
    ),
    path(
        "password-update/<str:user_id>/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
]
