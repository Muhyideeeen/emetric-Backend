from core.utils.exception import CustomValidation


DAILY = "daily"
WEEKLY = "weekly"
MONTHLY = "monthly"
QUARTERLY = "quarterly"
HALF_YEARLY = "half_yearly"
YEARLY = "yearly"
ONCE = "once"


def check_excess_data_count(
    inputs: list, expected_none_count: int, field: str = "fields"
) -> None:
    """Checks if the count of None in inputs is expected count"""
    if inputs.count(None) != expected_none_count:
        raise CustomValidation(
            detail=f"Missing or excess {field}, kindly provide required {field} only",
            field=field,
            status_code=400,
        )
