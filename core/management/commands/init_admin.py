"""
command for the application to intialise admin
"""
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from account.models import Role

User = get_user_model()


class Command(BaseCommand):
    """
    Django command to initialise admin
    """

    def handle(self, *args, **options):
        if Role.objects.count() == 0:
            self.stdout.write('Creating Roles for application')
            Role.objects.bulk_create([
                Role(role=Role.ADMIN),
                Role(role=Role.EMPLOYEE),
                Role(role=Role.ADMIN_HR),
                Role(role=Role.SUPER_ADMIN),
                Role(role=Role.TEAM_LEAD),
            ])
        email = settings.ADMIN_EMAIL
        user = User.objects.filter(email=email)
        if user.count() == 0:
            first_name = settings.ADMIN_FIRST_NAME
            last_name = settings.ADMIN_LAST_NAME
            phone_number = settings.ADMIN_PHONE_NUMBER
            password = settings.ADMIN_PASS
            self.stdout.write('Creating account for (%s)' % email)
            User.objects.create_superuser(email=email,
                                          first_name=first_name,
                                          last_name=last_name,
                                          phone_number=phone_number,
                                          password=password)
        else:
            self.stdout.write('Admin accounts can only be initialized if no Accounts exist')
