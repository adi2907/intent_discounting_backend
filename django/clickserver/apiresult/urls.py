from django.urls import path
from .views import *

urlpatterns = [
    path('crowd_favorites/', CartView.as_view(), name='cart-list'),
    path('featured_collection/', VisitsView.as_view(), name='visit-list'),
    path('pick_up_where_you_left_off/', MostVisitedView.as_view(), name='most-visited'),
    path('users_also_liked/', MostCartedView.as_view(), name='most-carted-list'), 
]
