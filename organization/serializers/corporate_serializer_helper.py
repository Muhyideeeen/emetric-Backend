from django.db import connection
from rest_framework import serializers

from client.models import Client
from organization.models import CorporateLevel


class NestedCorporateLevelSerializer(serializers.ModelSerializer):
    organisation_short_name = serializers.CharField(
        required=True, write_only=True
    )
    name = serializers.CharField(required=True)

    class Meta:
        model = CorporateLevel
        fields = ["name", "organisation_short_name", "uuid", "slug"]
        extra_kwargs = {
            "uuid": {"read_only": True},
            "slug": {"read_only": True},
        }

    def validate_name(self, value):
        request_data = self.context.get("request").data
        organisation_short_name = request_data.get("organisation_short_name")
        tenant_exist_qs = Client.objects.filter(
            schema_name=organisation_short_name
        )
        if not tenant_exist_qs.exists():
            raise serializers.ValidationError(
                {
                    "organisation_short_name": "Organisation short name does not exist"
                }
            )
        connection.set_schema(schema_name=organisation_short_name)
        if not CorporateLevel.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                {"name": "This corporate level name does not exist"}
            )
        connection.set_schema(schema_name="public")
        return value
