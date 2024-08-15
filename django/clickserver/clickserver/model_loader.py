# clickserver/model_loader.py

import os
import pickle
from django.conf import settings
import sys 

global_models = {}

def load_all_models():
    global global_models
    models_dir = os.path.join(settings.BASE_DIR, 'clickserver', 'models')
    for filename in os.listdir(models_dir):
        if filename.endswith('.pkl'):
            model_name = os.path.splitext(filename)[0]
            model_path = os.path.join(models_dir, filename)
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
                global_models[model_name] = model
               
    print("Loaded all models")
def get_model(model_name):
    return global_models.get(model_name)