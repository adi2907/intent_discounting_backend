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


def read_db_dump(file_path):
    events = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            event = {
                'token': row['token'],
                'session': row['session'],
                'user_login': row['user_login'] if row['user_login'] != 'NULL' else None,
                'user_id': row['user_id'] if row['user_id'] != 'NULL' else None,
                'click_time': datetime.strptime(row['click_time'], '%Y-%m-%d %H:%M:%S.%f').isoformat(),
                'user_regd': row['user_regd'] if row['user_regd'] != 'NULL' else None,
                'event_type': row['event_type'],
                'event_name': row['event_name'],
                'source_url': row['source_url'],
                'app_name': row['app_name'],
                'click_text': row['click_text'] if row['click_text'] != 'NULL' else None,
                'product_id': row['product_id'] if row['product_id'] != 'NULL' else None,
                'product_name': row['product_name'] if row['product_name'] != 'NULL' else None,
                'product_price': float(row['product_price']) if row['product_price'] != 'NULL' else None,
                'logged_time': datetime.strptime(row['click_time'], '%Y-%m-%d %H:%M:%S.%f').isoformat()
            }
            events.append(event)
    return events

def group_events(events):
    grouped_events = {}
    for event in events:
        key = (event['session'], event['app_name'])
        if key not in grouped_events:
            grouped_events[key] = []
        grouped_events[key].append(event)
    return grouped_events

# Function to convert click_time to datetime objects
def convert_to_datetime(events):
    for event in events:
        event['click_time'] = datetime.strptime(event['click_time'], '%Y-%m-%dT%H:%M:%S')
        event['logged_time'] = datetime.strptime(event['logged_time'], '%Y-%m-%dT%H:%M:%S')
    return events

def convert_to_isoformat(events):
    for event in events:
        event['click_time'] = event['click_time'].isoformat()
        event['logged_time'] = event['logged_time'].isoformat()
    return events

class TestSaleNotificationCreation(TransactionTestCase):
    def setUp(self):
        self.events = read_db_dump('apiresult/tests/db_dump_test.txt')
        if len(self.events) == 0:
            print("No events were read from the file")
            return
        events = convert_to_datetime(self.events)
        grouped_events = group_events(events)
        results = {}
        for (session, app_name), session_events in grouped_events.items():
            # pack session, app_name, classified_events, time_diff_events into a dictionary
            classified_events,time_diff_events = event_classifier(session_events, app_name)
            results[(session, app_name)] = {
                'session': session,
                'app_name': app_name,
                'classified_events': classified_events,
                'time_diff_events': time_diff_events,
            }
        self.results = results
        self.expected_output = {
            ('79ec89b7f5b6e97273813643d18e1fa2f136813b', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['product_visit'],
                'time_diff_events': [0],
            },
            ('798d82528c660e95e43805ea96c259a6762d5e8b', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['product_visit', 'product_visit'],
                'time_diff_events': [14.0, 0],
            },
            ('8a43e34936e5a7c3a304d723f0c7eaef302da9b2', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['other_click', 'home_page_click'],
                'time_diff_events': [3.0, 0],
            },
            ('f926b1b1825f009fa61a492ec24e4189281ca0ba', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['product_page_click', 'product_visit', 'product_page_click', 'product_visit'],
                'time_diff_events': [3.0, 11.0, 2.0, 0],
            },
            ('fb7cf9576cbffb2c9db1a05ae402e26883b6b0e2', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['catalog_to_product_click', 'product_visit'],
                'time_diff_events': [2.0, 0],
            },
            ('6c3ce6a9f3dda7f7eab441bdd79f40ea8030b741', 'desisandook.myshopify.com'): {
                'classified_events': ['catalog_page_visit'],
                'time_diff_events': [0],
            },
            ('b6ed5ca3ebe722b4df2726a4d0c0dbd75be2df01', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['catalog_to_product_click', 'product_visit', 'catalog_page_click'],
                'time_diff_events': [4.0, 13.0, 0],
            },
            ('aa0513a9150f9b88e83d5c055ba7ab288ea4eca3', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['product_visit'],
                'time_diff_events': [0],
            },
            ('ae515641a4a9accda6516d940f2e34cc06bb3c3f', 'desisandook.myshopify.com'): {
                'classified_events': ['product_visit'],
                'time_diff_events': [0],
            },
            ('341506b78dce47cfb5c9d6814daa72d367485ce0', 'sujatra-sarees.myshopify.com'): {
                'classified_events': ['product_page_click', 'cart_page_visit', 'product_visit'],
                'time_diff_events': [2.0, 42.0, 0],
            }
        }
    def test_event_classification(self):
        for key, expected in self.expected_output.items():
            self.assertEqual(self.results[key]['classified_events'], expected['classified_events'])
            self.assertEqual(self.results[key]['time_diff_events'], expected['time_diff_events'])

    def test_update_sale_notif_session_creation(self):
        session_key = '8a43e34936e5a7c3a304d723f0c7eaef302da9b2'
        app_name = 'sujatra-sarees.myshopify.com'
        events_data = [event for event in self.events if event['session'] == session_key and event['app_name'] == app_name]
        events_data = convert_to_isoformat(events_data)

        try:
            update_sale_notif_session(session_key, events_data, app_name)
            sale_notif_session = SaleNotificationSessions.objects.get(session_key=session_key, app_name=app_name)
            self.assertEqual(sale_notif_session.session_key, session_key)
            self.assertEqual(sale_notif_session.app_name, app_name)
        except SaleNotificationSessions.DoesNotExist:
            self.fail("SaleNotificationSession was not created.")
        except Exception as e:
            self.fail(f"Unexpected error occurred: {str(e)}")

    def test_extend_sale_notif_session(self):
        session_key = 'ddd'
        app_name = 'sujatra-sarees.myshopify.com'
        events_data = [event for event in self.events if event['session'] == session_key and event['app_name'] == app_name]
        # consider only the first event
        first_event = events_data[:1]
        first_event = convert_to_isoformat(first_event)
        second_event = events_data[1:]
        second_event = convert_to_isoformat(second_event)
        try: 
            # first create a new SaleNotificationSession
            update_sale_notif_session(session_key, first_event, app_name)
            sale_notif_session = SaleNotificationSessions.objects.get(session_key=session_key, app_name=app_name)
            self.assertEqual(sale_notif_session.events_category_list, ['catalog_page_click'])
            # now extend the SaleNotificationSession
            update_sale_notif_session(session_key, second_event, app_name)
            sale_notif_session = SaleNotificationSessions.objects.get(session_key=session_key, app_name=app_name)
            self.assertEqual(sale_notif_session.events_category_list, ['catalog_to_product_click', 'product_visit'])
        except SaleNotificationSessions.DoesNotExist:
            self.fail("SaleNotificationSession was not created.")
        except Exception as e:
            self.fail(f"Unexpected error occurred: {str(e)}")


    
            
       


        

        

            
            


    


