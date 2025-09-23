# Daily Outlook Tasks Deployment Guide

## Prerequisites

Before deploying the Daily Outlook Tasks system, ensure you have:

1. **Redis Server** running and accessible
2. **PostgreSQL/SQLite** database with required models
3. **Python 3.8+** with required dependencies
4. **Celery** installed and configured
5. **Notification services** (FCM/APNS/SMTP) configured

## Environment Setup

### 1. Environment Variables

Create or update your `.env` file with the following variables:

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/mingus_db
# OR for SQLite
# DATABASE_URL=sqlite:///mingus.db

# Notification Configuration
NOTIFICATION_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Push Notification Configuration
FCM_SERVER_KEY=your_fcm_server_key
APNS_CERTIFICATE_PATH=/path/to/apns_cert.pem

# Task Configuration
DAILY_OUTLOOK_QUEUE=daily_outlook_queue
DEFAULT_WEEKDAY_TIME=06:45
DEFAULT_WEEKEND_TIME=08:30
```

### 2. Dependencies

Install required Python packages:

```bash
pip install celery redis psycopg2-binary pytz
```

## Database Setup

### 1. Verify Models

Ensure the following models exist in your database:

```python
# DailyOutlook model
class DailyOutlook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    balance_score = db.Column(db.Integer, nullable=False)
    # ... other fields

# User model with notification preferences
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    timezone = db.Column(db.String(50), default='UTC')
    weekday_notification_time = db.Column(db.String(5), default='06:45')
    weekend_notification_time = db.Column(db.String(5), default='08:30')
    # ... other fields
```

### 2. Database Migration

If using Alembic, create a migration:

```bash
alembic revision --autogenerate -m "Add daily outlook tasks support"
alembic upgrade head
```

## Celery Configuration

### 1. Update Celery Beat Schedule

The daily outlook tasks are already configured in `backend/config/celery_beat_schedule.py`. Ensure this file is imported in your main Celery configuration.

### 2. Start Celery Workers

#### Development Environment

```bash
# Terminal 1: Start Celery Worker
celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue

# Terminal 2: Start Celery Beat Scheduler
celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info
```

#### Production Environment

```bash
# Start multiple workers for high availability
celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue --concurrency=4

# Start beat scheduler (single instance only)
celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info --pidfile=/var/run/celery/beat.pid
```

### 3. Process Management

For production, use a process manager like Supervisor:

```ini
# /etc/supervisor/conf.d/celery-daily-outlook.conf
[program:celery-daily-outlook-worker]
command=celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue --concurrency=4
directory=/path/to/your/app
user=celery
numprocs=1
stdout_logfile=/var/log/celery/daily-outlook-worker.log
stderr_logfile=/var/log/celery/daily-outlook-worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998

[program:celery-daily-outlook-beat]
command=celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info
directory=/path/to/your/app
user=celery
numprocs=1
stdout_logfile=/var/log/celery/daily-outlook-beat.log
stderr_logfile=/var/log/celery/daily-outlook-beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=999
```

## Testing

### 1. Run Test Suite

```bash
cd backend/tasks
python test_daily_outlook_tasks.py
```

### 2. Manual Task Testing

```python
# Test outlook generation
from backend.tasks.daily_outlook_tasks import generate_daily_outlooks_batch
result = generate_daily_outlooks_batch.delay()
print(f"Task ID: {result.id}")

# Check task status
print(f"Status: {result.status}")
print(f"Result: {result.result}")
```

### 3. Health Check

```python
# Test system health
from backend.tasks.daily_outlook_tasks import health_check_daily_outlook_tasks
result = health_check_daily_outlook_tasks.delay()
health_status = result.get()
print(f"System Status: {health_status['service_status']}")
```

## Monitoring

### 1. Celery Monitoring

```bash
# Monitor active tasks
celery -A backend.tasks.daily_outlook_tasks inspect active

# Monitor scheduled tasks
celery -A backend.tasks.daily_outlook_tasks inspect scheduled

# Get worker statistics
celery -A backend.tasks.daily_outlook_tasks inspect stats
```

### 2. Log Monitoring

Monitor logs for errors and performance:

```bash
# Monitor worker logs
tail -f /var/log/celery/daily-outlook-worker.log

# Monitor beat logs
tail -f /var/log/celery/daily-outlook-beat.log
```

### 3. Database Monitoring

Monitor database performance and task results:

```sql
-- Check recent outlook generations
SELECT date, COUNT(*) as generated_count 
FROM daily_outlooks 
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY date;

-- Check user engagement
SELECT 
    AVG(user_rating) as avg_rating,
    COUNT(CASE WHEN viewed_at IS NOT NULL THEN 1 END) as viewed_count,
    COUNT(*) as total_count
FROM daily_outlooks 
WHERE date >= CURRENT_DATE - INTERVAL '7 days';
```

## Production Deployment

### 1. Docker Deployment

Create a `docker-compose.yml` for production:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery-worker:
    build: .
    command: celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/2
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - redis
      - postgres
    volumes:
      - ./logs:/var/log/celery

  celery-beat:
    build: .
    command: celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/2
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - redis
      - postgres
    volumes:
      - ./logs:/var/log/celery

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mingus_db
      POSTGRES_USER: mingus_user
      POSTGRES_PASSWORD: mingus_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### 2. Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# celery-daily-outlook-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-daily-outlook-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: celery-daily-outlook-worker
  template:
    metadata:
      labels:
        app: celery-daily-outlook-worker
    spec:
      containers:
      - name: celery-worker
        image: mingus-app:latest
        command: ["celery", "-A", "backend.tasks.daily_outlook_tasks", "worker", "--loglevel=info", "--queues=daily_outlook_queue"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis-service:6379/2"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis-service:6379/2"
```

## Troubleshooting

### Common Issues

1. **Tasks Not Running**:
   - Check Celery worker status
   - Verify queue configuration
   - Check Redis connectivity

2. **Database Errors**:
   - Verify database connection
   - Check model definitions
   - Review migration status

3. **Notification Failures**:
   - Check notification service configuration
   - Verify API keys and certificates
   - Review user preferences

### Debug Commands

```bash
# Check Celery status
celery -A backend.tasks.daily_outlook_tasks inspect ping

# Purge failed tasks
celery -A backend.tasks.daily_outlook_tasks purge

# Reset task state
celery -A backend.tasks.daily_outlook_tasks control cancel_consumer daily_outlook_queue
celery -A backend.tasks.daily_outlook_tasks control add_consumer daily_outlook_queue
```

## Performance Optimization

### 1. Worker Scaling

Scale workers based on load:

```bash
# Scale workers
celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue --concurrency=8
```

### 2. Database Optimization

Add indexes for better performance:

```sql
-- Add indexes for daily outlook queries
CREATE INDEX idx_daily_outlooks_user_date ON daily_outlooks(user_id, date);
CREATE INDEX idx_daily_outlooks_created_at ON daily_outlooks(created_at);
CREATE INDEX idx_users_last_activity ON users(last_activity);
```

### 3. Redis Optimization

Configure Redis for optimal performance:

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Security Considerations

### 1. Environment Variables

- Store sensitive configuration in environment variables
- Use secrets management for production
- Rotate API keys regularly

### 2. Network Security

- Use TLS for Redis connections
- Restrict database access
- Implement firewall rules

### 3. Data Privacy

- Encrypt sensitive user data
- Implement data retention policies
- Follow GDPR compliance

## Backup and Recovery

### 1. Database Backups

```bash
# Daily database backup
pg_dump mingus_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql mingus_db < backup_20240115.sql
```

### 2. Task State Recovery

```bash
# Backup Redis data
redis-cli --rdb /backup/redis_$(date +%Y%m%d).rdb

# Restore Redis data
redis-cli --pipe < /backup/redis_20240115.rdb
```

## Maintenance

### 1. Regular Maintenance Tasks

- Monitor task performance
- Clean up old task results
- Update dependencies
- Review error logs

### 2. Scaling Considerations

- Monitor queue lengths
- Scale workers based on demand
- Implement auto-scaling policies
- Plan for peak usage periods

This deployment guide provides comprehensive instructions for deploying and maintaining the Daily Outlook Tasks system in both development and production environments.
