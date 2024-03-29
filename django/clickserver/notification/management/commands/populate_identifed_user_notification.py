import pandas as pd
from django.db import connection
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from apiresult.models import *
from .models import IdentifiedUserNotificationThreshold, IdentifiedUserNotification

class Command(BaseCommand):
    help = 'Populate identified user notification'

    def handle(self, *args, **kwargs):
        populate_identified_user_notification()

def populate_identified_user_notification():
    today = datetime.now().date()
    yesterday_start = datetime.combine(today - timedelta(days=1), datetime.min.time())
    yesterday_end = datetime.combine(today - timedelta(days=1), datetime.max.time())

    # Step 1: Find all the sessions for yesterday
    sessions = Sessions.objects.filter(
        session_start__gte=yesterday_start,
        session_start__lte=yesterday_end
    )

    df_sessions = pd.DataFrame(list(sessions.values('user__token', 'app_name', 'session_duration', 'total_products_visited', 'has_purchased')))
    # Step 2: Find all the tokens of identified users
    identified_user_tokens = IdentifiedUser.objects.values_list('tokens', flat=True)
    identified_user_tokens = [token for tokens in identified_user_tokens for token in tokens]

    # Filter out the sessions that have purchased
    df_sessions = df_sessions[df_sessions['has_purchased'] == False]

    # Step 3: Filter out the sessions of identified users
    df_sessions = df_sessions[df_sessions['user__token'].isin(identified_user_tokens)]
    

    for app_name in df_sessions['app_name'].unique():
        # find the threshold values for app_name
        identified_user_notification_threshold = IdentifiedUserNotificationThreshold.objects.filter(app_name=app_name).first()
        if identified_user_notification_threshold is None:
            continue
        session_duration_75 = identified_user_notification_threshold.session_duration_75
        total_products_visited_75 = identified_user_notification_threshold.total_products_visited_75

        df_app = df_sessions[df_sessions['app_name'] == app_name]
        if df_app.empty:
            continue

        # Step 5: Filter out the sessions that are above the threshold values
        df_app = df_app[df_app['session_duration'] > session_duration_75]
        df_app = df_app[df_app['total_products_visited'] > total_products_visited_75]

        # update or create IdentifiedUserNotification object
        for token in df_app['user__token'].unique():
            identified_user = IdentifiedUser.objects.filter(tokens__contains=[token]).first()
            if identified_user is None:
                continue
            identified_user_notification, created = IdentifiedUserNotification.objects.update_or_create(
                identified_user=identified_user,
                app_name=app_name,
                defaults={
                    'conversion_prob': True
                }
            )
