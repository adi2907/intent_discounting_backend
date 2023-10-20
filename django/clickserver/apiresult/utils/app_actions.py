import json
import os

def load_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "app_actions.json"), "r") as f:
        return json.load(f)

app_actions = load_config()
