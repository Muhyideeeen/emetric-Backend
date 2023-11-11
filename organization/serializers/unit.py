from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import serializers

from client.models import Client
from core.utils.eager_loading import EagerLoadingMixin
from employee.serializers import UserSerializer
from organization.models import CorporateLevel, Department, Unit
from core.utils.check_org_name_and_set_schema import (
    check_organization_name_and_set_appropriate_schema,
)
from organization.serializers.corporate_serializer_helper import (
    NestedCorporateLevelSerializer,
)

User = get_user_model()


class NestedDepartmentLevelSerializer(serializers.ModelSerializer):
    organisation_short_name = serializers.CharField(
        required=True, write_only=True
    )
    name = serializers.CharField(required=True)

    class Meta:
        model = Department
        fields = ["name", "organisation_short_name", "uuid", "slug"]
        extra_kwargs = {
            "uuid": {"read_only": True},
            "slug": {"read_only": True},
        }

    def validate_name(self, value):
        request_data = self.context.get("request").data
        organisation_short_name = request_data.get("organisation_short_name")
        tenant_exist_qs = Client.objects.filter(
            schema_name=organisation_short_name.lower()
        )
        if not tenant_exist_qs.exists():
            raise serializers.ValidationError(
                {
                    "organisation_short_name": "Organisation short name does not exist"
                }
            )
        connection.set_schema(schema_name=organisation_short_name)
        if not Department.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                {"name": "This departmental level name does not exist"}
            )
        connection.set_schema(schema_name="public")
        return value


class UnitLevelSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    name = serializers.CharField(required=True)
    organisation_short_name = serializers.CharField(required=True)
    corporate_level = NestedCorporateLevelSerializer(
        many=False, required=False
    )
    department = NestedDepartmentLevelSerializer(many=False, required=False)
    employee_count = serializers.SerializerMethodField()
    team_lead = UserSerializer(many=False, required=False)

    select_related_fields = (
        "organisation_short_name",
        "team_lead",
        "corporate_level",
        "department",
    )
    prefetch_related_fields = ("unit_employee",)

    def get_employee_count(self, obj):
        """Returns total employee count linked to object"""
        unit_employee_count = len(obj.unit_employee.all())
        return unit_employee_count

    class Meta:
        model = Unit
        fields = [
            "name",
            "organisation_short_name",
            "uuid",
            "slug",
            "corporate_level",
            "department",
            "employee_count",
            "team_lead",
        ]
        extra_kwargs = {
            "uuid": {"read_only": True},
            "slug": {"read_only": True},
        }

    def create(self, validated_data):
        name = validated_data.get("name")
        organisation_short_name = validated_data.get("organisation_short_name")
        corporate_level = validated_data.get("corporate_level", None)
        department = validated_data.get("department", None)

        corporate_level_name = department_level_name = None
        if corporate_level:
            corporate_level_name = corporate_level.get("name")
        if department:
            department_level_name = department.get("name")

        if department and corporate_level:
            raise serializers.ValidationError(
                {
                    "corporate_level": "Use department only, you cannot use both department and "
                    "corporate level in creating a unit"
                }
            )

        user_email = self.context["request"]._request.user.email
        tenant = check_organization_name_and_set_appropriate_schema(
            organisation_short_name, user_email
        )

        unit_qs = Unit.objects.filter(name=name.lower())
        if unit_qs.exists():
            raise serializers.ValidationError(
                {
                    "name": "Unit level name is not available, choose another name"
                }
            )

        unit = self.create_unit(
            corporate_level,
            corporate_level_name,
            department,
            department_level_name,
            name,
            tenant,
        )
        return unit

    @staticmethod
    def create_unit(
        corporate_level,
        corporate_level_name,
        department,
        department_level_name,
        name,
        tenant,
    ):
        unit = None
        if department is not None:
            department = Department.objects.get(
                name=department_level_name.lower()
            )
            unit = Unit.objects.create(
                name=name,
                organisation_short_name=tenant,
                department=department,
            )
        elif department is None and corporate_level is None:
            raise serializers.ValidationError(
                {
                    "corporate_level": "Corporate level is required, if the organisation does not have a department"
                }
            )
        elif department is None and corporate_level is not None:
            corporate_level = CorporateLevel.objects.get(
                name=corporate_level_name.lower()
            )
            unit = Unit.objects.create(
                name=name,
                organisation_short_name=tenant,
                corporate_level=corporate_level,
            )
        return unit

    def update(self, instance, validated_data):
        organisation_short_name = validated_data.pop("organisation_short_name")
        name = validated_data.pop("name")
        validated_data = {"name": name}
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

        return super(UnitLevelSerializer, self).update(
            instance=instance, validated_data=validated_data
        )


class MiniUnitLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = (
            "name",
            "uuid",
            "slug",
        )


class MultipleUnitSerializer(serializers.Serializer):
    unit = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Unit.objects.all(),
        required=True,
        many=True,
    )
