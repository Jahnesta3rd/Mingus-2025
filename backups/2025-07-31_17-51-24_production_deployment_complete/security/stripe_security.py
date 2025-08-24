"""
MINGUS Application - Stripe Security Module
==========================================

Comprehensive security features for Stripe integration including:
- Webhook signature verification
- Idempotency key management
- API rate limiting compliance
- PCI compliance best practices

Author: MINGUS Development Team
Date: January 2025
"""

import hashlib
import hmac
import time
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from ..config.stripe import get_stripe_config


class SecurityLevel(Enum):
    """Security level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_id: str
    event_type: str
    timestamp: datetime
    source_ip: str
    user_agent: str
    request_id: str
    severity: SecurityLevel
    details: Dict[str, Any]
    mitigated: bool = False
    mitigation_action: Optional[str] = None


class WebhookSecurityManager:
    """Manages webhook security and signature verification."""
    
    def __init__(self, config):
        """Initialize webhook security manager."""
        self.config = config
        self.logger = logging.getLogger('stripe.security.webhook')
        self.allowed_ips = self._load_allowed_ips()
        self.signature_cache = {}  # Simple in-memory cache for signature validation
    
    def _load_allowed_ips(self) -> List[str]:
        """Load allowed IP addresses for webhook verification."""
        # Stripe's webhook IP ranges (updated regularly)
        stripe_ips = [
            '3.18.12.63', '3.130.192.231', '13.235.14.237', '13.235.122.149',
            '18.211.135.69', '35.154.171.200', '52.15.183.38', '54.187.174.169',
            '54.187.205.235', '54.187.216.72', '54.241.31.99', '54.241.31.102',
            '54.241.34.107', '54.241.34.108', '54.241.34.109', '54.241.34.110',
            '54.241.34.111', '54.241.34.112', '54.241.34.113', '54.241.34.114',
            '54.241.34.115', '54.241.34.116', '54.241.34.117', '54.241.34.118',
            '54.241.34.119', '54.241.34.120', '54.241.34.121', '54.241.34.122',
            '54.241.34.123', '54.241.34.124', '54.241.34.125', '54.241.34.126',
            '54.241.34.127', '54.241.34.128', '54.241.34.129', '54.241.34.130',
            '54.241.34.131', '54.241.34.132', '54.241.34.133', '54.241.34.134',
            '54.241.34.135', '54.241.34.136', '54.241.34.137', '54.241.34.138',
            '54.241.34.139', '54.241.34.140', '54.241.34.141', '54.241.34.142',
            '54.241.34.143', '54.241.34.144', '54.241.34.145', '54.241.34.146',
            '54.241.34.147', '54.241.34.148', '54.241.34.149', '54.241.34.150',
            '54.241.34.151', '54.241.34.152', '54.241.34.153', '54.241.34.154',
            '54.241.34.155', '54.241.34.156', '54.241.34.157', '54.241.34.158',
            '54.241.34.159', '54.241.34.160', '54.241.34.161', '54.241.34.162',
            '54.241.34.163', '54.241.34.164', '54.241.34.165', '54.241.34.166',
            '54.241.34.167', '54.241.34.168', '54.241.34.169', '54.241.34.170',
            '54.241.34.171', '54.241.34.172', '54.241.34.173', '54.241.34.174',
            '54.241.34.175', '54.241.34.176', '54.241.34.177', '54.241.34.178',
            '54.241.34.179', '54.241.34.180', '54.241.34.181', '54.241.34.182',
            '54.241.34.183', '54.241.34.184', '54.241.34.185', '54.241.34.186',
            '54.241.34.187', '54.241.34.188', '54.241.34.189', '54.241.34.190',
            '54.241.34.191', '54.241.34.192', '54.241.34.193', '54.241.34.194',
            '54.241.34.195', '54.241.34.196', '54.241.34.197', '54.241.34.198',
            '54.241.34.199', '54.241.34.200', '54.241.34.201', '54.241.34.202',
            '54.241.34.203', '54.241.34.204', '54.241.34.205', '54.241.34.206',
            '54.241.34.207', '54.241.34.208', '54.241.34.209', '54.241.34.210',
            '54.241.34.211', '54.241.34.212', '54.241.34.213', '54.241.34.214',
            '54.241.34.215', '54.241.34.216', '54.241.34.217', '54.241.34.218',
            '54.241.34.219', '54.241.34.220', '54.241.34.221', '54.241.34.222',
            '54.241.34.223', '54.241.34.224', '54.241.34.225', '54.241.34.226',
            '54.241.34.227', '54.241.34.228', '54.241.34.229', '54.241.34.230',
            '54.241.34.231', '54.241.34.232', '54.241.34.233', '54.241.34.234',
            '54.241.34.235', '54.241.34.236', '54.241.34.237', '54.241.34.238',
            '54.241.34.239', '54.241.34.240', '54.241.34.241', '54.241.34.242',
            '54.241.34.243', '54.241.34.244', '54.241.34.245', '54.241.34.246',
            '54.241.34.247', '54.241.34.248', '54.241.34.249', '54.241.34.250',
            '54.241.34.251', '54.241.34.252', '54.241.34.253', '54.241.34.254',
            '54.241.34.255'
        ]
        
        # Add custom allowed IPs from environment
        custom_ips = os.environ.get('STRIPE_WEBHOOK_ALLOWED_IPS', '').split(',')
        return stripe_ips + [ip.strip() for ip in custom_ips if ip.strip()]
    
    def verify_webhook_signature(self, payload: bytes, signature: str, 
                                timestamp: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verify webhook signature with enhanced security checks.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature header
            timestamp: Webhook timestamp header
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check timestamp to prevent replay attacks
            if timestamp:
                webhook_time = int(timestamp)
                current_time = int(time.time())
                if abs(current_time - webhook_time) > 300:  # 5 minutes tolerance
                    return False, "Webhook timestamp too old or too new"
            
            # Verify signature format
            if not signature.startswith('t='):
                return False, "Invalid signature format"
            
            # Extract timestamp and signature
            try:
                timestamp_part, signature_part = signature.split(',', 1)
                timestamp_str = timestamp_part.split('=', 1)[1]
                signature_str = signature_part.split('=', 1)[1]
            except (ValueError, IndexError):
                return False, "Invalid signature format"
            
            # Check signature cache to prevent replay attacks
            signature_hash = hashlib.sha256(signature.encode()).hexdigest()
            if signature_hash in self.signature_cache:
                return False, "Duplicate signature detected"
            
            # Verify signature using HMAC
            expected_signature = hmac.new(
                self.config.webhook_secret.encode(),
                f"{timestamp_str}.{payload.decode()}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(f"sha256={expected_signature}", signature_str):
                return False, "Invalid signature"
            
            # Cache signature to prevent replay attacks
            self.signature_cache[signature_hash] = time.time()
            
            # Clean old cache entries (older than 1 hour)
            current_time = time.time()
            self.signature_cache = {
                k: v for k, v in self.signature_cache.items() 
                if current_time - v < 3600
            }
            
            return True, "Signature verified successfully"
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {e}")
            return False, f"Signature verification error: {str(e)}"
    
    def verify_source_ip(self, source_ip: str) -> Tuple[bool, str]:
        """
        Verify webhook source IP address.
        
        Args:
            source_ip: Source IP address
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if source_ip in self.allowed_ips:
            return True, "IP address allowed"
        
        # Check if IP is in Stripe's ranges (simplified check)
        if source_ip.startswith(('3.18.', '3.130.', '13.235.', '18.211.', 
                                '35.154.', '52.15.', '54.187.', '54.241.')):
            return True, "IP address in Stripe range"
        
        return False, f"IP address {source_ip} not allowed"
    
    def validate_webhook_payload(self, payload: bytes) -> Tuple[bool, str]:
        """
        Validate webhook payload structure and content.
        
        Args:
            payload: Raw webhook payload
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            import json
            data = json.loads(payload.decode())
            
            # Check required fields
            required_fields = ['type', 'data']
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"
            
            # Validate event type
            if not isinstance(data['type'], str):
                return False, "Invalid event type format"
            
            # Validate data structure
            if not isinstance(data['data'], dict):
                return False, "Invalid data structure"
            
            return True, "Payload validation successful"
            
        except json.JSONDecodeError:
            return False, "Invalid JSON payload"
        except Exception as e:
            return False, f"Payload validation error: {str(e)}"


class IdempotencyKeyManager:
    """Manages idempotency keys for API operations."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize idempotency key manager."""
        self.logger = logging.getLogger('stripe.security.idempotency')
        self.redis_client = None
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # Fallback to in-memory storage if Redis is not available
        self.memory_cache = {}
        self.cache_ttl = 24 * 60 * 60  # 24 hours
    
    def generate_idempotency_key(self, operation: str, user_id: str) -> str:
        """
        Generate a unique idempotency key.
        
        Args:
            operation: Operation type (e.g., 'create_subscription')
            user_id: User identifier
            
        Returns:
            Unique idempotency key
        """
        timestamp = str(int(time.time()))
        random_uuid = str(uuid.uuid4())
        return f"{operation}_{user_id}_{timestamp}_{random_uuid}"
    
    def check_idempotency_key(self, key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if idempotency key exists and return cached result.
        
        Args:
            key: Idempotency key
            
        Returns:
            Tuple of (exists, cached_result)
        """
        try:
            if self.redis_client:
                cached_result = self.redis_client.get(key)
                if cached_result:
                    return True, eval(cached_result.decode())
            else:
                if key in self.memory_cache:
                    timestamp, result = self.memory_cache[key]
                    if time.time() - timestamp < self.cache_ttl:
                        return True, result
                    else:
                        del self.memory_cache[key]
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"Idempotency key check failed: {e}")
            return False, None
    
    def store_idempotency_result(self, key: str, result: Dict[str, Any], 
                                ttl: int = 24 * 60 * 60) -> bool:
        """
        Store operation result with idempotency key.
        
        Args:
            key: Idempotency key
            result: Operation result
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, str(result))
            else:
                self.memory_cache[key] = (time.time(), result)
                
                # Clean old entries
                current_time = time.time()
                self.memory_cache = {
                    k: v for k, v in self.memory_cache.items() 
                    if current_time - v[0] < self.cache_ttl
                }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store idempotency result: {e}")
            return False
    
    def invalidate_idempotency_key(self, key: str) -> bool:
        """
        Invalidate an idempotency key.
        
        Args:
            key: Idempotency key to invalidate
            
        Returns:
            Success status
        """
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to invalidate idempotency key: {e}")
            return False


class RateLimitManager:
    """Manages API rate limiting for Stripe operations."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize rate limit manager."""
        self.logger = logging.getLogger('stripe.security.ratelimit')
        self.redis_client = None
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # Rate limits (requests per minute)
        self.rate_limits = {
            'customer': 100,
            'subscription': 50,
            'payment_intent': 200,
            'webhook': 1000,
            'default': 100
        }
        
        # Memory cache for rate limiting
        self.memory_cache = {}
    
    def check_rate_limit(self, operation: str, identifier: str, 
                        window: int = 60) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if operation is within rate limits.
        
        Args:
            operation: Operation type
            identifier: User or IP identifier
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        try:
            key = f"rate_limit:{operation}:{identifier}"
            limit = self.rate_limits.get(operation, self.rate_limits['default'])
            current_time = time.time()
            
            if self.redis_client:
                # Use Redis for rate limiting
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, current_time - window)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.zcard(key)
                pipe.expire(key, window)
                results = pipe.execute()
                current_count = results[2]
            else:
                # Use memory cache
                if key not in self.memory_cache:
                    self.memory_cache[key] = []
                
                # Remove old entries
                self.memory_cache[key] = [
                    t for t in self.memory_cache[key] 
                    if current_time - t < window
                ]
                
                # Add current request
                self.memory_cache[key].append(current_time)
                current_count = len(self.memory_cache[key])
            
            allowed = current_count <= limit
            remaining = max(0, limit - current_count)
            
            rate_limit_info = {
                'allowed': allowed,
                'limit': limit,
                'remaining': remaining,
                'reset_time': current_time + window,
                'current_count': current_count
            }
            
            return allowed, rate_limit_info
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return True, {'allowed': True, 'error': str(e)}
    
    def get_rate_limit_headers(self, operation: str, identifier: str) -> Dict[str, str]:
        """
        Get rate limit headers for response.
        
        Args:
            operation: Operation type
            identifier: User or IP identifier
            
        Returns:
            Rate limit headers
        """
        allowed, info = self.check_rate_limit(operation, identifier)
        
        headers = {
            'X-RateLimit-Limit': str(info.get('limit', 0)),
            'X-RateLimit-Remaining': str(info.get('remaining', 0)),
            'X-RateLimit-Reset': str(int(info.get('reset_time', 0)))
        }
        
        return headers


class PCISecurityManager:
    """Manages PCI compliance best practices."""
    
    def __init__(self):
        """Initialize PCI security manager."""
        self.logger = logging.getLogger('stripe.security.pci')
        self.encryption_key = self._get_or_generate_key()
        self.fernet = Fernet(self.encryption_key)
        
        # PCI compliance settings
        self.pci_settings = {
            'encrypt_sensitive_data': True,
            'log_retention_days': 90,
            'audit_logging': True,
            'data_masking': True,
            'secure_headers': True
        }
    
    def _get_or_generate_key(self) -> bytes:
        """Get or generate encryption key for sensitive data."""
        key = os.environ.get('STRIPE_ENCRYPTION_KEY')
        if key:
            return base64.urlsafe_b64decode(key)
        else:
            # Generate new key
            new_key = Fernet.generate_key()
            self.logger.warning("Generated new encryption key. Set STRIPE_ENCRYPTION_KEY for consistency.")
            return new_key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data for PCI compliance.
        
        Args:
            data: Sensitive data to encrypt
            
        Returns:
            Encrypted data
        """
        try:
            if not self.pci_settings['encrypt_sensitive_data']:
                return data
            
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt sensitive data: {e}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data to decrypt
            
        Returns:
            Decrypted data
        """
        try:
            if not self.pci_settings['encrypt_sensitive_data']:
                return encrypted_data
            
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt sensitive data: {e}")
            return encrypted_data
    
    def mask_sensitive_data(self, data: str, data_type: str = 'card') -> str:
        """
        Mask sensitive data for logging and display.
        
        Args:
            data: Data to mask
            data_type: Type of data (card, email, phone, etc.)
            
        Returns:
            Masked data
        """
        if not self.pci_settings['data_masking']:
            return data
        
        try:
            if data_type == 'card':
                if len(data) >= 4:
                    return '*' * (len(data) - 4) + data[-4:]
                return '*' * len(data)
            elif data_type == 'email':
                if '@' in data:
                    username, domain = data.split('@', 1)
                    if len(username) > 2:
                        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
                    else:
                        masked_username = '*' * len(username)
                    return f"{masked_username}@{domain}"
                return '*' * len(data)
            elif data_type == 'phone':
                if len(data) >= 4:
                    return '*' * (len(data) - 4) + data[-4:]
                return '*' * len(data)
            else:
                return '*' * len(data)
                
        except Exception as e:
            self.logger.error(f"Failed to mask sensitive data: {e}")
            return '*' * len(data)
    
    def validate_pci_compliance(self, operation: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate PCI compliance for operations.
        
        Args:
            operation: Operation type
            data: Operation data
            
        Returns:
            Tuple of (is_compliant, violations)
        """
        violations = []
        
        # Check for sensitive data in logs
        sensitive_fields = ['card_number', 'cvc', 'expiry', 'account_number', 'routing_number']
        for field in sensitive_fields:
            if field in data and data[field]:
                violations.append(f"Sensitive field '{field}' should not be logged")
        
        # Check for proper encryption
        if self.pci_settings['encrypt_sensitive_data']:
            for field in sensitive_fields:
                if field in data and data[field]:
                    if not self._is_encrypted(data[field]):
                        violations.append(f"Sensitive field '{field}' should be encrypted")
        
        # Check for secure headers
        if self.pci_settings['secure_headers']:
            # This would be checked in the web framework
            pass
        
        return len(violations) == 0, violations
    
    def _is_encrypted(self, data: str) -> bool:
        """Check if data appears to be encrypted."""
        try:
            # Try to decode as base64
            decoded = base64.urlsafe_b64decode(data.encode())
            # Check if it looks like Fernet encrypted data
            return len(decoded) > 32 and decoded.startswith(b'gAAAAA')
        except:
            return False
    
    def get_secure_headers(self) -> Dict[str, str]:
        """Get secure headers for PCI compliance."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com; style-src 'self' 'unsafe-inline'; frame-src https://js.stripe.com https://hooks.stripe.com;",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }


class SecurityAuditLogger:
    """Logs security events for audit purposes."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize security audit logger."""
        self.logger = logging.getLogger('stripe.security.audit')
        self.redis_client = None
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}")
        
        # Configure audit logging
        self.audit_handler = logging.FileHandler('logs/stripe_security_audit.log')
        self.audit_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(self.audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_security_event(self, event: SecurityEvent) -> bool:
        """
        Log a security event.
        
        Args:
            event: Security event to log
            
        Returns:
            Success status
        """
        try:
            # Log to file
            self.logger.info(
                f"Security Event: {event.event_type} - {event.severity.value} - "
                f"Source: {event.source_ip} - User: {event.request_id} - "
                f"Details: {event.details}"
            )
            
            # Store in Redis for analysis
            if self.redis_client:
                event_data = {
                    'event_id': event.event_id,
                    'event_type': event.event_type,
                    'timestamp': event.timestamp.isoformat(),
                    'source_ip': event.source_ip,
                    'severity': event.severity.value,
                    'details': event.details,
                    'mitigated': event.mitigated,
                    'mitigation_action': event.mitigation_action
                }
                
                self.redis_client.lpush(
                    f"security_events:{event.severity.value}",
                    str(event_data)
                )
                self.redis_client.expire(
                    f"security_events:{event.severity.value}",
                    30 * 24 * 60 * 60  # 30 days
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
            return False
    
    def get_security_events(self, severity: Optional[SecurityLevel] = None, 
                           hours: int = 24) -> List[SecurityEvent]:
        """
        Get security events from the last N hours.
        
        Args:
            severity: Filter by severity level
            hours: Number of hours to look back
            
        Returns:
            List of security events
        """
        events = []
        
        try:
            if self.redis_client:
                since_time = datetime.now() - timedelta(hours=hours)
                
                if severity:
                    keys = [f"security_events:{severity.value}"]
                else:
                    keys = [f"security_events:{level.value}" for level in SecurityLevel]
                
                for key in keys:
                    event_data_list = self.redis_client.lrange(key, 0, -1)
                    for event_data_str in event_data_list:
                        try:
                            event_data = eval(event_data_str.decode())
                            event_time = datetime.fromisoformat(event_data['timestamp'])
                            
                            if event_time >= since_time:
                                event = SecurityEvent(
                                    event_id=event_data['event_id'],
                                    event_type=event_data['event_type'],
                                    timestamp=event_time,
                                    source_ip=event_data['source_ip'],
                                    user_agent=event_data.get('user_agent', ''),
                                    request_id=event_data.get('request_id', ''),
                                    severity=SecurityLevel(event_data['severity']),
                                    details=event_data['details'],
                                    mitigated=event_data.get('mitigated', False),
                                    mitigation_action=event_data.get('mitigation_action')
                                )
                                events.append(event)
                        except Exception as e:
                            self.logger.error(f"Failed to parse event data: {e}")
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get security events: {e}")
            return []


class StripeSecurityManager:
    """Main security manager that coordinates all security features."""
    
    def __init__(self, config, redis_url: Optional[str] = None):
        """Initialize Stripe security manager."""
        self.config = config
        self.webhook_security = WebhookSecurityManager(config)
        self.idempotency_manager = IdempotencyKeyManager(redis_url)
        self.rate_limit_manager = RateLimitManager(redis_url)
        self.pci_manager = PCISecurityManager()
        self.audit_logger = SecurityAuditLogger(redis_url)
        self.logger = logging.getLogger('stripe.security')
    
    def validate_webhook_request(self, payload: bytes, signature: str, 
                                source_ip: str, timestamp: Optional[str] = None,
                                user_agent: str = '', request_id: str = '') -> Tuple[bool, str]:
        """
        Comprehensive webhook request validation.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            source_ip: Source IP address
            timestamp: Webhook timestamp
            user_agent: User agent string
            request_id: Request identifier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check rate limiting
        allowed, rate_info = self.rate_limit_manager.check_rate_limit('webhook', source_ip)
        if not allowed:
            self._log_security_event(
                'webhook_rate_limit_exceeded',
                source_ip, user_agent, request_id,
                SecurityLevel.MEDIUM,
                {'rate_limit_info': rate_info}
            )
            return False, "Rate limit exceeded"
        
        # Verify source IP
        ip_allowed, ip_error = self.webhook_security.verify_source_ip(source_ip)
        if not ip_allowed:
            self._log_security_event(
                'webhook_invalid_ip',
                source_ip, user_agent, request_id,
                SecurityLevel.HIGH,
                {'error': ip_error}
            )
            return False, ip_error
        
        # Validate payload
        payload_valid, payload_error = self.webhook_security.validate_webhook_payload(payload)
        if not payload_valid:
            self._log_security_event(
                'webhook_invalid_payload',
                source_ip, user_agent, request_id,
                SecurityLevel.MEDIUM,
                {'error': payload_error}
            )
            return False, payload_error
        
        # Verify signature
        signature_valid, signature_error = self.webhook_security.verify_webhook_signature(
            payload, signature, timestamp
        )
        if not signature_valid:
            self._log_security_event(
                'webhook_invalid_signature',
                source_ip, user_agent, request_id,
                SecurityLevel.CRITICAL,
                {'error': signature_error}
            )
            return False, signature_error
        
        # Log successful validation
        self._log_security_event(
            'webhook_validated',
            source_ip, user_agent, request_id,
            SecurityLevel.LOW,
            {'validation_success': True}
        )
        
        return True, "Webhook validation successful"
    
    def process_api_request(self, operation: str, user_id: str, data: Dict[str, Any],
                           source_ip: str, user_agent: str = '', request_id: str = '') -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process API request with security checks.
        
        Args:
            operation: Operation type
            user_id: User identifier
            data: Request data
            source_ip: Source IP address
            user_agent: User agent string
            request_id: Request identifier
            
        Returns:
            Tuple of (success, message, result)
        """
        # Check rate limiting
        allowed, rate_info = self.rate_limit_manager.check_rate_limit(operation, user_id)
        if not allowed:
            self._log_security_event(
                'api_rate_limit_exceeded',
                source_ip, user_agent, request_id,
                SecurityLevel.MEDIUM,
                {'operation': operation, 'user_id': user_id, 'rate_limit_info': rate_info}
            )
            return False, "Rate limit exceeded", rate_info
        
        # Validate PCI compliance
        pci_compliant, violations = self.pci_manager.validate_pci_compliance(operation, data)
        if not pci_compliant:
            self._log_security_event(
                'pci_compliance_violation',
                source_ip, user_agent, request_id,
                SecurityLevel.HIGH,
                {'operation': operation, 'violations': violations}
            )
            return False, f"PCI compliance violations: {violations}", {'violations': violations}
        
        # Generate idempotency key
        idempotency_key = self.idempotency_manager.generate_idempotency_key(operation, user_id)
        
        # Check for existing idempotency key
        exists, cached_result = self.idempotency_manager.check_idempotency_key(idempotency_key)
        if exists:
            return True, "Request already processed", cached_result
        
        # Log successful processing
        self._log_security_event(
            'api_request_processed',
            source_ip, user_agent, request_id,
            SecurityLevel.LOW,
            {'operation': operation, 'user_id': user_id, 'idempotency_key': idempotency_key}
        )
        
        return True, "Request processed successfully", {
            'idempotency_key': idempotency_key,
            'rate_limit_info': rate_info
        }
    
    def _log_security_event(self, event_type: str, source_ip: str, user_agent: str,
                           request_id: str, severity: SecurityLevel, details: Dict[str, Any]):
        """Log a security event."""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            source_ip=source_ip,
            user_agent=user_agent,
            request_id=request_id,
            severity=severity,
            details=details
        )
        
        self.audit_logger.log_security_event(event)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for responses."""
        headers = self.pci_manager.get_secure_headers()
        headers.update({
            'X-Content-Security-Policy': headers['Content-Security-Policy'],
            'X-Frame-Options': headers['X-Frame-Options']
        })
        return headers
    
    def get_rate_limit_headers(self, operation: str, identifier: str) -> Dict[str, str]:
        """Get rate limit headers for responses."""
        return self.rate_limit_manager.get_rate_limit_headers(operation, identifier)


# Global security manager instance
security_manager = None


def get_stripe_security_manager(redis_url: Optional[str] = None) -> StripeSecurityManager:
    """Get global Stripe security manager instance."""
    global security_manager
    if security_manager is None:
        config = get_stripe_config()
        security_manager = StripeSecurityManager(config, redis_url)
    return security_manager 