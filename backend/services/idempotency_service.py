"""
Idempotency Service for Webhook Event Processing
===============================================

Comprehensive service for handling idempotency, deduplication, and event ordering
in webhook processing to ensure reliable and consistent event handling.

Features:
- Idempotency key management
- Event deduplication with multiple strategies
- Event ordering and sequencing
- Processing state tracking
- Retry logic with exponential backoff

Author: MINGUS Development Team
Date: January 2025
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, desc, asc

from ..models.webhook_event_tracking import (
    WebhookEventRecord, EventProcessingState, IdempotencyKey, 
    EventDeduplication, EventOrderingQueue
)
from ..models.subscription import AuditLog, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class DeduplicationStrategy(Enum):
    """Deduplication strategies for webhook events"""
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MERGE = "merge"
    IGNORE = "ignore"


class ProcessingStatus(Enum):
    """Processing status for webhook events"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


@dataclass
class IdempotencyResult:
    """Result of idempotency check"""
    is_duplicate: bool
    existing_result: Optional[Dict[str, Any]] = None
    should_process: bool = True
    reason: str = ""


@dataclass
class DeduplicationResult:
    """Result of deduplication check"""
    is_duplicate: bool
    original_event_id: Optional[str] = None
    strategy: DeduplicationStrategy = DeduplicationStrategy.FIRST_WINS
    should_process: bool = True
    reason: str = ""


@dataclass
class OrderingResult:
    """Result of event ordering check"""
    sequence_number: int
    can_process: bool = True
    dependencies_satisfied: bool = True
    reason: str = ""


class IdempotencyService:
    """Comprehensive idempotency and deduplication service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.default_expiration_hours = 24
        self.default_deduplication_window = 3600  # 1 hour in seconds
        
    def generate_idempotency_key(
        self,
        operation_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a unique idempotency key for an operation"""
        try:
            # Create key components
            components = [
                operation_type,
                entity_type or "",
                entity_id or "",
                user_id or "",
                str(int(time.time())),  # Timestamp for uniqueness
                str(uuid.uuid4())  # Random UUID for additional uniqueness
            ]
            
            # Add additional data if provided
            if additional_data:
                components.append(json.dumps(additional_data, sort_keys=True))
            
            # Create key string
            key_string = "|".join(components)
            
            # Generate hash
            key_hash = hashlib.sha256(key_string.encode('utf-8')).hexdigest()
            
            return key_hash
            
        except Exception as e:
            logger.error(f"Error generating idempotency key: {e}")
            # Fallback to UUID-based key
            return str(uuid.uuid4())
    
    def check_idempotency(
        self,
        key_hash: str,
        operation_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> IdempotencyResult:
        """Check if an operation with the given idempotency key has already been processed"""
        try:
            # Look for existing idempotency key
            existing_key = self.db.query(IdempotencyKey).filter(
                and_(
                    IdempotencyKey.key_hash == key_hash,
                    IdempotencyKey.is_expired == False
                )
            ).first()
            
            if not existing_key:
                return IdempotencyResult(
                    is_duplicate=False,
                    should_process=True,
                    reason="No existing idempotency key found"
                )
            
            # Check if operation is already completed
            if existing_key.processing_status == ProcessingStatus.COMPLETED.value:
                return IdempotencyResult(
                    is_duplicate=True,
                    existing_result=existing_key.result_data,
                    should_process=False,
                    reason="Operation already completed successfully"
                )
            
            # Check if operation is currently processing
            if existing_key.processing_status == ProcessingStatus.PROCESSING.value:
                # Check if it's been processing too long (stuck)
                processing_timeout = timedelta(minutes=30)
                if (datetime.now(timezone.utc) - existing_key.last_processing_attempt) > processing_timeout:
                    logger.warning(f"Idempotency key {key_hash} appears to be stuck, allowing reprocessing")
                    return IdempotencyResult(
                        is_duplicate=True,
                        should_process=True,
                        reason="Previous processing appears stuck, allowing reprocessing"
                    )
                else:
                    return IdempotencyResult(
                        is_duplicate=True,
                        should_process=False,
                        reason="Operation currently being processed"
                    )
            
            # Check if operation failed
            if existing_key.processing_status == ProcessingStatus.FAILED.value:
                # Allow retry if within retry limits
                max_retries = 3
                if existing_key.processing_attempts < max_retries:
                    return IdempotencyResult(
                        is_duplicate=True,
                        should_process=True,
                        reason="Previous attempt failed, allowing retry"
                    )
                else:
                    return IdempotencyResult(
                        is_duplicate=True,
                        should_process=False,
                        reason="Maximum retry attempts exceeded"
                    )
            
            return IdempotencyResult(
                is_duplicate=True,
                should_process=False,
                reason="Unknown processing status"
            )
            
        except Exception as e:
            logger.error(f"Error checking idempotency: {e}")
            return IdempotencyResult(
                is_duplicate=False,
                should_process=True,
                reason=f"Error checking idempotency: {str(e)}"
            )
    
    def create_idempotency_key(
        self,
        key_hash: str,
        key_value: str,
        operation_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        expiration_hours: Optional[int] = None
    ) -> IdempotencyKey:
        """Create a new idempotency key record"""
        try:
            expiration_hours = expiration_hours or self.default_expiration_hours
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)
            
            idempotency_key = IdempotencyKey(
                key_hash=key_hash,
                key_value=key_value,
                operation_type=operation_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                processing_status=ProcessingStatus.PROCESSING.value,
                processing_attempts=1,
                last_processing_attempt=datetime.now(timezone.utc),
                expires_at=expires_at
            )
            
            self.db.add(idempotency_key)
            self.db.commit()
            
            logger.info(f"Created idempotency key: {key_hash} for operation: {operation_type}")
            return idempotency_key
            
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"Idempotency key already exists: {key_hash}")
            # Return existing key
            return self.db.query(IdempotencyKey).filter(
                IdempotencyKey.key_hash == key_hash
            ).first()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating idempotency key: {e}")
            raise
    
    def update_idempotency_key_result(
        self,
        key_hash: str,
        success: bool,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update idempotency key with processing result"""
        try:
            idempotency_key = self.db.query(IdempotencyKey).filter(
                IdempotencyKey.key_hash == key_hash
            ).first()
            
            if not idempotency_key:
                logger.warning(f"Idempotency key not found: {key_hash}")
                return
            
            # Update processing status
            if success:
                idempotency_key.processing_status = ProcessingStatus.COMPLETED.value
                idempotency_key.result_data = result_data
                idempotency_key.error_message = None
            else:
                idempotency_key.processing_status = ProcessingStatus.FAILED.value
                idempotency_key.error_message = error_message
                idempotency_key.processing_attempts += 1
            
            idempotency_key.last_processing_attempt = datetime.now(timezone.utc)
            idempotency_key.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"Updated idempotency key {key_hash} with result: {'success' if success else 'failed'}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating idempotency key result: {e}")
            raise
    
    def generate_deduplication_hash(
        self,
        event_type: str,
        entity_type: Optional[str],
        entity_id: Optional[str],
        event_data: Dict[str, Any]
    ) -> str:
        """Generate a deduplication hash for an event"""
        try:
            # Create hash components
            components = [
                event_type,
                entity_type or "",
                entity_id or "",
                # Include key fields from event data for deduplication
                str(event_data.get('id', '')),
                str(event_data.get('created', '')),
                # Hash the entire event data for additional uniqueness
                hashlib.sha256(json.dumps(event_data, sort_keys=True).encode('utf-8')).hexdigest()[:16]
            ]
            
            # Create hash string
            hash_string = "|".join(components)
            
            # Generate final hash
            deduplication_hash = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
            
            return deduplication_hash
            
        except Exception as e:
            logger.error(f"Error generating deduplication hash: {e}")
            # Fallback to simple hash
            return hashlib.sha256(f"{event_type}:{entity_id}:{time.time()}".encode('utf-8')).hexdigest()
    
    def check_deduplication(
        self,
        deduplication_hash: str,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        strategy: DeduplicationStrategy = DeduplicationStrategy.FIRST_WINS
    ) -> DeduplicationResult:
        """Check if an event is a duplicate based on deduplication hash"""
        try:
            # Look for existing deduplication record
            existing_record = self.db.query(EventDeduplication).filter(
                EventDeduplication.deduplication_hash == deduplication_hash
            ).first()
            
            if not existing_record:
                return DeduplicationResult(
                    is_duplicate=False,
                    should_process=True,
                    reason="No existing deduplication record found"
                )
            
            # Check if within time window
            time_window = timedelta(seconds=existing_record.time_window_seconds)
            if (datetime.now(timezone.utc) - existing_record.last_seen_at) > time_window:
                # Outside time window, treat as new event
                return DeduplicationResult(
                    is_duplicate=False,
                    should_process=True,
                    reason="Outside deduplication time window"
                )
            
            # Update occurrence count and last seen time
            existing_record.occurrence_count += 1
            existing_record.last_seen_at = datetime.now(timezone.utc)
            existing_record.updated_at = datetime.now(timezone.utc)
            
            # Apply deduplication strategy
            if strategy == DeduplicationStrategy.FIRST_WINS:
                return DeduplicationResult(
                    is_duplicate=True,
                    original_event_id=str(existing_record.processed_event_id),
                    strategy=strategy,
                    should_process=False,
                    reason="First wins strategy - original event already processed"
                )
            elif strategy == DeduplicationStrategy.LAST_WINS:
                return DeduplicationResult(
                    is_duplicate=True,
                    original_event_id=str(existing_record.processed_event_id),
                    strategy=strategy,
                    should_process=True,
                    reason="Last wins strategy - processing new event"
                )
            elif strategy == DeduplicationStrategy.MERGE:
                return DeduplicationResult(
                    is_duplicate=True,
                    original_event_id=str(existing_record.processed_event_id),
                    strategy=strategy,
                    should_process=True,
                    reason="Merge strategy - processing for merging"
                )
            else:  # IGNORE
                return DeduplicationResult(
                    is_duplicate=True,
                    original_event_id=str(existing_record.processed_event_id),
                    strategy=strategy,
                    should_process=False,
                    reason="Ignore strategy - skipping duplicate event"
                )
            
        except Exception as e:
            logger.error(f"Error checking deduplication: {e}")
            return DeduplicationResult(
                is_duplicate=False,
                should_process=True,
                reason=f"Error checking deduplication: {str(e)}"
            )
    
    def create_deduplication_record(
        self,
        deduplication_hash: str,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        strategy: DeduplicationStrategy = DeduplicationStrategy.FIRST_WINS,
        time_window_seconds: Optional[int] = None
    ) -> EventDeduplication:
        """Create a new deduplication record"""
        try:
            time_window_seconds = time_window_seconds or self.default_deduplication_window
            
            deduplication_record = EventDeduplication(
                deduplication_hash=deduplication_hash,
                event_signature=deduplication_hash[:32],  # Use first 32 chars as signature
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                deduplication_strategy=strategy.value,
                time_window_seconds=time_window_seconds
            )
            
            self.db.add(deduplication_record)
            self.db.commit()
            
            logger.info(f"Created deduplication record: {deduplication_hash} for event: {event_type}")
            return deduplication_record
            
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"Deduplication record already exists: {deduplication_hash}")
            # Return existing record
            return self.db.query(EventDeduplication).filter(
                EventDeduplication.deduplication_hash == deduplication_hash
            ).first()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating deduplication record: {e}")
            raise
    
    def get_next_sequence_number(
        self,
        entity_type: str,
        entity_id: str,
        event_type: str
    ) -> int:
        """Get the next sequence number for an entity and event type"""
        try:
            # Get current processing state
            processing_state = self.db.query(EventProcessingState).filter(
                and_(
                    EventProcessingState.entity_type == entity_type,
                    EventProcessingState.entity_id == entity_id,
                    EventProcessingState.event_type == event_type
                )
            ).first()
            
            if processing_state:
                next_sequence = processing_state.current_sequence_number + 1
                processing_state.current_sequence_number = next_sequence
                processing_state.updated_at = datetime.now(timezone.utc)
            else:
                # Create new processing state
                next_sequence = 1
                processing_state = EventProcessingState(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    event_type=event_type,
                    current_sequence_number=next_sequence
                )
                self.db.add(processing_state)
            
            self.db.commit()
            return next_sequence
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error getting next sequence number: {e}")
            # Fallback to timestamp-based sequence
            return int(time.time())
    
    def check_event_ordering(
        self,
        entity_type: str,
        entity_id: str,
        event_type: str,
        sequence_number: int
    ) -> OrderingResult:
        """Check if an event can be processed based on ordering requirements"""
        try:
            # Get processing state
            processing_state = self.db.query(EventProcessingState).filter(
                and_(
                    EventProcessingState.entity_type == entity_type,
                    EventProcessingState.entity_id == entity_id,
                    EventProcessingState.event_type == event_type
                )
            ).first()
            
            if not processing_state:
                return OrderingResult(
                    sequence_number=sequence_number,
                    can_process=True,
                    dependencies_satisfied=True,
                    reason="No existing processing state, allowing processing"
                )
            
            # Check if this is the expected next sequence
            expected_sequence = processing_state.last_processed_sequence + 1 if processing_state.last_processed_sequence else 1
            
            if sequence_number == expected_sequence:
                return OrderingResult(
                    sequence_number=sequence_number,
                    can_process=True,
                    dependencies_satisfied=True,
                    reason="Expected sequence number, allowing processing"
                )
            elif sequence_number < expected_sequence:
                return OrderingResult(
                    sequence_number=sequence_number,
                    can_process=False,
                    dependencies_satisfied=False,
                    reason=f"Sequence number {sequence_number} is less than expected {expected_sequence}"
                )
            else:
                # Future sequence number - check if we should wait
                return OrderingResult(
                    sequence_number=sequence_number,
                    can_process=False,
                    dependencies_satisfied=False,
                    reason=f"Sequence number {sequence_number} is greater than expected {expected_sequence}, waiting for dependencies"
                )
            
        except Exception as e:
            logger.error(f"Error checking event ordering: {e}")
            return OrderingResult(
                sequence_number=sequence_number,
                can_process=True,
                dependencies_satisfied=True,
                reason=f"Error checking ordering: {str(e)}"
            )
    
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
        try:
            processing_state = self.db.query(EventProcessingState).filter(
                and_(
                    EventProcessingState.entity_type == entity_type,
                    EventProcessingState.entity_id == entity_id,
                    EventProcessingState.event_type == event_type
                )
            ).first()
            
            if not processing_state:
                logger.warning(f"Processing state not found for {entity_type}:{entity_id}:{event_type}")
                return
            
            if success:
                processing_state.last_processed_event_id = event_id
                processing_state.last_processed_sequence = sequence_number
                processing_state.last_processed_at = datetime.now(timezone.utc)
                processing_state.consecutive_failures = 0
                processing_state.last_failure_reason = None
            else:
                processing_state.consecutive_failures += 1
                processing_state.last_failure_at = datetime.now(timezone.utc)
                processing_state.last_failure_reason = error_message
            
            processing_state.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Updated processing state for {entity_type}:{entity_id}:{event_type} - sequence {sequence_number}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating processing state: {e}")
            raise
    
    def cleanup_expired_records(self) -> Dict[str, int]:
        """Clean up expired idempotency keys and old deduplication records"""
        try:
            cleanup_stats = {
                'expired_idempotency_keys': 0,
                'expired_deduplication_records': 0,
                'old_webhook_records': 0
            }
            
            # Clean up expired idempotency keys
            expired_keys = self.db.query(IdempotencyKey).filter(
                IdempotencyKey.expires_at < datetime.now(timezone.utc)
            ).all()
            
            for key in expired_keys:
                key.is_expired = True
                cleanup_stats['expired_idempotency_keys'] += 1
            
            # Clean up old deduplication records (older than 7 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            old_dedup_records = self.db.query(EventDeduplication).filter(
                EventDeduplication.last_seen_at < cutoff_date
            ).all()
            
            for record in old_dedup_records:
                self.db.delete(record)
                cleanup_stats['expired_deduplication_records'] += 1
            
            # Clean up old webhook records (older than 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            old_webhook_records = self.db.query(WebhookEventRecord).filter(
                WebhookEventRecord.created_at < cutoff_date
            ).all()
            
            for record in old_webhook_records:
                self.db.delete(record)
                cleanup_stats['old_webhook_records'] += 1
            
            self.db.commit()
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during cleanup: {e}")
            return {'error': str(e)}
    
    def get_processing_metrics(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Get processing metrics for monitoring and analytics"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            
            # Base query for webhook records
            query = self.db.query(WebhookEventRecord).filter(
                WebhookEventRecord.created_at >= cutoff_time
            )
            
            if entity_type:
                query = query.filter(WebhookEventRecord.event_metadata.contains({'entity_type': entity_type}))
            if entity_id:
                query = query.filter(WebhookEventRecord.event_metadata.contains({'entity_id': entity_id}))
            
            records = query.all()
            
            # Calculate metrics
            total_events = len(records)
            completed_events = len([r for r in records if r.processing_status == ProcessingStatus.COMPLETED.value])
            failed_events = len([r for r in records if r.processing_status == ProcessingStatus.FAILED.value])
            duplicate_events = len([r for r in records if r.is_duplicate])
            
            # Calculate processing times
            processing_times = []
            for record in records:
                if record.processing_started_at and record.processing_completed_at:
                    processing_time = (record.processing_completed_at - record.processing_started_at).total_seconds()
                    processing_times.append(processing_time)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Event type distribution
            event_type_counts = {}
            for record in records:
                event_type_counts[record.event_type] = event_type_counts.get(record.event_type, 0) + 1
            
            metrics = {
                'total_events': total_events,
                'completed_events': completed_events,
                'failed_events': failed_events,
                'duplicate_events': duplicate_events,
                'success_rate': (completed_events / total_events * 100) if total_events > 0 else 0,
                'duplicate_rate': (duplicate_events / total_events * 100) if total_events > 0 else 0,
                'avg_processing_time_seconds': avg_processing_time,
                'event_type_distribution': event_type_counts,
                'time_range_hours': time_range_hours
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting processing metrics: {e}")
            return {'error': str(e)} 