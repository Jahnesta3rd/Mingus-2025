# Celery Configuration Guide for MINGUS Communication System

## Overview

This guide covers the comprehensive Celery configuration system for the MINGUS Communication System, including Flask integration, task routing, worker management, monitoring, and best practices.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Configuration Setup](#configuration-setup)
3. [Flask Integration](#flask-integration)
4. [Task Routing and Queues](#task-routing-and-queues)
5. [Worker Management](#worker-management)
6. [Monitoring and Health Checks](#monitoring-and-health-checks)
7. [Deployment and Operations](#deployment-and-operations)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    MINGUS Communication System              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Flask App     │    │   Celery Beat   │                │
│  │                 │    │   (Scheduler)   │                │
│  │ ┌─────────────┐ │    │                 │                │
│  │ │API Endpoints│ │    │ ┌─────────────┐ │                │
│  │ │Web Routes   │ │    │ │Periodic     │ │                │
│  │ │Services     │ │    │ │Tasks        │ │                │
│  │ └─────────────┘ │    │ └─────────────┘ │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           └───────────────────────┼────────────────────────┘
│                                   │
│  ┌─────────────────────────────────┼────────────────────────┐
│  │         Celery Workers          │                        │
│  │                                 │                        │
│  │  ┌─────────────┐ ┌─────────────┐│ ┌─────────────┐        │
│  │  │ SMS Worker  │ │Email Worker ││ │Analytics    │        │
│  │  │             │ │             ││ │Worker       │        │
│  │  │ ┌─────────┐ │ │ ┌─────────┐ ││ │ ┌─────────┐ │        │
│  │  │ │sms_crit │ │ │ │email_rep│ ││ │ │analytics│ │        │
│  │  │ │sms_daily│ │ │ │email_edu│ ││ │ │optimize │ │        │
│  │  │ └─────────┘ │ │ └─────────┘ ││ │ └─────────┘ │        │
│  │  └─────────────┘ └─────────────┘│ └─────────────┘        │
│  └─────────────────────────────────┼────────────────────────┘
│                                   │
│  ┌─────────────────────────────────┼────────────────────────┐
│  │         Message Broker          │                        │
│  │         (Redis/RabbitMQ)        │                        │
│  └─────────────────────────────────┴────────────────────────┘
```

### Queue Structure

| Queue | Priority | Purpose | Worker Type |
|-------|----------|---------|-------------|
| `sms_critical` | 1 | Critical financial alerts | SMS Worker |
| `sms_daily` | 3 | Daily communications | SMS Worker |
| `email_reports` | 5 | Monthly reports | Email Worker |
| `email_education` | 7 | Educational content | Email Worker |
| `analytics` | 8 | Analytics processing | Analytics Worker |
| `optimization` | 9 | System optimization | Analytics Worker |
| `monitoring` | 10 | Health checks | Default Worker |

---

## Configuration Setup

### 1. Environment Variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_SECURITY_KEY=your_security_key_here

# Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_WORKER_DISABLE_RATE_LIMITS=false
CELERY_WORKER_LOG_LEVEL=INFO

# SMS Worker Configuration
SMS_WORKER_CONCURRENCY=2
SMS_WORKER_MAX_TASKS_PER_CHILD=500

# Email Worker Configuration
EMAIL_WORKER_CONCURRENCY=3
EMAIL_WORKER_MAX_TASKS_PER_CHILD=750

# Analytics Worker Configuration
ANALYTICS_WORKER_CONCURRENCY=2
ANALYTICS_WORKER_MAX_TASKS_PER_CHILD=250

# Optimization Worker Configuration
OPTIMIZATION_WORKER_CONCURRENCY=1
OPTIMIZATION_WORKER_MAX_TASKS_PER_CHILD=100

# Database Configuration
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30

# Celery Database Configuration
CELERY_DB_POOL_SIZE=10
CELERY_DB_MAX_OVERFLOW=20
CELERY_DB_POOL_RECYCLE=1800
CELERY_DB_POOL_TIMEOUT=30

# Analytics Database Configuration
ANALYTICS_DB_POOL_SIZE=5
ANALYTICS_DB_MAX_OVERFLOW=10
ANALYTICS_DB_POOL_RECYCLE=7200
ANALYTICS_DB_POOL_TIMEOUT=60
```

### 2. Celery Configuration File

```python
# backend/celery_config.py
from backend.celery_config import create_celery_app, init_celery_app

# Create Celery app
celery_app = create_celery_app()

# Initialize with Flask app (in app factory)
def init_celery(flask_app):
    return init_celery_app(flask_app)
```

### 3. Flask Integration

```python
# backend/app_factory.py
from backend.celery_config import init_celery_app
from backend.integration.flask_celery_integration import init_flask_celery_integration

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Initialize Celery
    celery_app = init_celery_app(app)
    
    # Initialize Flask-Celery integration
    init_flask_celery_integration(app, celery_app)
    
    return app
```

---

## Flask Integration

### 1. Flask Task Base Class

```python
from backend.integration.flask_celery_integration import FlaskTask

class SendCommunicationTask(FlaskTask):
    """Base task class with Flask app context"""
    
    def __call__(self, *args, **kwargs):
        # Flask app context is automatically provided
        with self.flask_app.app_context():
            return super().__call__(*args, **kwargs)
    
    def run(self, user_id: int, message: str):
        # Access Flask services
        from backend.services.communication_orchestrator import CommunicationOrchestrator
        
        orchestrator = CommunicationOrchestrator()
        result = orchestrator.send_smart_communication(
            user_id=user_id,
            trigger_type='financial_alert',
            data={'message': message}
        )
        
        return result
```

### 2. Database Session Management

```python
from backend.integration.flask_celery_integration import with_flask_and_database

@with_flask_and_database
def send_sms_with_database(session, user_id: int, message: str):
    """Task with automatic database session management"""
    
    # Database operations
    communication = CommunicationMetrics(
        user_id=user_id,
        message_type='sms',
        channel='sms',
        status='sent'
    )
    session.add(communication)
    
    # Session is automatically committed
    return True
```

### 3. Service Access

```python
from backend.integration.flask_celery_integration import get_flask_service

def send_communication_task(user_id: int, message: str):
    """Task with Flask service access"""
    
    # Get Flask service
    orchestrator = get_flask_service('communication_orchestrator')
    
    if orchestrator:
        result = orchestrator.send_smart_communication(
            user_id=user_id,
            trigger_type='financial_alert',
            data={'message': message}
        )
        return result
    else:
        raise Exception("Communication orchestrator service not available")
```

### 4. Context Managers

```python
from backend.integration.flask_celery_integration import (
    flask_app_context,
    celery_database_session,
    flask_and_database_context
)

def complex_task(user_id: int, data: dict):
    """Task using context managers"""
    
    with flask_and_database_context() as (flask_app, session):
        # Flask app context and database session available
        user = session.query(User).filter_by(id=user_id).first()
        
        if user:
            # Process with Flask services
            orchestrator = get_flask_service('communication_orchestrator')
            result = orchestrator.send_smart_communication(
                user_id=user_id,
                trigger_type='financial_alert',
                data=data
            )
            
            # Log to database
            log = CommunicationLog(
                user_id=user_id,
                action='communication_sent',
                result=result
            )
            session.add(log)
            
            return result
```

---

## Task Routing and Queues

### 1. Task Routing Configuration

```python
# Task routing based on task type
task_routes = {
    # SMS Tasks
    'backend.tasks.mingus_celery_tasks.send_critical_financial_alert': {
        'queue': 'sms_critical',
        'routing_key': 'sms.critical'
    },
    'backend.tasks.mingus_celery_tasks.send_payment_reminder': {
        'queue': 'sms_daily',
        'routing_key': 'sms.daily'
    },
    
    # Email Tasks
    'backend.tasks.mingus_celery_tasks.send_monthly_report': {
        'queue': 'email_reports',
        'routing_key': 'email.reports'
    },
    'backend.tasks.mingus_celery_tasks.send_educational_content': {
        'queue': 'email_education',
        'routing_key': 'email.education'
    },
    
    # Analytics Tasks
    'backend.tasks.mingus_celery_tasks.analyze_user_engagement': {
        'queue': 'analytics',
        'routing_key': 'analytics.analysis'
    }
}
```

### 2. Queue Configuration

```python
# Queue definitions with priorities
task_queues = {
    'sms_critical': {
        'exchange': 'mingus_exchange',
        'routing_key': 'sms.critical',
        'queue_arguments': {'x-max-priority': 10}
    },
    'sms_daily': {
        'exchange': 'mingus_exchange',
        'routing_key': 'sms.daily',
        'queue_arguments': {'x-max-priority': 10}
    },
    'email_reports': {
        'exchange': 'mingus_exchange',
        'routing_key': 'email.reports',
        'queue_arguments': {'x-max-priority': 10}
    },
    'email_education': {
        'exchange': 'mingus_exchange',
        'routing_key': 'email.education',
        'queue_arguments': {'x-max-priority': 10}
    },
    'analytics': {
        'exchange': 'mingus_exchange',
        'routing_key': 'analytics.*',
        'queue_arguments': {'x-max-priority': 10}
    }
}
```

### 3. Task Annotations

```python
# Rate limiting and retry configuration
task_annotations = {
    'backend.tasks.mingus_celery_tasks.send_critical_financial_alert': {
        'rate_limit': '500/m',  # 500 per minute
        'max_retries': 3,
        'default_retry_delay': 60,
        'priority': 1
    },
    'backend.tasks.mingus_celery_tasks.send_payment_reminder': {
        'rate_limit': '100/m',  # 100 per minute
        'max_retries': 3,
        'default_retry_delay': 300,
        'priority': 3
    },
    'backend.tasks.mingus_celery_tasks.send_monthly_report': {
        'rate_limit': '1000/m', # 1000 per minute
        'max_retries': 2,
        'default_retry_delay': 1800,
        'priority': 5
    }
}
```

### 4. Periodic Tasks (Beat Schedule)

```python
# Periodic task scheduling
beat_schedule = {
    # Queue Monitoring (every 5 minutes)
    'monitor-queue-depth': {
        'task': 'backend.tasks.mingus_celery_tasks.monitor_queue_depth',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'analytics'}
    },
    
    # Delivery Rate Tracking (every 10 minutes)
    'track-delivery-rates': {
        'task': 'backend.tasks.mingus_celery_tasks.track_delivery_rates',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'analytics'}
    },
    
    # Weekly Check-ins (every Monday at 9 AM)
    'weekly-checkins': {
        'task': 'backend.tasks.mingus_celery_tasks.send_weekly_checkin',
        'schedule': crontab(minute=0, hour=9, day_of_week=1),
        'options': {'queue': 'sms_daily'}
    },
    
    # Monthly Reports (1st of month at 8 AM)
    'monthly-reports': {
        'task': 'backend.tasks.mingus_celery_tasks.send_monthly_report',
        'schedule': crontab(minute=0, hour=8, day_of_month=1),
        'options': {'queue': 'email_reports'}
    }
}
```

---

## Worker Management

### 1. Worker Types and Configuration

#### SMS Worker
```bash
# SMS Worker Configuration
celery -A backend.celery_config.celery_app worker \
    --loglevel=INFO \
    --concurrency=2 \
    --queues=sms_critical,sms_daily \
    --hostname=sms-worker@%h \
    --max-tasks-per-child=500 \
    --prefetch-multiplier=1
```

#### Email Worker
```bash
# Email Worker Configuration
celery -A backend.celery_config.celery_app worker \
    --loglevel=INFO \
    --concurrency=3 \
    --queues=email_reports,email_education \
    --hostname=email-worker@%h \
    --max-tasks-per-child=750 \
    --prefetch-multiplier=2
```

#### Analytics Worker
```bash
# Analytics Worker Configuration
celery -A backend.celery_config.celery_app worker \
    --loglevel=INFO \
    --concurrency=2 \
    --queues=analytics \
    --hostname=analytics-worker@%h \
    --max-tasks-per-child=250 \
    --prefetch-multiplier=1
```

#### Optimization Worker
```bash
# Optimization Worker Configuration
celery -A backend.celery_config.celery_app worker \
    --loglevel=INFO \
    --concurrency=1 \
    --queues=optimization \
    --hostname=optimization-worker@%h \
    --max-tasks-per-child=100 \
    --prefetch-multiplier=1
```

### 2. Worker Startup Scripts

```python
from backend.celery_worker_config import create_worker_startup_script

# Create SMS worker startup script
sms_script = create_worker_startup_script('sms', 'start_sms_worker.sh')

# Create Email worker startup script
email_script = create_worker_startup_script('email', 'start_email_worker.sh')

# Create Analytics worker startup script
analytics_script = create_worker_startup_script('analytics', 'start_analytics_worker.sh')
```

### 3. Celery Beat Scheduler

```bash
# Start Celery Beat
celery -A backend.celery_config.celery_app beat \
    --loglevel=INFO \
    --scheduler=celery.beat.PersistentScheduler \
    --schedule=/tmp/celerybeat-schedule \
    --pidfile=/tmp/celerybeat.pid
```

### 4. Worker Control Commands

```python
from backend.celery_worker_config import get_worker_manager

# Get worker manager
manager = get_worker_manager()

# Restart worker
manager.restart_worker('sms-worker@hostname')

# Shutdown worker
manager.shutdown_worker('email-worker@hostname')

# Get worker health status
health_status = manager.get_health_status()

# Get worker metrics
metrics = manager.get_worker_metrics()
```

---

## Monitoring and Health Checks

### 1. Health Check Endpoints

```python
from flask import Blueprint, jsonify
from backend.celery_worker_config import get_worker_health_status
from backend.celery_config import validate_celery_config

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/celery')
def celery_health():
    """Celery health check endpoint"""
    
    # Get worker health status
    worker_health = get_worker_health_status()
    
    # Validate Celery configuration
    config_validation = validate_celery_config()
    
    # Determine overall health
    all_healthy = (
        worker_health['status'] == 'healthy' and
        config_validation['broker_connection'] and
        config_validation['result_backend_connection']
    )
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'worker_health': worker_health,
        'config_validation': config_validation,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if all_healthy else 503
```

### 2. Metrics Collection

```python
@health_bp.route('/metrics/celery')
def celery_metrics():
    """Celery metrics endpoint"""
    
    from backend.celery_worker_config import get_worker_metrics, get_performance_stats
    
    worker_metrics = get_worker_metrics()
    performance_stats = get_performance_stats()
    
    return jsonify({
        'worker_metrics': worker_metrics,
        'performance_stats': performance_stats,
        'timestamp': datetime.utcnow().isoformat()
    })
```

### 3. Monitoring Dashboard

```python
@health_bp.route('/dashboard/celery')
def celery_dashboard():
    """Celery monitoring dashboard"""
    
    from backend.celery_worker_config import get_worker_health_status, get_worker_metrics
    from backend.celery_config import get_celery_config
    
    health_status = get_worker_health_status()
    metrics = get_worker_metrics()
    config = get_celery_config()
    
    # Calculate key performance indicators
    total_workers = len(health_status.get('workers', {}))
    active_workers = sum(1 for w in health_status.get('workers', {}).values() 
                        if w.get('status') == 'active')
    
    total_tasks = sum(m.completed_tasks for m in metrics.values())
    failed_tasks = sum(m.failed_tasks for m in metrics.values())
    error_rate = failed_tasks / max(total_tasks, 1)
    
    return jsonify({
        'health_status': health_status,
        'kpis': {
            'total_workers': total_workers,
            'active_workers': active_workers,
            'worker_utilization': active_workers / max(total_workers, 1),
            'total_tasks_processed': total_tasks,
            'failed_tasks': failed_tasks,
            'error_rate': error_rate,
            'average_task_time': sum(m.avg_task_time for m in metrics.values()) / max(len(metrics), 1)
        },
        'queues': health_status.get('queues', {}),
        'broker': health_status.get('broker', {}),
        'config_summary': {
            'broker_url': config.get('broker_url', 'unknown'),
            'result_backend': config.get('result_backend', 'unknown'),
            'task_queues': list(config.get('task_queues', {}).keys()),
            'worker_concurrency': config.get('worker_concurrency', 0)
        }
    })
```

### 4. Real-time Monitoring

```python
from backend.celery_worker_config import start_worker_monitoring, stop_worker_monitoring

# Start monitoring
start_worker_monitoring()

# Stop monitoring
stop_worker_monitoring()
```

---

## Deployment and Operations

### 1. Production Deployment

#### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  flask_app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  sms_worker:
    build: .
    command: celery -A backend.celery_config.celery_app worker --loglevel=INFO --concurrency=2 --queues=sms_critical,sms_daily --hostname=sms-worker@%h
    environment:
      - FLASK_ENV=production
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  email_worker:
    build: .
    command: celery -A backend.celery_config.celery_app worker --loglevel=INFO --concurrency=3 --queues=email_reports,email_education --hostname=email-worker@%h
    environment:
      - FLASK_ENV=production
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  analytics_worker:
    build: .
    command: celery -A backend.celery_config.celery_app worker --loglevel=INFO --concurrency=2 --queues=analytics --hostname=analytics-worker@%h
    environment:
      - FLASK_ENV=production
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  celery_beat:
    build: .
    command: celery -A backend.celery_config.celery_app beat --loglevel=INFO --scheduler=celery.beat.PersistentScheduler
    environment:
      - FLASK_ENV=production
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

#### Systemd Service Files
```ini
# /etc/systemd/system/mingus-sms-worker.service
[Unit]
Description=MINGUS SMS Worker
After=network.target

[Service]
Type=simple
User=mingus
Group=mingus
WorkingDirectory=/opt/mingus
Environment=FLASK_ENV=production
Environment=CELERY_BROKER_URL=redis://localhost:6379/0
Environment=CELERY_RESULT_BACKEND=redis://localhost:6379/0
ExecStart=/opt/mingus/venv/bin/celery -A backend.celery_config.celery_app worker --loglevel=INFO --concurrency=2 --queues=sms_critical,sms_daily --hostname=sms-worker@%%h
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Monitoring and Alerting

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Celery metrics
celery_tasks_total = Counter('celery_tasks_total', 'Total tasks processed', ['queue', 'status'])
celery_task_duration = Histogram('celery_task_duration_seconds', 'Task duration in seconds', ['queue'])
celery_workers_active = Gauge('celery_workers_active', 'Number of active workers')
celery_queue_depth = Gauge('celery_queue_depth', 'Queue depth', ['queue'])

# Task monitoring
def monitor_task(task_name, queue_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                celery_tasks_total.labels(queue=queue_name, status='success').inc()
                return result
            except Exception as e:
                celery_tasks_total.labels(queue=queue_name, status='failed').inc()
                raise
            finally:
                duration = time.time() - start_time
                celery_task_duration.labels(queue=queue_name).observe(duration)
        return wrapper
    return decorator
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "MINGUS Celery Monitoring",
    "panels": [
      {
        "title": "Task Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(celery_tasks_total[5m])",
            "legendFormat": "{{queue}} - {{status}}"
          }
        ]
      },
      {
        "title": "Queue Depth",
        "type": "graph",
        "targets": [
          {
            "expr": "celery_queue_depth",
            "legendFormat": "{{queue}}"
          }
        ]
      },
      {
        "title": "Active Workers",
        "type": "stat",
        "targets": [
          {
            "expr": "celery_workers_active"
          }
        ]
      }
    ]
  }
}
```

### 3. Logging Configuration

```python
# logging_config.py
import logging
from celery.utils.log import get_task_logger

# Celery task logging
task_logger = get_task_logger(__name__)

# Configure task logging
task_logger.setLevel(logging.INFO)

# Add file handler for tasks
task_handler = logging.FileHandler('/var/log/mingus/celery_tasks.log')
task_handler.setFormatter(logging.Formatter(
    '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
))
task_logger.addHandler(task_handler)

# Add error tracking
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[CeleryIntegration()],
    traces_sample_rate=0.1,
)
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Worker Connection Issues

**Symptoms:**
- Workers not connecting to broker
- Tasks not being processed
- Connection timeout errors

**Solutions:**
```bash
# Check broker connectivity
redis-cli ping

# Check Celery configuration
celery -A backend.celery_config.celery_app inspect ping

# Restart workers
celery -A backend.celery_config.celery_app control pool_restart

# Check worker logs
tail -f /var/log/mingus/celery_worker.log
```

#### 2. Task Queue Backlog

**Symptoms:**
- Tasks not being processed
- High queue depth
- Slow response times

**Solutions:**
```python
# Scale up workers
from backend.celery_worker_config import get_worker_manager

manager = get_worker_manager()
health_status = manager.get_health_status()

# Check queue depths
for queue_name, stats in health_status['queues'].items():
    if stats['total_tasks'] > 100:
        print(f"Queue {queue_name} has high backlog: {stats['total_tasks']} tasks")

# Increase worker concurrency
# Update environment variable: CELERY_WORKER_CONCURRENCY=8
```

#### 3. Memory Leaks

**Symptoms:**
- Increasing memory usage
- Workers crashing
- High memory consumption

**Solutions:**
```python
# Monitor memory usage
import psutil
import os

def check_memory_usage():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.2f} MB")
    
    if memory_mb > 1000:  # 1GB threshold
        print("High memory usage detected")

# Reduce max tasks per child
# Update environment variable: CELERY_WORKER_MAX_TASKS_PER_CHILD=500
```

#### 4. Database Connection Issues

**Symptoms:**
- Database connection errors
- Task failures
- Connection pool exhaustion

**Solutions:**
```python
# Check database connectivity
from backend.database.celery_session import get_celery_db_session

db_session = get_celery_db_session()
health_check = db_session.health_check()
print(f"Database health: {health_check}")

# Optimize connection pooling
# Update environment variables:
# CELERY_DB_POOL_SIZE=10
# CELERY_DB_MAX_OVERFLOW=20
# CELERY_DB_POOL_RECYCLE=1800
```

#### 5. Task Timeout Issues

**Symptoms:**
- Tasks timing out
- Soft time limit exceeded
- Long-running tasks

**Solutions:**
```python
# Increase task time limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Optimize task execution
@celery_app.task(bind=True, time_limit=1800, soft_time_limit=1500)
def long_running_task(self, *args, **kwargs):
    # Check for soft time limit
    if self.request.called_directly:
        return
    
    # Process in chunks
    for chunk in data_chunks:
        if self.request.called_directly:
            break
        process_chunk(chunk)
```

### Debugging Tools

#### 1. Celery Inspection
```python
from celery import current_app

# Inspect active workers
inspect = current_app.control.inspect()
active_workers = inspect.active()
reserved_tasks = inspect.reserved()
stats = inspect.stats()

print(f"Active workers: {active_workers}")
print(f"Reserved tasks: {reserved_tasks}")
print(f"Worker stats: {stats}")
```

#### 2. Queue Monitoring
```python
# Monitor queue depths
from backend.celery_worker_config import get_worker_manager

manager = get_worker_manager()
queue_stats = manager._get_queue_stats()

for queue_name, stats in queue_stats.items():
    total = stats.get('active', 0) + stats.get('reserved', 0) + stats.get('scheduled', 0)
    print(f"Queue {queue_name}: {total} tasks")
```

#### 3. Task Tracing
```python
# Enable task tracing
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_IGNORE_RESULT = False

# Monitor task execution
@celery_app.task(bind=True)
def traced_task(self, *args, **kwargs):
    print(f"Task {self.request.id} started at {self.request.timestamp}")
    
    try:
        result = process_task(*args, **kwargs)
        print(f"Task {self.request.id} completed successfully")
        return result
    except Exception as e:
        print(f"Task {self.request.id} failed: {e}")
        raise
```

---

## Best Practices

### 1. Task Design

```python
# ✅ Good: Idempotent tasks
@celery_app.task(bind=True, max_retries=3)
def send_communication(self, user_id: int, message: str):
    try:
        # Check if already sent
        if communication_already_sent(user_id, message):
            return "already_sent"
        
        # Send communication
        result = send_message(user_id, message)
        
        # Log success
        log_communication(user_id, message, result)
        return result
        
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries), max_retries=3)

# ❌ Bad: Non-idempotent tasks
@celery_app.task
def send_communication_bad(user_id: int, message: str):
    # No duplicate checking
    send_message(user_id, message)
    # Could send multiple times if retried
```

### 2. Error Handling

```python
# ✅ Good: Proper error handling
@celery_app.task(bind=True)
def robust_task(self, *args, **kwargs):
    try:
        result = process_data(*args, **kwargs)
        return result
        
    except ValueError as e:
        # Don't retry validation errors
        logger.error(f"Validation error: {e}")
        raise
        
    except ConnectionError as e:
        # Retry connection errors
        logger.warning(f"Connection error, retrying: {e}")
        raise self.retry(countdown=60, max_retries=3)
        
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error: {e}")
        raise

# ❌ Bad: Generic error handling
@celery_app.task
def fragile_task(*args, **kwargs):
    try:
        return process_data(*args, **kwargs)
    except Exception as e:
        print(f"Error: {e}")  # No logging, no retry logic
        return None
```

### 3. Resource Management

```python
# ✅ Good: Proper resource cleanup
@celery_app.task(bind=True)
def resource_intensive_task(self, *args, **kwargs):
    # Use context managers for resources
    with database_session() as session:
        with file_handler() as file:
            result = process_with_resources(session, file, *args, **kwargs)
            return result

# ❌ Bad: Resource leaks
@celery_app.task
def leaky_task(*args, **kwargs):
    session = get_database_session()
    file = open_file()
    
    result = process_with_resources(session, file, *args, **kwargs)
    
    # Resources not properly closed
    return result
```

### 4. Monitoring and Observability

```python
# ✅ Good: Comprehensive monitoring
@celery_app.task(bind=True)
def monitored_task(self, *args, **kwargs):
    start_time = time.time()
    
    try:
        # Log task start
        logger.info(f"Task {self.request.id} started", extra={
            'task_id': self.request.id,
            'args': args,
            'kwargs': kwargs
        })
        
        result = process_task(*args, **kwargs)
        
        # Log success
        duration = time.time() - start_time
        logger.info(f"Task {self.request.id} completed", extra={
            'task_id': self.request.id,
            'duration': duration,
            'result': result
        })
        
        return result
        
    except Exception as e:
        # Log failure
        duration = time.time() - start_time
        logger.error(f"Task {self.request.id} failed", extra={
            'task_id': self.request.id,
            'duration': duration,
            'error': str(e)
        })
        raise

# ❌ Bad: No monitoring
@celery_app.task
def unmonitored_task(*args, **kwargs):
    return process_task(*args, **kwargs)  # No logging, no metrics
```

---

## Summary

The Celery configuration system provides:

1. **Comprehensive Configuration**: Complete Celery setup with Flask integration
2. **Task Routing**: Intelligent task routing based on priority and type
3. **Worker Management**: Specialized workers for different task types
4. **Monitoring**: Real-time health checks and performance monitoring
5. **Flask Integration**: Seamless Flask app context in Celery tasks
6. **Database Integration**: Proper database session management
7. **Deployment Ready**: Production-ready configuration and deployment scripts
8. **Troubleshooting**: Comprehensive debugging and monitoring tools

This system ensures reliable, scalable, and maintainable background task processing for the MINGUS Communication System. 