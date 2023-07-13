from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apiresult.models import Visits,Cart,User

class Command(BaseCommand):
    help = 'Delete objects older than 15 days'
    def handle(self, *args, **kwargs):
        for Model in [Visits,Cart,User]:
            Model.objects.filter(created_at__lte=timezone.now()-timedelta(days=15)).delete()
