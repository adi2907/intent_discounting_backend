import datetime
from django.shortcuts import render
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.shortcuts import render
from .models import Event
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
logger = logging.getLogger(__name__)

IDLE_TIME = 60*30 # 30 minutes
# accept post requests from the xhttp request and save the data to the database
@csrf_exempt
def events(request):
    if request.method == 'GET':
#        logger.info("Got a get request")
        return HttpResponse("Hello, world. You're at the events index.")

    if request.method == 'POST':
         # Ensure session key exists
        if request.session.session_key is None:
            request.session.create()
        unique_session_id = request.session.session_key

        now = datetime.now()
        last_active = request.session.get('last_active')
        # print session key and last active time
        print('Session key:', unique_session_id)
        if last_active is None:
            last_active = now
        idle_period = timedelta(seconds=IDLE_TIME)
        if last_active:
            last_active = datetime.strptime(last_active, '%Y-%m-%d %H:%M:%S.%f')
        if now - last_active > idle_period:
            # Create a new session identifier
            request.session.create()
            unique_session_id = request.session.session_key

        request.session['last_active'] = str(now)

        # json loads the request body
        data = json.loads(request.body)
        # Iterate in the data and save each item as an event
        for item in data:
            event = Event()
            event.token = item.get('token', '')
            event.session = unique_session_id
            event.user_login = item.get('user_login', '')
            event.user_id = item.get('user_id', '')

            # convert epoch time to datetime in 'yyyy-mm-dd hh:mm:ss' format
            event.click_time = datetime.datetime.fromtimestamp(item.get('click_time', 0)).strftime('%Y-%m-%d %H:%M:%S')
            # convert the time to local time    
            #event.click_time = datetime.datetime.strptime(event.click_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=5, minutes=30)
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
            event.product_description = item.get('product_description', '')
            event.logged_time = datetime.datetime.now()
            #save the event object to the database
            event.save()

        return HttpResponse('success')
    
