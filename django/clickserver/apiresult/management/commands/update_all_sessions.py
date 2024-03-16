from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from apiresult.models import Sessions
from apiresult.utils.config import *
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update user sessions for a specified date range'


    def handle(self, *args, **options):
        logger.info("Updating user sessions")
        # Get active sessions for the specified date range
        active_sessions = Sessions.objects.filter(
            is_active=True,
        ).order_by('id')

        for session in active_sessions:
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

        