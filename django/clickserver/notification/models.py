from django.db import models


class SaleNotificationThreshold(models.Model):
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    events_count_threshold = models.IntegerField(null=True)
    page_load_count_threshold = models.IntegerField(null=True)
    click_count_threshold = models.IntegerField(null=True)
    unique_products_visited_threshold = models.IntegerField(null=True)
    total_products_visited_threshold = models.IntegerField(null=True)
    purchase_count_threshold = models.IntegerField(null=True)
    product_total_price = models.FloatField(null=True)
    cart_count_threshold = models.IntegerField(null=True)
    time_spent_product_pages_threshold = models.FloatField(null=True) # time spent on product pages in seconds
    session_duration_threshold = models.FloatField(null=True) # in seconds
    logged_time = models.DateTimeField(auto_now_add=True,null=True,db_index=True)
    
