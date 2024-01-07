from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta, datetime,time
from apiresult.models import *
from collections import defaultdict
from django.db.models import Count
from django.utils.dateparse import parse_datetime,parse_date

import logging
logger = logging.getLogger(__name__)

'''
API DOCUMENTATION FOR visit/user/session/cart count APIs
1. Default Use Case (Previous Day)
GET https://almeapp.com/analytics/[API_TYPE]_count?app_name=[YourAppName]
2. Specific Number of Previous Days
GET https://almeapp.com/analytics/[API_TYPE]_count?app_name=[YourAppName]&days=<number_of_days>
Parameters: days - Number of days to look back from the current date.
3. Specific Date Range
GET https://almeapp.com/analytics/session_count?app_name=[YourAppName]&days=3
Parameters: start_date - Start date of the range, end_date - End date of the range.


Response Format:
{
  "session_count": number,
  "app_name": string
}


'''


def get_date_range_from_request(request):
    query_days = request.query_params.get('days', None)
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)

    if query_days:
        try:
            days = int(query_days)
            end_of_day = datetime.now().date()
            start_of_day = end_of_day - timedelta(days=days)
        except ValueError:
            raise ValueError('Invalid value for days')
    elif start_date and end_date:
        try:
            start_of_day = parse_date(start_date)
            end_of_day = parse_date(end_date)
            if start_of_day > end_of_day:
                raise ValueError('Start date cannot be after end date.')
        except ValueError:
            raise ValueError('Invalid date format or range. Use YYYY-MM-DD.')
    else:
        end_of_day = datetime.now().date() - timedelta(days=1)
        start_of_day = end_of_day

    # Set start_of_day to 00:00 and end_of_day to 23:59:59.999999
    start_of_day = datetime.combine(start_of_day, datetime.min.time())
    end_of_day = datetime.combine(end_of_day, datetime.max.time())

    return start_of_day, end_of_day


class SessionCountView(APIView):
    def get(self, request, format=None):
        try:
            app_name = request.query_params.get('app_name')
            if not app_name:
                return Response({'error': 'app_name parameter is required'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            start_of_day, end_of_day = get_date_range_from_request(request)
            count = Sessions.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lte=end_of_day, 
                app_name=app_name
            ).count()

            return Response({'session_count': count, 'app_name': app_name})

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class UserCountView(APIView):
    def get(self, request, format=None):
        try:
            app_name = request.query_params.get('app_name')
            if not app_name:
                return Response({'error': 'app_name parameter is required'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            start_of_day, end_of_day = get_date_range_from_request(request)
            count = User.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lte=end_of_day, 
                app_name=app_name
            ).count()

            return Response({'user_count': count, 'app_name': app_name})

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class VisitsCountView(APIView):
    def get(self, request, format=None):
        try:
            app_name = request.query_params.get('app_name')
            if not app_name:
                return Response({'error': 'app_name parameter is required'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            start_of_day, end_of_day = get_date_range_from_request(request)
            count = Visits.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lte=end_of_day, 
                app_name=app_name
            ).count()

            return Response({'visit_count': count, 'app_name': app_name})

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CartCountView(APIView):
    def get(self, request, format=None):
        try:
            app_name = request.query_params.get('app_name')
            if not app_name:
                return Response({'error': 'app_name parameter is required'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            start_of_day, end_of_day = get_date_range_from_request(request)
            count = Cart.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lte=end_of_day, 
                app_name=app_name
            ).count()

            return Response({'cart_count': count, 'app_name': app_name})

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class IdentifiedUserCountView(APIView):
    def get(self, request, format=None):
        try:
            app_name = request.query_params.get('app_name')
            if not app_name:
                return Response({'error': 'app_name parameter is required'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            start_of_day, end_of_day = get_date_range_from_request(request)
            count = IdentifiedUser.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lte=end_of_day, 
                app_name=app_name
            ).count()

            return Response({'identified_user_count': count, 'app_name': app_name})

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)   


'''
API DOCUMENTATION FOR CONVERSION APIs
Endpoint: https://almeapp.com/analytics/visit_conversion


Parameters:
days (optional, integer): Number of past days to include (default: 1).
Response: JSON with dates as keys and objects containing purchases, total_sessions, and conversion_rate.
Example Request: https://almeapp.com/analytics/visit-conversion?app_name=[YourAppName]&days=3

Response Format:
{
  "YYYY-MM-DD": {
    "purchases": number,
    "total_sessions": number,
    "conversion_rate": percentage
  },
  ...
}

'''

class VisitConversionView(APIView):
    def get(self, request, format=None):
        app_name = request.query_params.get('app_name')
        if not app_name:
            return Response({'error': 'app_name parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        days = request.query_params.get('days', 1)
        try:
            days = int(days)
        except ValueError:
            return Response({'error': 'Invalid value for days'}, status=status.HTTP_400_BAD_REQUEST)

        conversion_data = defaultdict(lambda: {'visits': 0, 'total_sessions': 0})

        for day in range(days):
            end_of_day = datetime.now().date() - timedelta(days=day)
            start_of_day = end_of_day - timedelta(days=1)

            # Combine date with min and max time without timezone awareness
            start_of_day = datetime.combine(start_of_day, datetime.min.time())
            end_of_day = datetime.combine(end_of_day, datetime.max.time())

            total_sessions = Sessions.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lt=end_of_day, 
                app_name=app_name
            ).count()
            
            relevant_sessions = Sessions.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lt=end_of_day, 
                total_products_visited__gt=0, 
                app_name=app_name
            ).count()

            conversion_rate = (relevant_sessions / total_sessions * 100) if total_sessions > 0 else 0

            conversion_data[str(start_of_day.date())]['visits'] = relevant_sessions
            conversion_data[str(start_of_day.date())]['total_sessions'] = total_sessions
            conversion_data[str(start_of_day.date())]['conversion_rate'] = conversion_rate

        return Response(conversion_data)


class CartConversionView(APIView):
    def get(self, request, format=None):
        app_name = request.query_params.get('app_name')
        if not app_name:
            return Response({'error': 'app_name parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        days = request.query_params.get('days', 1)
        try:
            days = int(days)
        except ValueError:
            return Response({'error': 'Invalid value for days'}, status=status.HTTP_400_BAD_REQUEST)

        conversion_data = defaultdict(lambda: {'visits': 0, 'total_sessions': 0})

        for day in range(days):
            end_of_day = datetime.now().date() - timedelta(days=day)
            start_of_day = end_of_day - timedelta(days=1)

            # Combine date with min and max time for naive datetime
            start_of_day = datetime.combine(start_of_day, datetime.min.time())
            end_of_day = datetime.combine(end_of_day, datetime.max.time())

            total_sessions = Sessions.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lt=end_of_day, 
                app_name=app_name
            ).count()
            
            relevant_sessions = Sessions.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lt=end_of_day, 
                has_carted=True, 
                app_name=app_name
            ).count()

            conversion_rate = (relevant_sessions / total_sessions * 100) if total_sessions > 0 else 0

            conversion_data[str(start_of_day.date())]['carts'] = relevant_sessions
            conversion_data[str(start_of_day.date())]['total_sessions'] = total_sessions
            conversion_data[str(start_of_day.date())]['conversion_rate'] = conversion_rate

        return Response(conversion_data)


class PurchaseConversionView(APIView):
    def get(self, request, format=None):
        app_name = request.query_params.get('app_name')
        if not app_name:
            return Response({'error': 'app_name parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        days = request.query_params.get('days', 1)
        try:
            days = int(days)
        except ValueError:
            return Response({'error': 'Invalid value for days'}, status=status.HTTP_400_BAD_REQUEST)

        conversion_data = defaultdict(lambda: {'visits': 0, 'total_sessions': 0})

        for day in range(days):
            end_of_day = datetime.now().date() - timedelta(days=day)
            start_of_day = end_of_day - timedelta(days=1)

            # Combine date with min and max time for naive datetime
            start_of_day = datetime.combine(start_of_day, datetime.min.time())
            end_of_day = datetime.combine(end_of_day, datetime.max.time())

            total_sessions = Sessions.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lt=end_of_day, 
                app_name=app_name
            ).count()
            
            relevant_sessions = Sessions.objects.filter(
                logged_time__gte=start_of_day, 
                logged_time__lt=end_of_day, 
                has_purchased=True, 
                app_name=app_name
            ).count()

            conversion_rate = (relevant_sessions / total_sessions * 100) if total_sessions > 0 else 0

            conversion_data[str(start_of_day.date())]['visits'] = relevant_sessions
            conversion_data[str(start_of_day.date())]['total_sessions'] = total_sessions
            conversion_data[str(start_of_day.date())]['conversion_rate'] = conversion_rate

        return Response(conversion_data)

'''
API DOCUMENTATION FOR PRODUCT VISITS API
Endpoint: https://almeapp.com/analytics/product_visits

Parameters:
- start_date (optional, string): Start date for filtering visits in YYYY-MM-DD HH:MM:SS format. Defaults to the beginning of the previous day.
- end_date (optional, string): End date for filtering visits in YYYY-MM-DD HH:MM:SS format. Defaults to the end of the previous day.
- app_name: Application name for filtering visits.
- order (optional, string): Sort order for visit counts, either 'asc' for ascending or 'desc' for descending. Default is 'desc'.

Example Request:
https://almeapp.com/analytics/product_visits?app_name=[YourAppName]&start_date=YYYY-MM-DD 00:00:00&end_date=YYYY-MM-DD 23:59:59&order=desc

Example Request for Default Date Range (Previous Day):
https://almeapp.com/analytics/product_visits?app_name=[YourAppName]

Response Format:
[
  {
    "item__name": string,
    "item__product_id": string,
    "visit_count": number
  },
  ...
]

Notes:
- The response is a list of objects, each containing the name and product ID of the item, along with the count of visits.
- The results are sorted by visit count, in either ascending or descending order as specified by the 'order' parameter.

'''

class ProductVisitsView(APIView):

    def get(self, request, *args, **kwargs):

        previous_day = datetime.now().date() - timedelta(days=1)

        # Get start_date and end_date from request, or set defaults
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        app_name = request.query_params.get('app_name', None)

        if not app_name:
            return Response({'error': 'App_name must exist'}, status=400)
        order = request.query_params.get('order', 'desc')

        start_date = datetime.combine(previous_day, time.min)
        end_date = datetime.combine(previous_day, time.max)
        
        if start_date_str:
            start_date = datetime.combine(datetime.strptime(start_date_str, "%Y-%m-%d"), time.min)

        if end_date_str:
            end_date = datetime.combine(datetime.strptime(end_date_str, "%Y-%m-%d"), time.max)


        # Query to get visits
        visits_query = Visits.objects.filter(
            logged_time__range=(start_date, end_date),
            app_name=app_name,
        ).values('item__name', 'item__product_id').annotate(visit_count=Count('id'))

        if order == 'asc':
            visits_query = visits_query.order_by('visit_count')
        else:
            visits_query = visits_query.order_by('-visit_count')

        return Response(list(visits_query))

'''
API DOCUMENTATION FOR PRODUCT CART CONVERSION API
Endpoint: https://almeapp.com/analytics/product_cart_conversion

Parameters:
- app_name (required, string): Name of the application.
- order (optional, string): Sorting order of conversion rates, either 'asc' for ascending or 'desc' for descending. Default is 'desc'.

Example Request:
https://almeapp.com/analytics/product_cart_conversion?app_name=[YourAppName]&order=desc

Response Format:
[
  {
    "product_id": string,
    "visits": number,
    "cart_additions": number,
    "conversion_rate": percentage
  },
  ...
]

Notes:
- The response is a list of objects, each representing a product with its ID, number of visits, number of times added to the cart, and the cart conversion rate.
- Products are sorted by their conversion rate, in either ascending or descending order as specified by the 'order' parameter.
- If the 'order' parameter is not specified, the default sorting order is descending.

'''

class ProductCartConversionView(APIView):
    def get(self, request, *args, **kwargs):
        app_name = request.query_params.get('app_name', None)
        order = request.query_params.get('order', 'desc')

        # Validate token and app_name
        if not app_name:
            return Response({'error': 'App_name must exist'}, status=400)

        
        item_visits = Visits.objects.filter(app_name=app_name).values('item__product_id').annotate(visits_count=Count('id'))

        # Count the number of times each item was added to the cart
        item_cart_additions = Cart.objects.filter(app_name=app_name).values('item__product_id').annotate(cart_count=Count('id'))

        # Calculate conversion rate
        conversion_data = {}
        for visit in item_visits:
            product_id = visit['item__product_id']
            visits_count = visit['visits_count']
            cart_count = next((item['cart_count'] for item in item_cart_additions if item['item__product_id'] == product_id), 0)
            conversion_rate = (cart_count / visits_count * 100) if visits_count > 0 else 0
            conversion_data[product_id] = {
                'visits': visits_count,
                'cart_additions': cart_count,
                'conversion_rate': conversion_rate
            }
        
        sorted_conversion_data = sorted(conversion_data.items(), key=lambda x: x[1]['conversion_rate'], reverse=(order != 'asc'))
        return Response(sorted_conversion_data)
    
'''
API DOCUMENTATION FOR USER ACTIVITY SUMMARY API
Endpoint: https://almeapp.com/analytics/identified_user_activity

Parameters:
- app_name (required, string): Name of the application.
- days (optional, integer): Number of days to look back from the current date for user activity. Defaults to the previous day if not specified.
- start_date (optional, string): Start date of the range in YYYY-MM-DD format.
- end_date (optional, string): End date of the range in YYYY-MM-DD format.

Note: If both 'days' and 'start_date'/'end_date' are provided, 'days' will be ignored.

Usage Examples:
1. Default Use Case (Previous Day)
   GET https://almeapp.com/analytics/identified_user_activity?app_name=[YourAppName]

2. Specific Number of Previous Days
   GET https://almeapp.com/analytics/identified_user_activity?app_name=[YourAppName]&days=<number_of_days>

3. Specific Date Range
   GET https://almeapp.com/analytics/identified_user_activity?app_name=[YourAppName]&start_date=<YYYY-MM-DD>&end_date=<YYYY-MM-DD>

Response Format:
[
  {
    "serial_number": number,
    "name": string,
    "phone": string,
    "email": string,
    "last_visited": datetime,
    "visited": number,
    "added_to_cart": number,
    "purchased": number
  },
  ...
]
'''


class IdentifiedUserActivityView(APIView):
    def get(self, request):
        app_name = request.query_params.get('app_name', None)

        if not app_name:
            return Response({'error': 'App_name must exist'}, status=400)
        
        start_of_day, end_of_day = get_date_range_from_request(request)
        user_activity_summary = []
        serial_number = 1

        identified_users = IdentifiedUser.objects.filter(app_name=app_name,
            logged_time__gte=start_of_day, 
            logged_time__lte=end_of_day)

        for user in identified_users:
            tokens = user.tokens
            user_data = {
                'serial_number': serial_number,
                'name': user.name,
                'phone': user.phone,
                'email': user.email,
                'last_visited': user.logged_time,
                'visited': 0,
                'added_to_cart': 0,
                'purchased': 0

            }

            for token in tokens:
                user_data['visited'] += Visits.objects.filter(user__token=token, app_name=app_name).count()
                user_data['added_to_cart'] += Cart.objects.filter(user__token=token, app_name=app_name).count()
                user_data['purchased'] += Purchase.objects.filter(user__token=token, app_name=app_name).count()

            user_activity_summary.append(user_data)
            serial_number += 1

        return Response(user_activity_summary)


