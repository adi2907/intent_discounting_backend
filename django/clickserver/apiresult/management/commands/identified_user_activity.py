from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
import csv
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from django.db.models import Count


from apiresult.models import IdentifiedUser, User, Visits, Cart, Purchase, Item

class Command(BaseCommand):
    help = " Sends a daily summary of cart and visit activity of identified users"
    def handle(self, *args, **kwargs):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        '''
        We have 2 kinds of identified users. 1. Registered users who have a user_id.
        2. Non registered users who have shared their contact
        '''
        #1.  get all registered users where user_id is not null or empty
        registered_users = IdentifiedUser.objects.filter(user_id__isnull=False).exclude(user_id__exact='')
        user_ids = registered_users.values_list('user_id', flat=True)
        






        

