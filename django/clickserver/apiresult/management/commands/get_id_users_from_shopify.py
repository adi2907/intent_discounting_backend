from django.core.management.base import BaseCommand
from datetime import datetime
import requests
from apiresult.models import IdentifiedUser  

class Command(BaseCommand):
    help = 'Get all the identified user details from Shopify'

    def handle(self, *args, **options):
        # Get all users with missing details and registered under 'millet-amma-store.myshopify.com'
        users = IdentifiedUser.objects.filter(app_name='millet-amma-store.myshopify.com', email__isnull=True, name__isnull=True, phone__isnull=True)
        initial_count = users.count()  # Total users with missing details
        updated_count = 0  # Counter for users successfully updated

        self.stdout.write(f"Starting to update details for {initial_count} users.")

        for user in users:
            # Construct API URL for each user
            url = f"https://almeapp.co.in/mapCustomer?shop_name=millet-amma-store.myshopify.com&customer_id={user.registered_user_id}"
            response = requests.get(url)
            data = response.json()

            # Check if the API call was successful and the required data exists
            if data['status'] and 'customer' in data['response']:
                customer = data['response']['customer']
                email = customer.get('email')
                first_name = customer.get('first_name')
                last_name = customer.get('last_name')
                name = f"{first_name} {last_name}" if first_name and last_name else None
                phone = customer.get('phone')

                # Update the existing user entry
                user.email = email
                user.name = name
                user.phone = phone
                user.logged_time = datetime.now()
                user.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Updated user: {user.name}"))

        self.stdout.write(self.style.SUCCESS(f"Total users processed: {initial_count}"))
        self.stdout.write(self.style.SUCCESS(f"Total users updated: {updated_count}"))
