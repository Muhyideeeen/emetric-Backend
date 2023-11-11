from django.contrib.auth import get_user_model
from django.db import connection

from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from account.models.roles import Role

from client.models import Client


User = get_user_model()


def check_organization_name_and_set_appropriate_schema(
    organisation_short_name, user_email
):
    tenant_exist_qs = Client.objects.filter(
        schema_name=organisation_short_name
    )
    tenant = tenant_exist_qs.first()
    if not tenant_exist_qs.exists():
        raise serializers.ValidationError(
            {
                "organisation_short_name": "Organisation short name does not exist"
            }
        )
    connection.set_schema(schema_name=organisation_short_name)

    if not User.objects.filter(
        email=user_email, user_role__role__in=[Role.SUPER_ADMIN, Role.ADMIN_HR]
    ).exists():
        raise PermissionDenied(
            {
                "organisation_short_name": "Permission denied, You don'nt have access to this org"
            }
        )
    return tenant
