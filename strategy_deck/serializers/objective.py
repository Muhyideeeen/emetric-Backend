from typing import Dict, List
from django.contrib.auth import get_user_model
from pyexcel_xlsx import get_data
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from core.serializers.nested import (
    NestedCorporateLevelSerializer,
    OwnerOrAssignorSerializer,
)
from core.utils.bulk_upload import extract_key_message
from core.utils.eager_loading import EagerLoadingMixin
from core.utils.exception import CustomValidation
from core.utils.process_durations import (
    process_end_date,
    process_start_date_list,
    try_parsing_date,
)
from core.utils.process_levels import process_structure
from core.utils.validators import validate_file_extension_for_xlsx
from organization.models import CorporateLevel
from strategy_deck.models import (
    Objective,
    Perspective,
    ObjectivePerspectiveSpread,
)
from strategy_deck.models.initiative import Initiative
from strategy_deck.serializers.objective_perspective_spread import (
    ObjectivePerspectiveSpreadSerializer,
)

User = get_user_model()


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
            if not self.Meta.model.objects.filter(
                perspective_id=value
            ).exists():
                raise serializers.ValidationError(
                    {
                        "Perspective.perspective_id": "Perspective id is not a valid id"
                    }
                )
        return value


class NestedInitiativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Initiative
        fields = ["initiative_id", "name", "routine_round", "target_point"]


class ObjectiveSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    owner = serializers.SerializerMethodField()
    perspective = NestedPerspectiveSerializer(
        many=True, required=True, write_only=True
    )
    routine_option = serializers.ChoiceField(
        required=True, choices=Objective.ROUTINE_TYPE_CHOICES
    )
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False)
    after_occurrence = serializers.IntegerField(
        min_value=1, max_value=20, required=False
    )
    perspectives = serializers.SerializerMethodField()
    corporate_level = NestedCorporateLevelSerializer(many=False, required=True)
    active_initiative = serializers.SerializerMethodField(read_only=True)

    select_related_fields = (
        "corporate_level",
        "corporate_level__team_lead",
    )
    prefetch_related_fields = (
        "objective_initiative",
        "objective_objective_perspective_spread",
    )

    @staticmethod
    def get_owner(obj):
        """Returns team lead of attached corporate level"""
        return OwnerOrAssignorSerializer(obj.corporate_level.team_lead).data

    @staticmethod
    def get_active_initiative(obj):
        """Returns all active initiative connected to objective"""
        return NestedInitiativeSerializer(
            obj.objective_initiative.filter(
                initiative_status=Initiative.ACTIVE
            ),
            many=True,
        ).data

    @staticmethod
    def get_perspectives(obj):
        return ObjectivePerspectiveSpreadSerializer(
            obj.objective_objective_perspective_spread.all(), many=True
        ).data

    class Meta:
        model = Objective
        fields = [
            "name",
            "owner",
            "objective_status",
            "routine_option",
            "routine_round",
            "start_date",
            "end_date",
            "after_occurrence",
            "perspective",
            "perspectives",
            "objective_id",
            "target_point",
            "corporate_level",
            "active_initiative",
        ]
        extra_kwargs = {
            "objective_id": {"read_only": True},
            "target_point": {"read_only": True},
            "objective_status": {"read_only": True},
            "routine_round": {"read_only": True},
        }

    def validate_name(self, value: str):
        if self.Meta.model.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                {"name": "name is already taken"}
            )
        return value.lower()

    def validate(self, attrs):
        attrs = super(ObjectiveSerializer, self).validate(attrs=attrs)

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
        perspective_list = validated_data.pop("perspective")
        validated_data = self._process_serialized_input(validated_data)

        start_date_list = validated_data.pop("start_date_list", None)
        end_date = validated_data.get("end_date", None)
        routine_option = validated_data.get("routine_option")

        objectives_array = []

        for routine_round, start_date in enumerate(start_date_list):
            end_date = process_end_date(start_date, routine_option, end_date)
            validated_data.update(
                {
                    "start_date": start_date,
                    "routine_round": routine_round + 1,
                    "end_date": end_date,
                }
            )
            objectives_array.append(Objective(**validated_data))
        objectives = Objective.objects.bulk_create(objectives_array)

        for objective in objectives:
            for perspective_data in perspective_list:
                relative_point = perspective_data.get("relative_point")
                perspective_id = perspective_data.get("perspective_id")
                perspective = Perspective.objects.get(
                    perspective_id=perspective_id
                )
                ObjectivePerspectiveSpread.objects.create(
                    perspective=perspective,
                    objective=objective,
                    relative_point=relative_point,
                )
        return objectives[0]

    def update(self, instance: Objective, validated_data):
        if instance.objective_status != Objective.PENDING:
            raise PermissionDenied(
                {"status": "Permission denied to edit this objective"}
            )

        routine_option = validated_data.get("routine_option")
        if routine_option != Initiative.ONCE:
            raise serializers.ValidationError(
                {
                    "routine_option": "Routine option for objective update must be once"
                }
            )

        perspective_list = validated_data.pop("perspective")
        validated_data = self._process_serialized_input(
            validated_data, instance
        )
        start_date_list = validated_data.pop("start_date_list")

        validated_data.update({"start_date": start_date_list[0]})

        # Deactivate objective's perspective updates
        # objective_total_score = 0
        # for perspective_data in perspective_list:
        #     print(perspective_data)
        #     relative_point = perspective_data.get(
        #         "relative_point"
        #     )
        #     perspective_id = perspective_data.get("perspective_id")
        #     perspective = Perspective.objects.get(
        #         perspective_id=perspective_id
        #     )
        #     objective_perspective_spread = (
        #         ObjectivePerspectiveSpread.objects.get(
        #             perspective=perspective, objective=instance
        #         )
        #     )
        #     perspective.target_point -= (
        #         objective_perspective_spread.objective_perspective_point
        #     )
        #     print(relative_point, perspective.target_point)
        #     if perspective.target_point <= 0:
        #         perspective.target_point = 0
        #     perspective.target_point += objective_perspective_point
        #     perspective.save()
        #     objective_perspective_spread.objective_perspective_point = (
        #         objective_perspective_point
        #     )
        #     objective_perspective_spread.save()
        #     objective_total_score += objective_perspective_point
        # instance.target_point = objective_total_score
        instance = super(ObjectiveSerializer, self).update(
            instance=instance, validated_data=validated_data
        )

        instance.modify_change_to_active_task()
        instance.modify_change_to_closed_task()

        return instance

    def _process_serialized_input(self, validated_data, instance=None):
        name = validated_data.get("name").lower()

        if not instance:
            if self.Meta.model.objects.filter(name=name).exists():
                raise serializers.ValidationError(
                    {"name": "name is already taken"}
                )

        corporate_level = validated_data.pop("corporate_level")
        corporate_level_obj = process_structure(
            corporate_level, CorporateLevel
        )

        # process schedule
        start_date = validated_data.get("start_date")
        routine_option = validated_data.get("routine_option")
        after_occurrence = validated_data.get("after_occurrence", None)
        end_date = validated_data.get("end_date", None)
        start_date_list = []  # list of start dates

        try:
            start_date_list.extend(
                process_start_date_list(
                    routine_option,
                    start_date,
                    end_date,
                    after_occurrence,
                )
            )
        except CustomValidation as _:
            key, message = _.extract_key_message()
            raise serializers.ValidationError({key: message})

        validated_data.update(
            {
                "name": name,
                "corporate_level": corporate_level_obj,
                "start_date_list": start_date_list,
            }
        )
        return validated_data


class ObjectiveImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))

        error_arr = []
        fields = (
            "name",
            "corporate_name",
            "routine_option",
            "start_date",
            "end_date",
            "after_occurrence",
            "perspective_names",
            "perspective_relative_points",
        )

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                data = dict(zip(fields, line_from_file))
                cleaned_data = self.__clean_data(data)
                serializer = ObjectiveSerializer(
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
        return {"objective": "Objectives has been created"}

    def __clean_data(self, data: dict) -> dict:
        """returns a clean data for the serializer"""
        data.update(
            {
                "corporate_level": {
                    "uuid": self.__get_corporate_level(
                        data.pop("corporate_name")
                    ).uuid
                },
                "start_date": try_parsing_date(data.pop("start_date")),
                "end_date": self.__extract_end_date(data.pop("end_date")),
                "after_occurrence": self.__extract_if_exist(
                    data.pop("after_occurrence")
                ),
                "perspective": self.__extract_perspective(
                    data.pop("perspective_names"),
                    data.pop("perspective_relative_points"),
                ),
            }
        )
        return {field: value for field, value in data.items() if value != None}

    @staticmethod
    def __extract_if_exist(string: str):
        """Returns field if string is not empty"""
        return string if string != "" else None

    @staticmethod
    def __extract_end_date(date: str):
        """Returns end date if end date is not empty"""
        return try_parsing_date(date) if date != "" else None

    def __extract_perspective(self, names: str, relative_points: str) -> list:
        """Return a dict of perspectives"""
        names_list = str(names).strip().split(",")
        relative_points_list = str(relative_points).strip().split(",")

        if len(names_list) != len(relative_points_list):
            raise CustomValidation(
                detail="perspective names does not match perspective relative points.",
                field="perspective_names",
                status_code=400,
            )

        perspectives = []
        for name, relative_point in zip(names_list, relative_points_list):
            perspectives.append(
                {
                    "perspective_id": self.__get_perspective(
                        name
                    ).perspective_id,
                    "relative_point": relative_point,
                }
            )
        return perspectives

    @staticmethod
    def __get_corporate_level(name: str) -> CorporateLevel:
        """Returns coperate level by name if it exists"""
        corporate_levels = CorporateLevel.objects.filter(
            name=str(name).lower().strip()
        )
        if not corporate_levels.exists():
            raise CustomValidation(
                detail="corporate level does not exist.",
                field="corporate",
                status_code=400,
            )
        return corporate_levels.first()

    @staticmethod
    def __get_perspective(name: str) -> Perspective:
        """Returns perspective by name if it exists"""
        perspectives = Perspective.objects.filter(
            name=str(name).lower().strip()
        )
        if not perspectives.exists():
            raise CustomValidation(
                detail=f"perspective name ({name}) does not exist.",
                field="perspective",
                status_code=400,
            )
        return perspectives.first()


class MultipleObjectiveSerializer(serializers.Serializer):
    objective = serializers.SlugRelatedField(
        slug_field="objective_id",
        queryset=Objective.objects.all(),
        required=True,
        many=True,
    )
