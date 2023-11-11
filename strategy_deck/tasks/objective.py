from decimal import Decimal
from e_metric_api.celery import app
from strategy_deck.models import Objective


@app.task()
def change_objective_status_to_active(objective_id):
    """
    changes the objective status to active
    """
    objective_obj: Objective = Objective.objects.get(pk=objective_id)
    objective_obj.objective_status = Objective.ACTIVE
    objective_obj.save()

    return f"objective {objective_obj.name} has ben changed to active"


@app.task()
def change_objective_status_to_closed(objective_id: int):
    """
    change objective status to closed
    """
    objective_obj: Objective = Objective.objects.get(pk=objective_id)
    # change to closed status
    objective_obj.objective_status = Objective.CLOSED
    objective_obj.save()

    return f"objective {objective_obj.name} has ben changed to closed"


@app.task()
def update_upline_objective_target_point(
    objective_id: int, target_point: Decimal
):
    """
    Update objective target point based on target point
    changes from downline
    """
    objective_obj: Objective = Objective.objects.get(pk=objective_id)
    objective_obj.update_target_point(target_point)

    return f"{objective_obj.name} target point has been updated"
