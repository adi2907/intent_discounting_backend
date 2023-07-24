from django.test import TestCase

# Create your tests here.
from django.utils import timezone
from datetime import timedelta
from .models import Item, User, Purchase, Visits, Cart, IdentifiedUser
from events.models import Event
from datetime import datetime


class TestUpdateDatabase(TestCase):
    def setUp(self):
        self.app_name = 'desi_sandook'
        self.start_time = datetime(2023, 2, 1, 8, 0, 0)
        self.end_time = datetime(2023, 2, 1, 17, 0, 0)
        
   # check number of tokens in User model is equal to number of tokens in Event model
    def test_users(self):
        users = User.objects.filter(app_name=self.app_name).values_list('token').distinct().order_by('token')
        users_list = [user[0] for user in users]
        users_list.sort()
        users_events = Event.objects.filter(
            click_time__gte=self.start_time,
            click_time__lt=self.end_time,
            app_name=self.app_name
        ).values_list('token', flat=True).distinct().order_by('token')
        users_events_list = list(users_events)
        users_events_list.sort()
        self.assertEqual(users_list, users_events_list)
    
    # check for duplicate tokens in User model
    def test_duplicate_tokens(self):
        tokens = User.objects.filter(app_name=self.app_name).values_list('token', flat=True)
        self.assertEqual(len(tokens), len(set(tokens)))

    # check number of user_ids in User model is equal to number of user_ids in Event model
    def test_user_ids(self):
        registered_user_ids = User.objects.filter(app_name=self.app_name).values_list('registered_user_id', flat=True).distinct()
        registered_user_ids = [user_id for user_id in registered_user_ids if user_id]
        # convert user_ids to int
        registered_user_ids = [int(user_id) for user_id in registered_user_ids]
        registered_user_ids.sort()

        user_ids_events = Event.objects.filter(
            click_time__gte=self.start_time,
            click_time__lt=self.end_time,
            app_name=self.app_name,
            user_id__isnull=False,
            user_id__gt=0,
        ).values_list('user_id', flat=True).distinct()
        user_events_list = [int(user_id) for user_id in user_ids_events]
        user_events_list.sort()
        self.assertEqual(registered_user_ids, user_events_list)

    # check if number of items in Item model is equal to number of items in Event model
    def test_products(self):
        items = Item.objects.filter(app_name=self.app_name).values_list('product_id').distinct()
        # exclude blank items or items with product_id = 0
        items = [item for item in items if (item[0] != 0 or item[0] != '' or item[0] != None)]
        items_list = [int(item[0]) for item in items]
        items_list.sort()
        # arrange items_list in ascending order       
        items_events = Event.objects.filter(
            click_time__gte=self.start_time,
            click_time__lt=self.end_time,
            app_name=self.app_name,
            product_id__isnull=False,
        ).exclude(product_id='').values_list('product_id', flat=True).distinct()

        items_events_list = [int(product_id) for product_id in items_events]
        items_events_list.sort()
        self.assertEqual(items_list, items_events_list)

    # check for duplicate items in Item model
    def test_duplicate_products(self):
        items = Item.objects.filter(app_name=self.app_name).values_list('product_id', flat=True)
        self.assertEqual(len(items), len(set(items)))
    
    # check if number of visits in Visit model is equal to number of visits in Event model
    def test_visits(self):
        # get all user_ids and number of visits from Visit model
        visits = {}
        # get list of user_ids
        user_id_list = Visits.objects.filter(app_name=self.app_name).values_list('user_id', flat=True).distinct()
        for user in user_id_list:   
           # get the corresponding token for the user_id
            token = User.objects.get(id=user,app_name=self.app_name).token
            # get the number of visits for the user_id
            num_visits = Visits.objects.filter(user_id=user, app_name=self.app_name).count()
            # store the token and number of visits in a dictionary
            visits[token] = num_visits
        
        event_visits = {}
        # get all user tokens corresponding to the page views on products
        event_objects = Event.objects.filter(
            click_time__gte=self.start_time,
            click_time__lt=self.end_time,
            app_name=self.app_name,
            event_type='page_load',
            product_id__isnull=False
        ).exclude(product_id='')
        
        # get tokens and number of visits from the events
        for event in event_objects:
            if event.token in event_visits:
                event_visits[event.token] += 1
            else:
                event_visits[event.token] = 1
        
        # assert if the two dictionaries are not equal
        self.assertDictEqual(visits, event_visits)

    # check if number of carts in Cart model is equal to number of carts in Event model
    def test_cart(self):
        # get all user_ids and number of visits from Visit model
        carts = {}
        # get list of user_ids
        user_id_list = Cart.objects.filter(app_name=self.app_name).values_list('user_id', flat=True).distinct()
        for user in user_id_list:   
           # get the corresponding token for the user_id
            token = User.objects.get(id=user,app_name=self.app_name).token
            # get the number of visits for the user_id
            num_carts = Cart.objects.filter(user_id=user, app_name=self.app_name).count()
            # store the token and number of visits in a dictionary
            carts[token] = num_carts
        event_carts = {}
        # get all user tokens corresponding to the page views on products
        event_objects = Event.objects.filter(
            click_time__gte=self.start_time,
            click_time__lt=self.end_time,
            app_name=self.app_name,
            click_text__icontains='add to',
            product_id__isnull=False
        ).exclude(product_id='')
        
        # get tokens and number of visits from the events
        for event in event_objects:
            if event.token in event_carts:
                event_carts[event.token] += 1
            else:
                event_carts[event.token] = 1
        
        # assert if the two dictionaries are not equal
        self.assertDictEqual(carts, event_carts)


    # check if the right tokens are assigned to identified users
    def test_identified_user(self):
        # pick the first identified user if it exists
        identified_user = IdentifiedUser.objects.filter(app_name=self.app_name).first()
        if identified_user:
            
            # get the registered user id
            registered_user_id = identified_user.registered_user_id
            # get the tokens corresponding to the user id
            tokens = User.objects.filter(registered_user_id=registered_user_id, app_name=self.app_name).values_list('token', flat=True)


            # get the tokens corresponding to this user id from events
            event_tokens = Event.objects.filter(
                click_time__gte=self.start_time,
                click_time__lt=self.end_time,
                app_name=self.app_name,
                user_id=registered_user_id,
                user_id__isnull=False,
                user_id__gt=0,
            ).values_list('token', flat=True).distinct()
            # assert if the two lists are not equal
            self.assertListEqual(list(tokens), list(event_tokens))


    
        
        
