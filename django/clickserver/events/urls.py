# root url to handle post requests from the xhttp request
#
from urllib.parse import urlparse
from django.http import HttpResponse
from django.urls import re_path
from events import views

# define url to handle post requests from the xhttp request
urlpatterns = [
    re_path('', views.events)
]

