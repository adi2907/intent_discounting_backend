from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from apiresult.models import Sessions
from apiresult.utils.config import *
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update user sessions in weekly chunks starting from February 1st'

    def handle(self, *args, **options):
        logger.info("Updating user sessions in weekly chunks")

        start_date = datetime(2024, 2, 1).date()  # February 1st, 2023
        end_date = datetime.now().date()

        while start_date <= end_date:
            chunk_start = start_date
            chunk_end = min(start_date + timedelta(days=6), end_date)  # 7-day chunk

            logger.info(f"Processing chunk from {chunk_start} to {chunk_end}")

            # Get active sessions for the current chunk
            active_sessions = Sessions.objects.filter(
                is_active=True,
                logged_time__date__gte=chunk_start,
                logged_time__date__lte=chunk_end
            ).order_by('id')

            # Create a paginator with a chunk size of 1000
            paginator = Paginator(active_sessions, 1000)

            # Get the total number of chunks
            total_chunks = paginator.num_pages

            for chunk_number in paginator.page_range:
                logger.info(f"Processing page {chunk_number} of {total_chunks}")

                # Get the sessions for the current page
                sessions = paginator.page(chunk_number)

                for session in sessions:
                    current_time = datetime.now()
                    if (current_time - session.session_end).total_seconds() > (SESSION_IDLE_TIME * 60):
                        session.is_active = False
                        session.session_duration = (session.session_end - session.session_start).total_seconds()
                        session.save()

                        user = session.user
                        previous_4_sessions = Sessions.objects.filter(user=user).order_by('-session_end')[1:5]
                        previous_session = None
                        if len(previous_4_sessions) >= 1:
                            previous_session = previous_4_sessions[0]

                        purchase_history = [session.has_purchased for session in previous_4_sessions]
                        user.purchase_last_4_sessions = 1 if sum(purchase_history) > 0 else 0
                        user.carted_last_4_sessions = 1 if sum([session.has_carted for session in previous_4_sessions]) > 0 else 0

                        if previous_session:
                            user.purchase_prev_session = previous_session.has_purchased

                        sessions_last_30_days = Sessions.objects.filter(
                            user=user,
                            logged_time__gte=current_time - timedelta(days=30)
                        )
                        user.num_sessions_last_30_days = len(sessions_last_30_days)

                        sessions_last_7_days = Sessions.objects.filter(
                            user=user,
                            logged_time__gte=current_time - timedelta(days=7)
                        )
                        user.num_sessions_last_7_days = len(sessions_last_7_days)

                        user.save()

            start_date += timedelta(days=7)  # Move to the next 7-day chunk

        logger.info("User sessions update completed")