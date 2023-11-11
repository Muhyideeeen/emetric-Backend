from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save
from django.utils.translation import ugettext_lazy as _


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'
    verbose_name = _('account')

    def ready(self):
        from account.models import User, EmailInvitation
        from account.signals import (
            post_save_user_created_receiver,
            pre_save_email_activation,
        )

        post_save.connect(post_save_user_created_receiver, sender=User)
        pre_save.connect(pre_save_email_activation, sender=EmailInvitation)
