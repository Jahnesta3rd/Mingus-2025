# MINGUS Meme Splash Page Feature - Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Production Deployment](#production-deployment)
5. [AWS S3 Setup](#aws-s3-setup)
6. [Database Migration](#database-migration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Security Configuration](#security-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Performance Optimization](#performance-optimization)

## Overview

This guide provides step-by-step instructions for deploying the MINGUS meme splash page feature in both development and production environments. The feature includes:

- Meme content management and display
- User preference management
- Image upload and storage with AWS S3
- Analytics and engagement tracking
- Comprehensive security measures
- Monitoring and logging

## Prerequisites

### Required Software
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)

### Required Accounts
- AWS Account (for S3 storage)
- Sentry Account (for error tracking)
- Supabase Account (for database)

### Required Environment Variables
Copy `env.example` to `.env` and configure:

```bash
# Core Application
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=postgresql://user:password@host:port/database

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=mingus-meme-images
AWS_REGION=us-east-1

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
```

## Local Development Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone <repository-url>
cd mingus-application

# Copy environment file
cp env.example .env

# Edit environment variables for local development
nano .env
```

### 2. Start Local Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Or start specific services
docker-compose up -d db redis
docker-compose up -d app celery-worker celery-beat
```

### 3. Run Database Migrations

```bash
# Run migrations
docker-compose exec app flask db upgrade

# Or manually
docker-compose exec app python -c "
from backend.database import get_db_session
from backend.models import Base, engine
Base.metadata.create_all(bind=engine)
"
```

### 4. Seed Initial Data

```bash
# Run the seeding script
docker-compose exec app python scripts/seed_meme_data.py
```

### 5. Verify Setup

```bash
# Check application health
curl http://localhost:5000/health

# Check database connection
docker-compose exec app python -c "
from backend.database import get_db_session
session = get_db_session()
print('Database connection successful')
session.close()
"
```

## Production Deployment

### Option 1: Docker Deployment

#### 1. Build Production Image

```bash
# Build optimized production image
docker build -t mingus-app:latest .

# Tag for registry
docker tag mingus-app:latest your-registry/mingus-app:latest
```

#### 2. Deploy with Docker Compose

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to cloud platform
docker-compose -f docker-compose.prod.yml push
```

#### 3. Configure Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/mingus
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static file caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Option 2: Cloud Platform Deployment

#### Heroku Deployment

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create app
heroku create your-mingus-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis addon
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
heroku config:set AWS_ACCESS_KEY_ID=your-aws-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret

# Deploy
git push heroku main

# Run migrations
heroku run flask db upgrade

# Seed data
heroku run python scripts/seed_meme_data.py
```

#### AWS ECS Deployment

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name mingus-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
    --cluster mingus-cluster \
    --service-name mingus-service \
    --task-definition mingus-task:1 \
    --desired-count 2
```

## AWS S3 Setup

### 1. Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://mingus-meme-images

# Configure bucket for public read access
aws s3api put-bucket-policy --bucket mingus-meme-images --policy '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::mingus-meme-images/*"
        }
    ]
}'
```

### 2. Configure CORS

```bash
# Create CORS configuration
aws s3api put-bucket-cors --bucket mingus-meme-images --cors-configuration '{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag"]
        }
    ]
}'
```

### 3. Setup CloudFront (Optional)

```bash
# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json

# Update environment variables
export AWS_CLOUDFRONT_DISTRIBUTION_ID=your-distribution-id
```

## Database Migration

### 1. Run Core Migrations

```bash
# Run existing migrations
flask db upgrade

# Run meme feature migrations
psql $DATABASE_URL -f migrations/015_meme_feature_enhancements.sql
```

### 2. Verify Migration

```bash
# Check migration status
flask db current

# Verify tables exist
psql $DATABASE_URL -c "\dt memes"
psql $DATABASE_URL -c "\dt user_meme_*"
```

### 3. Rollback (if needed)

```bash
# Rollback meme feature
psql $DATABASE_URL -f migrations/015_meme_feature_enhancements_rollback.sql

# Or rollback to previous version
flask db downgrade
```

## Monitoring and Logging

### 1. Setup Sentry

```bash
# Install Sentry CLI
pip install sentry-cli

# Initialize Sentry
sentry-cli init

# Configure DSN in environment
export SENTRY_DSN=https://your-sentry-dsn
```

### 2. Setup Logging

```bash
# Create log directories
mkdir -p logs

# Configure log rotation
sudo logrotate -f /etc/logrotate.d/mingus
```

### 3. Monitor Application

```bash
# Check application logs
docker-compose logs -f app

# Check specific log files
tail -f logs/app.log
tail -f logs/error.log
tail -f logs/meme_feature.log

# Monitor performance
docker stats
```

## Security Configuration

### 1. File Upload Security

```python
# Verify security settings in your application
from backend.security.meme_security import MemeSecurityValidator

validator = MemeSecurityValidator(config)
# Test file validation
is_valid, error = validator.validate_file_upload(file, filename)
```

### 2. Rate Limiting

```bash
# Test rate limiting
curl -H "Content-Type: application/json" \
     -d '{"test": "data"}' \
     http://localhost:5000/api/meme/upload

# Check Redis for rate limit data
redis-cli keys "rate_limit:*"
```

### 3. Content Moderation

```python
# Test content validation
from backend.security.meme_security import validate_meme_upload

is_valid, error = validate_meme_upload(
    file, filename, caption, alt_text, category
)
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check database status
docker-compose ps db

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db

# Verify connection string
echo $DATABASE_URL
```

#### 2. S3 Upload Failures

**Problem**: `botocore.exceptions.NoCredentialsError`

**Solution**:
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Test S3 access
aws s3 ls s3://mingus-meme-images
```

#### 3. Redis Connection Issues

**Problem**: `redis.exceptions.ConnectionError`

**Solution**:
```bash
# Check Redis status
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Test Redis connection
docker-compose exec app python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
r.ping()
print('Redis connection successful')
"
```

#### 4. Image Processing Errors

**Problem**: `PIL.UnidentifiedImageError`

**Solution**:
```bash
# Install additional image libraries
docker-compose exec app apt-get update
docker-compose exec app apt-get install -y libjpeg-dev libpng-dev

# Rebuild image with dependencies
docker-compose build --no-cache app
```

#### 5. Memory Issues

**Problem**: `MemoryError` during image processing

**Solution**:
```bash
# Increase Docker memory limit
docker-compose down
docker-compose up -d --scale app=1

# Or optimize image processing
export IMAGE_OPTIMIZATION_QUALITY=75
export IMAGE_MAX_SIZE_MB=5
```

#### 6. Performance Issues

**Problem**: Slow meme loading

**Solution**:
```bash
# Check database indexes
psql $DATABASE_URL -c "\d+ memes"

# Add missing indexes
psql $DATABASE_URL -c "
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memes_category_active 
ON memes (category, is_active);
"

# Enable query logging
psql $DATABASE_URL -c "SET log_statement = 'all';"
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
# Set debug environment variable
export FLASK_DEBUG=1
export FLASK_ENV=development

# Restart application
docker-compose restart app

# Check debug logs
docker-compose logs -f app
```

### Health Checks

```bash
# Application health
curl http://localhost:5000/health

# Database health
docker-compose exec app python -c "
from backend.database import get_db_session
session = get_db_session()
result = session.execute('SELECT 1').scalar()
print(f'Database health: {result}')
session.close()
"

# Redis health
docker-compose exec redis redis-cli ping

# S3 health
aws s3 ls s3://mingus-meme-images --max-items 1
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_memes_category_active_priority 
ON memes (category, is_active, priority DESC);

CREATE INDEX CONCURRENTLY idx_user_meme_history_user_interaction 
ON user_meme_history (user_id, interaction_type, viewed_at DESC);

-- Analyze table statistics
ANALYZE memes;
ANALYZE user_meme_history;
```

### 2. Caching Strategy

```python
# Enable Redis caching
from backend.services.cache_service import CacheService

cache = CacheService()
cache.set('meme:popular', popular_memes, ttl=3600)
```

### 3. Image Optimization

```bash
# Optimize image processing
export IMAGE_OPTIMIZATION_QUALITY=85
export IMAGE_THUMBNAIL_SIZE=300x300
export IMAGE_PREVIEW_SIZE=800x600

# Enable WebP conversion
export ENABLE_WEBP_CONVERSION=true
```

### 4. CDN Configuration

```bash
# Configure CloudFront caching
aws cloudfront create-cache-policy \
    --name "MemeImagesCache" \
    --default-ttl 86400 \
    --max-ttl 31536000 \
    --min-ttl 0
```

## Support and Maintenance

### Regular Maintenance Tasks

```bash
# Daily health checks
./scripts/health_check.sh

# Weekly database maintenance
./scripts/db_maintenance.sh

# Monthly log rotation
./scripts/rotate_logs.sh

# Quarterly security updates
./scripts/security_update.sh
```

### Monitoring Alerts

Set up alerts for:
- Application errors (Sentry)
- Database connection issues
- S3 upload failures
- High memory usage
- Slow response times

### Backup Strategy

```bash
# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# S3 backup
aws s3 sync s3://mingus-meme-images s3://mingus-meme-images-backup

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

For additional support, refer to the project documentation or contact the development team.
