# clickserver/model_loader.py

import os
import pickle
from django.conf import settings
import sys 
import logging
logger = logging.getLogger(__name__)

global_models = {}

def load_all_models():
    global global_models
    models_dir = os.path.join(settings.BASE_DIR, 'clickserver', 'models')

    try:
        for filename in os.listdir(models_dir):
            if filename.endswith('.pkl'):
                model_name = os.path.splitext(filename)[0]
                model_path = os.path.join(models_dir, filename)
                with open(model_path, 'rb') as f:
                    try:
                        model = pickle.load(f)
                        global_models[model_name] = model
                    except Exception as e:
                        logger.info(f"Error loading model {model_name}: {e}")
        logger.info(f"Loaded {len(global_models)} models")
    except Exception as e:
        logger.info(f"Error loading models: {e}")
def get_model(model_name):
    return global_models.get(model_name)