from django.core.management.base import BaseCommand
from django.forms import model_to_dict
from django.db import transaction
from datetime import datetime, timedelta
from events.models import Event, EventArchive
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Archive events older than 1 day'

    def handle(self, *args, **kwargs):
        # Calculate the cutoff as the end of the day two days ago
        cutoff = (datetime.now() - timedelta(days=2)).replace(hour=23, minute=59, second=59, microsecond=999999)

        events_to_archive = Event.objects.filter(logged_time__lte=cutoff)
        last_event = events_to_archive.order_by('-id').first()

        if last_event:
            logger.info(f'Archiving events up to {last_event.logged_time}')

        # Create a bulk insert list
        bulk_insert = [EventArchive(**model_to_dict(event)) for event in events_to_archive]

        # Bulk insert the events to the event_archive table in smaller batches
        batch_size = 1000
        for i in range(0, len(bulk_insert), batch_size):
            with transaction.atomic():  # Transaction per batch
                EventArchive.objects.bulk_create(bulk_insert[i:i+batch_size])

        # Batch delete from the original table
            batch_size = 1000
            event_ids = list(events_to_archive.values_list('id', flat=True)) 
            for i in range(0, len(event_ids), batch_size):
                with transaction.atomic():
                    Event.objects.filter(id__in=event_ids[i:i+batch_size]).delete()

        logger.info("Events archived successfully on {datetime.now()}")