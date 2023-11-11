from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class DesignationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "designation"

    def ready(self):
        from designation.models import Designation
        from designation.signals import (
            post_delete_designation_receiver,
            post_save_designation_receiver,
        )

        post_delete.connect(
            post_delete_designation_receiver, sender=Designation
        )
        post_save.connect(post_save_designation_receiver, sender=Designation)
