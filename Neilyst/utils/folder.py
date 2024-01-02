import os

def check_folder_exists(path):
    return os.path.exists(path)

def creat_folder(path):
    os.makedirs(path, exist_ok=True)

def get_current_path():
    return os.getcwd()