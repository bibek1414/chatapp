#!/bin/bash

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the application using daphne (ASGI server that supports WebSockets)
exec daphne -b 0.0.0.0 -p 8000 chat_project.asgi:application