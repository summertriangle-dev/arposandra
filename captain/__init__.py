import os

def readonly_app_path(*p):
    return os.path.join(os.path.dirname(__file__), *p)
