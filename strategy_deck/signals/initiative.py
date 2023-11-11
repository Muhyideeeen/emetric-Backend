from typing import Dict
from celery import current_app
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django_celery_beat.models import PeriodicTask

from strategy_deck.models import Initiative
from strategy_deck.models.objective import Objective



def post_save_initiative_receiver(
    sender, instance: Initiative, created, **kwargs
):
    """Signal for Initiative post save"""
    if created:
        instance.create_change_to_active_task()
        instance.create_change_to_closed_task()

    cache.delete("initiative_queryset")
    return None


def pre_save_initiative_receiver(sender, instance: Initiative, **kwargs: Dict):
    """Execute before initiative is saved"""
    if instance.id is None:
        pass
    else:
        previous_initiative_obj: Initiative = Initiative.objects.get(
            id=instance.id
        )
        if instance.upline_initiative:
            update_connected_initiative_target_point_for_update(
                instance, previous_initiative_obj
            )
        else:
            update_connected_objective_target_point_for_update(
                instance, previous_initiative_obj
            )


def post_delete_initiative_receiver(sender, instance: Initiative, **kwargs):
    """Delete all connected elements"""

    PeriodicTask.objects.filter(
        name__in=[
            f"{str(instance.initiative_id)} active",
            f"{str(instance.initiative_id)} closed",
        ]
    ).delete()

    try:
        if instance.upline_initiative:
            current_app.send_task(
                "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
                (instance.upline_initiative.pk, -instance.target_point),
            )
        else:
            current_app.send_task(
                "strategy_deck.tasks.objective.update_upline_objective_target_point",
                (instance.upline_objective.pk, -instance.target_point),
            )
    except ObjectDoesNotExist:
        pass

    cache.delete("initiative_queryset")


def update_connected_initiative_target_point_for_update(
    instance: Initiative, previous_initiative_obj: Initiative
):
    """
    Updates the connected initiative target point dunring initiative
    update
    """
    if previous_initiative_obj.upline_initiative != instance.upline_initiative:
        current_app.send_task(
            "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
            (
                previous_initiative_obj.upline_initiative.pk,
                -previous_initiative_obj.target_point,
            ),
        )
        current_app.send_task(
            "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
            (instance.upline_initiative.pk, instance.target_point),
        )

    else:
        if previous_initiative_obj.target_point != instance.target_point:
            target_point_diff = (
                instance.target_point - previous_initiative_obj.target_point
            )
            current_app.send_task(
                "strategy_deck.tasks.initiative.update_upline_initiative_target_point",
                (instance.upline_initiative.pk, target_point_diff),
            )


def update_connected_objective_target_point_for_update(
    instance: Initiative, previous_initiative_obj: Initiative
):
    """
    Updates the connected objective target point dunring initiative
    update
    """
    if previous_initiative_obj.upline_objective != instance.upline_objective:
        current_app.send_task(
            "strategy_deck.tasks.objective.update_upline_objective_target_point",
            (
                previous_initiative_obj.upline_objective.pk,
                -previous_initiative_obj.target_point,
            ),
        )
        current_app.send_task(
            "strategy_deck.tasks.objective.update_upline_objective_target_point",
            (instance.upline_objective.pk, instance.target_point),
        )

    else:
        if previous_initiative_obj.target_point != instance.target_point:
            target_point_diff = (
                instance.target_point - previous_initiative_obj.target_point
            )
            current_app.send_task(
                "strategy_deck.tasks.objective.update_upline_objective_target_point",
                (instance.upline_objective.pk, target_point_diff),
            )
