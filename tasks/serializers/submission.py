from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from django.contrib.auth import get_user_model
from tasks.models import Task, TaskSubmission

User = get_user_model()


class NestedTaskSerializer(serializers.ModelSerializer):
    task_id = serializers.UUIDField(required=True)
    duration = serializers.DurationField(required=False, read_only=True)

    class Meta:
        model = Task
        fields = [
            "name",
            "task_id",
            "rework_limit",
            "start_date",
            "start_time",
            "duration",
        ]
        extra_kwargs = {
            "name": {"read_only": True},
            "rework_limit": {"read_only": True},
            "start_time": {"read_only": True},
            "start_date": {"read_only": True},
        }

    def validate_task_id(self, value):
        if (
            self.context["request"]._request.method == "POST"
            or self.context["request"]._request.method == "PUT"
        ):
            if not self.Meta.model.objects.filter(task_id=value).exists():
                raise serializers.ValidationError(
                    {"task.task_id": f"{value} is not a valid task id"}
                )
        return value

    @staticmethod
    def get_duration(obj):
        return obj.duration.total_seconds()


class UserByUUIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("user_id", "first_name", "last_name", "email")
        extra_kwargs = {
            "user_id": {"read_only": True},
            "first_name": {"read_only": True},
            "last_name": {"read_only": True},
            "email": {"read_only": True},
        }


class TaskSubmissionSerializer(serializers.ModelSerializer):
    task = NestedTaskSerializer(many=False, required=True, write_only=True)
    user = UserByUUIDSerializer(many=False, required=False)
    quantity_target_unit_achieved = serializers.DecimalField(
        required=False, decimal_places=2, max_digits=18, min_value=0.00
    )

    class Meta:
        model = TaskSubmission
        fields = [
            "task_submission_id",
            "task",
            "user",
            "submission",
            "quantity_target_unit_achieved",
            "user",
            "created",
        ]
        extra_kwargs = {
            "task_submission_id": {"read_only": True},
            "created": {"read_only": True},
            "submission": {"required": False},
        }

    def create(self, validated_data):
        validated_data = self._process_serialized_input(validated_data)
        # return None
        return super().create(validated_data)

    def _process_serialized_input(self, validated_data):
        user = self.context["request"].user
        task_id = validated_data.pop("task").get("task_id")
        task_obj = Task.objects.get(task_id=task_id)
        submission = validated_data.get("submission", None)
        quantity_target_unit_achieved = validated_data.get(
            "quantity_target_unit_achieved", None
        )

        self._check_permission_and_validate_submissions(
            task_obj, user, submission, quantity_target_unit_achieved
        )

        validated_data.update({"task": task_obj, "user": user})
        return validated_data

    @staticmethod
    def _check_permission_and_validate_submissions(
        task_obj: Task, user, submission, quantity_target_unit_achieved
    ):

        # raise exception if user is not assignor or owner
        if not task_obj.is_task_owner(user) and not task_obj.is_task_assignor(
            user
        ):
            raise PermissionDenied(
                {
                    "detail": "Permission denied to make submission for this task"
                }
            )

        # raise exception if user is owner and is not allowed to make submission
        if (
            task_obj.is_task_owner(user)
            and not task_obj.is_owner_allowed_to_make_submission()
        ):
            raise PermissionDenied(
                {
                    "detail": "Permission denied, owner is not allowed to make "
                    "submission at this stage"
                }
            )

        # raise exception if user is assignor and task is not closed
        if (
            task_obj.is_task_assignor(user)
            and not task_obj.task_status == Task.AWAITING_RATING
        ):
            raise PermissionDenied(
                {
                    "detail": "Permission denied, assignor is not allowed to make "
                    "submission at this stage"
                }
            )

        # ensures that submission is not none for qualitative task
        if task_obj.is_qualitative_task() and submission == None:
            raise serializers.ValidationError(
                {"submission": f"{submission} is not a valid submission"}
            )

        if (
            not task_obj.is_quantitative_task()
            and quantity_target_unit_achieved
        ):
            raise serializers.ValidationError(
                {"quantity_target_unit_achieved": f"Not valid for this task"}
            )
