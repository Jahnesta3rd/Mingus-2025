# MINGUS Article Library - Celery Configuration Summary

## Overview

This document summarizes the comprehensive Celery configuration for the MINGUS Article Library feature. The setup includes background task processing, task queues, monitoring, and management tools for handling article processing, AI classification, email extraction, analytics, and maintenance tasks.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │    │   Redis Broker  │    │   Celery Worker │
│                 │───▶│                 │───▶│                 │
│ - API Endpoints │    │ - Task Queue    │    │ - Task Execution│
│ - Task Dispatch │    │ - Result Store  │    │ - Background    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Flower        │
                       │   Monitoring    │
                       │   Dashboard     │
                       └─────────────────┘
```

## Files Created

### 1. Core Celery Configuration (`backend/celery_app.py`)
- **Purpose**: Main Celery application configuration and task definitions
- **Features**: 
  - Flask integration with app context
  - Task routing for different queues
  - Comprehensive task definitions
  - Error handling and logging
  - Task utilities and monitoring

### 2. Worker Configuration (`backend/celery_worker.py`)
- **Purpose**: Worker startup and queue-specific configurations
- **Features**:
  - Queue-specific worker creation
  - Beat scheduler configuration
  - Flower monitoring setup
  - Command-line interface

### 3. Management Script (`manage_celery.py`)
- **Purpose**: Comprehensive Celery management and monitoring
- **Features**:
  - Worker startup and management
  - Queue monitoring and statistics
  - Task status checking
  - Service configuration generation

## Task Queues and Categories

### 1. Article Processing Queue (`article_processing`)
```python
@celery.task(bind=True, queue='article_processing')
def process_new_articles(self, article_urls: List[str]) -> List[Dict[str, Any]]:
    """Background task to scrape and classify new articles"""
    
@celery.task(bind=True, queue='article_processing')
def reprocess_article(self, article_id: int) -> Dict[str, Any]:
    """Background task to reprocess an existing article"""
```

**Purpose**: Handle article scraping, content extraction, and initial processing
**Tasks**:
- Scrape article content from URLs
- Extract metadata (title, author, date, etc.)
- Handle duplicate detection
- Progress tracking and error handling

### 2. Email Processing Queue (`email_processing`)
```python
@celery.task(bind=True, queue='email_processing')
def process_email_articles(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Background task to process articles from email"""
```

**Purpose**: Process articles extracted from email sources
**Tasks**:
- Extract article URLs from email content
- Process email attachments
- Handle email-specific metadata
- Batch processing of email articles

### 3. AI Classification Queue (`ai_classification`)
```python
@celery.task(bind=True, queue='ai_classification')
def classify_article_batch(self, article_ids: List[int]) -> List[Dict[str, Any]]:
    """Background task to classify multiple articles with AI"""
```

**Purpose**: AI-powered article classification and analysis
**Tasks**:
- OpenAI API integration for classification
- Be-Do-Have framework analysis
- Cultural relevance scoring
- Content quality assessment
- Topic and category classification

### 4. Recommendations Queue (`recommendations`)
```python
@celery.task(bind=True, queue='recommendations')
def update_user_recommendations(self, user_id: int, limit: int = 20) -> Dict[str, Any]:
    """Background task to update user recommendations"""

@celery.task(bind=True, queue='recommendations')
def update_all_user_recommendations(self) -> Dict[str, Any]:
    """Background task to update recommendations for all users"""
```

**Purpose**: Generate and update personalized article recommendations
**Tasks**:
- User preference analysis
- Collaborative filtering
- Content-based recommendations
- Cultural personalization
- Cache management for recommendations

### 5. Analytics Queue (`analytics`)
```python
@celery.task(bind=True, queue='analytics')
def update_article_analytics(self, article_id: int) -> Dict[str, Any]:
    """Background task to update article analytics"""

@celery.task(bind=True, queue='analytics')
def generate_daily_analytics_report(self) -> Dict[str, Any]:
    """Background task to generate daily analytics report"""
```

**Purpose**: Generate analytics and reports
**Tasks**:
- Article performance metrics
- User engagement analytics
- Content quality metrics
- Daily/weekly reports
- Trend analysis

### 6. Cleanup Queue (`cleanup`)
```python
@celery.task(bind=True, queue='cleanup')
def cleanup_old_articles(self, days_old: int = 90) -> Dict[str, Any]:
    """Background task to cleanup old articles"""

@celery.task(bind=True, queue='cleanup')
def cleanup_expired_cache(self) -> Dict[str, Any]:
    """Background task to cleanup expired cache entries"""
```

**Purpose**: Maintenance and cleanup operations
**Tasks**:
- Archive old articles
- Clean expired cache entries
- Database maintenance
- Storage optimization

## Configuration Details

### Celery Configuration
```python
celery.conf.update(
    task_routes={
        'backend.tasks.article_processing.*': {'queue': 'article_processing'},
        'backend.tasks.email_processing.*': {'queue': 'email_processing'},
        'backend.tasks.ai_classification.*': {'queue': 'ai_classification'},
        'backend.tasks.analytics.*': {'queue': 'analytics'},
        'backend.tasks.cleanup.*': {'queue': 'cleanup'},
        'backend.tasks.recommendations.*': {'queue': 'recommendations'},
    },
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_always_eager=app.config.get('TESTING', False),
    task_eager_propagates=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 hour
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
)
```

### Periodic Tasks (Beat Schedule)
```python
celery.conf.beat_schedule = {
    'update-user-recommendations': {
        'task': 'backend.celery_app.update_all_user_recommendations',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'generate-daily-analytics': {
        'task': 'backend.celery_app.generate_daily_analytics_report',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'cleanup-old-articles': {
        'task': 'backend.celery_app.cleanup_old_articles',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Weekly on Sunday at 4 AM
    },
    'cleanup-expired-cache': {
        'task': 'backend.celery_app.cleanup_expired_cache',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}
```

## Usage Examples

### Starting Workers

#### 1. Using Management Script (Recommended)
```bash
# Start worker for all queues
python manage_celery.py worker

# Start worker for specific queue
python manage_celery.py worker --queue article_processing

# Start worker with custom concurrency
python manage_celery.py worker --concurrency 8 --loglevel DEBUG

# Start worker in background
python manage_celery.py worker --background
```

#### 2. Using Worker Script Directly
```bash
# Start worker
python backend/celery_worker.py worker

# Start worker for specific queue
python backend/celery_worker.py worker --queue article_processing
```

### Starting Beat Scheduler
```bash
# Start beat scheduler
python manage_celery.py beat

# Start beat scheduler in background
python manage_celery.py beat --background
```

### Starting Flower Monitoring
```bash
# Start Flower monitoring
python manage_celery.py flower

# Access monitoring dashboard at http://localhost:5555
```

### Monitoring and Management
```bash
# List all available tasks
python manage_celery.py tasks

# Show worker status
python manage_celery.py status

# Show queue statistics
python manage_celery.py queues

# Get task status
python manage_celery.py task-status <task_id>

# Test task execution
python manage_celery.py test

# Purge all queues
python manage_celery.py purge
```

## Task Execution Examples

### Processing New Articles
```python
from backend.celery_app import celery

# Process multiple articles
article_urls = [
    'https://example.com/article1',
    'https://example.com/article2',
    'https://example.com/article3'
]

result = celery.send_task('backend.celery_app.process_new_articles', args=[article_urls])
print(f"Task ID: {result.id}")

# Check task status
from backend.celery_app import get_task_status
status = get_task_status(result.id)
print(f"Task Status: {status}")
```

### Updating User Recommendations
```python
from backend.celery_app import celery

# Update recommendations for specific user
result = celery.send_task('backend.celery_app.update_user_recommendations', args=[user_id, 20])

# Update recommendations for all users
result = celery.send_task('backend.celery_app.update_all_user_recommendations')
```

### AI Classification
```python
from backend.celery_app import celery

# Classify multiple articles
article_ids = [1, 2, 3, 4, 5]
result = celery.send_task('backend.celery_app.classify_article_batch', args=[article_ids])
```

## Production Deployment

### 1. Supervisor Configuration
```bash
# Generate supervisor configuration
python manage_celery.py supervisor

# Install supervisor configuration
sudo cp supervisor-celery.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mingus-celery:*
```

### 2. Systemd Services
```bash
# Generate systemd service files
python manage_celery.py systemd

# Install and enable services
sudo cp mingus-celery-worker.service /etc/systemd/system/
sudo cp mingus-celery-beat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mingus-celery-worker
sudo systemctl enable mingus-celery-beat
sudo systemctl start mingus-celery-worker
sudo systemctl start mingus-celery-beat
```

### 3. Docker Compose Integration
The Celery services are already integrated into the Docker Compose configuration:
```yaml
celery-worker:
  build: .
  command: python manage_celery.py worker
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - redis
    - postgres

celery-beat:
  build: .
  command: python manage_celery.py beat
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - redis
    - postgres
```

## Monitoring and Observability

### 1. Flower Dashboard
- **URL**: http://localhost:5555
- **Features**:
  - Real-time worker monitoring
  - Task execution history
  - Queue statistics
  - Worker performance metrics
  - Task cancellation and retry

### 2. Logging
```python
import logging
logger = logging.getLogger(__name__)

# Task logging
logger.info(f"Processing article {article_id}")
logger.error(f"Error processing article {article_id}: {str(e)}")
```

### 3. Metrics and Health Checks
```python
# Health check endpoint
@app.route('/api/celery/health')
def celery_health():
    try:
        inspector = celery.control.inspect()
        stats = inspector.stats()
        return jsonify({
            'status': 'healthy',
            'workers': len(stats) if stats else 0,
            'queues': get_queue_stats()
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
```

## Error Handling and Recovery

### 1. Task Retry Logic
```python
@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_article_with_retry(self, article_id):
    try:
        # Process article
        pass
    except Exception as exc:
        self.retry(exc=exc)
```

### 2. Dead Letter Queues
```python
celery.conf.update(
    task_routes={
        'backend.tasks.*': {'queue': 'default', 'exchange': 'default'},
    },
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'dead_letter': {
            'exchange': 'dead_letter',
            'routing_key': 'dead_letter',
        }
    },
    task_default_exchange_type='direct',
    task_reject_on_worker_lost=True,
    task_acks_late=True,
)
```

### 3. Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
```

## Performance Optimization

### 1. Worker Configuration
```python
# Optimize for CPU-intensive tasks
celery.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
)
```

### 2. Queue-Specific Workers
```bash
# Start dedicated workers for different queues
python manage_celery.py worker --queue article_processing --concurrency 2
python manage_celery.py worker --queue ai_classification --concurrency 1
python manage_celery.py worker --queue cleanup --concurrency 1
```

### 3. Redis Optimization
```python
# Redis connection pooling
celery.conf.update(
    broker_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
        'fanout_prefix': True,
        'fanout_patterns': True,
    }
)
```

## Security Considerations

### 1. Task Authentication
```python
@celery.task(bind=True)
def authenticated_task(self, user_id, *args, **kwargs):
    # Verify user permissions
    if not has_permission(user_id, 'execute_task'):
        raise PermissionError("User not authorized")
    
    # Execute task
    return process_task(*args, **kwargs)
```

### 2. Input Validation
```python
from marshmallow import Schema, fields, ValidationError

class ArticleProcessingSchema(Schema):
    urls = fields.List(fields.Url(), required=True, validate=lambda x: len(x) <= 100)

@celery.task(bind=True)
def process_articles_validated(self, data):
    try:
        validated_data = ArticleProcessingSchema().load(data)
        return process_new_articles(validated_data['urls'])
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e.messages}")
```

### 3. Rate Limiting
```python
celery.conf.update(
    task_annotations={
        'backend.celery_app.process_new_articles': {'rate_limit': '10/m'},
        'backend.celery_app.classify_article_batch': {'rate_limit': '5/m'},
    }
)
```

## Troubleshooting

### Common Issues

#### 1. Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Check Redis configuration
redis-cli config get maxmemory
redis-cli config get maxmemory-policy
```

#### 2. Worker Not Starting
```bash
# Check logs
tail -f /var/log/mingus/celery-worker.log

# Check environment
python -c "import redis; r=redis.Redis(); print(r.ping())"

# Check dependencies
python -c "import celery; print(celery.__version__)"
```

#### 3. Tasks Not Executing
```bash
# Check queue status
python manage_celery.py queues

# Check worker status
python manage_celery.py status

# Purge queues if needed
python manage_celery.py purge
```

#### 4. Memory Issues
```python
# Monitor memory usage
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
```

## Conclusion

The Celery configuration for the MINGUS Article Library provides:

✅ **Comprehensive Task Processing**: All article library operations handled asynchronously
✅ **Queue-Based Architecture**: Separate queues for different types of tasks
✅ **Robust Error Handling**: Retry logic, circuit breakers, and dead letter queues
✅ **Production Ready**: Supervisor, systemd, and Docker integration
✅ **Monitoring and Observability**: Flower dashboard and comprehensive logging
✅ **Performance Optimized**: Queue-specific workers and Redis optimization
✅ **Security Focused**: Authentication, validation, and rate limiting
✅ **Easy Management**: Comprehensive management script with CLI interface
✅ **Scalable Architecture**: Horizontal scaling with multiple workers
✅ **Maintenance Automation**: Periodic cleanup and analytics tasks

The Celery infrastructure is ready for production deployment and can handle the high-volume background processing requirements of the article library feature.
