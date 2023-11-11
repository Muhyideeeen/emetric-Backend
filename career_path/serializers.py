from typing import List, Dict
from rest_framework import serializers
from pyexcel_xlsx import get_data

from career_path.models import CareerPath
from core.utils.bulk_upload import extract_key_message
from core.utils.validators import validate_file_extension_for_xlsx


class CareerPathSerializer(serializers.ModelSerializer):
    educational_qualification = serializers.CharField(required=True)
    years_of_experience_required = serializers.IntegerField(
        required=False, min_value=0
    )
    min_age = serializers.IntegerField(required=True, min_value=1)
    max_age = serializers.IntegerField(required=True, min_value=1)
    position_lifespan = serializers.IntegerField(required=True, min_value=1)
    slots_available = serializers.IntegerField(required=True, min_value=1)
    annual_package = serializers.IntegerField(required=True, min_value=0)

    class Meta:
        model = CareerPath
        fields = (
            "name",
            "level",
            "career_path_id",
            "educational_qualification",
            "years_of_experience_required",
            "min_age",
            "max_age",
            "position_lifespan",
            "slots_available",
            "annual_package",
        )
        extra_kwargs = {
            "career_path_id": {"read_only": True},
        }

    def validate_name(self, value: str):
        if self.Meta.model.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                {"name": "name is already taken"}
            )
        return value.lower()

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class CareerPathImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))
        error_arr = []
        fields = (
            "name",
            "level",
            "educational_qualification",
            "years_of_experience_required",
            "min_age",
            "max_age",
            "position_lifespan",
            "slots_available",
            "annual_package",
        )

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                data = dict(zip(fields, line_from_file))
                serializer = CareerPathSerializer(data=data, many=False)
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
        return {"career_path": "Career Path has been created"}


class MultipleCareerPathSerializer(serializers.Serializer):
    career_path = serializers.SlugRelatedField(
        slug_field="career_path_id",
        queryset=CareerPath.objects.all(),
        required=True,
        many=True,
    )
