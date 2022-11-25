from django.db import models

# create event model
class Event(models.Model):
    token = models.TextField()
    session = models.TextField()
    user_login = models.TextField()
    user_id = models.TextField()
    # click time is datetime field with format 'yyyy-mm-dd hh:mm:ss'
    click_time = models.DateTimeField()
    # allow null value for user_regd datetime field
    user_regd = models.TextField()
    user_agent = models.TextField()
    browser = models.TextField()
    os = models.TextField()
    event_type = models.TextField()
    event_name = models.TextField()
    source_url = models.TextField()
    app_name = models.TextField()
    class Meta:
        db_table = 'event_raw'

    


