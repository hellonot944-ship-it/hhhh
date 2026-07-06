#!/bin/bash
set -e
export PYTHONPATH=/app
echo "Starting Lamlibaas API..."
echo "PORT=${PORT:-8000}"
echo "PYTHONPATH=$PYTHONPATH"
cd /app
python manage.py migrate --noinput
mkdir -p staticfiles
python manage.py collectstatic --noinput --clear
exec gunicorn lamlibaas_api.wsgi --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
