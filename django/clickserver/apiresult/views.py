
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from .models import *
from django.utils import timezone
from django.db.models import Count

# return cart items for user
class CartView(APIView):
    
   # return cart items for user
    def get(self, request):
        token = self.request.query_params.get('token', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        max_items = self.request.query_params.get('max_items', None)

        if last_7_days is not None:
            queryset = Cart.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Cart.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Cart.objects.filter(user__token=token, created_at__range=(start_date, end_date))
        else:
            queryset = Cart.objects.filter(user__token=token)
        if max_items is not None:
            queryset = queryset[:int(max_items)]       
        queryset = queryset.values('item_id')     
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(id=item['item_id']).item_id)
        return Response(product_ids)


# return visit items for user
class VisitsView(APIView):
    def get(self, request):
        token = self.request.query_params.get('token', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        max_items = self.request.query_params.get('max_items', None)

        if last_7_days is not None:
            queryset = Visits.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Visits.objects.filter(user__token=token, created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Visits.objects.filter(user__token=token, created_at__range=(start_date, end_date))
        else:
            queryset = Visits.objects.filter(user__token=token)
        if max_items is not None:
            queryset = queryset[:int(max_items)]       
        queryset = queryset.values('item_id')     
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(id=item['item_id']).item_id)
        return Response(product_ids)


class MostVisitedView(APIView):
    def get(self,request):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        max_items = self.request.query_params.get('max_items', None)

        if last_7_days is not None:
            queryset = Visits.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Visits.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Visits.objects.filter(created_at__range=(start_date, end_date))
        else:
            queryset = Visits.objects.all()
            
        queryset = queryset.values('item_id').annotate(count=Count('item_id')).order_by('-count')
        if max_items is not None:
            queryset = queryset[:int(max_items)]       
        
        queryset = queryset.values('item_id')
       
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(id=item['item_id']).item_id)
        return Response(product_ids)
    

class MostCartedView(APIView):
    def get(self,request):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        last_7_days = self.request.query_params.get('last_7_days', None)
        last_30_days = self.request.query_params.get('last_30_days', None)
        max_items = self.request.query_params.get('max_items', None)

        if last_7_days is not None:
            queryset = Cart.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif last_30_days is not None:
            queryset = Cart.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
        elif start_date is not None and end_date is not None:
            queryset = Cart.objects.filter(created_at__range=(start_date, end_date))
        else:
            queryset = Cart.objects.all()
            
        queryset = queryset.values('item_id').annotate(count=Count('item_id')).order_by('-count')
        if max_items is not None:
            queryset = queryset[:int(max_items)]       
        queryset = queryset.values('item_id')
        product_ids = []
        for item in queryset:
            product_ids.append(Item.objects.get(id=item['item_id']).item_id)
        return Response(product_ids)