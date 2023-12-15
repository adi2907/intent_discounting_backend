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
# Example usage
# curl -X POST \
#   http://almeapp.com/events/purchase/ \
#   -H 'Content-Type: application/json' \
#   -d '{
#         "cart_token": "carttoken123",
#         "alme_user_token": "539311cienx",
#         "app_name": "almestore1.myshopify.com",
#         "session_id":"485d2ac7d7e4432eb576b614ea65f407",
#         "products": [
#             {
#                 "product_id": "123",
#                 "product_name": "Product A",
#                 "product_price": 100,
#                 "product_qty": 2
#             },
#             {
#                 "product_id": "456",
#                 "product_name": "Product B",
#                 "product_price": 200,
#                 "product_qty": 1
#             }
#         ]
#       }'




# Responses: 
# Errors:
# {'success': False, 'message': 'Cart token is empty'}
# {'success': False, 'message': 'Cart token already exists'}
# {'success': False, 'message': 'Session id is empty'}
# {'success': False, 'message': 'User does not exist'}
# {'success': False, 'message': 'Error processing request: <error message>'}

# Success:
# {'success': True, 'message': 'Purchase successful'}





@csrf_exempt
def purchase(request):
    if request.method == 'GET':
        return JsonResponse({'success': False, 'message': 'This is the purchase url. Please send a post request to this url'})

    if request.method == 'POST':
        data = json.loads(request.body)
        cart_token = data.get('cart_token')
        
        if not cart_token:
            return JsonResponse({'success': False, 'message': 'Cart token is empty'})
        
        if Purchase.objects.filter(cart_token=cart_token).exists():
            return JsonResponse({'success': False, 'message': 'Cart token already exists'})

        alme_user_token = data.get('alme_user_token')  
        app_name = data.get('app_name')
        session_id = data.get('session_id')

        if not session_id:
            return JsonResponse({'success': False, 'message': 'Session id is empty'})

        try:
            user = User.objects.get(token=alme_user_token)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User does not exist'})

        products = data.get('products', [])
        try:
            for product in products:
                item, _ = Item.objects.get_or_create(
                    product_id=product.get('product_id'),
                    defaults={
                        'name': product.get('product_name'),
                        'price': product.get('product_price')
                    }
                )
                
                event = Event(
                    token=alme_user_token,
                    session=session_id,
                    user_login=data.get('user_login', ''),
                    user_id=data.get('user_id', ''),
                    click_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    user_regd=data.get('user_regd', ''),
                    event_type='purchase',
                    event_name='purchase',
                    source_url='',
                    app_name=app_name,
                    click_text='',
                    product_name=product.get('product_name'),
                    product_id=product.get('product_id'),
                    product_price=product.get('product_price'),
                    logged_time=datetime.now()
                )
                event.save()

                purchase = Purchase(
                    user=user,
                    item=item,
                    app_name=app_name,
                    created_at=datetime.now(),
                    cart_token=cart_token,
                    quantity=product.get('product_qty'),
                    logged_time=datetime.now()
                )
                purchase.save()
            
            return JsonResponse({'success': True, 'message': 'Purchase successful'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error processing request: {str(e)}'})
            
        


            
            


