from django.urls import path
from .views import *

urlpatterns = [
    path('submit_contact/', submitContactView.as_view(), name='submitContact'),
]
