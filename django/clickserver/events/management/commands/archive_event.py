from django.core.management.base import BaseCommand
from django.forms import model_to_dict
from django.utils import timezone
from datetime import timedelta
from events.models import Event,ArchivedEvent

class Command(BaseCommand):
    help = 'Archive events older than 1 day'
    def handle(self, *args, **kwargs):
        one_day_ago = timezone.now() - timedelta(days=1)
        events_to_archive = Event.objects.filter(click_time__lte=one_day_ago)
        for event in events_to_archive:
            ArchivedEvent.objects.create(**model_to_dict(event))
        
        events_to_archive.delete()
