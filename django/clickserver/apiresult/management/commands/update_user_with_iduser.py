
from django.db import transaction
from django.core.management.base import BaseCommand
from apiresult.models import User, IdentifiedUser
class Command(BaseCommand):
    help = 'Process session data for analysis'

    def handle(self, *args, **options):
        # Call the function to start the update process
        update_user_identified_user()

def update_user_identified_user():
    batch_size = 100
    offset = 0

    while True:
        with transaction.atomic():
            identified_users = IdentifiedUser.objects.all().order_by('id')[offset:offset + batch_size]
            if not identified_users:
                break

            for identified_user in identified_users:
                if identified_user.tokens:
                    print(f'Attempting to update with IdentifiedUser ID {identified_user.id} and tokens {identified_user.tokens}')
                    # Only update users where identified_user is None
                    updated_count = User.objects.filter(token__in=identified_user.tokens, identified_user__isnull=True).update(identified_user=identified_user)
                    print(f'Updated {updated_count} users for IdentifiedUser ID {identified_user.id}')

            offset += batch_size

