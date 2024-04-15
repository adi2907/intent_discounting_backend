from django.core.management.base import BaseCommand
import requests
from django.utils import timezone
from apiresult.models import *
from events.models import *
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd

class Command(BaseCommand):
    help = "Process purchases"

    def handle(self, *args, **options):
        base_url = 'https://almeapp.co.in/testAlmePayload/'
        start_id = 17848
        end_id = 16000
        batch_size = 100
        results = []

        for start in range(start_id, end_id - 1, -batch_size):
            end = max(start - batch_size + 1, end_id)
            batch_results = self.process_batch(base_url, start, end)
            results.extend(batch_results)

            successes = sum(1 for result in batch_results if result['success'])
            failures = len(batch_results) - successes

            self.stdout.write(self.style.SUCCESS(f'Batch processed: {start} - {end}'))
            self.stdout.write(self.style.SUCCESS(f'Successes: {successes}, Failures: {failures}'))

        df = pd.DataFrame(results)
        df.to_excel('output.xlsx', index=False)
        self.stdout.write(self.style.SUCCESS('Output saved to output.xlsx'))

    def process_batch(self, base_url, start, end):
        batch_results = []

        with ThreadPoolExecutor() as executor:
            futures = []
            for id in range(start, end - 1, -1):
                url = base_url + str(id)
                future = executor.submit(self.process_request, url, id)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                batch_results.append(result)

        return batch_results

    def process_request(self, url, id):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                payload = response.json()['API Payload']
                cart_token = payload['cart_token']

                alme_user_token = payload.get('alme_user_token')
                app_name = payload.get('app_name')
                session_id = payload.get('session_id')

                if not session_id:
                    return {'id': id, 'success': False, 'error': 'No session_id found'}

                try:
                    user = User.objects.get(token=alme_user_token)
                except User.DoesNotExist:
                    return {'id': id, 'success': False, 'error': 'User does not exist'}

                products = payload.get('products', [])
                if not products:
                    return {'id': id, 'success': False, 'error': 'No products found'}

                for product in products:
                    product_id = product.get('product_id')
                    item = Item.objects.filter(product_id=product_id).first()
                    created_at_str = payload.get('timestamp', '')

                    if created_at_str:
                        created_at_time = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        return {'id': id, 'success': False, 'error': 'No timestamp found'}

                    event = Event(
                        token=alme_user_token,
                        session=session_id,
                        user_login=payload.get('user_login', ''),
                        user_id=payload.get('user_id', ''),
                        click_time=created_at_time,
                        user_regd=payload.get('user_regd', ''),
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
                        created_at=created_at_time,
                        cart_token=cart_token,
                        quantity=product.get('product_qty'),
                        logged_time=datetime.now()
                    )
                    purchase.save()

                return {'id': id, 'success': True}

            else:
                return {'id': id, 'success': False, 'error': f'Invalid response. Status code: {response.status_code}'}

        except Exception as e:
            return {'id': id, 'success': False, 'error': str(e)}
