"""
Payment Recovery Database Models
===============================

SQLAlchemy models for payment recovery system:
- PaymentRecoveryRecord: Tracks payment failures and recovery attempts
- DunningEvent: Records dunning communication events
- RecoveryStrategy: Stores recovery strategy configurations
- PaymentFailure: Historical payment failure data
- RecoveryAction: Scheduled and executed recovery actions

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from .base import Base


class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"


class RecoveryStatus(enum.Enum):
    """Recovery status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RECOVERED = "recovered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class DunningStage(enum.Enum):
    """Dunning stage enumeration"""
    SOFT_FAILURE = "soft_failure"
    HARD_FAILURE = "hard_failure"
    DUNNING_1 = "dunning_1"
    DUNNING_2 = "dunning_2"
    DUNNING_3 = "dunning_3"
    DUNNING_4 = "dunning_4"
    DUNNING_5 = "dunning_5"
    FINAL_NOTICE = "final_notice"
    CANCELLATION = "cancellation"
    RECOVERY = "recovery"


class RecoveryStrategy(enum.Enum):
    """Recovery strategy enumeration"""
    AUTOMATIC_RETRY = "automatic_retry"
    PAYMENT_METHOD_UPDATE = "payment_method_update"
    GRACE_PERIOD = "grace_period"
    PARTIAL_PAYMENT = "partial_payment"
    PAYMENT_PLAN = "payment_plan"
    MANUAL_INTERVENTION = "manual_intervention"
    CANCELLATION = "cancellation"


class ActionStatus(enum.Enum):
    """Action status enumeration"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentRecoveryRecord(Base):
    """Payment recovery record model"""
    
    __tablename__ = 'payment_recovery_records'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False)
    
    # Payment information
    invoice_id = Column(String(255), nullable=False)
    payment_intent_id = Column(String(255), nullable=False)
    original_payment_intent_id = Column(String(255), nullable=True)
    
    # Failure information
    failure_reason = Column(String(500), nullable=False)
    failure_code = Column(String(100), nullable=False)
    failure_message = Column(Text, nullable=True)
    
    # Amount information
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='usd', nullable=False)
    original_amount = Column(Float, nullable=True)
    
    # Status and tracking
    status = Column(SQLEnum(RecoveryStatus), default=RecoveryStatus.PENDING, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retry_attempts = Column(Integer, default=5, nullable=False)
    
    # Timestamps
    failed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    recovered_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Recovery information
    recovery_strategy = Column(SQLEnum(RecoveryStrategy), nullable=True)
    dunning_stage = Column(SQLEnum(DunningStage), default=DunningStage.SOFT_FAILURE, nullable=False)
    grace_period_until = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    error_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="payment_recovery_records")
    subscription = relationship("Subscription", back_populates="payment_recovery_records")
    dunning_events = relationship("DunningEvent", back_populates="recovery_record", cascade="all, delete-orphan")
    recovery_actions = relationship("RecoveryAction", back_populates="recovery_record", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PaymentRecoveryRecord(id={self.id}, customer_id={self.customer_id}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'subscription_id': str(self.subscription_id),
            'invoice_id': self.invoice_id,
            'payment_intent_id': self.payment_intent_id,
            'original_payment_intent_id': self.original_payment_intent_id,
            'failure_reason': self.failure_reason,
            'failure_code': self.failure_code,
            'failure_message': self.failure_message,
            'amount': self.amount,
            'currency': self.currency,
            'original_amount': self.original_amount,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retry_attempts': self.max_retry_attempts,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'recovery_strategy': self.recovery_strategy.value if self.recovery_strategy else None,
            'dunning_stage': self.dunning_stage.value,
            'grace_period_until': self.grace_period_until.isoformat() if self.grace_period_until else None,
            'last_error': self.last_error,
            'last_error_at': self.last_error_at.isoformat() if self.last_error_at else None,
            'error_count': self.error_count,
            'metadata': self.metadata
        }


class DunningEvent(Base):
    """Dunning event model"""
    
    __tablename__ = 'dunning_events'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    recovery_record_id = Column(UUID(as_uuid=True), ForeignKey('payment_recovery_records.id'), nullable=False)
    
    # Event information
    event_type = Column(String(100), nullable=False)  # email, sms, push, in_app
    dunning_stage = Column(SQLEnum(DunningStage), nullable=False)
    notification_type = Column(String(100), nullable=False)  # immediate, dunning_1, dunning_2, etc.
    
    # Communication details
    subject = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    recipient = Column(String(255), nullable=False)  # email, phone, user_id
    
    # Status and tracking
    status = Column(String(50), default='sent', nullable=False)  # sent, delivered, failed, opened, clicked
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    recovery_record = relationship("PaymentRecoveryRecord", back_populates="dunning_events")
    
    def __repr__(self):
        return f"<DunningEvent(id={self.id}, event_type={self.event_type}, dunning_stage={self.dunning_stage})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'recovery_record_id': str(self.recovery_record_id),
            'event_type': self.event_type,
            'dunning_stage': self.dunning_stage.value,
            'notification_type': self.notification_type,
            'subject': self.subject,
            'content': self.content,
            'recipient': self.recipient,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'metadata': self.metadata
        }


class RecoveryAction(Base):
    """Recovery action model"""
    
    __tablename__ = 'recovery_actions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    recovery_record_id = Column(UUID(as_uuid=True), ForeignKey('payment_recovery_records.id'), nullable=False)
    
    # Action information
    action_type = Column(String(100), nullable=False)  # retry_payment, update_payment_method, grace_period, etc.
    strategy = Column(SQLEnum(RecoveryStrategy), nullable=False)
    dunning_stage = Column(SQLEnum(DunningStage), nullable=True)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status and results
    status = Column(SQLEnum(ActionStatus), default=ActionStatus.SCHEDULED, nullable=False)
    success = Column(Boolean, nullable=True)
    result_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    
    # Relationships
    recovery_record = relationship("PaymentRecoveryRecord", back_populates="recovery_actions")
    
    def __repr__(self):
        return f"<RecoveryAction(id={self.id}, action_type={self.action_type}, strategy={self.strategy})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'recovery_record_id': str(self.recovery_record_id),
            'action_type': self.action_type,
            'strategy': self.strategy.value,
            'dunning_stage': self.dunning_stage.value if self.dunning_stage else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'status': self.status.value,
            'success': self.success,
            'result_message': self.result_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'metadata': self.metadata,
            'result_data': self.result_data
        }


class PaymentFailure(Base):
    """Payment failure historical data model"""
    
    __tablename__ = 'payment_failures'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False)
    
    # Payment information
    invoice_id = Column(String(255), nullable=False)
    payment_intent_id = Column(String(255), nullable=False)
    
    # Failure information
    failure_reason = Column(String(500), nullable=False)
    failure_code = Column(String(100), nullable=False)
    failure_message = Column(Text, nullable=True)
    
    # Amount information
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='usd', nullable=False)
    
    # Status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.FAILED, nullable=False)
    
    # Timestamps
    failed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Recovery tracking
    recovered = Column(Boolean, default=False, nullable=False)
    recovered_at = Column(DateTime(timezone=True), nullable=True)
    recovery_method = Column(String(100), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="payment_failures")
    subscription = relationship("Subscription", back_populates="payment_failures")
    
    def __repr__(self):
        return f"<PaymentFailure(id={self.id}, customer_id={self.customer_id}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'subscription_id': str(self.subscription_id),
            'invoice_id': self.invoice_id,
            'payment_intent_id': self.payment_intent_id,
            'failure_reason': self.failure_reason,
            'failure_code': self.failure_code,
            'failure_message': self.failure_message,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'recovered': self.recovered,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'recovery_method': self.recovery_method,
            'metadata': self.metadata
        }


class RecoveryStrategyConfig(Base):
    """Recovery strategy configuration model"""
    
    __tablename__ = 'recovery_strategy_configs'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Configuration information
    strategy_name = Column(String(100), nullable=False, unique=True)
    strategy_type = Column(SQLEnum(RecoveryStrategy), nullable=False)
    failure_reason_pattern = Column(String(500), nullable=True)  # Regex pattern for matching failure reasons
    failure_code_pattern = Column(String(500), nullable=True)    # Regex pattern for matching failure codes
    
    # Strategy parameters
    max_retry_attempts = Column(Integer, default=5, nullable=False)
    retry_intervals_days = Column(JSON, nullable=True)  # [1, 3, 7, 14, 30]
    grace_period_days = Column(Integer, nullable=True)
    
    # Priority and conditions
    priority = Column(Integer, default=1, nullable=False)
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    customer_tier = Column(String(50), nullable=True)  # basic, premium, enterprise
    
    # Status
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<RecoveryStrategyConfig(id={self.id}, strategy_name={self.strategy_name}, strategy_type={self.strategy_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'strategy_name': self.strategy_name,
            'strategy_type': self.strategy_type.value,
            'failure_reason_pattern': self.failure_reason_pattern,
            'failure_code_pattern': self.failure_code_pattern,
            'max_retry_attempts': self.max_retry_attempts,
            'retry_intervals_days': self.retry_intervals_days,
            'grace_period_days': self.grace_period_days,
            'priority': self.priority,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'customer_tier': self.customer_tier,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }


class DunningSchedule(Base):
    """Dunning schedule configuration model"""
    
    __tablename__ = 'dunning_schedules'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Schedule information
    stage_name = Column(String(100), nullable=False, unique=True)
    dunning_stage = Column(SQLEnum(DunningStage), nullable=False)
    
    # Timing
    delay_days = Column(Integer, nullable=False)
    delay_hours = Column(Integer, default=0, nullable=False)
    
    # Communication
    notification_type = Column(String(100), nullable=False)
    notification_channels = Column(JSON, nullable=True)  # ['email', 'sms', 'push', 'in_app']
    
    # Actions
    retry_attempt = Column(Boolean, default=False, nullable=False)
    payment_method_update = Column(Boolean, default=False, nullable=False)
    grace_period_days = Column(Integer, nullable=True)
    
    # Amount adjustments
    amount_multiplier = Column(Float, default=1.0, nullable=False)  # For partial payments
    amount_fixed = Column(Float, nullable=True)  # Fixed amount override
    
    # Status
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<DunningSchedule(id={self.id}, stage_name={self.stage_name}, dunning_stage={self.dunning_stage})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'stage_name': self.stage_name,
            'dunning_stage': self.dunning_stage.value,
            'delay_days': self.delay_days,
            'delay_hours': self.delay_hours,
            'notification_type': self.notification_type,
            'notification_channels': self.notification_channels,
            'retry_attempt': self.retry_attempt,
            'payment_method_update': self.payment_method_update,
            'grace_period_days': self.grace_period_days,
            'amount_multiplier': self.amount_multiplier,
            'amount_fixed': self.amount_fixed,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        } 