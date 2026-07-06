import os
import sys

# Ensure the app directory is on the Python path
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lamlibaas_api.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
