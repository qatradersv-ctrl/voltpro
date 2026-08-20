#!/bin/bash
# Deployment script for VoltPro
# This script handles migrations and deployment

echo "Starting deployment..."

# Pull latest changes
git pull origin master

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files (if needed)
python manage.py collectstatic --noinput

# Restart the application (adjust based on your hosting platform)
# For example, for gunicorn:
# pkill -f gunicorn
# gunicorn config.wsgi:application --bind 0.0.0.0:8000

echo "Deployment completed successfully!"
