from django.apps import AppConfig
#from apiresult.tasks import update_database

class ApiresultConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apiresult'
    def ready(self):
        run_background_job()
        from apiresult.tasks import update_database
        update_database.apply_async(countdown=10)






def run_background_job():
    pass
#    update_database()
