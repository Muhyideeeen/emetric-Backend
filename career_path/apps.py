from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class CareerPathConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "career_path"

    def ready(self) -> None:
        from career_path.models import CareerPath
        from career_path.signals import (
            post_career_path_save_receiver,
            post_career_path_delete_receiver,
        )

        post_save.connect(post_career_path_save_receiver, sender=CareerPath)
        post_delete.connect(post_career_path_delete_receiver, sender=CareerPath)

        return super().ready()
