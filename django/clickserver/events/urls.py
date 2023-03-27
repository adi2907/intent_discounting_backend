# root url to handle post requests from the xhttp request
#
from django.http import HttpResponse
from events import views
from django.urls import path


urlpatterns = [
    path('', views.events, name='events'),
]