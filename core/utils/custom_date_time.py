"""
Date time utility
"""
import datetime
from typing import Dict

import pytz
from dateutil.parser import parse


def tzware_datetime():
    """
    Return a timezone aware datetime.
    :return: Datetime
    """
    return datetime.datetime.now(pytz.utc)


def convert_to_another_timezone(
    date_time_object: Dict[str, str], timezone_to_convert_to: str = "UTC"
):
    date_string = date_time_object.get("time_to_convert", None)
    user_timezone = date_time_object.get("TIME_ZONE", None)
    if date_string is None or user_timezone is None:
        raise KeyError(
            "time_to_convert or TIME_ZONE must be present in the date_time_object dictionary"
        )

    user_pytz_timezone = pytz.timezone(user_timezone)
    pytz_time_zone_to_convert_to = pytz.timezone(timezone_to_convert_to)
    date_format_representation = "%Y-%m-%dT%H:%M:%S.%f%z"
    timestamp_representation = datetime.datetime.strptime(
        str(date_string), date_format_representation
    )

    if timestamp_representation.tzinfo is None:
        localized_user_timestamp = user_pytz_timezone.localize(
            timestamp_representation
        )
    else:
        localized_user_timestamp = timestamp_representation
    return localized_user_timestamp.astimezone(pytz_time_zone_to_convert_to)


def is_valid_date(date):
    if date:
        try:
            datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")
            return True
        except ValueError:
            return False
    return False
