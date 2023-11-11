from core.utils.exception import CustomValidation
from organization.models import (
    CorporateLevel,
    Department,
    Division,
    Group,
    Unit,
)


def process_structure(level, model):
    if level is not None:
        level_uuid = level.get("uuid")
        try:
            return model.objects.get(uuid=level_uuid)
        except model.DoesNotExist:
            raise CustomValidation(
                detail=f"{level_uuid} is not valid uuid",
                field="level",
                status_code=400,
            )
    return None


# No validation
def process_structure_by_uuid(uuid, model):
    if uuid is not None:
        try:
            return model.objects.get(uuid=uuid)
        except model.DoesNotExist:
            pass
    return None


# No validation
def process_structure_by_name_v2(name, model):
    if name is not None:
        try:
            return model.objects.get(name=name)
        except model.DoesNotExist:
            pass
    return None


def process_levels(validated_data):
    corporate_level = validated_data.pop("corporate_level", None)
    department_level = validated_data.pop("department", None)
    division_level = validated_data.pop("division", None)
    group_level = validated_data.pop("group", None)
    unit_level = validated_data.pop("unit", None)

    corporate_level_obj = (
        process_structure(corporate_level, CorporateLevel)
        if corporate_level
        else None
    )
    department_obj = (
        process_structure(department_level, Department)
        if department_level
        else None
    )
    division_level_obj = (
        process_structure(division_level, Division) if division_level else None
    )
    group_level_obj = (
        process_structure(group_level, Group) if group_level else None
    )
    unit_level_obj = (
        process_structure(unit_level, Unit) if unit_level else None
    )
    return (
        corporate_level_obj,
        department_obj,
        division_level_obj,
        group_level_obj,
        unit_level_obj,
        validated_data,
    )


def process_level_by_uuid(uuid):
    corporate_level_obj = (
        process_structure_by_uuid(uuid, CorporateLevel) if uuid else None
    )
    division_level_obj = (
        process_structure_by_uuid(uuid, Division) if uuid else None
    )
    group_level_obj = process_structure_by_uuid(uuid, Group) if uuid else None
    department_obj = (
        process_structure_by_uuid(uuid, Department) if uuid else None
    )
    unit_level_obj = process_structure_by_uuid(uuid, Unit) if uuid else None
    return (
        corporate_level_obj,
        division_level_obj,
        group_level_obj,
        department_obj,
        unit_level_obj,
    )


def process_level_by_name_to_dict(
    coperate_name="",
    division_name="",
    group_name="",
    department_name="",
    unit_name="",
):
    corporate_level_obj = (
        process_structure_by_name_v2(str(coperate_name).lower().strip(), CorporateLevel)
        if coperate_name
        else None
    )
    division_level_obj = (
        process_structure_by_name_v2(str(division_name).lower().strip(), Division)
        if division_name
        else None
    )
    group_level_obj = (
        process_structure_by_name_v2(str(group_name).lower().strip(), Group)
        if group_name
        else None
    )
    department_obj = (
        process_structure_by_name_v2(str(department_name).lower().strip(), Department)
        if department_name
        else None
    )
    unit_level_obj = (
        process_structure_by_name_v2(str(unit_name).lower().strip(), Unit)
        if unit_name
        else None
    )
    return (
        {"uuid": corporate_level_obj.uuid} if corporate_level_obj else None,
        {"uuid": division_level_obj.uuid} if division_level_obj else None,
        {"uuid": group_level_obj.uuid} if group_level_obj else None,
        {"uuid": department_obj.uuid} if department_obj else None,
        {"uuid": unit_level_obj.uuid} if unit_level_obj else None,
    )
