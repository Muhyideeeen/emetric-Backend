from django.db import connection
from django.utils import timezone
from rest_framework import serializers
from core.utils.process_durations import get_localized_time
from core.utils.validators import validate_file_extension_for_pdf

from tasks.models import Task
from tasks.models.submission import TaskSubmission


class TaskRatingSerializer(serializers.ModelSerializer):
    submission = serializers.FileField(
        required=False, validators=[validate_file_extension_for_pdf]
    )
    quantity_target_unit_achieved = serializers.DecimalField(
        required=False, decimal_places=2, max_digits=18, min_value=0.00
    )

    class Meta:
        model = Task
        fields = [
            "task_id",
            "quality_target_point_achieved",
            "quantity_target_unit_achieved",
            "rating_remark",
            "use_owner_submission",
            "submission",
        ]
        extra_kwargs = {
            "task_id": {"read_only": True},
            "quality_target_point_achieved": {"required": False},
            "rating_remark": {"required": True},
            "use_owner_submission": {"default": True},
        }

    def validate(self, attrs):
        attrs = super(TaskRatingSerializer, self).validate(attrs=attrs)

        submission = attrs.get("submission", None)
        use_owner_submission = attrs.get("use_owner_submission")

        if not use_owner_submission and not submission:
            raise serializers.ValidationError(
                {
                    "submission": "This field is required when the owner's submission is not used."
                }
            )

        elif use_owner_submission and submission:
            raise serializers.ValidationError(
                {
                    "submission": "This field is not required when the owner's submission is used.",
                }
            )

        return attrs

    def validate_quality_target_point_achieved(self, value):

        if (
            self.instance
            and not self.instance.is_quality_target_point_achieved_valid(value)
        ):
            raise serializers.ValidationError(
                {
                    "quality_target_point_achieved": "Invalid quality target point achieved"
                }
            )
        return value

    def update(self, instance: Task, validated_data):
        validated_data = self._process_serialized_input(
            validated_data, instance
        )
        submission = validated_data.pop("submission", None)
        quantity_target_unit_achieved = validated_data.pop(
            "quantity_target_unit_achieved",
            instance.task_submission.all()
            .first()
            .quantity_target_unit_achieved,
        )

        # create submission
        TaskSubmission.objects.create(
            user=self.context["request"].user,
            submission=submission,
            task=instance,
            quantity_target_unit_achieved=quantity_target_unit_achieved,
        )
        return super().update(instance, validated_data)

    @staticmethod
    def _process_serialized_input(validated_data, instance: Task):
        quality_target_point_achieved = validated_data.get(
            "quality_target_point_achieved", 0
        )

        if not instance.is_assignor_allowed_to_rate():
            raise serializers.ValidationError(
                {"task_status": "Task cannot be rated at this stage"}
            )

        validated_data.update(
            {
                "quality_target_point_achieved": quality_target_point_achieved,
                "task_status": Task.CLOSED,  # sets task to closed
            }
        )
        return validated_data


class TaskReworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "task_id",
            "rework_remark",
            "rework_end_date",
            "rework_end_time",
        ]
        extra_kwargs = {
            "task_id": {"read_only": True},
            "rework_remark": {"required": True},
            "rework_end_date": {"required": True},
            "rework_end_time": {"required": True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tenant = connection.tenant
        rework_end_date = attrs.get("rework_end_date")
        rework_end_time = attrs.get("rework_end_time")
        end_date_time = get_localized_time(
            rework_end_date, rework_end_time, tenant.timezone
        )

        if end_date_time < timezone.now():
            raise serializers.ValidationError(
                {
                    "rework_end_date": "New end date cannot be in the past",
                    "rework_end_time": "New end time cannot be in the past",
                }
            )
        return attrs

    def update(self, instance, validated_data):
        validated_data = self._process_serialized_input(
            validated_data, instance
        )
        # return None
        return super().update(instance, validated_data)

    @staticmethod
    def _process_serialized_input(validated_data, instance: Task):

        if not instance.is_assignor_allowed_to_rate():
            raise serializers.ValidationError(
                {"task_status": "Task rework is not possible at this stage"}
            )

        if instance.is_rework_limit_zero():
            raise serializers.ValidationError(
                {"rework_limit": "Rework limit is zero"}
            )

        validated_data.update(
            {
                "rework_limit": instance.rework_limit - 1,
                "task_status": Task.REWORK,
            }
        )
        return validated_data
