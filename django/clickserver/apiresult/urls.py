from django.urls import path
from .views import *

urlpatterns = [
    path('carts/', CartView.as_view(), name='cart-list'),
    path('visits/', VisitsView.as_view(), name='visit-list'),
    path('most_visited/', MostVisitedView.as_view(), name='most-visited'),
    path('most_carted/', MostCartedView.as_view(), name='most-carted-list'),
    path('new_user_check/', NewUserCheckView.as_view(), name='new-user'),
    path('user_summary/', UserSummaryView.as_view(), name='user-summary'),
    path('test_visited/', TestVisitView.as_view(), name='test-visit'),
    path('test_carted/', TestCartView.as_view(), name='test-cart'),
    path('test_visits_user/', TestVisitsUserView.as_view(), name='test-visits-user'),
    path('test_carts_user/', TestCartsUserView.as_view(), name='test-carts-user'),
]
