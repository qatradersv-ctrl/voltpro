# PowerShell deployment script for VoltPro
# This script handles migrations and deployment

Write-Host "Starting deployment..."

# Pull latest changes
git pull origin master

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files (if needed)
python manage.py collectstatic --noinput

Write-Host "Deployment completed successfully!"
