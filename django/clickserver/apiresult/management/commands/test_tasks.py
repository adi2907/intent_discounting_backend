from django.core.management.base import BaseCommand
from apiresult.models import *
from events.models import *
import logging
logger = logging.getLogger(__name__)
from datetime import datetime,timedelta

class Command(BaseCommand):
    help = 'Test aggregation of users, visits, and sessions in 15-minute intervals'

    def handle(self, *args, **kwargs):
        logger.info("Testing aggregation")
        # Define the 15-minute interval
        end_time_events = datetime.now() - timedelta(minutes=5)
        start_time_events = end_time_events - timedelta(minutes=5)

        # log the start and end time
        logger.info(f"Start time for events: {start_time_events} and end time for events: {end_time_events}")

        end_time_apiresult = datetime.now()
        start_time_apiresult = end_time_apiresult - timedelta(minutes=15)
        logger.info(f"Start time for apiresult: {start_time_apiresult} and end time for apiresult: {end_time_apiresult}")

        # get list of all app names
        app_names = Event.objects.values_list('app_name', flat=True).distinct()

        for app_name in app_names:
            events = Event.objects.filter(app_name=app_name,click_time__gte=start_time_events,click_time__lte=end_time_events)

            user_tokens_events = set(events.values_list('token', flat=True).distinct())
            user_tokens_apiresult = set(User.objects.filter(app_name=app_name,logged_time__gte=start_time_apiresult,logged_time__lte=end_time_apiresult).values_list('tokens', flat=True).distinct())

            if not user_tokens_events.issubset(user_tokens_apiresult):
                missing_tokens = user_tokens_events - user_tokens_apiresult
                logger.info(f"Missing tokens in User model for app {app_name}: {missing_tokens}")
        
            # get list of all sessions and check if they are in Sessions model
            sessions_events = set(events.values_list('session', flat=True).distinct())
            sessions_apiresult = set(Sessions.objects.filter(app_name=app_name,logged_time_gte=start_time_apiresult,logged_time_lte=end_time_apiresult).values_list('session_key', flat=True).distinct())
            
            if not sessions_events.issubset(sessions_apiresult):
                missing_sessions = sessions_events - sessions_apiresult
                logger.info(f"Missing sessions in Sessions model for app {app_name}: {missing_sessions}")
            

            # tally the number of visits
            # visit is where event_type is 'page_load' and has a product_id
            visits_events = events.filter(event_type='page_load',product_id__isnull=False)
            visits_apiresult = Visits.objects.filter(app_name=app_name,created_at__gte=start_time_apiresult,created_at__lte=end_time_apiresult)

            if visits_events.count() != visits_apiresult.count():
                logger.info(f"Number of visits in Visits model for app {app_name} does not match number of visits in events model")
                logger.info(f"Number of visits in events model: {visits_events.count()} and in Visits model: {visits_apiresult.count()}")
            
            # tally the number of carts
            # cart is where click_text is 'add to cart'
            carts_events = events.filter(click_text='add to cart')
            carts_apiresult = Cart.objects.filter(app_name=app_name,created_at__gte=start_time_apiresult,created_at__lte=end_time_apiresult)
            if carts_events.count() != carts_apiresult.count():
                logger.info(f"Number of carts in Cart model for app {app_name} does not match number of carts in events model")
                logger.info(f"Number of carts in events model: {carts_events.count()} and in Cart model: {carts_apiresult.count()}")



            



