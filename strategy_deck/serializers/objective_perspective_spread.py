from django.contrib.auth import get_user_model
from rest_framework import serializers

from strategy_deck.models import Perspective, ObjectivePerspectiveSpread

User = get_user_model()


class OwnerSerializer(serializers.ModelSerializer):
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
                    {"owner.email": "email provided is not a valid email"}
                )
        return value


class NestedPerspectiveSerializer(serializers.ModelSerializer):
    perspective_id = serializers.UUIDField(required=True)
    relative_point = serializers.DecimalField(
        write_only=True, decimal_places=2, max_digits=18
    )

    class Meta:
        model = Perspective
        fields = [
            "name",
            "perspective_id",
            "relative_point",
            "target_point",
        ]
        extra_kwargs = {
            "name": {"read_only": True},
            "target_point": {"read_only": True},
        }

    def validate_perspective_id(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(objective_id=value).exists():
                raise serializers.ValidationError(
                    {
                        "Perspective.perspective_id": "Perspective id is not a valid id"
                    }
                )
        return value


class ObjectivePerspectiveSpreadSerializer(serializers.ModelSerializer):
    perspective = NestedPerspectiveSerializer(many=False, required=True)
    relative_point = serializers.DecimalField(
        required=True, decimal_places=2, max_digits=18
    )

    class Meta:
        model = ObjectivePerspectiveSpread
        fields = [
            "objective",
            "perspective",
            "relative_point",
            "objective_perspective_id",
            "objective_perspective_point",
        ]
        extra_kwargs = {
            "objective_perspective_id": {"read_only": True},
            "objective": {"read_only": True},
            "relative_point": {"read_only": True},
            "objective_perspective_point": {"read_only": True},
        }
