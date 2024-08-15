from django.urls import path
from .views import *

urlpatterns = [
    path('submit_contact/', SubmitContactView.as_view(), name='submitContact'),
    path('sale_notification/', SaleNotificationView.as_view(), name='sale-notification'),
    path('new_sale_notification/', NewSaleNotificationView.as_view(), name='new-sale-notification'),
]
