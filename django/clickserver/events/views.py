import re
from django.shortcuts import render
from datetime import datetime, timedelta
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
from .models import Event,ShopifyPurchase
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import json
import logging
logger = logging.getLogger(__name__)
from uuid import uuid4
from apiresult.utils.config import *
from apiresult.models import *
import hashlib

#Example usage
'''
curl -X POST https://almeapp.com/events \
-H "Content-Type: application/json" \
-H "Origin: https://www.almeapp.co.in" \
-d '{
    "shop": "almestore1.myshopify.com",
    "events": [
        {
            "user_login": null,
            "user_id": null,
            "user_regd": "",
            "click_time": 1709702150,
            "click_text": "",
            "event_type": "page_load",
            "event_name": "page_load",
            "source_url": "https://almestore1.myshopify.com/",
            "app_name": "almestore1.myshopify.com",
            "product_id": null,
            "product_name": null,
            "product_price": null
        },
    ],
    "session_id": "1b562bf038ac4bdf8a3e8536511ce711",
    "alme_user_token": "2789929o260",
    "lastEventTimestamp": "1708336987"
}'
'''
# accept post requests from the xhttp request and save the data to the database
@csrf_exempt
def events(request):
    
    if request.method == 'GET':
        return HttpResponse(" This is the events url. Please send a post request to this url")
    if request.method == 'POST':
        session_flag = False
        data = json.loads(request.body)
        events = data.get('events', [])
        session_id = data.get('session_id')
        if not session_id:
            raw_session_id = f"{data.get('app_name', 'default_app')}_{datetime.now().isoformat()}"
            session_id = hashlib.sha1(raw_session_id.encode()).hexdigest()
        lastEventTimestamp = data.get('lastEventTimestamp')
        alme_user_token = data.get('alme_user_token')
        current_time = datetime.now()
        # print last event timestamp, session_id and current time and user
        # get the app_name from the first event
        app_name = events[0].get('app_name', 'default_app')
        if app_name == 'almestore1.myshopify.com':
            logger.info(f"Last event timestamp: {lastEventTimestamp}, Session id: {session_id}, Current time: {current_time}, User: {alme_user_token}, Events: {events}")
        if lastEventTimestamp and (current_time - datetime.fromtimestamp(int(lastEventTimestamp))).total_seconds() > (SESSION_IDLE_TIME*60):
            # print the existing session id
            logger.info(f"Session id: {session_id} is expired. Creating new session id.")
            raw_session_id = f"{data.get('app_name', 'default_app')}_{datetime.now().isoformat()}"
            session_id = hashlib.sha1(raw_session_id.encode()).hexdigest()
            session_flag = True
        if session_flag:
            logger.info(f"New session id: {session_id} created")

        
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
            # temp fix for desi_sandook, should be removed later
            if event.app_name == 'desi_sandook':
                event.app_name = 'desisandook.myshopify.com'
            event.click_text = item.get('click_text','')
            event.product_name = item.get('product_name', '')
            event.product_id = item.get('product_id', '')
            event.product_price = item.get('product_price', '')
            event.logged_time = datetime.now()
            #save the event object to the database
            event.save()
        if session_flag:
            logger.info("Returning new session id {} to the user".format(session_id))
        return JsonResponse({'session_id': session_id, 'success': True})
    
    

#Example usage
# curl -X POST \
#   https://almeapp.com/events/shopify_webhook_purchase \
#   -H 'Content-Type: application/json' \
#   -H 'Origin: https://www.almeapp.co.in' \
#   -d '{
#         "cart_token": "carttoken123",
#         "email": "user@example.com",
#         "user_id": "12345",
#         "created_at": "2024-01-20T12:00:00-05:00",
#         "line_items": [
#             {
#                 "product_id": "123",
#                 "title": "Product A",
#                 "price": "100",
#                 "quantity": 2
#             },
#             {
#                 "product_id": "456",
#                 "title": "Product B",
#                 "price": "200",
#                 "quantity": 1
#             }
#         ],
#         "total_discounts": "50.00",
#         "discount_codes": [
#             {
#                 "code": "DISCOUNT10",
#                 "amount": "10.00"
#             }
#         ]
#       }'

# Responses:
# Success: HTTP 200 OK
# Errors:
# HTTP 500 Internal Server Error: Error processing request.
# HTTP 405 Method Not Allowed: Invalid request method.

# Note: This endpoint is intended to be called by Shopify with the appropriate data format.
# The data should match the format of a Shopify order webhook payload.



@csrf_exempt
def shopify_webhook_purchase(request):
    if request.method == 'GET':
        return HttpResponse("This is the shopify webhook purchase url. Please send a post request to this url")
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_token = data.get('cart_token')
            user_login = data.get('email')
            user_id = data.get('user_id')
            created_at_str = data.get('created_at')
            if not isinstance(created_at_str, str) or not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', created_at_str):
                return JsonResponse({'error': 'created_at must be a string in ISO format'}, status=400)
            created_at = parse_datetime(created_at_str)
            if created_at:
                created_at += timedelta(hours=5, minutes=30)  # Convert to IST
            app_name = request.META.get('HTTP_X_SHOPIFY_SHOP_DOMAIN', 'Unknown Store')

            total_discount = float(data.get('total_discounts', '0.0'))
            # if line items are not present, return error response
            line_items = data.get('line_items', [])
            if not line_items:
                return JsonResponse({'error': 'line_items must be present'}, status=400)
            total_line_items_price = sum(float(item['price']) * item['quantity'] for item in line_items)
            discount_codes = data.get('discount_codes', [])

            discount_codes_processed = []
            # if discount codes is not empty, process the discount codes
            if discount_codes != [] and discount_codes != None:
                discount_codes_processed = [{'code': code['code'], 'amount': code['amount']} for code in discount_codes]

            for line_item in data.get('line_items', []):
                line_item_price_per_item = float(line_item['price'])
                line_item_quantity = line_item['quantity']
                line_item_total_price = line_item_price_per_item * line_item_quantity
                line_item_discount = (line_item_total_price / total_line_items_price) * total_discount if total_line_items_price > 0 else 0

                shopify_purchase = ShopifyPurchase(
                    cart_token=cart_token,
                    user_login=user_login,
                    user_id=user_id,
                    created_at=created_at,
                    app_name=app_name,
                    product_id=str(line_item.get('product_id')),
                    product_name=line_item.get('title'),
                    product_price=str(line_item_price_per_item),
                    product_quantity=str(line_item_quantity),
                    discount_codes=json.dumps(discount_codes_processed),
                    discount_amount=str(line_item_discount),
                    logged_time=None  # Set this as needed
                )
                shopify_purchase.save()

            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f'Error processing webhook purchase request: {str(e)}')
            return HttpResponse(status=500)
    else:
        return HttpResponse(status=405)





# Example usage
# curl -X POST \
#   https://almeapp.com/events/purchase/ \
#   -H 'Content-Type: application/json' \
#   -H 'Origin: https://www.almeapp.co.in' \
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
                product_id = product.get('product_id')
                item = Item.objects.filter(
                product_id=product_id,
                app_name=app_name
                ).first()

                if not item:
                    item = Item.objects.create(
                        product_id=product_id,
                        app_name=app_name,
                        name=product.get('product_name'),
                        price=product.get('product_price')
                    )
                created_at_str = data.get('created_at','')
                # if created_at is not present, use current time
                if created_at_str == '':
                    created_at_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    created_at_time = created_at_str
                event = Event(
                    token=alme_user_token,
                    session=session_id,
                    user_login=data.get('user_login', ''),
                    user_id=data.get('user_id', ''),       
                    click_time=created_at_time,
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
            

# Example usage
# curl -X POST \
#   https://almeapp.com/events/add_cart/ \
#   -H 'Content-Type: application/json' \
#   -H 'Origin: https://www.almeapp.co.in' \
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
# {'success': True, 'message': 'Add to cart successful'}




@csrf_exempt
def add_cart(request):
    if request.method == 'GET':
        return JsonResponse({'success': False, 'message': 'This is the add cart url. Please send a post request to this url'})

    if request.method == 'POST':
        data = json.loads(request.body)
        cart_token = data.get('cart_token')
        
        if not cart_token:
            return JsonResponse({'success': False, 'message': 'Cart token is empty'})
        
        if Cart.objects.filter(cart_token=cart_token).exists():
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
                product_id = product.get('product_id')
                item = Item.objects.filter(
                product_id=product_id,
                app_name=app_name
                ).first()

                if not item:
                    item = Item.objects.create(
                        product_id=product_id,
                        app_name=app_name,
                        name=product.get('product_name'),
                        price=product.get('product_price')
                    )
                
                event = Event(
                    token=alme_user_token,
                    session=session_id,
                    user_login=data.get('user_login', ''),
                    user_id=data.get('user_id', ''),
                    click_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    user_regd=data.get('user_regd', ''),
                    event_type='add_cart',
                    event_name='add_cart',
                    source_url='',
                    app_name=app_name,
                    click_text='',
                    product_name=product.get('product_name'),
                    product_id=product.get('product_id'),
                    product_price=product.get('product_price'),
                    logged_time=datetime.now()
                )
                event.save()

                cart = Cart(
                    user=user,
                    item=item,
                    app_name=app_name,
                    created_at=datetime.now(),
                    cart_token=cart_token,
                    quantity=product.get('product_qty'),
                    logged_time=datetime.now()
                )
                cart.save()
            
            return JsonResponse({'success': True, 'message': 'Add to cart successful'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error processing request: {str(e)}'})  


