from __future__ import print_function
import sib_api_v3_sdk
from django.conf import settings
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

from mailing.services.mailing import Mailing, MailException


class SendInBlue(Mailing):
    apiKey = settings.SENDINBLUE_API_KEY
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = apiKey

    @classmethod
    def send_email(cls, sender, to, subject, html_content, reply_to=None):
        """
        This function takes the details of the email to be sent,
        and sends it using the sendinblue API.
        """
        if reply_to is not None:
            reply_to = reply_to

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(cls.configuration)
        )
        # SendSmtpEmail | Values to send a transactional email
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sender,
            to=to,
            reply_to=reply_to,
            subject=subject,
            html_content=html_content,
        )

        try:
            # Send a transactional email
            api_response = api_instance.send_transac_email(send_smtp_email)
            pprint(api_response)
        except ApiException as e:
            raise MailException(
                "Exception when calling SMTPApi->send_transac_email: %s\n" % e
            )
