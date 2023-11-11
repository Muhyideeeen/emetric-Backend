from e_metric_api.celery import app
from tasks.models import Task


@app.task()
def change_task_status_to_active(task_id):
    """
    changes the task status to active
    """
    task_obj = Task.objects.get(pk=task_id)
    # change overdue task status
    if task_obj.task_status == Task.PENDING:
        task_obj.task_status = Task.ACTIVE
        task_obj.save()

    return f"task {task_obj.name} has ben changed to active"


@app.task()
def change_task_status_to_over_due(task_id: int):
    """
    change overdue task status to over due
    """
    task_obj: Task = Task.objects.get(pk=task_id)
    # change overdue task status
    if task_obj.task_status == Task.ACTIVE:
        task_obj.task_status = Task.OVER_DUE
        task_obj.save()

    return f"task {task_obj.name} has ben changed to over due"


@app.task()
def change_task_status_to_rework_over_due(task_id: int):
    """
    change overdue task status to rework over due
    """
    task_obj = Task.objects.get(pk=task_id)
    if task_obj.task_status == Task.REWORK:
        task_obj.task_status = Task.REWORK_OVER_DUE
        task_obj.save()
    return f"task {task_obj.name} has ben changed to rework over due"


@app.task()
def generate_system_based_rating(task_id: int):
    """Generates system based ratings"""
    task_obj: Task = Task.objects.get(pk=task_id)
    task_obj.generate_system_based_rating_for_task()

    return f"System based rating for task {task_obj.name} has been generated"
