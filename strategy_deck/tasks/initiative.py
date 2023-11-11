from decimal import Decimal
from e_metric_api.celery import app
from strategy_deck.models import Initiative


@app.task()
def change_initiative_status_to_active(initiative_id):
    """
    changes the initiative status to active
    """
    initiative_obj = Initiative.objects.get(pk=initiative_id)
    initiative_obj.initiative_status = Initiative.ACTIVE
    initiative_obj.save()

    return f"initiative {initiative_obj.name} has ben changed to active"


@app.task()
def change_initiative_status_to_closed(initiative_id: int):
    """
    change initiative status to closed"""
    initiative_obj: Initiative = Initiative.objects.get(pk=initiative_id)
    # change to closed status
    initiative_obj.initiative_status = Initiative.CLOSED
    initiative_obj.save()

    return f"initiative {initiative_obj.name} has ben changed to closed"


@app.task()
def update_upline_initiative_target_point(
    initiative_id: int, target_point: Decimal
):
    """
    Update initiative target point based on target point
    changes from downline
    """
    initiative_obj: Initiative = Initiative.objects.get(pk=initiative_id)
    initiative_obj.update_target_point(target_point)

    return f"{initiative_obj.name} target point has been updated"
