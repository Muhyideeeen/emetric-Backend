from e_metric_api.celery import app

from mailing.services.mailing import MailException
from mailing.services.send_in_blue import SendInBlue


@app.task()
def send_invitation_email(sender: dict, content: str, first_name: str, last_name: str, recipient_email: list):
    """
    A function that sends an invitation email
    Args:
        sender: the sender of the email
        first_name:
        content:
        last_name:
        recipient_email:
    Returns:

    """
    subject = f"Hi! {first_name} {last_name} Email Invitation from E-MetricSuite"
    try:
        SendInBlue.send_email(sender=sender, to=recipient_email, subject=subject, html_content=content)
    except MailException as _:
        print(_)
        from account.models import User
        from account.models.email_invitation import EmailInvitation
        print(f"deleting user with email: {recipient_email}")
        EmailInvitation.objects.filter(email=recipient_email).delete()
        User.objects.filter(email=recipient_email).delete()
        print(f"deleted user with email: {recipient_email}")

