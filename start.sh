#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn -w 4 -b 0.0.0.0:8000 voltpro.wsgi:application
