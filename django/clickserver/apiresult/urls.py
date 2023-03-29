from django.urls import path
from .views import *

urlpatterns = [
    path('carts/', CartView.as_view(), name='cart-list'),
    path('visits/', VisitsView.as_view(), name='visit-list'),
    path('most_visited/', MostVisitedView.as_view(), name='most-visited'),
    path('most_carted/', MostCartedView.as_view(), name='most-carted-list'),
    path('test_visits/', TestVisitView.as_view(), name='test-visit'),
    path('test_carts/', TestCartView.as_view(), name='test-cart'),
]