"""
Plaid Reliability Service for MINGUS

This module provides comprehensive error handling and reliability features for Plaid integration:
- Connection failure recovery
- Bank maintenance handling
- API rate limiting compliance
- Data synchronization reliability
- User notification for connection issues
"""

import logging
import time
import random
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import asyncio
from functools import wraps
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.models.plaid_models import PlaidConnection, PlaidAccount, PlaidTransaction, PlaidSyncLog
from backend.models.security_models import SecurityAuditLog
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class PlaidErrorType(Enum):
    """Types of Plaid errors"""
    CONNECTION_FAILURE = "connection_failure"
    BANK_MAINTENANCE = "bank_maintenance"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_ERROR = "authentication_error"
    INSTITUTION_ERROR = "institution_error"
    ITEM_ERROR = "item_error"
    PRODUCT_NOT_AVAILABLE = "product_not_available"
    INVALID_REQUEST = "invalid_request"
    INTERNAL_ERROR = "internal_error"
    UNKNOWN_ERROR = "unknown_error"

class ConnectionStatus(Enum):
    """Connection status enumeration"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"

class SyncStatus(Enum):
    """Data synchronization status"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"
    RETRYING = "retrying"

@dataclass
class PlaidError:
    """Plaid error information"""
    error_type: PlaidErrorType
    error_code: str
    error_message: str
    display_message: str
    retry_after: Optional[int] = None
    maintenance_until: Optional[datetime] = None
    affected_services: List[str] = None
    user_action_required: bool = False

@dataclass
class ConnectionHealth:
    """Connection health information"""
    connection_id: str
    status: ConnectionStatus
    last_successful_sync: Optional[datetime]
    last_error: Optional[PlaidError]
    sync_failure_count: int
    consecutive_failures: int
    maintenance_mode: bool
    maintenance_until: Optional[datetime]
    retry_attempts: int
    next_retry: Optional[datetime]

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    endpoint: str
    requests_per_minute: int
    requests_per_hour: int
    current_minute_requests: int
    current_hour_requests: int
    reset_time_minute: datetime
    reset_time_hour: datetime
    retry_after: Optional[int] = None

@dataclass
class SyncResult:
    """Data synchronization result"""
    success: bool
    status: SyncStatus
    records_processed: int
    records_failed: int
    error: Optional[PlaidError]
    retry_after: Optional[int]
    sync_duration: float
    timestamp: datetime

class PlaidReliabilityService:
    """Service for handling Plaid reliability and error recovery"""
    
    def __init__(self, db_session: Session, notification_service: NotificationService, config: Dict[str, Any]):
        self.db = db_session
        self.notification_service = notification_service
        self.config = config
        self.rate_limits = self._initialize_rate_limits()
        self.retry_strategies = self._initialize_retry_strategies()
        self.error_handlers = self._initialize_error_handlers()
        
    def _initialize_rate_limits(self) -> Dict[str, RateLimitInfo]:
        """Initialize rate limiting configuration"""
        return {
            'accounts/balance/get': RateLimitInfo(
                endpoint='accounts/balance/get',
                requests_per_minute=120,
                requests_per_hour=1000,
                current_minute_requests=0,
                current_hour_requests=0,
                reset_time_minute=datetime.utcnow(),
                reset_time_hour=datetime.utcnow()
            ),
            'transactions/get': RateLimitInfo(
                endpoint='transactions/get',
                requests_per_minute=100,
                requests_per_hour=800,
                current_minute_requests=0,
                current_hour_requests=0,
                reset_time_minute=datetime.utcnow(),
                reset_time_hour=datetime.utcnow()
            ),
            'item/get': RateLimitInfo(
                endpoint='item/get',
                requests_per_minute=300,
                requests_per_hour=2000,
                current_minute_requests=0,
                current_hour_requests=0,
                reset_time_minute=datetime.utcnow(),
                reset_time_hour=datetime.utcnow()
            ),
            'institutions/get': RateLimitInfo(
                endpoint='institutions/get',
                requests_per_minute=500,
                requests_per_hour=3000,
                current_minute_requests=0,
                current_hour_requests=0,
                reset_time_minute=datetime.utcnow(),
                reset_time_hour=datetime.utcnow()
            )
        }
    
    def _initialize_retry_strategies(self) -> Dict[PlaidErrorType, Dict[str, Any]]:
        """Initialize retry strategies for different error types"""
        return {
            PlaidErrorType.CONNECTION_FAILURE: {
                'max_retries': 5,
                'base_delay': 1,
                'max_delay': 60,
                'backoff_multiplier': 2,
                'jitter': True
            },
            PlaidErrorType.RATE_LIMIT_EXCEEDED: {
                'max_retries': 3,
                'base_delay': 60,
                'max_delay': 300,
                'backoff_multiplier': 1.5,
                'jitter': False
            },
            PlaidErrorType.BANK_MAINTENANCE: {
                'max_retries': 10,
                'base_delay': 300,
                'max_delay': 3600,
                'backoff_multiplier': 2,
                'jitter': True
            },
            PlaidErrorType.INSTITUTION_ERROR: {
                'max_retries': 3,
                'base_delay': 30,
                'max_delay': 300,
                'backoff_multiplier': 2,
                'jitter': True
            },
            PlaidErrorType.ITEM_ERROR: {
                'max_retries': 2,
                'base_delay': 60,
                'max_delay': 600,
                'backoff_multiplier': 2,
                'jitter': True
            }
        }
    
    def _initialize_error_handlers(self) -> Dict[PlaidErrorType, Callable]:
        """Initialize error handlers for different error types"""
        return {
            PlaidErrorType.CONNECTION_FAILURE: self._handle_connection_failure,
            PlaidErrorType.BANK_MAINTENANCE: self._handle_bank_maintenance,
            PlaidErrorType.RATE_LIMIT_EXCEEDED: self._handle_rate_limit_exceeded,
            PlaidErrorType.AUTHENTICATION_ERROR: self._handle_authentication_error,
            PlaidErrorType.INSTITUTION_ERROR: self._handle_institution_error,
            PlaidErrorType.ITEM_ERROR: self._handle_item_error,
            PlaidErrorType.PRODUCT_NOT_AVAILABLE: self._handle_product_not_available,
            PlaidErrorType.INVALID_REQUEST: self._handle_invalid_request,
            PlaidErrorType.INTERNAL_ERROR: self._handle_internal_error,
            PlaidErrorType.UNKNOWN_ERROR: self._handle_unknown_error
        }
    
    def parse_plaid_error(self, error_response: Dict[str, Any]) -> PlaidError:
        """Parse Plaid error response and create PlaidError object"""
        try:
            error_code = error_response.get('error_code', 'UNKNOWN_ERROR')
            error_message = error_response.get('error_message', 'Unknown error occurred')
            
            # Map error codes to error types
            error_type_mapping = {
                'ITEM_LOGIN_REQUIRED': PlaidErrorType.AUTHENTICATION_ERROR,
                'ITEM_GONE': PlaidErrorType.ITEM_ERROR,
                'INSTITUTION_DOWN': PlaidErrorType.BANK_MAINTENANCE,
                'INSTITUTION_NOT_RESPONDING': PlaidErrorType.CONNECTION_FAILURE,
                'RATE_LIMIT_EXCEEDED': PlaidErrorType.RATE_LIMIT_EXCEEDED,
                'INVALID_CREDENTIALS': PlaidErrorType.AUTHENTICATION_ERROR,
                'INVALID_REQUEST': PlaidErrorType.INVALID_REQUEST,
                'INTERNAL_SERVER_ERROR': PlaidErrorType.INTERNAL_ERROR,
                'PRODUCT_NOT_AVAILABLE': PlaidErrorType.PRODUCT_NOT_AVAILABLE
            }
            
            error_type = error_type_mapping.get(error_code, PlaidErrorType.UNKNOWN_ERROR)
            
            # Create user-friendly display message
            display_messages = {
                PlaidErrorType.CONNECTION_FAILURE: "We're having trouble connecting to your bank. Please try again later.",
                PlaidErrorType.BANK_MAINTENANCE: "Your bank is currently performing maintenance. We'll retry automatically.",
                PlaidErrorType.RATE_LIMIT_EXCEEDED: "We've reached our connection limit. Please try again in a few minutes.",
                PlaidErrorType.AUTHENTICATION_ERROR: "Your bank connection needs to be updated. Please reconnect your account.",
                PlaidErrorType.INSTITUTION_ERROR: "There's an issue with your bank's connection. We're working to resolve it.",
                PlaidErrorType.ITEM_ERROR: "Your bank connection has expired. Please reconnect your account.",
                PlaidErrorType.PRODUCT_NOT_AVAILABLE: "This feature is not available for your bank account.",
                PlaidErrorType.INVALID_REQUEST: "There was an issue with your request. Please try again.",
                PlaidErrorType.INTERNAL_ERROR: "We're experiencing technical difficulties. Please try again later.",
                PlaidErrorType.UNKNOWN_ERROR: "An unexpected error occurred. Please try again later."
            }
            
            display_message = display_messages.get(error_type, "An error occurred. Please try again later.")
            
            # Extract additional information
            retry_after = error_response.get('retry_after')
            maintenance_until = None
            if error_response.get('maintenance_until'):
                try:
                    maintenance_until = datetime.fromisoformat(error_response['maintenance_until'].replace('Z', '+00:00'))
                except:
                    pass
            
            return PlaidError(
                error_type=error_type,
                error_code=error_code,
                error_message=error_message,
                display_message=display_message,
                retry_after=retry_after,
                maintenance_until=maintenance_until,
                affected_services=error_response.get('affected_services', []),
                user_action_required=error_type in [
                    PlaidErrorType.AUTHENTICATION_ERROR,
                    PlaidErrorType.ITEM_ERROR
                ]
            )
            
        except Exception as e:
            logger.error(f"Error parsing Plaid error: {e}")
            return PlaidError(
                error_type=PlaidErrorType.UNKNOWN_ERROR,
                error_code="PARSE_ERROR",
                error_message=str(e),
                display_message="An error occurred while processing the response."
            )
    
    def check_rate_limit(self, endpoint: str) -> Tuple[bool, Optional[int]]:
        """Check if rate limit is exceeded for an endpoint"""
        try:
            if endpoint not in self.rate_limits:
                return True, None
            
            rate_limit = self.rate_limits[endpoint]
            now = datetime.utcnow()
            
            # Reset counters if needed
            if now >= rate_limit.reset_time_minute:
                rate_limit.current_minute_requests = 0
                rate_limit.reset_time_minute = now + timedelta(minutes=1)
            
            if now >= rate_limit.reset_time_hour:
                rate_limit.current_hour_requests = 0
                rate_limit.reset_time_hour = now + timedelta(hours=1)
            
            # Check limits
            minute_exceeded = rate_limit.current_minute_requests >= rate_limit.requests_per_minute
            hour_exceeded = rate_limit.current_hour_requests >= rate_limit.requests_per_hour
            
            if minute_exceeded or hour_exceeded:
                # Calculate retry after time
                if minute_exceeded:
                    retry_after = int((rate_limit.reset_time_minute - now).total_seconds())
                else:
                    retry_after = int((rate_limit.reset_time_hour - now).total_seconds())
                
                return False, retry_after
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True, None
    
    def increment_rate_limit(self, endpoint: str):
        """Increment rate limit counters for an endpoint"""
        try:
            if endpoint in self.rate_limits:
                rate_limit = self.rate_limits[endpoint]
                rate_limit.current_minute_requests += 1
                rate_limit.current_hour_requests += 1
                
        except Exception as e:
            logger.error(f"Error incrementing rate limit: {e}")
    
    def calculate_retry_delay(self, error_type: PlaidErrorType, attempt: int, retry_after: Optional[int] = None) -> int:
        """Calculate retry delay based on error type and attempt number"""
        try:
            if retry_after:
                return retry_after
            
            strategy = self.retry_strategies.get(error_type, self.retry_strategies[PlaidErrorType.UNKNOWN_ERROR])
            
            base_delay = strategy['base_delay']
            max_delay = strategy['max_delay']
            backoff_multiplier = strategy['backoff_multiplier']
            jitter = strategy['jitter']
            
            # Calculate exponential backoff
            delay = min(base_delay * (backoff_multiplier ** (attempt - 1)), max_delay)
            
            # Add jitter if enabled
            if jitter:
                jitter_amount = delay * 0.1  # 10% jitter
                delay += random.uniform(-jitter_amount, jitter_amount)
                delay = max(1, delay)  # Ensure minimum 1 second delay
            
            return int(delay)
            
        except Exception as e:
            logger.error(f"Error calculating retry delay: {e}")
            return 60  # Default 60 second delay
    
    def should_retry(self, error_type: PlaidErrorType, attempt: int) -> bool:
        """Determine if operation should be retried"""
        try:
            strategy = self.retry_strategies.get(error_type, self.retry_strategies[PlaidErrorType.UNKNOWN_ERROR])
            max_retries = strategy['max_retries']
            
            return attempt <= max_retries
            
        except Exception as e:
            logger.error(f"Error checking retry eligibility: {e}")
            return False
    
    def handle_plaid_error(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Plaid error and return appropriate response"""
        try:
            # Log the error
            self._log_error(error, connection, context)
            
            # Get error handler
            handler = self.error_handlers.get(error.error_type, self._handle_unknown_error)
            
            # Handle the error
            result = handler(error, connection, context)
            
            # Update connection health
            self._update_connection_health(connection, error)
            
            # Send user notification if needed
            if error.user_action_required or error.error_type in [PlaidErrorType.BANK_MAINTENANCE, PlaidErrorType.CONNECTION_FAILURE]:
                self._send_user_notification(connection, error)
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling Plaid error: {e}")
            return {
                'success': False,
                'error': 'Error handling failed',
                'retry_after': 300  # 5 minutes default
            }
    
    def _handle_connection_failure(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle connection failure errors"""
        try:
            # Mark connection as degraded
            connection.is_active = True
            connection.last_error = error.error_code
            connection.last_error_at = datetime.utcnow()
            
            # Schedule retry
            retry_delay = self.calculate_retry_delay(error.error_type, context.get('attempt', 1))
            
            self.db.commit()
            
            return {
                'success': False,
                'error': error.display_message,
                'retry_after': retry_delay,
                'connection_status': ConnectionStatus.DEGRADED.value
            }
            
        except Exception as e:
            logger.error(f"Error handling connection failure: {e}")
            return {'success': False, 'error': 'Connection failure handling error'}
    
    def _handle_bank_maintenance(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bank maintenance errors"""
        try:
            # Mark connection as in maintenance
            connection.is_active = True
            connection.last_error = error.error_code
            connection.last_error_at = datetime.utcnow()
            
            # Set maintenance mode
            if error.maintenance_until:
                connection.maintenance_until = error.maintenance_until
            else:
                # Default maintenance period of 2 hours
                connection.maintenance_until = datetime.utcnow() + timedelta(hours=2)
            
            self.db.commit()
            
            return {
                'success': False,
                'error': error.display_message,
                'retry_after': error.retry_after or 3600,  # 1 hour default
                'connection_status': ConnectionStatus.MAINTENANCE.value,
                'maintenance_until': connection.maintenance_until.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling bank maintenance: {e}")
            return {'success': False, 'error': 'Bank maintenance handling error'}
    
    def _handle_rate_limit_exceeded(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rate limit exceeded errors"""
        try:
            retry_delay = error.retry_after or self.calculate_retry_delay(error.error_type, context.get('attempt', 1))
            
            return {
                'success': False,
                'error': error.display_message,
                'retry_after': retry_delay,
                'connection_status': ConnectionStatus.DEGRADED.value
            }
            
        except Exception as e:
            logger.error(f"Error handling rate limit exceeded: {e}")
            return {'success': False, 'error': 'Rate limit handling error'}
    
    def _handle_authentication_error(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication errors"""
        try:
            # Mark connection as requiring re-authentication
            connection.is_active = False
            connection.last_error = error.error_code
            connection.last_error_at = datetime.utcnow()
            connection.requires_reauth = True
            
            self.db.commit()
            
            return {
                'success': False,
                'error': error.display_message,
                'user_action_required': True,
                'connection_status': ConnectionStatus.ERROR.value,
                'requires_reauth': True
            }
            
        except Exception as e:
            logger.error(f"Error handling authentication error: {e}")
            return {'success': False, 'error': 'Authentication error handling failed'}
    
    def _handle_institution_error(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle institution errors"""
        try:
            # Mark connection as degraded
            connection.is_active = True
            connection.last_error = error.error_code
            connection.last_error_at = datetime.utcnow()
            
            retry_delay = self.calculate_retry_delay(error.error_type, context.get('attempt', 1))
            
            self.db.commit()
            
            return {
                'success': False,
                'error': error.display_message,
                'retry_after': retry_delay,
                'connection_status': ConnectionStatus.DEGRADED.value
            }
            
        except Exception as e:
            logger.error(f"Error handling institution error: {e}")
            return {'success': False, 'error': 'Institution error handling failed'}
    
    def _handle_item_error(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item errors"""
        try:
            # Mark connection as requiring re-authentication
            connection.is_active = False
            connection.last_error = error.error_code
            connection.last_error_at = datetime.utcnow()
            connection.requires_reauth = True
            
            self.db.commit()
            
            return {
                'success': False,
                'error': error.display_message,
                'user_action_required': True,
                'connection_status': ConnectionStatus.ERROR.value,
                'requires_reauth': True
            }
            
        except Exception as e:
            logger.error(f"Error handling item error: {e}")
            return {'success': False, 'error': 'Item error handling failed'}
    
    def _handle_product_not_available(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle product not available errors"""
        return {
            'success': False,
            'error': error.display_message,
            'user_action_required': False,
            'connection_status': ConnectionStatus.ERROR.value
        }
    
    def _handle_invalid_request(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invalid request errors"""
        return {
            'success': False,
            'error': error.display_message,
            'user_action_required': False,
            'connection_status': ConnectionStatus.ERROR.value
        }
    
    def _handle_internal_error(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle internal errors"""
        try:
            retry_delay = self.calculate_retry_delay(error.error_type, context.get('attempt', 1))
            
            return {
                'success': False,
                'error': error.display_message,
                'retry_after': retry_delay,
                'connection_status': ConnectionStatus.DEGRADED.value
            }
            
        except Exception as e:
            logger.error(f"Error handling internal error: {e}")
            return {'success': False, 'error': 'Internal error handling failed'}
    
    def _handle_unknown_error(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown errors"""
        try:
            retry_delay = self.calculate_retry_delay(error.error_type, context.get('attempt', 1))
            
            return {
                'success': False,
                'error': error.display_message,
                'retry_after': retry_delay,
                'connection_status': ConnectionStatus.DEGRADED.value
            }
            
        except Exception as e:
            logger.error(f"Error handling unknown error: {e}")
            return {'success': False, 'error': 'Unknown error handling failed'}
    
    def get_connection_health(self, connection_id: str) -> Optional[ConnectionHealth]:
        """Get connection health information"""
        try:
            connection = self.db.query(PlaidConnection).filter(
                PlaidConnection.id == connection_id
            ).first()
            
            if not connection:
                return None
            
            # Get sync failure count
            sync_failures = self.db.query(PlaidSyncLog).filter(
                PlaidSyncLog.connection_id == connection_id,
                PlaidSyncLog.status == 'failed'
            ).count()
            
            # Determine status
            if connection.requires_reauth:
                status = ConnectionStatus.ERROR
            elif connection.maintenance_until and connection.maintenance_until > datetime.utcnow():
                status = ConnectionStatus.MAINTENANCE
            elif connection.last_error and connection.last_error_at:
                # Check if recent error (within last hour)
                if connection.last_error_at > datetime.utcnow() - timedelta(hours=1):
                    status = ConnectionStatus.DEGRADED
                else:
                    status = ConnectionStatus.ACTIVE
            else:
                status = ConnectionStatus.ACTIVE
            
            return ConnectionHealth(
                connection_id=str(connection.id),
                status=status,
                last_successful_sync=connection.last_sync_at,
                last_error=PlaidError(
                    error_type=PlaidErrorType.UNKNOWN_ERROR,
                    error_code=connection.last_error or "NONE",
                    error_message="",
                    display_message=""
                ) if connection.last_error else None,
                sync_failure_count=sync_failures,
                consecutive_failures=0,  # Would need to calculate from sync logs
                maintenance_mode=bool(connection.maintenance_until and connection.maintenance_until > datetime.utcnow()),
                maintenance_until=connection.maintenance_until,
                retry_attempts=0,  # Would need to track in sync logs
                next_retry=None  # Would need to calculate from retry strategy
            )
            
        except Exception as e:
            logger.error(f"Error getting connection health: {e}")
            return None
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Retry function with exponential backoff"""
        max_attempts = kwargs.pop('max_attempts', 3)
        base_delay = kwargs.pop('base_delay', 1)
        
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts:
                    raise e
                
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)
    
    def _log_error(self, error: PlaidError, connection: PlaidConnection, context: Dict[str, Any]):
        """Log error to security audit log"""
        try:
            audit_log = SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=connection.user_id,
                action='plaid_error',
                resource_type='plaid_connection',
                resource_id=str(connection.id),
                ip_address='system',
                user_agent='system',
                success=False,
                details={
                    'error_type': error.error_type.value,
                    'error_code': error.error_code,
                    'error_message': error.error_message,
                    'context': context
                },
                risk_level='medium'
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging Plaid error: {e}")
    
    def _update_connection_health(self, connection: PlaidConnection, error: PlaidError):
        """Update connection health based on error"""
        try:
            connection.last_error = error.error_code
            connection.last_error_at = datetime.utcnow()
            
            if error.error_type in [PlaidErrorType.AUTHENTICATION_ERROR, PlaidErrorType.ITEM_ERROR]:
                connection.requires_reauth = True
                connection.is_active = False
            
            if error.maintenance_until:
                connection.maintenance_until = error.maintenance_until
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating connection health: {e}")
    
    def _send_user_notification(self, connection: PlaidConnection, error: PlaidError):
        """Send user notification about connection issues"""
        try:
            notification_data = {
                'user_id': connection.user_id,
                'notification_type': 'plaid_connection_issue',
                'title': 'Bank Connection Issue',
                'message': error.display_message,
                'priority': 'medium' if error.user_action_required else 'low',
                'action_required': error.user_action_required,
                'connection_id': str(connection.id),
                'institution_name': connection.institution_name,
                'error_code': error.error_code
            }
            
            self.notification_service.send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error sending user notification: {e}")
    
    def create_sync_log(self, connection_id: str, sync_type: str, status: SyncStatus, 
                       result: SyncResult, context: Dict[str, Any] = None):
        """Create sync log entry"""
        try:
            sync_log = PlaidSyncLog(
                connection_id=connection_id,
                sync_type=sync_type,
                status=status.value,
                started_at=result.timestamp - timedelta(seconds=result.sync_duration),
                completed_at=result.timestamp,
                duration=result.sync_duration,
                records_processed=result.records_processed,
                records_failed=result.records_failed,
                error_message=result.error.error_message if result.error else None,
                retry_after=result.retry_after,
                context=context or {}
            )
            
            self.db.add(sync_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating sync log: {e}")
    
    def get_sync_reliability_stats(self, connection_id: str, days: int = 30) -> Dict[str, Any]:
        """Get sync reliability statistics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            sync_logs = self.db.query(PlaidSyncLog).filter(
                PlaidSyncLog.connection_id == connection_id,
                PlaidSyncLog.completed_at >= start_date
            ).all()
            
            total_syncs = len(sync_logs)
            successful_syncs = len([log for log in sync_logs if log.status == 'success'])
            failed_syncs = len([log for log in sync_logs if log.status == 'failed'])
            
            success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
            avg_duration = sum(log.duration for log in sync_logs) / total_syncs if total_syncs > 0 else 0
            
            return {
                'total_syncs': total_syncs,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'success_rate': round(success_rate, 2),
                'average_duration': round(avg_duration, 2),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting sync reliability stats: {e}")
            return {} 