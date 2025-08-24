# MINGUS Application Deployment Guide

## Overview

This guide covers deploying the MINGUS application with article library functionality in both development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended for production)
- **Storage**: Minimum 10GB free space
- **Network**: Internet access for downloading images and dependencies

### Required Accounts

- **OpenAI API**: For article classification and AI recommendations
- **Email Service**: For article extraction (optional)
- **Monitoring**: Sentry for error tracking (optional)

## Development Deployment

### Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd mingus-application
   ```

2. **Configure Environment**:
   ```bash
   # Copy development environment template
   cp config/development.env .env
   
   # Edit .env with your values
   nano .env
   ```

3. **Deploy Development Environment**:
   ```bash
   ./deploy_dev.sh deploy
   ```

4. **Access the Application**:
   - **Flask App**: http://localhost:5000
   - **API Health**: http://localhost:5000/api/health
   - **Celery Monitor**: http://localhost:5555
   - **PostgreSQL**: localhost:5432
   - **Redis**: localhost:6379

### Development Commands

```bash
# View service status
./deploy_dev.sh status

# View logs
./deploy_dev.sh logs web
./deploy_dev.sh logs celery

# Restart services
./deploy_dev.sh restart

# Stop all services
./deploy_dev.sh stop

# Clean up everything
./deploy_dev.sh clean

# Open shell in container
./deploy_dev.sh shell web
./deploy_dev.sh shell db

# Database operations
./deploy_dev.sh db          # Connect to PostgreSQL
./deploy_dev.sh migrate     # Run migrations

# Testing
./deploy_dev.sh test        # Run all tests
./deploy_dev.sh test tests/test_articles.py  # Run specific test

# Enable advanced search
./deploy_dev.sh search      # Start Elasticsearch
```

### Development Features

- **Hot Reloading**: Code changes automatically reload
- **Debug Mode**: Detailed error pages and logging
- **Development Database**: Local PostgreSQL with sample data
- **Celery Monitoring**: Flower interface for task monitoring
- **Volume Mounting**: Code changes reflect immediately

## Production Deployment

### Quick Start

1. **Prepare Production Environment**:
   ```bash
   # Copy production environment template
   cp config/production.env .env
   
   # Edit .env with production values
   nano .env
   ```

2. **Deploy Production Environment**:
   ```bash
   ./deploy_production.sh deploy
   ```

3. **Access Production Services**:
   - **Application**: https://your-domain.com
   - **API Health**: https://your-domain.com/api/health
   - **Monitoring**: http://your-domain.com:3000 (Grafana)

### Production Commands

```bash
# View deployment status
./deploy_production.sh status

# View service logs
./deploy_production.sh logs mingus-app
./deploy_production.sh logs celery-worker

# Restart services
./deploy_production.sh restart

# Stop all services
./deploy_production.sh stop

# Clean deployment
./deploy_production.sh clean
```

### Production Features

- **SSL/TLS**: HTTPS with modern cipher suites
- **Load Balancing**: Nginx reverse proxy
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **High Availability**: Health checks and restart policies
- **Security**: Non-root containers, security headers
- **Performance**: Redis caching, database optimization

## Configuration

### Environment Variables

#### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database
POSTGRES_PASSWORD=secure-password

# Redis
REDIS_URL=redis://host:port/database
CELERY_BROKER_URL=redis://host:port/database

# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# OpenAI
OPENAI_API_KEY=sk-proj-your-openai-key
```

#### Optional Variables

```bash
# Email Processing
MAC_EMAIL_ADDRESS=your_email@mac.com
MAC_EMAIL_APP_PASSWORD=your-app-password

# Feature Flags
ENABLE_ARTICLE_LIBRARY=true
ENABLE_AI_RECOMMENDATIONS=true
ENABLE_CULTURAL_PERSONALIZATION=true

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# Performance
CACHE_TYPE=redis
DATABASE_POOL_SIZE=20
```

### Feature Flags

| Flag | Description | Default |
|------|-------------|---------|
| `ENABLE_ARTICLE_LIBRARY` | Enable article library functionality | `true` |
| `ENABLE_AI_RECOMMENDATIONS` | Enable AI-powered recommendations | `true` |
| `ENABLE_CULTURAL_PERSONALIZATION` | Enable cultural personalization | `true` |
| `ENABLE_ADVANCED_SEARCH` | Enable Elasticsearch search | `true` |
| `ENABLE_ANALYTICS` | Enable article analytics | `true` |
| `ENABLE_SOCIAL_SHARING` | Enable social sharing features | `true` |

## Monitoring

### Health Checks

- **Application**: `GET /api/health`
- **Database**: PostgreSQL connection check
- **Redis**: Redis ping check
- **Celery**: Worker status check

### Metrics

- **Application Metrics**: Request rates, response times, errors
- **Database Metrics**: Connection pool, query performance
- **Redis Metrics**: Memory usage, hit rates
- **Celery Metrics**: Task queue, worker status

### Logging

- **Application Logs**: Flask application logs
- **Celery Logs**: Background task logs
- **Database Logs**: PostgreSQL logs
- **Nginx Logs**: Access and error logs

### Monitoring Tools

- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Flower**: Celery task monitoring
- **Sentry**: Error tracking and alerting

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database status
docker-compose -f docker-compose.dev.yml ps db

# View database logs
docker-compose -f docker-compose.dev.yml logs db

# Connect to database
docker exec -it mingus-db-dev psql -U mingus -d mingus
```

#### 2. Redis Connection Issues

```bash
# Check Redis status
docker-compose -f docker-compose.dev.yml ps redis

# Test Redis connection
docker exec -it mingus-redis-dev redis-cli ping
```

#### 3. Celery Worker Issues

```bash
# Check Celery status
docker-compose -f docker-compose.dev.yml ps celery

# View Celery logs
docker-compose -f docker-compose.dev.yml logs celery

# Check task queue
docker exec -it mingus-celery-dev celery -A backend.celery_app inspect active
```

#### 4. Application Startup Issues

```bash
# Check application logs
docker-compose -f docker-compose.dev.yml logs web

# Check health endpoint
curl http://localhost:5000/api/health

# Restart application
docker-compose -f docker-compose.dev.yml restart web
```

### Performance Issues

#### 1. Slow Database Queries

```bash
# Enable query logging
export DATABASE_ECHO=true

# Check database indexes
docker exec -it mingus-db-dev psql -U mingus -d mingus -c "\d+ articles"
```

#### 2. High Memory Usage

```bash
# Check container resource usage
docker stats

# Adjust Redis memory limits
# Edit docker-compose.dev.yml or docker-compose.production.yml
```

#### 3. Slow API Responses

```bash
# Check Redis cache hit rate
docker exec -it mingus-redis-dev redis-cli info memory

# Check application logs for slow queries
docker-compose -f docker-compose.dev.yml logs web | grep "slow"
```

### Security Issues

#### 1. SSL Certificate Issues

```bash
# Check SSL certificate
openssl s_client -connect your-domain.com:443

# Update certificates in nginx/ssl/
# Restart nginx container
docker-compose -f docker-compose.production.yml restart nginx
```

#### 2. Rate Limiting Issues

```bash
# Check rate limit configuration
docker exec -it mingus-web-dev env | grep RATE_LIMIT

# Adjust rate limits in .env file
```

## Maintenance

### Regular Tasks

#### 1. Database Maintenance

```bash
# Backup database
docker exec -it mingus-db-dev pg_dump -U mingus mingus > backup.sql

# Run database migrations
./deploy_dev.sh migrate

# Vacuum database
docker exec -it mingus-db-dev psql -U mingus -d mingus -c "VACUUM ANALYZE;"
```

#### 2. Log Rotation

```bash
# Check log sizes
du -sh logs/*

# Rotate logs
docker-compose -f docker-compose.dev.yml exec web logrotate /etc/logrotate.conf
```

#### 3. Cache Management

```bash
# Clear Redis cache
docker exec -it mingus-redis-dev redis-cli FLUSHALL

# Check cache statistics
docker exec -it mingus-redis-dev redis-cli info memory
```

### Updates

#### 1. Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.dev.yml build

# Restart services
docker-compose -f docker-compose.dev.yml up -d
```

#### 2. Dependency Updates

```bash
# Update Python dependencies
docker exec -it mingus-web-dev pip install -r requirements.txt --upgrade

# Update system packages
docker exec -it mingus-web-dev apt-get update && apt-get upgrade -y
```

### Backup and Recovery

#### 1. Database Backup

```bash
# Create backup
docker exec -it mingus-db-dev pg_dump -U mingus mingus > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker exec -i mingus-db-dev psql -U mingus mingus < backup.sql
```

#### 2. File Backup

```bash
# Backup data directory
tar -czf data_backup_$(date +%Y%m%d_%H%M%S).tar.gz data/

# Restore data
tar -xzf data_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Support

### Getting Help

1. **Check Logs**: Use the logging commands above
2. **Health Checks**: Verify all services are running
3. **Documentation**: Review this guide and code comments
4. **Issues**: Create an issue in the repository

### Useful Commands

```bash
# System information
docker version
docker-compose version
docker system info

# Container information
docker ps -a
docker images
docker network ls

# Resource usage
docker stats
docker system df

# Clean up
docker system prune -f
docker volume prune -f
```

## Next Steps

1. **Customize Configuration**: Adjust settings for your environment
2. **Set Up Monitoring**: Configure alerts and dashboards
3. **Implement CI/CD**: Set up automated deployment pipeline
4. **Security Hardening**: Review and enhance security measures
5. **Performance Tuning**: Optimize based on usage patterns
6. **Backup Strategy**: Implement automated backup procedures
