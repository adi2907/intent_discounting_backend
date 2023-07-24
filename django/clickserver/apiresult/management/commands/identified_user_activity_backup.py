from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Count
import json
import logging

from apiresult.models import IdentifiedUser, User, Visits, Cart, Purchase, Item

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = " Sends a daily email summary of cart and visit activity of identified users"
    def handle(self, *args, **kwargs):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        identified_users = IdentifiedUser.objects.filter(logged_time__gte=start_time, logged_time__lte=end_time)

        # Prepare the data for pandas DataFrame
        data = {
            'Name': [],
            'Phone': [],
            'Email': [],
            'Product Visits': [],
            'Product Carts': []
        }
        
        for identified_user in identified_users:
            user_name = identified_user.name
            user_phone = identified_user.phone
            user_email = identified_user.email
            
            if identified_user.registered_user_id and identified_user.registered_user_id.strip() != '':
                try:
                    user = User.objects.get(registered_user_id=identified_user.registered_user_id)
                    user_email = user.user_login
                except User.DoesNotExist:
                    logging.info(f"No User exists with registered_user_id: {identified_user.registered_user_id}")
                    continue

            tokens = identified_user.tokens
            users = User.objects.filter(token__in=tokens)
            visits = Visits.objects.filter(user__in=users, created_at__gte=start_time, created_at__lte=end_time)
            
            product_visits = list(visits.values('item__product_id', 'item__name').annotate(visit_count=Count('item')).order_by('-visit_count'))
            product_visits = json.dumps(product_visits).replace(',', '|')

            carts = Cart.objects.filter(user__in=users, created_at__gte=start_time, created_at__lte=end_time)
            product_carts = carts.values('item__product_id', 'item__name')
            product_carts = list(set((item['item__product_id'], item['item__name']) for item in product_carts))
            product_carts = json.dumps(product_carts).replace(',', '|')

            # Append the user data
            data['Name'].append(user_name)
            data['Phone'].append(user_phone)
            data['Email'].append(user_email)
            data['Product Visits'].append(product_visits)
            data['Product Carts'].append(product_carts)

        # Create pandas DataFrame
        df = pd.DataFrame(data)

        # Write the DataFrame to an Excel file
        date_today = datetime.now().strftime("%Y-%m-%d")
        excel_file_name = f'identified_user_activity_{date_today}.xlsx'
        df.to_excel(excel_file_name, index=False)

