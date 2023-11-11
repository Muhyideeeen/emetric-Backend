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

        self.stdout.write('Creating New Roles for application')
        Role.objects.create(role=Role.ADMIN_HR)
        self.stdout.write('Roles creation completed!')
