import uuid
from typing import Dict

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from account.models.roles import Role


class UserManager(BaseUserManager):
    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        password: str = None,
        **extra_fields: Dict
    ) -> "User":
        from core.utils import CustomValidation

        if not email:
            raise CustomValidation(
                detail="User must an email address",
                field="email",
                status_code=400,
            )
        user_roles_extra_fields = extra_fields.get("user_role", None)
        is_invited = extra_fields.get("is_invited", False)
        super_user = extra_fields.get("is_superuser", False)
        is_active = extra_fields.get("is_active", False)
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_superuser=super_user,
            is_active=is_active,
            is_invited=is_invited,
        )

        if password:
            user.set_password(password)
        if user_roles_extra_fields is not None:
            role = Role.objects.get(role=user_roles_extra_fields)
            user.user_role = role
        user.save(using=self._db)

        return user

    def create_staff(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        password: str,
    ):
        staff_user = {"is_superuser": False, "user_role": Role.ADMIN}
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password,
            **staff_user
        )
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_admin(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        password: str,
        is_invited: bool = False,
    ):
        super_user = {
            "is_superuser": True,
            "user_role": Role.ADMIN_HR,
            "is_invited": is_invited,
        }

        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password,
            **super_user
        )

        user.is_staff = True
        user.is_registration_mail_sent = True
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        password: str,
        is_invited: bool = False,
        is_creating_superuser_for_tenant: bool = False,
    ):
        super_user = {
            "is_superuser": True,
            "user_role": Role.SUPER_ADMIN,
            "is_invited": is_invited,
        }
        temp_password = password
        if is_creating_superuser_for_tenant:
            password = None
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password,
            **super_user
        )

        user.is_staff = True
        user.is_registration_mail_sent = True
        user.is_active = True
        if is_creating_superuser_for_tenant:
            password = temp_password
            user.password = password
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    first_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    last_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    phone_number = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    user_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    user_role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, blank=True, null=True
    )
    is_active = models.BooleanField(default=False, db_index=True)
    is_invited = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_registration_mail_sent = models.BooleanField(
        default=False, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]

    objects = UserManager()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.email
