from django.urls import path
from .views import *

urlpatterns = [
    path('identified-users-list', IdentifiedUsersListView.as_view(), name='identified-users-list'),
    path('identified-users-last-visit', IdentifiedUsersLastVisitView.as_view(), name='identified-users-last-visit'),
    path('identified-users-created-at', IdentifiedUsersCreatedAtView.as_view(), name='identified-users-created-at'),
    path('identified-users-sessions', IdentifiedUserSessionView.as_view(), name='identified-users-sessions'),

]