from decimal import Decimal
from rest_framework import serializers
from django_filters.utils import translate_validation

from core.serializers.nested import OwnerOrAssignorSerializer
from core.utils.process_report import get_initiatives, process_tasks_for_report
from strategy_deck.models.initiative import Initiative
from strategy_deck.models.objective import Objective
from tasks.filter import TaskFilter
from tasks.models.detail import Task


class TaskReportSerializer(serializers.ModelSerializer):
    percentage_turn_around_time_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )
    cumulative_turn_around_time_target_point = (
        serializers.SerializerMethodField(read_only=True)
    )
    cumulative_turn_around_time_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )
    percentage_cumulative_turn_around_time_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )

    percentage_quantity_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )
    cumulative_quantity_target_point = serializers.SerializerMethodField(
        read_only=True
    )
    cumulative_quantity_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )
    percentage_cumulative_quantity_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )

    percentage_quality_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )
    cumulative_quality_target_point = serializers.SerializerMethodField(
        read_only=True
    )
    cumulative_quality_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )
    percentage_cumulative_quality_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )

    percentage_target_point_achieved = serializers.SerializerMethodField(
        read_only=True
    )
    cumulative_target_point = serializers.SerializerMethodField(read_only=True)
    cumulative_target_point_achieved = serializers.SerializerMethodField(
        read_only=True
    )
    percentage_cumulative_target_point_achieved = (
        serializers.SerializerMethodField(read_only=True)
    )

    def get_percentage_turn_around_time_target_point_achieved(self, obj):
        if obj.turn_around_time_target_point != 0:
            return round(
                obj.turn_around_time_target_point_achieved
                / obj.turn_around_time_target_point
                * 100,
                2,
            )
        return Decimal(0)

    def get_cumulative_turn_around_time_target_point(self, obj):
        return obj.cumulative_turn_around_time_target_point

    def get_cumulative_turn_around_time_target_point_achieved(self, obj):
        return obj.cumulative_turn_around_time_target_point_achieved

    def get_percentage_cumulative_turn_around_time_target_point_achieved(
        self, obj
    ):
        if obj.cumulative_turn_around_time_target_point != 0:
            return round(
                obj.cumulative_turn_around_time_target_point_achieved
                / obj.cumulative_turn_around_time_target_point
                * 100,
                2,
            )
        return Decimal(0)

    def get_percentage_quantity_target_point_achieved(self, obj):
        if obj.quantity_target_point != 0:
            return round(
                obj.quantity_target_point_achieved
                / obj.quantity_target_point
                * 100,
                2,
            )
        return Decimal(0)

    def get_cumulative_quantity_target_point(self, obj):
        return obj.cumulative_quantity_target_point

    def get_cumulative_quantity_target_point_achieved(self, obj):
        return obj.cumulative_quantity_target_point_achieved

    def get_percentage_cumulative_quantity_target_point_achieved(self, obj):
        if obj.cumulative_quantity_target_point != 0:
            return round(
                obj.cumulative_quantity_target_point_achieved
                / obj.cumulative_quantity_target_point
                * 100,
                2,
            )
        return Decimal(0)

    def get_percentage_quality_target_point_achieved(self, obj):
        if obj.quality_target_point != 0:
            return round(
                obj.quality_target_point_achieved
                / obj.quality_target_point
                * 100,
                2,
            )
        return Decimal(0)

    def get_cumulative_quality_target_point(self, obj):
        return obj.cumulative_quality_target_point

    def get_cumulative_quality_target_point_achieved(self, obj):
        return obj.cumulative_quality_target_point_achieved

    def get_percentage_cumulative_quality_target_point_achieved(self, obj):
        if obj.cumulative_quality_target_point != 0:
            return round(
                obj.cumulative_quality_target_point_achieved
                / obj.cumulative_quality_target_point
                * 100,
                2,
            )
        return Decimal(0)

    def get_percentage_target_point_achieved(self, obj):
        if obj.target_point != 0:
            return round(
                obj.target_point_achieved / obj.target_point * 100,
                2,
            )
        return Decimal(0)

    def get_cumulative_target_point(self, obj):
        return obj.cumulative_target_point

    def get_cumulative_target_point_achieved(self, obj):
        return obj.cumulative_target_point_achieved

    def get_percentage_cumulative_target_point_achieved(self, obj):
        if obj.cumulative_target_point != 0:
            return round(
                obj.cumulative_target_point_achieved
                / obj.cumulative_target_point
                * 100,
                2,
            )
        return Decimal(0)

    class Meta:
        model = Task
        fields = [
            "task_id",
            "name",
            "start_date",
            "start_time",
            "duration",
            "routine_round",
            "task_type",
            "sensitivity_score",
            "plagiarism_score",
            "average_system_based_score",
            "turn_around_time_target_point",
            "turn_around_time_target_point_achieved",
            "percentage_turn_around_time_target_point_achieved",
            "cumulative_turn_around_time_target_point",
            "cumulative_turn_around_time_target_point_achieved",
            "percentage_cumulative_turn_around_time_target_point_achieved",
            "quantity_target_unit",
            "quantity_target_unit_achieved",
            "quantity_target_point",
            "quantity_target_point_achieved",
            "percentage_quantity_target_point_achieved",
            "cumulative_quantity_target_point",
            "cumulative_quantity_target_point_achieved",
            "percentage_cumulative_quantity_target_point_achieved",
            "quality_target_point",
            "quality_target_point_achieved",
            "percentage_quality_target_point_achieved",
            "cumulative_quality_target_point",
            "cumulative_quality_target_point_achieved",
            "percentage_cumulative_quality_target_point_achieved",
            "target_point",
            "target_point_achieved",
            "percentage_target_point_achieved",
            "cumulative_target_point",
            "cumulative_target_point_achieved",
            "percentage_cumulative_target_point_achieved",
        ]


class InitiativeReportSerializer(serializers.ModelSerializer):
    owner = OwnerOrAssignorSerializer(many=False)
    cumulative_report = serializers.SerializerMethodField(read_only=True)

    def get_cumulative_report(self, obj: Initiative):
        initiatives = get_initiatives(obj)  # gets all connected initiatives

        tasks = Task.objects.filter(
            task_status=Task.CLOSED, upline_initiative__in=initiatives
        )
        filterset = TaskFilter(self.context["request"].GET, queryset=tasks)

        if not filterset.is_valid():
            raise translate_validation(filterset.errors)

        processed_tasks = process_tasks_for_report(filterset.qs)
        # returns last task with the report details
        return TaskReportSerializer(processed_tasks, many=True).data[-1:]

    class Meta:
        model = Initiative
        fields = [
            "name",
            "initiative_id",
            "owner",
            "routine_round",
            "initiative_status",
            "start_date",
            "end_date",
            "target_point",
            "cumulative_report",
        ]


class ObjectiveReportSerializer(serializers.ModelSerializer):
    cumulative_report = serializers.SerializerMethodField(read_only=True)

    def get_cumulative_report(self, obj: Initiative):
        initiatives = get_initiatives(obj)  # gets all connected initiatives

        tasks = Task.objects.filter(
            task_status=Task.CLOSED, upline_initiative__in=initiatives
        )
        filterset = TaskFilter(self.context["request"].GET, queryset=tasks)

        if not filterset.is_valid():
            raise translate_validation(filterset.errors)

        processed_tasks = process_tasks_for_report(filterset.qs)
        # returns last task with the report details
        return TaskReportSerializer(processed_tasks, many=True).data[-1:]

    class Meta:
        model = Objective
        fields = [
            "name",
            "objective_id",
            "routine_round",
            "objective_status",
            "start_date",
            "end_date",
            "target_point",
            "cumulative_report",
        ]

    def get_cumulative_report(self, obj: Initiative):
        initiatives = get_initiatives(obj)  # gets all connected initiatives

        tasks = Task.objects.filter(
            task_status=Task.CLOSED, upline_initiative__in=initiatives
        )
        filterset = TaskFilter(self.context["request"].GET, queryset=tasks)

        if not filterset.is_valid():
            raise translate_validation(filterset.errors)

        processed_tasks = process_tasks_for_report(filterset.qs)
        # returns last task with the report details
        return TaskReportSerializer(processed_tasks, many=True).data[-1:]
