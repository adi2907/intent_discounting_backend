from django.core.management.base import BaseCommand
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Count
import json
import logging
import os


from apiresult.models import *
from analytics.models import *

logger = logging.getLogger(__name__)


