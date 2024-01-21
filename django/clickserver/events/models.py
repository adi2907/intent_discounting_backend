from django.db import models

# create event model
class Event(models.Model):
    token = models.CharField(max_length=255,db_index=True)
    session = models.TextField()
    user_login = models.TextField(null=True)
    user_id = models.TextField(null=True)
    # click time is datetime field with format 'yyyy-mm-dd hh:mm:ss'
    click_time = models.DateTimeField(db_index=True)
    # allow null value for user_regd datetime field
    user_regd = models.TextField(null=True)
    event_type = models.TextField()
    event_name = models.TextField(null=True)
    source_url = models.TextField(null=True)
    app_name = models.CharField(max_length=255,db_index=True)
    click_text = models.TextField(default='')
    # add product properties
    product_id = models.CharField(max_length=255,null=True,db_index=True)
    product_name = models.CharField(max_length=255, null=True,db_index=True)
    product_price = models.TextField(null=True)
    # add logged time, default is null
    logged_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'event_raw'

# create purchase model
class Purchase(models.Model):
    cart_token = models.CharField(max_length=255,db_index=True)
    user_login = models.TextField(null=True)
    user_id = models.TextField(null=True)
    # created_at is datetime field with format 'yyyy-mm-dd hh:mm:ss'
    created_at = models.DateTimeField(db_index=True)
    app_name = models.CharField(max_length=255,db_index=True)
   
    product_id = models.CharField(max_length=255,null=True,db_index=True)
    product_name = models.CharField(max_length=255, null=True,db_index=True)
    product_price = models.TextField(null=True)
    product_quantity = models.TextField(null=True)
    # array of discount codes
    discount_codes = models.JSONField(null=True)
    # add logged time, default is null
    logged_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'purchase_webhook'