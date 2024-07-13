
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
from django.db import transaction
import random



@shared_task
def update_products(new_product_ids, app_name, events_data):
    with ThreadPoolExecutor() as executor:
        product_tasks = [
            executor.submit(update_individual_product, product_id, events_data, app_name)
            for product_id in new_product_ids
        ]
        for future in concurrent.futures.as_completed(product_tasks):
            future.result()
       

@shared_task
def update_individual_product(product_id, events_data, app_name):
    if not product_id:
        return
    
    # Filter events for the specific product_id
    product_events = [event for event in events_data if event['product_id'] == str(product_id)]
    if not product_events:
        return

    # Sort product events by logged_time to find the latest event
    product_events.sort(key=lambda x: x['logged_time'], reverse=True)
    latest_event = product_events[0]

    try:
        # Update or create the item with the details from the latest event
        item, created = Item.objects.update_or_create(
            product_id=product_id,
            app_name=app_name,
            defaults={
                'name': latest_event['product_name'],
                'price': latest_event['product_price'] if latest_event['product_price'] else 0,
                'last_updated': latest_event['logged_time']
            }
        )   
    except:
        logger.info("Exception creating product: " + product_id  + " for app_name: " + app_name)
        return

    connections.close_all()


@shared_task
def update_users(tokens, events_data, app_name):      
    with ThreadPoolExecutor() as executor:
        user_tasks = [executor.submit(update_individual_user, user_token, events_data, app_name) for user_token in tokens]
        for future in concurrent.futures.as_completed(user_tasks):
            future.result()

@shared_task
def update_individual_user(user_token, events_data, app_name):
    user_events = [event for event in events_data if event['token'] == user_token]
    if not user_events:
        return

    # Sort to find the first and last events
    user_events.sort(key=lambda x: x['click_time'])
    first_event = user_events[0]
    last_event = user_events[-1]

    try: 
        user, created = User.objects.update_or_create(
            token=user_token, 
            defaults={
                'app_name': app_name,
                'first_visit': first_event['click_time'],
                'last_visit': last_event['click_time'],
                'last_updated': last_event['click_time']
            }
        )
    except:
        logger.info("Exception creating user: " + user_token)
        return
    if created:
        user.experiment_group = 'experimental' if random.random() < 0.5 else 'control'
        user.save()
    connections.close_all()

@shared_task
def update_user_activities(tokens, events_data, app_name):

    with ThreadPoolExecutor() as executor:
        user_activities_tasks = [executor.submit(update_individual_user_activities, user_token, events_data, app_name) for user_token in tokens]
        for future in concurrent.futures.as_completed(user_activities_tasks):
            future.result()

@shared_task
def update_individual_user_activities(user_token, events_data, app_name):
    cart_actions = app_actions.get(app_name, app_actions["default"])["add_to_cart"]
    try:
        user = User.objects.get(token=user_token,app_name=app_name)
    except:
        logger.info("Exception getting user: " + user_token)
        return

    # Filter the events_data based on the user_token
    user_events = [event for event in events_data if event['token'] == user_token]
    if not user_events:
        return

    # Get all product ids for the user, excluding blank and null
    product_ids = {event['product_id'] for event in user_events if event.get('product_id')}
    

    for product_id in product_ids:
        visit_events = [event for event in user_events if event['product_id'] == product_id and event['event_type'] == 'page_load']
        cart_events = [event for event in user_events if event.get('click_text') and any(action in event['click_text'].lower() for action in cart_actions) and event['product_id'] == product_id]

        item = Item.objects.filter(product_id=product_id).last()
        
        # Update each visit
        for event in visit_events:
            visit = Visits(user=user, item=item, app_name=app_name, created_at=event['click_time'])
            visit.save()
        

        for event in cart_events:
            cart = Cart(user=user, item=item, app_name=app_name, created_at=event['click_time'])
            cart.save()

    update_identified_user_details(user_events, user, app_name)
    connections.close_all()

def update_identified_user_details(user_events, user, app_name):
    # get only events which have non empty user_id
    userid_events = [event for event in user_events if event.get('user_id') and event.get('user_id').strip()]

    if userid_events:
        # Assuming the latest user_id is the most relevant
        latest_userid_event = max(userid_events, key=lambda event: event['click_time'])
        registered_user_id = latest_userid_event['user_id']
        user_login = latest_userid_event.get('user_login')

        # Get the IdentifiedUser instance or create a new one if it doesn't exist
        identified_user, created = IdentifiedUser.objects.get_or_create(
            registered_user_id=registered_user_id,
            app_name=app_name,
            defaults={
                'created_at': latest_userid_event['click_time'],  # Set at creation time
                'last_visit': latest_userid_event['click_time'],  # Set at creation time
                'tokens': [user.token]  # Initialize tokens at creation time
            }
        )
        # If the IdentifiedUser instance already exists, append the token to the tokens field
        if not created:
            # Only update if necessary to prevent unnecessary database hits
            if user.token not in identified_user.tokens:
                identified_user.tokens.append(user.token)
                identified_user.tokens = identified_user.tokens  # Reassign to trigger update
            identified_user.last_visit = latest_userid_event['click_time']
            identified_user.save()

        user.registered_user_id = registered_user_id
        user.user_login = user_login
        user.identified_user = identified_user
        user.save()


@shared_task
def update_sessions(session_keys, events_data, app_name):
    with ThreadPoolExecutor() as executor:
        session_tasks = [executor.submit(update_individual_session, session_key,events_data, app_name) for session_key in session_keys]
        for future in concurrent.futures.as_completed(session_tasks):
            future.result()

@shared_task
def update_individual_session(session_key, events_data, app_name):
    session_events = [event for event in events_data if event['session'] == session_key]
    if not session_events:
        return

    user_token = session_events[0]['token']
    session_variables = get_session_variables(session_events, app_name)

    with transaction.atomic():
        session, created = Sessions.objects.get_or_create(session_key=session_key, app_name=app_name)
        
        try:
            user = User.objects.get(token=user_token, app_name=app_name)
            session.user = user
        except User.DoesNotExist:
            logger.info(f"Exception getting user: {user_token} for session: {session_key}")
            return
        # get the experimenatal group from the user
        experiment_group = user.experiment_group
        if not experiment_group:
            # assign a group to user randomly and save the user also
            experiment_group = 'experimental' if random.random() < 0.5 else 'control'
            user.experiment_group = experiment_group
            user.save()
        session.experiment_group = experiment_group
        if created:       
            for key, value in session_variables.items():
                setattr(session, key, value)
            session.logged_time = session_variables['session_end']
            session.save()

        else: 
            
            # Update or set session variables
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
            session.save()
    connections.close_all()


def get_session_variables(session_events,app_name):

    cart_actions = app_actions.get(app_name, app_actions["default"])["add_to_cart"]
    #purchase_actions = app_actions.get(app_name, app_actions["default"])["purchase"]
    paid_traffic_strings = app_actions.get(app_name, app_actions["default"])['paid_traffic']
    
    # update session
    session_start = min(session_events, key=lambda e: e['click_time'])['click_time']
    session_start = datetime.strptime(session_start, '%Y-%m-%dT%H:%M:%S')
    session_end = max(session_events, key=lambda e: e['click_time'])['click_time']
    session_end = datetime.strptime(session_end, '%Y-%m-%dT%H:%M:%S')
    

    events_count = len(session_events)
    page_load_count = len([event for event in session_events if event['event_type'] == 'page_load'])
    click_count = len([event for event in session_events if event['event_type'] == 'click'])
    total_products_visited = len([event['product_id'] for event in session_events if event['product_id'] not in [None, '', 0]])

    
    unique_products_visited = list(set([event['product_id'] for event in session_events if event['product_id'] not in [None, '', 0]]))

    purchase_count = 0
    for event in session_events:
        if event['event_type'] == 'purchase':
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
def update_database_chunk(start_time, end_time, app_name, events_data):

    logger.info("Processing events for app_name: {}, start_time: {}, end_time: {}, number of events: {}".format(app_name, start_time, end_time, len(events_data)))

    # 1. List tokens in this event chunk
    tokens = list(set(event['token'] for event in events_data))
    
    # 2. List product ids in this event chunk
    product_ids = list(set(event['product_id'] for event in events_data if event['product_id']))

    # extract all product ids from database with the same app_name
    existing_product_ids = set(Item.objects.filter(app_name=app_name).values_list('product_id', flat=True))
    new_product_ids = [pid for pid in product_ids if pid not in existing_product_ids]

    # 3. List session keys in this event chunk
    session_keys = list(set(event['session'] for event in events_data))
    
    # update database
    if len(new_product_ids) > 0:
        # update products and users in parallel using celery
        
        g1 = group(update_products.si(new_product_ids,app_name,events_data),update_users.si(tokens,events_data,app_name))
        # chain update_user_activities to g1
        g2 = chain(g1,group(update_user_activities.si(tokens,events_data,app_name),update_sessions.si(session_keys,events_data,app_name)))
     
    else:
        # chain user and user_activities
        g1 = group(update_users.si(tokens,events_data,app_name))
        g2 = chain(g1,group(update_user_activities.si(tokens,events_data,app_name),update_sessions.si(session_keys,events_data,app_name)))
    
    g2()
    

@shared_task
def update_database():    
    start_time = datetime.now() - timedelta(seconds=TIME_CHUNK)
    end_time = datetime.now()

    events = Event.objects.filter(logged_time__gte=start_time, logged_time__lte=end_time)
    events_data_by_app_name = {}

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
            'logged_time': event.logged_time.isoformat() if event.logged_time else None,
        }

        if event.app_name not in events_data_by_app_name:
            events_data_by_app_name[event.app_name] = []
        
        events_data_by_app_name[event.app_name].append(event_data)
    
    for app_name, events_data in events_data_by_app_name.items():
        update_database_chunk(start_time, end_time, app_name, events_data)



   


    
        
        
        
                
            
