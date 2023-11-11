from django.core.cache import cache

from career_path.models import CareerPath


def post_career_path_save_receiver(
    sender, instance: CareerPath, created, **kwargs
):
    """Signal for career path post save"""
    cache.delete("career_path_queryset")  # clear career path queryset cache


def post_career_path_delete_receiver(sender, instance: CareerPath, **kwargs):
    """Signal for career path post delete"""
    cache.delete("career_path_queryset")
