#apiresult/models.py
from django.db import models
import os
from django.conf import settings
from django.forms.models import model_to_dict
from clickserver.model_loader import get_model,global_models,load_all_models
import logging
logger = logging.getLogger(__name__)

global_label_encoder = None

def get_label_encoder():
    global_label_encoder = get_model('global_label_encoder')
    if global_label_encoder is None:
        raise ValueError("Global label encoder not found. Please ensure it's loaded correctly.")
    
    return global_label_encoder

# load all deep learning models if not loaded yet
if not global_models:
    load_all_models()
    logger.info(f"Models loaded successfully in apiresult/models.py")
else:
    logger.info(f"Models already loaded in apiresult/models.py")



# create item model
class Item(models.Model):
    # item_id is interger field but can have null values or empty strings
    product_id = models.CharField(max_length=255,null=True,db_index=True)
    name = models.TextField(null=True)
    price = models.TextField(null=True)
    categories = models.JSONField(null=True)
    description = models.TextField(null=True)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    last_updated = models.DateTimeField(null=True)
    logged_time = models.DateTimeField(auto_now_add=True,null=True)


# Create compiled user model
class User(models.Model):
    token = models.CharField(max_length=255,db_index=True)
    experiment_group = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    user_login = models.TextField(null=True)
    registered_user_id = models.CharField(max_length=255,null=True)
    identified_user = models.ForeignKey('IdentifiedUser', on_delete=models.CASCADE,null=True)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    # date time of last visit
    last_visit = models.DateTimeField(db_index=True)
    # date time of first visit
    first_visit = models.DateTimeField()
    last_updated = models.DateTimeField()
    logged_time = models.DateTimeField(auto_now_add=True,null=True)
   
    purchase_last_4_sessions = models.IntegerField(null=True)
    carted_last_4_sessions = models.IntegerField(null=True)
    purchase_prev_session = models.IntegerField(null=True)
    num_sessions_last_30_days = models.IntegerField(null=True)
    num_sessions_last_7_days = models.IntegerField(null=True)

    class Meta:
        unique_together = ('token', 'app_name')
    
    
class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    cart_token = models.CharField(max_length=255,null=True,db_index=True)
    created_at = models.DateTimeField(db_index=True)
    quantity = models.PositiveIntegerField(null=True,default=1)
    logged_time = models.DateTimeField(auto_now_add=True,null=True,db_index=True)
    

class Visits(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    created_at = models.DateTimeField(db_index=True)
    logged_time = models.DateTimeField(auto_now_add=True,null=True)
    

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    created_at = models.DateTimeField(db_index=True)
    logged_time = models.DateTimeField(auto_now_add=True,null=True)
    quantity = models.PositiveIntegerField(null=True,default=1)
    cart_token = models.CharField(max_length=255,null=True,db_index=True)
    
    
class IdentifiedUser(models.Model):
    registered_user_id = models.CharField(max_length=255,null=True)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    # array of sub users that are associated with this user
    phone = models.CharField(max_length=15, null=True)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=255, null=True)
    tokens = models.JSONField(null=True)
    created_at = models.DateTimeField(null=True,db_index=True)
    last_visit = models.DateTimeField(null=True,db_index=True)
    shopify_update = models.BooleanField(default=False)
    logged_time = models.DateTimeField(auto_now_add=True,null=True)
    class Meta:
        unique_together = ('registered_user_id', 'app_name')

    

class UserSummary(models.Model):
    user_token = models.CharField(max_length=255,db_index=True)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    last_visited = models.JSONField(null=True, blank=True, default=list)
    last_carted = models.JSONField(null=True, blank=True, default=list)
    recommended = models.JSONField(null=True, blank=True, default=list)
    logged_time = models.DateTimeField(auto_now=True)


class Sessions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    is_active = models.BooleanField(null=True,default=True,db_index=True)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    session_key = models.CharField(max_length=255,null=False,db_index=True,unique=True)
    session_start = models.DateTimeField(null=True,db_index=True)
    session_end = models.DateTimeField(null=True,db_index=True)
    experiment_group = models.CharField(max_length=32, default='control', db_index=True)
    events_count = models.IntegerField(null=True)
    page_load_count = models.IntegerField(null=True)
    click_count = models.IntegerField(null=True)
    unique_products_visited = models.JSONField(null=True)
    total_products_visited = models.IntegerField(null=True)
    has_purchased = models.BooleanField(null=True)
    has_carted = models.BooleanField(null=True)
    has_checkout = models.BooleanField(null=True)
    is_logged_in = models.BooleanField(null=True)
    purchase_count = models.IntegerField(null=True)
    product_total_price = models.FloatField(null=True)
    cart_count = models.IntegerField(null=True)
    is_paid_traffic = models.BooleanField(null=True)
    time_spent_product_pages = models.FloatField(null=True) # time spent on product pages in seconds
    session_duration = models.FloatField(null=True) # in seconds
    logged_time = models.DateTimeField(auto_now_add=True,null=True,db_index=True)

class SaleNotificationSessions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    is_active = models.BooleanField(null=True,default=True,db_index=True)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    session_key = models.CharField(max_length=255,null=False,db_index=True,unique=True)
    experiment_group = models.CharField(max_length=32, default='control', db_index=True)
    events_category_list = models.JSONField(null=True)
    time_diff_list = models.JSONField(null=True)
    encoded_events_category_list = models.JSONField(null=True) # encoded events category list
    encoded_time_diff_list = models.JSONField(null=True) # encoded time difference list, for future use to maintain categorization
    has_purchased = models.BooleanField(null=True)
    event_sequence_length = models.IntegerField(null=True)
    last_event = models.JSONField(null=True)
    logged_time = models.DateTimeField(auto_now_add=True,null=True,db_index=True)

    class Meta:
        db_table = 'sale_notification_sessions'  
        unique_together = ('session_key', 'app_name')

    def encode_events(self):
        if self.events_category_list:
            encoder = get_label_encoder()
            self.encoded_events_category_list = encoder.transform(self.events_category_list).tolist()
            self.event_sequence_length = len(self.events_category_list)

    def save(self, *args, **kwargs):
        session = model_to_dict(self)
        print(f"Before encoding: {session.get('session_key')}")
        self.encode_events()
        print(f"After encoding: {session.get('session_key')}")
        super().save(*args, **kwargs)


