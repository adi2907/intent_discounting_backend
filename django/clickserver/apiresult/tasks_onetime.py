
from datetime import datetime
from .models import Item,User, Visits, Cart,IdentifiedUser
from events.models import Event
import numpy as np
from django.db import connections
from datetime import timedelta
from celery import shared_task,group,chain
import logging
logger = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time


@shared_task
def update_products(new_product_ids, event_ids, app_name,start_time):
    logger.info("update_products start time "+str(start_time))
    # Get events from the database from event_ids
    events = Event.objects.filter(id__in=event_ids)

    # Create a list of dictionaries containing necessary information for each event
    event_data = events.values('id', 'product_id', 'click_time', 'product_name', 'product_price', 'product_category')

    with ThreadPoolExecutor() as executor:
        product_tasks = [
            executor.submit(update_individual_product, product_id, event_data, app_name)
            for product_id in new_product_ids
        ]
        for future in concurrent.futures.as_completed(product_tasks):
            future.result()
       

@shared_task
def update_individual_product(product_id, event_data, app_name):
   
    # Check if an item with the given product_id already exists
    item, created = Item.objects.get_or_create(item_id=product_id, app_name=app_name)

    # Filter the event_data list for events with the specific product_id and get the last event
    product_events = [event for event in event_data if event['product_id'] == product_id]
    product_events.sort(key=lambda x: x['click_time'], reverse=True)
    event = product_events[0]

    item.name = event['product_name']
    price = event['product_price']
    if price == '':
        price = 0
    item.price = price
    item.categories = event['product_category']
    item.app_name = app_name
    item.last_updated = event['click_time']
    item.save()
    connections.close_all()


@shared_task
def update_users(tokens, event_ids, app_name,start_time):
    # log the start time and end time
    logger.info("update_users start time: " + str(start_time))
    events = Event.objects.filter(id__in=event_ids)
    event_data = events.values('id', 'token', 'click_time', 'session', 'user_id', 'user_login')
    with ThreadPoolExecutor() as executor:
        user_tasks = [executor.submit(update_individual_user, user_token, event_data, app_name) for user_token in tokens]
        for future in concurrent.futures.as_completed(user_tasks):
            future.result()

@shared_task
def update_individual_user(user_token, event_data, app_name):
    # user_events is now a list of dictionaries containing event attributes
    user_events = [event for event in event_data if event['token'] == user_token]
    if not user_events:
        return

    first_event = min(user_events, key=lambda e: e['click_time'])
    last_event = max(user_events, key=lambda e: e['click_time'])

    user, created = User.objects.get_or_create(token=user_token, defaults={
            'app_name': app_name,
            'num_sessions': 0,
            'first_visit': first_event['click_time'],
            'last_visit': last_event['click_time'],
            'last_updated': last_event['click_time']
        })

    if not created:
        user.last_visit = last_event['click_time']
        user.last_updated = last_event['click_time']
    user.save()
    connections.close_all()

@shared_task
def update_user_activities(tokens, event_ids, app_name,start_time):
    logger.info("update_user_activities start time: " + str(start_time))
    # Fetch all events related to the event_ids
    events = Event.objects.filter(id__in=event_ids)
    events_data = events.values('id', 'token', 'click_time', 'session', 'user_id', 'user_login', 'product_id', 'event_type', 'click_text')

    with ThreadPoolExecutor() as executor:
        user_activities_tasks = [executor.submit(update_individual_user_activities, user_token, events_data, app_name) for user_token in tokens]
        for future in concurrent.futures.as_completed(user_activities_tasks):
            future.result()

@shared_task
def update_individual_user_activities(user_token, events_data, app_name):
    try:
        user = User.objects.get(token=user_token)
    except:
        logger.info("Exception getting user: " + user_token)
        return

    # Filter the events_data based on the user_token
    user_events = [event for event in events_data if event['token'] == user_token]

    # Get all product ids for the user, excluding blank and null
    product_ids = list(set([event['product_id'] for event in user_events if event['product_id'] not in [None, '', 0]]))

    # Update visit and cart events
    if product_ids:
        for product_id in product_ids:
            visit_events = [event for event in user_events if event['product_id'] == product_id and event['event_type'] == 'page_load']
            item = Item.objects.filter(item_id=product_id).last()

            # Update each visit
            for event in visit_events:
                visit = Visits(user=user, item=item, app_name=app_name, created_at=event['click_time'])
                visit.save()

            cart_events = [event for event in user_events if event['product_id'] == product_id and event['click_text'] is not None and 'add to' in event['click_text'].lower()]

            # Update each cart
            for event in cart_events:
                cart = Cart(user=user, item=item, app_name=app_name, created_at=event['click_time'])
                cart.save()

    # Update identified user
    userid_events = [event for event in user_events if event['user_id'] not in [None, '', 0,'0']]
    
    if userid_events:
        user.user_id = userid_events[0]['user_id']
        user.user_login = userid_events[0]['user_login']
        user.save()

        if IdentifiedUser.objects.filter(user_id=user.user_id).filter(app_name=app_name).exists():
            identified_user = IdentifiedUser.objects.get(user_id=user.user_id, app_name=app_name)

            if user_token not in identified_user.tokens:
                identified_user.tokens.append(user_token)
                identified_user.save()
        else:
            identified_user = IdentifiedUser(user_id=user.user_id, app_name=app_name, tokens=[user_token])
            identified_user.save()
    connections.close_all()


@shared_task
def update_database_chunk(start_time, end_time, app_name):
   
    events = Event.objects.filter(click_time__gte=start_time).filter(click_time__lt=end_time).filter(app_name=app_name)
    # get the database ids corresponding to the events as a list
    event_ids = events.values_list('id', flat=True).distinct()
    event_ids = list(event_ids)

    logger.info("Number of events for app_name: %s, start_time: %s, end_time: %s, number of events: %s", app_name, start_time, end_time, len(events))
    #1. List customer tokens in this event chunk 
    tokens = events.values_list('token', flat=True).distinct()
    tokens = list(tokens)
    
    # 2. List product ids in this event chunk
    product_ids = events.values_list('product_id', flat=True).distinct()
    product_ids = product_ids.exclude(product_id__isnull=True).exclude(product_id='').exclude(product_id=0)
    # extract all product ids from database with the same app_name
    db_product_ids = Item.objects.filter(app_name=app_name).values_list('item_id', flat=True).distinct()
    
    new_product_ids = np.setdiff1d(product_ids, db_product_ids).tolist()
    

    # update database
    if len(new_product_ids) > 0:
        # update products and users in parallel using celery
        
        g1 = group(update_products.si(new_product_ids,event_ids,app_name,start_time),update_users.si(tokens,event_ids,app_name,start_time))
        # chain update_user_activities to g1
        g2 = chain(g1,update_user_activities.si(tokens,event_ids,app_name,start_time))
    
    else:
        # chain user and user_activities
        g2 = chain(update_users.si(tokens,event_ids,app_name,start_time),update_user_activities.si(tokens,event_ids,app_name,start_time))
    
    g2()
    
    

@shared_task
def update_database():  
 
    start_time = datetime(2023, 2, 1, 0, 0, 0)
    end_time = datetime(2023, 2, 7, 0, 0, 0)
    time_chunk = 60

    # for each app name
    # TODO: add app_name model and iterate from there
    for app_name in Event.objects.values_list('app_name', flat=True).distinct():
        
        # get all events in chunks of 5 minutes
        while start_time < end_time:
               
            update_database_chunk(start_time, start_time+timedelta(minutes=time_chunk), app_name)
            logger.info("Sleeping....")
            time.sleep(60)
            # update start time
            start_time = start_time+timedelta(minutes=time_chunk)
        
                
            
