from rest_framework import serializers,fields
from . import models
from timezone_field.rest_framework import TimeZoneSerializerField


class ClientMangerCleanerSerialzer(serializers.ModelSerializer):
    organisation_short_name = serializers.CharField(
        required=True, write_only=True
    )
    company_short_name = serializers.SerializerMethodField()
    work_days = fields.MultipleChoiceField(choices=models.Client.DAY_CHOICES)
    timezone = TimeZoneSerializerField(required=True)  

    class Meta:
        model = models.Client
        fields = [
            "organisation_short_name",
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
            'lincence','start_date','end_date','activate','poc','addresse','name_of_account_manager',
            'tel_of_account_manager','email_of_account_manager','name_of_account_HRmanager','tel_of_account_HRmanager','email_of_account_HRmanager'
        ]
    @staticmethod
    def get_company_short_name(obj):
        return obj.schema_name



