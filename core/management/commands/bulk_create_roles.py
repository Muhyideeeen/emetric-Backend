"""
command for the application to bulk create roles
"""
from django.core.management import BaseCommand

from account.models import Role


class Command(BaseCommand):
    """
    Django command to initialise admin
    """

    def handle(self, *args, **options):

        if Role.objects.count() == 0:
            self.stdout.write('Creating Roles for application')
            Role.objects.bulk_create([
                Role(role=Role.EMPLOYEE),
                Role(role=Role.ADMIN),
                Role(role=Role.ADMIN_HR),
                Role(role=Role.SUPER_ADMIN),
                Role(role=Role.TEAM_LEAD),
                Role(role=Role.Exco_or_Management),
                Role(role=Role.Committee_Member),
                Role(role=Role.Committee_Chair),
            ])
            self.stdout.write('Roles creation completed!')
        else:
            self.stdout.write('Roles already initialised')
