from datetime import timedelta, date
from typing import Dict, List
from django.db import connection
from django.contrib.auth import get_user_model
from pyexcel_xlsx import get_data
from rest_framework import serializers, fields
from rest_framework.exceptions import PermissionDenied
from core.utils.bulk_upload import extract_key_message
from core.utils.eager_loading import EagerLoadingMixin
from core.utils.exception import CustomValidation
from core.utils.permissions import has_access_to_create_task
from core.utils.process_durations import (
    try_parsing_date,
)
from core.utils.task_process import (
    process_start_date_list_for_task,
    process_target_point,
)
from core.utils.validators import validate_file_extension_for_xlsx
from strategy_deck.models import Initiative
from strategy_deck.serializers.initiative import NestedInitiativeSerializer
from tasks.models import Task

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    upline_initiative = NestedInitiativeSerializer(many=False, required=True)

    task_type = serializers.ChoiceField(
        required=True, choices=Task.TASK_TYPE_CHOICES
    )

    start_date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)
    duration = serializers.DurationField(required=True)
    routine_option = serializers.ChoiceField(
        required=True, choices=Task.ROUTINE_TYPE_CHOICES
    )
    repeat_every = serializers.IntegerField(
        min_value=1, max_value=14, required=False
    )
    occurs_days = fields.MultipleChoiceField(
        choices=Task.DAY_CHOICES, required=False
    )
    occurs_month_day_number = serializers.IntegerField(
        min_value=1, max_value=31, required=False
    )
    occurs_month_day_position = serializers.ChoiceField(
        required=False, choices=Task.DAY_POSITION_CHOICES
    )
    occurs_month_day = serializers.ChoiceField(
        required=False, choices=Task.DAY_CHOICES
    )
    end_date = serializers.DateField(required=False)
    after_occurrence = serializers.IntegerField(
        min_value=1, max_value=20, required=False
    )

    rework_limit = serializers.IntegerField(min_value=0, required=False)

    turn_around_time_target_point = serializers.DecimalField(
        required=True, decimal_places=2, max_digits=18, min_value=0
    )

    quantity_target_unit = serializers.DecimalField(
        required=False, decimal_places=2, max_digits=18, min_value=0
    )
    quantity_target_point = serializers.DecimalField(
        required=False, decimal_places=2, max_digits=18, min_value=0
    )

    quality_target_point = serializers.DecimalField(
        required=False, decimal_places=2, max_digits=18, min_value=0
    )
    select_related_fields = (
        "upline_initiative",
        "upline_initiative__owner",
        "upline_initiative__assignor",
    )
    prefetch_related_fields = ()

    class Meta:
        model = Task
        fields = [
            "task_id",
            "name",
            "upline_initiative",
            "task_type",
            "routine_round",
            "start_date",
            "start_time",
            "duration",
            "routine_option",
            "repeat_every",
            "occurs_days",
            "occurs_month_day_number",
            "occurs_month_day_position",
            "occurs_month_day",
            "end_date",
            "after_occurrence",
            "task_status",
            "target_brief",
            "turn_around_time_target_point",
            "turn_around_time_target_point_achieved",
            "rework_limit",
            "rework_remark",
            "rework_end_date",
            "rework_end_time",
            "quantity_target_unit",
            "quantity_target_unit_achieved",
            "quantity_target_point",
            "quantity_target_point_achieved",
            "quality_target_point",
            "quality_target_point_achieved",
            "target_point",
            "target_point_achieved",
            "sensitivity_score",
            "plagiarism_score",
            "average_system_based_score",
            "rating_remark",
        ]
        extra_kwargs = {
            "task_id": {"read_only": True},
            "target_brief": {"required": False},
            "routine_round": {"read_only": True},
            "task_status": {"read_only": True},
            "rework_remark": {"read_only": True},
            "rating_remark": {"read_only": True},
            "rework_end_date": {"read_only": True},
            "rework_end_time": {"read_only": True},
            "turn_around_time_target_point_achieved": {"read_only": True},
            "quantity_target_point_achieved": {"read_only": True},
            "quality_target_point_achieved": {"read_only": True},
            "target_point_achieved": {"read_only": True},
            "sensitivity_score": {"read_only": True},
            "plagiarism_score": {"read_only": True},
            "average_system_based_score": {"read_only": True},
        }

    @staticmethod
    def get_duration(obj):
        return obj.duration.total_seconds()

    def validate(self, attrs):
        tenant = connection.tenant
        attrs = super(TaskSerializer, self).validate(attrs=attrs)

        self._validate_targets(attrs)

        routine_option = attrs.get("routine_option")

        if routine_option != Task.ONCE:

            if routine_option == Task.DAILY:
                self._validate_for_daily(attrs)

            elif routine_option == Task.WEEKLY:
                self._validate_for_weekly(attrs, tenant)

            elif routine_option == Task.MONTHLY:
                self._validate_for_monthly(attrs, tenant)

            end_date = attrs.get("end_date", None)
            after_occurrence = attrs.get("after_occurrence", None)

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

        return attrs

    @staticmethod
    def _validate_targets(attrs):
        task_type = attrs.get("task_type")
        quantity_target_point = attrs.get("quantity_target_point", None)
        quality_target_point = attrs.get("quality_target_point", None)
        quantity_target_unit = attrs.get("quantity_target_unit", None)
        rework_limit = attrs.get("rework_limit", None)

        if task_type == Task.QUALITATIVE:
            if quantity_target_point:
                raise serializers.ValidationError(
                    {
                        "quantity_target_point": "This field is not required for task type.",
                    }
                )
            
            if  quantity_target_unit:
                raise serializers.ValidationError(
                    {
                        "quantity_target_unit": "This field is not required for task type.",
                    }
                )

            if not quality_target_point:
                raise serializers.ValidationError(
                    {
                        "quality_target_point": "This field is required for task type.",
                    }
                )
                
            if rework_limit == None:
                raise serializers.ValidationError(
                    {
                        "rework_limit": "This field is required for task type.",
                    }
                )

        elif task_type == Task.QUANTITATIVE:
            if quality_target_point:
                raise serializers.ValidationError(
                    {
                        "quality_target_point": "This field is not required for task type.",
                    }
                )
            if rework_limit:
                raise serializers.ValidationError(
                    {
                        "rework_limit": "This field is not required for task type.",
                    }
                )

            if not quantity_target_point:
                raise serializers.ValidationError(
                    {
                        "quantity_target_point": "This field is required for task type.",
                    }
                )
            
            if not quantity_target_unit:
                raise serializers.ValidationError(
                    {
                        "quantity_target_unit": "This field is required for task type.",
                    }
                )

        else:

            if (
                not quality_target_point
                or not quantity_target_point
                or quantity_target_unit == None
                or rework_limit == None
            ):
                raise serializers.ValidationError(
                    {
                        "quality_target_point": "This field is required for task type.",
                        "quantity_target_point": "This field is required for task type.",
                        "quantity_target_unit": "This field is required for task type.",
                        "rework_limit": "This field is required for task type.",
                    }
                )

    @staticmethod
    def _validate_for_monthly(attrs, tenant):
        occurs_month_day_number = attrs.get("occurs_month_day_number", None)
        occurs_month_day_position = attrs.get(
            "occurs_month_day_position", None
        )
        occurs_month_day = attrs.get("occurs_month_day", None)

        if occurs_month_day_number == None and (
            occurs_month_day_position == None or occurs_month_day == None
        ):
            raise serializers.ValidationError(
                {
                    "occurs_month_day_number": "This field is required.",
                    "occurs_month_day_position": "This field is required.",
                    "occurs_month_day": "This field is required.",
                }
            )

        if occurs_month_day_number != None and (
            occurs_month_day_position != None or occurs_month_day != None
        ):
            raise serializers.ValidationError(
                {
                    "occurs_month_day_number": "All fields can not be provided.",
                    "occurs_month_day_position": "All fields can not be provided.",
                    "occurs_month_day": "All fields can not be provided.",
                }
            )

        if occurs_month_day:

            if str(occurs_month_day) not in tenant.work_days:
                raise serializers.ValidationError(
                    {"occurs_days": "occurs days must be in work day"}
                )

    @staticmethod
    def _validate_for_weekly(attrs, tenant):
        occurs_days = attrs.get("occurs_days", None)
        start_date = attrs.get("start_date")

        if occurs_days == None:
            raise serializers.ValidationError(
                {"occurs_days": "This field is required."}
            )
        else:

            if start_date.weekday() not in occurs_days:
                raise serializers.ValidationError(
                    {"occurs_days": "occurs days every must include start day"}
                )

            for day in occurs_days:

                if str(day) not in tenant.work_days:
                    raise serializers.ValidationError(
                        {"occurs_days": "occurs days must be work days"}
                    )

    @staticmethod
    def _validate_for_daily(attrs):
        repeat_every = attrs.get("repeat_every", None)

        if repeat_every == None:
            raise serializers.ValidationError(
                {"repeat_every": "This field is required."}
            )

    def create(self, validated_data):
        validated_data = self._process_serialized_input(validated_data)
        start_date_list = validated_data.pop("start_date_list", None)
        # return None
        tasks_array = []

        for index, start_date in enumerate(start_date_list):
            validated_data.update(
                {"start_date": start_date, "routine_round": index + 1}
            )
            tasks_array.append(Task(**validated_data))
        tasks = Task.objects.bulk_create(tasks_array)

        return tasks[0]

    def update(self, instance: Task, validated_data):
        if instance.task_status != Task.PENDING:
            raise PermissionDenied(
                {"status": "Permission denied to edit this task"}
            )

        routine_option = validated_data.get("routine_option")
        if routine_option != Task.ONCE:
            raise serializers.ValidationError(
                {
                    "routine_option": "Routine option for task update must be once"
                }
            )

        validated_data = self._process_serialized_input(validated_data, instance)
        start_date_list = validated_data.pop("start_date_list", None)

        validated_data.update(
            {
                "start_date": start_date_list[0],
                "name": instance.name,
                "target_brief": validated_data.get(
                    "target_brief", instance.target_brief
                ),
            }
        )

        instance = super(TaskSerializer, self).update(
            validated_data=validated_data, instance=instance
        )

        instance.modify_scheduled_event_for_task()
        instance.modify_change_to_active_task()
        instance.modify_change_to_over_due()

        return instance

    def _process_serialized_input(self, validated_data, instance=None):
        upline_initiative_id = validated_data.pop("upline_initiative").get(
            "initiative_id"
        )
        upline_initiative = Initiative.objects.get(
            initiative_id=upline_initiative_id
        )

        name = validated_data.get("name")
        owner_email = upline_initiative.owner.email
        task_name = f"{name} - {owner_email}".lower()

        if not upline_initiative.owner.employee.is_available():
            raise serializers.ValidationError(
                {"upline_initiative": "Owner is not available at the moment"}
            )

        if not instance:
            if self.Meta.model.objects.filter(name=task_name).exists():
                raise serializers.ValidationError(
                    {"name": "name is already taken"}
                )

        task_type = validated_data.get("task_type")
        turn_around_time_target_point = validated_data.get(
            "turn_around_time_target_point"
        )

        quantity_target_point = validated_data.get("quantity_target_point", 0)
        quality_target_point = validated_data.get("quality_target_point", 0)
        rework_limit = validated_data.get("rework_limit", 0)
        quantity_target_unit = validated_data.get("quantity_target_unit", 0)

        # process schedule
        tenant = connection.tenant
        start_date = validated_data.get("start_date")
        start_time = validated_data.get("start_time")
        duration = validated_data.get("duration") - timedelta(seconds=1)
        routine_option = validated_data.get("routine_option")

        repeat_every = validated_data.get("repeat_every", None)
        occurs_days = validated_data.get("occurs_days", None)
        after_occurrence = validated_data.get("after_occurrence", None)
        end_date = validated_data.get("end_date", None)
        occurs_month_day_number = validated_data.get(
            "occurs_month_day_number", None
        )
        occurs_month_day_position = validated_data.get(
            "occurs_month_day_position", None
        )
        occurs_month_day = validated_data.get("occurs_month_day", None)

        start_date_list = []  # list of a task start dates

        try:
            start_date_list.extend(
                process_start_date_list_for_task(
                    upline_initiative,
                    routine_option,
                    start_date,
                    start_time,
                    duration,
                    repeat_every,
                    occurs_days,
                    occurs_month_day_number,
                    occurs_month_day_position,
                    occurs_month_day,
                    end_date,
                    after_occurrence,
                    tenant,
                )
            )
        except CustomValidation as _:
            key, message = _.extract_key_message()
            raise serializers.ValidationError({key: message})

        (
            target_point,
            rework_limit,
            quality_target_point,
            quantity_target_point,
            quantity_target_unit,
        ) = process_target_point(
            task_type,
            rework_limit,
            turn_around_time_target_point,
            quality_target_point,
            quantity_target_point,
            quantity_target_unit,
        )

        validated_data.update(
            {
                "name": task_name,
                "upline_initiative": upline_initiative,
                "duration": duration,
                "start_date_list": start_date_list,
                "rework_limit": rework_limit,
                "quality_target_point": quality_target_point,
                "quantity_target_unit": quantity_target_unit,
                "quantity_target_point": quantity_target_point,
                "target_point": target_point,
            }
        )
        return validated_data


class TaskImportSerializer(serializers.Serializer):
    template_file = serializers.FileField(required=True, write_only=True)
    days_ref = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    def validate(self, attrs):
        file_uploaded = attrs.pop("template_file")
        validate_file_extension_for_xlsx(file_uploaded)

        sheets_from_file: Dict = get_data(file_uploaded, start_row=1)
        lines_from_file: List[List] = next(iter((sheets_from_file.values())))

        error_arr = []
        fields = (
            "name",
            "upline_initiative_name",
            "owner_email",
            "task_type",
            "routine_option",
            "start_date",
            "start_time",
            "duration",
            "repeat_every",
            "occurs_days",
            "occurs_month_day_number",
            "occurs_month_day_position",
            "occurs_month_day",
            "end_date",
            "after_occurrence",
            "rework_limit",
            "quality_target_point",
            "quantity_target_point",
            "quantity_target_unit",
            "turn_around_time_target_point",
        )

        for index, line_from_file in enumerate(lines_from_file):
            if not line_from_file:
                break
            try:
                data = dict(zip(fields, line_from_file))
                cleaned_data = self.__clean_data(data)
                serializer = TaskSerializer(
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
        return {"Task": "Task(s) has been created"}

    def __clean_data(self, data: dict) -> dict:
        """returns a clean data for the serializer"""
        data.update(
            {
                "upline_initiative": {
                    "initiative_id": self.__get_upline_initiative(
                        data.pop("upline_initiative_name"),
                        data.pop("owner_email"),
                        try_parsing_date(data.get("start_date")),
                    ).initiative_id
                },
                "start_date": try_parsing_date(data.pop("start_date")),
                "repeat_every": self.__extract_if_exist(
                    data.pop("repeat_every")
                ),
                "occurs_days": self.__extract_occurs_days(
                    data.pop("occurs_days")
                ),
                "occurs_month_day_number": self.__extract_if_exist(
                    data.pop("occurs_month_day_number")
                ),
                "occurs_month_day_position": self.__extract_if_exist(
                    data.pop("occurs_month_day_position")
                ),
                "occurs_month_day": self.__extract_occurs_month_day(
                    data.pop("occurs_month_day")
                ),
                "end_date": self.__extract_end_date(data.pop("end_date")),
                "after_occurrence": self.__extract_if_exist(
                    data.pop("after_occurrence")
                ),
                "rework_limit": self.__extract_if_exist(
                    data.pop("rework_limit")
                ),
                "quality_target_point": self.__extract_if_exist(
                    data.pop("quality_target_point")
                ),
                "quantity_target_point": self.__extract_if_exist(
                    data.pop("quantity_target_point")
                ),
                "quantity_target_unit": self.__extract_if_exist(
                    data.pop("quantity_target_unit")
                ),
            }
        )
        return {field: value for field, value in data.items() if value != None}

    @staticmethod
    def __extract_if_exist(string: str):
        """Returns field if string is not empty"""
        return string if string != "" else None

    def __extract_occurs_days(self, days: str):
        """Returns occurs days if days is not empty"""
        return self.__get_occurs_days(days) if days != "" else None

    def __extract_occurs_month_day(self, day: str):
        """Returns occurs month day if days is not empty"""
        return self.__get_occurs_day(day) if day != "" else None

    @staticmethod
    def __extract_end_date(date: str):
        """Returns end date if end date is not empty"""
        return try_parsing_date(date) if date != "" else None

    @staticmethod
    def __get_upline_initiative(
        name: str, email: str, date: date
    ) -> Initiative:
        """Returns initiative by name if it exists"""

        initiatives = Initiative.objects.filter(
            name=f"{str(name).lower().strip()} - {str(email).lower().strip()}",
            start_date__lte=date,
            end_date__gte=date,
        )
        if not initiatives.exists():
            raise CustomValidation(
                detail=f"initiative ({name} - {email}) does not exist on {date}.",
                field="initiative",
                status_code=400,
            )
        return initiatives.first()

    def __get_occurs_days(self, days: str) -> list:
        """Get occurs days by changing value to week day int"""
        days_list = days.split(",")
        occurs_days = []
        for day in days_list:
            try:
                occurs_days.append(
                    self.days_ref.index(str(day).lower().strip())
                )
            except ValueError:
                raise CustomValidation(
                    detail=f"invalid day ({day}).",
                    field="occurs_days",
                    status_code=400,
                )
        return occurs_days

    def __get_occurs_day(self, day: str) -> list:
        """Get occurs day by changing value to week day int"""
        try:
            occurs_day = self.days_ref.index(str(day).lower().strip())
        except ValueError:
            raise CustomValidation(
                detail=f"invalid day ({day}).",
                field="occurs_month_day",
                status_code=400,
            )
        return occurs_day


class MultipleTaskSerializer(serializers.Serializer):
    task = serializers.SlugRelatedField(
        slug_field="task_id",
        queryset=Task.objects.all(),
        required=True,
        many=True,
    )
