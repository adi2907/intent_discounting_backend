
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from .models import *
from django.utils import timezone
from django.db.models import Count
import random
import logging
logger = logging.getLogger(__name__)


''' returns carts for user
Usage: "almeapp.com/api/carts/?token=q6wxm4v47y9&max_items=5&app_name=test_shopify"
'''
class CartView(APIView):
    
    # return cart items for user
    def get(self, request):
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)
        if not token or not app_name: 
            return Response({'error': 'token and app_name must be specified'})
        max_items = self.request.query_params.get('max_items', 10)
        
        # default query is for last 7 days, filter by token and app_name
        queryset = Cart.objects.filter(user__token=token, app_name=app_name, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        queryset = queryset.values('item__product_id').annotate(count=Count('item__product_id')).order_by('-count')[:int(max_items)]
        product_ids = [Item.objects.get(product_id=item['item__product_id']).product_id for item in queryset]
        return Response(product_ids)

''' returns visits for user in descending order of number of visits
Usage: "almeapp.com/api/visits/?token=q6wxm4v47y9&app_name=test_shopify&max_items=5"
'''
class VisitsView(APIView):

    class VisitsView(APIView):
        def get(self, request):
            token = request.query_params.get('token', None)
            app_name = request.query_params.get('app_name', None)
            if not token or not app_name: 
                return Response({'error': 'token and app_name must be specified'})

            max_items = request.query_params.get('max_items', 10)
            queryset = Visits.objects.filter(user__token=token,app_name=app_name, created_at__gte=timezone.now() - timezone.timedelta(days=7))
            
            # Annotate visit count and order by descending count
            queryset = queryset.values('item__product_id').annotate(visit_count=Count('item__product_id')).order_by('-visit_count')[:int(max_items)]
            product_ids = [Item.objects.get(product_id=item['item__product_id']).product_id for item in queryset]
            return Response(product_ids)
 

'''
Returns most visited items for the shop
Usage: "almeapp.com/api/most_visited/?app_name=test_shopify"
'''

class MostVisitedView(APIView):
    def get(self,request):
        app_name = self.request.query_params.get('app_name', None)
        if not app_name: # respond with error
            return Response({'error': 'app_name must be specified'})
            
        queryset = Visits.objects.filter(app_name=app_name, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        queryset = queryset.values('item__product_id').annotate(count=Count('item__product_id')).order_by('-count')
       
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(product_id=item['item__product_id']).product_id)
        logger.info(product_ids)
        # randomly select 10 items from product_ids
        product_ids = random.sample(product_ids, min(len(product_ids), 10))
        return Response(product_ids)
'''   
Returns most carted items
Usage: "almeapp.com/api/most_carted/?app_name=test_shopify"
'''
class MostCartedView(APIView):
    def get(self,request):
        app_name = self.request.query_params.get('app_name', None)
        if not app_name: 
            return Response({'error': 'app_name must be specified'})
            
        queryset = Cart.objects.filter(app_name=app_name, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        queryset = queryset.values('item__product_id').annotate(count=Count('item__product_id')).order_by('-count')
       
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(product_id=item['item__product_id']).product_id)
        # randomly select 10 items from product_ids
        product_ids = random.sample(product_ids, min(len(product_ids), 10))
        return Response(product_ids)
        

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





        



