# Part 6: Deployment Process

## Overview
This part covers deploying the Digital Asset Security application to production, including:
- Environment setup
- Security hardening
- Production configuration
- Deployment automation
- Monitoring and maintenance

## Step-by-Step Implementation

### Step 1: Production Settings

1. Create production settings file
```python
# securemyassets/settings/production.py

from .base import *
import os
from urllib.parse import urlparse

# Security settings
DEBUG = False
ALLOWED_HOSTS = [os.environ.get('ALLOWED_HOSTS', '').split(',')]

# Generate a new secret key for production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# Static and media files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# AWS S3 configuration for file storage
if os.environ.get('USE_S3', 'False') == 'True':
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.s3boto3.S3StaticStorage',
        },
    }

# Security middleware settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### Step 2: Environment Configuration

1. Create environment variables file template
```bash
# .env.example

# Django settings
DJANGO_SETTINGS_MODULE=securemyassets.settings.production
DJANGO_SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database settings
DB_NAME=securemyassets
DB_USER=dbuser
DB_PASSWORD=dbpassword
DB_HOST=localhost
DB_PORT=5432

# Redis settings
REDIS_URL=redis://localhost:6379/1

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# AWS settings
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=your-region

# Security settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Step 3: Docker Configuration

1. Create Dockerfile
```dockerfile
# Dockerfile

# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "securemyassets.wsgi:application"]
```

2. Create docker-compose.yml
```yaml
# docker-compose.yml

version: '3.8'

services:
  web:
    build: .
    command: gunicorn securemyassets.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
    expose:
      - 8000
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:6
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:1.19
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
      - ./nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### Step 4: Nginx Configuration

1. Create Nginx configuration
```nginx
# nginx/conf.d/app.conf

upstream app_server {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Other security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    location / {
        proxy_pass http://app_server;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
        client_max_body_size 100M;
    }

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /app/mediafiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

### Step 5: Deployment Scripts

1. Create deployment script
```bash
#!/bin/bash
# deploy.sh

# Exit on error
set -e

# Pull latest changes
git pull origin main

# Load environment variables
set -a
source .env
set +a

# Build and start containers
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate --noinput

# Clear cache
docker-compose exec web python manage.py clearcache

# Restart services
docker-compose restart web
```

2. Create backup script
```bash
#!/bin/bash
# backup.sh

# Exit on error
set -e

# Load environment variables
set -a
source .env
set +a

# Set backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups"
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Backup database
docker-compose exec db pg_dump -U ${DB_USER} ${DB_NAME} > ${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_FILE}

# Upload to S3 if configured
if [ "${USE_S3}" = "True" ]; then
    aws s3 cp ${BACKUP_FILE}.gz s3://${AWS_STORAGE_BUCKET_NAME}/backups/
fi

# Remove old backups (keep last 7 days)
find ${BACKUP_DIR} -type f -mtime +7 -delete
```

### Step 6: Monitoring Setup

1. Create health check endpoint
```python
# securemyassets/views.py

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from redis import Redis
from redis.exceptions import RedisError
import os

def health_check(request):
    # Check database
    db_healthy = True
    try:
        connections['default'].cursor()
    except OperationalError:
        db_healthy = False
    
    # Check Redis
    redis_healthy = True
    try:
        redis_client = Redis.from_url(os.environ.get('REDIS_URL'))
        redis_client.ping()
    except RedisError:
        redis_healthy = False
    
    status = 200 if (db_healthy and redis_healthy) else 503
    
    return JsonResponse({
        'status': 'healthy' if status == 200 else 'unhealthy',
        'database': 'up' if db_healthy else 'down',
        'cache': 'up' if redis_healthy else 'down',
    }, status=status)
```

2. Add Prometheus monitoring
```yaml
# prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'django'
    static_configs:
      - targets: ['web:8000']
```

### Step 7: CI/CD Pipeline

1. Create GitHub Actions workflow for deployment
```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SSH_HOST }}
        username: ${{ secrets.SSH_USERNAME }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /path/to/app
          ./deploy.sh
```

## Production Checklist

Before deploying:

1. Security
   - [ ] Generate new SECRET_KEY
   - [ ] Configure SSL certificates
   - [ ] Set up firewall rules
   - [ ] Enable security headers
   - [ ] Configure backup system

2. Performance
   - [ ] Enable caching
   - [ ] Configure static file serving
   - [ ] Set up CDN (optional)
   - [ ] Optimize database queries

3. Monitoring
   - [ ] Set up logging
   - [ ] Configure error tracking
   - [ ] Enable performance monitoring
   - [ ] Set up alerts

4. Backup
   - [ ] Configure database backups
   - [ ] Set up media files backup
   - [ ] Test restore procedures
   - [ ] Document recovery process

## Deployment Steps

1. Initial Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx

# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. SSL Certificate Setup
```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

3. Deploy Application
```bash
# Clone repository
git clone https://github.com/yourusername/securemyassets.git
cd securemyassets

# Set up environment
cp .env.example .env
# Edit .env with production values

# Deploy
./deploy.sh
```

## Maintenance Tasks

1. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f
```

2. Backup Verification
```bash
# Test backup
./backup.sh

# Verify backup integrity
gunzip -c backups/latest.sql.gz | psql -U ${DB_USER} test_restore
```

3. Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/securemyassets

/path/to/app/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

## Troubleshooting

### Common Deployment Issues

1. Database Connection Issues
   - Check database credentials
   - Verify network connectivity
   - Check database logs

2. Static Files Not Serving
   - Run collectstatic
   - Check nginx configuration
   - Verify file permissions

3. SSL Certificate Problems
   - Check certificate renewal
   - Verify nginx configuration
   - Check SSL settings

### Monitoring Tips
- Set up Sentry for error tracking
- Use Prometheus for metrics
- Configure Grafana dashboards
- Set up uptime monitoring