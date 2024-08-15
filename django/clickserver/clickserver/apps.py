# clickserver/apps.py
from django.apps import AppConfig
import logging
logger = logging.getLogger(__name__)

class ClickserverConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clickserver'

    def ready(self):
        from clickserver.model_loader import load_all_models
        try:
            load_all_models()
        except Exception as e:
            logger.info(f"Error loading models: {e}")
