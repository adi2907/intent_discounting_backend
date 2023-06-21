from django.urls import path
from .views import SubmitContactView

urlpatterns = [
    path('submit_contact/', SubmitContactView.as_view(), name='submitContact'),
]
