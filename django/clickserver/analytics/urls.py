from django.urls import path
from .views import *

urlpatterns = [
    path('session_count/', SessionCountView.as_view(), name='sessionCount'),
    path('user_count/', UserCountView.as_view(), name='userCount'),
    path('visits_count/', VisitsCountView.as_view(), name='visitsCount'),
    path('cart_count/', CartCountView.as_view(), name='cartCount'),
    path('identified_user_count/', IdentifiedUserCountView.as_view(), name='identifiedUserCount'),
    path('visit_conversion/', VisitConversionView.as_view(), name='visitConversion'),
    path('cart_conversion/', CartConversionView.as_view(), name='cartConversion'),
    path('purchase_conversion/', PurchaseConversionView.as_view(), name='purchaseConversion'),
    path('product_visits/', ProductVisitsView.as_view(), name='productVisits'),
    path('product_cart_conversion/', ProductCartConversionView.as_view(), name='productCart'),
]