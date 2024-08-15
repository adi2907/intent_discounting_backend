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
from notification.views import NewSaleNotificationView

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
    def test_integration(self):

        # get events in batches of 1 min each
        for i in range(1, 10):
            start_time = datetime(2024, 8, 7, 13, i, 0, 0)
            end_time = datetime(2024, 8, 7, 13, i+1, 0, 0)
            events = get_events_for_period(start_time, end_time)
            grouped_events = group_events(events)
            # create sale notification sessions
            for key,events in grouped_events.items():
                session_key, app_name = key
                update_sale_notif_session(session_key, events, app_name)
            
            # read all the active sale notification sessions
            sessions = SaleNotificationSessions.objects.all()

            # Pass this to the view
            

        
