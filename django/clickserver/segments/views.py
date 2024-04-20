from django.shortcuts import render

# Create your views here.
from datetime import datetime,timedelta
from apiresult.models import User,IdentifiedUser,Visits,Cart,Purchase
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from apiresult.serializers import UserSerializer,IdentifiedUserSerializer



'''
    API DOCUMENTATION FOR IDENTIFIED USERS ACTIONS

    Endpoint:
    https://almeapp.com/segments/identified-users-list

    Parameters:

    app_name (required, string): The name of the app.
    action (required, string): The action to filter the identified users. Possible values: 'purchase', 'cart', 'visit'.
    yesterday (optional, boolean): If set to true, filters the identified users for the previous day.
    today (optional, boolean): If set to true, filters the identified users for the current day.
    last_x_days (optional, integer): Filters the identified users for the last X days.
    before_x_days (optional, integer): Filters the identified users who did the action before X days and not after that.
    Note: The date range parameters (yesterday, today, last_x_days, before_x_days) are mutually exclusive. Only one of them should be provided at a time.

    Response:
    JSON object containing an array of identified users with their details.

    Example Request:
    https://almeapp.com/segments/identified-users-list?app_name=almestore1.myshopify.com&action=purchase&last_x_days=7
    https://almeapp.com/segments/identified-users-list?app_name=almestore1.myshopify.com&action=cart&before_x_days=7
    https://almeapp.com/segments/identified-users-list?app_name=almestore1.myshopify.com&action=purchase&yesterday=true
    https://almeapp.com/segments/identified-users-list?app_name=almestore1.myshopify.com&action=purchase&today=true


    Response Format:
    {
    "identified_users": [
    {
    "identified_user_id": string,
    "registered_user_id": string,
    "app_name": string,
    "phone": string,
    "email": string,
    "name": string,
    },
    ...
    ]
    }
    '''
class IdentifiedUsersListView(APIView):
    def get(self,request):
        app_name = request.query_params.get('app_name')
        action = request.query_params.get('action')
        yesterday = request.query_params.get('yesterday')
        today = request.query_params.get('today')
        last_x_days = request.query_params.get('last_x_days')
        before_x_days = request.query_params.get('before_x_days')

        if not app_name and not action:
            return Response({"error":"app_name and action are required parameters."},status=400)
        
        if action not in ['purchase','cart','visit']:
            return Response({"error":"action parameter is invalid."},status=400)
        
        if yesterday and today:
            return Response({"error":"yesterday and today parameters are mutually exclusive."},status=400)
        if last_x_days and before_x_days:
            return Response({"error":"last_x_days and before_x_days parameters are mutually exclusive."},status=400)
        
        if yesterday == 'true':
            start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end_date = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif today == 'true':
            start_date = datetime.now().replace(hour=0, minute=0, second=0)
            end_date = datetime.now().replace(hour=23, minute=59, second=59)
        elif last_x_days:
            start_date = (datetime.now() - timedelta(days=int(last_x_days))).replace(hour=0, minute=0, second=0)
            end_date = datetime.now().replace(hour=23, minute=59, second=59)
        elif before_x_days:
            start_date = (datetime.now() - timedelta(days=30)).replace(hour=0, minute=0, second=0)
            end_date = (datetime.now() - timedelta(days=int(before_x_days) - 1)).replace(hour=23, minute=59, second=59)
        else:
            return Response({"error":"One of the date range parameters is required."},status=400)

        # get all the users who have identified user id column not null
        users_with_identified_user_id = User.objects.filter(identified_user_id__isnull=False,app_name=app_name)

        if action == 'purchase':
            users_with_purchase = users_with_identified_user_id.filter(purchase__created_at__gte=start_date,purchase__created_at__lte=end_date).distinct()
            identified_user_ids = users_with_purchase.values_list('identified_user',flat=True)
            identified_users_with_purchase = IdentifiedUser.objects.filter(id__in=identified_user_ids,app_name=app_name)
            identified_users_with_purchase = identified_users_with_purchase.exclude(name__isnull=True,phone__isnull=True,email__isnull=True,registered_user_id__isnull=True)
            serializer = IdentifiedUserSerializer(identified_users_with_purchase,many=True)
        elif action == 'cart':
            users_with_cart = users_with_identified_user_id.filter(cart__created_at__gte=start_date,cart__created_at__lte=end_date).distinct()
            identified_user_ids = users_with_cart.values_list('identified_user',flat=True)
            identified_users_with_cart = IdentifiedUser.objects.filter(id__in=identified_user_ids,app_name=app_name)
            identified_users_with_cart = identified_users_with_cart.exclude(name__isnull=True,phone__isnull=True,email__isnull=True,registered_user_id__isnull=True)
            serializer = IdentifiedUserSerializer(identified_users_with_cart,many=True)

        elif action == 'visit':
            users_with_visit = users_with_identified_user_id.filter(visits__created_at__gte=start_date,visits__created_at__lte=end_date).distinct()
            identified_user_ids = users_with_visit.values_list('identified_user',flat=True)
            identified_users_with_visit = IdentifiedUser.objects.filter(id__in=identified_user_ids,app_name=app_name)
            identified_users_with_visit = identified_users_with_visit.exclude(name__isnull=True,phone__isnull=True,email__isnull=True,registered_user_id__isnull=True)
            serializer = IdentifiedUserSerializer(identified_users_with_visit,many=True)

        return Response(serializer.data)
            
            





