from django.core.management.base import BaseCommand
from apiresult.models import *
import logging
logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from apiresult.utils.config import *
from django.core.paginator import Paginator

class Command(BaseCommand):
    help = 'Update all user sessions'

    def handle(self, *args, **options):
        # change is_active to false if session last logged time is more than SESSION_IDLE_TIME (1 hour)
        logger.info("Updating all user sessions")
        
         # Get all active sessions
        active_sessions = Sessions.objects.filter(is_active=True).order_by('id')
        current_time = datetime.now()
        # Create a paginator with a chunk size of 1000
        paginator = Paginator(active_sessions, 1000)

        # Get the total number of chunks
        total_chunks = paginator.num_pages
        for chunk_number in paginator.page_range:
            logger.info(f"Processing chunk {chunk_number} of {total_chunks}")
            # Get the sessions for the current chunk
            sessions = paginator.page(chunk_number) 
            for session in sessions:
                if (current_time - session.session_end).total_seconds() > (SESSION_IDLE_TIME*60):
                    session.is_active = False
                    # update session duration
                    session.session_duration = (session.session_end - session.session_start).total_seconds()
                    session.save()
                    # update the user attributes
                    user = session.user
                    # excluding the current session
                    previous_4_sessions = Sessions.objects.filter(user=user).order_by('-session_end')[1:5]
                    previous_session = None
                    if len(previous_4_sessions) >= 1:
                        previous_session = previous_4_sessions[0] #most recent session excluding the current session
                
                    purchase_history = [session.has_purchased for session in previous_4_sessions]
                    user.purchase_last_4_sessions = 1 if sum(purchase_history) > 0 else 0
                    user.carted_last_4_sessions = 1 if sum([session.has_carted for session in previous_4_sessions]) > 0 else 0
                    
                    # if previous session then assign purchase_prev_session to has_purchased of previous session else assign 0
                    if previous_session:
                        user.purchase_prev_session = previous_session.has_purchased

                    # number of sessions last 30 days
                    sessions_last_30_days = Sessions.objects.filter(user=user).filter(logged_time__gte=current_time - timedelta(days=30))
                    user.num_sessions_last_30_days = len(sessions_last_30_days)

                    # number of sessions last 7 days
                    sessions_last_7_days = Sessions.objects.filter(user=user).filter(logged_time__gte=current_time - timedelta(days=7))
                    user.num_sessions_last_7_days = len(sessions_last_7_days)
                    user.save()

    
                            
