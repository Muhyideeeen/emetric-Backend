from e_metric_api.celery import app

from mailing.services.mailing import MailException
from mailing.services.send_in_blue import SendInBlue


@app.task()
def send_password_reset_email(sender: dict, content: str, first_name: str, recipient_email: list):
    """
    A function that sends a password reset email
    Args:
        sender: the sender of the email
        first_name:
        content:
        recipient_email:
    Returns:

    """
    subject = f"Hi! {first_name} Password Reset Email from E-MetricSuite"
    try:
        SendInBlue.send_email(sender=sender, to=recipient_email, subject=subject, html_content=content)
    except MailException as _:
        print(_)
