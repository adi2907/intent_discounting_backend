from django.core.management.base import BaseCommand
from apiresult.models import Sessions, User
from django.db.models import Count, F, Q
import pandas as pd

class Command(BaseCommand):
    help = 'Process session data for analysis'

    def handle(self, *args, **options):
        app_name ='desisandook.myshopify.com'
        sessions = Sessions.objects.filter(app_name=app_name).values()
        df = pd.DataFrame.from_records(sessions)

        percentile = 90
        # Calculate the 75th percentile of session duration
        events_count_percentile = df['events_count'].quantile(percentile/100)
        session_duration_percentile = df['session_duration'].quantile(percentile/100)
        total_products_visited_percentile = df['total_products_visited'].quantile(percentile/100)
        page_load_count_percentile = df['page_load_count'].quantile(percentile/100)

        # print all the percentiles
        print("For the percentile of {}:".format(percentile))
        print("Events count: {}".format(events_count_percentile))
        print("Session duration: {}".format(session_duration_percentile))
        print("Total products visited: {}".format(total_products_visited_percentile))
        print("Page load count: {}".format(page_load_count_percentile))

        matching_sessions = df[(df['events_count']>=events_count_percentile) | 
                               (df['session_duration']>=session_duration_percentile) |
                               (df['total_products_visited']>=total_products_visited_percentile) |
                               (df['page_load_count']>=page_load_count_percentile)
            ]
        # total number of sessions and matching sessions
        print("Total number of sessions: {}".format(len(df)))
        print("Number of matching sessions: {}".format(len(matching_sessions)))

        purchase_sessions = matching_sessions[matching_sessions['has_purchased']==True].shape[0]
        print("Number of matching sessions with purchase: {}".format(purchase_sessions))
        non_purchase_sessions = matching_sessions[matching_sessions['has_purchased']==False].shape[0]
        print("Number of matching sessions without purchase: {}".format(non_purchase_sessions))

        df['session_start'] = pd.to_datetime(df['session_start'])
        df = df.sort_values(by=['user_id', 'session_start'], ascending=[True, False])

        # Group by 'user_id' and use the 'cumcount' to assign a session number in descending order
        df['session_number'] = df.groupby('user_id').cumcount() + 1
        # Determine the maximum session number for purchases for each user
        df_purchases = df[df['has_purchased'] == True]
        max_purchase_session_numbers = df_purchases.groupby('user_id')['session_number'].max()

        # Create a DataFrame with users to exclude based on purchases in their last 4 sessions
        users_with_recent_purchases = df_purchases[df_purchases['session_number'] <= 4]['user_id'].unique()

        # Filter out these users' sessions
        df_filtered = df[~df['user_id'].isin(users_with_recent_purchases)]

        # Calculate the number of purchase and non-purchase sessions after filtering
        purchase_sessions_filtered = df_filtered[df_filtered['has_purchased'] == True]
        non_purchase_sessions_filtered = df_filtered[df_filtered['has_purchased'] == False]

        print(f"Number of purchase sessions after filtering: {len(purchase_sessions_filtered)}")
        print(f"Number of non-purchase sessions after filtering: {len(non_purchase_sessions_filtered)}")

