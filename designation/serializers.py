from rest_framework import serializers
from pyexcel_xlsx import get_data
from typing import List, Dict
from rest_framework import serializers

from core.serializers.nested import (
    NestedCorporateLevelSerializer,
    NestedDepartmentLevelSerializer,
    NestedDivisionLevelSerializer,
    NestedUnitLevelSerializer,
    NestedGroupLevelSerializer,
)
from core.utils.bulk_upload import extract_key_message
from core.utils.custom_data_validation import check_excess_data_count
from core.utils.exception import CustomValidation
from core.utils.process_levels import (
    process_level_by_name_to_dict,
    process_levels,
)
from core.utils.validators import validate_file_extension_for_xlsx
from core.utils.eager_loading import EagerLoadingMixin
from designation.models import Designation
from employee_profile.models.basic_information import BasicInformation


class DesignationSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    name = serializers.CharField(required=True)
    corporate_level = NestedCorporateLevelSerializer(
        many=False, required=False
    )
    department = NestedDepartmentLevelSerializer(many=False, required=False)
    division = NestedDivisionLevelSerializer(many=False, required=False)
    group = NestedGroupLevelSerializer(many=False, required=False)
    unit = NestedUnitLevelSerializer(many=False, required=False)

    select_related_fields = (
        "corporate_level",
        "department",
        "division",
        "group",
        "unit",
    )
    prefetch_related_fields = ()

    class Meta:
        model = Designation
        fields = (
            "name",
            "designation_id",
            "corporate_level",
            "department",
            "division",
            "group",
            "unit",
        )
        extra_kwargs = {
            "designation_id": {"read_only": True},
        }

    def validate_name(self, value: str):
        if self.Meta.model.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                {"name": "name is already taken"}
            )
        return value.lower()

    def create(self, validated_data):
        validated_data = self.process_designation(validated_data)
        return super(DesignationSerializer, self).create(
            validated_data=validated_data
        )

    def update(self, instance: Designation, validated_data):
        validated_data = self.process_designation(validated_data)

        # Levels cannot should not be changed if an employee is connected to designation
        if BasicInformation.objects.filter(designation=instance).exists():
            validated_data.update({"unit": instance.unit})
            validated_data.update({"department": instance.department})
            validated_data.update({"group": instance.group})
            validated_data.update(
                {"corporate_level": instance.corporate_level}
            )
            validated_data.update({"division": instance.division})
        return super().update(instance, validated_data)

    @staticmethod
    def process_designation(validated_data):
        (
            corporate_level_obj,
            department_obj,
            division_level_obj,
            group_level_obj,
            unit_level_obj,
            validated_data,
        ) = process_levels(validated_data)
        
        check_excess_data_count(
            [
                corporate_level_obj,
                division_level_obj,
                group_level_obj,
                department_obj,
                unit_level_obj,
            ],
            4,
            "level",
        )

        validated_data.update({"unit": unit_level_obj})
        validated_data.update({"department": department_obj})
        validated_data.update({"group": group_level_obj})
        validated_data.update({"corporate_level": corporate_level_obj})
        validated_data.update({"division": division_level_obj})

        return validated_data


class DesignationImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        # file_name = file_uploaded.name
        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))

        # designations = []
        error_arr = []
        fields = (
            "name",
            "corporate_level",
            "division",
            "group",
            "department",
            "unit",
        )

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                line_from_file[1:6] = process_level_by_name_to_dict(
                    *line_from_file[1:6]
                )
                data = dict(zip(fields, line_from_file))

                cleaned_data = {
                    field: value
                    for field, value in data.items()
                    if value != None
                }

                serializer = DesignationSerializer(
                    data=cleaned_data, many=False
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

            except CustomValidation as _:
                print(_)
                key, message = _.extract_key_message()
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
        return {"designation": "Designation has been created"}


class MultipleDesignationSerializer(serializers.Serializer):
    designation = serializers.SlugRelatedField(
        slug_field="designation_id",
        queryset=Designation.objects.all(),
        required=True,
        many=True,
    )
