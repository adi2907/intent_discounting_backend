from django.shortcuts import render

# Create your views here.
from datetime import datetime,timedelta
from apiresult.models import User,IdentifiedUser,Visits,Cart,Purchase,Sessions
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from apiresult.serializers import UserSerializer,IdentifiedUserSerializer
from django.db.models import Count



'''
    API DOCUMENTATION FOR IDENTIFIED USERS ACTIONS

    Endpoint:
    https://almeapp.com/segments/identified-users-list

    Parameters:

    app_name (required, string): The name of the app.
    action (required, string): The action to filter the identified users. Possible values: 'purchase', 'cart', 'visit','site_visit'.
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
    https://almeapp.com/segments/identified-users-list?app_name=almestore1.myshopify.com&action=site_visit&yesterday=true
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
        
        if action not in ['purchase','cart','visit','site_visit']:
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
        elif action == 'site_visit':
            users_with_session = users_with_identified_user_id.filter(sessions__logged_time__gte=start_date,sessions__logged_time__lte=end_date).distinct()
            identified_user_ids = users_with_session.values_list('identified_user',flat=True)
            identified_users_with_session = IdentifiedUser.objects.filter(id__in=identified_user_ids,app_name=app_name)
            identified_users_with_session = identified_users_with_session.exclude(name__isnull=True,phone__isnull=True,email__isnull=True,registered_user_id__isnull=True)
            serializer = IdentifiedUserSerializer(identified_users_with_session,many=True)
        else:
            return Response({"error":"action parameter is invalid."},status=400)


        return Response(serializer.data)
            
'''
API DOCUMENTATION FOR IDENTIFIED USERS LAST VISIT

Endpoint: 
https://almeapp.com/segments/identified-users-last-visit

Parameters:
app_name (required, string): The name of the app.
date_field (required, string): The date field to filter the identified users. Possible values: 'on', 'before', 'after', 'between'.
date (required if date_field is 'on', 'before', or 'after', string): The date to filter the identified users.
start_date (required if date_field is 'between', string): The start date to filter the identified users.
end_date (required if date_field is 'between', string): The end date to filter the identified users.

Response:
{
    "identified_users": [
        {
            "identified_user_id": string,
            "registered_user_id": string,
            "app_name": string,
            "phone": string,
            "email": string,
            "name": string
        },
        ...
    ]
}


Example Request:
https://almeapp.com/segments/identified-users-last-visit?app_name=almestore1.myshopify.com&date_field=on&date=2023-04-25
https://almeapp.com/segments/identified-users-last-visit?app_name=almestore1.myshopify.com&date_field=between&start_date=2023-04-20&end_date=2023-04-25
https://almeapp.com/segments/identified-users-last-visit?app_name=almestore1.myshopify.com&date_field=before&date=2023-04-25
https://almeapp.com/segments/identified-users-last-visit?app_name=almestore1.myshopify.com&date_field=after&date=2023-04-25

'''  



class IdentifiedUsersLastVisitView(APIView):
    def get(self,request):
        app_name = request.query_params.get('app_name')
        date_field = request.query_params.get('date_field')

        if date_field == 'on':
            # return the identified users who last visited the app on the given date
            date = request.query_params.get('date')
            if not date:
                return Response({"error":"date parameter is required."},status=400)
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameter is invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(last_visit__date=date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        elif date_field == 'between':
            # return the identified users who last visited the app between the given date range
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            if not start_date or not end_date:
                return Response({"error":"start_date and end_date parameters are required."},status=400)
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameters are invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(last_visit__date__gte=start_date,last_visit__date__lte=end_date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        elif date_field == 'before':
            # return the identified users who last visited the app before the given date
            date = request.query_params.get('date')
            if not date:
                return Response({"error":"date parameter is required."},status=400)
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameter is invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(last_visit__date__lt=date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        elif date_field == 'after':
            # return the identified users who last visited the app after the given date
            date = request.query_params.get('date')
            if not date:
                return Response({"error":"date parameter is required."},status=400)
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameter is invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(last_visit__date__gt=date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        else:
            return Response({"error":"date_field parameter is invalid."},status=400)

'''
API DOCUMENTATION FOR IDENTIFIED USERS CREATED AT

Endpoint: 
https://almeapp.com/segments/identified-users-created-at
Parameters:
app_name (required, string): The name of the app.
date_field (required, string): The date field to filter the identified users. Possible values: 'on', 'before', 'after', 'between'.
date (required if date_field is 'on', 'before', or 'after', string): The date to filter the identified users.
start_date (required if date_field is 'between', string): The start date to filter the identified users.
end_date (required if date_field is 'between', string): The end date to filter the identified users.

IDENTICAL TO IDENTIFIED USERS LAST VISIT API

'''      

class IdentifiedUsersCreatedAtView(APIView):
    def get(self,request):
        app_name = request.query_params.get('app_name')
        date_field = request.query_params.get('date_field')

        if date_field == 'on':
            # return the identified users who last visited the app on the given date
            date = request.query_params.get('date')
            if not date:
                return Response({"error":"date parameter is required."},status=400)
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameter is invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(created_at__date=date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        elif date_field == 'between':
            # return the identified users who last visited the app between the given date range
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            if not start_date or not end_date:
                return Response({"error":"start_date and end_date parameters are required."},status=400)
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameters are invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(created_at__date__gte=start_date,created_at__date__lte=end_date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        elif date_field == 'before':
            # return the identified users who last visited the app before the given date
            date = request.query_params.get('date')
            if not date:
                return Response({"error":"date parameter is required."},status=400)
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameter is invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(created_at__date__lt=date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        elif date_field == 'after':
            # return the identified users who last visited the app after the given date
            date = request.query_params.get('date')
            if not date:
                return Response({"error":"date parameter is required."},status=400)
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except:
                return Response({"error":"date parameter is invalid."},status=400)
            identified_users = IdentifiedUser.objects.filter(created_at__date__gt=date,app_name=app_name)
            serializer = IdentifiedUserSerializer(identified_users,many=True)
            return Response(serializer.data)
        else:
            return Response({"error":"date_field parameter is invalid."},status=400)

'''

API DOCUMENTATION FOR IDENTIFIED USERS SESSIONS

Endpoint:
https://almeapp.com/segments/identified-users-sessions

Parameters:
app_name (required, string): The name of the app.
comparison_field (required, string): The comparison field to filter the identified users. Possible values: 'greater_than', 'less_than', 'equal'.
comparison_value (required, integer): The comparison value to filter the identified users.

Response:
{
    "identified_users": [
        {
            "identified_user_id": string,
            "registered_user_id": string,
            "app_name": string,
            "phone": string,
            "email": string,
            "name": string
        },
        ...
    ]
}

Example Request:
https://almeapp.com/segments/identified-users-sessions?app_name=almestore1.myshopify.com&comparison_field=greater_than&comparison_value=10
https://almeapp.com/segments/identified-users-sessions?app_name=almestore1.myshopify.com&comparison_field=less_than&comparison_value=5



'''

class IdentifiedUserSessionView(APIView):
    def get(self,request):
        app_name = request.query_params.get('app_name')
        comparison_field = request.query_params.get('comparison_field')
        comparison_value = request.query_params.get('comparison_value')
        
        if not all([app_name, comparison_field, comparison_value]):
            return Response({"error": "app_name, comparison_field, and comparison_value are required parameters."}, status=400)

        try:
            comparison_value = int(comparison_value)
        except ValueError:
            return Response({"error": "comparison_value must be an integer."}, status=400)

        # get all users with indentified user id
        users_with_identified_user_id = User.objects.filter(identified_user__isnull=False,app_name=app_name)

        if comparison_field == 'greater_than':
            users = users_with_identified_user_id.annotate(session_count=Count('sessions')).filter(session_count__gt=comparison_value)
        elif comparison_field == 'less_than':
            users = users_with_identified_user_id.annotate(session_count=Count('sessions')).filter(session_count__lt=comparison_value)
        elif comparison_field == 'equal':
            users = users_with_identified_user_id.annotate(session_count=Count('sessions')).filter(session_count=comparison_value)
        else:
            return Response({"error": "comparison_field parameter is invalid."}, status=400)

        
        identified_user_ids = users.values_list('identified_user_id', flat=True).distinct()
        identified_users = IdentifiedUser.objects.filter(id__in=identified_user_ids, app_name=app_name)
        serializer = IdentifiedUserSerializer(identified_users, many=True)
        return Response(serializer.data)



