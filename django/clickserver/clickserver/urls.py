from urllib.parse import urlparse
from django.http import HttpResponse
from django.urls import path,re_path,include
from events import views

# define url to handle post requests from the xhttp request
urlpatterns = [
    #path('', include('events.urls')),
    path('api/', include('apiresult.urls')),
    path('api-auth/', include('rest_framework.urls')),
#    re_path('', views.events),
]
