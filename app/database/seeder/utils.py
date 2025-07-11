from fileinput import filename
import os
import json

def get_file_path(filename: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.abspath(os.path.join(current_dir, filename))
    return full_path

def load_data(filename: str):
    roles_file_path = get_file_path(filename)  
    with open(roles_file_path, "r") as f:
        return json.load(f)
