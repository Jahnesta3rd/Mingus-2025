# Flask Integration Layer Guide

## Overview

The Flask Integration Layer provides seamless integration between Flask application factory, Celery task system, communication preferences, and analytics systems. It ensures proper app context handling, database session management, and service coordination across all components.

## Architecture

### Core Components

1. **Flask-Celery Integration** (`backend/integration/flask_celery_integration.py`)
   - Configures Celery with Flask app factory pattern
   - Manages database sessions across Flask and Celery
   - Provides app context handling for background tasks

2. **Communication Orchestrator** (`backend/services/communication_orchestrator.py`)
   - Main service for orchestrating smart communications
   - Integrates user preferences, Celery tasks, and analytics
   - Handles failures and fallbacks

3. **API Endpoints** (`backend/routes/communication_orchestrator.py`)
   - RESTful API for communication management
   - JWT authentication and request validation
   - Batch operations and health checks

## Flask-Celery Integration

### Configuration

The integration layer automatically configures Celery with Flask:

```python
# In app_factory.py
from backend.integration.flask_celery_integration import init_flask_celery_integration

def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)
    # ... other initialization
    
    # Initialize Flask-Celery integration
    init_flask_celery_integration(app)
    
    return app
```

### Database Session Management

The integration provides proper database session handling:

```python
from backend.integration.flask_celery_integration import FlaskTaskBase

class MyCeleryTask(FlaskTaskBase):
    def run(self, user_id, data):
        with self.database_session() as session:
            # Use session for database operations
            user = session.query(User).filter_by(id=user_id).first()
            # ... process data
            session.commit()
```

### App Context Handling

Tasks automatically run within Flask app context:

```python
class MyTask(FlaskTaskBase):
    def run(self, *args, **kwargs):
        # Automatically runs within Flask app context
        with self.flask_app_context():
            # Access Flask app, config, etc.
            current_app.config['SOME_SETTING']
```

## Communication Orchestrator

### Core Service

The `CommunicationOrchestrator` is the main service that coordinates all communication activities:

```python
from backend.services.communication_orchestrator import (
    CommunicationOrchestrator,
    TriggerType,
    CommunicationChannel,
    CommunicationPriority
)

# Initialize orchestrator
orchestrator = CommunicationOrchestrator()

# Send smart communication
result = orchestrator.send_smart_communication(
    user_id=123,
    trigger_type=TriggerType.FINANCIAL_ALERT,
    data={'amount': 100.50, 'account': 'checking'},
    channel=CommunicationChannel.SMS,
    priority=CommunicationPriority.CRITICAL
)
```

### Smart Communication Flow

1. **Request Creation**: Creates `CommunicationRequest` with defaults
2. **Validation**: Checks user preferences and consent
3. **Optimization**: Determines optimal channel and timing
4. **Execution**: Routes to appropriate Celery task
5. **Analytics**: Tracks communication metrics
6. **Fallback**: Handles failures with alternative channels

### User Preference Integration

The orchestrator respects user communication preferences:

```python
# Check if user can receive SMS
user_prefs = orchestrator.preference_service.get_user_communication_prefs(user_id)
if user_prefs.get('sms_enabled', True):
    # Send SMS
    pass

# Check consent for specific message type
consent_result = orchestrator.preference_service.check_consent_for_message_type(
    user_id, 'financial_alert', 'sms'
)
if consent_result['can_send']:
    # Send communication
    pass
```

### Analytics Integration

All communications are automatically tracked:

```python
# Analytics are tracked automatically in send_smart_communication
# Manual tracking is also available:
orchestrator.flask_analytics_service.track_message_sent(
    user_id=123,
    channel='sms',
    message_type='financial_alert',
    cost=0.05
)
```

## API Endpoints

### Send Communication

**Endpoint**: `POST /api/communication/send`

**Request**:
```json
{
    "user_id": 123,
    "trigger_type": "financial_alert",
    "data": {
        "amount": 100.50,
        "account": "checking",
        "threshold": 200.00
    },
    "channel": "sms",
    "priority": "critical",
    "scheduled_time": "2025-01-27T10:00:00Z"
}
```

**Response**:
```json
{
    "success": true,
    "task_id": "abc123",
    "cost": 0.05,
    "fallback_used": false,
    "analytics_tracked": true,
    "message": "Communication scheduled successfully"
}
```

### Get Communication Status

**Endpoint**: `GET /api/communication/status/<task_id>`

**Response**:
```json
{
    "task_id": "abc123",
    "status": "SUCCESS",
    "result": {
        "message_id": "msg_456",
        "delivered": true
    },
    "info": {
        "delivery_time": "2025-01-27T10:01:00Z"
    }
}
```

### Cancel Communication

**Endpoint**: `POST /api/communication/cancel/<task_id>`

**Response**:
```json
{
    "success": true,
    "message": "Communication cancelled successfully"
}
```

### Batch Communications

**Endpoint**: `POST /api/communication/batch`

**Request**:
```json
{
    "communications": [
        {
            "user_id": 123,
            "trigger_type": "financial_alert",
            "data": {"amount": 100},
            "channel": "sms",
            "priority": "critical"
        },
        {
            "user_id": 456,
            "trigger_type": "weekly_checkin",
            "data": {"message": "check in"},
            "channel": "email"
        }
    ]
}
```

**Response**:
```json
{
    "success": true,
    "results": [
        {
            "user_id": 123,
            "success": true,
            "task_id": "abc123",
            "cost": 0.05
        },
        {
            "user_id": 456,
            "success": false,
            "error": "User has opted out"
        }
    ],
    "summary": {
        "total": 2,
        "successful": 1,
        "failed": 1,
        "total_cost": 0.05
    }
}
```

### Health Check

**Endpoint**: `GET /api/communication/health`

**Response**:
```json
{
    "status": "healthy",
    "services": {
        "preference_service": true,
        "analytics_service": true,
        "celery_integration": true
    },
    "timestamp": "2025-01-27T10:00:00Z"
}
```

### Get Trigger Types

**Endpoint**: `GET /api/communication/trigger-types`

**Response**:
```json
{
    "trigger_types": [
        {
            "value": "financial_alert",
            "name": "Financial Alert",
            "description": "Critical financial notifications",
            "default_channel": "sms",
            "default_priority": "critical"
        }
    ]
}
```

## Usage Examples

### Basic Communication Send

```python
from backend.services.communication_orchestrator import send_smart_communication, TriggerType

# Send immediate financial alert
result = send_smart_communication(
    user_id=123,
    trigger_type=TriggerType.FINANCIAL_ALERT,
    data={
        'amount': 100.50,
        'account': 'checking',
        'threshold': 200.00
    }
)

if result.success:
    print(f"Communication sent! Task ID: {result.task_id}")
else:
    print(f"Failed: {result.error_message}")
```

### Scheduled Communication

```python
from datetime import datetime, timedelta

# Schedule for tomorrow at 9 AM
scheduled_time = datetime.utcnow() + timedelta(days=1)
scheduled_time = scheduled_time.replace(hour=9, minute=0, second=0, microsecond=0)

result = send_smart_communication(
    user_id=123,
    trigger_type=TriggerType.WEEKLY_CHECKIN,
    data={'week_number': 3},
    scheduled_time=scheduled_time
)
```

### Batch Communications

```python
from backend.services.communication_orchestrator import CommunicationOrchestrator

orchestrator = CommunicationOrchestrator()

# Prepare batch of communications
communications = []
for user_id in [123, 456, 789]:
    communications.append({
        'user_id': user_id,
        'trigger_type': TriggerType.MONTHLY_REPORT,
        'data': {'month': 'January', 'year': 2025}
    })

# Send batch
for comm in communications:
    result = orchestrator.send_smart_communication(**comm)
    print(f"User {comm['user_id']}: {'Success' if result.success else 'Failed'}")
```

### Integration with Celery Tasks

```python
from backend.tasks.mingus_celery_tasks import send_critical_financial_alert

# Direct Celery task execution
task = send_critical_financial_alert.delay(
    user_id=123,
    trigger_type='financial_alert',
    data={'amount': 100.50}
)

# Check status
if task.ready():
    result = task.get()
    print(f"Task completed: {result}")
```

## Error Handling

### Communication Failures

The orchestrator handles failures gracefully:

```python
result = send_smart_communication(user_id=123, trigger_type=TriggerType.FINANCIAL_ALERT, data={})

if not result.success:
    if result.fallback_used:
        print("Primary channel failed, fallback used")
    else:
        print(f"Communication failed: {result.error_message}")
```

### Database Session Errors

```python
from backend.integration.flask_celery_integration import FlaskTaskBase

class MyTask(FlaskTaskBase):
    def run(self, user_id):
        try:
            with self.database_session() as session:
                # Database operations
                session.commit()
        except Exception as e:
            logger.error(f"Database error: {e}")
            # Session automatically rolled back
            raise
```

### Celery Integration Errors

```python
from backend.integration.flask_celery_integration import get_flask_celery_integration

integration = get_flask_celery_integration()
if integration:
    # Celery is available
    task = integration.execute_task_with_context('task_name', args)
else:
    # Handle Celery not available
    logger.error("Celery integration not available")
```

## Configuration

### Environment Variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ALWAYS_EAGER=false

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/mingus
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
```

### Flask Configuration

```python
# config/development.py
class DevelopmentConfig:
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_ALWAYS_EAGER = False
    
    DATABASE_URL = 'postgresql://user:pass@localhost/mingus'
    DB_POOL_SIZE = 10
    DB_MAX_OVERFLOW = 20
    
    JWT_SECRET_KEY = 'dev-secret-key'
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
# Run all communication orchestrator tests
pytest tests/test_communication_orchestrator.py -v

# Run specific test class
pytest tests/test_communication_orchestrator.py::TestCommunicationOrchestrator -v

# Run specific test method
pytest tests/test_communication_orchestrator.py::TestCommunicationOrchestrator::test_send_smart_communication -v
```

### Integration Tests

```python
# Test full integration
def test_full_communication_flow():
    # Create Flask app
    app = create_app('testing')
    
    with app.test_client() as client:
        # Send communication
        response = client.post('/api/communication/send', json={
            'user_id': 123,
            'trigger_type': 'financial_alert',
            'data': {'amount': 100}
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Check status
        task_id = data['task_id']
        status_response = client.get(f'/api/communication/status/{task_id}')
        assert status_response.status_code == 200
```

## Monitoring and Health Checks

### Health Check Endpoint

```bash
# Check communication system health
curl -H "Authorization: Bearer $JWT_TOKEN" \
     http://localhost:5000/api/communication/health
```

### Celery Health Check

```bash
# Check Celery integration health
curl -H "Authorization: Bearer $JWT_TOKEN" \
     http://localhost:5000/api/celery/health
```

### Logging

The integration layer provides comprehensive logging:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log communication events
logger.info(f"Communication sent to user {user_id}")
logger.warning(f"Communication failed for user {user_id}: {error}")
logger.error(f"Database error in communication: {e}")
```

## Best Practices

### 1. Always Use the Orchestrator

```python
# Good: Use orchestrator for all communications
result = send_smart_communication(user_id, trigger_type, data)

# Bad: Direct Celery task calls (bypasses preferences, analytics)
task = send_sms.delay(user_id, message)
```

### 2. Handle Failures Gracefully

```python
result = send_smart_communication(user_id, trigger_type, data)

if not result.success:
    if result.fallback_used:
        logger.info("Fallback communication used")
    else:
        logger.error(f"Communication failed: {result.error_message}")
        # Implement retry logic or alerting
```

### 3. Use Batch Operations for Multiple Communications

```python
# Good: Use batch endpoint for multiple communications
communications = [
    {'user_id': 123, 'trigger_type': 'alert', 'data': {}},
    {'user_id': 456, 'trigger_type': 'alert', 'data': {}}
]
# Send via batch endpoint

# Bad: Multiple individual calls
for comm in communications:
    send_smart_communication(**comm)
```

### 4. Monitor Communication Costs

```python
result = send_smart_communication(user_id, trigger_type, data)
total_cost += result.cost

# Track costs for budget management
if total_cost > daily_budget:
    logger.warning("Daily communication budget exceeded")
```

### 5. Use Appropriate Priorities

```python
# Critical: Financial alerts, payment reminders
send_smart_communication(user_id, TriggerType.FINANCIAL_ALERT, data, priority=CommunicationPriority.CRITICAL)

# Low: Educational content, monthly reports
send_smart_communication(user_id, TriggerType.EDUCATIONAL_CONTENT, data, priority=CommunicationPriority.LOW)
```

## Troubleshooting

### Common Issues

1. **Celery Not Available**
   - Check Redis connection
   - Verify Celery worker is running
   - Check `CELERY_BROKER_URL` configuration

2. **Database Session Errors**
   - Ensure proper session cleanup
   - Check database connection pool
   - Verify transaction management

3. **User Preferences Not Found**
   - Check if user exists
   - Verify preferences are set
   - Check consent status

4. **Communication Failures**
   - Check user opt-out status
   - Verify frequency limits
   - Check external service availability (Twilio, Resend)

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('backend.services.communication_orchestrator').setLevel(logging.DEBUG)
logging.getLogger('backend.integration.flask_celery_integration').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Advanced Analytics**: Machine learning for optimal send times
2. **A/B Testing**: Built-in testing framework for communication strategies
3. **Template Management**: Dynamic content templates
4. **Rate Limiting**: Advanced rate limiting per user/trigger type
5. **Webhook Integration**: Real-time status updates
6. **Multi-language Support**: Internationalization for communications
7. **Advanced Fallbacks**: Multiple fallback strategies
8. **Cost Optimization**: Smart cost management and budget controls 