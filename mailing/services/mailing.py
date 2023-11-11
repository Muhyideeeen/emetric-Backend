"""
Mailing base module
"""
from abc import ABCMeta, abstractmethod

from requests import Response


class MailException(Exception):
    """
    Mail Exception class
    """

    def __init__(self, message: str):
        super(MailException, self).__init__(message)


class Mailing(metaclass=ABCMeta):
    """
    Generic Mailing class
    """

    @classmethod
    @abstractmethod
    def send_email(cls, *args, **kwargs) -> Response:
        """
        Send Email using a given mailing service
        :return:
        """

    pass
