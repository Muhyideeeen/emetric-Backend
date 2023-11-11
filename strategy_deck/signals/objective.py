from typing import List
from celery import current_app
from django.core.cache import cache
from django.db.models import Sum
from django_celery_beat.models import PeriodicTask

from strategy_deck.models import Objective, ObjectivePerspectiveSpread
from strategy_deck.models.perspective import Perspective


def post_save_objective_receiver(
    sender, instance: Objective, created, **kwargs
):
    """Signal for objective post save"""
    if created:
        pass
    cache.delete("objective_queryset")
    return None


def pre_save_objective_receiver(sender, instance: Objective, **kwargs):
    """Execute before Objective is saved"""
    if instance.id is None:
        pass
    else:
        previous_objective_obj: Objective = Objective.objects.get(
            id=instance.id
        )
        update_connected_perspectives_target_point_for_update(
            instance, previous_objective_obj
        )


def post_delete_objective_receiver(sender, instance: Objective, **kwargs):
    """Delete all connected elements"""
    
    PeriodicTask.objects.filter(
        name__in=[
            f"{str(instance.objective_id)} active",
            f"{str(instance.objective_id)} closed",
        ]
    ).delete()
    
    spreads: List[
        ObjectivePerspectiveSpread
    ] = instance.objective_objective_perspective_spread.all()
    total_relative_point = (
        spreads.aggregate(Sum("relative_point")).get("relative_point__sum")
        or 0
    )

    for spread in spreads:
        target_point = (
            spread.relative_point
            / total_relative_point
            * instance.target_point
        )
        try:
            current_app.send_task(
                "strategy_deck.tasks.perspective.update_connected_perspective_target_point",
                (spread.perspective.pk, -target_point),
            )
        except Perspective.DoesNotExist:
            pass

    cache.delete("objective_queryset")


def update_connected_perspectives_target_point_for_update(
    instance: Objective, previous_objective_obj: Objective
):
    """
    Updates the connected perspectives target point during objective
    update
    """
    if previous_objective_obj.target_point != instance.target_point:
        target_point_diff = (
            instance.target_point - previous_objective_obj.target_point
        )

        spreads: List[
            ObjectivePerspectiveSpread
        ] = instance.objective_objective_perspective_spread.all()

        total_relative_point = (
            spreads.aggregate(Sum("relative_point")).get("relative_point__sum")
            or 0
        )

        for spread in spreads:
            target_point = (
                spread.relative_point
                / total_relative_point
                * target_point_diff
            )

            spread.objective_perspective_point = target_point
            current_app.send_task(
                "strategy_deck.tasks.perspective.update_connected_perspective_target_point",
                (spread.perspective.pk, target_point),
            )

        ObjectivePerspectiveSpread.objects.bulk_update(
            spreads, ["objective_perspective_point"]
        )
