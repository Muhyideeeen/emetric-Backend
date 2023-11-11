from itertools import zip_longest
from rest_framework import serializers
from pyexcel_xlsx import get_data
from typing import List, Dict
from core.utils.bulk_upload import extract_key_message
from core.utils.exception import CustomValidation

from core.utils.validators import validate_file_extension_for_xlsx
from organization.serializers import (
    CorporateLevelSerializer,
    DivisionLevelSerializer,
    GroupLevelSerializer,
    DepartmentLevelSerializer,
    UnitLevelSerializer,
)


class OrganisationImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)
    organisation_short_name = serializers.CharField(required=True)

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        org_short_name = attrs.get("organisation_short_name")
        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))

        error_arr = []
        fields = (
            "name",
            "current_level",
            "corporate_name",
            "division_name",
            "group_name",
            "department_name",
        )

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                data = dict(zip_longest(fields, line_from_file))
                serializer_class = self.__get_serializer_class(
                    data.pop("current_level")
                )
                cleaned_data = self.__clean_data(data, org_short_name)
                serializer = serializer_class(
                    data=cleaned_data, many=False, context=self.context
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
        return {"structure": "organisation structure has been created"}

    def __get_serializer_class(
        self, selected_level: str
    ) -> serializers.BaseSerializer:
        switcher = {
            "corporate": CorporateLevelSerializer,
            "division": DivisionLevelSerializer,
            "group": GroupLevelSerializer,
            "department": DepartmentLevelSerializer,
            "unit": UnitLevelSerializer,
        }
        serializer_class = switcher.get(selected_level)
        return (
            serializer_class if serializer_class else self.__invalid_option()
        )

    def __clean_data(self, data: dict, org_short_name: str) -> dict:
        """returns a clean data for the serializer"""
        data.update(
            {
                "organisation_short_name": org_short_name,
                "corporate_level": self.__extract_if_exist(
                    data.pop("corporate_name"), org_short_name
                ),
                "division": self.__extract_if_exist(
                    data.pop("division_name"), org_short_name
                ),
                "group": self.__extract_if_exist(
                    data.pop("group_name"), org_short_name
                ),
                "department": self.__extract_if_exist(
                    data.pop("department_name"), org_short_name
                ),
            }
        )
        return {field: value for field, value in data.items() if value != None}

    @staticmethod
    def __extract_if_exist(string: str, org_short_name: str):
        """Returns field if string is not empty"""
        return (
            {"name": string, "organisation_short_name": org_short_name}
            if string != "" and string != None
            else None
        )

    @staticmethod
    def __invalid_option():
        """Raises error for invalid option"""
        raise CustomValidation(
            detail="current level is not a valid option",
            field="current_level",
            status_code=400,
        )
