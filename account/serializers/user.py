from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection, IntegrityError
from django_tenants.postgresql_backend.base import is_valid_schema_name
from rest_framework import serializers, fields
from timezone_field.rest_framework import TimeZoneSerializerField

from account.serializers.role import RoleSerializer
from client.models import Client, Domain
from core.utils.check_org_name_and_set_schema import check_organization_name_and_set_appropriate_schema

User = get_user_model()


def normalize_email(email):
    """
    Normalize the email address by lower-casing the domain part of it.
    """
    email = email or ""
    try:
        email_name, domain_part = email.strip().rsplit("@", 1)
    except ValueError:
        pass
    else:
        email = email_name + "@" + domain_part.lower()
    return email


class OrganisationSerializer(serializers.ModelSerializer):
    organisation_short_name = serializers.CharField(
        required=True, write_only=True
    )
    organisation_name = serializers.CharField(required=True, write_only=True)
    organisation_logo = serializers.ImageField(required=False, write_only=True)
    company_short_name = serializers.SerializerMethodField()
    work_days = fields.MultipleChoiceField(choices=Client.DAY_CHOICES)
    timezone = TimeZoneSerializerField(required=True)

    class Meta:
        model = Client
        fields = [
            "organisation_short_name",
            "organisation_name",
            "organisation_logo",
            "company_name",
            "company_logo",
            "owner_email",
            "owner_first_name",
            "owner_last_name",
            "company_short_name",
            "owner_phone_number",
            "work_start_time",
            "work_stop_time",
            "work_break_start_time",
            "work_break_stop_time",
            "work_days",
            "timezone",
            "employee_limit",
        ]
        extra_kwargs = {
            "company_name": {"read_only": True},
            "owner_email": {"read_only": True},
            "company_logo": {"read_only": True},
            "owner_first_name": {"read_only": True},
            "owner_last_name": {"read_only": True},
            "owner_phone_number": {"read_only": True},
            "schema_name": {"read_only": True},
            "work_start_time": {"required": True},
            "work_stop_time": {"required": True},
            "work_break_start_time": {"required": True},
            "work_break_stop_time": {"required": True},
            "employee_limit": {"read_only": True},
        }

    @staticmethod
    def get_company_short_name(obj):
        return obj.schema_name

    @staticmethod
    def validate_organisation_short_name(data):
        if is_valid_schema_name(data):
            return data
        else:
            raise serializers.ValidationError(
                {
                    "organisation_short_name": "Organisation short name is not valid"
                }
            )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        work_start_time = attrs.get("work_start_time")
        work_stop_time = attrs.get("work_stop_time")
        work_break_start_time = attrs.get("work_break_start_time")
        work_break_stop_time = attrs.get("work_break_stop_time")

        if not (
            work_start_time
            < work_break_start_time
            < work_break_stop_time
            < work_stop_time
        ):
            raise serializers.ValidationError(
                {"work_start_time": "Time is not well aligned"}
            )

        return attrs

    def create(self, validated_data):
        organisation_short_name = validated_data.get(
            "organisation_short_name"
        ).lower()
        organisation_logo = validated_data.get("organisation_logo")
        organisation_name = validated_data.get("organisation_name").lower()
        user = self.context.get("request").user
        work_days = validated_data.get("work_days")
        work_start_time = validated_data.get("work_start_time")
        work_stop_time = validated_data.get("work_stop_time")
        work_break_start_time = validated_data.get("work_break_start_time")
        work_break_stop_time = validated_data.get("work_break_stop_time")
        timezone = validated_data.get("timezone")

        try:

            tenant_exist_qs = Client.objects.filter(
                schema_name=organisation_short_name
            )
            org_exist_qs = Client.objects.filter(
                company_name=organisation_name
            )
            if tenant_exist_qs.exists():
                raise serializers.ValidationError(
                    {
                        "organisation_short_name": "Organisation short name already exists"
                    }
                )
            if org_exist_qs.exists():
                raise serializers.ValidationError(
                    {"organisation_name": "Organisation name already exists"}
                )

            tenant = Client.objects.create(
                company_name=organisation_name,
                company_logo=organisation_logo,
                owner_email=normalize_email(email=user.email),
                owner_first_name=user.first_name,
                owner_last_name=user.last_name,
                owner_phone_number=user.phone_number,
                schema_name=organisation_short_name,
                work_days=work_days,
                work_start_time=work_start_time,
                work_stop_time=work_stop_time,
                work_break_start_time=work_break_start_time,
                work_break_stop_time=work_break_stop_time,
                timezone=timezone,
            )
            Domain.objects.create(
                domain=organisation_short_name, tenant=tenant, is_primary=True
            )
            connection.set_schema(schema_name=organisation_short_name)
            call_command("bulk_create_roles")
            User.objects.create_superuser(
                password=user.password,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=user.phone_number,
                is_creating_superuser_for_tenant=True,
            )
            connection.set_schema(schema_name="public")
            return tenant
        except IntegrityError as _:
            message = "value already exist"
            key = "default"
            if "email" or "phone_number" in _.__str__():
                message = "email already exists"
                key = "email"
            if "phone_number" in _.__str__():
                message = "phone_number already exists"
                key = "phone_number"

            raise serializers.ValidationError({key: message})

    def update(self, instance, validated_data):
        # organisation_short_name = validated_data.pop('organisation_short_name').lower()
        organisation_logo = validated_data.get(
            "organisation_logo", instance.company_logo
        )
        # organisation_name = validated_data.pop('organisation_name').lower()
        # user = self.context.get('request').user

        # tenant_exist_qs = Client.objects.filter(schema_name=organisation_short_name)
        # org_exist_qs = Client.objects.filter(company_name=organisation_name)
        # if tenant_exist_qs.exists():
        #     tenant_exist = tenant_exist_qs.first()
        #     # check if the current user is not the owner of the tenant that needs to be renamed
        #     if user.email != tenant_exist.owner_email:
        #         raise serializers.ValidationError({
        #             "organisation_short_name": "Organisation short name belongs to another organisation"
        #         })
        # if org_exist_qs.exists():
        #     org_exist = org_exist_qs.first()
        #     # check if the current user is not the owner of the tenant that needs to be renamed
        #     if user.email != org_exist.owner_email:
        #         raise serializers.ValidationError(
        #             {
        #                 "organisation_name": "Organisation name belongs to another organisation"
        #             }
        #         )
        # user_domain = Domain.objects.get(domain=instance.schema_name)
        # if instance.schema_name != organisation_name:
        #     schema_rename(tenant=instance, new_schema_name=organisation_short_name)
        # instance.company_name = organisation_name
        instance.company_logo = organisation_logo
        instance.work_days = validated_data.get("work_days")
        instance.work_start_time = validated_data.get("work_start_time")
        instance.work_stop_time = validated_data.get("work_stop_time")
        instance.work_break_start_time = validated_data.get(
            "work_break_start_time"
        )
        instance.work_break_stop_time = validated_data.get(
            "work_break_stop_time"
        )
        instance.timezone = validated_data.get("timezone")
        instance.save()

        # user_domain.domain = instance.schema_name
        # user_domain.save()
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    user_role = RoleSerializer(required=True)

    class Meta:
        model = User
        fields = (
            "user_id",
            "first_name",
            "user_role",
            "last_name",
            "phone_number",
            "email",
        )
        extra_kwargs = {
            "user_id": {"read_only": True},
        }


class ResendActivationMailSerializer(serializers.Serializer):
    user = serializers.SlugRelatedField(
        slug_field="user_id",
        queryset=User.objects.all(),
        required=False,
        many=True,
    )




class HrAdminSerializerCleaner(serializers.ModelSerializer):
    
    
    def update(self, instance, validated_data):
        print({'what happiing':validated_data})
        instance.first_name=validated_data.get('first_name',instance.first_name)
        instance.last_name=validated_data.get('last_name',instance.last_name)
        instance.phone_number=validated_data.get('phone_number',instance.phone_number)
        password =validated_data.get('password',None)
        if password:
            instance.password.set_password(password)
        instance.save()

        check_organization_name_and_set_appropriate_schema(self.context.get('organisation_short_name'),self.context.get('request').user.email)
        hr_admin_data_in_tenant = User.objects.get(email=self.context.get('instance_email'))
        hr_admin_data_in_tenant.first_name=validated_data.get('first_name',hr_admin_data_in_tenant.first_name)
        hr_admin_data_in_tenant.last_name=validated_data.get('last_name',hr_admin_data_in_tenant.last_name)
        hr_admin_data_in_tenant.phone_number=validated_data.get('phone_number',hr_admin_data_in_tenant.phone_number)
        password =validated_data.get('password',None)
        if password:
            hr_admin_data_in_tenant.password.set_password(password)
        hr_admin_data_in_tenant.save()

        
        return hr_admin_data_in_tenant
    class Meta:
        model =User
        fields=['first_name','last_name','phone_number','user_id','email']
        write_only_fields = ['password']
        read_only_fields = ['user_id','email']