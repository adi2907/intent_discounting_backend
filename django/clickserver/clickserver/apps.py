# clickserver/apps.py
from django.apps import AppConfig

class ClickserverConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clickserver'

    def ready(self):
        from . import model_loader
        model_loader.load_all_models()