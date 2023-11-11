from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from account.models import Role
from client.models import Client
from core.utils.eager_loading import EagerLoadingMixin
from employee.serializers import UserSerializer
from organization.models import CorporateLevel
from organization.serializers.department import MiniDepartmentLevelSerializer
from organization.serializers.division import MiniDivisionLevelSerializer
from organization.serializers.groups import MiniGroupLevelSerializer
from organization.serializers.unit import MiniUnitLevelSerializer


User = get_user_model()


class CorporateLevelSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    name = serializers.CharField(required=True)
    organisation_short_name = serializers.CharField(required=True)
    division = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    team_lead = UserSerializer(many=False, required=False)

    select_related_fields = ("organisation_short_name", "team_lead")
    prefetch_related_fields = (
        "corporate_level_division",
        "corporate_level_group",
        "corporate_level_department",
        "corporate_level_unit",
        "corporate_level_employee",
    )

    def get_division(self, obj: CorporateLevel):
        """Returns divisions linked to object"""
        return MiniDivisionLevelSerializer(
            obj.corporate_level_division.all(), many=True
        ).data

    def get_group(self, obj):
        """Returns groups linked to object"""
        return MiniGroupLevelSerializer(
            obj.corporate_level_group.all(), many=True
        ).data

    def get_department(self, obj):
        """Returns departments linked to object"""
        return MiniDepartmentLevelSerializer(
            obj.corporate_level_department.all(), many=True
        ).data

    def get_unit(self, obj):
        """Returns units linked to object"""
        return MiniUnitLevelSerializer(
            obj.corporate_level_unit.all(), many=True
        ).data

    def get_employee_count(self, obj):
        """Returns total employee count linked to object"""
        corporate_level_employee_count = (
            obj.corporate_level_employee.all().count()
        )
        divisions = obj.corporate_level_division.all()

        # nested technique - Not cool!
        for division in divisions:
            corporate_level_employee_count += (
                division.division_employee.all().count()
            )
            groups = division.division_group.all()
            for group in groups:
                corporate_level_employee_count += (
                    group.group_employee.all().count()
                )
                departments = group.group_department.all()
                for department in departments:
                    corporate_level_employee_count += (
                        department.department_employee.all().count()
                    )
                    units = department.department_unit.all()
                    for unit in units:
                        corporate_level_employee_count += (
                            unit.unit_employee.all().count()
                        )

        return corporate_level_employee_count

    class Meta:
        model = CorporateLevel
        fields = [
            "name",
            "organisation_short_name",
            "uuid",
            "slug",
            "division",
            "group",
            "department",
            "unit",
            "employee_count",
            "team_lead",
        ]
        extra_kwargs = {
            "uuid": {"read_only": True},
            "slug": {"read_only": True},
        }

    def create(self, validated_data):
        name = validated_data.get("name")
        organisation_short_name = validated_data.get(
            "organisation_short_name"
        ).lower()

        tenant_exist_qs = Client.objects.filter(
            schema_name=organisation_short_name.lower()
        )
        tenant = tenant_exist_qs.first()
        if not tenant_exist_qs.exists():
            raise serializers.ValidationError(
                {
                    "organisation_short_name": "Organisation short name does not exist"
                }
            )
        connection.set_schema(schema_name=organisation_short_name)

        user_email = self.context["request"]._request.user.email
        if not User.objects.filter(
            email=user_email, user_role__role__in=[Role.SUPER_ADMIN, Role.ADMIN_HR]
        ).exists():
            raise PermissionDenied(
                {
                    "organisation_short_name": "Permission denied, You don'nt have access to this org"
                }
            )

        corporate_name_qs = CorporateLevel.objects.filter(name=name.lower())
        if corporate_name_qs.exists():
            raise serializers.ValidationError(
                {
                    "name": "Corporate level name is not available, choose another name"
                }
            )

        corporate_level = CorporateLevel.objects.create(
            name=name, organisation_short_name=tenant
        )

        return corporate_level

    def update(self, instance, validated_data):
        organisation_short_name = validated_data.pop(
            "organisation_short_name"
        ).lower()

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

        user_email = self.context["request"]._request.user.email
        if not User.objects.filter(
            email=user_email, user_role__role=Role.SUPER_ADMIN
        ).exists():
            raise PermissionDenied(
                {
                    "organisation_short_name": "Permission denied, You don'nt have access to this org"
                }
            )

        return super(CorporateLevelSerializer, self).update(
            instance=instance, validated_data=validated_data
        )


class MultipleCorporateLevelSerializer(serializers.Serializer):
    corporate_level = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=CorporateLevel.objects.all(),
        required=True,
        many=True,
    )
