from typing import Dict

from strategy_deck.models import ObjectivePerspectiveSpread
from strategy_deck.models.objective import Objective
from strategy_deck.models.perspective import Perspective


def post_delete_objective_perspective_spread_receiver(
    sender, instance: ObjectivePerspectiveSpread, **kwargs: Dict
):
    """Reduce target point for perspective and objective"""

    try:
        instance.perspective.target_point -= (
            instance.objective_perspective_point
        )
        instance.perspective.save()
    except Perspective.DoesNotExist:
        pass

    try:
        instance.objective.target_point -= instance.objective_perspective_point
        instance.objective.save()
    except Objective.DoesNotExist:
        pass
