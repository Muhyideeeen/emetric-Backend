"""
command for the application to delete a particular client account
"""
from django.core.management import BaseCommand

from client.models import Client
from core.utils.tenant_management import delete_client


class Command(BaseCommand):
    """
    Django command to initialise admin
    """
    def add_arguments(self, parser):
        parser.add_argument('name', type=str)

    def handle(self, *args, **options):

        self.stdout.write('Deleting client and user')
        client = Client.objects.get(schema_name=options['name'])
        
        delete_client(client)

        self.stdout.write('User and Client details has been deleted!')
