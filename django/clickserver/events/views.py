import re
from django.shortcuts import render
from datetime import datetime, timedelta
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
from .models import Event
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_datetime
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
    

# Example usage
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
            logger.info("Processing webhook purchase request")
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
            total_line_items_price = sum(float(item['price']) * item['quantity'] for item in data.get('line_items', []))
            discount_codes = [{'code': code['code'], 'amount': code['amount']} for code in data.get('discount_codes', [])]

            for line_item in data.get('line_items', []):
                line_item_price_per_item = float(line_item['price'])
                line_item_quantity = line_item['quantity']
                line_item_total_price = line_item_price_per_item * line_item_quantity
                line_item_discount = (line_item_total_price / total_line_items_price) * total_discount if total_line_items_price > 0 else 0

                purchase = Purchase(
                    cart_token=cart_token,
                    user_login=user_login,
                    user_id=user_id,
                    created_at=created_at,
                    app_name=app_name,
                    product_id=str(line_item.get('product_id')),
                    product_name=line_item.get('title'),
                    product_price=str(line_item_price_per_item),
                    product_quantity=str(line_item_quantity),
                    discount_codes=json.dumps(discount_codes),
                    discount_amount=str(line_item_discount),
                    logged_time=None  # Set this as needed
                )
                purchase.save()

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


