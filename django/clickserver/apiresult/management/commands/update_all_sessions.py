from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from apiresult.models import Sessions, User
from apiresult.utils.config import *
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update user sessions for a specified date range'

    def handle(self, *args, **options):
        logger.info("Updating user sessions")
        current_time = datetime.now()

        # Get active sessions for the specified date range
        active_sessions = Sessions.objects.filter(is_active=True).order_by('id')

        batch_size = 1000
        paginator = Paginator(active_sessions, batch_size)

        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            sessions_to_update = []
            user_ids_to_update = set()

            for session in page.object_list:
                if (current_time - session.session_end).total_seconds() > (SESSION_IDLE_TIME * 60):
                    session.is_active = False
                    session.session_duration = (session.session_end - session.session_start).total_seconds()
                    sessions_to_update.append(session)
                    user_ids_to_update.add(session.user_id)

            Sessions.objects.bulk_update(sessions_to_update, ['is_active', 'session_duration'])

            users_to_update = User.objects.filter(id__in=user_ids_to_update)
            user_updates = {}

            for user in users_to_update:
                previous_4_sessions = Sessions.objects.filter(user=user).order_by('-session_end')
                carted_sessions = previous_4_sessions.filter(has_carted=True)
                purchase_history = previous_4_sessions[1:5].values_list('has_purchased', flat=True)
                user_updates[user.id] = {
                    'purchase_last_4_sessions': 1 if sum(purchase_history) > 0 else 0,
                    'carted_last_4_sessions': 1 if carted_sessions[1:5].exists() else 0,
                    'purchase_prev_session': previous_4_sessions.first().has_purchased if previous_4_sessions.exists() else None,
                    'num_sessions_last_30_days': Sessions.objects.filter(user=user, logged_time__gte=current_time - timedelta(days=30)).count(),
                    'num_sessions_last_7_days': Sessions.objects.filter(user=user, logged_time__gte=current_time - timedelta(days=7)).count(),
                }

            for user_id, updates in user_updates.items():
                User.objects.filter(id=user_id).update(**updates)

            print(f"Updated {page_number} pages")