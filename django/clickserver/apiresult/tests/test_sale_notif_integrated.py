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
from rest_framework.test import APIRequestFactory
from django.urls import reverse
import logging
logger = logging.getLogger(__name__)

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
        self.factory = APIRequestFactory()
    
    def test_integration(self):
            
        # read all the active sale notification sessions
        sessions = SaleNotificationSessions.objects.all()
        print(f"Length of sessions is {len(sessions)}")

        # Pass this to the view
        for session in sessions:
            url = reverse('new-sale-notification')
            request = self.factory.get(url,{
                'token': 'test_token',
                'app_name': session.app_name,
                'session_id': session.session_key,
            })

            view = NewSaleNotificationView.as_view()
            response = view(request)

            if session.event_sequence_length < 10:
                self.assertFalse(response.data['sale_notification'])
            else:
                # log the response for the session
                logger.info(f"Session: {session.session_key}, Sale Notification: {response.data['sale_notification']}")

                
                

               
