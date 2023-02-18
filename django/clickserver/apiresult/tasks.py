
from .models import Item,User, Visits, Cart,IdentifiedUser
from events.models import Event
import numpy as np
from django.db.models import Q
from datetime import timedelta
from celery import shared_task
#from .apilogger import logger
import logging
logger = logging.getLogger(__name__)

@shared_task
def update_products(new_product_ids,events):
    for product_id in new_product_ids:
        item = Item(item_id=product_id)
        # get the last event for the product
        event = events.filter(product_id=product_id).order_by('-click_time')[0]
        item.name = event.product_name
        price = event.product_price
        if price == '':
            price = 0
        item.price = price
        item.categories = event.product_category
        item.app_name = item.app_name
        item.last_updated = event.click_time
        item.save()

@shared_task
def update_user(tokens,events,app_name):
    for user_token in tokens:
        user_events = events.filter(token=user_token)
               
        # if token exists in database
        if User.objects.filter(token=user_token).exists():
            user = User.objects.get(token=user_token)            
            # update user
            user.last_visit = user_events.order_by('-click_time')[0].click_time
            # TODO: update user sessions as number of unique sessions 
            #user.num_sessions += user_events.values_list('session', flat=True).distinct().count()
            user.last_updated = user_events.order_by('-click_time')[0].click_time
            user.save()
        else:
            # add user to database
            user = User(token=user_token, app_name=app_name,num_sessions=0)
            user.first_visit = user_events.order_by('click_time')[0].click_time
            user.last_visit = user_events.order_by('-click_time')[0].click_time
            # TODO: update user sessions as number of unique sessions 
            #user.num_sessions = user_events.values_list('session', flat=True).distinct().count()
            user.last_updated = user_events.order_by('-click_time')[0].click_time
            user.save()
          

@shared_task
def update_user_activities(tokens,events,app_name):
    for user_token in tokens:
        user_events = events.filter(token=user_token)
        # get all product ids for the user, excluding blank and null
        product_ids = user_events.values_list('product_id', flat=True).distinct()
        product_ids = product_ids.exclude(product_id__isnull=True).exclude(product_id='').exclude(product_id=0)
        
        if len(product_ids) == 0:
            return
        user = User.objects.get(token=user_token)
        # iterate through each product id
        for product_id in product_ids:
            # get all the page load events for the product
            visit_events = user_events.filter(product_id=product_id).filter(event_type='page_load')
            
            # Update each visit
            for event in visit_events:
                visit = Visits(user=user, item=Item.objects.get(item_id=product_id), app_name=app_name, created_at=event.click_time)
                visit.save()

            cart_events = user_events.filter(product_id=product_id).filter(click_text__contains='add to')
            # Update each cart
            for event in cart_events:
                cart = Cart(user=user, item=Item.objects.get(item_id=product_id), app_name=app_name, created_at=event.click_time)
                cart.save()
        
        userid_events = user_events.filter(~Q(user_id__isnull=True)&~Q(user_id='')&~Q(user_id=0))
        if userid_events.exists():
            user.user_id = userid_events[0].user_id
            user.user_login = userid_events[0].user_login
            # add to identified user database
            
            if IdentifiedUser.objects.filter(user_id=user.user_id).filter(app_name=app_name).exists():
                # add this token to the identified user by user_id and app_name
                identified_user = IdentifiedUser.objects.get(user_id=user.user_id, app_name=app_name)
                # if token does not exist in list of tokens of identifed user
                
                if user_token not in identified_user.tokens:
                    identified_user.tokens.append(user_token)
                    identified_user.save()
            else:
                # create a new identified user
                identified_user = IdentifiedUser(user_id=user.user_id, app_name=app_name,tokens=[])
                identified_user.tokens.append(user_token)
                identified_user.save()



@shared_task
# update database chunk
def update_database_chunk(events,app_name):
    # extract all the tokens or customers
    tokens = events.values_list('token', flat=True).distinct()

    # 1. Update items database
    product_ids = events.values_list('product_id', flat=True).distinct()
    product_ids = product_ids.exclude(product_id__isnull=True).exclude(product_id='').exclude(product_id=0)

    #if there are no new product ids, skip to next app
    if len(product_ids) == 0:
       logger.info("No products to insert")
       return

    # check if product_id exists in database using numpy
    # extract all product ids from database
    db_product_ids = Item.objects.values_list('item_id', flat=True)

    # find the difference between the two arrays
    new_product_ids = np.setdiff1d(product_ids, db_product_ids)
    # if there are any new product ids, add to database
    if len(new_product_ids) > 0:
        update_products(new_product_ids,events)

    # 2. update user database
    update_user(tokens,events,app_name)

    # 3. update visits & carts and identified users database   
    update_user_activities(tokens,events,app_name)

@shared_task
def update_database():

    # for each app name
    # TODO: add app_name model and iterate from there
    for app_name in Event.objects.values_list('app_name', flat=True).distinct():
        # log the app_name
        logger.info("Updating database for app_name: %s", app_name)
        # start time of events to be added to database
        if User.objects.filter(app_name=app_name).count() == 0:
            start_time = Event.objects.filter(app_name=app_name).order_by('click_time')[0].click_time
        else:
            start_time = User.objects.filter(app_name=app_name).order_by('-last_updated')[0].last_updated
        # end time of events
        end_time = Event.objects.filter(app_name=app_name).order_by('-click_time')[0].click_time

        # get all events in chunks of 5 minutes
        while start_time < end_time:
            # get events between start and end time
            events = Event.objects.filter(click_time__gte=start_time).filter(click_time__lt=start_time+timedelta(minutes=5)).filter(app_name=app_name)
            # log the number of events
            logger.info("Number of events for app_name: %s, start_time: %s, end_time: %s, number of events: %s", app_name, start_time, start_time+timedelta(minutes=5), len(events))
            # update database
            update_database_chunk(events, app_name)
            # update start time
            start_time = start_time+timedelta(minutes=5)
