from django.contrib.auth import get_user_model, authenticate, user_logged_in
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import IntegrityError
from django.utils.encoding import force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from account.models import EmailInvitation, Role
from core.utils import CustomValidation, get_client_ip, gen_token, update_login
from core.utils.check_org_name_and_set_schema import (
    check_organization_name_and_set_appropriate_schema,
)
from tracking.models import PasswordResetTracking, PasswordUpdateTracking

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, min_length=8, max_length=60, write_only=True
    )

    class Meta:
        model = User
        fields = (
            "user_id",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "email",
        )
        extra_kwargs = {
            "user_id": {"read_only": True},
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")
        phone_number = attrs.get("phone_number")

        try:
            return User.objects.create_user(
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                user_role=Role.ADMIN,
            )
        except IntegrityError as _:
            message = "value already exist"
            key = "default"
            if "email" in _.__str__():
                message = "email already exists"
                key = "email"
            if "phone_number" in _.__str__():
                message = "phone_number already exists"
                key = "phone_number"

            raise serializers.ValidationError({key: message})


class RegisterAdminSerializer(serializers.ModelSerializer):
    organisation_short_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, min_length=8, max_length=60, write_only=True
    )

    class Meta:
        model = User
        fields = (
            "organisation_short_name",
            "user_id",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "email",
        )
        extra_kwargs = {
            "user_id": {"read_only": True},
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        organisation_short_name = attrs.get("organisation_short_name")
        email = attrs.get("email")
        password = attrs.get("password")
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")
        phone_number = attrs.get("phone_number")
        user_email = self.context["request"]._request.user.email

        try:
            user = User.objects.create_user(
                password=password,
                # the reason for this is to avoid duplication of hr admin in different organisation
                email=email+f'.emetricshort.{organisation_short_name}',
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                user_role=Role.ADMIN_HR,
            )

            check_organization_name_and_set_appropriate_schema(
                organisation_short_name, user_email
            )
            User.objects.create_admin(
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
            )
        except IntegrityError as _:
            message = "value already exist"
            key = "default"
            if "email" in _.__str__():
                message = "email already exists"
                key = "email"
            if "phone_number" in _.__str__():
                message = "phone_number already exists"
                key = "phone_number"
            raise serializers.ValidationError({key: message})

        return user


class LoginSerializer(TokenObtainPairSerializer):
    """
    Serializer for user authentication object
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):

        email = attrs.get("email", None)
        password = attrs.get("password", None)
        request = self.context.get("request", None)
        user = None
        user_email_invitation = None
        try:
            user = User.objects.select_related("user_role").get(email=email)
            user_email_invitation = EmailInvitation.objects.get(user=user)
        except User.DoesNotExist:
            user = None
        except EmailInvitation.DoesNotExist:
            user_email_invitation = None

        auth_user = authenticate(email=email, password=password)

        if (not user and not auth_user) or (user.is_active and not auth_user):
            raise AuthenticationFailed(
                "Invalid credentials, username or password incorrect"
            )

        if (
            user
            and user_email_invitation
            and not user.is_active
            and not auth_user
            and not user_email_invitation.activated
        ):
            raise AuthenticationFailed("Kindly verify your account")

        refresh = self.get_token(user)
        user_login = update_login(refresh)
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        return user_login

    @classmethod
    def get_token(cls, user: User):
        """
        get the token for a user
        Args:
            user:
        Returns:
        """
        token = gen_token(user)

        return token


class EmailValidateSerializer(serializers.Serializer):
    key = serializers.CharField(min_length=10)


class EmailInviteValidateSerializer(serializers.Serializer):
    key = serializers.CharField(min_length=10)
    password = serializers.CharField(
        required=True, min_length=8, max_length=60, write_only=True
    )


class CustomTokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        refresh = attrs.get("refresh_token")
        if refresh is None:
            raise AuthenticationFailed(
                "Authentication Credentials were not provided"
            )
        try:
            refresh = RefreshToken(refresh)
        except TokenError as e:
            raise AuthenticationFailed(str(e))

        data = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()

            data["refresh"] = str(refresh)

        return data


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh_token")
        if refresh_token is None:
            raise AuthenticationFailed(
                "Authentication Credentials were not provided"
            )

        try:
            token = RefreshToken(refresh_token)
        except TokenError as e:
            raise AuthenticationFailed(str(e))
        token.blacklist()
        return token


class RequestPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ["email"]


class SetNewPasswordFromResetPasswordEmailSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True
    )
    uid_base64 = serializers.CharField(min_length=1, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ["password", "uid_base64", "token"]

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            uid_base64 = attrs.get("uid_base64")
            token = attrs.get("token")

            user_id_decoded = force_str(
                urlsafe_base64_decode(uid_base64).decode()
            )
            user = User.objects.get(user_id=user_id_decoded)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise CustomValidation(
                    detail="token is not valid, please request a new one",
                    field="token",
                    status_code=401,
                )
            user.set_password(password)
            user.save()
            password_reset_tracking = PasswordResetTracking.objects.filter(
                user=user, is_password_changed=False
            ).first()
            password_reset_tracking.is_password_changed = True
            password_reset_tracking.save()
            return user
        except DjangoUnicodeDecodeError as _:
            raise CustomValidation(
                detail="uid_base64 is not valid or tampered with, please request a new one",
                field="uid_base64",
                status_code=401,
            )


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("old_password", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields does not match."}
            )

        return attrs

    def validate_old_password(self, value):
        user = self.context.get("request").user
        if not user.check_password(value):
            raise serializers.ValidationError(
                {"old_password": "Old password is not correct"}
            )
        return value

    def update(self, instance, validated_data):

        request = self.context.get("request")
        user = request.user

        if user.user_id != instance.user_id:
            raise serializers.ValidationError(
                {"authorize": "You dont have permission for this user."}
            )

        instance.set_password(validated_data["password"])
        instance.save()

        PasswordUpdateTracking.objects.create(
            user=user,
            email=user.email,
            device=request.user_agent.device.family,
            os=request.user_agent.os.family,
            os_version=request.user_agent.os.version_string,
            browser=request.user_agent.browser.family,
            browser_version=request.user_agent.browser.version_string,
            ip_address=get_client_ip(request),
            is_password_updated=True,
        )

        return instance
