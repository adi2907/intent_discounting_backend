from django.apps import AppConfig

class ApiresultConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apiresult'
    #def ready(self):
    #    from apiresult.tasks import update_database
    #    update_database.apply_async()


