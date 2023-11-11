import datetime
from operator import imod

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.utils.encoding import (
    force_bytes,
    smart_str,
    DjangoUnicodeDecodeError,
)
from django.db import connection
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status, generics
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
)
from rest_framework.exceptions import PermissionDenied
from account.models import EmailInvitation
from account.serializers import (
    RegisterSerializer,
    RegisterAdminSerializer,
    EmailValidateSerializer,
    EmailInviteValidateSerializer,
    CustomTokenRefreshSerializer,
    LogoutSerializer,
    RequestPasswordResetEmailSerializer,
    SetNewPasswordFromResetPasswordEmailSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    HrAdminSerializerCleaner
)
from core.utils import response_data, get_client_ip, tzware_datetime
from core.utils.check_org_name_and_set_schema import check_organization_name_and_set_appropriate_schema
from mailing.tasks.send_forgot_password_email_task import (
    send_password_reset_email,
)
from tracking.models import PasswordResetTracking
from account.models.roles import Role
from core.utils.exception import CustomValidation
User = get_user_model()


class RegisterView(GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(201, "Account Create Successful", [])
        return Response(data, status=status.HTTP_201_CREATED)


class RegisterAdminView(generics.ListAPIView,generics.CreateAPIView,generics.UpdateAPIView,):
    serializer_class = RegisterAdminSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(
            201, "Account for Admin HR created Successfully", []
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        email = request.data.get('email',None)
        organisation_short_name= request.query_params.get('organisation_short_name',None)
        
        if organisation_short_name is None:
            raise CustomValidation(
                 detail="Organisation short name cannot be null.",
                field="organisation_short_name",
                status_code=404,
            )

        if( email is None):CustomValidation(
                detail="email is required.",
                field="email",
                status_code=400,
            )
        if not User.objects.filter(email=email).exists(): raise CustomValidation(detail='Hr Admin does not exits',field='user_id',status_code=400)
        hr_admin = User.objects.get(email=email)
        serializer = HrAdminSerializerCleaner(data=request.data ,instance=hr_admin,
        context={'request':request,'organisation_short_name':organisation_short_name,'instance_email':email})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        updated_data = User.objects.get(email=email)
        data  = response_data(200,'Successful',[{
            'first_name':updated_data.first_name,
            'last_name':updated_data.last_name,
            'phone_number':updated_data.phone_number,
            'email':updated_data.email,
        }])

        return  Response(data,status=status.HTTP_200_OK)

    

    def list(self, request, *args, **kwargs):
        organisation_short_name = request.query_params.get('organisation_short_name',None)
        if organisation_short_name is None:
            raise PermissionDenied({"organisation_short_name": "Organisation short name must be included in the payload"})

        check_organization_name_and_set_appropriate_schema(organisation_short_name,request.user.email)
        all_admins = User.objects.filter(user_role__role__in=[Role.ADMIN_HR])
        serializer = HrAdminSerializerCleaner(all_admins,many=True)

        
        # serializer = self.get_serializer(data=request.data)
        data  = response_data(200,'Successful',serializer.data)
        return  Response(data,status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        organisation_short_name = request.query_params.get('organisation_short_name',None)
        user_email = request.query_params.get('user_email',None)
        if user_email is None: raise CustomValidation(
                detail="user email must be included",
                field="user_email",
                status_code=400,
            )
        if organisation_short_name is None: CustomValidation(
                detail="please enter a valid organisation_short_name",
                field="email",
                status_code=400,
            ) 
        if not User.objects.filter(email=user_email).exists(): raise CustomValidation(detail='User does not exist',
        field='user_email',status_code=400)
        
        public_user_data = User.objects.get(email=user_email)
        public_user_data.delete()

        check_organization_name_and_set_appropriate_schema(organisation_short_name,request.user.email)
        tenant_user_data = User.objects.get(email=user_email)
        tenant_user_data.delete()
        response  = response_data(200,f'{user_email} delete Successfully',[])
        return Response(response,status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    """
    Create a new auth token for user
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        serializer = self.get_serializer(data=request.data)
        if request.user.is_authenticated:
            data = response_data(400, "You are already authenticated", [])
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as e:
            data = response_data(401, str(e), [])
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        except TypeError as _:  # noqa: F841
            data = response_data(401, "username or password incorrect", [])
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        data = response_data(
            200, "login successful", {"tokens": serializer.validated_data}
        )
        return Response(data, status=status.HTTP_200_OK)


class EmailValidateView(GenericAPIView):
    """
    Account activation with email view
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EmailValidateSerializer

    def post(self, request):
        """
        :param request:
        :return:
        """

        key = request.data.get("key", None)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):

            email_activation_query = EmailInvitation.objects.filter(
                key__iexact=key
            ).select_related('user')
            confirm_query = email_activation_query.confirmable()
            if confirm_query.count() == 1:
                email_activation_object: EmailInvitation = (
                    confirm_query.first()
                )
                email_activation_object.activate()

                data = response_data(
                    200, "Your email is confirmed successfully", []
                )
                return Response(data, status=status.HTTP_200_OK)
            else:
                activated_query = email_activation_query.filter(activated=True)
                if activated_query.exists():
                    data = response_data(
                        200, "Your email has already been confirmed", []
                    )
                    return Response(data, status=status.HTTP_200_OK)

        data = response_data(400, "Bad request, 'Key' is invalid", [])
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class EmailInviteValidateView(GenericAPIView):
    """
    Account invite setup with email view
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EmailInviteValidateSerializer

    def post(self, request):
        """
        :param request:
        :return:
        """

        key = request.data.get("key", None)
        password = request.data.get("password", None)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):

            email_activation_query = EmailInvitation.objects.filter(
                key__iexact=key
            ).select_related('user')
            confirm_query = email_activation_query.confirmable()
            if confirm_query.count() == 1:
                email_activation_object: EmailInvitation = (
                    confirm_query.first()
                )
                email_activation_object.activate(password=password)

                data = response_data(
                    200, "Your account setup is successful", []
                )
                return Response(data, status=status.HTTP_200_OK)
            else:
                activated_query = email_activation_query.filter(activated=True)
                if activated_query.exists():
                    data = response_data(
                        400, "Your account has already been setup", []
                    )
                    return Response(data, status=status.HTTP_400_BAD_REQUEST)

        data = response_data(400, "Bad request, 'Key' is invalid", [])
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(TokenRefreshView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as e:
            data = response_data(401, str(e), [])
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        data = response_data(
            200,
            "Token Refresh successful",
            {"tokens": serializer.validated_data},
        )
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(GenericAPIView):
    """
    Blacklist tokens when users logout
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(200, "User Logout Successful", [])
        return Response(data, status=status.HTTP_200_OK)


class RequestPasswordResetEmailView(GenericAPIView):
    serializer_class = RequestPasswordResetEmailSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        self.serializer_class(data=request.data)
        email = request.data.get("email", "")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)

            uid_base64_encode = urlsafe_base64_encode(
                force_bytes(user.user_id)
            )
            token = PasswordResetTokenGenerator().make_token(user)

            # save user reset email tracking
            PasswordResetTracking.objects.create_password_reset_tracking(
                user=user,
                email=user.email,
                device=request.user_agent.device.family,
                os=request.user_agent.os.family,
                os_version=request.user_agent.os.version_string,
                browser=request.user_agent.browser.family,
                browser_version=request.user_agent.browser.version_string,
                ip_address=get_client_ip(request),
            )
            reset_password_email_path = (
                "password/reset/?uid_base64={}&token={}&org={}".format(
                    uid_base64_encode, token, connection.get_schema()
                )
            )
            base_url = settings.BASE_DOMAIN
            verification_path = f"{base_url}{reset_password_email_path}"
            time_and_date = datetime.datetime.strftime(
                tzware_datetime(), "%B %d, %Y, %I:%M %p (%Z)"
            )
            context = {
                "reset_password_email_path": verification_path,
                "first_name": user.first_name,
                "date": time_and_date,
                "operating_system": "{}".format(request.user_agent.os.family),
                "browser": "{}, version: {}".format(
                    request.user_agent.browser.family,
                    request.user_agent.browser.version_string,
                ),
                "ip_address": get_client_ip(request),
            }

            from_email = settings.DEFAULT_FROM_EMAIL

            html_template = render_to_string(
                "auth/forgot_password.html", context=context
            )

            mail_sender = {"email": from_email, "name": "Support"}
            mail_recipient = [{"email": user.email}]

            send_password_reset_email.delay(
                sender=mail_sender,
                content=html_template,
                first_name=user.first_name,
                recipient_email=mail_recipient,
            )
        data = response_data(200, "reset password email sent successfully", [])
        return Response(data, status=status.HTTP_200_OK)


class PasswordTokenCheckView(APIView):
    @staticmethod
    def get(_, uid_base64, token):
        try:
            user_id_decoded = smart_str(
                urlsafe_base64_decode(uid_base64).decode()
            )
            user = User.objects.get(user_id=user_id_decoded)

            if not PasswordResetTokenGenerator().check_token(user, token):
                data = response_data(
                    401, "Token is not valid, please request a new one", []
                )
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)
            data = response_data(
                200, "Token Valid", {"uid_base64": uid_base64, "token": token}
            )
            return Response(data, status=status.HTTP_200_OK)
        except (DjangoUnicodeDecodeError, ValueError, User.DoesNotExist) as _:
            data = response_data(
                401,
                "Token is not valid or tampered with, please request a new one",
                [],
            )
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)


class SetNewPasswordFromResetPasswordEmailView(GenericAPIView):
    serializer_class = SetNewPasswordFromResetPasswordEmailSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = response_data(200, "Password Reset Successful", [])
        return Response(data, status=status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    lookup_field = "user_id"
