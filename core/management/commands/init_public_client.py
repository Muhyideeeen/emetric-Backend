"""
command for the application to bulk create roles
"""
from datetime import time
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from account.models import Role
from client.models import Client, Domain

User = get_user_model()


class Command(BaseCommand):
    """
    Django command to initialise admin
    """

    def handle(self, *args, **options):
        public_schema = 'public'
        client = Client.objects.filter(schema_name=public_schema)
        if not client.exists():
            self.stdout.write("Creating public client")
            user = User.objects.get(is_superuser=True)
            tenant = Client.objects.create(
                company_name="e_metric_suite",
                owner_email=user.email,
                owner_first_name=user.first_name,
                owner_last_name=user.last_name,
                owner_phone_number=user.phone_number,
                work_start_time=time(hour=8),
                work_stop_time=time(hour=11),
                work_break_start_time=time(hour=12),
                work_break_stop_time=time(hour=16),
                schema_name=public_schema
            )
            Domain.objects.create(
                domain=settings.BASE_DOMAIN,
                tenant=tenant,
                is_primary=True
            )
            self.stdout.write("Public client created successfully")
        else:
            self.stdout.write("Public client already created")
