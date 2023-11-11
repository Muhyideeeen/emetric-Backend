from django.contrib.auth import get_user_model

from rest_framework import serializers
from career_path.models import CareerPath

from designation.models import Designation
from organization.models import (
    CorporateLevel,
    Department,
    Unit,
    Group,
    Division,
)
from tasks.models import Task


User = get_user_model()


class NestedDesignationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)

    class Meta:
        model = Designation
        fields = ("name", "designation_id")
        extra_kwargs = {
            "designation_id": {"read_only": True},
        }

    def validate_name(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(name=value.lower()).exists():
                raise serializers.ValidationError(
                    {
                        "designation.name": "name is not a valid destination name"
                    }
                )
        return value


class NestedCareerPathSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(required=False)

    class Meta:
        model = CareerPath
        fields = ("level", "career_path_id", "name")
        extra_kwargs = {
            "career_path_id": {"read_only": True},
            "name": {"read_only": True},
        }

    def validate_level(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(level=value).exists():
                raise serializers.ValidationError(
                    {
                        "level": f"level {value} is not a valid career path level"
                    }
                )
        return value


class NestedCorporateLevelSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=True)

    class Meta:
        model = CorporateLevel
        fields = ["name", "organisation_short_name", "uuid", "slug"]
        extra_kwargs = {
            "name": {"read_only": True},
            "slug": {"read_only": True},
            "organisation_short_name": {"read_only": True},
        }

    def validate_level_value(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(uuid=value).exists():
                raise serializers.ValidationError(
                    {
                        "uuid": f"{value} is not a valid uuid for a corporate level"
                    }
                )
        return value


class NestedDepartmentLevelSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=True)

    class Meta:
        model = Department
        fields = ["name", "organisation_short_name", "uuid", "slug"]
        extra_kwargs = {
            "name": {"read_only": True},
            "slug": {"read_only": True},
            "organisation_short_name": {"read_only": True},
        }

    def validate_level_value(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(uuid=value).exists():
                raise serializers.ValidationError(
                    {
                        "uuid": f"{value} is not a valid uuid for a departmental level"
                    }
                )
        return value


class NestedDivisionLevelSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=True)

    class Meta:
        model = Division
        fields = ["name", "organisation_short_name", "uuid", "slug"]
        extra_kwargs = {
            "name": {"read_only": True},
            "slug": {"read_only": True},
            "organisation_short_name": {"read_only": True},
        }

    def validate_level_value(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(uuid=value).exists():
                raise serializers.ValidationError(
                    {
                        "uuid": f"{value} is not a valid uuid for a divisional level"
                    }
                )
        return value


class NestedGroupLevelSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=True)

    class Meta:
        model = Group
        fields = ["name", "organisation_short_name", "uuid", "slug"]
        extra_kwargs = {
            "name": {"read_only": True},
            "slug": {"read_only": True},
            "organisation_short_name": {"read_only": True},
        }

    def validate_level_value(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(uuid=value).exists():
                raise serializers.ValidationError(
                    {"uuid": f"{value} is not a valid uuid for a group level"}
                )
        return value


class NestedUnitLevelSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=True)

    class Meta:
        model = Unit
        fields = ["name", "organisation_short_name", "uuid", "slug"]
        extra_kwargs = {
            "name": {"read_only": True},
            "slug": {"read_only": True},
            "organisation_short_name": {"read_only": True},
        }

    def validate_level_value(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(uuid=value).exists():
                raise serializers.ValidationError(
                    {"uuid": f"{value} is not a valid uuid for a unit level"}
                )
        return value


class OwnerOrAssignorSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "user_id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
        )
        extra_kwargs = {
            "user_id": {"read_only": True},
            "first_name": {"read_only": True},
            "last_name": {"read_only": True},
            "phone_number": {"read_only": True},
        }

    def validate_email(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(email=value).exists():
                raise serializers.ValidationError(
                    {"email": "email provided is not a valid email"}
                )
        return value


class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "user_id",
            "first_name",
            "last_name",
            "email",
        )


class NestedTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "task_id",
            "name",
            "task_type",
            "routine_round",
            "start_date",
            "start_time",
            "duration",
            "task_status",
            "target_point",
        )
