# SQLAlchemy Session Management Guide

## Overview

This guide covers the comprehensive SQLAlchemy session management system for the MINGUS Communication System, including proper session handling in Celery tasks, database connection pooling, transaction management, and error handling.

## Table of Contents

1. [Session Management Architecture](#session-management-architecture)
2. [Celery Task Session Management](#celery-task-session-management)
3. [Connection Pooling](#connection-pooling)
4. [Transaction Management](#transaction-management)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Troubleshooting](#troubleshooting)

---

## Session Management Architecture

### Core Components

#### 1. DatabaseSessionManager (`backend/database/session_manager.py`)
- **Purpose**: Main session manager for Flask application
- **Features**: Connection pooling, transaction management, error handling
- **Usage**: Web requests, API endpoints, background tasks

#### 2. CeleryDatabaseSession (`backend/database/celery_session.py`)
- **Purpose**: Specialized session manager for Celery tasks
- **Features**: Task-specific session lifecycle, retry logic, error handling
- **Usage**: Background task processing, communication delivery

#### 3. ConnectionPoolManager (`backend/database/connection_pool.py`)
- **Purpose**: Connection pool management and monitoring
- **Features**: Multiple pools, health checks, optimization
- **Usage**: Pool monitoring, performance optimization

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MINGUS Communication System              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Flask App     │    │   Celery Tasks  │                │
│  │                 │    │                 │                │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                │
│  │ │DatabaseSess │ │    │ │CelerySess   │ │                │
│  │ │Manager      │ │    │ │Manager      │ │                │
│  │ └─────────────┘ │    │ └─────────────┘ │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           └───────────────────────┼────────────────────────┘
│                                   │
│  ┌─────────────────────────────────┼────────────────────────┐
│  │         ConnectionPoolManager   │                        │
│  │                                 │                        │
│  │  ┌─────────────┐ ┌─────────────┐│ ┌─────────────┐        │
│  │  │   Main Pool │ │ Celery Pool ││ │Analytics    │        │
│  │  │             │ │             ││ │Pool         │        │
│  │  └─────────────┘ └─────────────┘│ └─────────────┘        │
│  └─────────────────────────────────┼────────────────────────┘
│                                   │
│  ┌─────────────────────────────────┼────────────────────────┐
│  │         PostgreSQL Database     │                        │
│  └─────────────────────────────────┴────────────────────────┘
```

---

## Celery Task Session Management

### Basic Usage

#### 1. Using the DatabaseTask Base Class

```python
from backend.database.celery_session import DatabaseTask, with_celery_db_session

class SendSMSTask(DatabaseTask):
    """Send SMS communication task"""
    
    def run(self, user_id: int, message: str):
        with self.db_session.session_scope() as session:
            # Your database operations here
            communication = CommunicationMetrics(
                user_id=user_id,
                message_type='sms',
                channel='sms',
                status='sent'
            )
            session.add(communication)
            # Session will be automatically committed
```

#### 2. Using the Decorator Pattern

```python
from backend.database.celery_session import with_celery_db_session

@with_celery_db_session()
def send_sms_communication(user_id: int, message: str):
    """Send SMS communication with automatic session management"""
    # Session is automatically injected and managed
    communication = CommunicationMetrics(
        user_id=user_id,
        message_type='sms',
        channel='sms',
        status='sent'
    )
    session.add(communication)
    # Session will be automatically committed
```

#### 3. Manual Session Management

```python
from backend.database.celery_session import get_celery_db_session

def send_sms_communication(user_id: int, message: str):
    """Manual session management for complex operations"""
    db_session = get_celery_db_session()
    
    with db_session.session_scope() as session:
        try:
            # Multiple database operations
            communication = CommunicationMetrics(
                user_id=user_id,
                message_type='sms',
                channel='sms',
                status='sent'
            )
            session.add(communication)
            
            # Update user preferences
            user_prefs = session.query(CommunicationPreferences).filter_by(user_id=user_id).first()
            if user_prefs:
                user_prefs.last_sms_sent = datetime.utcnow()
            
            # Session will be committed automatically
            return True
            
        except Exception as e:
            # Session will be rolled back automatically
            logger.error(f"Failed to send SMS: {e}")
            raise
```

### Advanced Usage

#### 1. Communication Transaction Manager

```python
from backend.database.celery_session import CommunicationTransactionManager

def process_communication_batch(communications: list):
    """Process multiple communications in a single transaction"""
    transaction_manager = CommunicationTransactionManager()
    
    with transaction_manager.communication_logging_transaction("batch_processing") as session:
        for comm_data in communications:
            communication = CommunicationMetrics(
                user_id=comm_data['user_id'],
                message_type=comm_data['type'],
                channel=comm_data['channel'],
                status='sent'
            )
            session.add(communication)
        
        # All communications will be committed together
        # If any fails, all will be rolled back
```

#### 2. Retry Logic with Error Handling

```python
from backend.database.celery_session import get_celery_db_session, CeleryDatabaseErrorHandler

def send_communication_with_retry(user_id: int, message: str):
    """Send communication with retry logic"""
    db_session = get_celery_db_session()
    
    def send_operation():
        with db_session.session_scope() as session:
            communication = CommunicationMetrics(
                user_id=user_id,
                message_type='sms',
                channel='sms',
                status='sent'
            )
            session.add(communication)
            return True
    
    # Execute with retry logic
    return db_session.execute_with_retry(send_operation, max_retries=3)
```

---

## Connection Pooling

### Pool Configuration

#### 1. Environment Variables

```bash
# Main application pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30

# Celery worker pool
CELERY_DB_POOL_SIZE=10
CELERY_DB_MAX_OVERFLOW=20
CELERY_DB_POOL_RECYCLE=1800
CELERY_DB_POOL_TIMEOUT=30

# Analytics pool
ANALYTICS_DB_POOL_SIZE=5
ANALYTICS_DB_MAX_OVERFLOW=10
ANALYTICS_DB_POOL_RECYCLE=7200
ANALYTICS_DB_POOL_TIMEOUT=60
```

#### 2. Pool Management

```python
from backend.database.connection_pool import get_pool_manager, PoolHealthChecker

# Initialize pool manager
pool_manager = get_pool_manager()

# Check pool health
health_status = PoolHealthChecker.check_all_pools()
print(health_status)

# Get pool metrics
metrics = PoolHealthChecker.get_pool_metrics('main')
print(metrics)

# Get performance metrics
performance = PoolHealthChecker.get_performance_metrics()
print(performance)
```

#### 3. Pool Monitoring

```python
from backend.database.connection_pool import PoolOptimizer

# Start monitoring
PoolOptimizer.start_monitoring()

# Optimize pools
PoolOptimizer.optimize_all_pools()

# Reset metrics
PoolOptimizer.reset_metrics()

# Stop monitoring
PoolOptimizer.stop_monitoring()
```

### Pool Context Management

```python
from backend.database.connection_pool import pool_context

# Use specific pool
with pool_context('analytics') as pool:
    with pool.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM communication_metrics"))
        count = result.scalar()
        print(f"Total communications: {count}")
```

---

## Transaction Management

### Basic Transaction Patterns

#### 1. Automatic Transaction Management

```python
from backend.database.session_manager import with_db_session

@with_db_session()
def update_user_preferences(user_id: int, preferences: dict):
    """Update user preferences with automatic transaction management"""
    # Session is automatically managed
    user_prefs = session.query(CommunicationPreferences).filter_by(user_id=user_id).first()
    if user_prefs:
        user_prefs.update(preferences)
    # Transaction will be committed automatically
```

#### 2. Manual Transaction Management

```python
from backend.database.session_manager import get_db_session_scope

def complex_communication_operation(user_id: int, data: dict):
    """Complex operation with manual transaction management"""
    with get_db_session_scope() as session:
        try:
            # Multiple operations
            communication = CommunicationMetrics(**data)
            session.add(communication)
            
            # Update analytics
            analytics = UserEngagementMetrics(user_id=user_id)
            session.add(analytics)
            
            # Commit transaction
            session.commit()
            return True
            
        except Exception as e:
            # Rollback on error
            session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
```

#### 3. Nested Transactions

```python
from backend.database.session_manager import session_scope

def nested_transaction_example():
    """Example of nested transaction handling"""
    with session_scope() as outer_session:
        # Outer transaction
        outer_operation(outer_session)
        
        try:
            with session_scope() as inner_session:
                # Inner transaction
                inner_operation(inner_session)
                # Inner transaction commits
        except Exception as e:
            # Inner transaction rolls back, outer continues
            logger.error(f"Inner transaction failed: {e}")
        
        # Outer transaction continues
        outer_operation2(outer_session)
        # Outer transaction commits
```

### Communication-Specific Transactions

#### 1. Communication Logging Transaction

```python
from backend.database.celery_session import CommunicationTransactionManager

def log_communication_event(user_id: int, event_data: dict):
    """Log communication event with specialized transaction"""
    transaction_manager = CommunicationTransactionManager()
    
    with transaction_manager.communication_logging_transaction("event_logging") as session:
        # Log the event
        event = CommunicationMetrics(
            user_id=user_id,
            message_type=event_data['type'],
            channel=event_data['channel'],
            status=event_data['status']
        )
        session.add(event)
        
        # Update user engagement
        engagement = session.query(UserEngagementMetrics).filter_by(user_id=user_id).first()
        if engagement:
            engagement.last_activity = datetime.utcnow()
            engagement.total_communications += 1
```

#### 2. Batch Communication Transaction

```python
def process_communication_batch(communications: list):
    """Process multiple communications in batch"""
    transaction_manager = CommunicationTransactionManager()
    
    def create_communication(session, comm_data):
        communication = CommunicationMetrics(**comm_data)
        session.add(communication)
    
    operations = [lambda s: create_communication(s, comm) for comm in communications]
    
    transaction_manager.batch_communication_transaction(
        operations, 
        operation_name="batch_communication_processing"
    )
```

---

## Error Handling

### Error Types and Handling

#### 1. Connection Errors

```python
from sqlalchemy.exc import DisconnectionError, OperationalError, TimeoutError

def handle_connection_error(error: Exception):
    """Handle connection-related errors"""
    if isinstance(error, DisconnectionError):
        logger.error("Database connection lost")
        # Attempt to reconnect
        return retry_operation()
    elif isinstance(error, TimeoutError):
        logger.error("Database operation timed out")
        # Increase timeout and retry
        return retry_with_longer_timeout()
    elif isinstance(error, OperationalError):
        logger.error("Database operational error")
        # Check database status and retry
        return check_database_and_retry()
```

#### 2. Data Errors

```python
from sqlalchemy.exc import IntegrityError, DataError, ProgrammingError

def handle_data_error(error: Exception):
    """Handle data-related errors"""
    if isinstance(error, IntegrityError):
        logger.error("Data integrity constraint violated")
        # Don't retry, fix data issue
        return handle_integrity_violation(error)
    elif isinstance(error, DataError):
        logger.error("Data format error")
        # Validate and fix data
        return validate_and_fix_data(error)
    elif isinstance(error, ProgrammingError):
        logger.error("SQL programming error")
        # Fix SQL query
        return fix_sql_query(error)
```

#### 3. Celery-Specific Error Handling

```python
from backend.database.celery_session import CeleryDatabaseErrorHandler

def handle_celery_database_error(error: Exception, task_id: str):
    """Handle database errors in Celery tasks"""
    error_info = CeleryDatabaseErrorHandler.handle_communication_error(
        error, task_id, "communication_processing"
    )
    
    if CeleryDatabaseErrorHandler.should_retry(error):
        retry_delay = CeleryDatabaseErrorHandler.get_retry_delay(error, attempt=1)
        logger.info(f"Retrying task {task_id} in {retry_delay}s")
        return retry_task(task_id, retry_delay)
    else:
        logger.error(f"Task {task_id} failed permanently: {error}")
        return mark_task_failed(task_id, error_info)
```

### Retry Logic

#### 1. Exponential Backoff

```python
def retry_with_exponential_backoff(operation, max_retries=3, base_delay=1.0):
    """Retry operation with exponential backoff"""
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except (DisconnectionError, OperationalError, TimeoutError) as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                time.sleep(delay)
                continue
            else:
                logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
                raise
```

#### 2. Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Circuit breaker for database operations"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, operation):
        """Execute operation with circuit breaker protection"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = operation()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

---

## Best Practices

### 1. Session Lifecycle Management

```python
# ✅ Good: Use context managers
with session_scope() as session:
    # Database operations
    session.add(record)
    # Session automatically committed and closed

# ❌ Bad: Manual session management without proper cleanup
session = get_session()
try:
    session.add(record)
    session.commit()
finally:
    session.close()  # Easy to forget
```

### 2. Transaction Boundaries

```python
# ✅ Good: Clear transaction boundaries
def process_communication(user_id: int, data: dict):
    with session_scope() as session:
        # All operations in single transaction
        communication = CommunicationMetrics(**data)
        session.add(communication)
        
        user_prefs = session.query(CommunicationPreferences).filter_by(user_id=user_id).first()
        if user_prefs:
            user_prefs.last_communication = datetime.utcnow()
        
        # All changes committed together

# ❌ Bad: Multiple transactions for related operations
def process_communication_bad(user_id: int, data: dict):
    with session_scope() as session:
        communication = CommunicationMetrics(**data)
        session.add(communication)
        # First transaction commits
    
    with session_scope() as session:
        user_prefs = session.query(CommunicationPreferences).filter_by(user_id=user_id).first()
        if user_prefs:
            user_prefs.last_communication = datetime.utcnow()
        # Second transaction commits
```

### 3. Error Handling

```python
# ✅ Good: Proper error handling with logging
def safe_database_operation():
    try:
        with session_scope() as session:
            # Database operations
            result = session.query(CommunicationMetrics).all()
            return result
    except SQLAlchemyError as e:
        logger.error(f"Database operation failed: {e}")
        # Handle specific error types
        if isinstance(e, IntegrityError):
            return handle_integrity_error(e)
        elif isinstance(e, OperationalError):
            return handle_operational_error(e)
        else:
            raise

# ❌ Bad: Generic exception handling
def unsafe_database_operation():
    try:
        with session_scope() as session:
            result = session.query(CommunicationMetrics).all()
            return result
    except Exception as e:  # Too broad
        print(f"Error: {e}")  # No logging
        return None  # Silent failure
```

### 4. Connection Pooling

```python
# ✅ Good: Use appropriate pool for context
def heavy_analytics_query():
    with pool_context('analytics') as pool:
        with pool.connect() as conn:
            # Long-running analytics query
            result = conn.execute(text("SELECT * FROM communication_metrics WHERE date > '2025-01-01'"))
            return result.fetchall()

# ✅ Good: Use main pool for regular operations
def regular_operation():
    with pool_context('main') as pool:
        with pool.connect() as conn:
            # Regular database operation
            result = conn.execute(text("SELECT COUNT(*) FROM communication_metrics"))
            return result.scalar()
```

### 5. Celery Task Best Practices

```python
# ✅ Good: Use DatabaseTask base class
class SendCommunicationTask(DatabaseTask):
    def run(self, user_id: int, message: str):
        with self.db_session.session_scope() as session:
            # Task operations
            communication = CommunicationMetrics(
                user_id=user_id,
                message_type='sms',
                channel='sms',
                status='sent'
            )
            session.add(communication)
            # Session automatically managed

# ✅ Good: Use decorator for simple tasks
@with_celery_db_session()
def simple_communication_task(user_id: int, message: str):
    # Session automatically injected
    communication = CommunicationMetrics(
        user_id=user_id,
        message_type='sms',
        channel='sms',
        status='sent'
    )
    session.add(communication)
```

---

## Monitoring and Health Checks

### 1. Health Check Endpoints

```python
from flask import Blueprint, jsonify
from backend.database.session_manager import get_session_manager
from backend.database.connection_pool import PoolHealthChecker

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/database')
def database_health():
    """Database health check endpoint"""
    session_manager = get_session_manager()
    pool_health = PoolHealthChecker.check_all_pools()
    
    # Check session manager health
    session_health = session_manager.health_check()
    
    # Determine overall health
    all_healthy = (
        session_health['status'] == 'healthy' and
        all(pool['status'] == 'healthy' for pool in pool_health.values())
    )
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'session_manager': session_health,
        'connection_pools': pool_health,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if all_healthy else 503
```

### 2. Metrics Collection

```python
@health_bp.route('/metrics/database')
def database_metrics():
    """Database metrics endpoint"""
    pool_metrics = PoolHealthChecker.get_pool_metrics()
    performance_metrics = PoolHealthChecker.get_performance_metrics()
    
    return jsonify({
        'pool_metrics': pool_metrics,
        'performance_metrics': performance_metrics,
        'timestamp': datetime.utcnow().isoformat()
    })
```

### 3. Monitoring Dashboard

```python
@health_bp.route('/dashboard/database')
def database_dashboard():
    """Database monitoring dashboard"""
    health_status = PoolHealthChecker.check_all_pools()
    metrics = PoolHealthChecker.get_pool_metrics()
    performance = PoolHealthChecker.get_performance_metrics()
    
    # Calculate key performance indicators
    total_connections = sum(m.total_connections for m in metrics.values())
    active_connections = sum(m.active_connections for m in metrics.values())
    error_rate = performance['total_errors'] / max(performance['total_checkouts'], 1)
    
    return jsonify({
        'health_status': health_status,
        'kpis': {
            'total_connections': total_connections,
            'active_connections': active_connections,
            'connection_utilization': active_connections / max(total_connections, 1),
            'error_rate': error_rate,
            'average_checkout_time': performance['average_checkout_time']
        },
        'pools': {
            name: {
                'health': health_status.get(name, {}).get('status', 'unknown'),
                'metrics': {
                    'pool_size': metrics[name].pool_size,
                    'checked_out': metrics[name].checked_out,
                    'checked_in': metrics[name].checked_in,
                    'overflow': metrics[name].overflow,
                    'errors': metrics[name].connection_errors
                }
            }
            for name in metrics.keys()
        }
    })
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Pool Exhaustion

**Symptoms:**
- `QueuePool limit of size X overflow Y reached`
- Slow response times
- Database connection timeouts

**Solutions:**
```python
# Increase pool size
os.environ['DB_POOL_SIZE'] = '30'
os.environ['DB_MAX_OVERFLOW'] = '50'

# Check for connection leaks
def check_connection_leaks():
    pool_metrics = PoolHealthChecker.get_pool_metrics()
    for pool_name, metrics in pool_metrics.items():
        if metrics.checked_out > metrics.pool_size * 0.8:
            logger.warning(f"Pool {pool_name} may have connection leaks")
```

#### 2. Transaction Deadlocks

**Symptoms:**
- `deadlock detected` errors
- Hanging transactions
- Database locks

**Solutions:**
```python
# Use shorter transactions
def avoid_deadlocks():
    with session_scope() as session:
        # Keep transactions short
        result = session.query(CommunicationMetrics).filter_by(user_id=user_id).first()
        session.commit()  # Commit early
    
    # Process data outside transaction
    process_data(result)
    
    with session_scope() as session:
        # Update in separate transaction
        update_metrics(session, result)

# Use proper ordering
def consistent_ordering():
    with session_scope() as session:
        # Always lock tables in same order
        user = session.query(User).filter_by(id=user_id).with_for_update().first()
        prefs = session.query(CommunicationPreferences).filter_by(user_id=user_id).with_for_update().first()
```

#### 3. Memory Leaks

**Symptoms:**
- Increasing memory usage
- Slow performance over time
- Out of memory errors

**Solutions:**
```python
# Proper session cleanup
def prevent_memory_leaks():
    with session_scope() as session:
        # Use session.query() instead of session.query().all()
        for record in session.query(CommunicationMetrics).yield_per(100):
            process_record(record)
            # Records are automatically expired

# Clear session periodically
def clear_session_periodically():
    session_manager = get_session_manager()
    session_manager.reset_metrics()  # Clear accumulated metrics
```

#### 4. Performance Issues

**Symptoms:**
- Slow query execution
- High CPU usage
- Database timeouts

**Solutions:**
```python
# Use appropriate pool for workload
def optimize_for_workload():
    if is_analytics_query():
        with pool_context('analytics') as pool:
            # Use analytics pool for heavy queries
            execute_analytics_query(pool)
    else:
        with pool_context('main') as pool:
            # Use main pool for regular operations
            execute_regular_query(pool)

# Monitor query performance
def monitor_query_performance():
    with session_scope() as session:
        start_time = time.time()
        result = session.query(CommunicationMetrics).all()
        duration = time.time() - start_time
        
        if duration > 5.0:  # 5 second threshold
            logger.warning(f"Slow query detected: {duration:.2f}s")
```

### Debugging Tools

#### 1. Query Logging

```python
# Enable SQL logging
os.environ['DB_ECHO'] = 'true'

# Custom query logging
from sqlalchemy import event

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Log slow queries
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

#### 2. Connection Monitoring

```python
def monitor_connections():
    """Monitor active connections"""
    pool_metrics = PoolHealthChecker.get_pool_metrics()
    
    for pool_name, metrics in pool_metrics.items():
        logger.info(f"Pool {pool_name}:")
        logger.info(f"  Active connections: {metrics.active_connections}")
        logger.info(f"  Idle connections: {metrics.idle_connections}")
        logger.info(f"  Total connections: {metrics.total_connections}")
        logger.info(f"  Connection errors: {metrics.connection_errors}")
```

#### 3. Transaction Monitoring

```python
def monitor_transactions():
    """Monitor transaction activity"""
    session_manager = get_session_manager()
    stats = session_manager.get_session_stats()
    
    logger.info("Session Statistics:")
    logger.info(f"  Total sessions: {stats['total_sessions']}")
    logger.info(f"  Active sessions: {stats['active_sessions']}")
    logger.info(f"  Failed sessions: {stats['failed_sessions']}")
    logger.info(f"  Transaction rollbacks: {stats['transaction_rollbacks']}")
```

---

## Configuration Examples

### 1. Production Configuration

```python
# config/production.py
class ProductionConfig:
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pooling
    DB_POOL_SIZE = 20
    DB_MAX_OVERFLOW = 30
    DB_POOL_RECYCLE = 3600
    DB_POOL_TIMEOUT = 30
    
    # Celery pool settings
    CELERY_DB_POOL_SIZE = 10
    CELERY_DB_MAX_OVERFLOW = 20
    CELERY_DB_POOL_RECYCLE = 1800
    
    # Analytics pool settings
    ANALYTICS_DB_POOL_SIZE = 5
    ANALYTICS_DB_MAX_OVERFLOW = 10
    ANALYTICS_DB_POOL_TIMEOUT = 60
    
    # Monitoring
    DB_ENABLE_MONITORING = True
    DB_HEALTH_CHECK_INTERVAL = 300
```

### 2. Development Configuration

```python
# config/development.py
class DevelopmentConfig:
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/mingus_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # Connection pooling (smaller for development)
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    DB_POOL_RECYCLE = 1800
    
    # Enable SQL logging
    DB_ECHO = True
    DB_ECHO_POOL = True
    
    # Monitoring
    DB_ENABLE_MONITORING = True
    DB_HEALTH_CHECK_INTERVAL = 60
```

### 3. Testing Configuration

```python
# config/testing.py
class TestingConfig:
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable connection pooling for tests
    DB_POOL_SIZE = 1
    DB_MAX_OVERFLOW = 0
    
    # Disable monitoring
    DB_ENABLE_MONITORING = False
    
    # Enable SQL logging for debugging
    DB_ECHO = True
```

---

## Summary

The SQLAlchemy session management system provides:

1. **Robust Session Management**: Automatic session lifecycle management with proper cleanup
2. **Connection Pooling**: Multiple optimized pools for different workloads
3. **Transaction Management**: Comprehensive transaction handling with rollback support
4. **Error Handling**: Specific error handling for different database error types
5. **Monitoring**: Real-time health checks and performance monitoring
6. **Celery Integration**: Specialized session management for background tasks
7. **Best Practices**: Guidelines for optimal database usage

This system ensures reliable, performant, and maintainable database operations for the MINGUS Communication System. 