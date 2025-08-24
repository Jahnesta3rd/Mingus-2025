"""
Webhook Event Tracking Models for Idempotency and Deduplication
==============================================================

SQLAlchemy models for tracking webhook events to ensure idempotency,
prevent duplicate processing, and maintain proper event ordering.

Models:
- WebhookEventRecord: Tracks processed webhook events
- EventProcessingState: Tracks processing state and ordering
- IdempotencyKey: Manages idempotency keys for operations
- EventDeduplication: Handles event deduplication logic

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from . import Base


class WebhookEventRecord(Base):
    """Tracks processed webhook events for idempotency and deduplication"""
    
    __tablename__ = 'webhook_event_records'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    stripe_event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_source = Column(String(50), nullable=False, default='stripe')
    
    # Processing information
    processing_status = Column(String(50), nullable=False, default='pending')  # pending, processing, completed, failed, skipped
    processing_attempts = Column(Integer, default=0)
    last_processing_attempt = Column(DateTime(timezone=True))
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    
    # Event data and context
    event_data = Column(JSONB, nullable=False, default=dict)
    event_metadata = Column(JSONB, nullable=True)
    source_ip = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(255))
    
    # Ordering and sequencing
    event_sequence_number = Column(Integer, nullable=True, index=True)
    event_created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Idempotency and deduplication
    idempotency_key = Column(String(255), nullable=True, index=True)
    deduplication_hash = Column(String(64), nullable=True, index=True)
    is_duplicate = Column(Boolean, default=False)
    original_event_id = Column(UUID(as_uuid=True), ForeignKey('webhook_event_records.id'), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    retry_after = Column(DateTime(timezone=True), nullable=True)
    
    # Related entities
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=True, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    customer = relationship("Customer")
    subscription = relationship("Subscription")
    user = relationship("User")
    original_event = relationship("WebhookEventRecord", remote_side=[id])
    duplicate_events = relationship("WebhookEventRecord", back_populates="original_event")
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_event_status_type', 'processing_status', 'event_type'),
        Index('idx_webhook_event_sequence', 'event_sequence_number', 'event_created_at'),
        Index('idx_webhook_event_deduplication', 'deduplication_hash', 'event_created_at'),
        Index('idx_webhook_event_retry', 'processing_status', 'retry_after'),
        Index('idx_webhook_event_processing_time', 'processing_started_at', 'processing_completed_at'),
        UniqueConstraint('stripe_event_id', name='uq_webhook_event_stripe_id'),
    )
    
    def __repr__(self):
        return f'<WebhookEventRecord {self.stripe_event_id}: {self.event_type}>'
    
    @validates('processing_status')
    def validate_processing_status(self, key, value):
        """Validate processing status"""
        valid_statuses = ['pending', 'processing', 'completed', 'failed', 'skipped', 'retry']
        if value not in valid_statuses:
            raise ValueError(f"Invalid processing status: {value}")
        return value


class EventProcessingState(Base):
    """Tracks processing state and ordering for webhook events"""
    
    __tablename__ = 'event_processing_states'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # State identification
    entity_type = Column(String(50), nullable=False)  # customer, subscription, invoice, etc.
    entity_id = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    
    # Processing state
    last_processed_event_id = Column(String(255), nullable=True)
    last_processed_sequence = Column(Integer, nullable=True)
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Ordering information
    current_sequence_number = Column(Integer, default=0)
    expected_next_sequence = Column(Integer, nullable=True)
    
    # Processing metadata
    processing_window_start = Column(DateTime(timezone=True), nullable=True)
    processing_window_end = Column(DateTime(timezone=True), nullable=True)
    events_in_window = Column(Integer, default=0)
    
    # Error handling
    consecutive_failures = Column(Integer, default=0)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_event_state_entity', 'entity_type', 'entity_id'),
        Index('idx_event_state_sequence', 'entity_type', 'entity_id', 'current_sequence_number'),
        Index('idx_event_state_failures', 'consecutive_failures', 'last_failure_at'),
        UniqueConstraint('entity_type', 'entity_id', 'event_type', name='uq_event_state_entity_type'),
    )
    
    def __repr__(self):
        return f'<EventProcessingState {self.entity_type}:{self.entity_id} - {self.event_type}>'


class IdempotencyKey(Base):
    """Manages idempotency keys for webhook operations"""
    
    __tablename__ = 'idempotency_keys'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Key identification
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_value = Column(String(255), nullable=False)
    operation_type = Column(String(100), nullable=False, index=True)
    
    # Operation context
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(255), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # Processing state
    processing_status = Column(String(50), nullable=False, default='pending')  # pending, processing, completed, failed
    processing_attempts = Column(Integer, default=0)
    last_processing_attempt = Column(DateTime(timezone=True))
    
    # Result storage
    result_data = Column(JSONB, nullable=True)
    result_metadata = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Expiration and cleanup
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_expired = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_idempotency_key_operation', 'operation_type', 'entity_type', 'entity_id'),
        Index('idx_idempotency_key_expiration', 'expires_at', 'is_expired'),
        Index('idx_idempotency_key_status', 'processing_status', 'created_at'),
    )
    
    def __repr__(self):
        return f'<IdempotencyKey {self.key_value}: {self.operation_type}>'
    
    @validates('processing_status')
    def validate_processing_status(self, key, value):
        """Validate processing status"""
        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        if value not in valid_statuses:
            raise ValueError(f"Invalid processing status: {value}")
        return value


class EventDeduplication(Base):
    """Handles event deduplication logic and tracking"""
    
    __tablename__ = 'event_deduplication'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Deduplication identification
    deduplication_hash = Column(String(64), nullable=False, unique=True, index=True)
    event_signature = Column(String(128), nullable=False, index=True)
    
    # Event information
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(255), nullable=True)
    
    # Processing information
    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    occurrence_count = Column(Integer, default=1)
    
    # Deduplication strategy
    deduplication_strategy = Column(String(50), nullable=False, default='first_wins')  # first_wins, last_wins, merge
    time_window_seconds = Column(Integer, default=3600)  # 1 hour default
    
    # Processing result
    processed_event_id = Column(UUID(as_uuid=True), ForeignKey('webhook_event_records.id'), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    processed_event = relationship("WebhookEventRecord")
    
    # Indexes
    __table_args__ = (
        Index('idx_deduplication_event_type', 'event_type', 'entity_type', 'entity_id'),
        Index('idx_deduplication_time_window', 'first_seen_at', 'last_seen_at'),
        Index('idx_deduplication_occurrence', 'occurrence_count', 'last_seen_at'),
    )
    
    def __repr__(self):
        return f'<EventDeduplication {self.deduplication_hash}: {self.event_type}>'
    
    @validates('deduplication_strategy')
    def validate_deduplication_strategy(self, key, value):
        """Validate deduplication strategy"""
        valid_strategies = ['first_wins', 'last_wins', 'merge', 'ignore']
        if value not in valid_strategies:
            raise ValueError(f"Invalid deduplication strategy: {value}")
        return value


class EventOrderingQueue(Base):
    """Manages event ordering and processing queue"""
    
    __tablename__ = 'event_ordering_queue'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Queue identification
    queue_name = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    
    # Event information
    event_record_id = Column(UUID(as_uuid=True), ForeignKey('webhook_event_records.id'), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    
    # Queue state
    queue_status = Column(String(50), nullable=False, default='queued')  # queued, processing, completed, failed
    queued_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dependencies
    depends_on_sequence = Column(Integer, nullable=True)
    dependency_satisfied = Column(Boolean, default=True)
    
    # Error handling
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    event_record = relationship("WebhookEventRecord")
    
    # Indexes
    __table_args__ = (
        Index('idx_ordering_queue_entity', 'entity_type', 'entity_id', 'sequence_number'),
        Index('idx_ordering_queue_status', 'queue_status', 'priority', 'queued_at'),
        Index('idx_ordering_queue_dependencies', 'depends_on_sequence', 'dependency_satisfied'),
        Index('idx_ordering_queue_retry', 'queue_status', 'next_retry_at'),
        UniqueConstraint('queue_name', 'entity_type', 'entity_id', 'sequence_number', name='uq_ordering_queue_sequence'),
    )
    
    def __repr__(self):
        return f'<EventOrderingQueue {self.queue_name}:{self.entity_id} - {self.sequence_number}>'
    
    @validates('queue_status')
    def validate_queue_status(self, key, value):
        """Validate queue status"""
        valid_statuses = ['queued', 'processing', 'completed', 'failed', 'retry']
        if value not in valid_statuses:
            raise ValueError(f"Invalid queue status: {value}")
        return value 