from typing import List, Dict

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction, connection
from rest_framework import serializers
from pyexcel_xlsx import get_data

from account.models import Role
from career_path.models import CareerPath
from core.serializers.nested import (
    NestedDesignationSerializer,
    NestedCorporateLevelSerializer,
    NestedDepartmentLevelSerializer,
    NestedDivisionLevelSerializer,
    NestedGroupLevelSerializer,
    NestedUnitLevelSerializer,
    NestedCareerPathSerializer,
)
from core.utils.bulk_upload import extract_key_message
from core.utils.eager_loading import EagerLoadingMixin
from core.utils.employee_data import employee_data_validation, get_upline_user
from core.utils.custom_data_validation import check_excess_data_count
from core.utils.exception import CustomValidation
from core.utils.process_durations import try_parsing_date
from core.utils.process_levels import (
    process_level_by_name_to_dict,
    process_levels,
)
from core.utils.validators import validate_file_extension_for_xlsx
from designation.models import Designation
from employee.models import Employee
from employee_profile.models import (
    EmploymentInformation,
    BasicInformation,
    ContactInformation,
)
from employee_profile.models.basic_information import EducationDetail

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    user_role = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            "user_id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "user_role",
        )
        extra_kwargs = {
            "user_id": {"read_only": True},
            "password": {"write_only": True},
        }

    def validate_email(self, value: str):
        return value.lower()


class UserEmploymentInformationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ("user_id", "email", "first_name", "last_name")
        extra_kwargs = {
            "user_id": {"read_only": True},
            "first_name": {"read_only": True},
            "last_name": {"read_only": True},
        }

    def validate_email(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(email=value).exists():
                raise serializers.ValidationError(
                    {"email": "invalid email, account cannot be found"}
                )
        return value


class UserRoles(serializers.ModelSerializer):
    role = serializers.CharField(required=True)

    class Meta:
        model = Role
        fields = ("role",)

    def validate_role(self, value):
        if self.context["request"]._request.method == "POST":
            if not self.Meta.model.objects.filter(role=value).exists():
                raise serializers.ValidationError(
                    {"role": "Role specified does not exist"}
                )
        return value


class EducationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationDetail
        fields = ("institution", "year", "qualification")


class NestedBasicInformationSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(
        format="%d-%m-%Y",
        input_formats=["%d-%m-%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    designation = NestedDesignationSerializer(required=False, read_only=True)
    education_details = EducationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = BasicInformation
        fields = (
            "designation",
            "basic_information_id",
            "date_of_birth",
            "brief_description",
            "education_details",
            "profile_picture",
        )
        extra_kwargs = {
            "designation": {"read_only": True},
            "basic_information_id": {"read_only": True},
            "brief_description": {"required": False},
            # "date_of_birth": {"required": False},
            "profile_picture": {"required": False},
        }


class NestedContactInformationSerializer(serializers.ModelSerializer):
    personal_email = serializers.EmailField(required=True)

    class Meta:
        model = ContactInformation
        fields = (
            "contact_information_id",
            "personal_email",
            "official_email",
            "phone_number",
            "address",
            "guarantor_one_first_name",
            "guarantor_one_last_name",
            "guarantor_one_address",
            "guarantor_one_occupation",
            "guarantor_one_age",
            "guarantor_one_id_card",
            "guarantor_one_passport",
            "guarantor_two_first_name",
            "guarantor_two_last_name",
            "guarantor_two_address",
            "guarantor_two_occupation",
            "guarantor_two_age",
            "guarantor_two_id_card",
            "guarantor_two_passport",
        )
        extra_kwargs = {
            "contact_information_id": {"read_only": True},
            "official_email": {"read_only": True},
            # 'personal_email': {'required': True},
            "phone_number": {"required": True},
            "address": {"required": True},
            "guarantor_one_first_name": {"required": False},
            "guarantor_one_last_name": {"required": False},
            "guarantor_one_address": {"required": False},
            "guarantor_one_occupation": {"required": False},
            "guarantor_one_age": {"required": False},
            "guarantor_one_id_card": {"required": False},
            "guarantor_one_passport": {"required": False},
            "guarantor_two_first_name": {"required": False},
            "guarantor_two_last_name": {"required": False},
            "guarantor_two_address": {"required": False},
            "guarantor_two_occupation": {"required": False},
            "guarantor_two_age": {"required": False},
            "guarantor_two_id_card": {"required": False},
            "guarantor_two_passport": {"required": False},
        }

    def validate_personal_email(self, value: str):
        return value.lower()

    def validate_official_email(self, value: str):
        return value.lower()


class NestedEmploymentInformationSerializer(serializers.ModelSerializer):
    date_employed = serializers.DateField(
        write_only=False,
        format="%d-%m-%Y",
        input_formats=["%d-%m-%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    upline = UserEmploymentInformationSerializer(required=False, many=False)

    class Meta:
        model = EmploymentInformation
        fields = (
            "employment_information_id",
            "date_employed",
            "upline",
            "date_of_last_promotion",
            "status",
        )
        extra_kwargs = {
            "employment_information_id": {"read_only": True},
            "date_of_last_promotion": {"read_only": True},
            # "date_employed": {"required": False},
        }


class EmployeeSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    user = UserSerializer(many=False)
    user_role = UserRoles(many=False, write_only=True)

    basic_information = NestedBasicInformationSerializer(
        many=False, required=True, write_only=True
    )
    contact_information = NestedContactInformationSerializer(
        many=False, required=True, write_only=True
    )
    employment_information = NestedEmploymentInformationSerializer(
        many=False, required=True, write_only=True
    )

    corporate_level = NestedCorporateLevelSerializer(
        many=False, required=False
    )
    department = NestedDepartmentLevelSerializer(many=False, required=False)
    division = NestedDivisionLevelSerializer(many=False, required=False)
    group = NestedGroupLevelSerializer(many=False, required=False)
    unit = NestedUnitLevelSerializer(many=False, required=False)

    employee_basic_information = serializers.SerializerMethodField()
    employee_contact_information = serializers.SerializerMethodField()
    employee_employment_information = serializers.SerializerMethodField()

    designation = NestedDesignationSerializer(many=False, write_only=True)

    education_details = EducationDetailSerializer(
        many=True, write_only=True, required=False
    )

    career_path = NestedCareerPathSerializer(many=False, required=False)

    select_related_fields = (
        "user",
        "organisation_short_name",
        "corporate_level",
        "department",
        "division",
        "group",
        "unit",
        "career_path",
        "employee_basic_infomation",
        "employee_contact_infomation",
        "employee_employmentinformation",
    )
    prefetch_related_fields = (
        "employee_basic_infomation",
        "employee_contact_infomation",
        "employee_employmentinformation",
        "employee_basic_infomation__designation",
        "employee_basic_infomation__education_details",
    )

    class Meta:
        model = Employee
        fields = [
            "user",
            "user_role",
            "designation",
            "basic_information",
            "contact_information",
            "employment_information",
            "corporate_level",
            "department",
            "division",
            "group",
            "unit",
            "employee_basic_information",
            "employee_contact_information",
            "employee_employment_information",
            "career_path",
            "education_details",
            "uuid",
            "slug",
        ]
        extra_kwargs = {
            "uuid": {"read_only": True},
            "slug": {"read_only": True},
        }

    def get_employee_designation(self, obj):
        return obj.employee_basic_infomation.designation.name

    def get_employee_basic_information(self, obj):
        return NestedBasicInformationSerializer(
            obj.employee_basic_infomation, many=False
        ).data

    def get_employee_contact_information(self, obj):
        return NestedContactInformationSerializer(
            obj.employee_contact_infomation, many=False
        ).data

    def get_employee_employment_information(self, obj):
        return NestedEmploymentInformationSerializer(
            obj.employee_employmentinformation, many=False
        ).data

    def create(self, validated_data):
        validated_data = self._process_serialized_input(validated_data)
        
        if Employee.objects.count() >= connection.tenant.employee_limit:
            raise serializers.ValidationError(
                {"detail": "Employee limit exceeded"}
            )

        user = validated_data.get("user")
        user_role = validated_data.get("user_role")

        corporate_level = validated_data.get("corporate_level")
        division = validated_data.get("division")
        group = validated_data.get("group")
        department = validated_data.get("department")
        unit = validated_data.get("unit")
        current_level = validated_data.get("current_level")

        upline_user = validated_data.get("upline_user")
        career_path = validated_data.get("career_path")
        designation = validated_data.get("designation")

        contact_information = validated_data.pop("contact_information")
        basic_information = validated_data.pop("basic_information")
        employment_information = validated_data.pop("employment_information")
        education_details = validated_data.pop("education_details")

        tenant_object = self.context.get("request").tenant
        user_extra_details = {"is_invited": True, "user_role": user_role}

        # return None

        try:
            with transaction.atomic():
                created_user = User.objects.create_user(
                    **user, **user_extra_details
                )

                # sets user to team lead for level if selected
                if user_role == Role.TEAM_LEAD:
                    current_level.team_lead = created_user
                    current_level.save()

                    # set team lead as upline for other employees in level
                    level_employees = Employee.objects.filter(
                        corporate_level=corporate_level,
                        department=department,
                        division=division,
                        group=group,
                        unit=unit,
                    )
                    role = Role.objects.get(role=Role.EMPLOYEE)
                    for level_employee in level_employees:
                        level_employee.employee_employmentinformation.upline = (
                            created_user
                        )
                        level_employee.employee_employmentinformation.save()

                        level_employee.user.user_role = role
                        level_employee.user.save()

                employee = Employee.objects.create(
                    user=created_user,
                    organisation_short_name=tenant_object,
                    unit=unit,
                    department=department,
                    group=group,
                    division=division,
                    corporate_level=corporate_level,
                    career_path=career_path,
                )

                employee_basic_information = BasicInformation.objects.create(
                    employee=employee,
                    designation=designation,
                    **basic_information,
                )

                # add create and add education details
                for education_detail in education_details:
                    education_detail_obj = EducationDetail.objects.create(
                        **education_detail
                    )
                    employee_basic_information.education_details.add(
                        education_detail_obj
                    )
                employee_basic_information.save()

                ContactInformation.objects.create(
                    employee=employee, **contact_information
                )

                EmploymentInformation.objects.create(
                    employee=employee,
                    upline=upline_user,
                    **employment_information,
                )

        except IntegrityError as _:
            if "email" in _.__str__():
                message = "email already exists"
                key = "email"
            elif "phone_number" in _.__str__():
                message = "phone_number already exists"
                key = "phone_number"
            elif "personal_email" in _.__str__():
                message = "personal email already exists"
                key = "contact_information.personal_email"
            elif "official_email" in _.__str__():
                message = "official email already exists"
                key = "contact_information.official_email"
            else:
                message = _
                key = "db_error"
            raise serializers.ValidationError({key: message})

        return employee

    def update(self, instance: Employee, validated_data):
        validated_data = self._process_serialized_input(
            validated_data, instance
        )

        user = validated_data.get("user")
        user_role = validated_data.get("user_role")

        corporate_level = validated_data.get("corporate_level")
        division = validated_data.get("division")
        group = validated_data.get("group")
        department = validated_data.get("department")
        unit = validated_data.get("unit")
        current_level = validated_data.get("current_level")

        career_path = validated_data.get("career_path")
        designation = validated_data.get("designation")

        contact_information = validated_data.pop("contact_information")
        contact_information.update(
            {
                "guarantor_one_id_card": contact_information.get(
                    "guarantor_one_id_card",
                    instance.employee_contact_infomation.guarantor_one_id_card,
                ),
                "guarantor_one_passport": contact_information.get(
                    "guarantor_one_passport",
                    instance.employee_contact_infomation.guarantor_one_passport,
                ),
                "guarantor_two_id_card": contact_information.get(
                    "guarantor_two_id_card",
                    instance.employee_contact_infomation.guarantor_two_id_card,
                ),
                "guarantor_two_passport": contact_information.get(
                    "guarantor_two_passport",
                    instance.employee_contact_infomation.guarantor_two_passport,
                ),
            }
        )
        basic_information = validated_data.pop("basic_information")
        basic_information.update(
            {
                "profile_picture": basic_information.get(
                    "profile_picture",
                    instance.employee_basic_infomation.profile_picture,
                ),
            }
        )
        employment_information = validated_data.pop("employment_information")
        education_details = validated_data.pop("education_details")
        upline_user = validated_data.pop("upline_user")
        # return instance

        try:
            with transaction.atomic():
                instance.user.__dict__.update(**user)
                role = Role.objects.get(role=user_role)
                instance.user.user_role = role
                instance.user.save()

                # sets user to team lead for level if selected
                if user_role == Role.TEAM_LEAD:
                    current_level.team_lead = instance.user
                    current_level.save()

                    # set team lead as upline for other employees
                    level_employees = Employee.objects.filter(
                        corporate_level=corporate_level,
                        department=department,
                        division=division,
                        group=group,
                        unit=unit,
                    ).exclude(user=instance.user)
                    role = Role.objects.get(role=Role.EMPLOYEE)
                    for level_employee in level_employees:
                        level_employee.employee_employmentinformation.upline = (
                            instance.user
                        )
                        level_employee.employee_employmentinformation.save()

                        level_employee.user.user_role = role
                        level_employee.user.save()

                instance.corporate_level = corporate_level
                instance.department = department
                instance.division = division
                instance.group = group
                instance.unit = unit
                instance.career_path = career_path
                instance.save()

                employee_basic_information = BasicInformation.objects.get(
                    employee=instance
                )
                employee_basic_information.__dict__.update(**basic_information)
                employee_basic_information.designation = designation
                employee_basic_information.education_details.all().delete()
                for education_detail in education_details:
                    education_detail_obj = EducationDetail.objects.create(
                        **education_detail
                    )
                    employee_basic_information.education_details.add(
                        education_detail_obj
                    )

                employee_basic_information.save()

                employee_contact_information = ContactInformation.objects.get(
                    employee=instance
                )
                employee_contact_information.__dict__.update(
                    **contact_information
                )
                employee_contact_information.save()

                employee_employment_information = (
                    EmploymentInformation.objects.get(employee=instance)
                )
                employee_employment_information.__dict__.update(
                    **employment_information
                )
                employee_employment_information.upline = upline_user
                employee_employment_information.save()

        except IntegrityError as _:
            if "email" in _.__str__():
                message = "email already exists"
                key = "email"
            elif "phone_number" in _.__str__():
                message = "phone_number already exists"
                key = "phone_number"
            elif "personal_email" in _.__str__():
                message = "personal email already exists"
                key = "contact_information.personal_email"
            elif "official_email" in _.__str__():
                message = "official email already exists"
                key = "contact_information.official_email"
            else:
                message = _
                key = "db_error"
            raise serializers.ValidationError({key: message})
        instance.refresh_from_db()
        return instance

    def _process_serialized_input(self, validated_data, instance=None):
        """custom data validation"""
        user_role = validated_data.pop("user_role").get("role")

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

        current_level = (
            corporate_level_obj
            or department_obj
            or division_level_obj
            or group_level_obj
            or unit_level_obj
        )

        designation = validated_data.pop("designation").get("name")
        designation_obj = Designation.objects.get(name=designation.lower())

        career_path = validated_data.pop("career_path", None)
        career_path_level = (
            career_path.get("level", None) if career_path else None
        )
        career_path_obj = (
            CareerPath.objects.get(level=career_path_level)
            if career_path_level
            else None
        )

        try:
            employee_data_validation(
                current_level, user_role, designation, instance
            )
        except CustomValidation as _:
            key, message = _.extract_key_message()
            raise serializers.ValidationError({key: message})

        # assign team lead as upline user except for corporate level
        upline_user = get_upline_user(
            user_role, current_level, corporate_level_obj
        )

        validated_data.update(
            {
                "user_role": user_role,
                "corporate_level": corporate_level_obj,
                "division": division_level_obj,
                "group": group_level_obj,
                "department": department_obj,
                "unit": unit_level_obj,
                "designation": designation_obj,
                "career_path": career_path_obj,
                "upline_user": upline_user,
                "current_level": current_level,
            }
        )
        return validated_data


class EmployeeImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))

        error_arr = []
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "personal_phone_number",
            "personal_email",
            "address",
            "date_of_birth",
            "institutions",
            "years",
            "qualifications",
            "guarantor_1_first_name",
            "guarantor_1_last_name",
            "guarantor_1_address",
            "guarantor_1_occupation",
            "guarantor_1_age",
            "guarantor_2_first_name",
            "guarantor_2_last_name",
            "guarantor_2_address",
            "guarantor_2_occupation",
            "guarantor_2_age",
            "brief_description",
            "user_role",
            "date_employed",
            "corporate_level",
            "division",
            "group",
            "department",
            "unit",
            "career_path_level",
            "designation",
        )

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                line_from_file[24:29] = process_level_by_name_to_dict(
                    *line_from_file[24:29]
                )
                data = dict(zip(fields, line_from_file))

                cleaned_data = self.__clean_data(data)
                serializer = EmployeeSerializer(
                    data=cleaned_data, many=False, context=self.context
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            except serializers.ValidationError as _:
                print(_)
                errors = _.detail
                key, message = extract_key_message(errors)
                error_arr.append(
                    {"key": key, "message": str(message), "line": index + 2}
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
        return {"employee": "employees invited"}

    def __clean_data(self, data: dict) -> dict:
        """returns a clean data for the serializer"""
        data.update(
            {
                "user": {
                    "first_name": data.pop("first_name"),
                    "last_name": data.pop("last_name"),
                    "phone_number": data.pop("phone_number"),
                    "email": data.pop("email"),
                },
                "user_role": {"role": data.pop("user_role")},
                "basic_information": {
                    "date_of_birth": self.__extract_date(
                        data.pop("date_of_birth")
                    ),
                    "brief_description": data.pop("brief_description"),
                },
                "education_details": self.__extract_education_details(
                    data.pop("institutions"),
                    data.pop("years"),
                    data.pop("qualifications"),
                ),
                "contact_information": {
                    "personal_email": data.pop("personal_email"),
                    "phone_number": data.pop("personal_phone_number"),
                    "address": data.pop("address"),
                    "guarantor_one_first_name": data.pop(
                        "guarantor_1_first_name"
                    ),
                    "guarantor_one_last_name": data.pop(
                        "guarantor_1_last_name"
                    ),
                    "guarantor_one_address": data.pop("guarantor_1_address"),
                    "guarantor_one_occupation": data.pop(
                        "guarantor_1_occupation"
                    ),
                    "guarantor_one_age": data.pop("guarantor_1_age"),
                    "guarantor_two_first_name": data.pop(
                        "guarantor_2_first_name"
                    ),
                    "guarantor_two_last_name": data.pop(
                        "guarantor_2_last_name"
                    ),
                    "guarantor_two_address": data.pop("guarantor_2_address"),
                    "guarantor_two_occupation": data.pop(
                        "guarantor_2_occupation"
                    ),
                    "guarantor_two_age": data.pop("guarantor_2_age"),
                },
                "employment_information": {
                    "date_employed": self.__extract_date(
                        data.pop("date_employed")
                    ),
                },
                "designation": {"name": data.pop("designation")},
                "career_path": self.__extract_career_path(
                    data.pop("career_path_level")
                ),
            }
        )
        return {field: value for field, value in data.items() if value != None}

    @staticmethod
    def __extract_date(date: str):
        """Returns date if end date is not empty"""
        return try_parsing_date(date) if date != "" else None

    @staticmethod
    def __extract_career_path(level: str):
        """Returns career path level dict if level is not empty"""
        return {"level": level} if level != "" else None

    @staticmethod
    def __extract_education_details(
        institutions: str, years: str, qualifications: str
    ) -> list:
        """Return a dict of education details"""
        institutions_list = str(institutions).strip().split(",")
        years_list = str(years).strip().split(",")
        qualifications_list = str(qualifications).strip().split(",")

        if (
            not len(institutions_list)
            == len(years_list)
            == len(qualifications_list)
        ):
            raise CustomValidation(
                detail="education details do not match",
                field="education_details",
                status_code=400,
            )

        education_details = []
        for institution, year, qualification in zip(
            institutions_list,
            years_list,
            qualifications_list,
        ):
            education_details.append(
                {
                    "institution": institution,
                    "year": year,
                    "qualification": qualification,
                }
            )
        return education_details


class MultipleEmployeeSerializer(serializers.Serializer):
    employee = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Employee.objects.all(),
        required=True,
        many=True,
    )
