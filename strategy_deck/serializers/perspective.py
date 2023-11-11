from typing import Dict, List
from pyexcel_xlsx import get_data

from rest_framework import serializers
from core.utils.bulk_upload import extract_key_message
from core.utils.validators import validate_file_extension_for_xlsx

from strategy_deck.models import Perspective


class PerspectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perspective
        fields = ["name", "perspective_id", "target_point"]
        extra_kwargs = {
            "perspective_id": {"read_only": True},
            "target_point": {"read_only": True},
        }

    def validate_name(self, value: str):
        if self.context["request"]._request.method == "POST":
            if self.Meta.model.objects.filter(name=value.lower()).exists():
                raise serializers.ValidationError(
                    {"name": "name is already taken"}
                )
        return value

    def create(self, validated_data: Dict):
        return super(PerspectiveSerializer, self).create(
            validated_data=validated_data
        )

    def update(self, instance, validated_data):
        return super(PerspectiveSerializer, self).update(
            instance=instance, validated_data=validated_data
        )


class PerspectiveImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))

        error_arr = []
        fields = ("name",)

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                data = dict(zip(fields, line_from_file))

                serializer = PerspectiveSerializer(
                    data=data, many=False, context=self.context
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            except serializers.ValidationError as _:
                print(_)
                errors = _.detail
                key, message = extract_key_message(errors)
                error_arr.append(
                    {"key": key, "message": message, "line": index + 2}
                )

            except Exception as _:
                print(_)
                error_arr.append(
                    {"key": "unknown", "message": _, "line": index + 2}
                )

        if error_arr:
            raise serializers.ValidationError({"import error": error_arr})
        return {"perspective": "Perspective has been created"}
