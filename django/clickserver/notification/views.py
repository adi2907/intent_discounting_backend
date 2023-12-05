# import
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from apiresult.models import *
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from apiresult.utils.config import *

import logging
logger = logging.getLogger(__name__)

class SubmitContactView(APIView):
    def post(self,request):
        data = json.loads(request.body)
        app_name = data.get('app_name')
        alme_user_token = data.get('alme_user_token')
        phone = data.get('phone')
        name = data.get('name')
        
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
        else:
            # create new IdentifiedUser
            i_user = IdentifiedUser(
                app_name=app_name,
                name=name,
                phone=phone,
                tokens=[alme_user_token]
            )
        # try saving user else return error response
        try:
            i_user.save()
            return Response({"status": "success"}, status=200)
        except Exception as e:
            logger.info(str(e))
            return Response({"Error in sending Alme contact details": str(e)})


class SaleNotificationView(APIView):
    def get(self,request):
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)
        session_key = self.request.query_params.get('session_id', None)  

        if token is None or app_name is None or session_key is None: # respond with error
            return Response({'error': 'token, app_name, session_id must be specified'})
        
        
        session = Sessions.objects.get(session_key=session_key,app_name=app_name)
        user = User.objects.get(token=token, app_name=app_name)

        if user.purchase_last_4_sessions == 1:
            return Response({'sale_notification': False})
        else:
            # return True if any of the threshold values TOTAL_COUNT_THRESHOLD, PL_COUNT_THRESHOLD, 
            # SESSION_DURATION_THRESHOLD, TOTAL_PRODUCTS_THRESHOLD are met
            if session.events_count >= TOTAL_COUNT_THRESHOLD or \
                session.page_load_count >= PL_COUNT_THRESHOLD or \
                session.session_duration >= SESSION_DURATION_THRESHOLD or \
                    session.total_products_visited >= TOTAL_PRODUCTS_THRESHOLD:
                return Response({'sale_notification': True})
   
    





