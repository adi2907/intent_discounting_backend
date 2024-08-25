# notification/views.py
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
from datetime import datetime,timedelta
import numpy as np
import requests

import logging
logger = logging.getLogger(__name__)

# from clickserver.model_loader import global_models,get_model,load_all_models

# def initialize_models():
#     if not global_models:
#         load_all_models()
#         logger.info("Models loaded successfully in notification/views.py")
#     else:
#         logger.info("Models already loaded in notification/views.py")

# global_prediction_model = None

# def get_prediction_model():
#     global global_prediction_model
#     if global_prediction_model is None:
#         try:
#             model_path = '/home/ubuntu/clickstream/django/clickserver/clickserver/models/desisandook.myshopify.com_model.pkl'
#             with open(model_path,'rb') as f:
#                 global_prediction_model = pickle.load(f)
#             logger.info("Predication model desisandook loaded successfully in notification/views.py")

#         except Exception as e:
#             logger.info("Error loading desisandook.myshopify.com_model: {e}")
#             global_prediction_model = None
#     return global_prediction_model

def get_prediction_model():
    # Return the base URL for TensorFlow Serving
    return "http://localhost:8502/v1/models/desisandook:predict"

def meets_criteria(user,app_name):
        cache_key = f'sale_notification_criteria_{app_name}'
        criteria = cache.get(cache_key)
        if criteria is None:
            # Criteria values not found in cache, fetch from the database
            try:
                criteria = SaleNotificationCriteria.objects.get(app_name=app_name)
                cache.set(cache_key, criteria, timeout=3600)
            except SaleNotificationCriteria.DoesNotExist:
                # set the cache_key to 0
                cache.set(cache_key, '0', timeout=3600)
                return True
        
        if criteria != '0':
            # check days_since_last_purchase
            if criteria.days_since_last_purchase is not None:
                days_since_last_purchased = criteria.days_since_last_purchase
                # find the last purchase date of the user
                latest_purchase_date = Purchase.objects.filter(user=user).order_by('-created_at').first()
                if latest_purchase_date is not None:
                    # check if the last purchase date is within the days_since_last_purchase
                    if (datetime.now() - latest_purchase_date.created_at).days <= days_since_last_purchased:
                        return False
            # check days_since_last_visit
            if criteria.days_since_last_visit is not None:
                days_since_last_visit = criteria.days_since_last_visit
                if (datetime.now() - user.last_visit).days <= days_since_last_visit:
                    #return Response({'sale_notification': False,'criteria_met': False})
                    return False
        return True

class NewSaleNotificationView(APIView):
    def get(self,request):
        
        token = self.request.query_params.get('token', None)
        app_name = self.request.query_params.get('app_name', None)
        session_key = self.request.query_params.get('session_id', None)  
        if token is None or app_name is None or session_key is None: # respond with error
           
            logger.info("Error in sale notification: token, app_name, session_id must be specified")
            return Response({'error': 'token, app_name, session_id must be specified'})
        
        sale_notification_session = SaleNotificationSessions.objects.filter(session_key=session_key).first()
        if sale_notification_session is None:
            logger.info("Error in sale notification: session not found")
            return Response({'error': 'session not found'})
        
        # check if number of events in sale_notification_session is more than 10
        if sale_notification_session.event_sequence_length < 10:
            return Response({'sale_notification': False})
        
        # check if sale notification is part of control or experimental group
        if sale_notification_session.experiment_group == 'control':
            return Response({'sale_notification': False,'experiment_group': False})

        #TODO: BELOW CODE NEEDS TO BE ENABLED AFTER TESTING
        user = sale_notification_session.user
        if user is None:
            logger.info("Error in sale notification: user not found")
            return Response({'error': 'user not found'})
        #check if the user meets the criteria
        check_user_criteria = meets_criteria(user,app_name)
        if not check_user_criteria:
           return Response({'sale_notification': False,'criteria_met': False})

        show_notification = predict_sale_notification(sale_notification_session)
        return Response({'sale_notification': show_notification})

def predict_sale_notification(sale_notification_session):
    MAX_SEQUENCE_LENGTH = 10
    #model = get_prediction_model()
    model_url = get_prediction_model()
    sequence_length = min(sale_notification_session.event_sequence_length, MAX_SEQUENCE_LENGTH)
    X_event_category = np.array(sale_notification_session.encoded_events_category_list[-sequence_length:])
    X_time_spent = np.array(sale_notification_session.time_diff_list[-sequence_length:])

    # Reshape the input to match the model's expected input shape
    X = np.stack([X_event_category, X_time_spent], axis=-1)
    X = X.reshape(1, sequence_length, 2)  # Add batch dimension

    # Prepare data for TensorFlow Serving
    data = {
        "inputs": X.tolist()  # Send the list
    }
    logger.info(f"Prepared data to send to TensorFlow Serving: {json.dumps(data, indent=2)}")

    # try:
    #     prob_prediction = model.predict(X)
    # except Exception as e:
    #     logger.error(f"Model prediction failed: {str(e)}")
    #     return False
    threshold = 0.3
    try:
        response = requests.post(model_url, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        logger.info(f"Response from TensorFlow Serving: {response.text}")
        prob_prediction = response.json()['outputs'][0]
        show_notification = prob_prediction[1] < threshold
        logger.info(f"Session: {sale_notification_session.session_key} Prediction probability: {prob_prediction[1]}, Threshold: {threshold}, Show notification: {show_notification}")
        return show_notification
    except requests.exceptions.RequestException as e:
        logger.info(f"RequestException during model prediction: {str(e)}")
        return False
    except Exception as e:
        logger.info(f"Unexpected error during model prediction: {str(e)}")
        return False

  


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
            i_user.name = i_user.name or name
            i_user.phone = i_user.phone or phone
            i_user.email = i_user.email or email
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
        except Exception as e:
            logger.info("Error in sending Alme contact details: %s" % str(e))
            return Response({"Error in sending Alme contact details": str(e)})

        user,created = User.objects.get_or_create(
            app_name=app_name,
            token = alme_user_token,
            defaults={
                'first_visit': datetime.now(),
                'last_visit': datetime.now(),
                'last_updated': datetime.now(),
            }
        )
        user.identified_user_id = i_user.id
        user.save()
        return Response({"status": "success"}, status=200)
    


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
        
        
        # Using only the latest available session and not the session sent by the javascript client

        try:
            # Get the user based on the token and app_name
            user = User.objects.get(token=token, app_name=app_name)

            # Get the most recent active session for this user
            session = Sessions.objects.filter(
                user=user,
                app_name=app_name,
                is_active=True
            ).order_by('-session_start').first()

            if not session:
                logger.info(f"Error in sale notification: no active session found for user with token: {token}, app_name: {app_name}")
                return Response({'error': 'no active session found'})

        except User.DoesNotExist:
            logger.info(f"Error in sale notification: user not found for token: {token}, app_name: {app_name}")
            return Response({'error': 'user not found'})
        except Exception as e:
            logger.info(f"Error in sale notification: {str(e)}")
            return Response({'error': 'An unexpected error occurred'})


        if user.purchase_last_4_sessions == 1:
            return Response({'sale_notification': False,'criteria_met': False})
        
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
            
        # Check if there's any criteria for the user
        cache_key = f'sale_notification_criteria_{app_name}'
        criteria = cache.get(cache_key)
        if criteria is None:
            # Criteria values not found in cache, fetch from the database
            try:
                criteria = SaleNotificationCriteria.objects.get(app_name=app_name)
                cache.set(cache_key, criteria, timeout=3600)
            except SaleNotificationCriteria.DoesNotExist:
                # set the cache_key to 0
                cache.set(cache_key, '0', timeout=3600)

        if criteria != '0':
            # check days_since_last_purchase
            if criteria.days_since_last_purchase is not None:
                days_since_last_purchased = criteria.days_since_last_purchase
                # find the last purchase date of the user
                latest_purchase_date = Purchase.objects.filter(user=user).order_by('-created_at').first()
                if latest_purchase_date is not None:
                    # check if the last purchase date is within the days_since_last_purchase
                    if (datetime.now() - latest_purchase_date.created_at).days <= days_since_last_purchased:
                        return Response({'sale_notification': False,'criteria_met': False})
            # check days_since_last_visit
            if criteria.days_since_last_visit is not None:
                days_since_last_visit = criteria.days_since_last_visit
                if (datetime.now() - user.last_visit).days <= days_since_last_visit:
                    return Response({'sale_notification': False,'criteria_met': False})
                
        if session.events_count >= threshold.events_count_threshold or \
            session.page_load_count >= threshold.page_load_count_threshold or \
            session.total_products_visited >= threshold.total_products_visited_threshold:
                logger.info("Sale notification true")
                return Response({'sale_notification': True})
        
       

        logger.info("Sale notification false")
        return Response({'sale_notification': False})

   
  





