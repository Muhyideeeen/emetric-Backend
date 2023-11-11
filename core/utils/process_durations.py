from datetime import datetime, timedelta, date, time, timezone
from dateutil.rrule import *
from django.utils import timezone

from core.utils.exception import CustomValidation


DAILY = "daily"
WEEKLY = "weekly"
FORTNIGHTLY = "fortnightly"
MONTHLY = "monthly"
QUARTERLY = "quarterly"
HALF_YEARLY = "half_yearly"
YEARLY = "yearly"
ONCE = "once"

MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

FIRST = "first"
SECOND = "second"
THIRD = "third"
FOURTH = "fourth"
LAST = "last"


def process_end_date(start_date, routine_option, end_date=None) -> date:
    """Uses start date and routine option selected to generate
    end date

    Args:
        date ([type]): [description]
        routine_option ([type]): [description]

    Returns:
        date: calculated end date
    """

    if routine_option == DAILY:
        end_date = start_date + timedelta(days=0)

    elif routine_option == WEEKLY:
        end_date = start_date + timedelta(days=6)

    elif routine_option == FORTNIGHTLY:
        end_date = start_date + timedelta(days=13)

    elif routine_option == MONTHLY:
        end_date = start_date + timedelta(days=29)

    elif routine_option == QUARTERLY:
        end_date = start_date + timedelta(days=90)

    elif routine_option == HALF_YEARLY:
        end_date = start_date + timedelta(days=181)

    elif routine_option == YEARLY:
        end_date = start_date + timedelta(days=364)

    return end_date


def process_end_date_time(
    start_date, start_time, duration, tenant
) -> datetime:
    """Uses start date start time and duration to get the localized
    end date time

    Args:
        start_date ([type]): [description]
        start_time ([type]): [description]
        duration ([type]): [description]
        tenant ([type]): [description]

    Returns:
        datetime: [description]
    """
    end_time = (datetime.combine(date.today(), start_time) + duration).time()

    return get_localized_time(start_date, end_time, tenant.timezone)


def week_difference(date_earlier: date, date_later: date) -> int:
    """Returns the week difference between two dates and takes into
    consideration different years

    Args:
        date_earlier (date): [description]
        date_later (date): [description]

    Returns:
        int: [description]
    """
    diff = date_later.isocalendar().week - date_earlier.isocalendar().week

    if diff < 0:  # extending to another year
        diff = (
            52
            - date_earlier.isocalendar().week
            + date_later.isocalendar().week
        )

    return diff


def monthly_occurrence_date_list(
    occurs_month_day_position, occurs_month_day, start_date, end_date
):
    """returns a date time list of possible dates of occurrence between
    start date and end date based on given occurs_month_day_position and
    occurs_month_day"""

    position = 1  # default
    if occurs_month_day_position == FIRST:
        position = 1
    elif occurs_month_day_position == SECOND:
        position = 2
    elif occurs_month_day_position == THIRD:
        position = 3
    elif occurs_month_day_position == FOURTH:
        position = 4
    elif occurs_month_day_position == LAST:
        position = -1

    day_code = MO  # default
    if occurs_month_day == MONDAY:
        day_code = MO
    elif occurs_month_day == TUESDAY:
        day_code = TU
    elif occurs_month_day == WEDNESDAY:
        day_code = WE
    elif occurs_month_day == THURSDAY:
        day_code = TH
    elif occurs_month_day == FRIDAY:
        day_code = FR
    elif occurs_month_day == SATURDAY:
        day_code = SA
    elif occurs_month_day == SUNDAY:
        day_code = SU

    month_diff = end_date.month - start_date.month + 1
    return list(
        rrule(
            1,  # MONTHLY
            count=month_diff,
            byweekday=day_code(position),
            dtstart=start_date,
        )
    )


def process_start_date_list(
    routine_option, start_date, end_date, after_occurrence, upline_obj=None
) -> list:
    """Gets start date list for objectives and initiatives

    Args:
        routine_option ([type]): [description]
        start_date ([type]): [description]
        after_occurrence ([type]): [description]
        upline_obj ([type], optional): [description]. Defaults to None.

    Returns:
        list: [description]

    Raises
    ------
    CustomValidation
        custom exception
    """
    start_date_list = []

    if start_date < timezone.now().date():
        raise CustomValidation(
            detail="start date cannot be in the past",
            field="start_date",
            status_code=400,
        )

    parent_end_date = None
    if upline_obj:
        reference_order = (
            ONCE,
            DAILY,
            WEEKLY,
            FORTNIGHTLY,
            MONTHLY,
            QUARTERLY,
            HALF_YEARLY,
            YEARLY,
        )
        parent_routine_option = upline_obj.routine_option
        parent_start_date = upline_obj.start_date
        parent_end_date = upline_obj.end_date

        if reference_order.index(
            parent_routine_option
        ) < reference_order.index(routine_option):
            raise CustomValidation(
                detail="selected routine option mismatch with upline",
                field="routine_option",
                status_code=400,
            )

        if parent_start_date > start_date:
            raise CustomValidation(
                detail="Start date can not be earlier than upline start date",
                field="start_date",
                status_code=400,
            )

        # the end-date must be <= parent end_date
        if end_date:
            if parent_end_date < end_date:
                raise CustomValidation(
                    detail="End date can not be greater than upline end date",
                    field="end_date",
                    status_code=400,
                )

    if routine_option == ONCE:

        if start_date >= end_date:
            raise CustomValidation(
                detail="Start date cannot be greater than or equal to end date",
                field="start_date",
                status_code=400,
            )

        start_date_list.append(start_date)

    else:

        current_start_date = start_date
        current_end_date = process_end_date(current_start_date, routine_option)

        if end_date != None:

            while (
                current_start_date < end_date and current_end_date <= end_date
            ):
                start_date_list.append(current_start_date)

                current_start_date = current_end_date + timedelta(days=1)
                current_end_date = process_end_date(
                    current_start_date, routine_option
                )

        else:

            while after_occurrence > 0:
                # checks if upline end date is before current end date
                if parent_end_date:
                    if parent_end_date < current_end_date:
                        raise CustomValidation(
                            detail="Possible end date can not be greater than upline end date",
                            field="after_occurrence",
                            status_code=400,
                        )

                start_date_list.append(current_start_date)
                current_start_date = current_end_date + timedelta(days=1)
                current_end_date = process_end_date(
                    current_start_date, routine_option
                )
                after_occurrence -= 1

    # edge case where upline end date is < first possible occurrance
    if len(start_date_list) == 0:
        raise CustomValidation(
            detail="End date is before the first possible occurrence",
            field="after_occurrence",
            status_code=400,
        )

    return start_date_list


def try_parsing_date(text) -> date:
    """
    Returns the date if it matches the available formats
    """
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(text).split(" ")[0], fmt).date()
        except ValueError:
            pass

    raise CustomValidation(
        detail="Invalid date format",
        field="date",
        status_code=400,
    )


def get_localized_time(date: date, time: time, timezone: timezone) -> datetime:
    """Returns a localized date time"""
    return timezone.localize(datetime.combine(date, time))
