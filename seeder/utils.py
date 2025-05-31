from fileinput import filename
import os
import json

def get_file_path(filename: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    roles_file_path = os.path.join(current_dir, filename)
    return roles_file_path

def load_data(filename: str):
    roles_file_path = get_file_path(filename)  
    with open(roles_file_path, "r") as f:
        return json.load(f)
