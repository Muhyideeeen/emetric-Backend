from typing import Dict

from account.models import User, EmailInvitation,Role
from core.utils import key_generator,helper_function


def post_save_user_created_receiver(sender,
                                    instance: User,
                                    created,
                                    **kwargs: Dict):
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

    if created and not instance.is_active and not instance.is_superuser:
        email = instance.email
        if instance.user_role.role==Role.ADMIN_HR:
            email=helper_function.get_adminHr_actuall_email(email)
        email_activation_obj: EmailInvitation = EmailInvitation.objects.create(
            user=instance,
            email=email
        )
        instance.is_registration_mail_sent = True
        instance.save()
        if not instance.is_invited:
            email_activation_obj.send_confirmation(first_name=instance.first_name, last_name=instance.last_name)


def pre_save_email_activation(sender,
                              instance: EmailInvitation,
                              **kwargs: Dict):
    """
    pre-save a key in db before email activation
    Args:
        sender:
        instance:
        **kwargs:

    Returns:

    """
    if not instance.activated and not instance.forced_expired:
        if not instance.key:
            instance.key = key_generator(instance)
