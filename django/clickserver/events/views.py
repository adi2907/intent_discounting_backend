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

IDLE_TIME = 5*60 # 1 minutes
# accept post requests from the xhttp request and save the data to the database
@csrf_exempt
def events(request):
    
    if request.method == 'GET':
        return HttpResponse("Hello, world. You're at the events index.")
    if request.method == 'POST':
        
        data = json.loads(request.body)
        events = data.get('events', [])
        session_id = data.get('session_id')
        if not session_id:
            session_id = uuid4().hex
        lastEventTimestamp = data.get('lastEventTimestamp')
        alme_user_token = data.get('alme_user_token')
        current_time = datetime.now()
        if lastEventTimestamp and (current_time - datetime.fromtimestamp(int(lastEventTimestamp))).total_seconds() > IDLE_TIME:
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
            event.logged_time = datetime.now()
            #save the event object to the database
            event.save()

        return JsonResponse({'session_id': session_id, 'success': True})
    
