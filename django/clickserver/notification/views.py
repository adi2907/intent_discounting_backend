# import
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from apiresult.models import IdentifiedUser, User
import json
from rest_framework.views import APIView
from rest_framework.response import Response

import logging
logger = logging.getLogger(__name__)

class SubmitContactView(APIView):
    def post(self,request):
        data = json.loads(request.body)
        app_name = data.get('app_name')
        alme_user_token = data.get('alme_user_token')
        phone = data.get('phone')
        email = data.get('email')
        name = data.get('name')
        logger.info("app_name: %s, alme_user_token: %s, phone: %s, email: %s, name: %s", app_name, alme_user_token, phone, email, name)
        users = IdentifiedUser.objects.filter(app_name=app_name)
        user = None
        for u in users:
            if any(alme_user_token == token.get('token') for token in u.tokens):
                user = u
                break
        if user:
            # user found, update name, email and phone number for IdentifiedUser
            user.name = name
            user.email = email
            user.phone = phone
        else:
            # create new IdentifiedUser
            user = IdentifiedUser(
                app_name=app_name,
                name=name,
                email=email,
                phone=phone,
                tokens=[{"token": alme_user_token}]
            )
        # try saving user else return error response
        try:
            user.save()
        except Exception as e:
            return Response({"Error in sending Alme contact details": str(e)})


   
   
    




