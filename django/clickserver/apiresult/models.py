from django.db import models


# create item model
class Item(models.Model):
    # item_id is interger field but can have null values or empty strings
    item_id = models.CharField(max_length=255,null=True,db_index=True)
    name = models.TextField(null=True)
    price = models.TextField(null=True)
    categories = models.JSONField(null=True)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    last_updated = models.DateTimeField(null=True)
    logged_time = models.DateTimeField(auto_now_add=True,null=True)


# Create compiled user model
class User(models.Model):
    token = models.CharField(max_length=255,db_index=True)
    user_login = models.TextField()
    user_id = models.TextField()
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    num_sessions = models.IntegerField(null=True)
    # date time of last visit
    last_visit = models.DateTimeField()
    # date time of first visit
    first_visit = models.DateTimeField()
    last_updated = models.DateTimeField()
    logged_time = models.DateTimeField(auto_now_add=True,null=True)
    
    
class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    created_at = models.DateTimeField()
    quantity = models.PositiveIntegerField()
    logged_time = models.DateTimeField(auto_now_add=True,null=True)
    

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
    
    
class IdentifiedUser(models.Model):
    user_id = models.TextField()
    app_name = models.CharField(max_length=255,null=True,db_index=True)
    # array of sub users that are associated with this user
    phone = models.CharField(max_length=15, null=True)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=255, null=True)
    tokens = models.JSONField(null=True)
    logged_time = models.DateTimeField(auto_now_add=True,null=True)
    

    


    
