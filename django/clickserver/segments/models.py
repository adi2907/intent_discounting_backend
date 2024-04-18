from django.db import models
from apiresult.models import IdentifiedUser

# create user segments model
class IdentifiedUserSegment(models.Model):
    segment_name = models.CharField(max_length=255,db_index=True)
    segment_description = models.TextField(null=True)
    app_name = models.CharField(max_length=255,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    # list of IdentifiedUser objects
    users = models.ManyToManyField(IdentifiedUser, related_name='segments')
    logged_time = models.DateTimeField(auto_now_add=True,null=True,db_index=True)
   
    class Meta:
        db_table = 'identified_user_segments'
    def __str__(self):
        return self.segment_name
