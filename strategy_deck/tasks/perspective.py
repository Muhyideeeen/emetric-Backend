from decimal import Decimal
from e_metric_api.celery import app
from strategy_deck.models import Perspective


@app.task()
def update_connected_perspective_target_point(
    perspective_id: int, target_point: Decimal
):
    """
    Update perspective target point based on target point
    changes from downline
    """
    perspective_obj: Perspective = Perspective.objects.get(pk=perspective_id)
    perspective_obj.update_target_point(target_point)

    return f"{perspective_obj.name} target point has been updated"
