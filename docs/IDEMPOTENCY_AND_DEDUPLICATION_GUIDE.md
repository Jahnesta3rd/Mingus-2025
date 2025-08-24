# Idempotency and Deduplication Guide

## Overview

The MINGUS application implements comprehensive idempotency handling, event deduplication, and ordering mechanisms to ensure reliable and consistent webhook processing. This system prevents duplicate processing, maintains event ordering, and provides robust error recovery.

## 🔄 Core Concepts

### Idempotency
- **Definition**: An operation is idempotent if performing it multiple times has the same effect as performing it once
- **Purpose**: Prevents duplicate processing of webhook events
- **Implementation**: Uses unique idempotency keys for each operation

### Event Deduplication
- **Definition**: Identifying and handling duplicate events based on content and context
- **Purpose**: Prevents processing the same event multiple times
- **Implementation**: Uses content-based hashing and time windows

### Event Ordering
- **Definition**: Ensuring events are processed in the correct sequence
- **Purpose**: Maintains data consistency and prevents race conditions
- **Implementation**: Uses sequence numbers and dependency tracking

## 🏗️ Architecture

### Database Models

#### 1. WebhookEventRecord
Tracks processed webhook events for idempotency and deduplication.

```python
class WebhookEventRecord(Base):
    __tablename__ = 'webhook_event_records'
    
    # Event identification
    stripe_event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    
    # Processing information
    processing_status = Column(String(50), nullable=False, default='pending')
    processing_attempts = Column(Integer, default=0)
    
    # Idempotency and deduplication
    idempotency_key = Column(String(255), nullable=True, index=True)
    deduplication_hash = Column(String(64), nullable=True, index=True)
    is_duplicate = Column(Boolean, default=False)
    
    # Ordering and sequencing
    event_sequence_number = Column(Integer, nullable=True, index=True)
    event_created_at = Column(DateTime(timezone=True), nullable=False, index=True)
```

#### 2. EventProcessingState
Tracks processing state and ordering for webhook events.

```python
class EventProcessingState(Base):
    __tablename__ = 'event_processing_states'
    
    # State identification
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    
    # Processing state
    last_processed_event_id = Column(String(255), nullable=True)
    last_processed_sequence = Column(Integer, nullable=True)
    current_sequence_number = Column(Integer, default=0)
    
    # Error handling
    consecutive_failures = Column(Integer, default=0)
    last_failure_reason = Column(Text, nullable=True)
```

#### 3. IdempotencyKey
Manages idempotency keys for webhook operations.

```python
class IdempotencyKey(Base):
    __tablename__ = 'idempotency_keys'
    
    # Key identification
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_value = Column(String(255), nullable=False)
    operation_type = Column(String(100), nullable=False, index=True)
    
    # Processing state
    processing_status = Column(String(50), nullable=False, default='pending')
    processing_attempts = Column(Integer, default=0)
    
    # Result storage
    result_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_expired = Column(Boolean, default=False, index=True)
```

#### 4. EventDeduplication
Handles event deduplication logic and tracking.

```python
class EventDeduplication(Base):
    __tablename__ = 'event_deduplication'
    
    # Deduplication identification
    deduplication_hash = Column(String(64), nullable=False, unique=True, index=True)
    event_signature = Column(String(128), nullable=False, index=True)
    
    # Processing information
    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    occurrence_count = Column(Integer, default=1)
    
    # Deduplication strategy
    deduplication_strategy = Column(String(50), nullable=False, default='first_wins')
    time_window_seconds = Column(Integer, default=3600)
```

### Service Layer

#### IdempotencyService
Comprehensive service for handling idempotency, deduplication, and event ordering.

```python
class IdempotencyService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.default_expiration_hours = 24
        self.default_deduplication_window = 3600  # 1 hour
```

## 🔧 Key Features

### 1. Idempotency Key Management

#### Key Generation
```python
def generate_idempotency_key(
    self,
    operation_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> str:
    """Generate a unique idempotency key for an operation"""
```

#### Key Validation
```python
def check_idempotency(
    self,
    key_hash: str,
    operation_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None
) -> IdempotencyResult:
    """Check if an operation with the given idempotency key has already been processed"""
```

#### Result Storage
```python
def update_idempotency_key_result(
    self,
    key_hash: str,
    success: bool,
    result_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> None:
    """Update idempotency key with processing result"""
```

### 2. Event Deduplication

#### Hash Generation
```python
def generate_deduplication_hash(
    self,
    event_type: str,
    entity_type: Optional[str],
    entity_id: Optional[str],
    event_data: Dict[str, Any]
) -> str:
    """Generate a deduplication hash for an event"""
```

#### Deduplication Strategies
- **FIRST_WINS**: Only process the first occurrence of an event
- **LAST_WINS**: Process the most recent occurrence of an event
- **MERGE**: Merge multiple occurrences of an event
- **IGNORE**: Skip duplicate events entirely

#### Strategy Implementation
```python
def check_deduplication(
    self,
    deduplication_hash: str,
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    strategy: DeduplicationStrategy = DeduplicationStrategy.FIRST_WINS
) -> DeduplicationResult:
    """Check if an event is a duplicate based on deduplication hash"""
```

### 3. Event Ordering

#### Sequence Number Management
```python
def get_next_sequence_number(
    self,
    entity_type: str,
    entity_id: str,
    event_type: str
) -> int:
    """Get the next sequence number for an entity and event type"""
```

#### Ordering Validation
```python
def check_event_ordering(
    self,
    entity_type: str,
    entity_id: str,
    event_type: str,
    sequence_number: int
) -> OrderingResult:
    """Check if an event can be processed based on ordering requirements"""
```

#### State Updates
```python
def update_processing_state(
    self,
    entity_type: str,
    entity_id: str,
    event_type: str,
    event_id: str,
    sequence_number: int,
    success: bool,
    error_message: Optional[str] = None
) -> None:
    """Update processing state after event processing"""
```

## 🚀 Usage Examples

### Basic Webhook Processing with Idempotency

```python
from backend.webhooks.stripe_webhooks import StripeWebhookManager
from backend.services.idempotency_service import IdempotencyService

# Initialize services
webhook_manager = StripeWebhookManager(db_session, config)
idempotency_service = IdempotencyService(db_session)

# Process webhook with automatic idempotency handling
result = webhook_manager.process_webhook(
    payload=webhook_payload,
    signature=stripe_signature,
    source_ip=request.remote_addr,
    user_agent=request.headers.get('User-Agent'),
    request_id=request.headers.get('X-Request-ID')
)

if result.success:
    print(f"Webhook processed successfully: {result.message}")
else:
    print(f"Webhook processing failed: {result.error}")
```

### Manual Idempotency Key Management

```python
# Generate idempotency key
key_hash = idempotency_service.generate_idempotency_key(
    operation_type="customer.created",
    entity_type="customer",
    entity_id="cus_1234567890",
    additional_data={"source": "webhook"}
)

# Check if operation already processed
result = idempotency_service.check_idempotency(
    key_hash=key_hash,
    operation_type="customer.created",
    entity_type="customer",
    entity_id="cus_1234567890"
)

if result.is_duplicate:
    if result.existing_result:
        print(f"Operation already completed: {result.existing_result}")
    else:
        print(f"Operation in progress: {result.reason}")
else:
    # Create idempotency key and process
    idempotency_service.create_idempotency_key(
        key_hash=key_hash,
        key_value="customer_creation_001",
        operation_type="customer.created",
        entity_type="customer",
        entity_id="cus_1234567890"
    )
    
    # Process operation...
    
    # Update with result
    idempotency_service.update_idempotency_key_result(
        key_hash=key_hash,
        success=True,
        result_data={"customer_id": "cus_1234567890", "status": "created"}
    )
```

### Event Deduplication with Different Strategies

```python
# Generate deduplication hash
dedup_hash = idempotency_service.generate_deduplication_hash(
    event_type="customer.updated",
    entity_type="customer",
    entity_id="cus_1234567890",
    event_data=customer_update_data
)

# Check with first_wins strategy
result = idempotency_service.check_deduplication(
    deduplication_hash=dedup_hash,
    event_type="customer.updated",
    entity_type="customer",
    entity_id="cus_1234567890",
    strategy=DeduplicationStrategy.FIRST_WINS
)

if result.is_duplicate:
    if result.strategy == DeduplicationStrategy.FIRST_WINS:
        print("Duplicate event - skipping (first_wins strategy)")
    elif result.strategy == DeduplicationStrategy.LAST_WINS:
        print("Duplicate event - processing (last_wins strategy)")
    elif result.strategy == DeduplicationStrategy.MERGE:
        print("Duplicate event - merging with existing data")
    else:  # IGNORE
        print("Duplicate event - ignoring")
else:
    # Create deduplication record and process
    idempotency_service.create_deduplication_record(
        deduplication_hash=dedup_hash,
        event_type="customer.updated",
        entity_type="customer",
        entity_id="cus_1234567890",
        strategy=DeduplicationStrategy.FIRST_WINS
    )
    
    # Process event...
```

### Event Ordering and Sequencing

```python
# Get next sequence number
sequence_number = idempotency_service.get_next_sequence_number(
    entity_type="customer",
    entity_id="cus_1234567890",
    event_type="customer.updated"
)

# Check if event can be processed
ordering_result = idempotency_service.check_event_ordering(
    entity_type="customer",
    entity_id="cus_1234567890",
    event_type="customer.updated",
    sequence_number=sequence_number
)

if ordering_result.can_process:
    # Process event...
    
    # Update processing state
    idempotency_service.update_processing_state(
        entity_type="customer",
        entity_id="cus_1234567890",
        event_type="customer.updated",
        event_id="evt_1234567890",
        sequence_number=sequence_number,
        success=True
    )
else:
    print(f"Cannot process event: {ordering_result.reason}")
```

## 📊 Monitoring and Analytics

### Processing Metrics

```python
# Get processing metrics
metrics = idempotency_service.get_processing_metrics(
    entity_type="customer",
    entity_id="cus_1234567890",
    time_range_hours=24
)

print(f"Total events: {metrics['total_events']}")
print(f"Success rate: {metrics['success_rate']:.2f}%")
print(f"Duplicate rate: {metrics['duplicate_rate']:.2f}%")
print(f"Average processing time: {metrics['avg_processing_time_seconds']:.3f}s")
```

### Cleanup Operations

```python
# Clean up expired records
cleanup_stats = idempotency_service.cleanup_expired_records()

print(f"Expired idempotency keys: {cleanup_stats['expired_idempotency_keys']}")
print(f"Expired deduplication records: {cleanup_stats['expired_deduplication_records']}")
print(f"Old webhook records: {cleanup_stats['old_webhook_records']}")
```

## 🔧 Configuration

### Environment Variables

```bash
# Idempotency Configuration
IDEMPOTENCY_EXPIRATION_HOURS=24
DEDUPLICATION_WINDOW_SECONDS=3600
MAX_RETRY_ATTEMPTS=3
PROCESSING_TIMEOUT_MINUTES=30

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/mingus_db
```

### Service Configuration

```python
# Initialize with custom settings
idempotency_service = IdempotencyService(
    db_session=db_session,
    default_expiration_hours=48,  # Custom expiration
    default_deduplication_window=7200  # 2 hour window
)
```

## 🛡️ Security Considerations

### Idempotency Key Security
- Keys are cryptographically secure (SHA-256)
- Include timestamp and random components
- Expire automatically to prevent key exhaustion

### Deduplication Security
- Hash-based deduplication prevents content tampering
- Time windows prevent replay attacks
- Configurable strategies for different use cases

### Event Ordering Security
- Sequence numbers prevent race conditions
- Dependency tracking ensures correct processing order
- Failure handling maintains consistency

## 🔍 Troubleshooting

### Common Issues

#### 1. Duplicate Processing
**Symptoms**: Same event processed multiple times
**Causes**: 
- Idempotency key not generated correctly
- Deduplication hash collision
- Race condition in key creation

**Solutions**:
```python
# Check idempotency key generation
key_hash = idempotency_service.generate_idempotency_key(
    operation_type=event.event_type,
    entity_type=entity_type,
    entity_id=entity_id,
    additional_data={"timestamp": event.created_at.isoformat()}
)

# Verify deduplication hash
dedup_hash = idempotency_service.generate_deduplication_hash(
    event_type=event.event_type,
    entity_type=entity_type,
    entity_id=entity_id,
    event_data=event.event_data
)
```

#### 2. Event Ordering Issues
**Symptoms**: Events processed out of order
**Causes**:
- Sequence number generation failure
- Processing state not updated correctly
- Concurrent processing conflicts

**Solutions**:
```python
# Check processing state
state = db_session.query(EventProcessingState).filter(
    and_(
        EventProcessingState.entity_type == entity_type,
        EventProcessingState.entity_id == entity_id,
        EventProcessingState.event_type == event_type
    )
).first()

# Reset sequence if needed
if state and state.consecutive_failures > 5:
    state.current_sequence_number = 0
    state.consecutive_failures = 0
    db_session.commit()
```

#### 3. Performance Issues
**Symptoms**: Slow processing, high database load
**Causes**:
- Missing database indexes
- Large number of expired records
- Inefficient queries

**Solutions**:
```python
# Regular cleanup
cleanup_stats = idempotency_service.cleanup_expired_records()

# Monitor metrics
metrics = idempotency_service.get_processing_metrics(time_range_hours=1)
if metrics['avg_processing_time_seconds'] > 5.0:
    logger.warning("High processing time detected")
```

### Debugging Tools

#### Enable Debug Logging
```python
import logging
logging.getLogger('backend.services.idempotency_service').setLevel(logging.DEBUG)
```

#### Check Processing State
```python
def debug_processing_state(entity_type: str, entity_id: str, event_type: str):
    state = db_session.query(EventProcessingState).filter(
        and_(
            EventProcessingState.entity_type == entity_type,
            EventProcessingState.entity_id == entity_id,
            EventProcessingState.event_type == event_type
        )
    ).first()
    
    if state:
        print(f"Current sequence: {state.current_sequence_number}")
        print(f"Last processed: {state.last_processed_sequence}")
        print(f"Consecutive failures: {state.consecutive_failures}")
    else:
        print("No processing state found")
```

## 🚀 Best Practices

### 1. Idempotency Key Design
- Include all relevant context in key generation
- Use consistent key format across operations
- Set appropriate expiration times

### 2. Deduplication Strategy Selection
- Use `FIRST_WINS` for most webhook events
- Use `LAST_WINS` for configuration updates
- Use `MERGE` for complex state changes
- Use `IGNORE` for informational events

### 3. Event Ordering
- Always check ordering before processing
- Update processing state after completion
- Handle failures gracefully

### 4. Monitoring and Maintenance
- Monitor processing metrics regularly
- Clean up expired records automatically
- Set up alerts for high failure rates

### 5. Error Handling
- Always update idempotency keys with results
- Handle partial failures correctly
- Provide detailed error messages

## 📈 Performance Optimization

### Database Indexes
Ensure proper indexes are created:
```sql
-- Idempotency keys
CREATE INDEX idx_idempotency_key_hash ON idempotency_keys(key_hash);
CREATE INDEX idx_idempotency_expiration ON idempotency_keys(expires_at, is_expired);

-- Deduplication records
CREATE INDEX idx_deduplication_hash ON event_deduplication(deduplication_hash);
CREATE INDEX idx_deduplication_time ON event_deduplication(first_seen_at, last_seen_at);

-- Processing state
CREATE INDEX idx_processing_state_entity ON event_processing_states(entity_type, entity_id);
CREATE INDEX idx_processing_state_sequence ON event_processing_states(current_sequence_number);
```

### Caching Strategy
Consider caching frequently accessed data:
```python
# Cache processing state
@lru_cache(maxsize=1000)
def get_processing_state(entity_type: str, entity_id: str, event_type: str):
    return db_session.query(EventProcessingState).filter(
        and_(
            EventProcessingState.entity_type == entity_type,
            EventProcessingState.entity_id == entity_id,
            EventProcessingState.event_type == event_type
        )
    ).first()
```

### Batch Operations
For high-volume processing:
```python
def batch_update_processing_states(updates: List[Dict]):
    """Batch update processing states for better performance"""
    for update in updates:
        state = EventProcessingState(**update)
        db_session.add(state)
    db_session.commit()
```

## 🎯 Conclusion

The idempotency and deduplication system provides comprehensive protection against duplicate processing, ensures event ordering, and maintains data consistency. By following the best practices and monitoring guidelines, you can ensure reliable and efficient webhook processing in your MINGUS application.

The system is designed to be:
- **Reliable**: Prevents duplicate processing and maintains consistency
- **Scalable**: Handles high-volume event processing efficiently
- **Configurable**: Supports different strategies for different use cases
- **Monitorable**: Provides comprehensive metrics and debugging tools
- **Maintainable**: Includes automatic cleanup and error recovery 