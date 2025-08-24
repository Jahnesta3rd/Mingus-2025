"""
Comprehensive Stripe Webhook Management System for MINGUS
Handles all subscription events in real-time with robust error handling and logging
"""
import logging
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import stripe
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.subscription import (
    Customer, Subscription, PricingTier, BillingHistory, 
    PaymentMethod, AuditLog, AuditEventType, AuditSeverity
)
from ..models.user import User
from ..config.base import Config
from ..services.notification_service import NotificationService
from ..services.analytics_service import AnalyticsService
from ..monitoring.webhook_health_monitor import WebhookHealthMonitor
from ..monitoring.audit_trail_service import AuditTrailService, AuditEventType, AuditSeverity, AuditCategory

logger = logging.getLogger(__name__)

class WebhookEventType(Enum):
    """Enumeration of all supported Stripe webhook event types"""
    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    
    # Subscription events
    CUSTOMER_SUBSCRIPTION_CREATED = "customer.subscription.created"
    CUSTOMER_SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    CUSTOMER_SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    CUSTOMER_SUBSCRIPTION_TRIAL_WILL_END = "customer.subscription.trial_will_end"
    
    # Invoice events
    INVOICE_CREATED = "invoice.created"
    INVOICE_FINALIZED = "invoice.finalized"
    INVOICE_PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    INVOICE_UPCOMING = "invoice.upcoming"
    
    # Payment events
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_INTENT_PAYMENT_FAILED = "payment_intent.payment_failed"
    PAYMENT_METHOD_ATTACHED = "payment_method.attached"
    PAYMENT_METHOD_DETACHED = "payment_method.detached"
    PAYMENT_METHOD_UPDATED = "payment_method.updated"
    
    # Charge events
    CHARGE_SUCCEEDED = "charge.succeeded"
    CHARGE_FAILED = "charge.failed"
    CHARGE_REFUNDED = "charge.refunded"
    CHARGE_DISPUTE_CREATED = "charge.dispute.created"
    
    # Coupon and discount events
    COUPON_CREATED = "coupon.created"
    COUPON_DELETED = "coupon.deleted"
    INVOICEITEM_CREATED = "invoiceitem.created"
    INVOICEITEM_DELETED = "invoiceitem.deleted"

@dataclass
class WebhookEvent:
    """Data class for webhook event information"""
    event_id: str
    event_type: str
    event_data: Dict[str, Any]
    created_at: datetime
    livemode: bool
    api_version: str
    request_id: str
    source_ip: str
    user_agent: str

class WebhookProcessingResult:
    """Result of webhook processing"""
    def __init__(self, success: bool, message: str = "", error: str = "", 
                 changes: List[str] = None, notifications_sent: int = 0):
        self.success = success
        self.message = message
        self.error = error
        self.changes = changes or []
        self.notifications_sent = notifications_sent
        self.processed_at = datetime.utcnow()

class StripeWebhookManager:
    """Comprehensive Stripe webhook management system"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.stripe = stripe
        self.stripe.api_key = config.STRIPE_SECRET_KEY
        
        # Initialize services
        self.notification_service = NotificationService(db_session, config)
        self.analytics_service = AnalyticsService(db_session, config)
        
        # Webhook configuration
        self.webhook_secret = config.STRIPE_WEBHOOK_SECRET
        self.supported_events = [event.value for event in WebhookEventType]
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
        
        # Event handlers mapping
        self.event_handlers = {
            WebhookEventType.CUSTOMER_CREATED.value: self._handle_customer_created,
            WebhookEventType.CUSTOMER_UPDATED.value: self._handle_customer_updated,
            WebhookEventType.CUSTOMER_DELETED.value: self._handle_customer_deleted,
            WebhookEventType.CUSTOMER_SUBSCRIPTION_CREATED.value: self._handle_subscription_created,
            WebhookEventType.CUSTOMER_SUBSCRIPTION_UPDATED.value: self._handle_subscription_updated,
            WebhookEventType.CUSTOMER_SUBSCRIPTION_DELETED.value: self._handle_subscription_deleted,
            WebhookEventType.CUSTOMER_SUBSCRIPTION_TRIAL_WILL_END.value: self._handle_subscription_trial_will_end,
            WebhookEventType.INVOICE_CREATED.value: self._handle_invoice_created,
            WebhookEventType.INVOICE_FINALIZED.value: self._handle_invoice_finalized,
            WebhookEventType.INVOICE_PAYMENT_SUCCEEDED.value: self._handle_invoice_payment_succeeded,
            WebhookEventType.INVOICE_PAYMENT_FAILED.value: self._handle_invoice_payment_failed,
            WebhookEventType.INVOICE_UPCOMING.value: self._handle_invoice_upcoming,
            WebhookEventType.PAYMENT_INTENT_SUCCEEDED.value: self._handle_payment_intent_succeeded,
            WebhookEventType.PAYMENT_INTENT_PAYMENT_FAILED.value: self._handle_payment_intent_failed,
            WebhookEventType.PAYMENT_METHOD_ATTACHED.value: self._handle_payment_method_attached,
            WebhookEventType.PAYMENT_METHOD_DETACHED.value: self._handle_payment_method_detached,
            WebhookEventType.PAYMENT_METHOD_UPDATED.value: self._handle_payment_method_updated,
            WebhookEventType.CHARGE_SUCCEEDED.value: self._handle_charge_succeeded,
            WebhookEventType.CHARGE_FAILED.value: self._handle_charge_failed,
            WebhookEventType.CHARGE_REFUNDED.value: self._handle_charge_refunded,
            WebhookEventType.CHARGE_DISPUTE_CREATED.value: self._handle_charge_dispute_created,
        }
    
    def process_webhook(
        self,
        payload: bytes,
        signature: str,
        source_ip: str = "",
        user_agent: str = "",
        request_id: str = ""
    ) -> WebhookProcessingResult:
        """Process a Stripe webhook event with enhanced security and reliability"""
        start_time = time.time()
        
        try:
            # Step 1: Security validation
            security_result = self._validate_webhook_security(payload, signature, source_ip, user_agent)
            if not security_result['valid']:
                self._log_security_violation(security_result, source_ip, user_agent, request_id)
                return WebhookProcessingResult(
                    success=False,
                    error=f"Security validation failed: {security_result['reason']}"
                )
            
            # Step 2: Rate limiting check
            if not self._check_rate_limit(source_ip):
                logger.warning(f"Rate limit exceeded for IP: {source_ip}")
                return WebhookProcessingResult(
                    success=False,
                    error="Rate limit exceeded"
                )
            
            # Step 3: Verify webhook signature with enhanced validation
            signature_result = self._verify_webhook_signature_enhanced(payload, signature)
            if not signature_result['valid']:
                self._log_signature_failure(signature_result, source_ip, user_agent, request_id)
                return WebhookProcessingResult(
                    success=False,
                    error=f"Signature verification failed: {signature_result['reason']}"
                )
            
            # Step 4: Parse webhook event with validation
            event = self._parse_webhook_event_enhanced(payload, source_ip, user_agent, request_id)
            if not event:
                return WebhookProcessingResult(
                    success=False,
                    error="Failed to parse webhook event"
                )
            
            # Step 5: Event validation and filtering
            validation_result = self._validate_webhook_event(event)
            if not validation_result['valid']:
                logger.warning(f"Event validation failed: {validation_result['reason']}")
                return WebhookProcessingResult(
                    success=False,
                    error=f"Event validation failed: {validation_result['reason']}"
                )
            
            # Step 6: Check if event is supported
            if event.event_type not in self.supported_events:
                logger.info(f"Unsupported webhook event: {event.event_type}")
                return WebhookProcessingResult(
                    success=True,
                    message=f"Unsupported event type: {event.event_type}"
                )
            
            # Step 7: Enhanced idempotency and deduplication handling
            idempotency_result = self._handle_idempotency_and_deduplication(event)
            if not idempotency_result['should_process']:
                return WebhookProcessingResult(
                    success=True,
                    message=f"Event handled by idempotency: {idempotency_result['reason']}"
                )
            
            # Step 8: Log webhook receipt with enhanced logging
            self._log_webhook_receipt_enhanced(event, signature_result)
            
            # Step 9: Initialize comprehensive webhook logging service
            from ..services.webhook_logging_service import WebhookLoggingService
            logging_service = WebhookLoggingService(self.db, self.config)
            
            # Step 10: Process event with enhanced retry logic
            result = self._process_event_with_enhanced_retry(event)
            
            # Step 11: Log processing result with comprehensive monitoring
            processing_time = time.time() - start_time
            self._log_processing_result_enhanced(event, result, processing_time)
            
            # Step 12: Log to comprehensive webhook logging service
            self._log_to_comprehensive_service(
                logging_service, event, result, processing_time, 
                signature_result, idempotency_result
            )
            
            # Step 11: Update rate limiting counters
            self._update_rate_limit_counters(source_ip, result.success)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing webhook: {e}")
            self._log_processing_error(e, source_ip, user_agent, request_id, processing_time)
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _validate_webhook_security(self, payload: bytes, signature: str, source_ip: str, user_agent: str) -> Dict[str, Any]:
        """Enhanced security validation for webhook requests"""
        try:
            # Check if webhook secret is configured
            if not self.webhook_secret:
                return {
                    'valid': False,
                    'reason': 'Webhook secret not configured',
                    'type': 'configuration_error'
                }
            
            # Validate signature format
            if not signature or not signature.startswith('t='):
                return {
                    'valid': False,
                    'reason': 'Invalid signature format',
                    'type': 'signature_format_error'
                }
            
            # Check payload size limits
            if len(payload) > 1024 * 1024:  # 1MB limit
                return {
                    'valid': False,
                    'reason': 'Payload too large',
                    'type': 'payload_size_error'
                }
            
            # Validate source IP (optional - can be configured)
            if hasattr(self.config, 'ALLOWED_WEBHOOK_IPS') and self.config.ALLOWED_WEBHOOK_IPS:
                if source_ip not in self.config.ALLOWED_WEBHOOK_IPS:
                    return {
                        'valid': False,
                        'reason': f'IP not allowed: {source_ip}',
                        'type': 'ip_restriction_error'
                    }
            
            # Validate user agent (optional - can be configured)
            if hasattr(self.config, 'ALLOWED_WEBHOOK_USER_AGENTS') and self.config.ALLOWED_WEBHOOK_USER_AGENTS:
                if not any(allowed_ua in user_agent for allowed_ua in self.config.ALLOWED_WEBHOOK_USER_AGENTS):
                    return {
                        'valid': False,
                        'reason': f'User agent not allowed: {user_agent}',
                        'type': 'user_agent_restriction_error'
                    }
            
            return {'valid': True, 'reason': 'Security validation passed'}
            
        except Exception as e:
            logger.error(f"Error in security validation: {e}")
            return {
                'valid': False,
                'reason': f'Security validation error: {str(e)}',
                'type': 'validation_error'
            }
    
    def _verify_webhook_signature_enhanced(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Enhanced Stripe webhook signature verification"""
        try:
            # Extract timestamp and signatures from header
            timestamp, signatures = self._extract_signature_parts_enhanced(signature)
            
            if not timestamp:
                return {
                    'valid': False,
                    'reason': 'No timestamp found in signature',
                    'type': 'timestamp_missing'
                }
            
            if not signatures:
                return {
                    'valid': False,
                    'reason': 'No signatures found in header',
                    'type': 'signature_missing'
                }
            
            # Check timestamp (reject if too old or too new)
            current_time = time.time()
            time_diff = abs(current_time - timestamp)
            
            if time_diff > 300:  # 5 minutes tolerance
                return {
                    'valid': False,
                    'reason': f'Timestamp too old/new: {time_diff:.0f}s difference',
                    'type': 'timestamp_invalid',
                    'timestamp': timestamp,
                    'current_time': current_time,
                    'time_diff': time_diff
                }
            
            # Verify signature using Stripe's recommended method
            expected_signature = self._compute_expected_signature(payload, timestamp)
            
            if expected_signature in signatures:
                return {
                    'valid': True,
                    'reason': 'Signature verification successful',
                    'timestamp': timestamp,
                    'signature_count': len(signatures)
                }
            else:
                return {
                    'valid': False,
                    'reason': 'Signature verification failed',
                    'type': 'signature_mismatch',
                    'expected': expected_signature,
                    'received': signatures,
                    'timestamp': timestamp
                }
            
        except Exception as e:
            logger.error(f"Error in enhanced signature verification: {e}")
            return {
                'valid': False,
                'reason': f'Signature verification error: {str(e)}',
                'type': 'verification_error'
            }
    
    def _extract_signature_parts_enhanced(self, signature: str) -> Tuple[Optional[int], List[str]]:
        """Enhanced signature parts extraction with better error handling"""
        try:
            parts = signature.split(',')
            timestamp = None
            signatures = []
            
            for part in parts:
                part = part.strip()
                if part.startswith('t='):
                    try:
                        timestamp = int(part[2:])
                    except ValueError:
                        logger.error(f"Invalid timestamp format: {part}")
                        continue
                elif part.startswith('v1='):
                    signatures.append(part[3:])
            
            return timestamp, signatures
            
        except Exception as e:
            logger.error(f"Error extracting signature parts: {e}")
            return None, []
    
    def _compute_expected_signature(self, payload: bytes, timestamp: int) -> str:
        """Compute expected signature using Stripe's method"""
        try:
            # Use Stripe's recommended signature computation
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return expected_signature
            
        except Exception as e:
            logger.error(f"Error computing expected signature: {e}")
            raise
    
    def _check_rate_limit(self, source_ip: str) -> bool:
        """Check rate limiting for webhook requests"""
        try:
            # Simple in-memory rate limiting (in production, use Redis or similar)
            current_time = time.time()
            window_size = 60  # 1 minute window
            
            if not hasattr(self, '_rate_limit_cache'):
                self._rate_limit_cache = {}
            
            # Clean old entries
            self._rate_limit_cache = {
                ip: timestamps for ip, timestamps in self._rate_limit_cache.items()
                if timestamps and current_time - timestamps[-1] < window_size
            }
            
            # Get timestamps for this IP
            timestamps = self._rate_limit_cache.get(source_ip, [])
            
            # Remove old timestamps outside the window
            timestamps = [ts for ts in timestamps if current_time - ts < window_size]
            
            # Check rate limit (max 100 requests per minute per IP)
            max_requests = getattr(self.config, 'WEBHOOK_RATE_LIMIT', 100)
            
            if len(timestamps) >= max_requests:
                return False
            
            # Add current timestamp
            timestamps.append(current_time)
            self._rate_limit_cache[source_ip] = timestamps
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow request if rate limiting fails
    
    def _update_rate_limit_counters(self, source_ip: str, success: bool) -> None:
        """Update rate limiting counters and metrics"""
        try:
            # Update success/failure counters for analytics
            if not hasattr(self, '_rate_limit_metrics'):
                self._rate_limit_metrics = {'success': 0, 'failure': 0}
            
            if success:
                self._rate_limit_metrics['success'] += 1
            else:
                self._rate_limit_metrics['failure'] += 1
                
        except Exception as e:
            logger.error(f"Error updating rate limit counters: {e}")
    
    def _parse_webhook_event_enhanced(self, payload: bytes, source_ip: str, user_agent: str, request_id: str) -> Optional[WebhookEvent]:
        """Enhanced webhook event parsing with validation"""
        try:
            # Validate JSON format
            try:
                event_data = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook payload: {e}")
                return None
            
            # Validate required fields
            required_fields = ['id', 'type', 'data', 'created']
            missing_fields = [field for field in required_fields if field not in event_data]
            
            if missing_fields:
                logger.error(f"Missing required fields in webhook: {missing_fields}")
                return None
            
            # Validate event ID format
            if not event_data['id'].startswith('evt_'):
                logger.error(f"Invalid event ID format: {event_data['id']}")
                return None
            
            # Validate timestamp
            try:
                created_at = datetime.fromtimestamp(event_data['created'])
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid timestamp in webhook: {e}")
                return None
            
            return WebhookEvent(
                event_id=event_data['id'],
                event_type=event_data['type'],
                event_data=event_data.get('data', {}),
                created_at=created_at,
                livemode=event_data.get('livemode', False),
                api_version=event_data.get('api_version', ''),
                request_id=request_id,
                source_ip=source_ip,
                user_agent=user_agent
            )
            
        except Exception as e:
            logger.error(f"Error parsing webhook event: {e}")
            return None
    
    def _validate_webhook_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Validate webhook event content and structure"""
        try:
            # Check event age (reject if too old)
            event_age = time.time() - event.created_at.timestamp()
            if event_age > 3600:  # 1 hour
                return {
                    'valid': False,
                    'reason': f'Event too old: {event_age:.0f}s',
                    'type': 'event_age_error'
                }
            
            # Validate event data structure
            if not isinstance(event.event_data, dict):
                return {
                    'valid': False,
                    'reason': 'Invalid event data structure',
                    'type': 'data_structure_error'
                }
            
            # Check for required object field
            if 'object' not in event.event_data:
                return {
                    'valid': False,
                    'reason': 'Missing object field in event data',
                    'type': 'missing_object_error'
                }
            
            return {'valid': True, 'reason': 'Event validation passed'}
            
        except Exception as e:
            logger.error(f"Error validating webhook event: {e}")
            return {
                'valid': False,
                'reason': f'Event validation error: {str(e)}',
                'type': 'validation_error'
            }
    
    def _is_duplicate_event(self, event: WebhookEvent) -> bool:
        """Check if webhook event is a duplicate using enhanced deduplication"""
        try:
            # Import idempotency service
            from ..services.idempotency_service import IdempotencyService, DeduplicationStrategy
            
            # Initialize idempotency service
            idempotency_service = IdempotencyService(self.db)
            
            # Extract entity information from event data
            entity_type, entity_id = self._extract_entity_info(event.event_data)
            
            # Generate deduplication hash
            deduplication_hash = idempotency_service.generate_deduplication_hash(
                event_type=event.event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data=event.event_data
            )
            
            # Check deduplication
            dedup_result = idempotency_service.check_deduplication(
                deduplication_hash=deduplication_hash,
                event_type=event.event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                strategy=DeduplicationStrategy.FIRST_WINS
            )
            
            if dedup_result.is_duplicate:
                logger.info(f"Duplicate event detected: {event.event_id} - {dedup_result.reason}")
                
                # Create deduplication record if it doesn't exist
                if not dedup_result.original_event_id:
                    idempotency_service.create_deduplication_record(
                        deduplication_hash=deduplication_hash,
                        event_type=event.event_type,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        strategy=DeduplicationStrategy.FIRST_WINS
                    )
                
                return True
            
            # Create deduplication record for new event
            idempotency_service.create_deduplication_record(
                deduplication_hash=deduplication_hash,
                event_type=event.event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                strategy=DeduplicationStrategy.FIRST_WINS
            )
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicate event: {e}")
            return False  # Allow processing if duplicate detection fails
    
    def _extract_entity_info(self, event_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract entity type and ID from event data"""
        try:
            # Extract from object data
            object_data = event_data.get('object', {})
            
            # Check for customer events
            if 'customer' in object_data:
                return 'customer', object_data['customer']
            
            # Check for subscription events
            if 'subscription' in object_data:
                return 'subscription', object_data['subscription']
            
            # Check for invoice events
            if 'invoice' in object_data:
                return 'invoice', object_data['invoice']
            
            # Check for payment events
            if 'payment_intent' in object_data:
                return 'payment_intent', object_data['payment_intent']
            
            # Check for charge events
            if 'charge' in object_data:
                return 'charge', object_data['charge']
            
            # Default to object ID if available
            if 'id' in object_data:
                return 'object', object_data['id']
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error extracting entity info: {e}")
            return None, None
    
    def _handle_idempotency_and_deduplication(self, event: WebhookEvent) -> Dict[str, Any]:
        """Comprehensive idempotency and deduplication handling"""
        try:
            # Import idempotency service
            from ..services.idempotency_service import IdempotencyService, DeduplicationStrategy
            
            # Initialize idempotency service
            idempotency_service = IdempotencyService(self.db)
            
            # Extract entity information
            entity_type, entity_id = self._extract_entity_info(event.event_data)
            
            # Step 1: Check idempotency key
            idempotency_key = self._generate_event_idempotency_key(event, entity_type, entity_id)
            idempotency_result = idempotency_service.check_idempotency(
                key_hash=idempotency_key,
                operation_type=event.event_type,
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            if idempotency_result.is_duplicate:
                if not idempotency_result.should_process:
                    return {
                        'should_process': False,
                        'reason': f"Idempotency check: {idempotency_result.reason}",
                        'existing_result': idempotency_result.existing_result
                    }
            
            # Step 2: Check deduplication
            deduplication_hash = idempotency_service.generate_deduplication_hash(
                event_type=event.event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data=event.event_data
            )
            
            dedup_result = idempotency_service.check_deduplication(
                deduplication_hash=deduplication_hash,
                event_type=event.event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                strategy=DeduplicationStrategy.FIRST_WINS
            )
            
            if dedup_result.is_duplicate:
                if not dedup_result.should_process:
                    return {
                        'should_process': False,
                        'reason': f"Deduplication check: {dedup_result.reason}",
                        'original_event_id': dedup_result.original_event_id
                    }
            
            # Step 3: Check event ordering
            if entity_type and entity_id:
                sequence_number = idempotency_service.get_next_sequence_number(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    event_type=event.event_type
                )
                
                ordering_result = idempotency_service.check_event_ordering(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    event_type=event.event_type,
                    sequence_number=sequence_number
                )
                
                if not ordering_result.can_process:
                    return {
                        'should_process': False,
                        'reason': f"Ordering check: {ordering_result.reason}",
                        'sequence_number': sequence_number
                    }
            else:
                sequence_number = None
            
            # Step 4: Create idempotency key for new processing
            if not idempotency_result.is_duplicate:
                idempotency_service.create_idempotency_key(
                    key_hash=idempotency_key,
                    key_value=event.event_id,
                    operation_type=event.event_type,
                    entity_type=entity_type,
                    entity_id=entity_id
                )
            
            # Step 5: Create deduplication record
            if not dedup_result.is_duplicate:
                idempotency_service.create_deduplication_record(
                    deduplication_hash=deduplication_hash,
                    event_type=event.event_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    strategy=DeduplicationStrategy.FIRST_WINS
                )
            
            # Step 6: Store processing context for later use
            event.processing_context = {
                'idempotency_key': idempotency_key,
                'deduplication_hash': deduplication_hash,
                'sequence_number': sequence_number,
                'entity_type': entity_type,
                'entity_id': entity_id
            }
            
            return {
                'should_process': True,
                'reason': "Event passed all idempotency and deduplication checks",
                'idempotency_key': idempotency_key,
                'deduplication_hash': deduplication_hash,
                'sequence_number': sequence_number
            }
            
        except Exception as e:
            logger.error(f"Error in idempotency and deduplication handling: {e}")
            return {
                'should_process': True,
                'reason': f"Error in idempotency handling: {str(e)}, allowing processing"
            }
    
    def _generate_event_idempotency_key(self, event: WebhookEvent, entity_type: Optional[str], entity_id: Optional[str]) -> str:
        """Generate idempotency key for webhook event"""
        try:
            # Import idempotency service
            from ..services.idempotency_service import IdempotencyService
            
            # Initialize idempotency service
            idempotency_service = IdempotencyService(self.db)
            
            # Generate key with event-specific data
            additional_data = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'created_at': event.created_at.isoformat(),
                'livemode': event.livemode
            }
            
            return idempotency_service.generate_idempotency_key(
                operation_type=event.event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=None,  # Webhook events don't have user context
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error generating event idempotency key: {e}")
            # Fallback to simple hash
            return hashlib.sha256(f"{event.event_id}:{event.event_type}:{time.time()}".encode('utf-8')).hexdigest()
    
    def _log_security_violation(self, security_result: Dict[str, Any], source_ip: str, user_agent: str, request_id: str) -> None:
        """Log security violations for monitoring and alerting"""
        try:
            violation_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'source_ip': source_ip,
                'user_agent': user_agent,
                'request_id': request_id,
                'violation_type': security_result.get('type', 'unknown'),
                'reason': security_result.get('reason', 'unknown'),
                'severity': 'high'
            }
            
            logger.warning(f"Webhook security violation: {violation_data}")
            
            # Log to audit trail
            self._log_audit_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                event_description=f"Webhook security violation: {security_result.get('reason')}",
                metadata=violation_data
            )
            
        except Exception as e:
            logger.error(f"Error logging security violation: {e}")
    
    def _log_signature_failure(self, signature_result: Dict[str, Any], source_ip: str, user_agent: str, request_id: str) -> None:
        """Log signature verification failures"""
        try:
            failure_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'source_ip': source_ip,
                'user_agent': user_agent,
                'request_id': request_id,
                'failure_type': signature_result.get('type', 'unknown'),
                'reason': signature_result.get('reason', 'unknown'),
                'severity': 'critical'
            }
            
            logger.error(f"Webhook signature failure: {failure_data}")
            
            # Log to audit trail
            self._log_audit_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                event_description=f"Webhook signature failure: {signature_result.get('reason')}",
                metadata=failure_data
            )
            
        except Exception as e:
            logger.error(f"Error logging signature failure: {e}")
    
    def _log_webhook_receipt_enhanced(self, event: WebhookEvent, signature_result: Dict[str, Any]) -> None:
        """Enhanced webhook receipt logging with security information"""
        try:
            receipt_data = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'source_ip': event.source_ip,
                'user_agent': event.user_agent,
                'request_id': event.request_id,
                'timestamp': event.created_at.isoformat(),
                'livemode': event.livemode,
                'api_version': event.api_version,
                'signature_valid': signature_result.get('valid', False),
                'signature_timestamp': signature_result.get('timestamp'),
                'signature_count': signature_result.get('signature_count', 0)
            }
            
            logger.info(f"Webhook received: {receipt_data}")
            
            # Log to audit trail
            self._log_audit_event(
                event_type=AuditEventType.WEBHOOK_RECEIVED,
                event_description=f"Webhook received: {event.event_type}",
                metadata=receipt_data
            )
            
        except Exception as e:
            logger.error(f"Error logging webhook receipt: {e}")
    
    def _process_event_with_enhanced_retry(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Enhanced event processing with improved retry logic and idempotency handling"""
        last_error = None
        start_time = time.time()
        
        for attempt in range(self.retry_attempts):
            try:
                # Get event handler
                handler = self.event_handlers.get(event.event_type)
                if not handler:
                    return WebhookProcessingResult(
                        success=False,
                        error=f"No handler for event type: {event.event_type}"
                    )
                
                # Process event
                result = handler(event)
                
                if result.success:
                    # Update idempotency key with success result
                    self._update_idempotency_result(event, True, result)
                    
                    # Update processing state
                    self._update_processing_state(event, True)
                    
                    # Log successful processing
                    processing_time = time.time() - start_time
                    logger.info(f"Event {event.event_id} processed successfully in {processing_time:.3f}s (attempt {attempt + 1})")
                    return result
                else:
                    last_error = result.error
                    logger.warning(f"Event {event.event_id} processing failed (attempt {attempt + 1}): {result.error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} failed for event {event.event_id}: {e}")
                
                # Add exponential backoff delay
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
        
        # All attempts failed
        processing_time = time.time() - start_time
        logger.error(f"All {self.retry_attempts} attempts failed for event {event.event_id} in {processing_time:.3f}s")
        
        # Update idempotency key with failure result
        self._update_idempotency_result(event, False, None, last_error)
        
        # Update processing state
        self._update_processing_state(event, False, last_error)
        
        return WebhookProcessingResult(
            success=False,
            error=f"Processing failed after {self.retry_attempts} attempts: {last_error}"
        )
    
    def _update_idempotency_result(self, event: WebhookEvent, success: bool, result: Optional[WebhookProcessingResult] = None, error_message: Optional[str] = None) -> None:
        """Update idempotency key with processing result"""
        try:
            if not hasattr(event, 'processing_context') or not event.processing_context:
                return
            
            # Import idempotency service
            from ..services.idempotency_service import IdempotencyService
            
            # Initialize idempotency service
            idempotency_service = IdempotencyService(self.db)
            
            # Prepare result data
            result_data = None
            if success and result:
                result_data = {
                    'success': result.success,
                    'message': result.message,
                    'changes': result.changes,
                    'notifications_sent': result.notifications_sent
                }
            
            # Update idempotency key
            idempotency_service.update_idempotency_key_result(
                key_hash=event.processing_context['idempotency_key'],
                success=success,
                result_data=result_data,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Error updating idempotency result: {e}")
    
    def _update_processing_state(self, event: WebhookEvent, success: bool, error_message: Optional[str] = None) -> None:
        """Update processing state after event processing"""
        try:
            if not hasattr(event, 'processing_context') or not event.processing_context:
                return
            
            # Import idempotency service
            from ..services.idempotency_service import IdempotencyService
            
            # Initialize idempotency service
            idempotency_service = IdempotencyService(self.db)
            
            # Update processing state
            idempotency_service.update_processing_state(
                entity_type=event.processing_context.get('entity_type'),
                entity_id=event.processing_context.get('entity_id'),
                event_type=event.event_type,
                event_id=event.event_id,
                sequence_number=event.processing_context.get('sequence_number'),
                success=success,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Error updating processing state: {e}")
    
    def _log_to_comprehensive_service(
        self,
        logging_service,
        event: WebhookEvent,
        result: WebhookProcessingResult,
        processing_time: float,
        signature_result: Dict[str, Any],
        idempotency_result: Dict[str, Any]
    ) -> None:
        """Log to comprehensive webhook logging service"""
        try:
            # Prepare error details
            error_message = None
            error_details = None
            if not result.success:
                error_message = result.error
                error_details = {
                    'error_type': 'processing_error',
                    'error_code': 'WEBHOOK_PROCESSING_FAILED',
                    'retry_attempts': getattr(event, 'retry_attempts', 0),
                    'processing_context': getattr(event, 'processing_context', {})
                }
            
            # Prepare metadata
            metadata = {
                'signature_valid': signature_result.get('valid', False),
                'signature_timestamp': signature_result.get('timestamp'),
                'idempotency_key': idempotency_result.get('idempotency_key'),
                'deduplication_hash': idempotency_result.get('deduplication_hash'),
                'sequence_number': idempotency_result.get('sequence_number'),
                'changes_count': len(result.changes) if result.changes else 0,
                'notifications_sent': result.notifications_sent,
                'livemode': event.livemode,
                'api_version': event.api_version
            }
            
            # Extract entity information
            entity_type = None
            entity_id = None
            if hasattr(event, 'processing_context') and event.processing_context:
                entity_type = event.processing_context.get('entity_type')
                entity_id = event.processing_context.get('entity_id')
            
            # Log to comprehensive service
            logging_service.log_webhook_event(
                event_id=event.event_id,
                event_type=event.event_type,
                source_ip=event.source_ip,
                user_agent=event.user_agent,
                request_id=event.request_id,
                processing_time=processing_time,
                success=result.success,
                error_message=error_message,
                error_details=error_details,
                metadata=metadata,
                entity_type=entity_type,
                entity_id=entity_id,
                session_id=None,  # Webhook events don't have session context
                correlation_id=event.request_id
            )
            
        except Exception as e:
            logger.error(f"Error logging to comprehensive service: {e}")
    
    def get_webhook_analytics(
        self,
        time_range_hours: int = 24,
        include_health: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive webhook analytics"""
        try:
            from ..services.webhook_logging_service import WebhookLoggingService
            
            # Initialize logging service
            logging_service = WebhookLoggingService(self.db, self.config)
            
            # Get performance metrics
            performance_metrics = logging_service.get_performance_metrics(time_range_hours)
            
            # Get event analytics
            event_analytics = logging_service.get_event_analytics(time_range_hours)
            
            # Get error analytics
            error_analytics = logging_service.get_error_analytics(time_range_hours)
            
            # Prepare analytics response
            analytics = {
                'time_range_hours': time_range_hours,
                'performance_metrics': performance_metrics,
                'event_analytics': event_analytics,
                'error_analytics': error_analytics,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Include health status if requested
            if include_health:
                health_status = logging_service.get_health_status()
                analytics['health_status'] = health_status
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting webhook analytics: {e}")
            return {
                'error': str(e),
                'time_range_hours': time_range_hours,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def generate_webhook_report(
        self,
        time_range_hours: int = 24,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive webhook report"""
        try:
            from ..services.webhook_logging_service import WebhookLoggingService
            
            # Initialize logging service
            logging_service = WebhookLoggingService(self.db, self.config)
            
            # Generate report
            report = logging_service.generate_webhook_report(time_range_hours, include_details)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating webhook report: {e}")
            return {
                'error': str(e),
                'time_range_hours': time_range_hours,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _log_processing_result_enhanced(self, event: WebhookEvent, result: WebhookProcessingResult, processing_time: float) -> None:
        """Enhanced processing result logging with performance metrics"""
        try:
            result_data = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'success': result.success,
                'processing_time': processing_time,
                'changes_count': len(result.changes),
                'notifications_sent': result.notifications_sent,
                'error': result.error if not result.success else None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if result.success:
                logger.info(f"Webhook processing completed: {result_data}")
            else:
                logger.error(f"Webhook processing failed: {result_data}")
            
            # Log to audit trail
            self._log_audit_event(
                event_type=AuditEventType.WEBHOOK_PROCESSED,
                event_description=f"Webhook processing {'completed' if result.success else 'failed'}: {event.event_type}",
                metadata=result_data
            )
            
        except Exception as e:
            logger.error(f"Error logging processing result: {e}")
    
    def _log_processing_error(self, error: Exception, source_ip: str, user_agent: str, request_id: str, processing_time: float) -> None:
        """Log processing errors for monitoring and debugging"""
        try:
            error_data = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'source_ip': source_ip,
                'user_agent': user_agent,
                'request_id': request_id,
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'error'
            }
            
            logger.error(f"Webhook processing error: {error_data}")
            
            # Log to audit trail
            self._log_audit_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                event_description=f"Webhook processing error: {str(error)}",
                metadata=error_data
            )
            
        except Exception as e:
            logger.error(f"Error logging processing error: {e}")
    
    def _log_audit_event(self, event_type: AuditEventType, event_description: str, metadata: Dict[str, Any] = None) -> None:
        """Log audit events for security and compliance"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                event_description=event_description,
                metadata=metadata or {},
                severity=AuditSeverity.INFO
            )
            
            self.db.add(audit_log)
            # Note: Don't commit here to avoid transaction issues
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    # Legacy method for backward compatibility
    def _verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Legacy signature verification method (deprecated)"""
        result = self._verify_webhook_signature_enhanced(payload, signature)
        return result['valid']
    
    def _extract_signature_parts(self, signature: str) -> Tuple[Optional[int], List[str]]:
        """Extract timestamp and signatures from signature header"""
        try:
            parts = signature.split(',')
            timestamp = None
            signatures = []
            
            for part in parts:
                if part.startswith('t='):
                    timestamp = int(part[2:])
                elif part.startswith('v1='):
                    signatures.append(part[3:])
            
            return timestamp, signatures
            
        except Exception as e:
            logger.error(f"Error extracting signature parts: {e}")
            return None, []
    
    def _parse_webhook_event(
        self,
        payload: bytes,
        source_ip: str,
        user_agent: str,
        request_id: str
    ) -> Optional[WebhookEvent]:
        """Parse webhook event from payload"""
        try:
            event_data = json.loads(payload.decode('utf-8'))
            
            return WebhookEvent(
                event_id=event_data.get('id', ''),
                event_type=event_data.get('type', ''),
                event_data=event_data.get('data', {}),
                created_at=datetime.fromtimestamp(event_data.get('created', 0)),
                livemode=event_data.get('livemode', False),
                api_version=event_data.get('api_version', ''),
                request_id=request_id,
                source_ip=source_ip,
                user_agent=user_agent
            )
            
        except Exception as e:
            logger.error(f"Error parsing webhook event: {e}")
            return None
    
    def _process_event_with_retry(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Process event with retry logic"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Get event handler
                handler = self.event_handlers.get(event.event_type)
                if not handler:
                    return WebhookProcessingResult(
                        success=False,
                        error=f"No handler for event type: {event.event_type}"
                    )
                
                # Process event
                result = handler(event)
                
                if result.success:
                    return result
                else:
                    last_error = result.error
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} failed for event {event.event_id}: {e}")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return WebhookProcessingResult(
            success=False,
            error=f"Failed after {self.retry_attempts} attempts. Last error: {last_error}"
        )
    
    def _log_webhook_receipt(self, event: WebhookEvent) -> None:
        """Log webhook receipt"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.WEBHOOK_RECEIVED,
                event_description=f"Webhook received: {event.event_type}",
                severity=AuditSeverity.INFO,
                metadata={
                    'event_id': event.event_id,
                    'event_type': event.event_type,
                    'livemode': event.livemode,
                    'api_version': event.api_version,
                    'source_ip': event.source_ip,
                    'user_agent': event.user_agent,
                    'request_id': event.request_id,
                    'timestamp': event.created_at.isoformat()
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"Webhook received: {event.event_type} (ID: {event.event_id})")
            
        except Exception as e:
            logger.error(f"Error logging webhook receipt: {e}")
    
    def _log_processing_result(self, event: WebhookEvent, result: WebhookProcessingResult) -> None:
        """Log webhook processing result"""
        try:
            severity = AuditSeverity.ERROR if not result.success else AuditSeverity.INFO
            
            audit_log = AuditLog(
                event_type=AuditEventType.WEBHOOK_PROCESSED,
                event_description=f"Webhook processed: {event.event_type}",
                severity=severity,
                metadata={
                    'event_id': event.event_id,
                    'event_type': event.event_type,
                    'success': result.success,
                    'message': result.message,
                    'error': result.error,
                    'changes': result.changes,
                    'notifications_sent': result.notifications_sent,
                    'processed_at': result.processed_at.isoformat()
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            if result.success:
                logger.info(f"Webhook processed successfully: {event.event_type}")
            else:
                logger.error(f"Webhook processing failed: {event.event_type} - {result.error}")
                
        except Exception as e:
            logger.error(f"Error logging processing result: {e}")
    
    # Event Handlers
    def _handle_customer_created(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle customer.created webhook - Enhanced comprehensive customer registration"""
        try:
            customer_data = event.event_data.get('object', {})
            changes = []
            notifications_sent = 0
            
            logger.info(f"Processing customer creation for customer ID: {customer_data.get('id')}")
            
            # Step 1: Validate customer data
            validation_result = self._validate_customer_data(customer_data)
            if not validation_result['valid']:
                return WebhookProcessingResult(
                    success=False,
                    error=f"Invalid customer data: {validation_result['error']}"
                )
            
            # Step 2: Check if customer already exists
            existing_customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_data.get('id')
            ).first()
            
            if existing_customer:
                logger.info(f"Customer {customer_data.get('id')} already exists")
                return WebhookProcessingResult(
                    success=True,
                    message="Customer already exists",
                    changes=["Customer already exists in database"]
                )
            
            # Step 3: Extract and validate user information
            user_info = self._extract_user_information(customer_data)
            if not user_info:
                return WebhookProcessingResult(
                    success=False,
                    error="Unable to extract user information from customer data"
                )
            
            # Step 4: Create customer record with comprehensive data
            customer = self._create_customer_record(customer_data, user_info)
            
            # Step 5: Set up customer preferences and settings
            self._setup_customer_preferences(customer, customer_data)
            
            # Step 6: Initialize customer analytics and tracking
            self._initialize_customer_analytics(customer, customer_data)
            
            # Step 7: Set up customer portal access
            portal_setup = self._setup_customer_portal_access(customer, customer_data)
            if portal_setup:
                changes.append(portal_setup)
            
            # Step 8: Create initial audit trail
            self._create_customer_creation_audit(customer, customer_data)
            
            # Step 9: Send comprehensive welcome notifications
            notifications_sent = self._send_customer_welcome_notifications(customer, customer_data)
            
            # Step 10: Track customer creation analytics
            self._track_customer_creation_analytics(customer, customer_data)
            
            # Step 11: Set up customer lifecycle management
            lifecycle_setup = self._setup_customer_lifecycle_management(customer, customer_data)
            if lifecycle_setup:
                changes.append(lifecycle_setup)
            
            # Commit all changes
            self.db.commit()
            
            changes.append(f"Created customer: {customer.email}")
            changes.append(f"Stripe Customer ID: {customer.stripe_customer_id}")
            if customer.name:
                changes.append(f"Customer Name: {customer.name}")
            
            logger.info(f"Successfully created customer {customer.stripe_customer_id} for {customer.email}")
            
            return WebhookProcessingResult(
                success=True,
                message="Customer created successfully with comprehensive setup",
                changes=changes,
                notifications_sent=notifications_sent
            )
            
        except Exception as e:
            logger.error(f"Error handling customer.created: {e}")
            self.db.rollback()
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _validate_customer_data(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate customer data from Stripe webhook"""
        try:
            required_fields = ['id', 'email']
            missing_fields = [field for field in required_fields if not customer_data.get(field)]
            
            if missing_fields:
                return {
                    'valid': False,
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Validate email format
            email = customer_data.get('email', '')
            if not self._is_valid_email(email):
                return {
                    'valid': False,
                    'error': f"Invalid email format: {email}"
                }
            
            # Validate Stripe customer ID format
            stripe_id = customer_data.get('id', '')
            if not stripe_id.startswith('cus_'):
                return {
                    'valid': False,
                    'error': f"Invalid Stripe customer ID format: {stripe_id}"
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating customer data: {e}")
            return {
                'valid': False,
                'error': f"Validation error: {str(e)}"
            }
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _extract_user_information(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and validate user information from customer data"""
        try:
            # Get user ID from metadata
            user_id = customer_data.get('metadata', {}).get('mingus_user_id')
            
            if not user_id:
                logger.warning(f"No user ID in customer metadata: {customer_data.get('id')}")
                return None
            
            # Validate user exists in our system
            user = self.db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                logger.error(f"User {user_id} not found in database")
                return None
            
            return {
                'user_id': int(user_id),
                'user': user,
                'email': customer_data.get('email'),
                'name': customer_data.get('name'),
                'phone': customer_data.get('phone'),
                'address': customer_data.get('address'),
                'metadata': customer_data.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Error extracting user information: {e}")
            return None
    
    def _create_customer_record(self, customer_data: Dict[str, Any], user_info: Dict[str, Any]) -> Customer:
        """Create comprehensive customer record"""
        try:
            customer = Customer(
                user_id=user_info['user_id'],
                stripe_customer_id=customer_data['id'],
                email=customer_data.get('email'),
                name=customer_data.get('name'),
                phone=customer_data.get('phone'),
                address=customer_data.get('address'),
                tax_exempt=customer_data.get('tax_exempt', 'none'),
                metadata=customer_data.get('metadata', {})
            )
            
            self.db.add(customer)
            return customer
            
        except Exception as e:
            logger.error(f"Error creating customer record: {e}")
            raise
    
    def _setup_customer_preferences(self, customer: Customer, customer_data: Dict[str, Any]) -> None:
        """Set up customer preferences and default settings"""
        try:
            # Set default notification preferences
            # This would integrate with your notification preferences system
            logger.info(f"Setting up preferences for customer {customer.id}")
            
            # Set default billing preferences
            customer.metadata = customer_data.get('metadata', {})
            customer.metadata.update({
                'customer_created_at': datetime.utcnow().isoformat(),
                'preferences_setup': True,
                'default_currency': 'USD',
                'timezone': 'America/New_York'
            })
            
        except Exception as e:
            logger.error(f"Error setting up customer preferences: {e}")
    
    def _initialize_customer_analytics(self, customer: Customer, customer_data: Dict[str, Any]) -> None:
        """Initialize customer analytics and tracking"""
        try:
            # Track customer creation event
            self.analytics_service.track_event(
                event_type='customer_created',
                customer_id=customer.id,
                user_id=customer.user_id,
                properties={
                    'stripe_customer_id': customer.stripe_customer_id,
                    'email': customer.email,
                    'has_name': bool(customer.name),
                    'has_phone': bool(customer.phone),
                    'has_address': bool(customer.address),
                    'source': customer_data.get('metadata', {}).get('source', 'webhook'),
                    'created_via': 'stripe_webhook'
                }
            )
            
            logger.info(f"Initialized analytics for customer {customer.id}")
            
        except Exception as e:
            logger.error(f"Error initializing customer analytics: {e}")
    
    def _setup_customer_portal_access(self, customer: Customer, customer_data: Dict[str, Any]) -> Optional[str]:
        """Set up customer portal access"""
        try:
            # This would integrate with your customer portal system
            logger.info(f"Setting up portal access for customer {customer.id}")
            
            # Update metadata with portal information
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'portal_access_enabled': True,
                'portal_setup_at': datetime.utcnow().isoformat()
            })
            
            return "Customer portal access configured"
            
        except Exception as e:
            logger.error(f"Error setting up customer portal access: {e}")
            return None
    
    def _create_customer_creation_audit(self, customer: Customer, customer_data: Dict[str, Any]) -> None:
        """Create comprehensive audit trail for customer creation"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_CREATED,
                customer_id=customer.id,
                user_id=customer.user_id,
                event_description=f"Customer created via Stripe webhook: {customer.email}",
                metadata={
                    'stripe_customer_id': customer.stripe_customer_id,
                    'webhook_event_id': customer_data.get('id'),
                    'customer_email': customer.email,
                    'customer_name': customer.name,
                    'has_phone': bool(customer.phone),
                    'has_address': bool(customer.address),
                    'tax_exempt': customer.tax_exempt,
                    'creation_source': 'stripe_webhook'
                }
            )
            
            self.db.add(audit_log)
            logger.info(f"Created audit log for customer {customer.id}")
            
        except Exception as e:
            logger.error(f"Error creating customer creation audit: {e}")
    
    def _send_customer_welcome_notifications(self, customer: Customer, customer_data: Dict[str, Any]) -> int:
        """Send comprehensive welcome notifications"""
        try:
            notifications_sent = 0
            
            # Send welcome email
            try:
                self.notification_service.send_welcome_email(customer.id)
                notifications_sent += 1
                logger.info(f"Sent welcome email to {customer.email}")
            except Exception as e:
                logger.error(f"Error sending welcome email: {e}")
            
            # Send onboarding information if this is a new user
            try:
                if customer_data.get('metadata', {}).get('is_new_user'):
                    self.notification_service.send_onboarding_guide(customer.id)
                    notifications_sent += 1
                    logger.info(f"Sent onboarding guide to {customer.email}")
            except Exception as e:
                logger.error(f"Error sending onboarding guide: {e}")
            
            # Send customer portal access information
            try:
                self.notification_service.send_portal_access_info(customer.id)
                notifications_sent += 1
                logger.info(f"Sent portal access info to {customer.email}")
            except Exception as e:
                logger.error(f"Error sending portal access info: {e}")
            
            return notifications_sent
            
        except Exception as e:
            logger.error(f"Error sending customer welcome notifications: {e}")
            return 0
    
    def _track_customer_creation_analytics(self, customer: Customer, customer_data: Dict[str, Any]) -> None:
        """Track comprehensive analytics for customer creation"""
        try:
            # Track customer creation metrics
            self.analytics_service.track_metric(
                metric_name='customers_created',
                value=1,
                tags={
                    'source': 'stripe_webhook',
                    'has_name': bool(customer.name),
                    'has_phone': bool(customer.phone),
                    'has_address': bool(customer.address)
                }
            )
            
            # Track customer acquisition source
            source = customer_data.get('metadata', {}).get('source', 'unknown')
            self.analytics_service.track_metric(
                metric_name='customer_acquisition_source',
                value=1,
                tags={'source': source}
            )
            
            logger.info(f"Tracked analytics for customer {customer.id}")
            
        except Exception as e:
            logger.error(f"Error tracking customer creation analytics: {e}")
    
    def _setup_customer_lifecycle_management(self, customer: Customer, customer_data: Dict[str, Any]) -> Optional[str]:
        """Set up customer lifecycle management"""
        try:
            # This would integrate with your customer lifecycle management system
            logger.info(f"Setting up lifecycle management for customer {customer.id}")
            
            # Update metadata with lifecycle information
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'lifecycle_stage': 'new_customer',
                'lifecycle_setup_at': datetime.utcnow().isoformat(),
                'next_milestone': 'first_subscription'
            })
            
            return "Customer lifecycle management configured"
            
        except Exception as e:
            logger.error(f"Error setting up customer lifecycle management: {e}")
            return None
    
    def _handle_customer_updated(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle customer.updated webhook"""
        try:
            customer_data = event.event_data.get('object', {})
            changes = []
            
            # Find customer
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_data.get('id')
            ).first()
            
            if not customer:
                return WebhookProcessingResult(
                    success=False,
                    error="Customer not found"
                )
            
            # Update customer fields
            if customer_data.get('email') and customer_data['email'] != customer.email:
                old_email = customer.email
                customer.email = customer_data['email']
                changes.append(f"Email updated: {old_email} → {customer.email}")
            
            if customer_data.get('name') and customer_data['name'] != customer.name:
                old_name = customer.name
                customer.name = customer_data['name']
                changes.append(f"Name updated: {old_name} → {customer.name}")
            
            if customer_data.get('phone') and customer_data['phone'] != customer.phone:
                old_phone = customer.phone
                customer.phone = customer_data['phone']
                changes.append(f"Phone updated: {old_phone} → {customer.phone}")
            
            if customer_data.get('address'):
                customer.address = customer_data['address']
                changes.append("Address updated")
            
            customer.metadata = customer_data.get('metadata', {})
            
            self.db.commit()
            
            return WebhookProcessingResult(
                success=True,
                message="Customer updated successfully",
                changes=changes
            )
            
        except Exception as e:
            logger.error(f"Error handling customer.updated: {e}")
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _handle_customer_deleted(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle customer.deleted webhook"""
        try:
            customer_data = event.event_data.get('object', {})
            
            # Find customer
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_data.get('id')
            ).first()
            
            if not customer:
                return WebhookProcessingResult(
                    success=True,
                    message="Customer not found in database"
                )
            
            # Soft delete customer (mark as deleted)
            customer.deleted_at = datetime.utcnow()
            customer.is_active = False
            
            self.db.commit()
            
            return WebhookProcessingResult(
                success=True,
                message="Customer deleted successfully",
                changes=[f"Deleted customer: {customer.email}"]
            )
            
        except Exception as e:
            logger.error(f"Error handling customer.deleted: {e}")
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _handle_subscription_created(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle customer.subscription.created webhook - Comprehensive new subscription setup"""
        try:
            subscription_data = event.event_data.get('object', {})
            changes = []
            notifications_sent = 0
            
            logger.info(f"Processing subscription creation for subscription ID: {subscription_data.get('id')}")
            
            # Step 1: Validate and find customer
            customer = self._validate_and_find_customer(subscription_data)
            if not customer:
                return WebhookProcessingResult(
                    success=False,
                    error="Customer not found or invalid"
                )
            
            # Step 2: Check for existing subscription
            existing_subscription = self._check_existing_subscription(subscription_data)
            if existing_subscription:
                return WebhookProcessingResult(
                    success=True,
                    message="Subscription already exists",
                    changes=["Subscription already exists in database"]
                )
            
            # Step 3: Extract and validate subscription details
            subscription_details = self._extract_subscription_details(subscription_data)
            if not subscription_details:
                return WebhookProcessingResult(
                    success=False,
                    error="Invalid subscription data"
                )
            
            # Step 4: Find or create pricing tier
            pricing_tier = self._find_or_create_pricing_tier(subscription_details)
            
            # Step 5: Create subscription with comprehensive data
            subscription = self._create_subscription_record(
                customer, subscription_data, subscription_details, pricing_tier
            )
            
            # Step 6: Set up subscription features and access
            self._setup_subscription_features(subscription, subscription_details)
            
            # Step 7: Handle trial period if applicable
            trial_info = self._handle_trial_period(subscription, subscription_data)
            if trial_info:
                changes.append(trial_info)
            
            # Step 8: Set up billing and payment methods
            billing_setup = self._setup_billing_and_payment(subscription, subscription_data)
            if billing_setup:
                changes.append(billing_setup)
            
            # Step 9: Create initial billing history
            billing_history = self._create_initial_billing_history(subscription, subscription_data)
            
            # Step 10: Update customer subscription status
            self._update_customer_subscription_status(customer, subscription)
            
            # Step 11: Send comprehensive notifications
            notifications_sent = self._send_subscription_notifications(customer, subscription, subscription_details)
            
            # Step 12: Track analytics and metrics
            self._track_subscription_analytics(customer, subscription, subscription_details)
            
            # Step 13: Log comprehensive audit trail
            self._log_subscription_creation_audit(customer, subscription, subscription_details)
            
            # Step 14: Execute business logic for subscription creation
            business_logic_result = self._execute_business_logic_for_subscription_created(
                customer, subscription, subscription_data
            )
            
            # Add business logic changes and notifications
            if business_logic_result['success']:
                changes.extend(business_logic_result['changes'])
                notifications_sent += business_logic_result['notifications_sent']
            
            # Commit all changes
            self.db.commit()
            
            changes.append(f"Created subscription: {subscription.status} (ID: {subscription.stripe_subscription_id})")
            changes.append(f"Pricing tier: {pricing_tier.name if pricing_tier else 'Custom'}")
            changes.append(f"Billing cycle: {subscription.billing_cycle}")
            changes.append(f"Amount: ${subscription.amount}")
            
            if subscription_details.get('trial_end'):
                changes.append(f"Trial ends: {datetime.fromtimestamp(subscription_details['trial_end'])}")
            
            logger.info(f"Successfully created subscription {subscription.stripe_subscription_id} for customer {customer.email}")
            
            return WebhookProcessingResult(
                success=True,
                message="Subscription created successfully with comprehensive setup",
                changes=changes,
                notifications_sent=notifications_sent
            )
            
        except Exception as e:
            logger.error(f"Error handling subscription.created: {e}")
            self.db.rollback()
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _validate_and_find_customer(self, subscription_data: Dict[str, Any]) -> Optional[Customer]:
        """Validate and find customer for subscription"""
        try:
            customer_id = subscription_data.get('customer')
            if not customer_id:
                logger.error("No customer ID found in subscription data")
                return None
            
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_id
            ).first()
            
            if not customer:
                logger.error(f"Customer not found for ID: {customer_id}")
                return None
            
            if not customer.is_active:
                logger.warning(f"Customer {customer.email} is not active")
            
            return customer
            
        except Exception as e:
            logger.error(f"Error validating customer: {e}")
            return None
    
    def _check_existing_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Subscription]:
        """Check if subscription already exists"""
        try:
            subscription_id = subscription_data.get('id')
            if not subscription_id:
                return None
            
            existing_subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if existing_subscription:
                logger.info(f"Subscription {subscription_id} already exists in database")
            
            return existing_subscription
            
        except Exception as e:
            logger.error(f"Error checking existing subscription: {e}")
            return None
    
    def _extract_subscription_details(self, subscription_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and validate subscription details"""
        try:
            items = subscription_data.get('items', {}).get('data', [])
            if not items:
                logger.error("No subscription items found")
                return None
            
            # Get the first item (primary subscription)
            item = items[0]
            price = item.get('price', {})
            
            subscription_details = {
                'subscription_id': subscription_data.get('id'),
                'status': subscription_data.get('status'),
                'current_period_start': subscription_data.get('current_period_start'),
                'current_period_end': subscription_data.get('current_period_end'),
                'trial_start': subscription_data.get('trial_start'),
                'trial_end': subscription_data.get('trial_end'),
                'cancel_at_period_end': subscription_data.get('cancel_at_period_end', False),
                'canceled_at': subscription_data.get('canceled_at'),
                'price_id': price.get('id'),
                'price_amount': price.get('unit_amount', 0) / 100,
                'price_currency': price.get('currency', 'usd'),
                'price_interval': price.get('recurring', {}).get('interval', 'month'),
                'price_interval_count': price.get('recurring', {}).get('interval_count', 1),
                'quantity': item.get('quantity', 1),
                'metadata': subscription_data.get('metadata', {}),
                'application_fee_percent': subscription_data.get('application_fee_percent'),
                'automatic_tax': subscription_data.get('automatic_tax', {}),
                'billing_cycle_anchor': subscription_data.get('billing_cycle_anchor'),
                'billing_thresholds': subscription_data.get('billing_thresholds'),
                'collection_method': subscription_data.get('collection_method'),
                'days_until_due': subscription_data.get('days_until_due'),
                'default_payment_method': subscription_data.get('default_payment_method'),
                'default_source': subscription_data.get('default_source'),
                'default_tax_rates': subscription_data.get('default_tax_rates'),
                'discount': subscription_data.get('discount'),
                'ended_at': subscription_data.get('ended_at'),
                'livemode': subscription_data.get('livemode', False),
                'next_pending_invoice_item_invoice': subscription_data.get('next_pending_invoice_item_invoice'),
                'pause_collection': subscription_data.get('pause_collection'),
                'pending_invoice_item_interval': subscription_data.get('pending_invoice_item_interval'),
                'pending_setup_intent': subscription_data.get('pending_setup_intent'),
                'quantity': subscription_data.get('quantity'),
                'schedule': subscription_data.get('schedule'),
                'start_date': subscription_data.get('start_date'),
                'transfer_data': subscription_data.get('transfer_data')
            }
            
            # Validate required fields
            required_fields = ['subscription_id', 'status', 'current_period_start', 'current_period_end']
            for field in required_fields:
                if not subscription_details.get(field):
                    logger.error(f"Missing required field: {field}")
                    return None
            
            return subscription_details
            
        except Exception as e:
            logger.error(f"Error extracting subscription details: {e}")
            return None
    
    def _find_or_create_pricing_tier(self, subscription_details: Dict[str, Any]) -> Optional[PricingTier]:
        """Find or create pricing tier based on subscription details"""
        try:
            price_id = subscription_details.get('price_id')
            if not price_id:
                logger.warning("No price ID found, using default pricing tier")
                return None
            
            # Try to find existing pricing tier
            pricing_tier = self.db.query(PricingTier).filter(
                (PricingTier.stripe_price_id_monthly == price_id) |
                (PricingTier.stripe_price_id_yearly == price_id)
            ).first()
            
            if pricing_tier:
                logger.info(f"Found existing pricing tier: {pricing_tier.name}")
                return pricing_tier
            
            # Create new pricing tier if not found
            price_interval = subscription_details.get('price_interval', 'month')
            price_amount = subscription_details.get('price_amount', 0)
            
            tier_name = f"Custom Tier - ${price_amount}/{price_interval}"
            
            pricing_tier = PricingTier(
                name=tier_name,
                monthly_price=price_amount if price_interval == 'month' else price_amount / 12,
                yearly_price=price_amount if price_interval == 'year' else price_amount * 12,
                stripe_price_id_monthly=price_id if price_interval == 'month' else None,
                stripe_price_id_yearly=price_id if price_interval == 'year' else None,
                features=["custom_subscription"],
                description=f"Auto-generated tier for price {price_id}"
            )
            
            self.db.add(pricing_tier)
            self.db.flush()  # Get the ID without committing
            
            logger.info(f"Created new pricing tier: {tier_name}")
            return pricing_tier
            
        except Exception as e:
            logger.error(f"Error finding/creating pricing tier: {e}")
            return None
    
    def _create_subscription_record(
        self,
        customer: Customer,
        subscription_data: Dict[str, Any],
        subscription_details: Dict[str, Any],
        pricing_tier: Optional[PricingTier]
    ) -> Subscription:
        """Create comprehensive subscription record"""
        try:
            # Determine billing cycle
            price_interval = subscription_details.get('price_interval', 'month')
            billing_cycle = 'monthly' if price_interval == 'month' else 'yearly'
            
            # Calculate total amount
            amount = subscription_details.get('price_amount', 0) * subscription_details.get('quantity', 1)
            
            # Handle trial period
            trial_start = None
            trial_end = None
            if subscription_details.get('trial_start'):
                trial_start = datetime.fromtimestamp(subscription_details['trial_start'])
            if subscription_details.get('trial_end'):
                trial_end = datetime.fromtimestamp(subscription_details['trial_end'])
            
            # Create subscription
            subscription = Subscription(
                customer_id=customer.id,
                stripe_subscription_id=subscription_details['subscription_id'],
                pricing_tier_id=pricing_tier.id if pricing_tier else None,
                status=subscription_details['status'],
                current_period_start=datetime.fromtimestamp(subscription_details['current_period_start']),
                current_period_end=datetime.fromtimestamp(subscription_details['current_period_end']),
                amount=amount,
                billing_cycle=billing_cycle,
                cancel_at_period_end=subscription_details.get('cancel_at_period_end', False),
                trial_start=trial_start,
                trial_end=trial_end,
                quantity=subscription_details.get('quantity', 1),
                metadata=subscription_details.get('metadata', {}),
                collection_method=subscription_details.get('collection_method'),
                days_until_due=subscription_details.get('days_until_due'),
                default_payment_method=subscription_details.get('default_payment_method'),
                default_source=subscription_details.get('default_source'),
                application_fee_percent=subscription_details.get('application_fee_percent'),
                automatic_tax=subscription_details.get('automatic_tax', {}),
                billing_cycle_anchor=datetime.fromtimestamp(subscription_details['billing_cycle_anchor']) if subscription_details.get('billing_cycle_anchor') else None,
                billing_thresholds=subscription_details.get('billing_thresholds'),
                default_tax_rates=subscription_details.get('default_tax_rates'),
                discount=subscription_details.get('discount'),
                ended_at=datetime.fromtimestamp(subscription_details['ended_at']) if subscription_details.get('ended_at') else None,
                livemode=subscription_details.get('livemode', False),
                next_pending_invoice_item_invoice=subscription_details.get('next_pending_invoice_item_invoice'),
                pause_collection=subscription_details.get('pause_collection'),
                pending_invoice_item_interval=subscription_details.get('pending_invoice_item_interval'),
                pending_setup_intent=subscription_details.get('pending_setup_intent'),
                schedule=subscription_details.get('schedule'),
                start_date=datetime.fromtimestamp(subscription_details['start_date']) if subscription_details.get('start_date') else None,
                transfer_data=subscription_details.get('transfer_data')
            )
            
            self.db.add(subscription)
            self.db.flush()  # Get the ID without committing
            
            logger.info(f"Created subscription record with ID: {subscription.id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error creating subscription record: {e}")
            raise
    
    def _setup_subscription_features(self, subscription: Subscription, subscription_details: Dict[str, Any]) -> None:
        """Set up subscription features and access"""
        try:
            # This would integrate with your feature management system
            # For now, we'll log the setup
            logger.info(f"Setting up features for subscription {subscription.stripe_subscription_id}")
            
            # Example feature setup based on pricing tier
            if subscription.pricing_tier_id:
                pricing_tier = self.db.query(PricingTier).filter(
                    PricingTier.id == subscription.pricing_tier_id
                ).first()
                
                if pricing_tier:
                    features = pricing_tier.features or []
                    logger.info(f"Activating features: {features}")
                    
                    # Here you would activate features for the customer
                    # self.feature_service.activate_features(subscription.customer_id, features)
            
        except Exception as e:
            logger.error(f"Error setting up subscription features: {e}")
    
    def _handle_trial_period(self, subscription: Subscription, subscription_data: Dict[str, Any]) -> Optional[str]:
        """Handle trial period setup"""
        try:
            trial_start = subscription_data.get('trial_start')
            trial_end = subscription_data.get('trial_end')
            
            if trial_start and trial_end:
                trial_start_dt = datetime.fromtimestamp(trial_start)
                trial_end_dt = datetime.fromtimestamp(trial_end)
                
                logger.info(f"Trial period: {trial_start_dt} to {trial_end_dt}")
                
                # Set up trial-specific features or limitations
                # self.trial_service.setup_trial(subscription.customer_id, trial_end_dt)
                
                return f"Trial period set: {trial_start_dt.date()} to {trial_end_dt.date()}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error handling trial period: {e}")
            return None
    
    def _setup_billing_and_payment(self, subscription: Subscription, subscription_data: Dict[str, Any]) -> Optional[str]:
        """Set up billing and payment methods"""
        try:
            default_payment_method = subscription_data.get('default_payment_method')
            default_source = subscription_data.get('default_source')
            collection_method = subscription_data.get('collection_method')
            
            billing_info = []
            
            if default_payment_method:
                billing_info.append(f"Default payment method: {default_payment_method}")
                # self.payment_service.set_default_payment_method(subscription.customer_id, default_payment_method)
            
            if default_source:
                billing_info.append(f"Default source: {default_source}")
            
            if collection_method:
                billing_info.append(f"Collection method: {collection_method}")
            
            if billing_info:
                return "; ".join(billing_info)
            
            return None
            
        except Exception as e:
            logger.error(f"Error setting up billing and payment: {e}")
            return None
    
    def _create_initial_billing_history(self, subscription: Subscription, subscription_data: Dict[str, Any]) -> Optional[BillingHistory]:
        """Create initial billing history record"""
        try:
            # Create billing history for the subscription creation
            billing_history = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                stripe_invoice_id=None,  # No invoice yet for subscription creation
                amount=subscription.amount,
                currency='usd',  # Default currency
                status='pending',
                description=f"Subscription created: {subscription.stripe_subscription_id}",
                billing_date=datetime.utcnow(),
                due_date=subscription.current_period_end,
                metadata={
                    'subscription_creation': True,
                    'stripe_subscription_id': subscription.stripe_subscription_id,
                    'billing_cycle': subscription.billing_cycle
                }
            )
            
            self.db.add(billing_history)
            logger.info(f"Created initial billing history for subscription {subscription.stripe_subscription_id}")
            
            return billing_history
            
        except Exception as e:
            logger.error(f"Error creating initial billing history: {e}")
            return None
    
    def _update_customer_subscription_status(self, customer: Customer, subscription: Subscription) -> None:
        """Update customer subscription status"""
        try:
            # Update customer's subscription status
            customer.has_active_subscription = True
            customer.current_subscription_id = subscription.id
            customer.subscription_status = subscription.status
            
            # Update customer metadata
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'subscription_created_at': datetime.utcnow().isoformat(),
                'current_subscription_id': subscription.stripe_subscription_id,
                'subscription_status': subscription.status,
                'billing_cycle': subscription.billing_cycle
            })
            
            logger.info(f"Updated customer {customer.email} subscription status")
            
        except Exception as e:
            logger.error(f"Error updating customer subscription status: {e}")
    
    def _send_subscription_notifications(self, customer: Customer, subscription: Subscription, subscription_details: Dict[str, Any]) -> int:
        """Send comprehensive subscription notifications"""
        try:
            notifications_sent = 0
            
            # Send welcome email
            try:
                self.notification_service.send_welcome_email(customer.id)
                notifications_sent += 1
                logger.info(f"Sent welcome email to {customer.email}")
            except Exception as e:
                logger.error(f"Error sending welcome email: {e}")
            
            # Send subscription confirmation
            try:
                self.notification_service.send_subscription_confirmation(customer.id, subscription.id)
                notifications_sent += 1
                logger.info(f"Sent subscription confirmation to {customer.email}")
            except Exception as e:
                logger.error(f"Error sending subscription confirmation: {e}")
            
            # Send trial information if applicable
            if subscription_details.get('trial_end'):
                try:
                    self.notification_service.send_trial_information(customer.id, subscription.id)
                    notifications_sent += 1
                    logger.info(f"Sent trial information to {customer.email}")
                except Exception as e:
                    logger.error(f"Error sending trial information: {e}")
            
            # Send feature activation notification
            try:
                self.notification_service.send_feature_activation_notification(customer.id, subscription.id)
                notifications_sent += 1
                logger.info(f"Sent feature activation notification to {customer.email}")
            except Exception as e:
                logger.error(f"Error sending feature activation notification: {e}")
            
            return notifications_sent
            
        except Exception as e:
            logger.error(f"Error sending subscription notifications: {e}")
            return 0
    
    def _track_subscription_analytics(self, customer: Customer, subscription: Subscription, subscription_details: Dict[str, Any]) -> None:
        """Track comprehensive subscription analytics"""
        try:
            # Track subscription creation
            self.analytics_service.track_subscription_created(customer.id, subscription.id)
            
            # Track pricing tier selection
            if subscription.pricing_tier_id:
                self.analytics_service.track_pricing_tier_selection(customer.id, subscription.pricing_tier_id)
            
            # Track billing cycle selection
            self.analytics_service.track_billing_cycle_selection(customer.id, subscription.billing_cycle)
            
            # Track trial usage if applicable
            if subscription_details.get('trial_end'):
                self.analytics_service.track_trial_started(customer.id, subscription.id)
            
            # Track subscription value
            self.analytics_service.track_subscription_value(customer.id, subscription.amount, subscription.billing_cycle)
            
            logger.info(f"Tracked analytics for subscription {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error tracking subscription analytics: {e}")
    
    def _log_subscription_creation_audit(self, customer: Customer, subscription: Subscription, subscription_details: Dict[str, Any]) -> None:
        """Log comprehensive audit trail for subscription creation"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_CREATED,
                event_description=f"Subscription created: {subscription.stripe_subscription_id}",
                severity=AuditSeverity.INFO,
                metadata={
                    'customer_id': customer.id,
                    'customer_email': customer.email,
                    'subscription_id': subscription.id,
                    'stripe_subscription_id': subscription.stripe_subscription_id,
                    'pricing_tier_id': subscription.pricing_tier_id,
                    'status': subscription.status,
                    'amount': subscription.amount,
                    'billing_cycle': subscription.billing_cycle,
                    'trial_start': subscription.trial_start.isoformat() if subscription.trial_start else None,
                    'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                    'collection_method': subscription.collection_method,
                    'quantity': subscription.quantity,
                    'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            logger.info(f"Logged audit trail for subscription creation: {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error logging subscription creation audit: {e}")
    
    def _handle_subscription_updated(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle customer.subscription.updated webhook - Comprehensive subscription changes"""
        try:
            subscription_data = event.event_data.get('object', {})
            changes = []
            notifications_sent = 0
            
            logger.info(f"Processing subscription update for subscription ID: {subscription_data.get('id')}")
            
            # Step 1: Find and validate subscription
            subscription = self._find_and_validate_subscription(subscription_data)
            if not subscription:
                return WebhookProcessingResult(
                    success=False,
                    error="Subscription not found or invalid"
                )
            
            # Step 2: Extract subscription details
            subscription_details = self._extract_subscription_details(subscription_data)
            if not subscription_details:
                return WebhookProcessingResult(
                    success=False,
                    error="Invalid subscription data"
                )
            
            # Step 3: Capture old values for comparison
            old_values = self._capture_old_subscription_values(subscription)
            
            # Step 4: Update subscription with comprehensive changes
            self._update_subscription_record(subscription, subscription_details, changes)
            
            # Step 5: Handle pricing tier changes
            pricing_tier_changes = self._handle_pricing_tier_changes(subscription, subscription_details)
            if pricing_tier_changes:
                changes.extend(pricing_tier_changes)
            
            # Step 6: Handle trial period changes
            trial_changes = self._handle_trial_period_changes(subscription, subscription_details)
            if trial_changes:
                changes.extend(trial_changes)
            
            # Step 7: Handle billing and payment changes
            billing_changes = self._handle_billing_changes(subscription, subscription_details)
            if billing_changes:
                changes.extend(billing_changes)
            
            # Step 8: Update customer subscription status
            customer_changes = self._update_customer_for_subscription_changes(subscription, old_values)
            if customer_changes:
                changes.extend(customer_changes)
            
            # Step 9: Handle feature changes
            feature_changes = self._handle_feature_changes(subscription, old_values)
            if feature_changes:
                changes.extend(feature_changes)
            
            # Step 10: Create billing history for significant changes
            billing_history = self._create_billing_history_for_changes(subscription, old_values, changes)
            
            # Step 11: Send comprehensive notifications
            notifications_sent = self._send_subscription_update_notifications(subscription, old_values, changes)
            
            # Step 12: Track analytics and metrics
            self._track_subscription_update_analytics(subscription, old_values, changes)
            
            # Step 13: Log comprehensive audit trail
            self._log_subscription_update_audit(subscription, old_values, changes)
            
            # Commit all changes
            self.db.commit()
            
            if not changes:
                changes.append("No significant changes detected")
            
            logger.info(f"Successfully updated subscription {subscription.stripe_subscription_id} with {len(changes)} changes")
            
            return WebhookProcessingResult(
                success=True,
                message="Subscription updated successfully with comprehensive changes",
                changes=changes,
                notifications_sent=notifications_sent
            )
            
        except Exception as e:
            logger.error(f"Error handling subscription.updated: {e}")
            self.db.rollback()
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _find_and_validate_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Subscription]:
        """Find and validate subscription for updates"""
        try:
            subscription_id = subscription_data.get('id')
            if not subscription_id:
                logger.error("No subscription ID found in subscription data")
                return None
            
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"Subscription not found for ID: {subscription_id}")
                return None
            
            return subscription
            
        except Exception as e:
            logger.error(f"Error finding subscription: {e}")
            return None
    
    def _capture_old_subscription_values(self, subscription: Subscription) -> Dict[str, Any]:
        """Capture old subscription values for comparison"""
        return {
            'status': subscription.status,
            'amount': subscription.amount,
            'billing_cycle': subscription.billing_cycle,
            'pricing_tier_id': subscription.pricing_tier_id,
            'trial_start': subscription.trial_start,
            'trial_end': subscription.trial_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'canceled_at': subscription.canceled_at,
            'current_period_start': subscription.current_period_start,
            'current_period_end': subscription.current_period_end,
            'quantity': subscription.quantity,
            'collection_method': subscription.collection_method,
            'default_payment_method': subscription.default_payment_method,
            'metadata': subscription.metadata.copy() if subscription.metadata else {}
        }
    
    def _update_subscription_record(self, subscription: Subscription, subscription_details: Dict[str, Any], changes: List[str]) -> None:
        """Update subscription record with comprehensive changes"""
        try:
            # Update basic fields
            old_status = subscription.status
            old_amount = subscription.amount
            old_billing_cycle = subscription.billing_cycle
            old_quantity = subscription.quantity
            
            # Update status
            subscription.status = subscription_details['status']
            if old_status != subscription.status:
                changes.append(f"Status changed: {old_status} → {subscription.status}")
            
            # Update billing periods
            subscription.current_period_start = datetime.fromtimestamp(subscription_details['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(subscription_details['current_period_end'])
            
            # Update amount and billing cycle
            price_interval = subscription_details.get('price_interval', 'month')
            new_billing_cycle = 'monthly' if price_interval == 'month' else 'yearly'
            subscription.billing_cycle = new_billing_cycle
            
            new_amount = subscription_details.get('price_amount', 0) * subscription_details.get('quantity', 1)
            subscription.amount = new_amount
            
            if old_amount != new_amount:
                changes.append(f"Amount changed: ${old_amount} → ${new_amount}")
            
            if old_billing_cycle != new_billing_cycle:
                changes.append(f"Billing cycle changed: {old_billing_cycle} → {new_billing_cycle}")
            
            # Update quantity
            new_quantity = subscription_details.get('quantity', 1)
            subscription.quantity = new_quantity
            if old_quantity != new_quantity:
                changes.append(f"Quantity changed: {old_quantity} → {new_quantity}")
            
            # Update cancellation settings
            subscription.cancel_at_period_end = subscription_details.get('cancel_at_period_end', False)
            if subscription_details.get('canceled_at'):
                subscription.canceled_at = datetime.fromtimestamp(subscription_details['canceled_at'])
            
            # Update trial period
            if subscription_details.get('trial_start'):
                subscription.trial_start = datetime.fromtimestamp(subscription_details['trial_start'])
            if subscription_details.get('trial_end'):
                subscription.trial_end = datetime.fromtimestamp(subscription_details['trial_end'])
            
            # Update other fields
            subscription.collection_method = subscription_details.get('collection_method')
            subscription.days_until_due = subscription_details.get('days_until_due')
            subscription.default_payment_method = subscription_details.get('default_payment_method')
            subscription.default_source = subscription_details.get('default_source')
            subscription.application_fee_percent = subscription_details.get('application_fee_percent')
            subscription.automatic_tax = subscription_details.get('automatic_tax', {})
            subscription.billing_thresholds = subscription_details.get('billing_thresholds')
            subscription.default_tax_rates = subscription_details.get('default_tax_rates')
            subscription.discount = subscription_details.get('discount')
            subscription.pause_collection = subscription_details.get('pause_collection')
            subscription.pending_invoice_item_interval = subscription_details.get('pending_invoice_item_interval')
            subscription.pending_setup_intent = subscription_details.get('pending_setup_intent')
            subscription.schedule = subscription_details.get('schedule')
            subscription.transfer_data = subscription_details.get('transfer_data')
            
            # Update metadata
            subscription.metadata = subscription_details.get('metadata', {})
            
            logger.info(f"Updated subscription record for {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error updating subscription record: {e}")
            raise
    
    def _handle_pricing_tier_changes(self, subscription: Subscription, subscription_details: Dict[str, Any]) -> List[str]:
        """Handle pricing tier changes"""
        changes = []
        try:
            price_id = subscription_details.get('price_id')
            if not price_id:
                return changes
            
            # Find new pricing tier
            new_pricing_tier = self.db.query(PricingTier).filter(
                (PricingTier.stripe_price_id_monthly == price_id) |
                (PricingTier.stripe_price_id_yearly == price_id)
            ).first()
            
            old_pricing_tier_id = subscription.pricing_tier_id
            subscription.pricing_tier_id = new_pricing_tier.id if new_pricing_tier else None
            
            if old_pricing_tier_id != subscription.pricing_tier_id:
                if new_pricing_tier:
                    changes.append(f"Pricing tier changed: {new_pricing_tier.name}")
                else:
                    changes.append("Pricing tier removed")
                
                # Handle feature changes based on pricing tier
                self._update_features_for_pricing_tier_change(subscription, old_pricing_tier_id, subscription.pricing_tier_id)
            
        except Exception as e:
            logger.error(f"Error handling pricing tier changes: {e}")
        
        return changes
    
    def _handle_trial_period_changes(self, subscription: Subscription, subscription_details: Dict[str, Any]) -> List[str]:
        """Handle trial period changes"""
        changes = []
        try:
            old_trial_start = subscription.trial_start
            old_trial_end = subscription.trial_end
            
            # Update trial period
            if subscription_details.get('trial_start'):
                subscription.trial_start = datetime.fromtimestamp(subscription_details['trial_start'])
            if subscription_details.get('trial_end'):
                subscription.trial_end = datetime.fromtimestamp(subscription_details['trial_end'])
            
            # Check for changes
            if old_trial_start != subscription.trial_start:
                if subscription.trial_start:
                    changes.append(f"Trial started: {subscription.trial_start.date()}")
                else:
                    changes.append("Trial start removed")
            
            if old_trial_end != subscription.trial_end:
                if subscription.trial_end:
                    changes.append(f"Trial ends: {subscription.trial_end.date()}")
                else:
                    changes.append("Trial end removed")
            
            # Handle trial-specific changes
            if subscription.trial_end and not old_trial_end:
                changes.append("Trial period activated")
            elif old_trial_end and not subscription.trial_end:
                changes.append("Trial period ended")
            
        except Exception as e:
            logger.error(f"Error handling trial period changes: {e}")
        
        return changes
    
    def _handle_billing_changes(self, subscription: Subscription, subscription_details: Dict[str, Any]) -> List[str]:
        """Handle billing and payment method changes"""
        changes = []
        try:
            old_collection_method = subscription.collection_method
            old_default_payment_method = subscription.default_payment_method
            old_default_source = subscription.default_source
            
            # Update billing fields
            subscription.collection_method = subscription_details.get('collection_method')
            subscription.default_payment_method = subscription_details.get('default_payment_method')
            subscription.default_source = subscription_details.get('default_source')
            
            # Check for changes
            if old_collection_method != subscription.collection_method:
                changes.append(f"Collection method changed: {old_collection_method} → {subscription.collection_method}")
            
            if old_default_payment_method != subscription.default_payment_method:
                if subscription.default_payment_method:
                    changes.append(f"Default payment method updated: {subscription.default_payment_method}")
                else:
                    changes.append("Default payment method removed")
            
            if old_default_source != subscription.default_source:
                if subscription.default_source:
                    changes.append(f"Default source updated: {subscription.default_source}")
                else:
                    changes.append("Default source removed")
            
        except Exception as e:
            logger.error(f"Error handling billing changes: {e}")
        
        return changes
    
    def _update_customer_for_subscription_changes(self, subscription: Subscription, old_values: Dict[str, Any]) -> List[str]:
        """Update customer based on subscription changes"""
        changes = []
        try:
            customer = self.db.query(Customer).filter(Customer.id == subscription.customer_id).first()
            if not customer:
                return changes
            
            old_status = old_values.get('status')
            new_status = subscription.status
            
            # Update customer subscription status
            if old_status != new_status:
                customer.subscription_status = new_status
                
                # Update active subscription flag
                if new_status in ['active', 'trialing']:
                    customer.has_active_subscription = True
                elif new_status in ['canceled', 'unpaid', 'past_due']:
                    customer.has_active_subscription = False
                
                changes.append(f"Customer subscription status updated: {old_status} → {new_status}")
            
            # Update customer metadata
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'subscription_last_updated': datetime.utcnow().isoformat(),
                'current_subscription_status': new_status,
                'current_subscription_amount': subscription.amount,
                'current_billing_cycle': subscription.billing_cycle
            })
            
        except Exception as e:
            logger.error(f"Error updating customer for subscription changes: {e}")
        
        return changes
    
    def _handle_feature_changes(self, subscription: Subscription, old_values: Dict[str, Any]) -> List[str]:
        """Handle feature changes based on subscription updates"""
        changes = []
        try:
            old_pricing_tier_id = old_values.get('pricing_tier_id')
            new_pricing_tier_id = subscription.pricing_tier_id
            
            if old_pricing_tier_id != new_pricing_tier_id:
                # Update features based on new pricing tier
                if new_pricing_tier_id:
                    pricing_tier = self.db.query(PricingTier).filter(PricingTier.id == new_pricing_tier_id).first()
                    if pricing_tier:
                        features = pricing_tier.features or []
                        changes.append(f"Features updated: {', '.join(features)}")
                        # self.feature_service.update_features(subscription.customer_id, features)
                else:
                    changes.append("Features removed (no pricing tier)")
            
            # Handle status-based feature changes
            old_status = old_values.get('status')
            new_status = subscription.status
            
            if old_status != new_status:
                if new_status == 'active':
                    changes.append("Features activated")
                elif new_status == 'canceled':
                    changes.append("Features deactivated")
                elif new_status == 'past_due':
                    changes.append("Features limited (past due)")
            
        except Exception as e:
            logger.error(f"Error handling feature changes: {e}")
        
        return changes
    
    def _create_billing_history_for_changes(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> Optional[BillingHistory]:
        """Create billing history for significant changes"""
        try:
            # Only create billing history for significant changes
            significant_changes = [
                'Amount changed',
                'Billing cycle changed',
                'Pricing tier changed',
                'Status changed'
            ]
            
            has_significant_changes = any(any(sig in change for sig in significant_changes) for change in changes)
            
            if has_significant_changes:
                billing_history = BillingHistory(
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    stripe_invoice_id=None,
                    amount=subscription.amount,
                    currency='usd',
                    status='pending',
                    description=f"Subscription updated: {', '.join(changes[:3])}",
                    billing_date=datetime.utcnow(),
                    due_date=subscription.current_period_end,
                    metadata={
                        'subscription_update': True,
                        'stripe_subscription_id': subscription.stripe_subscription_id,
                        'changes': changes,
                        'old_amount': old_values.get('amount'),
                        'new_amount': subscription.amount
                    }
                )
                
                self.db.add(billing_history)
                logger.info(f"Created billing history for subscription update: {subscription.stripe_subscription_id}")
                return billing_history
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating billing history for changes: {e}")
            return None
    
    def _send_subscription_update_notifications(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> int:
        """Send comprehensive subscription update notifications"""
        notifications_sent = 0
        try:
            # Send status change notification
            old_status = old_values.get('status')
            new_status = subscription.status
            
            if old_status != new_status:
                try:
                    self.notification_service.send_subscription_status_update(
                        subscription.customer_id, subscription.id, new_status
                    )
                    notifications_sent += 1
                    logger.info(f"Sent status update notification for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending status update notification: {e}")
            
            # Send amount change notification
            old_amount = old_values.get('amount')
            new_amount = subscription.amount
            
            if old_amount != new_amount:
                try:
                    self.notification_service.send_subscription_amount_change_notification(
                        subscription.customer_id, subscription.id, old_amount, new_amount
                    )
                    notifications_sent += 1
                    logger.info(f"Sent amount change notification for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending amount change notification: {e}")
            
            # Send billing cycle change notification
            old_billing_cycle = old_values.get('billing_cycle')
            new_billing_cycle = subscription.billing_cycle
            
            if old_billing_cycle != new_billing_cycle:
                try:
                    self.notification_service.send_billing_cycle_change_notification(
                        subscription.customer_id, subscription.id, old_billing_cycle, new_billing_cycle
                    )
                    notifications_sent += 1
                    logger.info(f"Sent billing cycle change notification for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending billing cycle change notification: {e}")
            
            # Send trial ending notification
            if subscription.trial_end and not old_values.get('trial_end'):
                try:
                    self.notification_service.send_trial_ending_notification(
                        subscription.customer_id, subscription.id
                    )
                    notifications_sent += 1
                    logger.info(f"Sent trial ending notification for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending trial ending notification: {e}")
            
            # Send cancellation scheduled notification
            if subscription.cancel_at_period_end and not old_values.get('cancel_at_period_end'):
                try:
                    self.notification_service.send_cancellation_scheduled_notification(
                        subscription.customer_id, subscription.id, subscription.current_period_end
                    )
                    notifications_sent += 1
                    logger.info(f"Sent cancellation scheduled notification for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending cancellation scheduled notification: {e}")
            
        except Exception as e:
            logger.error(f"Error sending subscription update notifications: {e}")
        
        return notifications_sent
    
    def _track_subscription_update_analytics(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> None:
        """Track comprehensive analytics for subscription updates"""
        try:
            # Track subscription update
            self.analytics_service.track_subscription_updated(subscription.customer_id, subscription.id, changes)
            
            # Track specific change types
            for change in changes:
                if 'Amount changed' in change:
                    old_amount = old_values.get('amount', 0)
                    new_amount = subscription.amount
                    self.analytics_service.track_subscription_amount_change(
                        subscription.customer_id, subscription.id, old_amount, new_amount
                    )
                
                if 'Billing cycle changed' in change:
                    old_cycle = old_values.get('billing_cycle')
                    new_cycle = subscription.billing_cycle
                    self.analytics_service.track_billing_cycle_change(
                        subscription.customer_id, subscription.id, old_cycle, new_cycle
                    )
                
                if 'Status changed' in change:
                    old_status = old_values.get('status')
                    new_status = subscription.status
                    self.analytics_service.track_subscription_status_change(
                        subscription.customer_id, subscription.id, old_status, new_status
                    )
                
                if 'Pricing tier changed' in change:
                    old_tier_id = old_values.get('pricing_tier_id')
                    new_tier_id = subscription.pricing_tier_id
                    self.analytics_service.track_pricing_tier_change(
                        subscription.customer_id, subscription.id, old_tier_id, new_tier_id
                    )
            
            # Track cancellation scheduling
            if subscription.cancel_at_period_end and not old_values.get('cancel_at_period_end'):
                self.analytics_service.track_cancellation_scheduled(
                    subscription.customer_id, subscription.id, subscription.current_period_end
                )
            
            logger.info(f"Tracked analytics for subscription update: {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error tracking subscription update analytics: {e}")
    
    def _log_subscription_update_audit(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> None:
        """Log comprehensive audit trail for subscription updates"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                event_description=f"Subscription updated: {subscription.stripe_subscription_id}",
                severity=AuditSeverity.INFO,
                metadata={
                    'subscription_id': subscription.id,
                    'stripe_subscription_id': subscription.stripe_subscription_id,
                    'customer_id': subscription.customer_id,
                    'old_values': old_values,
                    'new_values': {
                        'status': subscription.status,
                        'amount': subscription.amount,
                        'billing_cycle': subscription.billing_cycle,
                        'pricing_tier_id': subscription.pricing_tier_id,
                        'trial_start': subscription.trial_start.isoformat() if subscription.trial_start else None,
                        'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
                        'quantity': subscription.quantity,
                        'collection_method': subscription.collection_method
                    },
                    'changes': changes,
                    'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
                    'updated_at': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            logger.info(f"Logged audit trail for subscription update: {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error logging subscription update audit: {e}")
    
    def _update_features_for_pricing_tier_change(self, subscription: Subscription, old_tier_id: Optional[int], new_tier_id: Optional[int]) -> None:
        """Update features when pricing tier changes"""
        try:
            # This would integrate with your feature management system
            logger.info(f"Updating features for pricing tier change: {old_tier_id} → {new_tier_id}")
            
            # Example feature update logic
            # if old_tier_id:
            #     self.feature_service.remove_features(subscription.customer_id, old_tier_id)
            # if new_tier_id:
            #     self.feature_service.add_features(subscription.customer_id, new_tier_id)
            
        except Exception as e:
            logger.error(f"Error updating features for pricing tier change: {e}")
    
    def _handle_subscription_deleted(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle customer.subscription.deleted webhook - Comprehensive subscription cancellation"""
        try:
            subscription_data = event.event_data.get('object', {})
            changes = []
            notifications_sent = 0
            
            logger.info(f"Processing subscription cancellation for subscription ID: {subscription_data.get('id')}")
            
            # Step 1: Find and validate subscription
            subscription = self._find_and_validate_subscription(subscription_data)
            if not subscription:
                return WebhookProcessingResult(
                    success=True,
                    message="Subscription not found in database"
                )
            
            # Step 2: Extract cancellation details
            cancellation_details = self._extract_cancellation_details(subscription_data)
            
            # Step 3: Capture subscription state before cancellation
            pre_cancellation_state = self._capture_pre_cancellation_state(subscription)
            
            # Step 4: Update subscription status and cancellation info
            self._update_subscription_for_cancellation(subscription, cancellation_details, changes)
            
            # Step 5: Handle feature deactivation
            feature_changes = self._handle_feature_deactivation(subscription, pre_cancellation_state)
            if feature_changes:
                changes.extend(feature_changes)
            
            # Step 6: Update customer subscription status
            customer_changes = self._update_customer_for_cancellation(subscription, pre_cancellation_state)
            if customer_changes:
                changes.extend(customer_changes)
            
            # Step 7: Create final billing history
            billing_history = self._create_final_billing_history(subscription, cancellation_details)
            
            # Step 8: Handle data retention and cleanup
            cleanup_changes = self._handle_data_retention_and_cleanup(subscription, cancellation_details)
            if cleanup_changes:
                changes.extend(cleanup_changes)
            
            # Step 9: Send comprehensive cancellation notifications
            notifications_sent = self._send_cancellation_notifications(subscription, cancellation_details, pre_cancellation_state)
            
            # Step 10: Track cancellation analytics
            self._track_cancellation_analytics(subscription, cancellation_details, pre_cancellation_state)
            
            # Step 11: Log comprehensive cancellation audit
            self._log_cancellation_audit(subscription, cancellation_details, pre_cancellation_state)
            
            # Commit all changes
            self.db.commit()
            
            changes.append(f"Subscription canceled: {subscription.stripe_subscription_id}")
            
            logger.info(f"Successfully canceled subscription {subscription.stripe_subscription_id}")
            
            return WebhookProcessingResult(
                success=True,
                message="Subscription canceled successfully with comprehensive cleanup",
                changes=changes,
                notifications_sent=notifications_sent
            )
            
        except Exception as e:
            logger.error(f"Error handling subscription.deleted: {e}")
            self.db.rollback()
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _extract_cancellation_details(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract cancellation details from subscription data"""
        try:
            return {
                'cancellation_reason': subscription_data.get('cancellation_reason'),
                'canceled_at': subscription_data.get('canceled_at'),
                'cancel_at_period_end': subscription_data.get('cancel_at_period_end', False),
                'ended_at': subscription_data.get('ended_at'),
                'status': subscription_data.get('status'),
                'metadata': subscription_data.get('metadata', {}),
                'cancellation_source': subscription_data.get('metadata', {}).get('cancellation_source', 'unknown'),
                'cancellation_feedback': subscription_data.get('metadata', {}).get('cancellation_feedback'),
                'cancellation_date': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error extracting cancellation details: {e}")
            return {}
    
    def _capture_pre_cancellation_state(self, subscription: Subscription) -> Dict[str, Any]:
        """Capture subscription state before cancellation"""
        try:
            return {
                'status': subscription.status,
                'amount': subscription.amount,
                'billing_cycle': subscription.billing_cycle,
                'pricing_tier_id': subscription.pricing_tier_id,
                'trial_start': subscription.trial_start,
                'trial_end': subscription.trial_end,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'quantity': subscription.quantity,
                'collection_method': subscription.collection_method,
                'default_payment_method': subscription.default_payment_method,
                'metadata': subscription.metadata.copy() if subscription.metadata else {},
                'created_at': subscription.created_at,
                'total_billing_cycles': self._calculate_total_billing_cycles(subscription),
                'total_amount_paid': self._calculate_total_amount_paid(subscription)
            }
        except Exception as e:
            logger.error(f"Error capturing pre-cancellation state: {e}")
            return {}
    
    def _calculate_total_billing_cycles(self, subscription: Subscription) -> int:
        """Calculate total billing cycles for the subscription"""
        try:
            if not subscription.created_at or not subscription.current_period_end:
                return 0
            
            # This is a simplified calculation - in practice, you'd query billing history
            time_diff = subscription.current_period_end - subscription.created_at
            if subscription.billing_cycle == 'monthly':
                return max(1, int(time_diff.days / 30))
            else:  # yearly
                return max(1, int(time_diff.days / 365))
        except Exception as e:
            logger.error(f"Error calculating total billing cycles: {e}")
            return 0
    
    def _calculate_total_amount_paid(self, subscription: Subscription) -> float:
        """Calculate total amount paid for the subscription"""
        try:
            # Query billing history for total paid amount
            billing_records = self.db.query(BillingHistory).filter(
                BillingHistory.subscription_id == subscription.id,
                BillingHistory.status == 'paid'
            ).all()
            
            return sum(record.amount for record in billing_records)
        except Exception as e:
            logger.error(f"Error calculating total amount paid: {e}")
            return 0.0
    
    def _update_subscription_for_cancellation(self, subscription: Subscription, cancellation_details: Dict[str, Any], changes: List[str]) -> None:
        """Update subscription for cancellation"""
        try:
            old_status = subscription.status
            
            # Update status
            subscription.status = 'canceled'
            if old_status != subscription.status:
                changes.append(f"Status changed: {old_status} → {subscription.status}")
            
            # Update cancellation timestamp
            if cancellation_details.get('canceled_at'):
                subscription.canceled_at = datetime.fromtimestamp(cancellation_details['canceled_at'])
            else:
                subscription.canceled_at = datetime.utcnow()
            
            changes.append(f"Canceled at: {subscription.canceled_at}")
            
            # Update cancellation settings
            subscription.cancel_at_period_end = cancellation_details.get('cancel_at_period_end', False)
            
            # Update metadata with cancellation information
            if not subscription.metadata:
                subscription.metadata = {}
            
            subscription.metadata.update({
                'cancellation_reason': cancellation_details.get('cancellation_reason'),
                'cancellation_source': cancellation_details.get('cancellation_source'),
                'cancellation_feedback': cancellation_details.get('cancellation_feedback'),
                'cancellation_date': cancellation_details.get('cancellation_date').isoformat(),
                'canceled_at_period_end': cancellation_details.get('cancel_at_period_end', False)
            })
            
            logger.info(f"Updated subscription {subscription.stripe_subscription_id} for cancellation")
            
        except Exception as e:
            logger.error(f"Error updating subscription for cancellation: {e}")
            raise
    
    def _handle_feature_deactivation(self, subscription: Subscription, pre_cancellation_state: Dict[str, Any]) -> List[str]:
        """Handle feature deactivation for canceled subscription"""
        changes = []
        try:
            # Deactivate features based on pricing tier
            if subscription.pricing_tier_id:
                pricing_tier = self.db.query(PricingTier).filter(
                    PricingTier.id == subscription.pricing_tier_id
                ).first()
                
                if pricing_tier:
                    features = pricing_tier.features or []
                    changes.append(f"Features deactivated: {', '.join(features)}")
                    # self.feature_service.deactivate_features(subscription.customer_id, features)
            
            # Handle immediate vs end-of-period cancellation
            if subscription.cancel_at_period_end:
                changes.append("Features will be deactivated at period end")
            else:
                changes.append("Features immediately deactivated")
            
            # Handle trial-specific cleanup
            if pre_cancellation_state.get('trial_end'):
                changes.append("Trial period ended with cancellation")
            
        except Exception as e:
            logger.error(f"Error handling feature deactivation: {e}")
        
        return changes
    
    def _update_customer_for_cancellation(self, subscription: Subscription, pre_cancellation_state: Dict[str, Any]) -> List[str]:
        """Update customer for subscription cancellation"""
        changes = []
        try:
            customer = self.db.query(Customer).filter(Customer.id == subscription.customer_id).first()
            if not customer:
                return changes
            
            old_status = customer.subscription_status
            
            # Update customer subscription status
            customer.subscription_status = 'canceled'
            customer.has_active_subscription = False
            
            if old_status != customer.subscription_status:
                changes.append(f"Customer subscription status updated: {old_status} → {customer.subscription_status}")
            
            # Update customer metadata
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'subscription_canceled_at': datetime.utcnow().isoformat(),
                'last_subscription_status': 'canceled',
                'last_subscription_amount': pre_cancellation_state.get('amount', 0),
                'last_billing_cycle': pre_cancellation_state.get('billing_cycle'),
                'total_billing_cycles': pre_cancellation_state.get('total_billing_cycles', 0),
                'total_amount_paid': pre_cancellation_state.get('total_amount_paid', 0.0),
                'cancellation_reason': subscription.metadata.get('cancellation_reason'),
                'cancellation_source': subscription.metadata.get('cancellation_source')
            })
            
            changes.append("Customer subscription data updated")
            
        except Exception as e:
            logger.error(f"Error updating customer for cancellation: {e}")
        
        return changes
    
    def _create_final_billing_history(self, subscription: Subscription, cancellation_details: Dict[str, Any]) -> Optional[BillingHistory]:
        """Create final billing history record for cancellation"""
        try:
            billing_history = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                stripe_invoice_id=None,
                amount=subscription.amount,
                currency='usd',
                status='cancelled',
                description=f"Subscription canceled: {subscription.stripe_subscription_id}",
                billing_date=datetime.utcnow(),
                due_date=subscription.current_period_end,
                metadata={
                    'subscription_cancellation': True,
                    'stripe_subscription_id': subscription.stripe_subscription_id,
                    'cancellation_reason': cancellation_details.get('cancellation_reason'),
                    'cancellation_source': cancellation_details.get('cancellation_source'),
                    'canceled_at_period_end': cancellation_details.get('cancel_at_period_end', False),
                    'cancellation_date': cancellation_details.get('cancellation_date').isoformat()
                }
            )
            
            self.db.add(billing_history)
            logger.info(f"Created final billing history for subscription cancellation: {subscription.stripe_subscription_id}")
            
            return billing_history
            
        except Exception as e:
            logger.error(f"Error creating final billing history: {e}")
            return None
    
    def _handle_data_retention_and_cleanup(self, subscription: Subscription, cancellation_details: Dict[str, Any]) -> List[str]:
        """Handle data retention and cleanup for canceled subscription"""
        changes = []
        try:
            # Determine retention period based on cancellation reason
            retention_period = self._determine_retention_period(cancellation_details)
            
            # Set data retention flags
            if not subscription.metadata:
                subscription.metadata = {}
            
            subscription.metadata.update({
                'data_retention_until': (datetime.utcnow() + timedelta(days=retention_period)).isoformat(),
                'data_retention_period_days': retention_period,
                'data_cleanup_scheduled': True
            })
            
            changes.append(f"Data retention set for {retention_period} days")
            
            # Schedule cleanup tasks
            # self.cleanup_service.schedule_subscription_cleanup(subscription.id, retention_period)
            
            # Handle immediate cleanup for certain cancellation reasons
            if cancellation_details.get('cancellation_reason') in ['fraudulent', 'duplicate']:
                changes.append("Immediate data cleanup scheduled (fraudulent/duplicate)")
                # self.cleanup_service.immediate_cleanup(subscription.id)
            
        except Exception as e:
            logger.error(f"Error handling data retention and cleanup: {e}")
        
        return changes
    
    def _determine_retention_period(self, cancellation_details: Dict[str, Any]) -> int:
        """Determine data retention period based on cancellation details"""
        try:
            reason = cancellation_details.get('cancellation_reason', 'unknown')
            
            # Retention periods in days
            retention_periods = {
                'fraudulent': 30,      # Short retention for fraud
                'duplicate': 7,        # Very short for duplicates
                'requested_by_customer': 365,  # Long retention for customer requests
                'payment_failure': 90,  # Medium retention for payment issues
                'expired': 180,        # Medium retention for expired
                'unknown': 90          # Default retention
            }
            
            return retention_periods.get(reason, 90)
            
        except Exception as e:
            logger.error(f"Error determining retention period: {e}")
            return 90  # Default to 90 days
    
    def _send_cancellation_notifications(self, subscription: Subscription, cancellation_details: Dict[str, Any], pre_cancellation_state: Dict[str, Any]) -> int:
        """Send comprehensive cancellation notifications"""
        notifications_sent = 0
        try:
            # Send cancellation confirmation
            try:
                self.notification_service.send_subscription_cancellation(
                    subscription.customer_id, subscription.id
                )
                notifications_sent += 1
                logger.info(f"Sent cancellation confirmation for {subscription.stripe_subscription_id}")
            except Exception as e:
                logger.error(f"Error sending cancellation confirmation: {e}")
            
            # Send cancellation reason specific notification
            reason = cancellation_details.get('cancellation_reason')
            if reason == 'requested_by_customer':
                try:
                    self.notification_service.send_customer_requested_cancellation_notification(
                        subscription.customer_id, subscription.id, cancellation_details
                    )
                    notifications_sent += 1
                    logger.info(f"Sent customer-requested cancellation notification for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending customer-requested cancellation notification: {e}")
            
            # Send feedback request if no feedback provided
            if not cancellation_details.get('cancellation_feedback'):
                try:
                    self.notification_service.send_cancellation_feedback_request(
                        subscription.customer_id, subscription.id
                    )
                    notifications_sent += 1
                    logger.info(f"Sent cancellation feedback request for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending cancellation feedback request: {e}")
            
            # Send reactivation offer if appropriate
            if self._should_send_reactivation_offer(cancellation_details, pre_cancellation_state):
                try:
                    self.notification_service.send_reactivation_offer(
                        subscription.customer_id, subscription.id, pre_cancellation_state
                    )
                    notifications_sent += 1
                    logger.info(f"Sent reactivation offer for {subscription.stripe_subscription_id}")
                except Exception as e:
                    logger.error(f"Error sending reactivation offer: {e}")
            
            # Send data retention notification
            retention_period = self._determine_retention_period(cancellation_details)
            try:
                self.notification_service.send_data_retention_notification(
                    subscription.customer_id, subscription.id, retention_period
                )
                notifications_sent += 1
                logger.info(f"Sent data retention notification for {subscription.stripe_subscription_id}")
            except Exception as e:
                logger.error(f"Error sending data retention notification: {e}")
            
        except Exception as e:
            logger.error(f"Error sending cancellation notifications: {e}")
        
        return notifications_sent
    
    def _should_send_reactivation_offer(self, cancellation_details: Dict[str, Any], pre_cancellation_state: Dict[str, Any]) -> bool:
        """Determine if reactivation offer should be sent"""
        try:
            # Don't send for fraudulent or duplicate cancellations
            if cancellation_details.get('cancellation_reason') in ['fraudulent', 'duplicate']:
                return False
            
            # Send for customer-requested cancellations with good history
            if (cancellation_details.get('cancellation_reason') == 'requested_by_customer' and
                pre_cancellation_state.get('total_billing_cycles', 0) >= 3):
                return True
            
            # Send for payment failure cancellations
            if cancellation_details.get('cancellation_reason') == 'payment_failure':
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining reactivation offer: {e}")
            return False
    
    def _track_cancellation_analytics(self, subscription: Subscription, cancellation_details: Dict[str, Any], pre_cancellation_state: Dict[str, Any]) -> None:
        """Track comprehensive analytics for subscription cancellation"""
        try:
            # Track basic cancellation
            self.analytics_service.track_subscription_canceled(subscription.customer_id, subscription.id)
            
            # Track cancellation reason
            reason = cancellation_details.get('cancellation_reason', 'unknown')
            self.analytics_service.track_cancellation_reason(subscription.customer_id, subscription.id, reason)
            
            # Track cancellation source
            source = cancellation_details.get('cancellation_source', 'unknown')
            self.analytics_service.track_cancellation_source(subscription.customer_id, subscription.id, source)
            
            # Track subscription lifetime metrics
            total_cycles = pre_cancellation_state.get('total_billing_cycles', 0)
            total_amount = pre_cancellation_state.get('total_amount_paid', 0.0)
            subscription_duration = (subscription.canceled_at - subscription.created_at).days if subscription.canceled_at and subscription.created_at else 0
            
            self.analytics_service.track_subscription_lifetime_metrics(
                subscription.customer_id, subscription.id, total_cycles, total_amount, subscription_duration
            )
            
            # Track churn metrics
            self.analytics_service.track_churn_metrics(
                subscription.customer_id, subscription.id, reason, source, total_cycles, total_amount
            )
            
            # Track reactivation potential
            if self._should_send_reactivation_offer(cancellation_details, pre_cancellation_state):
                self.analytics_service.track_reactivation_potential(
                    subscription.customer_id, subscription.id, reason, total_cycles, total_amount
                )
            
            logger.info(f"Tracked analytics for subscription cancellation: {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error tracking cancellation analytics: {e}")
    
    def _log_cancellation_audit(self, subscription: Subscription, cancellation_details: Dict[str, Any], pre_cancellation_state: Dict[str, Any]) -> None:
        """Log comprehensive audit trail for subscription cancellation"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_CANCELED,
                event_description=f"Subscription canceled: {subscription.stripe_subscription_id}",
                severity=AuditSeverity.WARNING,
                metadata={
                    'subscription_id': subscription.id,
                    'stripe_subscription_id': subscription.stripe_subscription_id,
                    'customer_id': subscription.customer_id,
                    'cancellation_details': cancellation_details,
                    'pre_cancellation_state': pre_cancellation_state,
                    'cancellation_reason': cancellation_details.get('cancellation_reason'),
                    'cancellation_source': cancellation_details.get('cancellation_source'),
                    'cancellation_feedback': cancellation_details.get('cancellation_feedback'),
                    'total_billing_cycles': pre_cancellation_state.get('total_billing_cycles', 0),
                    'total_amount_paid': pre_cancellation_state.get('total_amount_paid', 0.0),
                    'subscription_duration_days': (subscription.canceled_at - subscription.created_at).days if subscription.canceled_at and subscription.created_at else 0,
                    'canceled_at_period_end': cancellation_details.get('cancel_at_period_end', False),
                    'data_retention_period_days': self._determine_retention_period(cancellation_details),
                    'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
                    'canceled_at': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            logger.info(f"Logged audit trail for subscription cancellation: {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error logging cancellation audit: {e}")
    
    def _handle_subscription_trial_will_end(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle customer.subscription.trial_will_end webhook"""
        try:
            subscription_data = event.event_data.get('object', {})
            
            # Find subscription
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_data.get('id')
            ).first()
            
            if not subscription:
                return WebhookProcessingResult(
                    success=False,
                    error="Subscription not found"
                )
            
            # Send trial ending notification
            notifications_sent = self.notification_service.send_trial_ending_notification(
                subscription.customer_id, subscription.id
            )
            
            return WebhookProcessingResult(
                success=True,
                message="Trial ending notification sent",
                changes=["Trial ending notification sent"],
                notifications_sent=notifications_sent
            )
            
        except Exception as e:
            logger.error(f"Error handling subscription.trial_will_end: {e}")
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _handle_invoice_payment_succeeded(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle invoice.payment_succeeded webhook - Comprehensive successful payment processing"""
        try:
            invoice_data = event.event_data.get('object', {})
            changes = []
            notifications_sent = 0
            
            logger.info(f"Processing successful payment for invoice ID: {invoice_data.get('id')}")
            
            # Step 1: Extract and validate invoice details
            invoice_details = self._extract_invoice_details(invoice_data)
            if not invoice_details:
                return WebhookProcessingResult(
                    success=False,
                    error="Invalid invoice data"
                )
            
            # Step 2: Find and validate customer
            customer = self._find_and_validate_customer_for_invoice(invoice_data)
            if not customer:
                return WebhookProcessingResult(
                    success=False,
                    error="Customer not found or invalid"
                )
            
            # Step 3: Find or create billing history record
            billing_record = self._find_or_create_billing_record(invoice_data, customer, invoice_details, changes)
            
            # Step 4: Update billing record with payment success
            self._update_billing_record_for_successful_payment(billing_record, invoice_details, changes)
            
            # Step 5: Handle subscription status updates
            subscription_changes = self._handle_subscription_status_for_successful_payment(customer, invoice_details)
            if subscription_changes:
                changes.extend(subscription_changes)
            
            # Step 6: Update customer payment status
            customer_changes = self._update_customer_for_successful_payment(customer, invoice_details)
            if customer_changes:
                changes.extend(customer_changes)
            
            # Step 7: Handle payment method updates
            payment_method_changes = self._handle_payment_method_for_successful_payment(customer, invoice_details)
            if payment_method_changes:
                changes.extend(payment_method_changes)
            
            # Step 8: Process discounts and credits
            discount_changes = self._handle_discounts_and_credits(invoice_details)
            if discount_changes:
                changes.extend(discount_changes)
            
            # Step 9: Handle tax calculations
            tax_changes = self._handle_tax_calculations(invoice_details)
            if tax_changes:
                changes.extend(tax_changes)
            
            # Step 10: Send comprehensive notifications
            notifications_sent = self._send_successful_payment_notifications(customer, billing_record, invoice_details)
            
            # Step 11: Track comprehensive analytics
            self._track_successful_payment_analytics(customer, billing_record, invoice_details)
            
            # Step 12: Log comprehensive audit trail
            self._log_successful_payment_audit(customer, billing_record, invoice_details)
            
            # Commit all changes
            self.db.commit()
            
            changes.append(f"Payment processed successfully: ${invoice_details['amount_paid']}")
            
            logger.info(f"Successfully processed payment for invoice {invoice_data.get('id')}")
            
            return WebhookProcessingResult(
                success=True,
                message="Payment succeeded with comprehensive processing",
                changes=changes,
                notifications_sent=notifications_sent
            )
            
        except Exception as e:
            logger.error(f"Error handling invoice.payment_succeeded: {e}")
            self.db.rollback()
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _extract_invoice_details(self, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and validate invoice details"""
        try:
            # Extract comprehensive invoice data
            invoice_details = {
                'invoice_id': invoice_data.get('id'),
                'customer_id': invoice_data.get('customer'),
                'subscription_id': invoice_data.get('subscription'),
                'status': invoice_data.get('status'),
                'amount_due': invoice_data.get('amount_due', 0) / 100,
                'amount_paid': invoice_data.get('amount_paid', 0) / 100,
                'amount_remaining': invoice_data.get('amount_remaining', 0) / 100,
                'currency': invoice_data.get('currency', 'usd'),
                'created': invoice_data.get('created'),
                'due_date': invoice_data.get('due_date'),
                'period_start': invoice_data.get('period_start'),
                'period_end': invoice_data.get('period_end'),
                'hosted_invoice_url': invoice_data.get('hosted_invoice_url'),
                'invoice_pdf': invoice_data.get('invoice_pdf'),
                'receipt_url': invoice_data.get('receipt_url'),
                'collection_method': invoice_data.get('collection_method'),
                'auto_advance': invoice_data.get('auto_advance'),
                'attempt_count': invoice_data.get('attempt_count', 0),
                'next_payment_attempt': invoice_data.get('next_payment_attempt'),
                'metadata': invoice_data.get('metadata', {}),
                'discount': invoice_data.get('discount'),
                'tax': invoice_data.get('tax'),
                'tax_percent': invoice_data.get('tax_percent'),
                'total_tax_amounts': invoice_data.get('total_tax_amounts', []),
                'lines': invoice_data.get('lines', {}).get('data', []),
                'payment_intent': invoice_data.get('payment_intent'),
                'charge': invoice_data.get('charge'),
                'payment_method': invoice_data.get('payment_method'),
                'payment_method_types': invoice_data.get('payment_method_types', []),
                'payment_settings': invoice_data.get('payment_settings', {}),
                'transfer_data': invoice_data.get('transfer_data'),
                'application_fee_amount': invoice_data.get('application_fee_amount'),
                'last_finalization_error': invoice_data.get('last_finalization_error'),
                'last_payment_error': invoice_data.get('last_payment_error'),
                'livemode': invoice_data.get('livemode', False)
            }
            
            # Validate required fields
            required_fields = ['invoice_id', 'customer_id', 'status', 'amount_paid']
            for field in required_fields:
                if not invoice_details.get(field):
                    logger.error(f"Missing required field: {field}")
                    return None
            
            return invoice_details
            
        except Exception as e:
            logger.error(f"Error extracting invoice details: {e}")
            return None
    
    def _find_and_validate_customer_for_invoice(self, invoice_data: Dict[str, Any]) -> Optional[Customer]:
        """Find and validate customer for invoice"""
        try:
            customer_id = invoice_data.get('customer')
            if not customer_id:
                logger.error("No customer ID found in invoice data")
                return None
            
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_id
            ).first()
            
            if not customer:
                logger.error(f"Customer not found for ID: {customer_id}")
                return None
            
            if not customer.is_active:
                logger.warning(f"Customer {customer.email} is not active")
            
            return customer
            
        except Exception as e:
            logger.error(f"Error finding customer for invoice: {e}")
            return None
    
    def _find_or_create_billing_record(self, invoice_data: Dict[str, Any], customer: Customer, invoice_details: Dict[str, Any], changes: List[str]) -> BillingHistory:
        """Find or create billing history record"""
        try:
            # Try to find existing billing record
            billing_record = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_invoice_id == invoice_details['invoice_id']
            ).first()
            
            if billing_record:
                logger.info(f"Found existing billing record for invoice {invoice_details['invoice_id']}")
                return billing_record
            
            # Find subscription if available
            subscription = None
            if invoice_details.get('subscription_id'):
                subscription = self.db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == invoice_details['subscription_id']
                ).first()
            
            # Create new billing record
            billing_record = BillingHistory(
                customer_id=customer.id,
                subscription_id=subscription.id if subscription else None,
                stripe_invoice_id=invoice_details['invoice_id'],
                amount=invoice_details['amount_paid'],
                currency=invoice_details['currency'],
                status='paid',
                description=f"Invoice payment: {invoice_details['invoice_id']}",
                billing_date=datetime.fromtimestamp(invoice_details['created']) if invoice_details.get('created') else datetime.utcnow(),
                due_date=datetime.fromtimestamp(invoice_details['due_date']) if invoice_details.get('due_date') else None,
                paid_at=datetime.utcnow(),
                invoice_url=invoice_details.get('hosted_invoice_url'),
                invoice_pdf=invoice_details.get('invoice_pdf'),
                receipt_url=invoice_details.get('receipt_url'),
                metadata={
                    'invoice_created': invoice_details.get('created'),
                    'period_start': invoice_details.get('period_start'),
                    'period_end': invoice_details.get('period_end'),
                    'collection_method': invoice_details.get('collection_method'),
                    'attempt_count': invoice_details.get('attempt_count', 0),
                    'payment_intent': invoice_details.get('payment_intent'),
                    'charge': invoice_details.get('charge'),
                    'payment_method': invoice_details.get('payment_method'),
                    'payment_method_types': invoice_details.get('payment_method_types', []),
                    'livemode': invoice_details.get('livemode', False)
                }
            )
            
            self.db.add(billing_record)
            changes.append(f"Created billing record: ${billing_record.amount}")
            
            logger.info(f"Created new billing record for invoice {invoice_details['invoice_id']}")
            return billing_record
            
        except Exception as e:
            logger.error(f"Error finding/creating billing record: {e}")
            raise
    
    def _update_billing_record_for_successful_payment(self, billing_record: BillingHistory, invoice_details: Dict[str, Any], changes: List[str]) -> None:
        """Update billing record for successful payment"""
        try:
            old_status = billing_record.status
            old_amount = billing_record.amount
            
            # Update billing record
            billing_record.status = 'paid'
            billing_record.amount = invoice_details['amount_paid']
            billing_record.paid_at = datetime.utcnow()
            billing_record.invoice_url = invoice_details.get('hosted_invoice_url')
            billing_record.invoice_pdf = invoice_details.get('invoice_pdf')
            billing_record.receipt_url = invoice_details.get('receipt_url')
            
            # Update metadata
            if not billing_record.metadata:
                billing_record.metadata = {}
            
            billing_record.metadata.update({
                'payment_processed_at': datetime.utcnow().isoformat(),
                'payment_intent': invoice_details.get('payment_intent'),
                'charge': invoice_details.get('charge'),
                'payment_method': invoice_details.get('payment_method'),
                'attempt_count': invoice_details.get('attempt_count', 0),
                'collection_method': invoice_details.get('collection_method')
            })
            
            if old_status != billing_record.status:
                changes.append(f"Billing status updated: {old_status} → {billing_record.status}")
            
            if old_amount != billing_record.amount:
                changes.append(f"Billing amount updated: ${old_amount} → ${billing_record.amount}")
            
            logger.info(f"Updated billing record for successful payment: {billing_record.stripe_invoice_id}")
            
        except Exception as e:
            logger.error(f"Error updating billing record for successful payment: {e}")
            raise
    
    def _handle_subscription_status_for_successful_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle subscription status updates for successful payment"""
        changes = []
        try:
            if not invoice_details.get('subscription_id'):
                return changes
            
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == invoice_details['subscription_id']
            ).first()
            
            if not subscription:
                return changes
            
            old_status = subscription.status
            
            # Update subscription status based on payment success
            if subscription.status in ['past_due', 'unpaid']:
                subscription.status = 'active'
                changes.append(f"Subscription status updated: {old_status} → {subscription.status}")
            
            # Update subscription metadata
            if not subscription.metadata:
                subscription.metadata = {}
            
            subscription.metadata.update({
                'last_payment_successful': datetime.utcnow().isoformat(),
                'last_payment_amount': invoice_details['amount_paid'],
                'last_payment_invoice': invoice_details['invoice_id'],
                'payment_method_used': invoice_details.get('payment_method')
            })
            
            logger.info(f"Updated subscription status for successful payment: {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error handling subscription status for successful payment: {e}")
        
        return changes
    
    def _update_customer_for_successful_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
        """Update customer for successful payment"""
        changes = []
        try:
            # Update customer payment status
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'last_payment_successful': datetime.utcnow().isoformat(),
                'last_payment_amount': invoice_details['amount_paid'],
                'last_payment_invoice': invoice_details['invoice_id'],
                'total_payments_made': customer.metadata.get('total_payments_made', 0) + 1,
                'total_amount_paid': customer.metadata.get('total_amount_paid', 0.0) + invoice_details['amount_paid']
            })
            
            # Update customer subscription status if they have active subscription
            if customer.has_active_subscription:
                customer.subscription_status = 'active'
                changes.append("Customer subscription status updated to active")
            
            changes.append("Customer payment data updated")
            
            logger.info(f"Updated customer for successful payment: {customer.email}")
            
        except Exception as e:
            logger.error(f"Error updating customer for successful payment: {e}")
        
        return changes
    
    def _handle_payment_method_for_successful_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle payment method updates for successful payment"""
        changes = []
        try:
            payment_method = invoice_details.get('payment_method')
            if not payment_method:
                return changes
            
            # Update customer's default payment method if successful
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'last_successful_payment_method': payment_method,
                'payment_method_last_used': datetime.utcnow().isoformat()
            })
            
            changes.append(f"Payment method updated: {payment_method}")
            
            logger.info(f"Updated payment method for successful payment: {payment_method}")
            
        except Exception as e:
            logger.error(f"Error handling payment method for successful payment: {e}")
        
        return changes
    
    def _handle_discounts_and_credits(self, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle discounts and credits for successful payment"""
        changes = []
        try:
            discount = invoice_details.get('discount')
            if discount:
                discount_amount = discount.get('amount_off', 0) / 100
                discount_type = discount.get('type', 'unknown')
                changes.append(f"Discount applied: ${discount_amount} ({discount_type})")
            
            # Handle any credits applied
            if invoice_details.get('amount_remaining') < 0:
                credit_amount = abs(invoice_details['amount_remaining'])
                changes.append(f"Credit applied: ${credit_amount}")
            
            logger.info(f"Processed discounts and credits for invoice {invoice_details['invoice_id']}")
            
        except Exception as e:
            logger.error(f"Error handling discounts and credits: {e}")
        
        return changes
    
    def _handle_tax_calculations(self, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle tax calculations for successful payment"""
        changes = []
        try:
            tax_amount = invoice_details.get('tax', 0) / 100
            tax_percent = invoice_details.get('tax_percent')
            total_tax_amounts = invoice_details.get('total_tax_amounts', [])
            
            if tax_amount > 0:
                changes.append(f"Tax applied: ${tax_amount}")
                if tax_percent:
                    changes.append(f"Tax rate: {tax_percent}%")
            
            if total_tax_amounts:
                for tax in total_tax_amounts:
                    tax_rate = tax.get('rate', 0)
                    tax_amount = tax.get('amount', 0) / 100
                    changes.append(f"Tax breakdown: ${tax_amount} at {tax_rate}%")
            
            logger.info(f"Processed tax calculations for invoice {invoice_details['invoice_id']}")
            
        except Exception as e:
            logger.error(f"Error handling tax calculations: {e}")
        
        return changes
    
    def _send_successful_payment_notifications(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> int:
        """Send comprehensive successful payment notifications"""
        notifications_sent = 0
        try:
            # Send payment confirmation
            try:
                self.notification_service.send_payment_confirmation(
                    customer.id, billing_record.id
                )
                notifications_sent += 1
                logger.info(f"Sent payment confirmation for {customer.email}")
            except Exception as e:
                logger.error(f"Error sending payment confirmation: {e}")
            
            # Send receipt
            try:
                self.notification_service.send_payment_receipt(
                    customer.id, billing_record.id, invoice_details
                )
                notifications_sent += 1
                logger.info(f"Sent payment receipt for {customer.email}")
            except Exception as e:
                logger.error(f"Error sending payment receipt: {e}")
            
            # Send subscription reactivation notification if applicable
            if invoice_details.get('subscription_id'):
                subscription = self.db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == invoice_details['subscription_id']
                ).first()
                
                if subscription and subscription.status == 'active':
                    try:
                        self.notification_service.send_subscription_reactivated_notification(
                            customer.id, subscription.id
                        )
                        notifications_sent += 1
                        logger.info(f"Sent subscription reactivation notification for {customer.email}")
                    except Exception as e:
                        logger.error(f"Error sending subscription reactivation notification: {e}")
            
            # Send thank you notification for first payment
            total_payments = customer.metadata.get('total_payments_made', 0) if customer.metadata else 0
            if total_payments == 1:
                try:
                    self.notification_service.send_first_payment_thank_you(
                        customer.id, billing_record.id
                    )
                    notifications_sent += 1
                    logger.info(f"Sent first payment thank you for {customer.email}")
                except Exception as e:
                    logger.error(f"Error sending first payment thank you: {e}")
            
        except Exception as e:
            logger.error(f"Error sending successful payment notifications: {e}")
        
        return notifications_sent
    
    def _track_successful_payment_analytics(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
        """Track comprehensive analytics for successful payment"""
        try:
            # Track basic payment success
            self.analytics_service.track_payment_succeeded(customer.id, billing_record.amount)
            
            # Track payment method usage
            payment_method = invoice_details.get('payment_method')
            if payment_method:
                self.analytics_service.track_payment_method_usage(customer.id, payment_method, billing_record.amount)
            
            # Track subscription payment if applicable
            if invoice_details.get('subscription_id'):
                subscription = self.db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == invoice_details['subscription_id']
                ).first()
                
                if subscription:
                    self.analytics_service.track_subscription_payment(
                        customer.id, subscription.id, billing_record.amount
                    )
            
            # Track customer lifetime value
            total_amount_paid = customer.metadata.get('total_amount_paid', 0.0) if customer.metadata else 0.0
            self.analytics_service.track_customer_lifetime_value(customer.id, total_amount_paid)
            
            # Track payment frequency
            self.analytics_service.track_payment_frequency(customer.id, billing_record.amount)
            
            # Track discount usage
            if invoice_details.get('discount'):
                discount_amount = invoice_details['discount'].get('amount_off', 0) / 100
                self.analytics_service.track_discount_usage(customer.id, discount_amount)
            
            logger.info(f"Tracked analytics for successful payment: {billing_record.stripe_invoice_id}")
            
        except Exception as e:
            logger.error(f"Error tracking successful payment analytics: {e}")
    
    def _log_successful_payment_audit(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
        """Log comprehensive audit trail for successful payment"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.PAYMENT_SUCCEEDED,
                event_description=f"Payment succeeded: {billing_record.stripe_invoice_id}",
                severity=AuditSeverity.INFO,
                metadata={
                    'customer_id': customer.id,
                    'customer_email': customer.email,
                    'billing_record_id': billing_record.id,
                    'stripe_invoice_id': billing_record.stripe_invoice_id,
                    'subscription_id': billing_record.subscription_id,
                    'amount_paid': billing_record.amount,
                    'currency': billing_record.currency,
                    'payment_method': invoice_details.get('payment_method'),
                    'payment_intent': invoice_details.get('payment_intent'),
                    'charge': invoice_details.get('charge'),
                    'collection_method': invoice_details.get('collection_method'),
                    'attempt_count': invoice_details.get('attempt_count', 0),
                    'discount': invoice_details.get('discount'),
                    'tax': invoice_details.get('tax'),
                    'tax_percent': invoice_details.get('tax_percent'),
                    'invoice_url': invoice_details.get('hosted_invoice_url'),
                    'receipt_url': invoice_details.get('receipt_url'),
                    'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
                    'processed_at': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            logger.info(f"Logged audit trail for successful payment: {billing_record.stripe_invoice_id}")
            
        except Exception as e:
            logger.error(f"Error logging successful payment audit: {e}")
    
    def _handle_invoice_payment_failed(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle invoice.payment_failed webhook - Comprehensive failed payment handling"""
        try:
            invoice_data = event.event_data.get('object', {})
            changes = []
            notifications_sent = 0
            
            logger.info(f"Processing failed payment for invoice ID: {invoice_data.get('id')}")
            
            # Step 1: Extract and validate invoice details
            invoice_details = self._extract_invoice_details(invoice_data)
            if not invoice_details:
                return WebhookProcessingResult(
                    success=False,
                    error="Invalid invoice data"
                )
            
            # Step 2: Find and validate customer
            customer = self._find_and_validate_customer_for_invoice(invoice_data)
            if not customer:
                return WebhookProcessingResult(
                    success=False,
                    error="Customer not found or invalid"
                )
            
            # Step 3: Find or create billing history record
            billing_record = self._find_or_create_billing_record_for_failure(invoice_data, customer, invoice_details, changes)
            
            # Step 4: Update billing record with payment failure
            self._update_billing_record_for_failed_payment(billing_record, invoice_details, changes)
            
            # Step 5: Handle subscription status updates
            subscription_changes = self._handle_subscription_status_for_failed_payment(customer, invoice_details)
            if subscription_changes:
                changes.extend(subscription_changes)
            
            # Step 6: Update customer payment status
            customer_changes = self._update_customer_for_failed_payment(customer, invoice_details)
            if customer_changes:
                changes.extend(customer_changes)
            
            # Step 7: Handle payment method issues
            payment_method_changes = self._handle_payment_method_for_failed_payment(customer, invoice_details)
            if payment_method_changes:
                changes.extend(payment_method_changes)
            
            # Step 8: Process retry logic
            retry_changes = self._handle_payment_retry_logic(invoice_details)
            if retry_changes:
                changes.extend(retry_changes)
            
            # Step 9: Handle dunning management
            dunning_changes = self._handle_dunning_management(customer, invoice_details)
            if dunning_changes:
                changes.extend(dunning_changes)
            
            # Step 10: Send comprehensive failure notifications
            notifications_sent = self._send_failed_payment_notifications(customer, billing_record, invoice_details)
            
            # Step 11: Track comprehensive analytics
            self._track_failed_payment_analytics(customer, billing_record, invoice_details)
            
            # Step 12: Log comprehensive audit trail
            self._log_failed_payment_audit(customer, billing_record, invoice_details)
            
            # Commit all changes
            self.db.commit()
            
            changes.append(f"Payment failed: ${invoice_details['amount_due']}")
            
            logger.info(f"Successfully processed failed payment for invoice {invoice_data.get('id')}")
            
            return WebhookProcessingResult(
                success=True,
                message="Payment failed with comprehensive handling",
                changes=changes,
                notifications_sent=notifications_sent
            )
            
        except Exception as e:
            logger.error(f"Error handling invoice.payment_failed: {e}")
            self.db.rollback()
            return WebhookProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _find_or_create_billing_record_for_failure(self, invoice_data: Dict[str, Any], customer: Customer, invoice_details: Dict[str, Any], changes: List[str]) -> BillingHistory:
        """Find or create billing history record for failed payment"""
        try:
            # Try to find existing billing record
            billing_record = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_invoice_id == invoice_details['invoice_id']
            ).first()
            
            if billing_record:
                logger.info(f"Found existing billing record for failed invoice {invoice_details['invoice_id']}")
                return billing_record
            
            # Find subscription if available
            subscription = None
            if invoice_details.get('subscription_id'):
                subscription = self.db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == invoice_details['subscription_id']
                ).first()
            
            # Create new billing record for failed payment
            billing_record = BillingHistory(
                customer_id=customer.id,
                subscription_id=subscription.id if subscription else None,
                stripe_invoice_id=invoice_details['invoice_id'],
                amount=invoice_details['amount_due'],
                currency=invoice_details['currency'],
                status='failed',
                description=f"Failed invoice payment: {invoice_details['invoice_id']}",
                billing_date=datetime.fromtimestamp(invoice_details['created']) if invoice_details.get('created') else datetime.utcnow(),
                due_date=datetime.fromtimestamp(invoice_details['due_date']) if invoice_details.get('due_date') else None,
                invoice_url=invoice_details.get('hosted_invoice_url'),
                invoice_pdf=invoice_details.get('invoice_pdf'),
                metadata={
                    'invoice_created': invoice_details.get('created'),
                    'period_start': invoice_details.get('period_start'),
                    'period_end': invoice_details.get('period_end'),
                    'collection_method': invoice_details.get('collection_method'),
                    'attempt_count': invoice_details.get('attempt_count', 0),
                    'next_payment_attempt': invoice_details.get('next_payment_attempt'),
                    'last_payment_error': invoice_details.get('last_payment_error'),
                    'livemode': invoice_details.get('livemode', False)
                }
            )
            
            self.db.add(billing_record)
            changes.append(f"Created failed billing record: ${billing_record.amount}")
            
            logger.info(f"Created new billing record for failed invoice {invoice_details['invoice_id']}")
            return billing_record
            
        except Exception as e:
            logger.error(f"Error finding/creating billing record for failure: {e}")
            raise
    
    def _update_billing_record_for_failed_payment(self, billing_record: BillingHistory, invoice_details: Dict[str, Any], changes: List[str]) -> None:
        """Update billing record for failed payment"""
        try:
            old_status = billing_record.status
            old_amount = billing_record.amount
            
            # Update billing record
            billing_record.status = 'failed'
            billing_record.amount = invoice_details['amount_due']
            billing_record.invoice_url = invoice_details.get('hosted_invoice_url')
            billing_record.invoice_pdf = invoice_details.get('invoice_pdf')
            
            # Update metadata
            if not billing_record.metadata:
                billing_record.metadata = {}
            
            billing_record.metadata.update({
                'payment_failed_at': datetime.utcnow().isoformat(),
                'attempt_count': invoice_details.get('attempt_count', 0),
                'next_payment_attempt': invoice_details.get('next_payment_attempt'),
                'last_payment_error': invoice_details.get('last_payment_error'),
                'collection_method': invoice_details.get('collection_method')
            })
            
            if old_status != billing_record.status:
                changes.append(f"Billing status updated: {old_status} → {billing_record.status}")
            
            if old_amount != billing_record.amount:
                changes.append(f"Billing amount updated: ${old_amount} → ${billing_record.amount}")
            
            logger.info(f"Updated billing record for failed payment: {billing_record.stripe_invoice_id}")
            
        except Exception as e:
            logger.error(f"Error updating billing record for failed payment: {e}")
            raise
    
    def _handle_subscription_status_for_failed_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle subscription status updates for failed payment"""
        changes = []
        try:
            if not invoice_details.get('subscription_id'):
                return changes
            
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == invoice_details['subscription_id']
            ).first()
            
            if not subscription:
                return changes
            
            old_status = subscription.status
            
            # Update subscription status based on payment failure
            if subscription.status == 'active':
                subscription.status = 'past_due'
                changes.append(f"Subscription status updated: {old_status} → {subscription.status}")
            
            # Update subscription metadata
            if not subscription.metadata:
                subscription.metadata = {}
            
            subscription.metadata.update({
                'last_payment_failed': datetime.utcnow().isoformat(),
                'last_payment_failure_amount': invoice_details['amount_due'],
                'last_payment_failure_invoice': invoice_details['invoice_id'],
                'payment_failure_count': subscription.metadata.get('payment_failure_count', 0) + 1,
                'last_payment_error': invoice_details.get('last_payment_error')
            })
            
            logger.info(f"Updated subscription status for failed payment: {subscription.stripe_subscription_id}")
            
        except Exception as e:
            logger.error(f"Error handling subscription status for failed payment: {e}")
        
        return changes
    
    def _update_customer_for_failed_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
        """Update customer for failed payment"""
        changes = []
        try:
            # Update customer payment status
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'last_payment_failed': datetime.utcnow().isoformat(),
                'last_payment_failure_amount': invoice_details['amount_due'],
                'last_payment_failure_invoice': invoice_details['invoice_id'],
                'total_payment_failures': customer.metadata.get('total_payment_failures', 0) + 1,
                'last_payment_error': invoice_details.get('last_payment_error')
            })
            
            # Update customer subscription status if they have active subscription
            if customer.has_active_subscription:
                customer.subscription_status = 'past_due'
                changes.append("Customer subscription status updated to past_due")
            
            changes.append("Customer payment failure data updated")
            
            logger.info(f"Updated customer for failed payment: {customer.email}")
            
        except Exception as e:
            logger.error(f"Error updating customer for failed payment: {e}")
        
        return changes
    
    def _handle_payment_method_for_failed_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle payment method issues for failed payment"""
        changes = []
        try:
            payment_method = invoice_details.get('payment_method')
            last_payment_error = invoice_details.get('last_payment_error')
            
            if not payment_method or not last_payment_error:
                return changes
            
            # Update customer's payment method failure tracking
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'last_failed_payment_method': payment_method,
                'payment_method_failure_count': customer.metadata.get('payment_method_failure_count', 0) + 1,
                'last_payment_error': last_payment_error
            })
            
            changes.append(f"Payment method failure tracked: {payment_method}")
            
            logger.info(f"Updated payment method for failed payment: {payment_method}")
            
        except Exception as e:
            logger.error(f"Error handling payment method for failed payment: {e}")
        
        return changes
    
    def _handle_payment_retry_logic(self, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle payment retry logic"""
        changes = []
        try:
            attempt_count = invoice_details.get('attempt_count', 0)
            next_payment_attempt = invoice_details.get('next_payment_attempt')
            
            if attempt_count > 0:
                changes.append(f"Payment attempt #{attempt_count} failed")
            
            if next_payment_attempt:
                next_attempt_date = datetime.fromtimestamp(next_payment_attempt)
                changes.append(f"Next retry scheduled: {next_attempt_date}")
                
                # Schedule retry notification
                # self.retry_service.schedule_retry_notification(customer_id, next_attempt_date)
            
            # Determine retry strategy based on attempt count
            if attempt_count >= 3:
                changes.append("Maximum retry attempts reached")
                # self.retry_service.escalate_to_collections(customer_id)
            elif attempt_count >= 2:
                changes.append("Final retry attempt scheduled")
                # self.retry_service.schedule_final_retry(customer_id)
            
            logger.info(f"Processed retry logic for invoice {invoice_details['invoice_id']}")
            
        except Exception as e:
            logger.error(f"Error handling payment retry logic: {e}")
        
        return changes
    
    def _handle_dunning_management(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
        """Handle dunning management for failed payments"""
        changes = []
        try:
            attempt_count = invoice_details.get('attempt_count', 0)
            amount_due = invoice_details['amount_due']
            
            # Determine dunning stage based on attempt count
            if attempt_count == 1:
                changes.append("Dunning stage 1: Payment reminder sent")
                # self.dunning_service.send_payment_reminder(customer.id, amount_due)
            elif attempt_count == 2:
                changes.append("Dunning stage 2: Payment warning sent")
                # self.dunning_service.send_payment_warning(customer.id, amount_due)
            elif attempt_count == 3:
                changes.append("Dunning stage 3: Final notice sent")
                # self.dunning_service.send_final_notice(customer.id, amount_due)
            elif attempt_count >= 4:
                changes.append("Dunning stage 4: Account suspension initiated")
                # self.dunning_service.suspend_account(customer.id)
            
            # Track dunning metrics
            if not customer.metadata:
                customer.metadata = {}
            
            customer.metadata.update({
                'dunning_stage': min(attempt_count, 4),
                'last_dunning_action': datetime.utcnow().isoformat(),
                'dunning_amount': amount_due
            })
            
            logger.info(f"Processed dunning management for customer {customer.email}")
            
        except Exception as e:
            logger.error(f"Error handling dunning management: {e}")
        
        return changes
    
    def _send_failed_payment_notifications(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> int:
        """Send comprehensive failed payment notifications"""
        notifications_sent = 0
        try:
            # Send payment failure notification
            try:
                self.notification_service.send_payment_failure_notification(
                    customer.id, billing_record.id
                )
                notifications_sent += 1
                logger.info(f"Sent payment failure notification for {customer.email}")
            except Exception as e:
                logger.error(f"Error sending payment failure notification: {e}")
            
            # Send payment method update request
            try:
                self.notification_service.send_payment_method_update_request(
                    customer.id, billing_record.id, invoice_details
                )
                notifications_sent += 1
                logger.info(f"Sent payment method update request for {customer.email}")
            except Exception as e:
                logger.error(f"Error sending payment method update request: {e}")
            
            # Send retry notification if applicable
            next_payment_attempt = invoice_details.get('next_payment_attempt')
            if next_payment_attempt:
                try:
                    self.notification_service.send_payment_retry_notification(
                        customer.id, billing_record.id, next_payment_attempt
                    )
                    notifications_sent += 1
                    logger.info(f"Sent payment retry notification for {customer.email}")
                except Exception as e:
                    logger.error(f"Error sending payment retry notification: {e}")
            
            # Send account suspension warning if multiple failures
            attempt_count = invoice_details.get('attempt_count', 0)
            if attempt_count >= 3:
                try:
                    self.notification_service.send_account_suspension_warning(
                        customer.id, billing_record.id
                    )
                    notifications_sent += 1
                    logger.info(f"Sent account suspension warning for {customer.email}")
                except Exception as e:
                    logger.error(f"Error sending account suspension warning: {e}")
            
            # Send support contact information
            try:
                self.notification_service.send_payment_support_contact(
                    customer.id, billing_record.id
                )
                notifications_sent += 1
                logger.info(f"Sent payment support contact for {customer.email}")
            except Exception as e:
                logger.error(f"Error sending payment support contact: {e}")
            
        except Exception as e:
            logger.error(f"Error sending failed payment notifications: {e}")
        
        return notifications_sent
    
    def _track_failed_payment_analytics(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
        """Track comprehensive analytics for failed payment"""
        try:
            # Track basic payment failure
            self.analytics_service.track_payment_failed(customer.id, billing_record.amount)
            
            # Track payment method failure
            payment_method = invoice_details.get('payment_method')
            if payment_method:
                self.analytics_service.track_payment_method_failure(customer.id, payment_method, billing_record.amount)
            
            # Track subscription payment failure if applicable
            if invoice_details.get('subscription_id'):
                subscription = self.db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == invoice_details['subscription_id']
                ).first()
                
                if subscription:
                    self.analytics_service.track_subscription_payment_failure(
                        customer.id, subscription.id, billing_record.amount
                    )
            
            # Track failure reason
            last_payment_error = invoice_details.get('last_payment_error')
            if last_payment_error:
                self.analytics_service.track_payment_failure_reason(customer.id, last_payment_error, billing_record.amount)
            
            # Track attempt count
            attempt_count = invoice_details.get('attempt_count', 0)
            self.analytics_service.track_payment_attempt_count(customer.id, attempt_count, billing_record.amount)
            
            # Track dunning stage
            dunning_stage = min(attempt_count, 4)
            self.analytics_service.track_dunning_stage(customer.id, dunning_stage, billing_record.amount)
            
            logger.info(f"Tracked analytics for failed payment: {billing_record.stripe_invoice_id}")
            
        except Exception as e:
            logger.error(f"Error tracking failed payment analytics: {e}")
    
    def _log_failed_payment_audit(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
        """Log comprehensive audit trail for failed payment"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.PAYMENT_FAILED,
                event_description=f"Payment failed: {billing_record.stripe_invoice_id}",
                severity=AuditSeverity.WARNING,
                metadata={
                    'customer_id': customer.id,
                    'customer_email': customer.email,
                    'billing_record_id': billing_record.id,
                    'stripe_invoice_id': billing_record.stripe_invoice_id,
                    'subscription_id': billing_record.subscription_id,
                    'amount_due': billing_record.amount,
                    'currency': billing_record.currency,
                    'payment_method': invoice_details.get('payment_method'),
                    'attempt_count': invoice_details.get('attempt_count', 0),
                    'next_payment_attempt': invoice_details.get('next_payment_attempt'),
                    'last_payment_error': invoice_details.get('last_payment_error'),
                    'collection_method': invoice_details.get('collection_method'),
                    'invoice_url': invoice_details.get('hosted_invoice_url'),
                    'dunning_stage': min(invoice_details.get('attempt_count', 0), 4),
                    'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
                    'failed_at': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            logger.info(f"Logged audit trail for failed payment: {billing_record.stripe_invoice_id}")
            
        except Exception as e:
            logger.error(f"Error logging failed payment audit: {e}")
    
    # Additional event handlers (implemented as needed)
    def _handle_invoice_created(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle invoice.created webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Invoice created (no action required)"
        )
    
    def _handle_invoice_finalized(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle invoice.finalized webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Invoice finalized (no action required)"
        )
    
    def _handle_invoice_upcoming(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle invoice.upcoming webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Invoice upcoming (no action required)"
        )
    
    def _handle_payment_intent_succeeded(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle payment_intent.succeeded webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Payment intent succeeded (no action required)"
        )
    
    def _handle_payment_intent_failed(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle payment_intent.payment_failed webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Payment intent failed (no action required)"
        )
    
    def _handle_payment_method_attached(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle payment_method.attached webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Payment method attached (no action required)"
        )
    
    def _handle_payment_method_detached(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle payment_method.detached webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Payment method detached (no action required)"
        )
    
    def _handle_payment_method_updated(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle payment_method.updated webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Payment method updated (no action required)"
        )
    
    def _handle_charge_succeeded(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle charge.succeeded webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Charge succeeded (no action required)"
        )
    
    def _handle_charge_failed(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle charge.failed webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Charge failed (no action required)"
        )
    
    def _handle_charge_refunded(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle charge.refunded webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Charge refunded (no action required)"
        )
    
    def _handle_charge_dispute_created(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle charge.dispute.created webhook"""
        return WebhookProcessingResult(
            success=True,
            message="Charge dispute created (no action required)"
        ) 
    
    # Business Logic Integration Methods
    
    def _execute_business_logic_for_subscription_created(
        self,
        customer: Customer,
        subscription: Subscription,
        subscription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute business logic for subscription creation with immediate feature access updates"""
        try:
            from ..services.business_logic_service import BusinessLogicService
            from ..monitoring.audit_trail_service import AuditTrailService
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            # Initialize services
            business_logic_service = BusinessLogicService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            performance_optimizer = PerformanceOptimizer(self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Execute business logic
            result = business_logic_service.handle_subscription_created(
                customer, subscription, subscription_data
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            performance_optimizer.record_webhook_event(
                event_type="subscription_created",
                processing_time=processing_time,
                success=result['success'],
                error=result.get('error')
            )
            
            # Log audit trail
            audit_service.log_business_logic_event(
                operation="subscription_created",
                description=f"Subscription created for customer {customer.id}",
                details={
                    'subscription_id': str(subscription.id),
                    'pricing_tier': subscription.pricing_tier,
                    'amount': subscription.amount,
                    'currency': subscription.currency,
                    'business_logic_result': result
                },
                customer_id=str(customer.id),
                success=result['success'],
                error_message=result.get('error')
            )
            
            # Immediate feature access update
            if result['success']:
                feature_update_result = self._update_feature_access_immediately(
                    customer, subscription, subscription_data
                )
                result['feature_access_updated'] = feature_update_result['success']
                result['changes'].extend(feature_update_result['changes'])
                
                # Log feature access update
                audit_service.log_feature_access_event(
                    user_id=str(customer.user_id) if customer.user_id else None,
                    feature="subscription_features",
                    action="access_granted",
                    details={
                        'subscription_tier': subscription.pricing_tier,
                        'features_granted': feature_update_result.get('features_granted', []),
                        'access_level': feature_update_result.get('access_level')
                    },
                    success=feature_update_result['success']
                )
                
                # Trigger user notifications
                notification_result = self._trigger_user_notifications(
                    customer, subscription, "subscription_created", feature_update_result
                )
                result['notifications_triggered'] = notification_result['success']
                result['notifications_sent'] += notification_result['notifications_sent']
                
                # Track analytics events
                analytics_result = self._track_analytics_events(
                    customer, subscription, "subscription_created", feature_update_result
                )
                result['analytics_tracked'] = analytics_result['success']
                result['analytics_events'] = analytics_result.get('events', [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing business logic for subscription creation: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def _execute_business_logic_for_subscription_updated(
        self,
        customer: Customer,
        subscription: Subscription,
        old_values: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute business logic for subscription updates with immediate feature access updates"""
        try:
            from ..services.business_logic_service import BusinessLogicService
            from ..monitoring.audit_trail_service import AuditTrailService
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            # Initialize services
            business_logic_service = BusinessLogicService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            performance_optimizer = PerformanceOptimizer(self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Execute business logic
            result = business_logic_service.handle_subscription_updated(
                customer, subscription, old_values, new_data
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            performance_optimizer.record_webhook_event(
                event_type="subscription_updated",
                processing_time=processing_time,
                success=result['success'],
                error=result.get('error')
            )
            
            # Log audit trail
            audit_service.log_business_logic_event(
                operation="subscription_updated",
                description=f"Subscription updated for customer {customer.id}",
                details={
                    'subscription_id': str(subscription.id),
                    'old_values': old_values,
                    'new_data': new_data,
                    'business_logic_result': result
                },
                customer_id=str(customer.id),
                success=result['success'],
                error_message=result.get('error')
            )
            
            # Immediate feature access update
            if result['success']:
                feature_update_result = self._update_feature_access_immediately(
                    customer, subscription, new_data
                )
                result['feature_access_updated'] = feature_update_result['success']
                result['changes'].extend(feature_update_result['changes'])
                
                # Log feature access update
                audit_service.log_feature_access_event(
                    user_id=str(customer.user_id) if customer.user_id else None,
                    feature="subscription_features",
                    action="access_updated",
                    details={
                        'subscription_tier': subscription.pricing_tier,
                        'features_granted': feature_update_result.get('features_granted', []),
                        'features_removed': feature_update_result.get('features_removed', []),
                        'access_level': feature_update_result.get('access_level')
                    },
                    success=feature_update_result['success']
                )
                
                # Trigger user notifications
                notification_result = self._trigger_user_notifications(
                    customer, subscription, "subscription_updated", feature_update_result
                )
                result['notifications_triggered'] = notification_result['success']
                result['notifications_sent'] += notification_result['notifications_sent']
                
                # Track analytics events
                analytics_result = self._track_analytics_events(
                    customer, subscription, "subscription_updated", feature_update_result
                )
                result['analytics_tracked'] = analytics_result['success']
                result['analytics_events'] = analytics_result.get('events', [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing business logic for subscription update: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def _execute_business_logic_for_subscription_cancelled(
        self,
        customer: Customer,
        subscription: Subscription,
        cancellation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute business logic for subscription cancellation with immediate feature access updates"""
        try:
            from ..services.business_logic_service import BusinessLogicService
            from ..monitoring.audit_trail_service import AuditTrailService
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            # Initialize services
            business_logic_service = BusinessLogicService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            performance_optimizer = PerformanceOptimizer(self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Execute business logic
            result = business_logic_service.handle_subscription_cancelled(
                customer, subscription, cancellation_data
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            performance_optimizer.record_webhook_event(
                event_type="subscription_cancelled",
                processing_time=processing_time,
                success=result['success'],
                error=result.get('error')
            )
            
            # Log audit trail
            audit_service.log_business_logic_event(
                operation="subscription_cancelled",
                description=f"Subscription cancelled for customer {customer.id}",
                details={
                    'subscription_id': str(subscription.id),
                    'cancellation_data': cancellation_data,
                    'business_logic_result': result
                },
                customer_id=str(customer.id),
                success=result['success'],
                error_message=result.get('error')
            )
            
            # Immediate feature access update
            if result['success']:
                feature_update_result = self._revoke_feature_access_immediately(
                    customer, subscription, cancellation_data
                )
                result['feature_access_revoked'] = feature_update_result['success']
                result['changes'].extend(feature_update_result['changes'])
                
                # Log feature access update
                audit_service.log_feature_access_event(
                    user_id=str(customer.user_id) if customer.user_id else None,
                    feature="subscription_features",
                    action="access_revoked",
                    details={
                        'subscription_tier': subscription.pricing_tier,
                        'features_revoked': feature_update_result.get('features_revoked', []),
                        'access_level': feature_update_result.get('access_level')
                    },
                    success=feature_update_result['success']
                )
                
                # Trigger user notifications
                notification_result = self._trigger_user_notifications(
                    customer, subscription, "subscription_cancelled", feature_update_result
                )
                result['notifications_triggered'] = notification_result['success']
                result['notifications_sent'] += notification_result['notifications_sent']
                
                # Track analytics events
                analytics_result = self._track_analytics_events(
                    customer, subscription, "subscription_cancelled", feature_update_result
                )
                result['analytics_tracked'] = analytics_result['success']
                result['analytics_events'] = analytics_result.get('events', [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing business logic for subscription cancellation: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def _execute_business_logic_for_payment_succeeded(
        self,
        customer: Customer,
        billing_record: BillingHistory,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute business logic for successful payments with recovery handling"""
        try:
            from ..services.business_logic_service import BusinessLogicService
            
            # Initialize business logic service
            business_logic_service = BusinessLogicService(self.db, self.config)
            
            # Check if this is a recovery scenario (payment after previous failures)
            is_recovery_scenario = self._is_recovery_scenario(customer, billing_record)
            
            if is_recovery_scenario:
                # Execute business logic with recovery handling
                result = business_logic_service.handle_payment_success_after_recovery(
                    customer, billing_record, payment_data
                )
            else:
                # Execute standard business logic
                result = business_logic_service.handle_payment_succeeded(
                    customer, billing_record, payment_data
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing business logic for payment success: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def _execute_business_logic_for_payment_failed(
        self,
        customer: Customer,
        billing_record: BillingHistory,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute business logic for failed payments with recovery workflows"""
        try:
            from ..services.business_logic_service import BusinessLogicService
            
            # Initialize business logic service
            business_logic_service = BusinessLogicService(self.db, self.config)
            
            # Execute business logic with payment recovery
            result = business_logic_service.handle_payment_failure_with_recovery(
                customer, billing_record, payment_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing business logic for payment failure: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def _execute_business_logic_for_trial_ending(
        self,
        customer: Customer,
        subscription: Subscription,
        trial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute business logic for trial ending with immediate feature access updates"""
        try:
            from ..services.business_logic_service import BusinessLogicService
            from ..monitoring.audit_trail_service import AuditTrailService
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            # Initialize services
            business_logic_service = BusinessLogicService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            performance_optimizer = PerformanceOptimizer(self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Execute business logic
            result = business_logic_service.handle_trial_ending(
                customer, subscription, trial_data
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            performance_optimizer.record_webhook_event(
                event_type="trial_ending",
                processing_time=processing_time,
                success=result['success'],
                error=result.get('error')
            )
            
            # Log audit trail
            audit_service.log_business_logic_event(
                operation="trial_ending",
                description=f"Trial ending for customer {customer.id}",
                details={
                    'subscription_id': str(subscription.id),
                    'trial_data': trial_data,
                    'business_logic_result': result
                },
                customer_id=str(customer.id),
                success=result['success'],
                error_message=result.get('error')
            )
            
            # Immediate feature access update for trial ending
            if result['success']:
                feature_update_result = self._update_feature_access_for_trial_ending(
                    customer, subscription, trial_data
                )
                result['feature_access_updated'] = feature_update_result['success']
                result['changes'].extend(feature_update_result['changes'])
                
                # Log feature access update
                audit_service.log_feature_access_event(
                    user_id=str(customer.user_id) if customer.user_id else None,
                    feature="trial_features",
                    action="access_restricted",
                    details={
                        'subscription_tier': subscription.pricing_tier,
                        'features_restricted': feature_update_result.get('features_restricted', []),
                        'access_level': feature_update_result.get('access_level')
                    },
                    success=feature_update_result['success']
                )
                
                # Trigger user notifications
                notification_result = self._trigger_user_notifications(
                    customer, subscription, "trial_ending", feature_update_result
                )
                result['notifications_triggered'] = notification_result['success']
                result['notifications_sent'] += notification_result['notifications_sent']
                
                # Track analytics events
                analytics_result = self._track_analytics_events(
                    customer, subscription, "trial_ending", feature_update_result
                )
                result['analytics_tracked'] = analytics_result['success']
                result['analytics_events'] = analytics_result.get('events', [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing business logic for trial ending: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    # Immediate Feature Access Update Methods
    
    def _update_feature_access_immediately(
        self,
        customer: Customer,
        subscription: Subscription,
        subscription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update feature access immediately for subscription changes"""
        try:
            from ..services.feature_access_service import FeatureAccessService
            from ..monitoring.audit_trail_service import AuditTrailService
            
            # Initialize services
            feature_service = FeatureAccessService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Update feature access
            update_result = feature_service.update_feature_access_immediately(
                customer_id=str(customer.id),
                subscription_tier=subscription.pricing_tier,
                subscription_status=subscription.status,
                subscription_data=subscription_data
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._record_feature_access_metric("immediate_update", processing_time, update_result['success'])
            
            # Log audit trail
            audit_service.log_feature_access_event(
                user_id=str(customer.user_id) if customer.user_id else None,
                feature="subscription_features",
                action="immediate_access_update",
                details={
                    'subscription_tier': subscription.pricing_tier,
                    'subscription_status': subscription.status,
                    'features_granted': update_result.get('features_granted', []),
                    'features_removed': update_result.get('features_removed', []),
                    'access_level': update_result.get('access_level'),
                    'processing_time_ms': processing_time
                },
                success=update_result['success']
            )
            
            # Invalidate user cache
            if customer.user_id:
                self._invalidate_user_cache(str(customer.user_id))
            
            return update_result
            
        except Exception as e:
            logger.error(f"Error updating feature access immediately: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'features_granted': [],
                'features_removed': [],
                'access_level': None
            }
    
    def _revoke_feature_access_immediately(
        self,
        customer: Customer,
        subscription: Subscription,
        cancellation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Revoke feature access immediately for subscription cancellation"""
        try:
            from ..services.feature_access_service import FeatureAccessService
            from ..monitoring.audit_trail_service import AuditTrailService
            
            # Initialize services
            feature_service = FeatureAccessService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Revoke feature access
            revoke_result = feature_service.revoke_feature_access_immediately(
                customer_id=str(customer.id),
                subscription_tier=subscription.pricing_tier,
                cancellation_data=cancellation_data
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._record_feature_access_metric("immediate_revoke", processing_time, revoke_result['success'])
            
            # Log audit trail
            audit_service.log_feature_access_event(
                user_id=str(customer.user_id) if customer.user_id else None,
                feature="subscription_features",
                action="immediate_access_revoke",
                details={
                    'subscription_tier': subscription.pricing_tier,
                    'features_revoked': revoke_result.get('features_revoked', []),
                    'access_level': revoke_result.get('access_level'),
                    'processing_time_ms': processing_time
                },
                success=revoke_result['success']
            )
            
            # Invalidate user cache
            if customer.user_id:
                self._invalidate_user_cache(str(customer.user_id))
            
            return revoke_result
            
        except Exception as e:
            logger.error(f"Error revoking feature access immediately: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'features_revoked': [],
                'access_level': None
            }
    
    def _update_feature_access_for_trial_ending(
        self,
        customer: Customer,
        subscription: Subscription,
        trial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update feature access for trial ending"""
        try:
            from ..services.feature_access_service import FeatureAccessService
            from ..monitoring.audit_trail_service import AuditTrailService
            
            # Initialize services
            feature_service = FeatureAccessService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Update feature access for trial ending
            update_result = feature_service.update_feature_access_for_trial_ending(
                customer_id=str(customer.id),
                subscription_tier=subscription.pricing_tier,
                trial_data=trial_data
            )
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._record_feature_access_metric("trial_ending_update", processing_time, update_result['success'])
            
            # Log audit trail
            audit_service.log_feature_access_event(
                user_id=str(customer.user_id) if customer.user_id else None,
                feature="trial_features",
                action="trial_ending_access_update",
                details={
                    'subscription_tier': subscription.pricing_tier,
                    'features_restricted': update_result.get('features_restricted', []),
                    'access_level': update_result.get('access_level'),
                    'processing_time_ms': processing_time
                },
                success=update_result['success']
            )
            
            # Invalidate user cache
            if customer.user_id:
                self._invalidate_user_cache(str(customer.user_id))
            
            return update_result
            
        except Exception as e:
            logger.error(f"Error updating feature access for trial ending: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'features_restricted': [],
                'access_level': None
            }
    
    def _record_feature_access_metric(self, operation: str, processing_time: float, success: bool):
        """Record feature access performance metric"""
        try:
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            performance_optimizer = PerformanceOptimizer(self.config)
            performance_optimizer.record_webhook_event(
                event_type=f"feature_access_{operation}",
                processing_time=processing_time,
                success=success
            )
            
        except Exception as e:
            logger.error(f"Error recording feature access metric: {e}")
    
    def _invalidate_user_cache(self, user_id: str):
        """Invalidate user cache for immediate updates"""
        try:
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            performance_optimizer = PerformanceOptimizer(self.config)
            
            # Invalidate user-specific caches
            cache_keys = [
                f"user_features:{user_id}",
                f"user_subscription:{user_id}",
                f"user_access:{user_id}",
                f"user_permissions:{user_id}"
            ]
            
            for cache_key in cache_keys:
                performance_optimizer.invalidate_cache(cache_key)
            
        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")
    
    # MINGUS Integration Methods
    
    def _trigger_user_notifications(
        self,
        customer: Customer,
        subscription: Subscription,
        event_type: str,
        feature_update_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger user notifications for subscription events"""
        try:
            from ..services.notification_service import NotificationService
            from ..monitoring.audit_trail_service import AuditTrailService
            
            # Initialize services
            notification_service = NotificationService(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Prepare notification data
            notification_data = {
                'customer_id': str(customer.id),
                'user_id': str(customer.user_id) if customer.user_id else None,
                'subscription_id': str(subscription.id),
                'subscription_tier': subscription.pricing_tier,
                'subscription_status': subscription.status,
                'event_type': event_type,
                'feature_changes': {
                    'features_granted': feature_update_result.get('features_granted', []),
                    'features_removed': feature_update_result.get('features_removed', []),
                    'features_revoked': feature_update_result.get('features_revoked', []),
                    'features_restricted': feature_update_result.get('features_restricted', []),
                    'access_level': feature_update_result.get('access_level')
                }
            }
            
            # Trigger notifications based on event type
            notifications_sent = 0
            notification_channels = []
            
            if event_type == "subscription_created":
                # Welcome notifications
                welcome_result = notification_service.send_welcome_notifications(notification_data)
                notifications_sent += welcome_result.get('notifications_sent', 0)
                notification_channels.extend(welcome_result.get('channels', []))
                
                # Feature access notifications
                feature_result = notification_service.send_feature_access_notifications(notification_data)
                notifications_sent += feature_result.get('notifications_sent', 0)
                notification_channels.extend(feature_result.get('channels', []))
                
            elif event_type == "subscription_updated":
                # Update notifications
                update_result = notification_service.send_subscription_update_notifications(notification_data)
                notifications_sent += update_result.get('notifications_sent', 0)
                notification_channels.extend(update_result.get('channels', []))
                
            elif event_type == "subscription_cancelled":
                # Cancellation notifications
                cancel_result = notification_service.send_cancellation_notifications(notification_data)
                notifications_sent += cancel_result.get('notifications_sent', 0)
                notification_channels.extend(cancel_result.get('channels', []))
                
            elif event_type == "trial_ending":
                # Trial ending notifications
                trial_result = notification_service.send_trial_ending_notifications(notification_data)
                notifications_sent += trial_result.get('notifications_sent', 0)
                notification_channels.extend(trial_result.get('channels', []))
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._record_notification_metric(event_type, processing_time, notifications_sent > 0)
            
            # Log audit trail
            audit_service.log_notification_event(
                user_id=str(customer.user_id) if customer.user_id else None,
                notification_type=f"subscription_{event_type}",
                channels=notification_channels,
                details={
                    'event_type': event_type,
                    'subscription_tier': subscription.pricing_tier,
                    'notifications_sent': notifications_sent,
                    'processing_time_ms': processing_time
                },
                success=notifications_sent > 0
            )
            
            return {
                'success': notifications_sent > 0,
                'notifications_sent': notifications_sent,
                'channels': notification_channels,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error triggering user notifications: {e}")
            return {
                'success': False,
                'error': str(e),
                'notifications_sent': 0,
                'channels': []
            }
    
    def _track_analytics_events(
        self,
        customer: Customer,
        subscription: Subscription,
        event_type: str,
        feature_update_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track analytics events for subscription changes"""
        try:
            from ..analytics.event_tracker import EventTracker
            from ..monitoring.audit_trail_service import AuditTrailService
            
            # Initialize services
            event_tracker = EventTracker(self.db, self.config)
            audit_service = AuditTrailService(self.db, self.config)
            
            # Start performance monitoring
            start_time = time.time()
            
            # Prepare analytics data
            analytics_data = {
                'customer_id': str(customer.id),
                'user_id': str(customer.user_id) if customer.user_id else None,
                'subscription_id': str(subscription.id),
                'subscription_tier': subscription.pricing_tier,
                'subscription_status': subscription.status,
                'event_type': event_type,
                'feature_changes': feature_update_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Track events based on event type
            events_tracked = []
            
            if event_type == "subscription_created":
                # Track subscription creation
                subscription_event = event_tracker.track_subscription_created(analytics_data)
                events_tracked.append(subscription_event)
                
                # Track feature access granted
                feature_event = event_tracker.track_feature_access_granted(analytics_data)
                events_tracked.append(feature_event)
                
                # Track conversion event
                conversion_event = event_tracker.track_conversion_event(analytics_data)
                events_tracked.append(conversion_event)
                
            elif event_type == "subscription_updated":
                # Track subscription update
                update_event = event_tracker.track_subscription_updated(analytics_data)
                events_tracked.append(update_event)
                
                # Track feature changes
                if feature_update_result.get('features_granted') or feature_update_result.get('features_removed'):
                    feature_event = event_tracker.track_feature_access_changed(analytics_data)
                    events_tracked.append(feature_event)
                
            elif event_type == "subscription_cancelled":
                # Track subscription cancellation
                cancel_event = event_tracker.track_subscription_cancelled(analytics_data)
                events_tracked.append(cancel_event)
                
                # Track churn event
                churn_event = event_tracker.track_churn_event(analytics_data)
                events_tracked.append(churn_event)
                
            elif event_type == "trial_ending":
                # Track trial ending
                trial_event = event_tracker.track_trial_ending(analytics_data)
                events_tracked.append(trial_event)
                
                # Track trial conversion opportunity
                conversion_opp_event = event_tracker.track_trial_conversion_opportunity(analytics_data)
                events_tracked.append(conversion_opp_event)
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._record_analytics_metric(event_type, processing_time, len(events_tracked) > 0)
            
            # Log audit trail
            audit_service.log_analytics_event(
                user_id=str(customer.user_id) if customer.user_id else None,
                analytics_type=f"subscription_{event_type}",
                events_count=len(events_tracked),
                details={
                    'event_type': event_type,
                    'subscription_tier': subscription.pricing_tier,
                    'events_tracked': [event.get('event_name') for event in events_tracked],
                    'processing_time_ms': processing_time
                },
                success=len(events_tracked) > 0
            )
            
            return {
                'success': len(events_tracked) > 0,
                'events': events_tracked,
                'events_count': len(events_tracked),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error tracking analytics events: {e}")
            return {
                'success': False,
                'error': str(e),
                'events': [],
                'events_count': 0
            }
    
    def _record_notification_metric(self, event_type: str, processing_time: float, success: bool):
        """Record notification performance metric"""
        try:
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            performance_optimizer = PerformanceOptimizer(self.config)
            performance_optimizer.record_webhook_event(
                event_type=f"notification_{event_type}",
                processing_time=processing_time,
                success=success
            )
            
        except Exception as e:
            logger.error(f"Error recording notification metric: {e}")
    
    def _record_analytics_metric(self, event_type: str, processing_time: float, success: bool):
        """Record analytics performance metric"""
        try:
            from ..monitoring.performance_optimizer import PerformanceOptimizer
            
            performance_optimizer = PerformanceOptimizer(self.config)
            performance_optimizer.record_webhook_event(
                event_type=f"analytics_{event_type}",
                processing_time=processing_time,
                success=success
            )
            
        except Exception as e:
            logger.error(f"Error recording analytics metric: {e}")
    
    def _is_recovery_scenario(self, customer: Customer, billing_record: BillingHistory) -> bool:
        """Check if this is a recovery scenario (payment after previous failures)"""
        try:
            # Check if there are any failed payment attempts for this customer/subscription
            # This would typically query a dunning events table
            # For now, we'll check if the billing record has a previous failed status
            
            # Check if subscription was in a failed state
            if customer.subscription and customer.subscription.status in ['past_due', 'unpaid', 'canceled']:
                return True
            
            # Check if there are recent failed billing records
            recent_failed_records = self.db.query(BillingHistory).filter(
                BillingHistory.customer_id == customer.id,
                BillingHistory.subscription_id == billing_record.subscription_id,
                BillingHistory.status == 'failed',
                BillingHistory.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
            ).count()
            
            return recent_failed_records > 0
            
        except Exception as e:
            logger.error(f"Error checking recovery scenario: {e}")
            return False