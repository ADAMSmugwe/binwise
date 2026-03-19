from django.core.management.base import BaseCommand
from django.db import connection
from api.models import WasteItem

class Command(BaseCommand):
    help = 'Delete all WasteItem records and reset the ID counter'

    def handle(self, *args, **kwargs):
        WasteItem.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='api_wasteitem';")
        self.stdout.write(self.style.SUCCESS('WasteItem table cleared and ID reset to 1.'))