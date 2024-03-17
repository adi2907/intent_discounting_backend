from django.core.management.base import BaseCommand
from apiresult.models import *
from events.models import Event
from notification.models import SaleNotificationThreshold
import pandas as pd
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Calculate thresholds for sale notification'

    def handle(self, *args, **kwargs):
        app_list = Event.objects.values_list('app_name', flat=True).distinct()
        for app_name in app_list:
            # Get non-active sessions for the app in the last 7 days
            sessions = Sessions.objects.filter(app_name=app_name, is_active=False, logged_time__gte=datetime.now()-timedelta(days=7)).select_related('user')
            df_sessions = pd.DataFrame(list(sessions.values('user__token', 'logged_time', 'events_count', 'total_products_visited', 'page_load_count', 'session_duration', 'has_purchased')))
            if df_sessions.empty:
                continue

            logger.info("Calculating thresholds for app %s" % app_name)

            total_rows = len(df_sessions)
            
            # Drop rows with null values in the threshold fields
            threshold_fields = ['events_count', 'total_products_visited', 'page_load_count', 'session_duration']
            df_sessions.dropna(subset=threshold_fields, inplace=True)

            dropped_rows = total_rows - len(df_sessions)
            logger.info(f"Dropped {dropped_rows} rows out of {total_rows} total rows for app {app_name}")

            if df_sessions.empty:
                logger.info(f"No valid sessions found for app {app_name} after dropping null values")
                continue

            logger.info(df_sessions.head(5))
            df_sessions.rename(columns={'user__token': 'user_token'}, inplace=True)

            # Get 75%ile, 80%ile, 85%ile, 90%ile for each threshold field
            thresholds = {}
            for field in threshold_fields:
                thresholds[field] = {}
                for percentile in [75, 80, 85, 90]:
                    thresholds[field][percentile] = df_sessions[field].quantile(percentile/100)

            df_sessions.sort_values(by=['user_token', 'logged_time'], inplace=True)
            df_sessions['has_purchased_int'] = df_sessions['has_purchased'].astype(int)

            # Apply a rolling sum of purchases over the last 4 sessions for each user, then shift the results.
            purchase_counts = df_sessions.groupby('user_token')['has_purchased_int'].rolling(window=4, min_periods=1).sum().shift().reset_index(level=0, drop=True)
            df_sessions['purchase_last_4_sessions'] = purchase_counts - df_sessions['has_purchased_int']
            df_sessions['purchase_last_4_sessions'] = df_sessions['purchase_last_4_sessions'].apply(lambda x: 1 if x > 0 else 0)

            # Drop the 'has_purchased_int' column as it's no longer needed.
            df_sessions.drop('has_purchased_int', axis=1, inplace=True)

            # Initialize a dictionary to hold the ratios for each percentile
            purchase_ratio_by_percentile = {}

            # Iterate over each percentile to calculate the necessary statistics
            for percentile in [75, 80, 85, 90]:
                # Filter sessions that exceed all specified thresholds at the current percentile
                combined_filter = (df_sessions[threshold_fields[0]] > thresholds[threshold_fields[0]][percentile])
                for field in threshold_fields[1:]:
                    combined_filter &= (df_sessions[field] > thresholds[field][percentile])

                # Apply the filter to df_sessions to get the subset for this percentile
                df_percentile = df_sessions[combined_filter]

                # Number of purchase sessions
                purchase_sessions = df_percentile[df_percentile['has_purchased'] == 1].shape[0]

                # Number of purchase sessions with purchase in the last 4 sessions
                purchase_sessions_recent = df_percentile[(df_percentile['has_purchased'] == 1) & (df_percentile['purchase_last_4_sessions'] == 1)].shape[0]

                # Calculate the ratio if there are any purchase sessions, otherwise set to 0
                ratio = (purchase_sessions_recent / purchase_sessions) * 100 if purchase_sessions else 0

                # Store the ratio for the current percentile
                purchase_ratio_by_percentile[percentile] = ratio

            # Find the percentile with the highest ratio
            selected_percentile = max(purchase_ratio_by_percentile, key=purchase_ratio_by_percentile.get)
            selected_thresholds = {field: int(round(thresholds[field][selected_percentile])) for field in threshold_fields}
            logger.info("Selected percentiles for app %s: %s" % (app_name, selected_thresholds))
            
            # Save the selected thresholds to the database
            threshold, created = SaleNotificationThreshold.objects.get_or_create(app_name=app_name)
            threshold.events_count_threshold = selected_thresholds['events_count']
            threshold.total_products_visited_threshold = selected_thresholds['total_products_visited']
            threshold.page_load_count_threshold = selected_thresholds['page_load_count']
            threshold.session_duration_threshold = selected_thresholds['session_duration']
            threshold.save()