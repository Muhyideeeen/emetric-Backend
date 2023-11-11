from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import serializers

from client.models import Client
from core.utils.eager_loading import EagerLoadingMixin
from employee.serializers import UserSerializer
from organization.models import CorporateLevel, Division, Group
from core.utils.check_org_name_and_set_schema import (
    check_organization_name_and_set_appropriate_schema,
)
from organization.serializers.corporate_serializer_helper import (
    NestedCorporateLevelSerializer,
)
from organization.serializers.department import MiniDepartmentLevelSerializer

User = get_user_model()


class NestedDivisionLevelSerializer(serializers.ModelSerializer):
    organisation_short_name = serializers.CharField(
        required=True, write_only=True
    )
    name = serializers.CharField(required=True)

    class Meta:
        model = Division
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
        if not Division.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                {"name": "This divisional level name does not exist"}
            )
        connection.set_schema(schema_name="public")
        return value


class GroupLevelSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    name = serializers.CharField(required=True)
    organisation_short_name = serializers.CharField(required=True)
    corporate_level = NestedCorporateLevelSerializer(
        many=False, required=False
    )
    division = NestedDivisionLevelSerializer(many=False, required=False)
    department = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    team_lead = UserSerializer(many=False, required=False)

    select_related_fields = (
        "organisation_short_name",
        "team_lead",
        "corporate_level",
        "division",
    )
    prefetch_related_fields = ("group_department", "group_employee")

    def get_department(self, obj):
        """Returns departments linked to object"""
        return MiniDepartmentLevelSerializer(
            obj.group_department.all(), many=True
        ).data

    def get_employee_count(self, obj):
        """Returns total employee count linked to object"""
        group_employee_count = len(obj.group_employee.all())
        departments = obj.group_department.all()

        # nested technique - Not cool!
        for department in departments:
            group_employee_count += len(department.department_employee.all())
            units = department.department_unit.all()
            for unit in units:
                group_employee_count += len(unit.unit_employee.all())

        return group_employee_count

    class Meta:
        model = Group
        fields = [
            "name",
            "organisation_short_name",
            "uuid",
            "slug",
            "corporate_level",
            "division",
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
        division = validated_data.get("division", None)

        corporate_level_name = division_level_name = None
        if corporate_level:
            corporate_level_name = corporate_level.get("name")
        if division:
            division_level_name = division.get("name")

        if division and corporate_level:
            raise serializers.ValidationError(
                {
                    "corporate_level": "Use division only, you cannot use both division and "
                    "corporate level in creating a group"
                }
            )

        user_email = self.context["request"]._request.user.email
        tenant = check_organization_name_and_set_appropriate_schema(
            organisation_short_name, user_email
        )

        group_qs = Group.objects.filter(name=name.lower())
        if group_qs.exists():
            raise serializers.ValidationError(
                {
                    "name": "Group level name is not available, choose another name"
                }
            )

        group = self.create_group(
            corporate_level,
            corporate_level_name,
            division,
            division_level_name,
            name,
            tenant,
        )

        return group

    @staticmethod
    def create_group(
        corporate_level,
        corporate_level_name,
        division,
        division_level_name,
        name,
        tenant,
    ):
        group = None
        if division is not None:
            division = Division.objects.get(name=division_level_name.lower())
            group = Group.objects.create(
                name=name, organisation_short_name=tenant, division=division
            )
        elif division is None and corporate_level is None:
            raise serializers.ValidationError(
                {
                    "corporate_level": "Corporate level is required, if the organisation does not have a division"
                }
            )
        elif division is None and corporate_level is not None:
            corporate_level = CorporateLevel.objects.get(
                name=corporate_level_name.lower()
            )
            group = Group.objects.create(
                name=name,
                organisation_short_name=tenant,
                corporate_level=corporate_level,
            )
        return group

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

        return super(GroupLevelSerializer, self).update(
            instance=instance, validated_data=validated_data
        )


class MiniGroupLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (
            "name",
            "uuid",
            "slug",
        )


class MultipleGroupSerializer(serializers.Serializer):
    group = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Group.objects.all(),
        required=True,
        many=True,
    )
