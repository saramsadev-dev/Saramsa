#!/bin/bash
set -e

echo "Starting Django application..."
cd /home/site/wwwroot

echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 4 apis.wsgi:application
