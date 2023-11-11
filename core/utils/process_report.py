from typing import List

from strategy_deck.models.initiative import Initiative
from strategy_deck.models.objective import Objective


def process_tasks_for_report(tasks):
    """returns cumulation for all target points"""
    current_cumulative_turn_around_time_target_point = 0
    current_cumulative_turn_around_time_target_point_achieved = 0

    current_cumulative_quantity_target_point = 0
    current_cumulative_quantity_target_point_achieved = 0

    current_cumulative_quality_target_point = 0
    current_cumulative_quality_target_point_achieved = 0

    current_cumulative_target_point = 0
    current_cumulative_target_point_achieved = 0

    for task in tasks:

        current_cumulative_turn_around_time_target_point += (
            task.turn_around_time_target_point
        )
        task.cumulative_turn_around_time_target_point = (
            current_cumulative_turn_around_time_target_point
        )
        current_cumulative_turn_around_time_target_point_achieved += (
            task.turn_around_time_target_point_achieved
        )
        task.cumulative_turn_around_time_target_point_achieved = (
            current_cumulative_turn_around_time_target_point_achieved
        )

        current_cumulative_quantity_target_point += task.quantity_target_point
        task.cumulative_quantity_target_point = (
            current_cumulative_quantity_target_point
        )
        current_cumulative_quantity_target_point_achieved += (
            task.quantity_target_point_achieved
        )
        task.cumulative_quantity_target_point_achieved = (
            current_cumulative_quantity_target_point_achieved
        )

        current_cumulative_quality_target_point += task.quality_target_point
        task.cumulative_quality_target_point = (
            current_cumulative_quality_target_point
        )
        current_cumulative_quality_target_point_achieved += (
            task.quality_target_point_achieved
        )
        task.cumulative_quality_target_point_achieved = (
            current_cumulative_quality_target_point_achieved
        )

        current_cumulative_target_point += task.target_point
        task.cumulative_target_point = current_cumulative_target_point
        current_cumulative_target_point_achieved += task.target_point_achieved
        task.cumulative_target_point_achieved = (
            current_cumulative_target_point_achieved
        )

    return tasks


def get_initiatives(upline_obj) -> List[Initiative]:
    """Returns a list of all connected initiatives to an objective or initiative"""

    if isinstance(upline_obj, Objective):
        initiatives = []  # empty initial connected initiatives array

        # current objective downlines
        current_initiatives = upline_obj.objective_initiative.all()

    else:  # is an instance of initiative
        initiatives = [upline_obj]  # initial connected initiatives array

        # current initiative downlines
        current_initiatives = upline_obj.initiative_initiative.all()

    while current_initiatives.exists():
        temp_initiatives = Initiative.objects.none()
        for initiative in current_initiatives:
            temp_initiatives = (
                temp_initiatives | initiative.initiative_initiative.all()
            )
            initiatives += [initiative]
        current_initiatives = temp_initiatives

    return initiatives
