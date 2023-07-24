
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from .models import *
from django.utils import timezone
from django.db.models import Count
import random


''' returns carts for user
Usage: curl "http://127.0.0.1:8000/api/carts/?token=q6wxm4v47y9"
curl "http://127.0.0.1:8000/api/carts/?token=q6wxm4v47y9&last_7_days=True"
curl "http://127.0.0.1:8000/api/carts/?token=q6wxm4v47y9&last_7_days&max_items=5"
curl  "http://127.0.0.1:8000/api/carts/?token=q6wxm4v47y9&start_date=2023-01-01&end_date=2023-01-02?max_items=5"
Response: ["114338","130233","130438","114799","128072"]
'''
class CartView(APIView):
    
    # return cart items for user
    def get(self, request):
        token = self.request.query_params.get('token', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        max_items = self.request.query_params.get('max_items', 10)

        if last_7_days is not None:
            queryset = Cart.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Cart.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Cart.objects.filter(user__token=token, created_at__range=(start_date, end_date))
        else:
            queryset = Cart.objects.filter(user__token=token)
        
        queryset = queryset.values('product_id').annotate(count=Count('product_id')).order_by('-count')[:int(max_items)]
        queryset = queryset[:int(max_items)]  
        product_ids = [Item.objects.get(id=item['product_id']).product_id for item in queryset]      
        return Response(product_ids)

''' returns visits for user in descending order of number of visits
Usage: curl "http://127.0.0.1:8000/api/visits/?token=q6wxm4v47y9"
curl "http://127.0.0.1:8000/api/visits/?token=q6wxm4v47y9&last_7_days=True"
curl "http://127.0.0.1:8000/api/visits/?token=q6wxm4v47y9&last_7_days&max_items=5"
curl  "http://127.0.0.1:8000/api/visits/?token=q6wxm4v47y9&start_date=2023-01-01&end_date=2023-01-02?max_items=5"
Response: ["130233","128072","130438","107096","114799"]
'''
class VisitsView(APIView):
    def get(self, request):
        token = self.request.query_params.get('token', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        max_items = self.request.query_params.get('max_items', 10)

        if last_7_days is not None:
            queryset = Visits.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Visits.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Visits.objects.filter(user__token=token, created_at__range=(start_date, end_date))
        else:
            # default to 7 days if no date range is specified
            queryset = Visits.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        
        # Annotate visit count and order by descending count
        queryset = queryset.values('product_id').annotate(visit_count=Count('product_id')).order_by('-visit_count')
        queryset = queryset[:int(max_items)]       

        product_ids = [Item.objects.get(id=item['product_id']).product_id for item in queryset]      
        return Response(product_ids)
 

'''
Returns most visited items
Usage: curl "http://127.0.0.1:8000/api/most_visited/?max_items=5"
Response: ["127109","130239","126319","130438","129470"]
'''

class MostVisitedView(APIView):
    def get(self,request):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        # set max_items to 30 if not specified
        max_items = self.request.query_params.get('max_items', 30)
       


        if last_7_days is not None:
            queryset = Visits.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Visits.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Visits.objects.filter(created_at__range=(start_date, end_date))
        else:
            # default to 7 days if no date range is specified
            queryset = Visits.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
        
            
        queryset = queryset.values('product_id').annotate(count=Count('product_id')).order_by('-count')
        queryset = queryset[:int(max_items)].values('product_id')    
        
       
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(id=item['product_id']).product_id)
        # randomly select 10 items from product_ids
        product_ids = random.sample(product_ids, 10)
        return Response(product_ids)
'''   
Returns most carted items
Usage: curl "http://127.0.0.1:8000/api/most_carted/?max_items=5"
Response: ["130188","130415","128734","128153","124324"]
'''
class MostCartedView(APIView):
    def get(self,request):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        max_items = self.request.query_params.get('max_items', 30)

        if last_7_days is not None:
            queryset = Cart.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Cart.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Cart.objects.filter(created_at__range=(start_date, end_date))
        else:
            # default to 7 days if no date range is specified
            queryset = Cart.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))

        queryset = queryset.values('product_id').annotate(count=Count('product_id')).order_by('-count')
        queryset = queryset[:int(max_items)].values('product_id')    
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(id=item['product_id']).product_id)
        # randomly select 10 items from product_ids
        product_ids = random.sample(product_ids, 10)
        return Response(product_ids)

# check if user is new user
class NewUserCheckView(APIView):
    def get(self,request):
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)

        if token is None or app_name is None: # respond with error
            return Response({'error': 'token and app_name must be specified'})
        # check if user token exists in User table
        try:
            queryset = User.objects.get(token=token, app_name=app_name)
            return Response({'new_user': False})
        except:
            return Response({'new_user': True})

class UserSummaryView(APIView):
    def get(self,request):
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)

        if token is None or app_name is None: # respond with error
            return Response({'error': 'token and app_name must be specified'})
        try:
            queryset = UserSummary.objects.get(user_token=token, app_name=app_name)
        except:
            return Response({'error': 'user summary not found'})

        serializer = UserSummarySerializer(queryset)
        return Response(serializer.data)


class TestVisitView(APIView):
    def get(self, request):
        visit_list = ['8816','8691','500','820','48','4976','972','5092','8703','8693']
        token_visit_list = ['5638','2935','2856']
        # get query parameters
        token = self.request.query_params.get('token', None)
        max_items = self.request.query_params.get('max_items', 10)

        # if token is not specified
        if token is None:
            # return all visits subject to max_items
            return Response(visit_list[:int(max_items)])
        else:
            # return visits for user with token'
            return Response(token_visit_list[:int(max_items)])
        



class TestCartView(APIView):
    def get(self, request):
        cart_list = ['4926','2856','500','6764','48','381','5554','5623','5277','5179']
        token_cart_list = ['381','48']
        # get query parameters
        token = self.request.query_params.get('token', None)
        max_items = self.request.query_params.get('max_items', 10)

        # if token is not specified
        if token is None:
            # return all visits subject to max_items
            return Response(cart_list[:int(max_items)])
        else:
            # return visits for user with token'
            return Response(token_cart_list[:int(max_items)])

class TestVisitsUserView(APIView):
    def get(self,request):
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)
        if token !='test_token' or app_name is None: # respond with error
            return Response({'error': 'token and app_name must be specified'})
        visit_list = ['1596','1702','2023','2250','3332','4610','5208','5408','7617','8019']
        return Response(visit_list)

class TestCartsUserView(APIView):
    def get(self,request):
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)
        if token !='test_token' or app_name is None: # respond with error
            return Response({'error': 'token and app_name must be specified'})
        visit_list = ['7456','7129','6970','5396','3804','2767','2502','771','60','1432']
        return Response(visit_list)
