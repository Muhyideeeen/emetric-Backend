from account.models import Role
from core.utils.exception import CustomValidation
from organization.models import CorporateLevel


def employee_data_validation(
    current_level, user_role, designation, instance=None
):

    # checks if level does not have a team lead and team lead role is not selected
    if current_level.team_lead == None and user_role != Role.TEAM_LEAD:
        raise CustomValidation(
            detail="Kindly assign a team lead to selected level",
            field="role",
            status_code=400,
        )

    # checks if level does not have a team lead and team lead role is selected but
    # parent level has no team lead
    if (
        current_level.team_lead == None
        and user_role == Role.TEAM_LEAD
        and not isinstance(current_level, CorporateLevel)
    ):
        if current_level.parent_name().team_lead == None:
            raise CustomValidation(
                detail="Kindly assign a team lead to parent level",
                field="role",
                status_code=400,
            )

    # checks if user is level team lead and team lead role is not selected

    if instance:

        if (
            current_level.team_lead == instance.user
            and user_role != Role.TEAM_LEAD
        ):
            raise CustomValidation(
                detail="Kindly assign  a new team lead to selected level",
                field="role",
                status_code=400,
            )
    # checks if designation is available for selected level
    if not current_level.designation_set.filter(
        name=designation.lower()
    ).exists():
        raise CustomValidation(
            detail="invalid designation for selected level",
            field="designation",
            status_code=400,
        )


def get_upline_user(user_role, current_level, corporate_level_obj):
    """assign team lead as upline user except for corporate level"""
    if user_role != Role.TEAM_LEAD:
        return current_level.team_lead

    elif current_level != corporate_level_obj:
        return current_level.parent_name().team_lead

    else:
        return None
