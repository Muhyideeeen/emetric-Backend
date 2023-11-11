from typing import Dict
from celery import current_app
from django.core.cache import cache
from django_celery_beat.models import PeriodicTask
from strategy_deck.models.initiative import Initiative

from tasks.models import Task, TaskSubmission
from tasks.tasks.detail import generate_system_based_rating


def post_save_task_created_receiver(
    sender, instance: Task, created, **kwargs: Dict
):
    """Execute after task is saved"""
    # created
    if created:
        instance.create_scheduled_event_for_task()
        instance.create_change_to_active_task()
        instance.create_change_to_over_due()
        current_app.send_task(
            "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
            (instance.upline_initiative.pk, instance.target_point),
        )

    if instance.task_status == Task.REWORK:
        instance.create_change_to_rework_over_due_task()

    cache.delete("task_queryset")


def pre_save_task_receiver(sender, instance: Task, **kwargs: Dict):
    """Execute before task is saved"""
    if instance.id is None:
        pass
    else:
        previous_task_obj: Task = Task.objects.get(id=instance.id)
        update_connected_initiative_target_point_for_update(
            instance, previous_task_obj
        )


def post_save_task_submission_created_receiver(
    sender, instance: TaskSubmission, created, **kwargs: Dict
):
    """Execute after task submission is saved"""
    if created:
        user = instance.user
        task: Task = instance.task

        # reduce rework limit is user is the owner
        if user == task.upline_initiative.owner:
            task.task_status = Task.AWAITING_RATING

        task.save()

        generate_system_based_rating.delay(task.pk)


def post_delete_task_receiver(sender, instance: Task, **kwargs: Dict):
    """Delete all connected elements"""
    PeriodicTask.objects.filter(
        name=f"{str(instance.task_id)} active"
    ).delete()

    PeriodicTask.objects.filter(
        name=f"{str(instance.task_id)} over_due"
    ).delete()
    try:
        current_app.send_task(
            "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
            (instance.upline_initiative.pk, -instance.target_point),
        )
    except Initiative.DoesNotExist:
        pass

    cache.delete("task_queryset")


def update_connected_initiative_target_point_for_update(
    instance: Task, previous_task_obj: Task
):
    """
    Updates the connected initiative target point dunring task
    update
    """
    if previous_task_obj.upline_initiative != instance.upline_initiative:
        current_app.send_task(
            "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
            (
                previous_task_obj.upline_initiative.pk,
                -previous_task_obj.target_point,
            ),
        )
        current_app.send_task(
            "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
            (instance.upline_initiative.pk, instance.target_point),
        )
    else:
        if previous_task_obj.target_point != instance.target_point:
            target_point_diff = (
                instance.target_point - previous_task_obj.target_point
            )
            current_app.send_task(
                "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
                (instance.upline_initiative.pk, target_point_diff),
            )
