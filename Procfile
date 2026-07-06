web: PYTHONPATH=/app python manage.py migrate --noinput && PYTHONPATH=/app gunicorn lamlibaas_api.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120
