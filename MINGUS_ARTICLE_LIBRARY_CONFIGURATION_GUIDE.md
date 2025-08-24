# MINGUS Article Library - Configuration and Deployment Guide

## Overview

This guide provides comprehensive configuration and deployment setup for the MINGUS Article Library feature. The article library integrates with the existing MINGUS Flask application to provide AI-powered article classification, cultural personalization, and advanced search capabilities.

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Flask Application Integration](#flask-application-integration)
3. [Frontend Integration](#frontend-integration)
4. [Database Configuration](#database-configuration)
5. [Background Tasks](#background-tasks)
6. [Deployment Setup](#deployment-setup)
7. [Monitoring and Analytics](#monitoring-and-analytics)
8. [Security Configuration](#security-configuration)
9. [Troubleshooting](#troubleshooting)

## Environment Configuration

### Required Environment Variables

Copy the environment template and configure the required variables:

```bash
cp config/article_library.env.example .env
```

#### Core Application Settings
```bash
# Flask Application
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_APP=backend.app:create_app()

# Database
DATABASE_URL=postgresql://user:password@localhost/mingus
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-jwt-secret-key
```

#### Article Library Specific Settings
```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-your-openai-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.1

# Email Processing
MAC_EMAIL_ADDRESS=your_email@mac.com
MAC_EMAIL_APP_PASSWORD=your-app-specific-password
EMAIL_PROCESSING_RATE_LIMIT=2
EMAIL_BATCH_SIZE=50

# Article Processing
ARTICLE_SCRAPING_DELAY=2
ARTICLE_CONTENT_MAX_SIZE=50000
ARTICLE_QUALITY_THRESHOLD=0.7
CULTURAL_RELEVANCE_THRESHOLD=6.0

# Search Configuration
SEARCH_RESULTS_PER_PAGE=20
SEARCH_CACHE_TIMEOUT=3600
ELASTICSEARCH_URL=http://localhost:9200

# Assessment Configuration
ASSESSMENT_CACHE_DURATION=7200
BE_INTERMEDIATE_THRESHOLD=60
DO_INTERMEDIATE_THRESHOLD=60
HAVE_INTERMEDIATE_THRESHOLD=60
BE_ADVANCED_THRESHOLD=80
DO_ADVANCED_THRESHOLD=80
HAVE_ADVANCED_THRESHOLD=80

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ROUTES={}

# Monitoring and Analytics
ENABLE_ARTICLE_ANALYTICS=true
ANALYTICS_RETENTION_DAYS=90
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn-here

# Performance Configuration
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=mingus_articles
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0

# Security Configuration
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1
DEFAULT_RATE_LIMIT=100/hour
SEARCH_RATE_LIMIT=30/minute
API_RATE_LIMIT=1000/hour

# Feature Flags
ENABLE_AI_RECOMMENDATIONS=true
ENABLE_CULTURAL_PERSONALIZATION=true
ENABLE_ADVANCED_SEARCH=true
ENABLE_SOCIAL_SHARING=true
ENABLE_OFFLINE_READING=false

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=true
REACT_APP_API_BASE_URL=http://localhost:5000/api
REACT_APP_ENVIRONMENT=development
```

## Flask Application Integration

### 1. Register Article Library Blueprints

The article library automatically registers its blueprints with the main Flask application:

```python
# In backend/app_factory.py
from backend.integrations.article_library_integration import integrate_article_library

def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)
    
    # ... existing configuration ...
    
    # Integrate article library
    if app.config.get('ENABLE_ARTICLE_LIBRARY', True):
        integration = integrate_article_library(app)
        app.article_library_integration = integration
    
    return app
```

### 2. Available API Endpoints

The article library provides the following API endpoints:

- `GET /api/articles` - List articles with pagination and filtering
- `POST /api/articles/search` - Advanced search functionality
- `GET /api/articles/recommendations` - AI-powered recommendations
- `GET /api/articles/trending` - Trending articles
- `GET /api/articles/recent` - Recently added articles
- `GET /api/articles/featured` - Featured articles
- `GET /api/articles/popular` - Popular articles
- `GET /api/articles/topics` - Available topics
- `GET /api/articles/filters` - Available filters
- `GET /api/articles/{id}` - Article details
- `POST /api/articles/{id}/view` - Record article view
- `POST /api/articles/{id}/bookmark` - Bookmark article
- `POST /api/articles/{id}/rating` - Rate article
- `GET /api/articles/user/reading-progress` - User reading progress
- `GET /api/articles/user/bookmarks` - User bookmarks
- `GET /api/articles/user/assessment` - User assessment scores
- `POST /api/articles/user/assessment` - Submit assessment

### 3. Authentication Integration

The article library integrates with existing MINGUS authentication:

```python
# Authentication decorator
@require_auth
def protected_endpoint():
    user_id = get_user_id()
    # Access user-specific data
```

## Frontend Integration

### 1. Configuration

The frontend configuration is located in `frontend/src/config/articleLibrary.js`:

```javascript
import ARTICLE_LIBRARY_CONFIG from './config/articleLibrary';

// Access configuration
const apiBaseUrl = ARTICLE_LIBRARY_CONFIG.API_BASE_URL;
const features = ARTICLE_LIBRARY_CONFIG.FEATURES;
```

### 2. Routes Integration

Add article library routes to your React router:

```javascript
import { ARTICLE_LIBRARY_ROUTES } from './config/articleLibrary';

// In your router configuration
<Route path={ARTICLE_LIBRARY_ROUTES.LIBRARY} component={ArticleLibrary} />
<Route path={ARTICLE_LIBRARY_ROUTES.ARTICLE_DETAIL} component={ArticleDetail} />
<Route path={ARTICLE_LIBRARY_ROUTES.SEARCH} component={ArticleSearch} />
<Route path={ARTICLE_LIBRARY_ROUTES.RECOMMENDATIONS} component={ArticleRecommendations} />
```

### 3. Navigation Integration

Add article library to main navigation:

```javascript
import { ARTICLE_LIBRARY_NAVIGATION } from './config/articleLibrary';

// Add to main menu
const mainMenuItems = [
    // ... existing items ...
    ARTICLE_LIBRARY_NAVIGATION.MAIN_MENU_ITEM
];
```

## Database Configuration

### 1. Article Tables

The article library creates the following database tables:

- `articles` - Main article data
- `user_article_reads` - User reading history
- `user_article_bookmarks` - User bookmarks
- `user_article_ratings` - User ratings
- `user_article_progress` - Reading progress
- `user_assessment_scores` - Assessment scores
- `article_recommendations` - AI recommendations
- `article_analytics` - Analytics data

### 2. Database Migrations

Run database migrations to create article tables:

```bash
# Using Flask-Migrate
flask db upgrade

# Or using the deployment script
./deploy-article-library.sh
```

### 3. Database Performance

Configure database performance settings:

```bash
# Database pool settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30

# Performance settings
DB_STATEMENT_TIMEOUT=30000
DB_IDLE_TIMEOUT=60000
DB_LOCK_TIMEOUT=10000
```

## Background Tasks

### 1. Celery Configuration

The article library uses Celery for background processing:

```bash
# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ROUTES={}
```

### 2. Available Tasks

- `articles.process_email_articles` - Process articles from email
- `articles.classify_article` - AI classification of articles
- `articles.update_analytics` - Update article analytics
- `articles.cleanup_old_articles` - Cleanup old data

### 3. Running Celery Workers

```bash
# Start Celery worker
celery -A backend.tasks.article_tasks worker --loglevel=info --concurrency=4

# Start Celery beat for scheduled tasks
celery -A backend.tasks.article_tasks beat --loglevel=info
```

## Deployment Setup

### 1. Quick Deployment

Use the deployment script for easy setup:

```bash
# Make script executable
chmod +x deploy-article-library.sh

# Deploy article library
./deploy-article-library.sh

# Or with specific action
./deploy-article-library.sh deploy
```

### 2. Manual Deployment

If you prefer manual deployment:

```bash
# 1. Build Docker images
docker-compose -f docker-compose.article-library.yml build

# 2. Start services
docker-compose -f docker-compose.article-library.yml up -d

# 3. Run migrations
docker-compose -f docker-compose.article-library.yml exec mingus-app flask db upgrade

# 4. Initialize article library
docker-compose -f docker-compose.article-library.yml exec mingus-app python -c "
from backend.integrations.article_library_integration import integrate_article_library
from backend.app_factory import create_app
app = create_app()
integration = integrate_article_library(app)
"
```

### 3. Deployment Script Commands

```bash
# Deploy (default)
./deploy-article-library.sh

# Stop services
./deploy-article-library.sh stop

# Restart services
./deploy-article-library.sh restart

# View logs
./deploy-article-library.sh logs

# Check status
./deploy-article-library.sh status

# Clean up
./deploy-article-library.sh clean
```

### 4. Production Deployment

For production deployment:

1. **Update environment variables** for production settings
2. **Configure SSL certificates** in nginx/ssl directory
3. **Set up monitoring** with Prometheus and Grafana
4. **Configure backups** for database and data
5. **Set up CI/CD** pipeline for automated deployments

## Monitoring and Analytics

### 1. Prometheus Configuration

The deployment includes Prometheus for metrics collection:

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mingus-app'
    static_configs:
      - targets: ['mingus-app:5000']
    metrics_path: '/metrics'
```

### 2. Grafana Dashboards

Access Grafana at `http://localhost:3001` to view:

- Application performance metrics
- Article library usage statistics
- User engagement analytics
- System resource utilization

### 3. Application Metrics

The article library exposes metrics at `/metrics`:

- Article processing rates
- Search performance
- User engagement metrics
- API response times
- Error rates

## Security Configuration

### 1. Rate Limiting

Configure rate limiting for API endpoints:

```bash
# Rate limiting settings
DEFAULT_RATE_LIMIT=100/hour
SEARCH_RATE_LIMIT=30/minute
API_RATE_LIMIT=1000/hour
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1
```

### 2. Authentication

The article library integrates with existing MINGUS authentication:

- Session-based authentication
- JWT token support
- Role-based access control
- Assessment-based content access

### 3. Data Protection

- All user data is encrypted at rest
- API communications use HTTPS
- Database connections use SSL
- Sensitive data is masked in logs

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database connectivity
docker-compose -f docker-compose.article-library.yml exec postgres pg_isready -U mingus_user

# Check database logs
docker-compose -f docker-compose.article-library.yml logs postgres
```

#### 2. Redis Connection Issues

```bash
# Check Redis connectivity
docker-compose -f docker-compose.article-library.yml exec redis redis-cli ping

# Check Redis logs
docker-compose -f docker-compose.article-library.yml logs redis
```

#### 3. Celery Worker Issues

```bash
# Check Celery worker status
docker-compose -f docker-compose.article-library.yml exec celery-worker celery -A backend.tasks.article_tasks inspect active

# Check Celery logs
docker-compose -f docker-compose.article-library.yml logs celery-worker
```

#### 4. OpenAI API Issues

```bash
# Verify OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check API usage
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/usage
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment variables
export FLASK_DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services
./deploy-article-library.sh restart
```

### Log Analysis

View application logs:

```bash
# View all logs
docker-compose -f docker-compose.article-library.yml logs -f

# View specific service logs
docker-compose -f docker-compose.article-library.yml logs -f mingus-app
docker-compose -f docker-compose.article-library.yml logs -f celery-worker
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Database backups** - Daily automated backups
2. **Log rotation** - Weekly log cleanup
3. **Security updates** - Monthly dependency updates
4. **Performance monitoring** - Continuous monitoring
5. **Data cleanup** - Monthly old data cleanup

### Performance Optimization

1. **Database indexing** - Optimize query performance
2. **Caching strategy** - Implement Redis caching
3. **CDN setup** - Use CDN for static assets
4. **Load balancing** - Scale horizontally
5. **Monitoring** - Track performance metrics

### Scaling Considerations

1. **Horizontal scaling** - Multiple application instances
2. **Database scaling** - Read replicas and sharding
3. **Cache scaling** - Redis cluster setup
4. **Search scaling** - Elasticsearch cluster
5. **Background tasks** - Multiple Celery workers

## Conclusion

The MINGUS Article Library provides a comprehensive solution for AI-powered article management with cultural personalization and advanced search capabilities. This configuration guide covers all aspects of setup, deployment, and maintenance.

For additional support or questions, refer to the API documentation or contact the development team.
