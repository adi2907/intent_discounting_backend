from django.core.management.base import BaseCommand
from apiresult.models import *
from notification.models import SaleNotificationThreshold
import pandas as pd
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)
from apiresult.utils.config import PERCENTILE


class Command(BaseCommand):
    help = 'Calculate thresholds for sale notification'

    def handle(self, *args, **kwargs):
        
        app_list = Sessions.objects.values_list('app_name', flat=True).distinct()
        for app_name in app_list:
            print(f'Calculating thresholds for {app_name}')
            # take the last 30 days data
            sessions = Sessions.objects.filter(app_name=app_name,
                                               session_start__gte=datetime.now() - timedelta(days=30)).values()
            
            df = pd.DataFrame.from_records(sessions)

            events_count_percentile = df['events_count'].quantile(PERCENTILE)
            total_products_visited_percentile = df['total_products_visited'].quantile(PERCENTILE)
            page_load_count_percentile = df['page_load_count'].quantile(PERCENTILE)

            # load the existing threshold
            threshold = SaleNotificationThreshold.objects.filter(app_name=app_name).first()
            if not threshold:
                threshold = SaleNotificationThreshold(app_name=app_name)
            threshold.events_count_threshold = events_count_percentile
            threshold.total_products_visited_threshold = total_products_visited_percentile
            threshold.page_load_count_threshold = page_load_count_percentile
            # print the total sessions and matching sessions by ORing all of these percentile valies 
            matching_sessions = df[(df['events_count']>=events_count_percentile) | 
                                   (df['total_products_visited']>=total_products_visited_percentile) |
                                   (df['page_load_count']>=page_load_count_percentile)
                ]
            
            print(f"Total number of sessions: {len(df)}")
            print(f"Number of matching sessions: {len(matching_sessions)}")

            # calculate the purchase sessions
            purchase_sessions = matching_sessions[matching_sessions['has_purchased']==True].shape[0]
            print(f"Number of matching sessions with purchase: {purchase_sessions}")


            matching_sessions['session_start'] = pd.to_datetime(matching_sessions['session_start'])
            matching_sessions = matching_sessions.sort_values(by=['user_id', 'session_start'], ascending=[True, False])

            # Group by 'user_id' and use the 'cumcount' to assign a session number in descending order
            matching_sessions['session_number'] = matching_sessions.groupby('user_id').cumcount() + 1
            # Determine the maximum session number for purchases for each user
            df_purchases = matching_sessions[matching_sessions['has_purchased'] == True]

            users_with_recent_purchases = df_purchases[df_purchases['session_number'] <= 4]['user_id'].unique()
            df_filtered = matching_sessions[~matching_sessions['user_id'].isin(users_with_recent_purchases)]

            purchase_sessions_filtered = df_filtered[df_filtered['has_purchased'] == True]
            print(f"Number of purchase sessions after filtering: {len(purchase_sessions_filtered)}")
            
            non_purchase_sessions_filtered = df_filtered[df_filtered['has_purchased'] == False]
            print(f"Number of non-purchase sessions after filtering: {len(non_purchase_sessions_filtered)}")
            

            threshold.save()
            logger.info(f'Thresholds calculated for {app_name}')
            

            
