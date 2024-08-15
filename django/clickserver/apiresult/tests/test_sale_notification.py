from datetime import datetime
import random
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.models import User
from apiresult.models import SaleNotificationSessions
from events.models import Event
from apiresult.tasks import update_sale_notif_session
from apiresult.utils.event_classification import event_classifier
import csv
from django.test import TransactionTestCase

# helper functions

def get_events_for_period(start_time, end_time):
    events = Event.objects.filter(
        logged_time__gte=start_time,
        logged_time__lt=end_time,
    ).order_by('logged_time')
    
    events_data = []
    for event in events:
        event_data = {
            'token': event.token,
            'session': event.session,
            'user_login': event.user_login,
            'user_id': event.user_id,
            'click_time': event.click_time.isoformat(),
            'user_regd': event.user_regd,
            'event_type': event.event_type,
            'event_name': event.event_name,
            'source_url': event.source_url,
            'app_name': event.app_name,
            'click_text': event.click_text,
            'product_id': event.product_id,
            'product_name': event.product_name,
            'product_price': event.product_price,
            'logged_time': event.logged_time.isoformat()
        }
        events_data.append(event_data)
    return events_data

def group_events(events):
    grouped_events = {}
    for event in events:
        key = (event['session'], event['app_name'])
        if key not in grouped_events:
            grouped_events[key] = []
        grouped_events[key].append(event)
    return grouped_events



class TestSaleNotification(TransactionTestCase):
    def setUp(self):
        self.events = get_events_for_period('2024-08-07 13:00:00', '2024-08-07 13:01:00')
        if len(self.events) == 0:
            print("No events were read from the file")
            return
    def test_event_creation_from_db(self):
        # group the events
        grouped_events = group_events(self.events)
            
        # create sale notification sessions
        for key,events in grouped_events.items():
            session_key, app_name = key
            print(f"Processing session: {session_key}, app: {app_name}, events: {len(events)}")
            update_sale_notif_session(session_key, events, app_name)
        # check if the sale notification sessions are created
        sessions = SaleNotificationSessions.objects.all()
        print(f"Total created sessions: {len(sessions)}")
        # Print details of each session
        for session in sessions:
            print(f"Session: {session.session_key}, App: {session.app_name}, Events: {session.event_sequence_length}")

        # the length of the sessions should be equal to the number of unique sessions
        self.assertEqual(len(sessions), len(grouped_events))
       