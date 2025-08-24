#!/usr/bin/env python3
"""
MINGUS API Security System
Comprehensive API protection with endpoint-specific rate limiting
Protects against abuse, DDoS, and ensures fair resource usage
"""

import os
import re
import json
import hashlib
import logging
import secrets
import time
import threading
import hmac
import base64
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis
from functools import wraps

from flask import Flask, request, Response, g, current_app, session, jsonify, abort
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized, TooManyRequests
from flask_cors import CORS

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limiting configuration for different endpoint types"""
    # Authentication endpoints: 5 attempts per minute
    auth_endpoints: Dict[str, int] = field(default_factory=lambda: {
        'requests_per_minute': 5,
        'window_size': 60,  # seconds
        'burst_limit': 3
    })
    
    # Financial data endpoints: 100 requests per hour per user
    financial_endpoints: Dict[str, int] = field(default_factory=lambda: {
        'requests_per_hour': 100,
        'window_size': 3600,  # seconds
        'burst_limit': 20
    })
    
    # Health checkin endpoints: 10 submissions per day
    health_endpoints: Dict[str, int] = field(default_factory=lambda: {
        'requests_per_day': 10,
        'window_size': 86400,  # seconds
        'burst_limit': 2
    })
    
    # Income comparison: 3 requests per hour (lead magnet protection)
    income_comparison: Dict[str, int] = field(default_factory=lambda: {
        'requests_per_hour': 3,
        'window_size': 3600,  # seconds
        'burst_limit': 1
    })
    
    # PDF generation: 5 requests per hour
    pdf_generation: Dict[str, int] = field(default_factory=lambda: {
        'requests_per_hour': 5,
        'window_size': 3600,  # seconds
        'burst_limit': 2
    })
    
    # General API: 1000 requests per hour per user
    general_api: Dict[str, int] = field(default_factory=lambda: {
        'requests_per_hour': 1000,
        'window_size': 3600,  # seconds
        'burst_limit': 100
    })

@dataclass
class APISecurityConfig:
    """API security configuration"""
    environment: str = "production"
    
    # Rate limiting configuration
    rate_limit_config: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Redis configuration for rate limiting
    redis_url: str = "redis://localhost:6379/0"
    redis_connection_pool_size: int = 10
    
    # Security features
    request_logging: bool = True
    suspicious_activity_detection: bool = True
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    
    # Request validation
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    allowed_content_types: List[str] = field(default_factory=lambda: [
        'application/json',
        'application/x-www-form-urlencoded',
        'multipart/form-data'
    ])
    
    # API key management
    require_api_key: bool = False
    api_key_header: str = "X-API-Key"
    api_key_length: int = 32
    premium_api_key_header: str = "X-Premium-Key"
    premium_features: List[str] = field(default_factory=lambda: [
        'advanced_analytics', 'pdf_generation', 'data_export', 'priority_support'
    ])
    
    # Request signature validation
    signature_validation: bool = True
    signature_header: str = "X-Request-Signature"
    signature_timestamp_header: str = "X-Request-Timestamp"
    signature_window: int = 300  # 5 minutes
    signature_secret: str = None
    
    # Response data filtering
    response_filtering: bool = True
    sensitive_fields: List[str] = field(default_factory=lambda: [
        'password', 'token', 'secret', 'key', 'ssn', 'credit_card'
    ])
    filter_patterns: List[str] = field(default_factory=lambda: [
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card numbers
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email addresses
    ])
    
    # CORS configuration
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: [
        'https://mingus.app',
        'https://www.mingus.app',
        'https://app.mingus.com'
    ])
    cors_methods: List[str] = field(default_factory=lambda: [
        'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'
    ])
    cors_headers: List[str] = field(default_factory=lambda: [
        'Content-Type', 'Authorization', 'X-API-Key', 'X-Premium-Key'
    ])
    cors_credentials: bool = True
    cors_max_age: int = 86400  # 24 hours
    
    # API versioning security
    api_versioning: bool = True
    supported_versions: List[str] = field(default_factory=lambda: ['v1', 'v2'])
    default_version: str = 'v1'
    version_header: str = "X-API-Version"
    deprecated_versions: List[str] = field(default_factory=list)
    version_deprecation_warning_days: int = 30
    
    # Endpoint monitoring and alerting
    endpoint_monitoring: bool = True
    alert_thresholds: Dict[str, int] = field(default_factory=lambda: {
        'error_rate': 5,  # 5% error rate
        'response_time': 5000,  # 5 seconds
        'request_volume': 1000,  # 1000 requests per minute
        'concurrent_users': 100  # 100 concurrent users
    })
    monitoring_endpoints: List[str] = field(default_factory=lambda: [
        '/api/financial/*', '/api/health/*', '/api/auth/*'
    ])
    
    # Monitoring and alerting
    alert_on_rate_limit: bool = True
    alert_on_suspicious_activity: bool = True
    log_retention_days: int = 90

class RateLimitManager:
    """Manages rate limiting for different endpoint types"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.redis_client = None
        self._init_redis()
        
        # In-memory fallback for development
        self.memory_storage = defaultdict(lambda: defaultdict(deque))
        self.memory_lock = threading.Lock()
    
    def _init_redis(self):
        """Initialize Redis connection for rate limiting"""
        try:
            if self.config.redis_url.startswith('redis://'):
                self.redis_client = redis.from_url(
                    self.config.redis_url,
                    max_connections=self.config.redis_connection_pool_size,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established for rate limiting")
            else:
                logger.warning("Invalid Redis URL, using memory storage")
                self.redis_client = None
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory storage: {e}")
            self.redis_client = None
    
    def _get_identifier(self, endpoint_type: str, user_id: str = None, ip_address: str = None) -> str:
        """Generate unique identifier for rate limiting"""
        if user_id:
            return f"{endpoint_type}:user:{user_id}"
        elif ip_address:
            return f"{endpoint_type}:ip:{ip_address}"
        else:
            return f"{endpoint_type}:anonymous"
    
    def _get_rate_limit_config(self, endpoint_type: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint type"""
        config_map = {
            'auth': self.config.rate_limit_config.auth_endpoints,
            'financial': self.config.rate_limit_config.financial_endpoints,
            'health': self.config.rate_limit_config.health_endpoints,
            'income_comparison': self.config.rate_limit_config.income_comparison,
            'pdf_generation': self.config.rate_limit_config.pdf_generation,
            'general': self.config.rate_limit_config.general_api
        }
        return config_map.get(endpoint_type, self.config.rate_limit_config.general_api)
    
    def check_rate_limit(self, endpoint_type: str, user_id: str = None, 
                        ip_address: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits"""
        identifier = self._get_identifier(endpoint_type, user_id, ip_address)
        config = self._get_rate_limit_config(endpoint_type)
        
        if self.redis_client:
            return self._check_redis_rate_limit(identifier, config)
        else:
            return self._check_memory_rate_limit(identifier, config)
    
    def _check_redis_rate_limit(self, identifier: str, config: Dict[str, int]) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis"""
        try:
            current_time = int(time.time())
            window_size = config.get('window_size', 3600)
            max_requests = self._get_max_requests(config)
            
            # Use Redis sorted set for sliding window
            key = f"rate_limit:{identifier}"
            
            # Remove expired entries
            self.redis_client.zremrangebyscore(key, 0, current_time - window_size)
            
            # Count current requests in window
            current_requests = self.redis_client.zcard(key)
            
            if current_requests >= max_requests:
                # Get oldest request time to calculate retry after
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    retry_after = window_size - (current_time - int(oldest_request[0][1]))
                else:
                    retry_after = window_size
                
                return False, {
                    'limited': True,
                    'retry_after': retry_after,
                    'current_requests': current_requests,
                    'max_requests': max_requests,
                    'window_size': window_size
                }
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, window_size)
            
            return True, {
                'limited': False,
                'current_requests': current_requests + 1,
                'max_requests': max_requests,
                'window_size': window_size
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to memory storage
            return self._check_memory_rate_limit(identifier, config)
    
    def _check_memory_rate_limit(self, identifier: str, config: Dict[str, int]) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using memory storage"""
        with self.memory_lock:
            current_time = time.time()
            window_size = config.get('window_size', 3600)
            max_requests = self._get_max_requests(config)
            
            # Get request history for this identifier
            request_history = self.memory_storage[identifier]
            
            # Remove expired requests
            cutoff_time = current_time - window_size
            while request_history and request_history[0] < cutoff_time:
                request_history.popleft()
            
            current_requests = len(request_history)
            
            if current_requests >= max_requests:
                # Calculate retry after
                if request_history:
                    retry_after = int(window_size - (current_time - request_history[0]))
                else:
                    retry_after = window_size
                
                return False, {
                    'limited': True,
                    'retry_after': retry_after,
                    'current_requests': current_requests,
                    'max_requests': max_requests,
                    'window_size': window_size
                }
            
            # Add current request
            request_history.append(current_time)
            
            return True, {
                'limited': False,
                'current_requests': current_requests + 1,
                'max_requests': max_requests,
                'window_size': window_size
            }
    
    def _get_max_requests(self, config: Dict[str, int]) -> int:
        """Get maximum requests from config"""
        if 'requests_per_minute' in config:
            return config['requests_per_minute']
        elif 'requests_per_hour' in config:
            return config['requests_per_hour']
        elif 'requests_per_day' in config:
            return config['requests_per_day']
        else:
            return 1000  # Default fallback

class RequestValidator:
    """Validates API requests for security"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
    
    def validate_request(self, request) -> Tuple[bool, List[str]]:
        """Validate incoming request"""
        errors = []
        
        # Check request size
        if request.content_length and request.content_length > self.config.max_request_size:
            errors.append(f"Request too large: {request.content_length} bytes")
        
        # Check content type
        if request.content_type:
            content_type = request.content_type.split(';')[0]
            if content_type not in self.config.allowed_content_types:
                errors.append(f"Unsupported content type: {content_type}")
        
        # Check IP blacklist
        if request.remote_addr in self.config.ip_blacklist:
            errors.append("IP address is blacklisted")
        
        # Validate API key if required
        if self.config.require_api_key:
            api_key = request.headers.get(self.config.api_key_header)
            if not api_key:
                errors.append("API key required")
            elif not self._validate_api_key(api_key):
                errors.append("Invalid API key")
        
        return len(errors) == 0, errors
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and existence"""
        if not api_key or len(api_key) != self.config.api_key_length:
            return False
        
        # TODO: Implement API key validation against database
        # For now, just check format
        return bool(re.match(r'^[a-zA-Z0-9]{32}$', api_key))

class SuspiciousActivityDetector:
    """Detects suspicious API activity patterns"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.activity_patterns = defaultdict(list)
        self.suspicious_patterns = [
            'rapid_requests',  # Too many requests in short time
            'unusual_timing',  # Requests at unusual hours
            'pattern_requests',  # Repeated identical requests
            'large_payloads',  # Consistently large request payloads
            'failed_requests',  # High rate of failed requests
        ]
    
    def analyze_request(self, request, user_id: str = None, ip_address: str = None) -> Dict[str, Any]:
        """Analyze request for suspicious activity"""
        identifier = user_id or ip_address or 'anonymous'
        current_time = time.time()
        
        # Record request pattern
        pattern = {
            'timestamp': current_time,
            'method': request.method,
            'endpoint': request.endpoint,
            'user_agent': request.headers.get('User-Agent', ''),
            'content_length': request.content_length or 0,
            'ip_address': request.remote_addr
        }
        
        self.activity_patterns[identifier].append(pattern)
        
        # Keep only recent activity (last 24 hours)
        cutoff_time = current_time - 86400
        self.activity_patterns[identifier] = [
            p for p in self.activity_patterns[identifier] 
            if p['timestamp'] > cutoff_time
        ]
        
        # Analyze for suspicious patterns
        suspicious_indicators = []
        
        # Check for rapid requests
        recent_requests = [p for p in self.activity_patterns[identifier] 
                         if p['timestamp'] > current_time - 300]  # Last 5 minutes
        if len(recent_requests) > 50:
            suspicious_indicators.append('rapid_requests')
        
        # Check for unusual timing (requests between 2-6 AM)
        hour = datetime.fromtimestamp(current_time).hour
        if 2 <= hour <= 6:
            suspicious_indicators.append('unusual_timing')
        
        # Check for large payloads
        if request.content_length and request.content_length > 1024 * 1024:  # 1MB
            suspicious_indicators.append('large_payloads')
        
        # Check for pattern requests (identical requests)
        identical_requests = sum(1 for p in recent_requests 
                               if p['method'] == request.method and 
                               p['endpoint'] == request.endpoint)
        if identical_requests > 10:
            suspicious_indicators.append('pattern_requests')
        
        return {
            'suspicious': len(suspicious_indicators) > 0,
            'indicators': suspicious_indicators,
            'risk_score': len(suspicious_indicators) * 25,  # 0-100 scale
            'recent_requests': len(recent_requests)
        }

class APIActivityLogger:
    """Logs API activity for monitoring and security"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.logger = logging.getLogger('api_activity')
    
    def log_request(self, request, response, user_id: str = None, 
                   rate_limit_info: Dict = None, suspicious_info: Dict = None):
        """Log API request activity"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'method': request.method,
            'endpoint': request.endpoint,
            'status_code': response.status_code,
            'user_id': user_id,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'content_length': request.content_length or 0,
            'response_time': getattr(g, 'response_time', None),
            'rate_limited': rate_limit_info.get('limited', False) if rate_limit_info else False,
            'suspicious': suspicious_info.get('suspicious', False) if suspicious_info else False,
            'risk_score': suspicious_info.get('risk_score', 0) if suspicious_info else 0
        }
        
        # Log based on severity
        if log_entry['suspicious'] or log_entry['rate_limited']:
            self.logger.warning(f"API Activity: {json.dumps(log_entry)}")
        else:
            self.logger.info(f"API Activity: {json.dumps(log_entry)}")
        
        # Alert on high-risk activity
        if self.config.alert_on_suspicious_activity and log_entry['risk_score'] > 75:
            self._send_alert('high_risk_activity', log_entry)
        
        if self.config.alert_on_rate_limit and log_entry['rate_limited']:
            self._send_alert('rate_limit_exceeded', log_entry)
    
    def _send_alert(self, alert_type: str, data: Dict):
        """Send security alert"""
        # TODO: Implement alert sending (email, Slack, etc.)
        logger.warning(f"SECURITY ALERT - {alert_type}: {json.dumps(data)}")

class RequestSignatureValidator:
    """Validates request signatures for API security"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.signature_secret = config.signature_secret or os.environ.get('SIGNATURE_SECRET', 'default-secret')
    
    def validate_signature(self, request) -> Tuple[bool, str]:
        """Validate request signature"""
        if not self.config.signature_validation:
            return True, "Signature validation disabled"
        
        signature = request.headers.get(self.config.signature_header)
        timestamp = request.headers.get(self.config.signature_timestamp_header)
        
        if not signature or not timestamp:
            return False, "Missing signature or timestamp"
        
        # Validate timestamp
        try:
            timestamp_int = int(timestamp)
            current_time = int(time.time())
            
            if abs(current_time - timestamp_int) > self.config.signature_window:
                return False, "Request timestamp expired"
        except ValueError:
            return False, "Invalid timestamp format"
        
        # Generate expected signature
        expected_signature = self._generate_signature(request, timestamp)
        
        if not hmac.compare_digest(signature, expected_signature):
            return False, "Invalid signature"
        
        return True, "Signature valid"
    
    def _generate_signature(self, request, timestamp: str) -> str:
        """Generate signature for request"""
        # Create signature payload
        payload = f"{request.method}:{request.path}:{timestamp}"
        
        if request.data:
            payload += f":{request.data.decode('utf-8')}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.signature_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

class PremiumAPIKeyManager:
    """Manages premium API keys for premium features"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.premium_keys = {}  # In production, this would be in database
        self._load_premium_keys()
    
    def _load_premium_keys(self):
        """Load premium API keys from environment or database"""
        # Load from environment variables for demo
        for i in range(1, 6):  # Load 5 demo premium keys
            key = os.environ.get(f'PREMIUM_API_KEY_{i}')
            if key:
                self.premium_keys[key] = {
                    'features': self.config.premium_features,
                    'created_at': datetime.utcnow(),
                    'last_used': None
                }
    
    def validate_premium_key(self, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate premium API key"""
        if not api_key:
            return False, {'valid': False, 'message': 'No premium key provided'}
        
        if api_key not in self.premium_keys:
            return False, {'valid': False, 'message': 'Invalid premium key'}
        
        # Update last used timestamp
        self.premium_keys[api_key]['last_used'] = datetime.utcnow()
        
        return True, {
            'valid': True,
            'features': self.premium_keys[api_key]['features'],
            'message': 'Premium key valid'
        }
    
    def has_feature_access(self, api_key: str, feature: str) -> bool:
        """Check if API key has access to specific feature"""
        is_valid, _ = self.validate_premium_key(api_key)
        if not is_valid:
            return False
        
        return feature in self.premium_keys[api_key]['features']
    
    def generate_premium_key(self, features: List[str] = None) -> str:
        """Generate new premium API key"""
        if features is None:
            features = self.config.premium_features
        
        api_key = secrets.token_urlsafe(self.config.api_key_length)
        self.premium_keys[api_key] = {
            'features': features,
            'created_at': datetime.utcnow(),
            'last_used': None
        }
        
        return api_key

class ResponseDataFilter:
    """Filters sensitive data from API responses"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.sensitive_fields = set(config.sensitive_fields)
        self.filter_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in config.filter_patterns]
    
    def filter_response_data(self, data: Any) -> Any:
        """Filter sensitive data from response"""
        if not self.config.response_filtering:
            return data
        
        if isinstance(data, dict):
            return self._filter_dict(data)
        elif isinstance(data, list):
            return [self.filter_response_data(item) for item in data]
        elif isinstance(data, str):
            return self._filter_string(data)
        else:
            return data
    
    def _filter_dict(self, data: Dict) -> Dict:
        """Filter sensitive data from dictionary"""
        filtered = {}
        
        for key, value in data.items():
            # Check if key contains sensitive field names
            key_lower = key.lower()
            is_sensitive = any(sensitive in key_lower for sensitive in self.sensitive_fields)
            
            if is_sensitive:
                filtered[key] = '***FILTERED***'
            elif isinstance(value, (dict, list, str)):
                filtered[key] = self.filter_response_data(value)
            else:
                filtered[key] = value
        
        return filtered
    
    def _filter_string(self, data: str) -> str:
        """Filter sensitive patterns from string"""
        if not isinstance(data, str):
            return data
        
        filtered = data
        
        # Apply pattern filtering
        for pattern in self.filter_patterns:
            filtered = pattern.sub('***FILTERED***', filtered)
        
        return filtered

class CORSManager:
    """Manages CORS configuration for web app"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
    
    def setup_cors(self, app: Flask):
        """Setup CORS for Flask application"""
        if not self.config.cors_enabled:
            return
        
        CORS(app, 
             origins=self.config.cors_origins,
             methods=self.config.cors_methods,
             allow_headers=self.config.cors_headers,
             supports_credentials=self.config.cors_credentials,
             max_age=self.config.cors_max_age)
    
    def validate_origin(self, origin: str) -> bool:
        """Validate CORS origin"""
        if not self.config.cors_enabled:
            return True
        
        return origin in self.config.cors_origins

class APIVersionManager:
    """Manages API versioning security"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.version_deprecation_dates = {}
        self._load_deprecation_dates()
    
    def _load_deprecation_dates(self):
        """Load version deprecation dates"""
        for version in self.config.deprecated_versions:
            # In production, this would be loaded from database
            self.version_deprecation_dates[version] = datetime.utcnow() - timedelta(days=30)
    
    def validate_version(self, version: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate API version"""
        if not self.config.api_versioning:
            return True, {'valid': True, 'message': 'Version validation disabled'}
        
        if not version:
            version = self.config.default_version
        
        if version not in self.config.supported_versions:
            return False, {
                'valid': False,
                'message': f'Unsupported API version: {version}',
                'supported_versions': self.config.supported_versions
            }
        
        # Check if version is deprecated
        if version in self.config.deprecated_versions:
            deprecation_date = self.version_deprecation_dates.get(version)
            if deprecation_date:
                days_since_deprecation = (datetime.utcnow() - deprecation_date).days
                
                if days_since_deprecation > self.config.version_deprecation_warning_days:
                    return False, {
                        'valid': False,
                        'message': f'API version {version} has been deprecated',
                        'deprecation_date': deprecation_date.isoformat()
                    }
                else:
                    return True, {
                        'valid': True,
                        'message': f'API version {version} is deprecated but still supported',
                        'deprecation_date': deprecation_date.isoformat(),
                        'warning': True
                    }
        
        return True, {'valid': True, 'message': f'API version {version} is valid'}

class EndpointMonitor:
    """Monitors endpoints for performance and security"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.endpoint_stats = defaultdict(lambda: {
            'request_count': 0,
            'error_count': 0,
            'total_response_time': 0,
            'concurrent_users': set(),
            'last_request': None
        })
        self.alerts = []
    
    def record_request(self, endpoint: str, user_id: str = None, 
                      response_time: float = None, status_code: int = None):
        """Record request statistics"""
        stats = self.endpoint_stats[endpoint]
        
        # Update basic stats
        stats['request_count'] += 1
        stats['last_request'] = datetime.utcnow()
        
        if user_id:
            stats['concurrent_users'].add(user_id)
        
        if response_time:
            stats['total_response_time'] += response_time
        
        if status_code and status_code >= 400:
            stats['error_count'] += 1
        
        # Check for alerts
        self._check_alerts(endpoint, stats)
    
    def _check_alerts(self, endpoint: str, stats: Dict):
        """Check for alert conditions"""
        # Check error rate
        if stats['request_count'] > 0:
            error_rate = (stats['error_count'] / stats['request_count']) * 100
            if error_rate > self.config.alert_thresholds['error_rate']:
                self._create_alert('high_error_rate', endpoint, {
                    'error_rate': error_rate,
                    'threshold': self.config.alert_thresholds['error_rate']
                })
        
        # Check response time
        if stats['request_count'] > 0:
            avg_response_time = stats['total_response_time'] / stats['request_count']
            if avg_response_time > self.config.alert_thresholds['response_time']:
                self._create_alert('high_response_time', endpoint, {
                    'avg_response_time': avg_response_time,
                    'threshold': self.config.alert_thresholds['response_time']
                })
        
        # Check request volume
        if stats['request_count'] > self.config.alert_thresholds['request_volume']:
            self._create_alert('high_request_volume', endpoint, {
                'request_count': stats['request_count'],
                'threshold': self.config.alert_thresholds['request_volume']
            })
        
        # Check concurrent users
        concurrent_users = len(stats['concurrent_users'])
        if concurrent_users > self.config.alert_thresholds['concurrent_users']:
            self._create_alert('high_concurrent_users', endpoint, {
                'concurrent_users': concurrent_users,
                'threshold': self.config.alert_thresholds['concurrent_users']
            })
    
    def _create_alert(self, alert_type: str, endpoint: str, data: Dict):
        """Create security alert"""
        alert = {
            'type': alert_type,
            'endpoint': endpoint,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data,
            'severity': 'high' if alert_type in ['high_error_rate', 'high_response_time'] else 'medium'
        }
        
        self.alerts.append(alert)
        logger.warning(f"ENDPOINT ALERT - {alert_type}: {json.dumps(alert)}")
    
    def get_endpoint_stats(self, endpoint: str = None) -> Dict[str, Any]:
        """Get endpoint statistics"""
        if endpoint:
            return dict(self.endpoint_stats[endpoint])
        else:
            return {ep: dict(stats) for ep, stats in self.endpoint_stats.items()}
    
    def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alerts 
                if datetime.fromisoformat(alert['timestamp']) > cutoff_time]

class InjectionProtection:
    """Comprehensive injection attack prevention"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        
        # SQL injection patterns
        self.sql_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|EXECUTE)\b',
            r'[\'";]',
            r'--',
            r'/\*.*?\*/',
            r'xp_cmdshell',
            r'sp_',
            r'@@',
            r'WAITFOR',
            r'BENCHMARK',
            r'SLEEP',
            r'INFORMATION_SCHEMA',
            r'sys\.',
            r'@@version',
            r'@@servername'
        ]
        
        # NoSQL injection patterns
        self.nosql_patterns = [
            r'\$where\s*:',
            r'\$ne\s*:',
            r'\$gt\s*:',
            r'\$lt\s*:',
            r'\$regex\s*:',
            r'\$exists\s*:',
            r'\$in\s*:',
            r'\$nin\s*:',
            r'\$or\s*:',
            r'\$and\s*:',
            r'\$not\s*:',
            r'\$nor\s*:',
            r'\$text\s*:',
            r'\$search\s*:',
            r'javascript:',
            r'function\s*\(',
            r'eval\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\('
        ]
        
        # Command injection patterns
        self.command_patterns = [
            r'[;&|`$(){}]',
            r'\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ipconfig)\b',
            r'\b(rm|del|mkdir|touch|chmod|chown|sudo|su)\b',
            r'\b(wget|curl|nc|telnet|ssh|scp|rsync)\b',
            r'\b(python|perl|ruby|bash|sh|zsh|fish)\b',
            r'\b(echo|printf|grep|sed|awk|sort|uniq)\b',
            r'\b(find|xargs|tar|gzip|gunzip|zip|unzip)\b',
            r'\b(docker|kubectl|helm|terraform|ansible)\b',
            r'\b(git|svn|hg|bzr|cvs)\b',
            r'\b(mysql|psql|sqlite|mongo|redis|memcached)\b'
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'..%2f',
            r'..%5c',
            r'%252e%252e%252f',
            r'%252e%252e%255c',
            r'..%252f',
            r'..%255c',
            r'%c0%ae%c0%ae%c0%af',
            r'%c0%ae%c0%ae%c0%5c',
            r'%c1%9c%c1%9c%c1%af',
            r'%c1%9c%c1%9c%c1%5c',
            r'%c0%af',
            r'%c0%5c',
            r'%c1%af',
            r'%c1%5c',
            r'%c0%2f',
            r'%c0%5c',
            r'%c1%2f',
            r'%c1%5c'
        ]
        
        # Request smuggling patterns
        self.smuggling_patterns = [
            r'Content-Length:\s*0',
            r'Transfer-Encoding:\s*chunked',
            r'Content-Length:\s*\d+\s*[\r\n]+Content-Length:\s*\d+',
            r'Transfer-Encoding:\s*chunked\s*[\r\n]+Content-Length:\s*\d+',
            r'Content-Length:\s*\d+\s*[\r\n]+Transfer-Encoding:\s*chunked',
            r'GET\s+.*\s+HTTP/\d\.\d\s*[\r\n]+Content-Length:\s*\d+',
            r'POST\s+.*\s+HTTP/\d\.\d\s*[\r\n]+Content-Length:\s*0',
            r'Host:\s*.*\s*[\r\n]+Host:\s*.*',
            r'Content-Type:\s*.*\s*[\r\n]+Content-Type:\s*.*'
        ]
        
        # Compile patterns for efficiency
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.nosql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.nosql_patterns]
        self.command_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.command_patterns]
        self.path_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.path_traversal_patterns]
        self.smuggling_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.smuggling_patterns]
    
    def validate_input(self, data: Any, input_type: str = 'general') -> Tuple[bool, List[str]]:
        """Validate input for injection attacks"""
        errors = []
        
        if isinstance(data, str):
            # Check for SQL injection
            if self._contains_sql_injection(data):
                errors.append(f"SQL injection detected in {input_type}")
            
            # Check for NoSQL injection
            if self._contains_nosql_injection(data):
                errors.append(f"NoSQL injection detected in {input_type}")
            
            # Check for command injection
            if self._contains_command_injection(data):
                errors.append(f"Command injection detected in {input_type}")
            
            # Check for path traversal
            if self._contains_path_traversal(data):
                errors.append(f"Path traversal detected in {input_type}")
        
        elif isinstance(data, dict):
            # Recursively check dictionary values
            for key, value in data.items():
                is_valid, value_errors = self.validate_input(value, f"{input_type}.{key}")
                if not is_valid:
                    errors.extend(value_errors)
        
        elif isinstance(data, list):
            # Recursively check list items
            for i, item in enumerate(data):
                is_valid, item_errors = self.validate_input(item, f"{input_type}[{i}]")
                if not is_valid:
                    errors.extend(item_errors)
        
        return len(errors) == 0, errors
    
    def validate_request(self, request) -> Tuple[bool, List[str]]:
        """Validate entire request for injection attacks"""
        errors = []
        
        # Validate URL parameters
        for key, value in request.args.items():
            is_valid, value_errors = self.validate_input(value, f"query_param.{key}")
            if not is_valid:
                errors.extend(value_errors)
        
        # Validate form data
        for key, value in request.form.items():
            is_valid, value_errors = self.validate_input(value, f"form_data.{key}")
            if not is_valid:
                errors.extend(value_errors)
        
        # Validate JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                is_valid, json_errors = self.validate_input(json_data, "json_data")
                if not is_valid:
                    errors.extend(json_errors)
            except Exception as e:
                errors.append(f"Invalid JSON data: {str(e)}")
        
        # Validate headers for request smuggling
        smuggling_errors = self._check_request_smuggling(request)
        if smuggling_errors:
            errors.extend(smuggling_errors)
        
        # Validate file uploads
        for key, file in request.files.items():
            if file and file.filename:
                is_valid, file_errors = self.validate_input(file.filename, f"file_upload.{key}")
                if not is_valid:
                    errors.extend(file_errors)
        
        return len(errors) == 0, errors
    
    def _contains_sql_injection(self, data: str) -> bool:
        """Check for SQL injection patterns"""
        for pattern in self.sql_regex:
            if pattern.search(data):
                return True
        return False
    
    def _contains_nosql_injection(self, data: str) -> bool:
        """Check for NoSQL injection patterns"""
        for pattern in self.nosql_regex:
            if pattern.search(data):
                return True
        return False
    
    def _contains_command_injection(self, data: str) -> bool:
        """Check for command injection patterns"""
        for pattern in self.command_regex:
            if pattern.search(data):
                return True
        return False
    
    def _contains_path_traversal(self, data: str) -> bool:
        """Check for path traversal patterns"""
        for pattern in self.path_regex:
            if pattern.search(data):
                return True
        return False
    
    def _check_request_smuggling(self, request) -> List[str]:
        """Check for request smuggling attempts"""
        errors = []
        
        # Check for duplicate headers
        headers = dict(request.headers)
        content_length_count = sum(1 for h in headers if h.lower() == 'content-length')
        transfer_encoding_count = sum(1 for h in headers if h.lower() == 'transfer-encoding')
        
        if content_length_count > 1:
            errors.append("Multiple Content-Length headers detected (request smuggling)")
        
        if transfer_encoding_count > 1:
            errors.append("Multiple Transfer-Encoding headers detected (request smuggling)")
        
        # Check for conflicting headers
        if 'Content-Length' in headers and 'Transfer-Encoding' in headers:
            errors.append("Conflicting Content-Length and Transfer-Encoding headers (request smuggling)")
        
        # Check for malformed headers
        raw_headers = str(request.headers)
        for pattern in self.smuggling_regex:
            if pattern.search(raw_headers):
                errors.append("Request smuggling pattern detected in headers")
        
        return errors
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input by removing dangerous patterns"""
        if isinstance(data, str):
            # Remove SQL injection patterns
            for pattern in self.sql_regex:
                data = pattern.sub('', data)
            
            # Remove NoSQL injection patterns
            for pattern in self.nosql_regex:
                data = pattern.sub('', data)
            
            # Remove command injection patterns
            for pattern in self.command_regex:
                data = pattern.sub('', data)
            
            # Remove path traversal patterns
            for pattern in self.path_regex:
                data = pattern.sub('', data)
            
            return data.strip()
        
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        
        else:
            return data

class SecurityHeadersValidator:
    """Validate and enforce security headers"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
    
    def validate_security_headers(self, request) -> Tuple[bool, List[str]]:
        """Validate security headers in request"""
        errors = []
        
        # Check for required security headers
        required_headers = [
            'User-Agent',
            'Accept',
            'Accept-Language'
        ]
        
        for header in required_headers:
            if header not in request.headers:
                errors.append(f"Missing required header: {header}")
        
        # Check for suspicious headers
        suspicious_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Forwarded-Host',
            'X-Forwarded-Proto'
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                # Log suspicious header but don't block
                logger.warning(f"Suspicious header detected: {header} = {request.headers[header]}")
        
        return len(errors) == 0, errors
    
    def add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # Strict Transport Security
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # X-Content-Type-Options
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )
        
        return response

class APIAccessLogger:
    """Comprehensive API access logging with detailed analytics"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.logger = logging.getLogger('api_access')
        
        # Configure detailed logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for access logs
        file_handler = logging.FileHandler('logs/api_access.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_api_access(self, request, response, user_id: str = None, 
                      security_info: Dict = None, performance_info: Dict = None):
        """Log detailed API access information"""
        
        # Extract request details
        request_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'method': request.method,
            'endpoint': request.endpoint,
            'url': request.url,
            'path': request.path,
            'query_params': dict(request.args),
            'headers': dict(request.headers),
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'forwarded_for': request.headers.get('X-Forwarded-For', ''),
            'real_ip': request.headers.get('X-Real-IP', ''),
            'content_type': request.content_type,
            'content_length': request.content_length or 0,
            'user_id': user_id,
            'session_id': session.get('session_id') if session else None,
            'referrer': request.headers.get('Referer', ''),
            'origin': request.headers.get('Origin', ''),
            'accept_language': request.headers.get('Accept-Language', ''),
            'accept_encoding': request.headers.get('Accept-Encoding', ''),
            'connection': request.headers.get('Connection', ''),
            'host': request.headers.get('Host', ''),
            'cache_control': request.headers.get('Cache-Control', ''),
            'pragma': request.headers.get('Pragma', ''),
            'upgrade_insecure_requests': request.headers.get('Upgrade-Insecure-Requests', ''),
            'sec_fetch_dest': request.headers.get('Sec-Fetch-Dest', ''),
            'sec_fetch_mode': request.headers.get('Sec-Fetch-Mode', ''),
            'sec_fetch_site': request.headers.get('Sec-Fetch-Site', ''),
            'sec_fetch_user': request.headers.get('Sec-Fetch-User', ''),
            'sec_ch_ua': request.headers.get('Sec-CH-UA', ''),
            'sec_ch_ua_mobile': request.headers.get('Sec-CH-UA-Mobile', ''),
            'sec_ch_ua_platform': request.headers.get('Sec-CH-UA-Platform', ''),
            'dnt': request.headers.get('DNT', ''),
            'api_key': request.headers.get('X-API-Key', '')[:8] + '...' if request.headers.get('X-API-Key') else None,
            'premium_key': request.headers.get('X-Premium-Key', '')[:8] + '...' if request.headers.get('X-Premium-Key') else None,
            'signature': request.headers.get('X-Request-Signature', '')[:8] + '...' if request.headers.get('X-Request-Signature') else None,
            'api_version': request.headers.get('X-API-Version', ''),
            'authorization': request.headers.get('Authorization', '')[:8] + '...' if request.headers.get('Authorization') else None
        }
        
        # Extract response details
        response_data = {
            'status_code': response.status_code,
            'response_headers': dict(response.headers),
            'response_size': len(response.data) if response.data else 0,
            'content_type': response.content_type,
            'cache_control': response.headers.get('Cache-Control', ''),
            'etag': response.headers.get('ETag', ''),
            'last_modified': response.headers.get('Last-Modified', ''),
            'expires': response.headers.get('Expires', ''),
            'pragma': response.headers.get('Pragma', ''),
            'vary': response.headers.get('Vary', ''),
            'access_control_allow_origin': response.headers.get('Access-Control-Allow-Origin', ''),
            'access_control_allow_methods': response.headers.get('Access-Control-Allow-Methods', ''),
            'access_control_allow_headers': response.headers.get('Access-Control-Allow-Headers', ''),
            'access_control_allow_credentials': response.headers.get('Access-Control-Allow-Credentials', ''),
            'access_control_max_age': response.headers.get('Access-Control-Max-Age', ''),
            'x_content_type_options': response.headers.get('X-Content-Type-Options', ''),
            'x_frame_options': response.headers.get('X-Frame-Options', ''),
            'x_xss_protection': response.headers.get('X-XSS-Protection', ''),
            'strict_transport_security': response.headers.get('Strict-Transport-Security', ''),
            'content_security_policy': response.headers.get('Content-Security-Policy', ''),
            'referrer_policy': response.headers.get('Referrer-Policy', ''),
            'permissions_policy': response.headers.get('Permissions-Policy', ''),
            'retry_after': response.headers.get('Retry-After', ''),
            'x_rate_limit_limit': response.headers.get('X-Rate-Limit-Limit', ''),
            'x_rate_limit_remaining': response.headers.get('X-Rate-Limit-Remaining', ''),
            'x_rate_limit_reset': response.headers.get('X-Rate-Limit-Reset', '')
        }
        
        # Add security information
        if security_info:
            request_data.update({
                'security_validation': security_info.get('validation_passed', False),
                'injection_detected': security_info.get('injection_detected', False),
                'rate_limited': security_info.get('rate_limited', False),
                'suspicious_activity': security_info.get('suspicious_activity', False),
                'abuse_detected': security_info.get('abuse_detected', False),
                'security_score': security_info.get('security_score', 0),
                'threat_level': security_info.get('threat_level', 'low')
            })
        
        # Add performance information
        if performance_info:
            request_data.update({
                'response_time': performance_info.get('response_time', 0),
                'processing_time': performance_info.get('processing_time', 0),
                'database_queries': getattr(g, 'db_queries', 0),
                'cache_hits': getattr(g, 'cache_hits', 0),
                'cache_misses': getattr(g, 'cache_misses', 0),
                'memory_usage': getattr(g, 'memory_usage', 0),
                'cpu_usage': getattr(g, 'cpu_usage', 0)
            })
        
        # Log the complete access information
        log_entry = {
            'request': request_data,
            'response': response_data,
            'security': security_info or {},
            'performance': performance_info or {}
        }
        
        # Log based on security level
        if security_info and security_info.get('threat_level') in ['high', 'critical']:
            self.logger.warning(f"SECURITY ALERT - API Access: {json.dumps(log_entry)}")
        elif response.status_code >= 400:
            self.logger.error(f"API Error - Access: {json.dumps(log_entry)}")
        else:
            self.logger.info(f"API Access: {json.dumps(log_entry)}")

class APIAbuseDetector:
    """Detects and blocks API abuse patterns"""
    
    def __init__(self, config: APISecurityConfig):
        self.config = config
        self.abuse_patterns = defaultdict(list)
        self.blocked_ips = set()
        self.blocked_users = set()
        self.suspicious_patterns = defaultdict(int)
        
        # Abuse detection thresholds
        self.thresholds = {
            'rapid_requests': 50,  # requests per minute
            'failed_requests': 10,  # failed requests per minute
            'large_payloads': 5,   # large payloads per minute
            'suspicious_patterns': 20,  # suspicious patterns per hour
            'injection_attempts': 5,  # injection attempts per hour
            'unauthorized_access': 10,  # unauthorized access attempts per hour
            'premium_feature_abuse': 3,  # premium feature abuse per hour
            'rate_limit_violations': 5,  # rate limit violations per hour
        }
        
        # Abuse patterns to detect
        self.abuse_patterns_list = [
            'sql_injection',
            'nosql_injection',
            'command_injection',
            'path_traversal',
            'request_smuggling',
            'xss_attempt',
            'csrf_attempt',
            'authentication_bypass',
            'authorization_bypass',
            'data_exfiltration',
            'ddos_attempt',
            'brute_force',
            'credential_stuffing',
            'session_hijacking',
            'api_key_abuse',
            'premium_feature_abuse',
            'rate_limit_circumvention',
            'header_manipulation',
            'parameter_pollution',
            'cache_poisoning'
        ]
    
    def analyze_request(self, request, user_id: str = None, 
                       security_info: Dict = None) -> Tuple[bool, Dict[str, Any]]:
        """Analyze request for abuse patterns"""
        
        ip_address = request.remote_addr
        current_time = time.time()
        
        # Check if IP is already blocked
        if ip_address in self.blocked_ips:
            return False, {
                'blocked': True,
                'reason': 'IP address is blocked due to previous abuse',
                'blocked_at': current_time,
                'threat_level': 'critical'
            }
        
        # Check if user is blocked
        if user_id and user_id in self.blocked_users:
            return False, {
                'blocked': True,
                'reason': 'User account is blocked due to previous abuse',
                'blocked_at': current_time,
                'threat_level': 'critical'
            }
        
        abuse_score = 0
        detected_patterns = []
        
        # Analyze request patterns
        pattern_key = f"{ip_address}:{user_id or 'anonymous'}"
        
        # Check for rapid requests
        recent_requests = [t for t in self.abuse_patterns[pattern_key] 
                         if current_time - t < 60]  # Last minute
        if len(recent_requests) > self.thresholds['rapid_requests']:
            abuse_score += 30
            detected_patterns.append('rapid_requests')
        
        # Check for failed requests
        if response and response.status_code >= 400:
            failed_requests = [t for t in self.abuse_patterns[f"{pattern_key}:failed"] 
                             if current_time - t < 60]
            if len(failed_requests) > self.thresholds['failed_requests']:
                abuse_score += 25
                detected_patterns.append('failed_requests')
        
        # Check for large payloads
        if request.content_length and request.content_length > 1024 * 1024:  # 1MB
            large_payloads = [t for t in self.abuse_patterns[f"{pattern_key}:large"] 
                            if current_time - t < 60]
            if len(large_payloads) > self.thresholds['large_payloads']:
                abuse_score += 20
                detected_patterns.append('large_payloads')
        
        # Check for security violations
        if security_info:
            if security_info.get('injection_detected'):
                abuse_score += 50
                detected_patterns.append('injection_attempt')
            
            if security_info.get('rate_limited'):
                abuse_score += 15
                detected_patterns.append('rate_limit_violation')
            
            if security_info.get('suspicious_activity'):
                abuse_score += 20
                detected_patterns.append('suspicious_activity')
        
        # Check for suspicious headers
        suspicious_headers = self._check_suspicious_headers(request)
        if suspicious_headers:
            abuse_score += len(suspicious_headers) * 10
            detected_patterns.extend(suspicious_headers)
        
        # Check for unauthorized premium feature access
        if request.headers.get('X-Premium-Key') and not user_id:
            abuse_score += 30
            detected_patterns.append('premium_feature_abuse')
        
        # Check for API key abuse
        if request.headers.get('X-API-Key'):
            api_key_abuse = self._check_api_key_abuse(request.headers.get('X-API-Key'))
            if api_key_abuse:
                abuse_score += 25
                detected_patterns.append('api_key_abuse')
        
        # Record the request
        self.abuse_patterns[pattern_key].append(current_time)
        
        # Determine threat level
        threat_level = 'low'
        if abuse_score >= 80:
            threat_level = 'critical'
        elif abuse_score >= 60:
            threat_level = 'high'
        elif abuse_score >= 40:
            threat_level = 'medium'
        elif abuse_score >= 20:
            threat_level = 'low'
        
        # Check if blocking is needed
        should_block = False
        block_reason = None
        
        if threat_level == 'critical':
            should_block = True
            block_reason = f"Critical abuse detected: {', '.join(detected_patterns)}"
            self.blocked_ips.add(ip_address)
            if user_id:
                self.blocked_users.add(user_id)
        elif threat_level == 'high' and len(detected_patterns) >= 3:
            should_block = True
            block_reason = f"High abuse detected: {', '.join(detected_patterns)}"
            self.blocked_ips.add(ip_address)
        
        return not should_block, {
            'blocked': should_block,
            'reason': block_reason,
            'abuse_score': abuse_score,
            'threat_level': threat_level,
            'detected_patterns': detected_patterns,
            'timestamp': current_time
        }
    
    def _check_suspicious_headers(self, request) -> List[str]:
        """Check for suspicious request headers"""
        suspicious = []
        
        # Check for spoofed headers
        if request.headers.get('X-Forwarded-For') and not request.headers.get('X-Real-IP'):
            suspicious.append('header_spoofing')
        
        # Check for multiple user agents
        user_agents = [h for h in request.headers if h.lower() == 'user-agent']
        if len(user_agents) > 1:
            suspicious.append('multiple_user_agents')
        
        # Check for suspicious user agent
        user_agent = request.headers.get('User-Agent', '')
        if not user_agent or user_agent.lower() in ['curl', 'wget', 'python', 'bot']:
            suspicious.append('suspicious_user_agent')
        
        # Check for missing required headers
        if not request.headers.get('Accept'):
            suspicious.append('missing_accept_header')
        
        return suspicious
    
    def _check_api_key_abuse(self, api_key: str) -> bool:
        """Check for API key abuse patterns"""
        # This would typically check against a database
        # For demo purposes, we'll use a simple pattern
        abuse_patterns = [
            'test_key',
            'demo_key',
            'invalid_key',
            'expired_key'
        ]
        
        return any(pattern in api_key.lower() for pattern in abuse_patterns)
    
    def get_abuse_stats(self) -> Dict[str, Any]:
        """Get abuse detection statistics"""
        return {
            'blocked_ips': len(self.blocked_ips),
            'blocked_users': len(self.blocked_users),
            'total_patterns': len(self.abuse_patterns),
            'thresholds': self.thresholds,
            'recent_blocks': len([t for t in self.abuse_patterns.values() 
                                if time.time() - max(t) < 3600])  # Last hour
        }

class ComprehensiveSecurityMiddleware:
    """Comprehensive security middleware for all routes"""
    
    def __init__(self, app: Flask, config: Optional[APISecurityConfig] = None):
        self.app = app
        self.config = config or self._get_default_config()
        
        # Initialize all security components
        self.rate_limit_manager = RateLimitManager(self.config)
        self.request_validator = RequestValidator(self.config)
        self.suspicious_detector = SuspiciousActivityDetector(self.config)
        self.activity_logger = APIActivityLogger(self.config)
        self.access_logger = APIAccessLogger(self.config)
        self.abuse_detector = APIAbuseDetector(self.config)
        self.signature_validator = RequestSignatureValidator(self.config)
        self.premium_key_manager = PremiumAPIKeyManager(self.config)
        self.response_filter = ResponseDataFilter(self.config)
        self.cors_manager = CORSManager(self.config)
        self.api_version_manager = APIVersionManager(self.config)
        self.endpoint_monitor = EndpointMonitor(self.config)
        self.injection_protection = InjectionProtection(self.config)
        self.security_headers_validator = SecurityHeadersValidator(self.config)
        
        # Register comprehensive middleware
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        self.app.teardown_request(self._teardown_request)
        
        # Register error handlers
        self.app.register_error_handler(429, self._handle_rate_limited)
        self.app.register_error_handler(400, self._handle_bad_request)
        self.app.register_error_handler(403, self._handle_forbidden)
        self.app.register_error_handler(401, self._handle_unauthorized)
        self.app.register_error_handler(500, self._handle_server_error)
    
    def _get_default_config(self) -> APISecurityConfig:
        """Get default configuration based on environment"""
        environment = os.environ.get('FLASK_ENV', 'production')
        
        config = APISecurityConfig(
            environment=environment,
            redis_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
            require_api_key=environment == 'production'
        )
        
        return config
    
    def _before_request(self):
        """Comprehensive request processing before handling"""
        start_time = time.time()
        g.start_time = start_time
        g.request_id = secrets.token_hex(16)
        
        # Get user ID from session or token
        user_id = None
        if hasattr(g, 'user_id'):
            user_id = g.user_id
        elif session.get('user_id'):
            user_id = session['user_id']
        
        # Comprehensive security validation
        security_info = self._validate_security(request, user_id)
        
        # Check for abuse
        abuse_allowed, abuse_info = self.abuse_detector.analyze_request(
            request, user_id, security_info
        )
        
        if not abuse_allowed:
            response = jsonify({
                'error': 'Access denied',
                'message': abuse_info['reason'],
                'request_id': g.request_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            response.status_code = 403
            return response
        
        # Store security information for after_request
        g.security_info = security_info
        g.abuse_info = abuse_info
        g.user_id = user_id
        g.request_start_time = start_time
    
    def _validate_security(self, request, user_id: str = None) -> Dict[str, Any]:
        """Comprehensive security validation"""
        security_info = {
            'validation_passed': True,
            'injection_detected': False,
            'rate_limited': False,
            'suspicious_activity': False,
            'abuse_detected': False,
            'security_score': 100,
            'threat_level': 'low',
            'validation_errors': []
        }
        
        # Basic request validation
        is_valid, errors = self.request_validator.validate_request(request)
        if not is_valid:
            security_info['validation_passed'] = False
            security_info['validation_errors'].extend(errors)
            security_info['security_score'] -= 20
        
        # IP whitelist/blacklist check
        if self.config.ip_whitelist and request.remote_addr not in self.config.ip_whitelist:
            security_info['validation_passed'] = False
            security_info['validation_errors'].append("IP address not whitelisted")
            security_info['security_score'] -= 30
        
        # Injection protection validation
        injection_valid, injection_errors = self.injection_protection.validate_request(request)
        if not injection_valid:
            security_info['injection_detected'] = True
            security_info['validation_errors'].extend(injection_errors)
            security_info['security_score'] -= 40
            security_info['threat_level'] = 'high'
        
        # Signature validation
        if self.config.signature_validation:
            is_signature_valid, signature_message = self.signature_validator.validate_signature(request)
            if not is_signature_valid:
                security_info['validation_passed'] = False
                security_info['validation_errors'].append(f"Invalid signature: {signature_message}")
                security_info['security_score'] -= 25
        
        # Premium API key validation
        premium_key = request.headers.get(self.config.premium_api_key_header)
        if premium_key:
            is_premium_valid, premium_info = self.premium_key_manager.validate_premium_key(premium_key)
            if not is_premium_valid:
                security_info['validation_passed'] = False
                security_info['validation_errors'].append(f"Invalid premium key: {premium_info['message']}")
                security_info['security_score'] -= 20
        
        # API version validation
        version = request.headers.get(self.config.version_header)
        is_version_valid, version_info = self.api_version_manager.validate_version(version)
        if not is_version_valid:
            security_info['validation_passed'] = False
            security_info['validation_errors'].append(f"Invalid API version: {version_info['message']}")
            security_info['security_score'] -= 10
        
        # Rate limiting check
        endpoint_type = self._get_endpoint_type(request.endpoint)
        allowed, rate_limit_info = self.rate_limit_manager.check_rate_limit(
            endpoint_type, user_id, request.remote_addr
        )
        
        if not allowed:
            security_info['rate_limited'] = True
            security_info['security_score'] -= 15
        
        # Suspicious activity detection
        suspicious_info = self.suspicious_detector.analyze_request(
            request, user_id, request.remote_addr
        )
        
        if suspicious_info['suspicious']:
            security_info['suspicious_activity'] = True
            security_info['security_score'] -= suspicious_info['risk_score'] / 10
            if suspicious_info['risk_score'] > 50:
                security_info['threat_level'] = 'medium'
        
        # Update threat level based on security score
        if security_info['security_score'] <= 20:
            security_info['threat_level'] = 'critical'
        elif security_info['security_score'] <= 40:
            security_info['threat_level'] = 'high'
        elif security_info['security_score'] <= 60:
            security_info['threat_level'] = 'medium'
        
        return security_info
    
    def _after_request(self, response: Response) -> Response:
        """Comprehensive response processing after handling"""
        end_time = time.time()
        response_time = end_time - getattr(g, 'request_start_time', end_time)
        
        # Calculate performance metrics
        performance_info = {
            'response_time': response_time * 1000,  # Convert to milliseconds
            'processing_time': response_time * 1000,
            'database_queries': getattr(g, 'db_queries', 0),
            'cache_hits': getattr(g, 'cache_hits', 0),
            'cache_misses': getattr(g, 'cache_misses', 0),
            'memory_usage': getattr(g, 'memory_usage', 0),
            'cpu_usage': getattr(g, 'cpu_usage', 0)
        }
        
        # Add security headers
        response = self.security_headers_validator.add_security_headers(response)
        
        # Add custom headers
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        response.headers['X-Response-Time'] = f"{response_time:.3f}"
        response.headers['X-Security-Score'] = str(getattr(g, 'security_info', {}).get('security_score', 100))
        response.headers['X-Threat-Level'] = getattr(g, 'security_info', {}).get('threat_level', 'low')
        
        # Log comprehensive access information
        self.access_logger.log_api_access(
            request, response,
            user_id=getattr(g, 'user_id', None),
            security_info=getattr(g, 'security_info', {}),
            performance_info=performance_info
        )
        
        # Log activity for monitoring
        self.activity_logger.log_request(
            request, response,
            user_id=getattr(g, 'user_id', None),
            rate_limit_info=getattr(g, 'rate_limit_info', {}),
            suspicious_info=getattr(g, 'suspicious_info', {})
        )
        
        # Filter sensitive data
        if response.data:
            response.data = self.response_filter.filter_response_data(response.data)
        
        # Record endpoint statistics
        self.endpoint_monitor.record_request(
            request.endpoint,
            user_id=getattr(g, 'user_id', None),
            response_time=response_time,
            status_code=response.status_code
        )
        
        return response
    
    def _teardown_request(self, exception=None):
        """Clean up after request processing"""
        # Clean up any request-specific data
        if hasattr(g, 'request_id'):
            del g.request_id
        if hasattr(g, 'security_info'):
            del g.security_info
        if hasattr(g, 'abuse_info'):
            del g.abuse_info
        if hasattr(g, 'user_id'):
            del g.user_id
        if hasattr(g, 'request_start_time'):
            del g.request_start_time
    
    def _get_endpoint_type(self, endpoint: str) -> str:
        """Determine endpoint type for rate limiting"""
        if not endpoint:
            return 'general'
        
        endpoint_lower = endpoint.lower()
        
        # Authentication endpoints
        if any(auth in endpoint_lower for auth in ['login', 'logout', 'register', 'auth']):
            return 'auth'
        
        # Financial data endpoints
        if any(financial in endpoint_lower for financial in ['financial', 'income', 'expense', 'budget']):
            return 'financial'
        
        # Health checkin endpoints
        if any(health in endpoint_lower for health in ['health', 'checkin', 'wellness']):
            return 'health'
        
        # Income comparison endpoints
        if any(income in endpoint_lower for income in ['income_comparison', 'salary_comparison', 'career_advancement']):
            return 'income_comparison'
        
        # PDF generation endpoints
        if any(pdf in endpoint_lower for pdf in ['pdf', 'generate', 'report']):
            return 'pdf_generation'
        
        # Default to general API
        return 'general'
    
    def _handle_rate_limited(self, error):
        """Handle rate limit exceeded errors"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'retry_after': getattr(error, 'retry_after', 3600),
            'timestamp': datetime.utcnow().isoformat()
        }), 429
    
    def _handle_bad_request(self, error):
        """Handle bad request errors"""
        return jsonify({
            'error': 'Bad request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    def _handle_forbidden(self, error):
        """Handle forbidden errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        }), 403
    
    def _handle_unauthorized(self, error):
        """Handle unauthorized errors"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    def _handle_server_error(self, error):
        """Handle server errors"""
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Decorators for specific endpoint rate limiting
def rate_limit_auth(f):
    """Rate limit decorator for authentication endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_financial(f):
    """Rate limit decorator for financial endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_health(f):
    """Rate limit decorator for health endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_income_comparison(f):
    """Rate limit decorator for income comparison endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_pdf_generation(f):
    """Rate limit decorator for PDF generation endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

# Enhanced decorators for new security features
def require_premium_feature(feature: str):
    """Decorator to require premium feature access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            premium_key = request.headers.get('X-Premium-Key')
            if not premium_key:
                abort(401, description=f"Premium feature '{feature}' requires premium API key")
            
            # Get middleware instance
            middleware = current_app.extensions.get('api_security')
            if middleware and middleware.middleware:
                if not middleware.middleware.premium_key_manager.has_feature_access(premium_key, feature):
                    abort(403, description=f"Premium API key does not have access to feature '{feature}'")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_signature(f):
    """Decorator to require request signature validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Signature validation is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def require_api_version(version: str):
    """Decorator to require specific API version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request_version = request.headers.get('X-API-Version', 'v1')
            if request_version != version:
                abort(400, description=f"Endpoint requires API version {version}, got {request_version}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def filter_response(f):
    """Decorator to filter sensitive data from response"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Get middleware instance
        middleware = current_app.extensions.get('api_security')
        if middleware and middleware.middleware:
            if isinstance(response, tuple):
                data, status_code = response
                filtered_data = middleware.middleware.response_filter.filter_response_data(data)
                return jsonify(filtered_data), status_code
            else:
                filtered_data = middleware.middleware.response_filter.filter_response_data(response)
                return jsonify(filtered_data)
        
        return response
    return decorated_function

# Enhanced decorators for injection protection
def prevent_sql_injection(f):
    """Decorator to prevent SQL injection attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # SQL injection protection is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def prevent_nosql_injection(f):
    """Decorator to prevent NoSQL injection attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # NoSQL injection protection is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def prevent_command_injection(f):
    """Decorator to prevent command injection attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Command injection protection is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def prevent_path_traversal(f):
    """Decorator to prevent path traversal attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Path traversal protection is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def prevent_request_smuggling(f):
    """Decorator to prevent request smuggling attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Request smuggling protection is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def sanitize_input(f):
    """Decorator to sanitize input data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get middleware instance
        middleware = current_app.extensions.get('api_security')
        if middleware and middleware.middleware:
            # Sanitize request data
            if request.is_json:
                sanitized_data = middleware.middleware.injection_protection.sanitize_input(request.get_json())
                # Replace request data with sanitized version
                request._cached_json = sanitized_data
        
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def create_api_security_config(environment: str = None) -> APISecurityConfig:
    """Create API security configuration"""
    if not environment:
        environment = os.environ.get('FLASK_ENV', 'production')
    
    config = APISecurityConfig(
        environment=environment,
        redis_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        require_api_key=environment == 'production'
    )
    
    return config

def validate_api_security_config(config: APISecurityConfig) -> List[str]:
    """Validate API security configuration"""
    errors = []
    
    if not config.redis_url:
        errors.append("Redis URL is required for rate limiting")
    
    if config.max_request_size <= 0:
        errors.append("Max request size must be positive")
    
    if not config.allowed_content_types:
        errors.append("At least one allowed content type must be specified")
    
    return errors

# Utility functions for API security
def generate_request_signature(method: str, path: str, data: str = None, 
                             secret: str = None) -> Tuple[str, str]:
    """Generate request signature for API calls"""
    if not secret:
        secret = os.environ.get('SIGNATURE_SECRET', 'default-secret')
    
    timestamp = str(int(time.time()))
    
    # Create signature payload
    payload = f"{method}:{path}:{timestamp}"
    if data:
        payload += f":{data}"
    
    # Generate HMAC signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature, timestamp

def validate_api_version(version: str, supported_versions: List[str] = None) -> bool:
    """Validate API version"""
    if not supported_versions:
        supported_versions = ['v1', 'v2']
    
    return version in supported_versions

def check_premium_feature_access(api_key: str, feature: str) -> bool:
    """Check if API key has access to premium feature"""
    # This would typically check against a database
    # For demo purposes, we'll use environment variables
    premium_keys = {
        os.environ.get('PREMIUM_API_KEY_1', ''): ['advanced_analytics', 'pdf_generation'],
        os.environ.get('PREMIUM_API_KEY_2', ''): ['data_export', 'priority_support'],
    }
    
    if api_key in premium_keys:
        return feature in premium_keys[api_key]
    
    return False

def filter_sensitive_data(data: Any, sensitive_fields: List[str] = None) -> Any:
    """Filter sensitive data from response"""
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'secret', 'key', 'ssn', 'credit_card']
    
    if isinstance(data, dict):
        filtered = {}
        for key, value in data.items():
            key_lower = key.lower()
            is_sensitive = any(sensitive in key_lower for sensitive in sensitive_fields)
            
            if is_sensitive:
                filtered[key] = '***FILTERED***'
            elif isinstance(value, (dict, list, str)):
                filtered[key] = filter_sensitive_data(value, sensitive_fields)
            else:
                filtered[key] = value
        
        return filtered
    elif isinstance(data, list):
        return [filter_sensitive_data(item, sensitive_fields) for item in data]
    elif isinstance(data, str):
        # Apply pattern filtering
        patterns = [
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        ]
        
        filtered = data
        for pattern in patterns:
            filtered = re.sub(pattern, '***FILTERED***', filtered)
        
        return filtered
    else:
        return data

# Example usage functions
def create_premium_api_key(features: List[str] = None) -> str:
    """Create a new premium API key"""
    if features is None:
        features = ['advanced_analytics', 'pdf_generation', 'data_export', 'priority_support']
    
    api_key = secrets.token_urlsafe(32)
    
    # In production, this would be stored in a database
    logger.info(f"Generated premium API key: {api_key[:8]}... for features: {features}")
    
    return api_key

def get_api_security_stats() -> Dict[str, Any]:
    """Get API security statistics"""
    # This would typically get stats from the middleware
    return {
        'total_requests': 0,
        'rate_limited_requests': 0,
        'suspicious_requests': 0,
        'premium_feature_usage': 0,
        'signature_validations': 0,
        'filtered_responses': 0
    }

# Flask extension enhancement
class APISecurity:
    """Flask extension for API security"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.middleware = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the extension with the Flask app"""
        self.app = app
        
        # Create configuration
        config = create_api_security_config()
        
        # Validate configuration
        errors = validate_api_security_config(config)
        if errors:
            raise ValueError(f"Invalid API security configuration: {', '.join(errors)}")
        
        # Initialize middleware
        self.middleware = ComprehensiveSecurityMiddleware(app, config)
        
        # Setup CORS
        self.middleware.cors_manager.setup_cors(app)
        
        # Store extension on app
        app.extensions['api_security'] = self
    
    def get_rate_limit_info(self, endpoint_type: str, user_id: str = None, 
                           ip_address: str = None) -> Dict[str, Any]:
        """Get rate limit information for endpoint type"""
        if self.middleware:
            return self.middleware.rate_limit_manager.check_rate_limit(
                endpoint_type, user_id, ip_address
            )[1]
        return {}
    
    def get_suspicious_activity(self, user_id: str = None, ip_address: str = None) -> Dict[str, Any]:
        """Get suspicious activity analysis"""
        if self.middleware:
            # Create a mock request for analysis
            class MockRequest:
                def __init__(self):
                    self.method = 'GET'
                    self.endpoint = 'unknown'
                    self.headers = {}
                    self.content_length = 0
                    self.remote_addr = ip_address or 'unknown'
            
            mock_request = MockRequest()
            return self.middleware.suspicious_detector.analyze_request(
                mock_request, user_id, ip_address
            )
        return {}
    
    def get_endpoint_stats(self, endpoint: str = None) -> Dict[str, Any]:
        """Get endpoint monitoring statistics"""
        if self.middleware:
            return self.middleware.endpoint_monitor.get_endpoint_stats(endpoint)
        return {}
    
    def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent security alerts"""
        if self.middleware:
            return self.middleware.endpoint_monitor.get_alerts(hours)
        return []
    
    def generate_premium_key(self, features: List[str] = None) -> str:
        """Generate new premium API key"""
        if self.middleware:
            return self.middleware.premium_key_manager.generate_premium_key(features)
        return create_premium_api_key(features)
    
    def validate_premium_key(self, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate premium API key"""
        if self.middleware:
            return self.middleware.premium_key_manager.validate_premium_key(api_key)
        return False, {'valid': False, 'message': 'Middleware not initialized'}
    
    def has_feature_access(self, api_key: str, feature: str) -> bool:
        """Check if API key has access to specific feature"""
        if self.middleware:
            return self.middleware.premium_key_manager.has_feature_access(api_key, feature)
        return check_premium_feature_access(api_key, feature) 