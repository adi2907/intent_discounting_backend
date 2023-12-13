from django.shortcuts import render
from datetime import datetime, timedelta
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
from .models import Event
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
logger = logging.getLogger(__name__)
from uuid import uuid4
from apiresult.utils.config import *
from apiresult.models import *


# accept post requests from the xhttp request and save the data to the database
@csrf_exempt
def events(request):
    
    if request.method == 'GET':
        return HttpResponse(" This is the events url. Please send a post request to this url")
    if request.method == 'POST':
        
        data = json.loads(request.body)
        events = data.get('events', [])
        session_id = data.get('session_id')
        if not session_id:
            session_id = uuid4().hex
        lastEventTimestamp = data.get('lastEventTimestamp')
        alme_user_token = data.get('alme_user_token')
        current_time = datetime.now()
        if lastEventTimestamp and (current_time - datetime.fromtimestamp(int(lastEventTimestamp))).total_seconds() > (SESSION_IDLE_TIME*60):
            session_id = uuid4().hex
            
        for item in events:
            event = Event()
            event.token = alme_user_token
            event.session = session_id
            event.user_login = item.get('user_login', '')
            event.user_id = item.get('user_id', '')

            # convert epoch time to datetime in 'yyyy-mm-dd hh:mm:ss' format
            event.click_time = datetime.fromtimestamp(item.get('click_time', 0)).strftime('%Y-%m-%d %H:%M:%S')
            event.user_regd = item.get('user_regd','')
            event.event_type = item.get('event_type', '')
            event.event_name = item.get('event_name', '')
            event.source_url = item.get('source_url', '')
            event.app_name = item.get('app_name','')
            event.click_text = item.get('click_text','')
            event.product_name = item.get('product_name', '')
            event.product_id = item.get('product_id', '')
            event.product_price = item.get('product_price', '')
            event.logged_time = datetime.now()
            #save the event object to the database
            event.save()

        return JsonResponse({'session_id': session_id, 'success': True})
    
@csrf_exempt
def purchase(request):
    # don't allow get requests
    if request.method == 'GET':
        return HttpResponse("This is the purchase url. Please send a post request to this url.")
    if request.method == 'POST':
        data = json.loads(request.body)
        cart_token = data.get('cart_token')
        
        if not cart_token:
            return JsonResponse({'success': False, 'message': 'Cart token is empty'})
        
        if Purchase.objects.filter(cart_token=cart_token).exists():
            return JsonResponse({'success': False, 'message': 'Cart token already exists'})
        
        alme_user_token = data.get('alme_user_token')  
        app_name = data.get('app_name')
        # get click_time as this timestamp in ('%Y-%m-%d %H:%M:%S') format
        click_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # find the user
        try:
            user = User.objects.get(token=alme_user_token)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User does not exist'})
        # get product details as a list and iterate through the list
        products = data.get('products', [])
        for product in products:
            product_id = product.get('product_id')
            product_name = product.get('product_name')
            product_price = product.get('product_price')
            product_qty = product.get('product_qty')

            # get item 
            item, created = Item.objects.get_or_create(product_id=product_id,
                                defaults={'name': product.get('product_name'),
                                'price': product.get('product_price')})
            # create a new purchase event
            event = Event()
            event.token = alme_user_token
            event.session = data.get('session_id')
            event.user_login = data.get('user_login', '')
            event.user_id = data.get('user_id', '')
            click_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            event.click_time = click_time
            event.user_regd = data.get('user_regd','')
            event.event_type = 'purchase'
            event.event_name = 'purchase'
            
            event.source_url = ''
            event.app_name = app_name
            event.click_text = ''
            event.product_name = product_name
            event.product_id = product_id
            event.product_price = product_price
            event.logged_time = datetime.now()
            #save the event object to the database
            event.save()
            # create a new purchase object
            purchase = Purchase()
            purchase.user = user
            purchase.item = item
            purchase.app_name = app_name
            purchase.created_at = click_time
            purchase.cart_token = cart_token
            purchase.quantity = product_qty
            purchase.logged_time = datetime.now()

            purchase.save()


            
            


