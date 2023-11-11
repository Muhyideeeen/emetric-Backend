from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, post_delete


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks"

    def ready(self) -> None:
        from tasks.models import TaskSubmission, Task
        from tasks.signals import (
            post_save_task_submission_created_receiver,
            post_save_task_created_receiver,
            post_delete_task_receiver,
            pre_save_task_receiver
        )

        post_save.connect(
            post_save_task_submission_created_receiver, sender=TaskSubmission
        )

        post_save.connect(post_save_task_created_receiver, sender=Task)
        
        pre_save.connect(pre_save_task_receiver, sender=Task)

        post_delete.connect(post_delete_task_receiver, sender=Task)

        return super().ready()
