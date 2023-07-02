from django.db import models

# create event model
class Event(models.Model):
    token = models.CharField(max_length=255,db_index=True)
    session = models.TextField()
    user_login = models.TextField()
    user_id = models.TextField()
    # click time is datetime field with format 'yyyy-mm-dd hh:mm:ss'
    click_time = models.DateTimeField(db_index=True)
    # allow null value for user_regd datetime field
    user_regd = models.TextField()
    user_agent = models.TextField()
    browser = models.TextField()
    os = models.TextField()
    event_type = models.TextField()
    event_name = models.TextField()
    source_url = models.TextField()
    app_name = models.CharField(max_length=255,db_index=True)
    click_text = models.TextField(default='')
    # add product properties
    product_id = models.CharField(max_length=255,null=True,db_index=True)
    product_name = models.CharField(max_length=255, null=True)
    product_price = models.TextField(null=True)
    # array of categories
    product_category = models.TextField(null=True)
    # add logged time, default is null
    logged_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'event_raw'

