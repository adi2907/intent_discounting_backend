from django.urls import path
from .views import *

urlpatterns = [
    path('identified-users-list', IdentifiedUsersListView.as_view(), name='identified-users-list'),
]