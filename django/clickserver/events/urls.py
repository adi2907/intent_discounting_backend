# root url to handle post requests from the xhttp request
#
from django.http import HttpResponse
from events import views
from django.urls import path


urlpatterns = [
    path('', views.events, name='events'),
    path('purchase/', views.purchase, name='purchase'),
    path('add_cart/', views.add_cart, name='add_cart'),
]