# import
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from apiresult.models import *
from notification.models import *
from django.core.cache import cache
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from apiresult.utils.config import *
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

class SubmitContactView(APIView):
    def post(self,request):
        data = json.loads(request.body)
        app_name = data.get('app_name')
        alme_user_token = data.get('alme_user_token')
        phone = data.get('phone')
        name = data.get('name')
        email = data.get('email', '')
        
        i_users = IdentifiedUser.objects.filter(app_name=app_name)
        i_user = None
        for u in i_users:
            if alme_user_token in u.tokens:    
                i_user = u
                break
        if i_user:
            # user found, update name, email and phone number for IdentifiedUser
            i_user.name = name
            i_user.phone = phone
            i_user.email = email
            i_user.last_visit = datetime.now()
        else:
            # create new IdentifiedUser
            i_user = IdentifiedUser(
                app_name=app_name,
                name=name,
                phone=phone,
                email=email,
                tokens=[alme_user_token],
                created_at=datetime.now(),
                last_visit=datetime.now()
            )
        # try saving user else return error response
        try:
            i_user.save()
            return Response({"status": "success"}, status=200)
        except Exception as e:
            logger.info("Error in sending Alme contact details: %s" % str(e))
            return Response({"Error in sending Alme contact details": str(e)})


class SaleNotificationView(APIView):
    def get(self,request):
        logger.info("Sale notification request received")
        # log the payload
        logger.info("Payload: %s" % request.query_params)
        
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)
        session_key = self.request.query_params.get('session_id', None)  

        if token is None or app_name is None or session_key is None: # respond with error
           
            logger.info("Error in sale notification: token, app_name, session_id must be specified")
            logger.info("token: %s, app_name: %s, session_id: %s" % (token, app_name, session_key))
            return Response({'error': 'token, app_name, session_id must be specified'})
        
        
        try:
            session = Sessions.objects.get(session_key=session_key,app_name=app_name)
        except:
            
            logger.info("Error in sale notification: session not found for token: %s, app_name: %s, session_id: %s" % (token, app_name, session_key))
            return Response({'error': 'session not found'})

        try:
            user = User.objects.get(token=token, app_name=app_name)
        except:
           
            logger.info("Error in sale notification: user not found for token: %s, app_name: %s, session_id: %s" % (token, app_name, session_key))
            return Response({'error': 'user not found'})

        if user.purchase_last_4_sessions == 1:
            return Response({'sale_notification': False})
        if session.events_count is None or \
                session.page_load_count is None or \
                session.total_products_visited is None:
                    return Response({'error': 'One or more session parameters are None'})
        
         # Check if the threshold values are already in cache
        cache_key = f'sale_notification_threshold_{app_name}'
        threshold = cache.get(cache_key)

        if threshold is None:
            # Threshold values not found in cache, fetch from the database
            try:
                threshold = SaleNotificationThreshold.objects.get(app_name=app_name)
                # Store the threshold values in cache for future use
                cache.set(cache_key, threshold, timeout=3600)  # Cache for 1 hour (adjust as needed)
            except SaleNotificationThreshold.DoesNotExist:
                logger.info("Error in sale notification: threshold not found for app_name: %s" % app_name)
                return Response({'error': 'threshold not found'})
            
        # log the threshold values
        logger.info("Threshold values for app_name: %s" % app_name)
        logger.info(f"events_count_threshold: {threshold.events_count_threshold}")
        logger.info(f"page_load_count_threshold: {threshold.page_load_count_threshold}")
        logger.info(f"total_products_visited_threshold: {threshold.total_products_visited_threshold}")
        

        # log the session values
        logger.info("Session values for app_name: %s" % app_name)
        logger.info(f"events_count: {session.events_count}")
        logger.info(f"page_load_count: {session.page_load_count}")
        logger.info(f"total_products_visited: {session.total_products_visited}")
         
        if session.events_count >= threshold.events_count_threshold or \
        session.page_load_count >= threshold.page_load_count_threshold or \
        session.total_products_visited >= threshold.total_products_visited_threshold:
            return Response({'sale_notification': True})
        
        return Response({'sale_notification': False})

   
    





