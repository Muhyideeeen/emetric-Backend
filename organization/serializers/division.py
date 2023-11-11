from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import serializers

from client.models import Client
from core.utils.eager_loading import EagerLoadingMixin
from employee.serializers import UserSerializer
from organization.models import CorporateLevel, Division
from core.utils.check_org_name_and_set_schema import (
    check_organization_name_and_set_appropriate_schema,
)
from organization.serializers.corporate_serializer_helper import (
    NestedCorporateLevelSerializer,
)
from organization.serializers.groups import MiniGroupLevelSerializer

User = get_user_model()


class DivisionLevelSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    name = serializers.CharField(required=True)
    organisation_short_name = serializers.CharField(required=True)
    corporate_level = NestedCorporateLevelSerializer(many=False, required=True)
    group = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    team_lead = UserSerializer(many=False, required=False)

    select_related_fields = (
        "organisation_short_name",
        "team_lead",
        "corporate_level",
    )
    prefetch_related_fields = ("division_group", "division_employee")

    def get_group(self, obj):
        """Returns groups linked to object"""
        return MiniGroupLevelSerializer(
            obj.division_group.all(), many=True
        ).data

    def get_employee_count(self, obj):
        """Returns total employee count linked to object"""
        division_employee_count = len(obj.division_employee.all())
        groups = obj.division_group.all()

        # nested technique - Not cool!
        for group in groups:
            division_employee_count += len(group.group_employee.all())
            departments = group.group_department.all()
            for department in departments:
                division_employee_count += len(
                    department.department_employee.all()
                )
                units = department.department_unit.all()
                for unit in units:
                    division_employee_count += len(unit.unit_employee.all())

        return division_employee_count

    class Meta:
        model = Division
        fields = [
            "name",
            "organisation_short_name",
            "uuid",
            "slug",
            "corporate_level",
            "group",
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
        corporate_level = validated_data.get("corporate_level")
        corporate_level_name = corporate_level.get("name")

        user_email = self.context["request"]._request.user.email
        tenant = check_organization_name_and_set_appropriate_schema(
            organisation_short_name, user_email
        )

        division_qs = Division.objects.filter(name=name.lower())
        if division_qs.exists():
            raise serializers.ValidationError(
                {
                    "name": "Division level name is not available, choose another name"
                }
            )

        corporate_level = CorporateLevel.objects.get(
            name=corporate_level_name.lower()
        )
        division = Division.objects.create(
            name=name,
            organisation_short_name=tenant,
            corporate_level=corporate_level,
        )
        return division

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

        return super(DivisionLevelSerializer, self).update(
            instance=instance, validated_data=validated_data
        )


class MiniDivisionLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = (
            "name",
            "uuid",
            "slug",
        )


class MultipleDivisionSerializer(serializers.Serializer):
    division = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Division.objects.all(),
        required=True,
        many=True,
    )
