import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from .models import Event
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

@csrf_exempt
def index(request):
    print("hello")
    return HttpResponse('Hello, world. You are at the events index.')  

# accept post requests from the xhttp request and save the data to the database
@csrf_exempt
def events(request):
    if request.method == 'GET':
        return HttpResponse("Hello, world. You're at the events index.")

    if request.method == 'POST':
        # json loads the request body
        data = json.loads(request.body)
        # Iterate in the data and save each item as an event
        for item in data:
            event = Event()
            event.token = item.get('token', '')
            event.session = item.get('session', '')
            event.user_login = item.get('user_login', '')
            event.user_id = item.get('user_id', '')

            # convert epoch time to datetime in 'yyyy-mm-dd hh:mm:ss' format
            event.click_time = datetime.datetime.fromtimestamp(item.get('click_time', 0)).strftime('%Y-%m-%d %H:%M:%S')
            # convert the time to local time    
            event.click_time = datetime.datetime.strptime(event.click_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=5, minutes=30)
            event.user_regd = item.get('user_regd','')
            event.user_agent = item.get('user_agent', '')
            event.browser = item.get('browser', '')
            event.os = item.get('os', '')
            event.event_type = item.get('event_type', '')
            event.event_name = item.get('event_name', '')
            event.source_url = item.get('source_url', '')
            event.app_name = item.get('app_name','')
            event.click_text = item.get('click_text','')
            event.product_name = item.get('product_name', '')
            event.product_id = item.get('product_id', '')
            event.product_price = item.get('product_price', '')
            event.product_category = item.get('product_category', '')
            event.product_created_date = item.get('product_created_date', '')
            event.logged_time = datetime.datetime.now()
            # convert the time to local time
            event.logged_time = event.logged_time + datetime.timedelta(hours=5, minutes=30)
            #save the event object to the database
            event.save()

        return HttpResponse('success')
    
