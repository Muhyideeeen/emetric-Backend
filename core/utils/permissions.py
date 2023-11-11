from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions
from rest_framework.permissions import BasePermission

from account.models import Role
from core.utils.response_data import response_data
from employee.models import Employee


class BasePermissionMixin(BasePermission):
    """
    Base permission blueprints for users
    """

    message = response_data(
        401, "You do not have permission to perform this " "action"
    )

    def has_permission(self, request, view):
        """
        permissions method to be implemented
        :param request:
        :param view:
        :return:
        """
        pass


class AnonPermissionOnly(BasePermissionMixin):
    """
    Non authenticated users only
    """

    def has_permission(self, request, view):
        """
        check if the user is not authenticated and give permissions to them
        :param request:
        :param view:
        :return:
        """
        return not request.user.is_authenticated


class IsSuperAdminUserOnly(BasePermissionMixin):
    """
    Allows access only to super admin users.
    """

    def has_permission(self, request, view):
        """
        super admin permission
        :param request:
        :param view:
        :return:
        """

        if not isinstance(request.user, AnonymousUser):
            return request.user.is_superuser and request.user.is_staff
        return False


class IsAdminUserOnly(BasePermissionMixin):
    """
    Allows access only to Admin users.
    """

    def has_permission(self, request, view):
        """
        super admin permission
        :param request:
        :param view:
        :return:
        """
        if not isinstance(request.user, AnonymousUser):
            return request.user.user_role.role == Role.ADMIN
        return False


class IsSuperAdminUserOrAdminUser(BasePermissionMixin):
    """
    Allows access only to super admin users or admin Users.
    """

    def has_permission(self, request, view):
        """
        super admin permission
        :param request:
        :param view:
        :return:
        """
        if not isinstance(request.user, AnonymousUser):
            if (
                request.user
                and request.user.is_superuser
                and request.user.is_staff
            ):
                return True
            else:
                return bool(
                    request.user
                    and request.user.user_role.role == Role.ADMIN
                    and request.user.is_staff
                )
        return False


class IsEmployeeOnly(BasePermissionMixin):
    """
    Allows access only to an employee.
    """

    def has_permission(self, request, view):
        """
        Staff user permission
        :param request:
        :param view:
        :return:
        """
        if not isinstance(request.user, AnonymousUser):
            return request.user.user_role.role == Role.EMPLOYEE
        return False


class IsTeamLeadOnly(BasePermissionMixin):
    """
    Allows access only to team lead.
    """

    def has_permission(self, request, view):
        """
        Staff user permission
        :param request:
        :param view:
        :return:
        """
        if not isinstance(request.user, AnonymousUser):
            return request.user.user_role.role == Role.TEAM_LEAD
        return False


# class IsDepartmentalLeadOnly(BasePermissionMixin):
#     """
#     Allows access only to departmental lead.
#     """

#     def has_permission(self, request, view):
#         """
#         Staff user permission
#         :param request:
#         :param view:
#         :return:
#         """
#         if not isinstance(request.user, AnonymousUser):
#             return request.user.user_role.role == Role.TEAM_LEAD
#         return False


class IsOwnerOrReadOnly(BasePermissionMixin):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        """Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.user == request.user


class IsOrganisationOwnerOrReadOnly(BasePermissionMixin):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        """
        Staff user permission
        :param request:
        :param view:
        :return:
        """
        if not isinstance(request.user, AnonymousUser):
            return request.user.user_role.role == Role.ADMIN
        return False

    def has_object_permission(self, request, view, obj):
        """Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        """

        # Instance must have an attribute named `owner`.
        return obj.owner_email == request.user.email


class IsAdminOrSuperAdminOrReadOnly(BasePermissionMixin):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        """
        Staff user permission
        :param request:
        :param view:
        :return:
        """
        return not isinstance(request.user, AnonymousUser)

    def has_object_permission(self, request, view, obj):
        """Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return (
            request.user.user_role.role == Role.ADMIN
            or request.user.user_role.role == Role.SUPER_ADMIN
        )


class IsAdminOrHRAdminOrReadOnly(BasePermissionMixin):
    """
    Object-level permission to only SuperAdmin, Admin, HRAdmin to edit it.
    """

    def has_permission(self, request, view):
        """
        Staff user permission
        :param request:
        :param view:
        :return:
        """
        if (
            request.user.is_authenticated
            and request.method in permissions.SAFE_METHODS
        ):
            return True
        return request.user.is_authenticated and (
            request.user.user_role.role == Role.ADMIN
            or request.user.user_role.role == Role.ADMIN_HR
            or request.user.user_role.role == Role.SUPER_ADMIN
        )

    def has_object_permission(self, request, view, obj):
        """Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        """
        if (
            request.user.is_authenticated
            and request.method in permissions.SAFE_METHODS
        ):
            return True
        return request.user.is_authenticated and (
            request.user.user_role.role == Role.ADMIN
            or request.user.user_role.role == Role.ADMIN_HR
            or request.user.user_role.role == Role.SUPER_ADMIN
        )

class IsAdminOrHRAdminOrEmployeeOrReadOnly(IsAdminOrHRAdminOrReadOnly):
    """
    Object-level permission to only SuperAdmin, Admin, HRAdmin or employee to edit it.
    """
    def has_permission(self, request, view):
        """
        Staff user permission
        :param request:
        :param view:
        :return:
        """
        if request.user.is_authenticated:
            return True
    
    def has_object_permission(self, request, view, obj):
        """Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        """
        if (
            request.user.is_authenticated
            and request.method in permissions.SAFE_METHODS
        ):
            return True
        print(request.user == obj.user)
        return request.user.is_authenticated and (
            request.user.user_role.role == Role.ADMIN
            or request.user.user_role.role == Role.ADMIN_HR
            or request.user.user_role.role == Role.SUPER_ADMIN
            or request.user == obj.user
        )
        

class IsTeamLeadOrAdminOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow assignor and admin of an
    object to edit it.
    Assumes the model instance has an `assignor` attribute.
    """

    def has_permission(self, request, view):
        """
        logged in user permission
        :param request:
        :param view:
        :return:
        """

        return not isinstance(request.user, AnonymousUser)

    def has_object_permission(self, request, view, obj):

        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of a post
        return (
            request.user.user_role.role == Role.TEAM_LEAD
            or request.user.user_role.role == Role.ADMIN
            or request.user.user_role.role == Role.SUPER_ADMIN
            or request.user.user_role.role == Role.ADMIN_HR
        )


class IsAssignorOrAdminOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow assignor and admin of an
    object to edit it.
    Assumes the model instance has an `assignor` attribute.
    """

    def has_permission(self, request, view):
        """
        logged in user permission
        :param request:
        :param view:
        :return:
        """

        return not isinstance(request.user, AnonymousUser)

    def has_object_permission(self, request, view, obj):

        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of a post
        return (
            obj.assignor == request.user
            or request.user.user_role.role == Role.ADMIN
            or request.user.user_role.role == Role.SUPER_ADMIN
        )


class IsTaskAssignorOrAdminOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow assignor and admin of an
    object to edit it.
    Assumes the model instance has an `assignor` attribute.
    """

    def has_permission(self, request, view):
        """
        logged in user permission
        :param request:
        :param view:
        :return:
        """

        return not isinstance(request.user, AnonymousUser)

    def has_object_permission(self, request, view, obj):

        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.upline_initiative.assignor == None:
            user_employee_queryset = Employee.objects.filter(user=request.user)
            if user_employee_queryset.exists():
                # allows corporate team lead
                if (
                    request.user.user_role.role == Role.TEAM_LEAD
                    and user_employee_queryset.first().corporate_level != None
                ):
                    return True

        # Write permissions are only allowed to the author of a post
        return (
            obj.upline_initiative.assignor == request.user
            or request.user.user_role.role == Role.ADMIN
            or request.user.user_role.role == Role.SUPER_ADMIN
            or request.user.user_role.role == Role.ADMIN_HR
        )


def has_access_to_user(user, request):
    """Returns true if request user is admin or user or user upline"""
    # allows super admin and admin to access
    if (
        request.user.user_role.role == Role.ADMIN
        or request.user.user_role.role == Role.SUPER_ADMIN
    ):
        return True
    # allows request user to access
    elif request.user == user:
        return True

    else:
        # allows only user upline to access
        upline = Employee.objects.get(
            user=user
        ).employee_employmentinformation.upline
        while upline != None:
            if upline == request.user:
                return True
            upline = Employee.objects.get(
                user=upline
            ).employee_employmentinformation.upline
        return False


def has_access_to_team(team, request):
    """Returns true if request user is admin or team lead or team lead upline"""
    # allows super admin and admin to access
    if (
        request.user.user_role.role == Role.ADMIN
        or request.user.user_role.role == Role.SUPER_ADMIN
    ):
        return True

    else:
        # allows team lead and upline to access
        upline = team.team_lead
        while upline != None:
            if upline == request.user:
                return True
            upline = Employee.objects.get(
                user=upline
            ).employee_employmentinformation.upline
        return False

def is_same_team(emp1,emp2):
    'this checks if two employeess are in the same team'
    emp1_level_id = emp1.corporate_level or emp1.unit or emp1.department or emp1.group or emp1.division or None
    emp2_level_id =  emp2.corporate_level or emp2.unit or emp2.department or emp2.group or emp2.division or None
    print({
        'emp1_level_id':emp1_level_id,
        'emp2_level_id':emp2_level_id,
    })
    if emp1_level_id is None: return False
    if emp2_level_id is None: return False

    return emp2_level_id.uuid == emp1_level_id.uuid

def has_access_to_initiative_report(request, owner):
    """
    Returns true if request user is admin or initiative owner or initiative
    owner's team lead upline
    """
    if (
        request.user.user_role.role == Role.ADMIN
        or request.user.user_role.role == Role.SUPER_ADMIN
    ):
        return True

    elif request.user == owner:
        return True

    else:
        # allows only user upline to access
        upline = Employee.objects.get(
            user=owner
        ).employee_employmentinformation.upline
        while upline != None:
            if upline == request.user:
                return True
            upline = Employee.objects.get(
                user=upline
            ).employee_employmentinformation.upline
        return False


def has_access_to_objective_report(request):
    """Returns true if request user is admin or team lead of corporate"""
    if (
        request.user.user_role.role == Role.ADMIN
        or request.user.user_role.role == Role.SUPER_ADMIN
    ):
        return True

    else:
        user_employee = Employee.objects.get(user=request.user)
        # allows corporate team lead
        if (
            request.user.user_role.role == Role.TEAM_LEAD
            and user_employee.corporate_level != None
        ):
            return True
        return False


def has_access_to_create_task(request_user, employee: Employee):
    """Returns true if request user is admin or team lead of corporate"""
    if (
        request_user.user_role.role == Role.ADMIN
        or request_user.user_role.role == Role.SUPER_ADMIN
    ):
        return True

    # allows employee's upline to create task for employee
    elif (
        request_user.user_role.role
        == employee.employee_employmentinformation.upline
    ):
        return True
    # allows corporate team lead to create task for self
    elif (
        request_user.user_role.role == Role.TEAM_LEAD
        and employee.corporate_level != None
        and employee == request_user
    ):
        return True

    return False
