from typing import Union, List
from datetime import datetime, date, timedelta
from django.db.models import Q, QuerySet
from django.utils import timezone
from core.utils.exception import CustomValidation

from core.utils.process_durations import (
    get_localized_time,
    monthly_occurrence_date_list,
    process_end_date_time,
    week_difference,
)
from tasks.models.detail import Task
from emetric_calendar.models import Holiday, UserScheduledEventCalendar


def process_start_date_list_for_task(
    upline_initiative,
    routine_option,
    start_date,
    start_time,
    duration,
    repeat_every,
    occurs_days,
    occurs_month_day_number,
    occurs_month_day_position,
    occurs_month_day,
    end_date,
    after_occurrence,
    tenant,
) -> list:
    """Gets start date list for task

    Args:
        upline_initiative ([type]): [description]
        routine_option ([type]): [description]
        start_date ([type]): [description]
        start_time ([type]): [description]
        duration ([type]): [description]
        repeat_every ([type]): [description]
        occurs_days ([type]): [description]
        occurs_month_day_number ([type]): [description]
        occurs_month_day_position ([type]): [description]
        occurs_month_day ([type]): [description]
        end_date ([type]): [description]
        after_occurrencetenant ([type]): [description]

    Returns:
        list: [description]

    Raises
    ------
    CustomValidation
        custom exception
    """
    start_date_list = []
    owner = upline_initiative.owner
    start_date_time = get_localized_time(
        start_date, start_time, tenant.timezone
    )
    end_time = (datetime.combine(date.today(), start_time) + duration).time()

    if start_date_time < timezone.now():
        raise CustomValidation(
            detail="start time cannot be in the past",
            field="start_time",
            status_code=400,
        )

    if not tenant.is_work_day(start_date):
        raise CustomValidation(
            detail="start date is not a work day",
            field="start_date",
            status_code=400,
        )

    # the end-time must be <= parent end_time
    if routine_option == Task.ONCE and upline_initiative.end_date < start_date:
        raise CustomValidation(
            detail="start date can not be greater than upline end date",
            field="start_date",
            status_code=400,
        )

    if upline_initiative.start_date > start_date:
        raise CustomValidation(
            detail="Start date can not be earlier than upline start date",
            field="start_date",
            status_code=400,
        )

    # check if work time
    if start_time < tenant.work_start_time or tenant.work_stop_time < end_time:
        raise CustomValidation(
            detail="selected time is outside work time",
            field="start_time",
            status_code=400,
        )

    if (
        start_time > tenant.work_break_start_time
        and start_time < tenant.work_break_stop_time
    ):
        raise CustomValidation(
            detail="Task cannot overflow to break time",
            field="start_time",
            status_code=400,
        )

    if (
        end_time > tenant.work_break_start_time
        and end_time < tenant.work_break_stop_time
    ):
        raise CustomValidation(
            detail="Task cannot overflow to break time",
            field="duration",
            status_code=400,
        )

    if end_date:
        # the end date must be <= parent end date
        if upline_initiative.end_date < end_date:
            raise CustomValidation(
                detail="start date can not be greater than upline end date",
                field="end_date",
                status_code=400,
            )

    else:
        end_date = upline_initiative.end_date

    holidays = Holiday.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
    )

    user_schedule = get_user_schedule(start_date, end_date, owner, tenant)

    if routine_option == Task.ONCE:
        end_date_time = process_end_date_time(
            start_date, start_time, duration, tenant
        )

        if not is_day_free(holidays, start_date):
            raise CustomValidation(
                detail="Date is a holiday",
                field="start_date",
                status_code=400,
            )

        if not is_user_free(user_schedule, start_date_time, end_date_time):
            raise CustomValidation(
                detail=f"Task owner is not free between {start_date_time} and {end_date_time}",
                field="start_time",
                status_code=400,
            )

        start_date_list.append(start_date)

    elif routine_option == Task.DAILY:
        # extracts all possible dates till end date

        if not after_occurrence:
            after_occurrence = 999999999
        current = start_date
        repeat_every_check = 1

        while current <= end_date:

            if tenant.is_work_day(current):

                if repeat_every_check == 1:
                    repeat_every_check = repeat_every  # resets repeat every

                    current_start_date_time = get_localized_time(
                        current, start_time, tenant.timezone
                    )
                    current_end_date_time = process_end_date_time(
                        current, start_time, duration, tenant
                    )

                    if not is_day_free(holidays, current):
                        current += timedelta(days=1)
                        continue

                    if not is_user_free(
                        user_schedule,
                        current_start_date_time,
                        current_end_date_time,
                    ):
                        raise CustomValidation(
                            detail=f"Task owner is not free between "
                            f"{current_start_date_time} and "
                            f"{current_end_date_time}",
                            field="start_time",
                            status_code=400,
                        )

                    start_date_list.append(current)
                    after_occurrence -= 1

                    if after_occurrence <= 0:
                        break
                else:
                    repeat_every_check -= 1

            current += timedelta(days=1)

    elif routine_option == Task.WEEKLY:

        # cache all user's schedule between start date time and end date time
        end_date_time = process_end_date_time(
            end_date, start_time, duration, tenant
        )

        if not after_occurrence:
            after_occurrence = 999999999
        current = start_date

        while current <= end_date:

            if tenant.is_work_day(current):

                if (
                    week_difference(start_date, current) % repeat_every == 0
                    and current.weekday() in occurs_days
                ):
                    # check that user is free
                    current_start_date_time = get_localized_time(
                        current, start_time, tenant.timezone
                    )
                    current_end_date_time = process_end_date_time(
                        current, start_time, duration, tenant
                    )

                    if not is_day_free(holidays, current):
                        current += timedelta(days=1)
                        continue

                    if not is_user_free(
                        user_schedule,
                        current_start_date_time,
                        current_end_date_time,
                    ):
                        raise CustomValidation(
                            detail=f"Task owner is not free between "
                            f"{current_start_date_time} and "
                            f"{current_end_date_time}",
                            field="start_time",
                            status_code=400,
                        )

                    start_date_list.append(current)
                    after_occurrence -= 1

                    if after_occurrence <= 0:
                        break
            current += timedelta(days=1)

    elif routine_option == Task.MONTHLY:

        if not after_occurrence:
            after_occurrence = 999999999
        repeat_every_check = 1

        if occurs_month_day_number:
            current = start_date

            while current <= end_date:

                if current.day == occurs_month_day_number:

                    if repeat_every_check == 1:
                        repeat_every_check = repeat_every  # restores

                        # checks if the occurred day number falls on a non work day
                        if not tenant.is_work_day(current):
                            current += timedelta(days=1)
                            continue
                            # # while it is not, adds a day till it is
                            # while not tenant.is_work_day(current):
                            #     current += timedelta(days=1)

                        current_start_date_time = get_localized_time(
                            current, start_time, tenant.timezone
                        )
                        current_end_date_time = process_end_date_time(
                            current, start_time, duration, tenant
                        )

                        if not is_day_free(holidays, current):
                            current += timedelta(days=1)
                            continue

                        if not is_user_free(
                            user_schedule,
                            current_start_date_time,
                            current_end_date_time,
                        ):
                            raise CustomValidation(
                                detail=f"Task owner is not free between "
                                f"{current_start_date_time} and "
                                f"{current_end_date_time}",
                                field="start_time",
                                status_code=400,
                            )

                        start_date_list.append(current)
                        after_occurrence -= 1

                        if after_occurrence <= 0:
                            break
                        current += timedelta(days=25)
                    else:
                        repeat_every_check -= 1
                current += timedelta(days=1)

        elif occurs_month_day_position and occurs_month_day:
            possible_date_time = monthly_occurrence_date_list(
                occurs_month_day_position,
                occurs_month_day,
                start_date,
                end_date,
            )

            for date_time in possible_date_time:

                if (
                    date_time.date() >= start_date
                    and date_time.date() <= end_date
                    and repeat_every_check == 1
                ):
                    repeat_every_check = repeat_every

                    # check that user is free
                    current_start_date_time = get_localized_time(
                        date_time.date(), start_time, tenant.timezone
                    )
                    current_end_date_time = process_end_date_time(
                        date_time.date(), start_time, duration, tenant
                    )

                    if not is_day_free(holidays, date_time):
                        continue

                    if not is_user_free(
                        user_schedule,
                        current_start_date_time,
                        current_end_date_time,
                    ):
                        raise CustomValidation(
                            detail=f"Task owner is not free between "
                            f"{current_start_date_time} and "
                            f"{current_end_date_time}",
                            field="start_time",
                            status_code=400,
                        )

                    start_date_list.append(date_time.date())
                    after_occurrence -= 1

                    if after_occurrence <= 0:
                        break

                repeat_every_check -= 1

    # edge case where upline end date is < first possible occurrence
    if len(start_date_list) == 0:
        raise CustomValidation(
            detail=f"Upline end date is before the first possible occurrence",
            field="after_occurrence",
            status_code=400,
        )

    return start_date_list


def is_user_free(user_schedule, start_time, end_time):
    user_scheduled_event = user_schedule.filter(
        (Q(start_time__lte=start_time) & Q(end_time__gte=start_time))
        | (Q(start_time__lte=end_time) & Q(end_time__gte=end_time))
    )
    if user_scheduled_event.exists():
        return False
    else:
        return True


def process_target_point(
    task_type,
    rework_limit,
    turn_around_time_target_point,
    quality_target_point,
    quantity_target_point,
    quantity_target_unit,
):
    if task_type == Task.QUANTITATIVE:
        rework_limit = 0
        quality_target_point = 0

    if task_type == Task.QUALITATIVE:
        quantity_target_point = 0
        quantity_target_unit = 0

    target_point = (
        turn_around_time_target_point
        + quality_target_point
        + quantity_target_point
    )

    return (
        target_point,
        rework_limit,
        quality_target_point,
        quantity_target_point,
        quantity_target_unit,
    )


def is_day_free(holidays: Union[QuerySet, List[Holiday]], date: date):
    """Returns True if the date is not a holiday"""
    if holidays.filter(date=date).exists():
        return False
    return True


def get_user_schedule(start_date: datetime, end_date: datetime, user, tenant):
    """Returns a queryset of user's schedule between start date and end date"""
    return UserScheduledEventCalendar.objects.filter(
        start_time__gte=get_localized_time(
            start_date, datetime.min.time(), tenant.timezone
        ),
        end_time__lte=get_localized_time(
            end_date, datetime.max.time(), tenant.timezone
        ),
        user=user,
        is_free=False,
    )
