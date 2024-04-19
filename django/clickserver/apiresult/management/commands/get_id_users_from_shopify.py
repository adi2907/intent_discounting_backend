from django.core.management.base import BaseCommand
from datetime import datetime
import requests
from apiresult.models import IdentifiedUser  

class Command(BaseCommand):
    help = 'Get all the identified user details from Shopify'

    def handle(self, *args, **options):
        users = IdentifiedUser.objects.filter(app_name='millet-amma-store.myshopify.com', email__isnull=True, name__isnull=True, phone__isnull=True)
        initial_count = users.count()
        updated_count = 0

        self.stdout.write(f"Starting to update details for {initial_count} users.")

        for user in users:
            url = f"https://almeapp.co.in/mapCustomer?shop_name=millet-amma-store.myshopify.com&customer_id={user.registered_user_id}"
            self.stdout.write(f"Requesting details for user ID {user.registered_user_id} from URL: {url}")

            try:
                response = requests.get(url)
                response.raise_for_status()  # Raises an HTTPError for bad responses

                # Logging the raw response data
                self.stdout.write(f"Response status code: {response.status_code}")
                self.stdout.write(f"Response content: {response.text}")

                data = response.json()

                if data and data.get('status') and 'customer' in data['response']:
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
                else:
                    self.stdout.write(self.style.WARNING(f"No valid customer data for user ID: {user.registered_user_id}"))
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Failed to fetch user details for {user.registered_user_id}: {str(e)}"))
            except ValueError:  # Includes JSONDecodeError
                self.stdout.write(self.style.ERROR(f"Invalid JSON response for user ID: {user.registered_user_id}"))

        self.stdout.write(self.style.SUCCESS(f"Total users processed: {initial_count}"))
        self.stdout.write(self.style.SUCCESS(f"Total users updated: {updated_count}"))
