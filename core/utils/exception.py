from django.http import Http404
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken

from core.utils.response_data import response_data


def custom_exception_handler(exc, context):
    """
    Custom error overriding
    :param exc:
    :param context:
    :return:
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    # print(response)
    #
    # # TODO: clean up
    # print("Response: ", exc.__class__)
    # print("Context: ", context)
    #
    # Now override the error message.

    print("Hmm", type(exc))
    if response is not None and isinstance(exc, Http404):
        # set the custom message data on response object
        # exc.args[0] will have the message text,
        del response.data["detail"]
        response.data["message"] = "data not found"
        response.data["status"] = status.HTTP_404_NOT_FOUND
        response.data["errors"] = []

    # if isinstance(exc, ValueError):
    #     print(response)
    #     # set the custom message data on response object
    #     # exc.args[0] will have the message text,
    #     CustomValidation('', )

    # validation error
    if isinstance(exc, ValidationError):
        customized_response = {"errors": []}

        for key, value in response.data.items():
            if key == "user":
                if isinstance(value, dict):
                    for keyInner, valueInner in value.items():
                        if isinstance(valueInner, list):
                            error = {
                                "field": keyInner,
                                "message": valueInner[0],
                            }
                        else:
                            error = {"field": keyInner, "message": valueInner}
                        # error = {'field': keyInner, 'message': valueInner[0]}
                        customized_response["errors"].append(error)
                else:
                    error = {"field": key, "message": value[0]}
                    customized_response["errors"].append(error)
            else:
                if isinstance(value, list):
                    error = {"field": key, "message": value}
                else:
                    error = {"field": key, "message": value}
                customized_response["errors"].append(error)
        customized_response["message"] = "Request Validation Error"
        customized_response["status"] = status.HTTP_400_BAD_REQUEST
        response.data = customized_response

    # token invalid error
    if isinstance(exc, InvalidToken):
        del response.data["detail"]
        del response.data["code"]
        if response.data.get("messages", None) is None:
            response.data["message"] = "Token is invalid or expired"
        response.data["status"] = status.HTTP_401_UNAUTHORIZED
        response.data["errors"] = []

    if isinstance(exc, NotAuthenticated):
        del response.data["detail"]
        code = response.data.get("code", None)
        if code:
            del response.data["code"]
        response.data[
            "message"
        ] = "Authentication credentials were not provided."
        response.data["status"] = status.HTTP_401_UNAUTHORIZED
        response.data["errors"] = []

    if isinstance(exc, PermissionDenied):
        code = response.data.get("code", None)
        detail = response.data.get("detail", None)
        if code:
            del response.data["code"]
        if detail is not None:
            response.data["message"] = detail
            del response.data["detail"]
        else:
            response.data[
                "message"
            ] = "Permission denied to access this resource"
        response.data["status"] = status.HTTP_403_FORBIDDEN
        response.data["errors"] = []

    return response


class CustomValidation(APIException):
    """
    custom error validation
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "A server error occurred."

    def __init__(self, detail, field, status_code):
        self.status_code = (
            status_code
            if status_code
            else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        if detail is not None:
            self.detail = response_data(
                self.status_code,
                "validation error",
                {field: force_text(detail)},
            )
        else:
            self.detail = response_data(
                self.status_code, force_text(self.default_detail), {}
            )

    def extract_key_message(self):
        """Returns the key and message for the first error"""
        error_dict = self.detail["error"]
        key = list(error_dict.keys())[0]
        message = error_dict[key]
        return key, message


class CustomServerError(APIException):
    """
    custom server error
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "A server error occurred."

    def __init__(self, detail, status_code=None):
        self.status_code = (
            status_code
            if status_code
            else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        if detail is not None:
            self.detail = response_data(
                self.status_code, force_text(detail), {}
            )
        else:
            self.detail = response_data(
                self.status_code, force_text(self.default_detail), {}
            )


class ExportError(APIException):
    status_code = 400
    default_detail = _("Export error")
    default_code = "export_error"


class ImportError(APIException):
    status_code = 500
    default_detail = _("Import error")
    default_code = "import_error"
