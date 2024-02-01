from django.core.management.base import BaseCommand
from apiresult.models import *
import logging
logger = logging.getLogger(__name__)
from datetime import datetime
from apiresult.tasks import update_all_user_sessions

class Command(BaseCommand):
    help = 'Update all user sessions'

    def handle(self, *args, **options):
        update_all_user_sessions()
                            
