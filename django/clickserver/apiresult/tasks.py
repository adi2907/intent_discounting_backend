
from datetime import datetime
from .models import *
from events.models import Event
import numpy as np
from django.db import connections
from datetime import timedelta, timezone
from celery import shared_task,group,chain
import logging
logger = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
from apiresult.utils.app_actions import app_actions
from apiresult.utils.config import *
from django.utils import timezone



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
    item, created = Item.objects.get_or_create(product_id=product_id, app_name=app_name)

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
            'first_visit': first_event['click_time'],
            'last_visit': last_event['click_time'],
            'last_updated': last_event['click_time']
        })
    # if user is created then create user_summary object
    #if created:
    #    user_summary = UserSummary(user_token=user_token, app_name =app_name, last_visited=[], last_carted=[], recommended=[], logged_time=last_event['click_time'])
    #    user_summary.save()

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
        user = User.objects.get(token=user_token,app_name=app_name)
    except:
        logger.info("Exception getting user: " + user_token)
        return

    # Filter the events_data based on the user_token
    user_events = [event for event in events_data if event['token'] == user_token]

    # Get all product ids for the user, excluding blank and null
    product_ids = list(set([event['product_id'] for event in user_events if event['product_id'] not in [None, '', 0]]))

    # Update visit and cart events
    if product_ids:
        #try:
        #    user_summary = UserSummary.objects.get(user_token=user_token, app_name=app_name)
        #except UserSummary.DoesNotExist:
        #    logger.info("Exception getting user summary object: " + user_token)
        #    return

        for product_id in product_ids:
            visit_events = [event for event in user_events if event['product_id'] == product_id and event['event_type'] == 'page_load']
            item = Item.objects.filter(product_id=product_id).last()

            # Update each visit
            for event in visit_events:
                visit = Visits(user=user, item=item, app_name=app_name, created_at=event['click_time'])
                visit.save()
            
                # update user_summary
                # if product_id is in last_visited, remove it and append to the front else append to the front
         #       if product_id in user_summary.last_visited:
         #           user_summary.last_visited.remove(product_id)
         #       user_summary.last_visited.insert(0, product_id)
         #       user_summary.logged_time = event['click_time']

            cart_events = [event for event in user_events if event['product_id'] == product_id and event['click_text'] is not None and 'add to' in event['click_text'].lower()]

            # Update each cart
            for event in cart_events:
                cart = Cart(user=user, item=item, app_name=app_name, created_at=event['click_time'])
                cart.save()
                # update user_summary
         #       if product_id in user_summary.last_carted:
         #           user_summary.last_carted.remove(product_id)
         #       user_summary.last_carted.insert(0, product_id)
         #       user_summary.logged_time = event['click_time']

        # keep only the last 20 items in last_visited and last_carted
        #user_summary.last_visited = user_summary.last_visited[:20]
        #user_summary.last_carted = user_summary.last_carted[:20]
        #user_summary.save()

    # Update identified user
    userid_events = [event for event in user_events if event['user_id'] not in [None, '', 0,'0']]
    
    if userid_events:
        user.registered_user_id = userid_events[0]['user_id']
        user.user_login = userid_events[0]['user_login']
        user.save()

        if IdentifiedUser.objects.filter(registered_user_id=user.registered_user_id).filter(app_name=app_name).exists():
            identified_user = IdentifiedUser.objects.get(registered_user_id=user.registered_user_id, app_name=app_name)

            if user_token not in identified_user.tokens:
                identified_user.tokens.append(user_token)
                identified_user.save()
        else:
            identified_user = IdentifiedUser(registered_user_id=user.registered_user_id, app_name=app_name, tokens=[user_token])
            identified_user.save()
    connections.close_all()

@shared_task
def update_sessions(tokens,session_keys, event_ids, app_name,start_time):
    logger.info("update_sessions start time: " + str(start_time))
    events = Event.objects.filter(id__in=event_ids)
    events_data = events.values('id', 'token', 'click_time', 'session', 'user_id', 'user_login', 'product_id', 'event_type', 'click_text','product_price','source_url')
    with ThreadPoolExecutor() as executor:
        session_tasks = [executor.submit(update_individual_session, session_key,events_data, app_name) for session_key in session_keys]
        for future in concurrent.futures.as_completed(session_tasks):
            future.result()

@shared_task
def update_individual_session(session_key,events_data, app_name):
    session_events = [event for event in events_data if event['session'] == session_key]
    user_token = session_events[0]['token']
    if not session_events:
        return
    # if session exists then update it else create it
    session_variables = get_session_variables(session_events,app_name)
    try:
        session = Sessions.objects.get(session_key=session_key)     
        user = User.objects.get(token=user_token,app_name=app_name)
        session.user = user

        # get all session variables
        for key, value in session_variables.items():
            if key in ['events_count', 'page_load_count', 'click_count', 'total_products_visited', 'purchase_count', 'cart_count',
                       'product_total_price']:
                # Increment the existing attribute for these keys
                setattr(session, key, getattr(session, key) + value)
            
            elif key in ['has_purchased', 'has_carted', 'has_checkout', 'is_logged_in', 'is_paid_traffic','session_end']:
                setattr(session, key, max(getattr(session, key), value))
            
            elif key == 'unique_products_visited':
                # take unique products visited and add to existing unique products visited
                unique_products_visited = getattr(session, key)
                unique_products_visited.extend(value)
                unique_products_visited = list(set(unique_products_visited))
                setattr(session, key, unique_products_visited)
        session.logged_time = session_variables['session_end']
        session.status = 'active'
        session.save()
    except:
        session = Sessions(session_key=session_key,app_name=app_name)
        user = User.objects.get(token=user_token,app_name=app_name)
        session.user = user
        # set all session variables
        for key, value in session_variables.items():
            setattr(session, key, value)
        session.logged_time = session_variables['session_end']
        session.save()



def get_session_variables(session_events,app_name):

    cart_actions = app_actions[app_name]['add_to_cart']
    purchase_actions = app_actions[app_name]['purchase']
    paid_traffic_strings = app_actions[app_name]['paid_traffic']
    
    # update session
    session_start = min(session_events, key=lambda e: e['click_time'])['click_time']
   
    session_end = max(session_events, key=lambda e: e['click_time'])['click_time']
    

    events_count = len(session_events)
    page_load_count = len([event for event in session_events if event['event_type'] == 'page_load'])
    click_count = len([event for event in session_events if event['event_type'] == 'click'])
    total_products_visited = len([event['product_id'] for event in session_events if event['product_id'] not in [None, '', 0]])

    
    unique_products_visited = list(set([event['product_id'] for event in session_events if event['product_id'] not in [None, '', 0]]))

    # add events where any of purchase_actions is a substring of source_url
    purchase_count = 0
    for event in session_events:
        for action in purchase_actions:
            if action.lower() in event['source_url'].lower():
                purchase_count += 1
                break
    
    # add events where any of cart_actions exactly matches click_text
    cart_count = 0
    for event in session_events:
        if event['click_text']:
            for action in cart_actions:
                if action in event['click_text'].lower():
                    cart_count += 1
                    break

    # has_carted = 1 if cart_count > 0 else 0
    has_carted = 1 if cart_count > 0 else 0
    has_purchased = 1 if purchase_count > 0 else 0
    product_total_price = sum([float(event['product_price']) for event in session_events if event['product_price'] not in [None, '', 0]])

    is_logged_in = 1 if any(event['user_id'] not in [None, '', 0,'0'] for event in session_events) else 0

    is_paid_traffic = 0
    for event in session_events:
        for string in paid_traffic_strings:
            if string in event['source_url'].lower():
                is_paid_traffic = 1
                break
        if is_paid_traffic:
            break
    
    # return a dictionary of session variables
    return {'session_start':session_start,'session_end':session_end,
            'events_count':events_count,'page_load_count':page_load_count,
            'click_count':click_count,'total_products_visited':total_products_visited,
            'unique_products_visited':unique_products_visited,'purchase_count':purchase_count,
            'cart_count':cart_count,'has_carted':has_carted,'has_purchased':has_purchased,
            'product_total_price':product_total_price,'is_logged_in':is_logged_in,
            'is_paid_traffic':is_paid_traffic}

@shared_task
def update_database_chunk(start_time, end_time, app_name):
   
    events = Event.objects.filter(click_time__gte=start_time).filter(click_time__lte=end_time).filter(app_name=app_name)
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
    db_product_ids = Item.objects.filter(app_name=app_name).values_list('product_id', flat=True).distinct()
    
    new_product_ids = np.setdiff1d(product_ids, db_product_ids).tolist()

    session_keys = events.values_list('session', flat=True).distinct()
    session_keys = list(session_keys)
    

    # update database
    if len(new_product_ids) > 0:
        # update products and users in parallel using celery
        
        g1 = group(update_products.si(new_product_ids,event_ids,app_name,start_time),update_users.si(tokens,event_ids,app_name,start_time))
        # chain update_user_activities to g1
        g2 = chain(g1,group(update_user_activities.si(tokens,event_ids,app_name,start_time),update_sessions.si(tokens,session_keys,event_ids,app_name,start_time)))
        g3 = chain(g2,update_all_user_sessions.si())
    else:
        # chain user and user_activities
        g1 = group(update_users.si(tokens,event_ids,app_name,start_time))
        g2 = chain(g1,group(update_user_activities.si(tokens,event_ids,app_name,start_time),update_sessions.si(tokens,session_keys,event_ids,app_name,start_time)))
        g3 = chain(g2,update_all_user_sessions.si())
    
    g3()
    
@shared_task
def update_all_user_sessions():
    # change is_active to false if session last logged time is more than SESSION_IDLE_TIME (1 hour)
    sessions = Sessions.objects.filter(is_active=True)
    for session in sessions:
        if (timezone.now() - session.session_end).total_seconds() > (SESSION_IDLE_TIME*60):
            session.is_active = False
            # update session duration
            session.session_duration = (session.session_end - session.session_start).total_seconds()
            session.save()
            # update the user attributes
            user = session.user
            # excluding the current session
            previous_4_sessions = Sessions.objects.filter(user=user).order_by('-session_end')[1:5]
            previous_session = None
            if len(previous_4_sessions) >= 1:
                previous_session = previous_4_sessions[0] #most recent session excluding the current session
                
            purchase_history = [session.has_purchased for session in previous_4_sessions]
            user.purchase_last_4_sessions = 1 if sum(purchase_history) > 0 else 0
            user.carted_last_4_sessions = 1 if sum([session.has_carted for session in previous_4_sessions]) > 0 else 0
            
            # if previous session then assign purchase_prev_session to has_purchased of previous session else assign 0
            if previous_session:
                user.purchase_prev_session = previous_session.has_purchased

            # number of sessions last 30 days
            sessions_last_30_days = Sessions.objects.filter(user=user).filter(logged_time__gte=timezone.now() - timedelta(days=30))
            user.num_sessions_last_30_days = len(sessions_last_30_days)

            # number of sessions last 7 days
            sessions_last_7_days = Sessions.objects.filter(user=user).filter(logged_time__gte=timezone.now() - timedelta(days=7))
            user.num_sessions_last_7_days = len(sessions_last_7_days)
            user.save()
            


@shared_task
def update_database():    
    time_chunk = 30
    start_time = datetime.now() - timedelta(seconds=time_chunk)
    end_time = datetime.now()
    # start_time = datetime(2023, 1, 1, 0, 0, 0)
    # end_time = datetime(2023, 2, 1, 0, 0, 0)
    # time_chunk = 60
   
    
    for app_name in Event.objects.values_list('app_name', flat=True).distinct():
        update_database_chunk(start_time, end_time, app_name)

        # get all events in chunks of 5 minutes
        # while start_time < end_time:
        #     # chain update_database_chunk and update_all_user_sessions
                
        #     update_database_chunk(start_time, start_time+timedelta(minutes=time_chunk), app_name)
            
        #     logger.info("Sleeping....")
        #     time.sleep(60)
        #     # update start time
        #     start_time = start_time+timedelta(minutes=time_chunk)
        
        
        
                
            
