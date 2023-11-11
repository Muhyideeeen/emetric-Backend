from django.apps import AppConfig
from django.db.models.signals import post_save


class EmetricCalendarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "emetric_calendar"

    def ready(self) -> None:
        from emetric_calendar.models import Holiday
        from emetric_calendar.signals import post_save_holiday_created_receiver

        post_save.connect(post_save_holiday_created_receiver, sender=Holiday)
        return super().ready()
