from django.core.management.base import BaseCommand
import json
import csv
import requests

class Command(BaseCommand):
    help = 'Update all missing purchases basis some attributes'
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']

        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                table_id = row[0]
                order_url = f'https://almeapp.co.in/full_order/{table_id}'
                purchase_url = f'https://almeapp.co.in/checkPurchaseEvent/{table_id}'


                # Extract cart_token from the order response
                cart_token = self.extract_cart_token(order_url)
                if cart_token:
                    # Get data related to the order
                    data = self.get_order_data(purchase_url)
                    if data:
                        alme_token = data.get('alme_token')
                        shopify_cart_token = data.get('shopify_cart_token')
                        created_at = data.get('created_at')
                        session_id = data.get('session_id')

                        print(f"Table ID: {table_id}")
                        print(f"Alme Token: {alme_token}")
                        print(f"Shopify Cart Token: {shopify_cart_token}")
                        print(f"Created At: {created_at}")
                        print(f"Session ID: {session_id}")
                        print("---") 

                
    def extract_cart_token(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            note_attributes = data['data']['body']['order']['note_attributes']
            for attribute in note_attributes:
                if attribute['name'] == 'cart_token':
                    return attribute['value']

        except (requests.exceptions.RequestException, KeyError, ValueError):
            pass

        return None   


       
    

    
                    

