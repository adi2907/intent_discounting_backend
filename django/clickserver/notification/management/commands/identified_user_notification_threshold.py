import pandas as pd
from django.db import connection
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from apiresult.models import *
from notification.models import *

class Command(BaseCommand):
    help = 'Calculate identified user notification threshold'

    def handle(self, *args, **kwargs):
        populate_identified_user_notifications_threshold()


def populate_identified_user_notifications_threshold():
    today = datetime.now().date()
    yesterday_start = datetime.combine(today - timedelta(days=1), datetime.min.time())
    yesterday_end = datetime.combine(today - timedelta(days=1), datetime.max.time())

    # Query sessions data for yesterday and create a DataFrame
    sessions = Sessions.objects.filter(
        session_start__gte=yesterday_start,
        session_start__lte=yesterday_end
    )

    df_sessions = pd.DataFrame(list(sessions.values('user__token', 'app_name', 'session_duration', 'total_products_visited', 'has_purchased')))

    for app_name in df_sessions['app_name'].unique():
        df_app = df_sessions[df_sessions['app_name'] == app_name]

        if df_app.empty:
            continue

        # Get 75th percentile for session duration and total products visited
        session_duration_75 = df_app['session_duration'].quantile(0.75)
        total_products_visited_75 = df_app['total_products_visited'].quantile(0.75)

        # Create or update IdentifiedUserNotification object
        identified_user_notification, created = IdentifiedUserNotificationThreshold.objects.update_or_create(
            app_name=app_name,
            defaults={
                'session_duration_75': session_duration_75,
                'total_products_visited_75': total_products_visited_75
            }
        )

       

