from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Count
import json
import logging
import os

from apiresult.models import IdentifiedUser, User, Visits, Cart, Purchase, Item

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = " Sends a daily email summary of cart and visit activity of identified users"
    def handle(self, *args, **kwargs):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)

        # Get all IdentifiedUsers, regardless of their logged_time
        identified_users = IdentifiedUser.objects.all()

        # Prepare the data for pandas DataFrame
        data = {
            'Name': [],
            'Phone': [],
            'Email': [],
            'Registered User ID': [],
            'Registered Date': [],
            'Product Visits': [],
            'Product Carts': []
        }

        for identified_user in identified_users:
            user_name = identified_user.name
            user_phone = identified_user.phone
            user_email = identified_user.email
            registered_user_id = identified_user.registered_user_id
            registered_date = identified_user.logged_time

            if identified_user.registered_user_id.strip() != '':
                try:
                    user = User.objects.filter(registered_user_id=identified_user.registered_user_id).first()
                    if user is None:
                        logging.info(f"No User exists with registered_user_id: {identified_user.registered_user_id}")
                        continue
                    user_email = user.user_login
                except Exception as e:
                    logging.error(f"An error occurred: {str(e)}")
                    continue

            tokens = identified_user.tokens
            users = User.objects.filter(token__in=tokens)
            # Fetch only visits from the last 24 hours
            visits = Visits.objects.filter(user__in=users, created_at__gte=start_time, created_at__lte=end_time)

            product_visits = list(visits.values('item__product_id', 'item__name').annotate(visit_count=Count('item')).order_by('-visit_count'))
            product_visits = json.dumps(product_visits).replace(',', '|')

            # Fetch only carts from the last 24 hours
            carts = Cart.objects.filter(user__in=users, created_at__gte=start_time, created_at__lte=end_time)
            product_carts = carts.values('item__product_id', 'item__name')
            product_carts_list = list(product_carts)  # Convert queryset to a list of dictionaries
            product_carts = json.dumps(product_carts_list).replace(',', '|')  # Pass the list of dictionaries to json.dumps

            # if both product_visits and product_carts are empty, skip this user
            if product_visits == '[]' and product_carts == '[]':
                continue
            # Append the user data
            data['Name'].append(user_name)
            data['Phone'].append(user_phone)
            data['Email'].append(user_email)
            data['Registered User ID'].append(registered_user_id)
            data['Registered Date'].append(registered_date.strftime("%Y-%m-%d"))
            data['Product Visits'].append(product_visits)
            data['Product Carts'].append(product_carts)

        # Create pandas DataFrame
        df = pd.DataFrame(data)

        # Write the DataFrame to an Excel file
        date_today = datetime.now().strftime("%Y-%m-%d")
        excel_file_name = f'identified_user_activity_{date_today}.xlsx'
        df.to_excel(excel_file_name, index=False)
        
        # Define email parameters
        email = EmailMessage(
        f"Identified user activity - {date_today}",
        'Please find the attached file for the daily identified user activity summary.',
        'aditya@almeapp.co',  # Replace with your actual email
        ['helloworld.adi@gmail.com'],  # Replace with the recipient's email
        )

        # Attach the excel file to the email
        email.attach_file(excel_file_name)

        # Send the email
        email.send()

        # Delete the Excel file after sending the email
        if os.path.exists(excel_file_name):
            os.remove(excel_file_name)
