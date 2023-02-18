from .models import Item,User, Visits, Cart,IdentifiedUser
from events.models import Event
import numpy as np
from django.db.models import Q

from celery import shared_task

@shared_task
def update_database():

    # for each app name
    # TODO: add app_name model and iterate from there
    for app_name in Event.objects.values_list('app_name', flat=True).distinct():
        
        # check if User database is empty for the app_name
        if User.objects.filter(app_name=app_name).count() == 0:
            events = Event.objects.filter(app_name=app_name)
            print(len(events))
        else:
            # extract the last updated time from the database
            last_updated = User.objects.filter(app_name=app_name).order_by('-last_updated')[0].last_updated
            # get all events after the last updated time for the app
            events = Event.objects.filter(click_time__gt=last_updated).filter(app_name=app_name)
            print(len(events))
            

        # extract all the tokens or customers
        tokens = events.values_list('token', flat=True).distinct()
        print(len(tokens))
        
        # 1. extract all new item ids and add to Item database
        product_ids = events.values_list('product_id', flat=True).distinct()
        product_ids = product_ids.exclude(product_id__isnull=True).exclude(product_id='').exclude(product_id=0)

        print(len(product_ids))
        # if there are no new product ids, skip to next app
        if len(product_ids) == 0:
            continue

        # check if product_id exists in database using numpy
        # extract all product ids from database
        db_product_ids = Item.objects.values_list('item_id', flat=True)
        print(len(db_product_ids))
  
        # find the difference between the two arrays
        new_product_ids = np.setdiff1d(product_ids, db_product_ids)
        print(len(new_product_ids))
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

        # 2. update user database, visits and add to carts
        # iterate through each token
        for token in tokens:
            user_events = events.filter(token=token)
            print(len(user_events))
            # get all product ids for the user, excluding blank and null
            product_ids = user_events.values_list('product_id', flat=True).distinct()
            product_ids = product_ids.exclude(product_id__isnull=True).exclude(product_id='').exclude(product_id=0)
            print(len(product_ids))

            # if token exists in database
            if User.objects.filter(token=token).exists():
                user = User.objects.get(token=token)            
                # update user
                user.last_visit = user_events.order_by('-click_time')[0].click_time
                # update user sessions as number of unique sessions 
                user.num_sessions += user_events.values_list('session', flat=True).distinct().count()
                user.last_updated = user_events.order_by('-click_time')[0].click_time
                # update user product and cart visits     
                # iterate through each product id
                for product_id in product_ids:
                    # get all the page load events for the product
                    visit_events = user_events.filter(product_id=product_id).filter(event_type='page_load')
                    print(len(visit_events))
                    # Update each visit
                    for event in visit_events:
                        visit = Visits(user=user, item=Item.objects.get(item_id=product_id), app_name=app_name, created_at=event.click_time)
                        visit.save()
                    
                    # update user product cart, where the event has 'add to' in the click_text
                    # TODO: This needs to be mapped as per the app_name, for now will suffice
                    cart_events = user_events.filter(product_id=product_id).filter(click_text__contains='add to')
                    print(len(cart_events))
                    # Update each cart
                    for event in cart_events:
                        cart = Cart(user=user, item=Item.objects.get(item_id=product_id), app_name=app_name, created_at=event.click_time)
                        cart.save()
            # if token does not exist in database
            else:
                # create a new user
                user = User(token=token, app_name=app_name,num_sessions=0)
                # if user_id exists then update user_id
                
                userid_events = user_events.filter(~Q(user_id__isnull=True)&~Q(user_id='')&~Q(user_id=0))
                print(len(userid_events))
                if userid_events.exists():
                    user.user_id = userid_events[0].user_id
                    user.user_login = userid_events[0].user_login
                    # add to identified user database
                   
                    if IdentifiedUser.objects.filter(user_id=user.user_id).filter(app_name=app_name).exists():
                        # add this token to the identified user by user_id and app_name
                        identified_user = IdentifiedUser.objects.get(user_id=user.user_id, app_name=app_name)
                        # if token does not exist in list of tokens of identifed user
                        
                        if token not in identified_user.tokens:
                            identified_user.tokens.append(token)
                            identified_user.save()
                    else:
                        # create a new identified user
                        identified_user = IdentifiedUser(user_id=user.user_id, app_name=app_name,tokens=[])
                        identified_user.tokens.append(token)
                        identified_user.save()

            
                # update user
                user.first_visit = user_events.order_by('click_time')[0].click_time
                user.last_updated = user_events.order_by('-click_time')[0].click_time
                user.last_visit = user_events.order_by('-click_time')[0].click_time
                user.num_sessions += user_events.values_list('session', flat=True).distinct().count()      
                user.save()

                # iterate through each product id
                for product_id in product_ids:
                    # get all the page load events for the product
                    visit_events = user_events.filter(product_id=product_id).filter(event_type='page_load')
                    print(len(visit_events))
                    # Update each visit
                    for event in visit_events:
                        visit = Visits(user=user, item=Item.objects.get(item_id=product_id), app_name=app_name, created_at=event.click_time)
                        visit.save()
                    
                    cart_events = user_events.filter(product_id=product_id).filter(click_text__contains='add to')
                    print(len(cart_events))
                     # update user product cart, where the event has 'add to' in the click_text
                    # TODO: This needs to be mapped as per the app_name
                    for event in cart_events:
                        cart = Cart(user=user, item=Item.objects.get(item_id=product_id), app_name=app_name, created_at=event.click_time)
                        cart.save()

                

                    
            
   
