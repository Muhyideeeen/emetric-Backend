from typing import Dict
from django.core.cache import cache

from emetric_calendar.models import Holiday


def post_save_holiday_created_receiver(
    sender, instance: Holiday, created, **kwargs: Dict
):

    if created:
        instance.delete_related_tasks()

    cache.delete("holiday_queryset")
