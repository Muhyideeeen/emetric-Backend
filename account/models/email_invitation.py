"""
email activation models
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, connection
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.apps import apps

from mailing.tasks.send_invitation_email_task import send_invitation_email
from mailing.tasks.send_confirmation_email_task import send_confirmation_email


DEFAULT_ACTIVATION_DAYS = getattr(settings, "DEFAULT_ACTIVATION_DAYS", 7)
User = get_user_model()


class EmailInvitationQuerySet(models.query.QuerySet):
    """
    Custom queryset for email
    """

    def confirmable(self):
        """
        check if mail is confirmable
        :return:
        """
        now = timezone.now()
        start_range = now - timedelta(days=DEFAULT_ACTIVATION_DAYS)
        end_range = now
        return self.filter(activated=False, forced_expired=False).filter(
            timestamp__gt=start_range, timestamp__lte=end_range
        )


class EmailInvitationManager(models.Manager):
    """
    Email activation model manager
    """

    def get_queryset(self):
        """
        query_set customizable for an email activation
        :return:
        """
        return EmailInvitationQuerySet(self.model, using=self._db)

    def confirmable(self):
        """
        check if email is confirmable
        :return:
        """
        return self.get_queryset().confirmable()

    def email_exists(self, email):
        """
        check the email activation model if a given email exist
        :param email:
        :return:
        """
        return (
            self.get_queryset()
            .filter(Q(email=email) | Q(user__email=email))
            .filter(activated=False)
        )


class EmailInvitation(models.Model):
    """
    Model for Email Activation
    """

    user: User = models.ForeignKey(
        User, to_field="user_id", on_delete=models.CASCADE
    )
    email: str = models.EmailField()
    key: str = models.CharField(max_length=255, blank=True, null=True)
    activated: bool = models.BooleanField(default=False)
    forced_expired: bool = models.BooleanField(default=False)
    expires: int = models.IntegerField(default=7)  # 7 days or 1 week
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    update: models.DateTimeField = models.DateTimeField(auto_now=True)

    objects = EmailInvitationManager()

    def __str__(self):
        return self.email

    @property
    def is_activated(self):
        """
        check if user is activated
        :return:
        """
        return self.activated

    def can_activate(self):
        """
        check if email can be activated
        :return:
        """
        email_activation_query = EmailInvitation.objects.filter(
            pk=self.pk
        ).confirmable()
        if email_activation_query.exists():
            return True
        return False

    def activate(self, password=None):
        """
        activate a user
        :return:
        """
        if self.can_activate():
            user = self.user
            user.is_active = True
            if password is not None:
                user.set_password(password)
            user.save()
            self.activated = True
            self.save()
            return True
        return False

    def send_confirmation(self, first_name: str, last_name: str):
        """
        send activation email
        :return:
        """

        if not self.activated and not self.forced_expired:
            if self.key:
                from_email = settings.DEFAULT_FROM_EMAIL
                base_url = settings.BASE_DOMAIN
                key_path = "account/verify/?key={}".format(self.key)
                verification_path = f"{base_url}{key_path}"

                context = {
                    "verification_path": verification_path,
                    "first_name": first_name,
                }
                html_template = render_to_string(
                    "auth/email_verification.html", context=context
                )

                mail_sender = {"email": from_email, "name": "Support"}
                mail_recipient = [{"email": self.email}]

                return send_confirmation_email.delay(
                    sender=mail_sender,
                    content=html_template,
                    first_name=first_name,
                    last_name=last_name,
                    recipient_email=mail_recipient,
                )
        return False

    def send_invitation(self):
        """
        send invitation email
        :return:
        """
        first_name = self.user.first_name
        last_name = self.user.last_name
        tenant = connection.tenant
        organisation_short_name = tenant.schema_name
        organisation_name = tenant.company_name

        if not self.activated and not self.forced_expired:
            if self.key:
                from_email = settings.DEFAULT_FROM_EMAIL
                base_url = settings.BASE_DOMAIN
                key_path = f"account/verify/service/?key={self.key}&org={organisation_short_name}"
                setup_path = f"{base_url}{key_path}"
                client_login_link = f"{base_url}"

                context = {
                    "setup_path": setup_path,
                    "first_name": first_name,
                    "organisation_name": organisation_name,
                    "organisation_short_name": organisation_short_name,
                    "client_login_link": client_login_link,
                }
                html_template = render_to_string(
                    "invitation/invite_user.html", context=context
                )

                mail_sender = {"email": from_email, "name": "Support"}
                mail_recipient = [{"email": self.email}]

                return send_invitation_email.delay(
                    sender=mail_sender,
                    content=html_template,
                    first_name=first_name,
                    last_name=last_name,
                    recipient_email=mail_recipient,
                )
        return False
