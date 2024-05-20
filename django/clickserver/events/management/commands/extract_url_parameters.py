from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.db import transaction
from events.models import EventArchive, EventUrlParameters
from urllib.parse import urlparse, parse_qs

class Command(BaseCommand):
    help = 'Extract URL parameters from the event_archive table and store them'

    def handle(self, *args, **kwargs):
        batch_size = 10000
        thread_count = 100  # Adjust thread count based on your server's capability

        # Get all events from event_archive table
        events_to_process = list(EventArchive.objects.all().order_by('id'))
        event_batches = [events_to_process[i:i + batch_size] for i in range(0, len(events_to_process), batch_size)]
        total_batches = len(event_batches)

        print(f"Processing {len(events_to_process)} events from event_archive table in {total_batches} batches.")

        # Process each batch using multi-threading
        for i, batch in enumerate(event_batches, start=1):
            print(f"Processing batch {i} of {total_batches}.")
            updated_count = self.process_batch(batch, thread_count)
            print(f"Batch {i} processed. {updated_count} URLs updated.")

    def process_batch(self, events, thread_count):
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            future_to_event = {executor.submit(self.extract_and_save_parameters, event): event for event in events}
            updated_count = 0
            for future in as_completed(future_to_event):
                if future.result():
                    updated_count += 1
        return updated_count

    def extract_and_save_parameters(self, event):
        source_url = event.source_url
        if not source_url:
            return False

        parsed_url = urlparse(source_url)
        query_params = parse_qs(parsed_url.query)
        params = {
            'token': event.token,
            'session': event.session,
            'click_time': event.click_time,
            'source_url': source_url,
            'app_name': event.app_name,
            'product_id': event.product_id,
            'utm_source': query_params.get('utm_source', [None])[0],
            'utm_medium': query_params.get('utm_medium', [None])[0],
            'ad_id': query_params.get('ad_id', [None])[0],
            'utm_term': query_params.get('utm_term', [None])[0],
            'fbclid': query_params.get('fbclid', [None])[0],
            'gclid': query_params.get('gclid', [None])[0],
            'utm_campaign': query_params.get('utm_campaign', [None])[0],
            'utm_content': query_params.get('utm_content', [None])[0],
        }

        if not any(params[key] for key in ['utm_source', 'utm_medium', 'ad_id', 'utm_term', 'fbclid', 'gclid', 'utm_campaign', 'utm_content']):
            return False

        EventUrlParameters.objects.create(**params)  # Use create instead of update_or_create
        return True