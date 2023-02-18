from django.db import models

# create item model
class Item(models.Model):
    # item_id is interger field but can have null values or empty strings
    item_id = models.TextField(null=True)
    name = models.TextField(null=True)
    price = models.IntegerField(null=True)
    categories = models.JSONField(null=True)
    app_name = models.TextField(null=True)
    last_updated = models.DateTimeField(null=True)


# Create compiled user model
class User(models.Model):
    token = models.TextField()
    user_login = models.TextField()
    user_id = models.TextField()
    app_name = models.TextField(null=True)
    num_sessions = models.IntegerField()
    # date time of last visit
    last_visit = models.DateTimeField()
    # date time of first visit
    first_visit = models.DateTimeField()
    last_updated = models.DateTimeField()
    
    
class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    app_name = models.TextField(null=True)
    created_at = models.DateTimeField()
    quantity = models.PositiveIntegerField()

class Visits(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    app_name = models.TextField(null=True)
    created_at = models.DateTimeField()

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    app_name = models.TextField(null=True)
    created_at = models.DateTimeField()

class IdentifiedUser(models.Model):
    user_id = models.TextField()
    app_name = models.TextField(null=True)
    # array of sub users that are associated with this user
    tokens = models.JSONField(null=True)

    


    
