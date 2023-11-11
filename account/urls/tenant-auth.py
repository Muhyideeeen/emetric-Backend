"""
user tenant auth url config
"""
from django.urls import path

from account.urls.shared import shared_auth_url
from account.views.auth import EmailInviteValidateView
from account.views.user import ResendActivationMailView

app_name = "tenant-auth"

urlpatterns = [
    path(
        "email-invite/setup/",
        EmailInviteValidateView.as_view(),
        name="email-invite",
    ),
    path(
        "resend-activation-mail/",
        ResendActivationMailView.as_view(),
        name="resend-activation-mail",
    ),
] + shared_auth_url
