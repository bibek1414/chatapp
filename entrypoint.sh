#!/bin/bash

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the application using gunicorn
exec gunicorn chat_project.wsgi:application --bind 0.0.0.0:8000
