from django.core.cache import cache

from strategy_deck.models import Perspective


def post_save_perspective_receiver(
    sender, instance: Perspective, created, **kwargs
):
    """Signal for Perspective post save"""
    cache.delete("perspective_queryset")


def post_delete_perspective_receiver(
    sender, instance: Perspective, **kwargs
):
    """Delete all connected elements"""

    cache.delete("perspective_queryset")
