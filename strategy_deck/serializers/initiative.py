from typing import Dict, List
from django.contrib.auth import get_user_model
from pyexcel_xlsx import get_data
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from core.serializers.nested import OwnerOrAssignorSerializer
from core.utils.bulk_upload import extract_key_message
from core.utils.eager_loading import EagerLoadingMixin
from core.utils.exception import CustomValidation
from core.utils.process_durations import (
    process_end_date,
    process_start_date_list,
    try_parsing_date,
)
from core.utils.custom_data_validation import check_excess_data_count
from core.utils.validators import validate_file_extension_for_xlsx
from core.serializers.nested import NestedTaskSerializer
from employee.models import Employee
from organization.models import CorporateLevel

from strategy_deck.models import Objective, Initiative
from tasks.models.detail import Task

User = get_user_model()


class NestedObjectiveSerializer(serializers.ModelSerializer):
    objective_id = serializers.UUIDField(required=True)
    owner = OwnerOrAssignorSerializer(many=False, read_only=True)

    class Meta:
        model = Objective
        fields = (
            "name",
            "owner",
            "routine_option",
            "start_date",
            "end_date",
            "objective_id",
            "target_point",
        )
        extra_kwargs = {
            "name": {"read_only": True},
            "owner": {"read_only": True},
            "routine_option": {"read_only": True},
            "start_date": {"read_only": True},
            "end_date": {"read_only": True},
            "target_point": {"read_only": True},
        }

    def validate_objective_id(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(objective_id=value).exists():
                raise serializers.ValidationError(
                    {
                        "objective.objective_id": "Objective id is not a valid id"
                    }
                )
        return value


class NestedInitiativeSerializer(serializers.ModelSerializer):
    initiative_id = serializers.UUIDField(required=True)
    owner = OwnerOrAssignorSerializer(many=False, read_only=True)
    assignor = OwnerOrAssignorSerializer(many=False, read_only=True)

    class Meta:
        model = Initiative
        fields = (
            "name",
            "owner",
            "assignor",
            "routine_option",
            "start_date",
            "end_date",
            "initiative_id",
            "target_point",
        )
        extra_kwargs = {
            "name": {"read_only": True},
            "routine_option": {"read_only": True},
            "start_date": {"read_only": True},
            "end_date": {"read_only": True},
            "target_point": {"read_only": True},
        }

    def validate_initiative_id(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(
                initiative_id=value
            ).exists():
                raise serializers.ValidationError(
                    {
                        "initiative.initiative_id": "Initiative id is not a valid id"
                    }
                )
        return value


class InitiativeSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    upline_objective = NestedObjectiveSerializer(many=False, required=False)
    upline_initiative = NestedInitiativeSerializer(many=False, required=False)
    assignor = OwnerOrAssignorSerializer(many=False, required=False)
    owner = OwnerOrAssignorSerializer(many=False)
    routine_option = serializers.ChoiceField(
        required=True, choices=Initiative.ROUTINE_TYPE_CHOICES
    )
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False)
    after_occurrence = serializers.IntegerField(
        min_value=1, max_value=20, required=False
    )

    initiative_brief = serializers.FileField(required=False)

    tasks = serializers.SerializerMethodField(read_only=True)
    select_related_fields = (
        "upline_objective",
        "upline_initiative",
        "corporate_level",
        "corporate_level__team_lead",
        "division",
        "group",
        "department",
        "unit",
        "assignor",
        "owner",
    )
    prefetch_related_fields = ("initiative_task",)

    def get_tasks(self, obj):
        """Returns all pending and active tasks connected to initiative"""
        return NestedTaskSerializer(
            obj.initiative_task.filter(
                task_status__in=[Task.PENDING, Task.ACTIVE]
            ),
            many=True,
        ).data

    class Meta:
        model = Initiative
        fields = [
            "name",
            "upline_objective",
            "upline_initiative",
            "assignor",
            "owner",
            "routine_option",
            "routine_round",
            "initiative_status",
            "start_date",
            "end_date",
            "after_occurrence",
            "initiative_brief",
            "target_point",
            "tasks",
            "initiative_id",
        ]
        extra_kwargs = {
            "initiative_id": {"read_only": True},
            "initiative_status": {"read_only": True},
            "routine_round": {"read_only": True},
            "target_point": {"read_only": True},
        }

    def validate(self, attrs):
        attrs = super(InitiativeSerializer, self).validate(attrs=attrs)

        routine_option = attrs.get("routine_option")
        end_date = attrs.get("end_date", None)
        after_occurrence = attrs.get("after_occurrence", None)

        self._validate_routine_details(
            routine_option, end_date, after_occurrence
        )

        return attrs

    @staticmethod
    def _validate_routine_details(
        routine_option, end_date, after_occurrence
    ) -> None:
        """Checks that end date and after occurrence match routine option"""
        if routine_option != Objective.ONCE:
            if end_date == None and after_occurrence == None:
                raise serializers.ValidationError(
                    {
                        "end_date": "This field is required.",
                        "after_occurrence": "This field is required.",
                    }
                )
            if end_date != None and after_occurrence != None:
                raise serializers.ValidationError(
                    {
                        "end_date": "Both fields can not be provided.",
                        "after_occurrence": "Both fields can not be provided.",
                    }
                )
        else:
            if end_date == None:
                raise serializers.ValidationError(
                    {
                        "end_date": "This field is required.",
                    }
                )
            elif after_occurrence != None:
                raise serializers.ValidationError(
                    {
                        "after_occurrence": "This field is not required.",
                    }
                )

    def create(self, validated_data: Dict):
        validated_data = self._process_serialized_input(validated_data)

        start_date_list = validated_data.pop("start_date_list", None)

        end_date = validated_data.get("end_date", None)
        routine_option = validated_data.get("routine_option")
        initiatives_array = []

        for routine_round, start_date in enumerate(start_date_list):
            end_date = process_end_date(start_date, routine_option, end_date)
            validated_data.update(
                {
                    "start_date": start_date,
                    "routine_round": routine_round + 1,
                    "end_date": end_date,
                }
            )
            initiatives_array.append(Initiative(**validated_data))
        initiatives = Initiative.objects.bulk_create(initiatives_array)

        return initiatives[0]

    def update(self, instance: Initiative, validated_data):
        if instance.initiative_status != Initiative.PENDING:
            raise PermissionDenied(
                {"status": "Permission denied to edit this initiative"}
            )

        routine_option = validated_data.get("routine_option")
        if routine_option != Initiative.ONCE:
            raise serializers.ValidationError(
                {
                    "routine_option": "Routine option for initiative update must be once"
                }
            )

        validated_data = self._process_serialized_input(validated_data, instance)
        start_date_list = validated_data.pop("start_date_list")
        # prevent name update.
        validated_data.update(
            {
                "start_date": start_date_list[0],
                "name": instance.name,
                "initiative_brief": validated_data.get(
                    "initiative_brief", instance.initiative_brief
                ),
            }
        )

        instance = super(InitiativeSerializer, self).update(
            validated_data=validated_data, instance=instance
        )

        instance.modify_change_to_active_task()
        instance.modify_change_to_closed_task()

        return instance

    def _process_serialized_input(self, validated_data, instance=None):
        assignor_email = (
            validated_data.pop("assignor").get("email", None)
            if validated_data.get("assignor", None)
            else None
        )

        owner_email = validated_data.pop("owner").get("email")
        name = validated_data.get("name")
        initiative_name = f"{name} - {owner_email}".lower()
        
        if not instance:
            if self.Meta.model.objects.filter(name=initiative_name).exists():
                raise serializers.ValidationError(
                    {"name": "name is already taken"}
                )

        upline_objective_id = (
            validated_data.pop("upline_objective").get("objective_id", None)
            if validated_data.get("upline_objective", None)
            else None
        )

        upline_initiative_id = (
            validated_data.pop("upline_initiative").get("initiative_id", None)
            if validated_data.get("upline_initiative", None)
            else None
        )

        start_date = validated_data.get("start_date")
        routine_option = validated_data.get("routine_option")
        after_occurrence = validated_data.get("after_occurrence", None)
        end_date = validated_data.get("end_date", None)

        owner = User.objects.get(email=owner_email)
        assignor = (
            User.objects.get(email=assignor_email) if assignor_email else None
        )
        employee = Employee.objects.get(user=owner)

        # confirms that the assignor is owner's upline
        if (
            assignor
            and employee.employee_employmentinformation.upline != assignor
        ):
            raise serializers.ValidationError(
                {"assignor": "Invalid assignor for owner"}
            )

        elif (
            not assignor
            and not CorporateLevel.objects.filter(team_lead=owner).exists()
        ):
            raise serializers.ValidationError(
                {"assignor": "Invalid assignor for owner"}
            )

        upline_objective = (
            Objective.objects.get(objective_id=upline_objective_id)
            if upline_objective_id
            else None
        )

        upline_initiative = (
            Initiative.objects.get(initiative_id=upline_initiative_id)
            if upline_initiative_id
            else None
        )

        check_excess_data_count(
            inputs=[upline_objective, upline_initiative], expected_none_count=1
        )

        # process schedule
        start_date_list = []  # list of start dates
        try:
            start_date_list.extend(
                process_start_date_list(
                    routine_option,
                    start_date,
                    end_date,
                    after_occurrence,
                    upline_objective or upline_initiative,
                )
            )
        except CustomValidation as _:
            key, message = _.extract_key_message()
            raise serializers.ValidationError({key: message})

        validated_data.update(
            {
                "name": initiative_name,
                "owner": owner,
                "assignor": assignor,
                "upline_objective": upline_objective,
                "upline_initiative": upline_initiative,
                "corporate_level": employee.corporate_level,
                "division": employee.division,
                "group": employee.group,
                "department": employee.department,
                "unit": employee.unit,
                "start_date_list": start_date_list,
            }
        )
        return validated_data


class InitiativeImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))

        error_arr = []
        fields = (
            "name",
            "upline_objective_name",
            "upline_initiative_name",
            "assignor_email",
            "owner_email",
            "routine_option",
            "start_date",
            "end_date",
            "after_occurrence",
        )

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                data = dict(zip(fields, line_from_file))
                cleaned_data = self.__clean_data(data)
                serializer = InitiativeSerializer(
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
        return {"Initiative": "Initiative(s) has been created"}

    def __clean_data(self, data: dict) -> dict:
        """returns a clean data for the serializer"""
        data.update(
            {
                "upline_objective": self.__extract_objective(
                    data.pop("upline_objective_name")
                ),
                "upline_initiative": self.__extract_initiative(
                    data.pop("upline_initiative_name")
                ),
                "assignor": self.__extract_assignor(
                    data.pop("assignor_email")
                ),
                "owner": {"email": data.pop("owner_email")},
                "start_date": try_parsing_date(data.pop("start_date")),
                "end_date": self.__extract_end_date(data.pop("end_date")),
                "after_occurrence": self.__extract_if_exist(
                    data.pop("after_occurrence")
                ),
            }
        )
        return {field: value for field, value in data.items() if value != None}

    @staticmethod
    def __extract_if_exist(string: str):
        """Returns field if string is not empty"""
        return string if string != "" else None

    def __extract_objective(self, name: str):
        """Returns objective if name is not empty"""
        return (
            {"objective_id": self.__get_objective(name).objective_id}
            if name != ""
            else None
        )

    def __extract_initiative(self, name: str):
        """Returns initiative if name is not empty"""
        return (
            {"initiative_id": self.__get_initiative(name).initiative_id}
            if name != ""
            else None
        )

    def __extract_assignor(self, email: str):
        """Returns assignor email if email is not empty"""
        return {"email": email} if email != "" else None

    @staticmethod
    def __extract_end_date(date: str):
        """Returns end date if end date is not empty"""
        return try_parsing_date(date) if date != "" else None

    @staticmethod
    def __get_objective(name: str) -> Objective:
        """Returns objective by name if it exists"""
        objectives = Objective.objects.filter(name=str(name).lower().strip())
        if not objectives.exists():
            raise CustomValidation(
                detail="objective does not exist.",
                field="objective",
                status_code=400,
            )
        return objectives.first()

    @staticmethod
    def __get_initiative(name: str) -> Initiative:
        """Returns initiative by name if it exists"""
        initiatives = Initiative.objects.filter(name=str(name).lower().strip())
        if not initiatives.exists():
            raise CustomValidation(
                detail="initiative does not exist.",
                field="initiative",
                status_code=400,
            )
        return initiatives.first()


class MultipleInitiativeSerializer(serializers.Serializer):
    initiative = serializers.SlugRelatedField(
        slug_field="initiative_id",
        queryset=Initiative.objects.all(),
        required=True,
        many=True,
    )
