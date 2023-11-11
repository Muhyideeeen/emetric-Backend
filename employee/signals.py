from typing import Dict
from django.core.cache import cache

from account.models import EmailInvitation
from employee.models import Employee
from django.db import transaction


def post_save_employee_created_receiver(
    sender, instance: Employee, created, **kwargs: Dict
):
    """
    Create an email invitation when a user is created, for a super admin,
    disregard sending an email, just validate it.
    Args:
        sender:
        created:
        instance:
        **kwargs:

    Returns:

    """

    if created:
        user = instance.user
        email_activation_obj: EmailInvitation = EmailInvitation.objects.get(
            user=user, email=user.email
        )

        if user.is_invited:
            transaction.on_commit(
                lambda: email_activation_obj.send_invitation()
            )
        cache.delete("employee_queryset")


def post_delete_employee_receiver(sender, instance: Employee, **kwargs: Dict):
    """Delete all connected elements"""
    instance.user.delete()
    cache.delete("employee_queryset")
