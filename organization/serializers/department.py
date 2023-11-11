from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import serializers

from client.models import Client
from core.utils.eager_loading import EagerLoadingMixin
from employee.models import Employee
from employee.serializers import UserSerializer
from organization.models import CorporateLevel, Group, Department
from core.utils.check_org_name_and_set_schema import (
    check_organization_name_and_set_appropriate_schema,
)
from organization.serializers.corporate_serializer_helper import (
    NestedCorporateLevelSerializer,
)
from organization.serializers.unit import MiniUnitLevelSerializer

User = get_user_model()


class NestedGroupLevelSerializer(serializers.ModelSerializer):
    organisation_short_name = serializers.CharField(
        required=True, write_only=True
    )
    name = serializers.CharField(required=True)

    class Meta:
        model = Group
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
        if not Group.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                {"name": "This group level name does not exist"}
            )
        connection.set_schema(schema_name="public")
        return value


class DepartmentLevelSerializer(
    serializers.ModelSerializer, EagerLoadingMixin
):
    name = serializers.CharField(required=True)
    organisation_short_name = serializers.CharField(required=True)
    corporate_level = NestedCorporateLevelSerializer(
        many=False, required=False
    )
    group = NestedGroupLevelSerializer(many=False, required=False)
    unit = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    team_lead = UserSerializer(many=False, required=False)

    select_related_fields = (
        "organisation_short_name",
        "team_lead",
        "corporate_level",
        "group",
    )
    prefetch_related_fields = ("department_unit", "department_employee")

    def get_unit(self, obj):
        """Returns units linked to object"""
        return MiniUnitLevelSerializer(
            obj.department_unit.all(), many=True
        ).data

    def get_employee_count(self, obj):
        """Returns total employee count linked to object"""
        department_employee_count = len(obj.department_employee.all())
        units = obj.department_unit.all()

        # nested technique - Not cool!
        for unit in units:
            department_employee_count += len(unit.unit_employee.all())

        return department_employee_count

    class Meta:
        model = Department
        fields = [
            "name",
            "organisation_short_name",
            "uuid",
            "slug",
            "unit",
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
        corporate_level = validated_data.get("corporate_level", None)
        group = validated_data.get("group", None)

        corporate_level_name = group_level_name = None
        if corporate_level:
            corporate_level_name = corporate_level.get("name")
        if group:
            group_level_name = group.get("name")

        if group and corporate_level:
            raise serializers.ValidationError(
                {
                    "corporate_level": "Use group only, you cannot use both group and "
                    "corporate level in creating a group"
                }
            )

        user_email = self.context["request"]._request.user.email
        tenant = check_organization_name_and_set_appropriate_schema(
            organisation_short_name, user_email
        )

        department_qs = Department.objects.filter(name=name.lower())
        if department_qs.exists():
            raise serializers.ValidationError(
                {
                    "name": "Department level name is not available, choose another name"
                }
            )

        department = self.create_department(
            corporate_level,
            corporate_level_name,
            group,
            group_level_name,
            name,
            tenant,
        )

        return department

    @staticmethod
    def create_department(
        corporate_level,
        corporate_level_name,
        group,
        group_level_name,
        name,
        tenant,
    ):
        department = None
        if group is not None:
            group = Group.objects.get(name=group_level_name.lower())
            department = Department.objects.create(
                name=name, organisation_short_name=tenant, group=group
            )
        elif group is None and corporate_level is None:
            raise serializers.ValidationError(
                {
                    "corporate_level": "Corporate level is required, if the organisation does not have a group"
                }
            )
        elif group is None and corporate_level is not None:
            corporate_level = CorporateLevel.objects.get(
                name=corporate_level_name.lower()
            )
            department = Department.objects.create(
                name=name,
                organisation_short_name=tenant,
                corporate_level=corporate_level,
            )
        return department

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

        return super(DepartmentLevelSerializer, self).update(
            instance=instance, validated_data=validated_data
        )


class MiniDepartmentLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = (
            "name",
            "uuid",
            "slug",
        )


class MultipleDepartmentSerializer(serializers.Serializer):
    department = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Department.objects.all(),
        required=True,
        many=True,
    )
