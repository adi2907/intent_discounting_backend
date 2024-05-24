from django.core.management.base import BaseCommand
import json
import csv
import requests
from apiresult.models import *
from events.models import EventUrlParameters
from datetime import datetime

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file containing purchase IDs')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        with open(csv_file, 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            ids = [row[0] for row in reader]
            # Compose standard requests headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            for id in ids:
                url = f"https://almeapp.co.in/full_order/{id}"
                print("Fetching order info from: ", url)
                response = requests.get(url, headers=headers)
                data = response.json()
                
                if data.get('status') and data.get('data', {}).get('statusCode') == 200:
                    order_info = data['data']['body']['order']
                    tracking_params = {}
                    for attr in order_info.get('note_attributes', []):
                        if attr['name'] in ['gclid', 'fbclid', 'ad_id']:
                            tracking_params[attr['name']] = attr['value']

                    if tracking_params:
                        self.process_order(order_info, tracking_params)

    def process_order(self, order_info, tracking_params):
        created_at_str = order_info['created_at']
        created_at_datetime = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%S%z')
         # Convert to naive datetime by removing timezone
        created_at_naive = created_at_datetime.replace(tzinfo=None)
        user = None

        # Try to match and process based on tracking parameters
        for param, value in tracking_params.items():
            matches = EventUrlParameters.objects.filter(**{param: value, 'click_time__date': created_at_naive.date()})
            if matches.exists():
                event_url = matches.first()
                print("Match found for tracking param: ", param)
                user = User.objects.filter(token=event_url.token,app_name='millet-amma-store.myshopify.com').first()
                print("User: ", user)

                break
            else:
                print("No match found for tracking param: ", param)
                return
          
        cart_token = order_info.get('cart_token', '')
        if cart_token == '':
            for attr in order_info.get('note_attributes', []):
                if attr['name'] == 'cart_token':
                    cart_token = attr['value']
                    break
       
        # Process each line item and create purchases
        for item in order_info['line_items']:
            product_id = str(item['product_id'])
            print("Processing product: ", product_id)
            db_item = Item.objects.filter(product_id=product_id).first()
            print("Item: ", db_item)
            if db_item:
                Purchase.objects.create(
                    user=user,
                    item=db_item,
                    app_name='millet-amma-store.myshopify.com',  
                    cart_token=cart_token,
                    created_at=created_at_naive,
                    quantity=item['quantity']
                )

        # Update the session in Sessions table
        session = Sessions.objects.filter(session_key=event_url.session)
        if session.exists():
            print("Updating session: ", event_url.session)
            # update has_purchased to 1 for the session
            session.update(has_purchased=True)
        
        if user:
            self.update_user_sessions(user)

   
    def update_user_sessions(self, user):
        # Get the last four sessions excluding the current one
        last_sessions = Sessions.objects.filter(user=user).order_by('-session_start')[1:5]
        purchase_last_4_sessions = any(session.has_purchased for session in last_sessions)
        purchase_prev_session = last_sessions.first().has_purchased if last_sessions.exists() else False

        # Update user fields based on the sessions queried
        user.purchase_last_4_sessions = 1 if purchase_last_4_sessions else 0
        user.purchase_prev_session = 1 if purchase_prev_session else 0
        user.save()

       
    

    
                    

