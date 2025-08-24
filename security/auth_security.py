#!/usr/bin/env python3
"""
MINGUS Authentication Security System
Comprehensive authentication security for financial wellness application
Protects user accounts and sessions with banking-grade security measures
"""

import os
import re
import json
import hashlib
import logging
import secrets
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import bcrypt
import jwt
import requests
from functools import wraps

from flask import Flask, request, Response, g, current_app, session, jsonify, abort
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

@dataclass
class PasswordPolicy:
    """Password strength policy for financial applications"""
    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    min_special_chars: int = 2
    prevent_common_passwords: bool = True
    prevent_sequential_chars: bool = True
    prevent_repeated_chars: bool = True
    max_repeated_chars: int = 3
    prevent_keyboard_patterns: bool = True
    prevent_personal_info: bool = True
    password_history_size: int = 5

@dataclass
class AccountLockoutPolicy:
    """Account lockout policy for failed login attempts"""
    max_failed_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    progressive_lockout: bool = True
    progressive_multiplier: float = 2.0
    max_lockout_duration: int = 86400  # 24 hours
    require_captcha_after: int = 3
    require_email_verification_after: int = 10

@dataclass
class RateLimitPolicy:
    """Rate limiting policy for authentication endpoints"""
    login_attempts_per_minute: int = 5
    password_reset_attempts_per_hour: int = 3
    mfa_attempts_per_minute: int = 3
    registration_attempts_per_hour: int = 3
    api_requests_per_minute: int = 100
    burst_limit: int = 20
    window_size: int = 60  # seconds

@dataclass
class SessionPolicy:
    """Session management policy"""
    session_timeout: int = 1800  # 30 minutes
    session_refresh_threshold: int = 300  # 5 minutes
    max_concurrent_sessions: int = 3
    session_fixation_protection: bool = True
    secure_session_cookies: bool = True
    session_regeneration_interval: int = 3600  # 1 hour
    remember_me_duration: int = 604800  # 7 days

@dataclass
class AuthSecurityConfig:
    """Authentication security configuration"""
    environment: str = "production"
    
    # Password policy
    password_policy: PasswordPolicy = field(default_factory=PasswordPolicy)
    
    # Account lockout policy
    lockout_policy: AccountLockoutPolicy = field(default_factory=AccountLockoutPolicy)
    
    # Rate limiting policy
    rate_limit_policy: RateLimitPolicy = field(default_factory=RateLimitPolicy)
    
    # Session policy
    session_policy: SessionPolicy = field(default_factory=SessionPolicy)
    
    # Security features
    mfa_enabled: bool = True
    mfa_required_for_financial_actions: bool = True
    suspicious_activity_detection: bool = True
    password_breach_detection: bool = True
    activity_logging: bool = True
    
    # JWT configuration
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    jwt_refresh_expiration: int = 604800  # 7 days
    
    # Breach detection
    breach_api_url: str = "https://api.pwnedpasswords.com/range/"
    breach_check_enabled: bool = True
    
    # Activity logging
    log_retention_days: int = 90
    sensitive_actions: List[str] = field(default_factory=lambda: [
        'login', 'logout', 'password_change', 'profile_update',
        'financial_data_access', 'subscription_change', 'mfa_setup',
        'account_lockout', 'suspicious_activity', 'breach_detection'
    ])

class PasswordValidator:
    """Password strength validator for financial applications"""
    
    def __init__(self, policy: PasswordPolicy):
        self.policy = policy
        self.common_passwords = self._load_common_passwords()
        self.keyboard_patterns = self._load_keyboard_patterns()
    
    def _load_common_passwords(self) -> set:
        """Load list of common passwords"""
        common_passwords = {
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            'dragon', 'master', 'football', 'superman', 'trustno1'
        }
        return common_passwords
    
    def _load_keyboard_patterns(self) -> List[str]:
        """Load keyboard patterns to prevent"""
        return [
            'qwerty', 'asdfgh', 'zxcvbn', '123456', '654321',
            'qazwsx', 'edcrfv', 'tgbyhn', 'ujmikl', 'poiuyt',
            'lkjhgf', 'mnbvcx', 'zxcvbn', 'qwertyuiop', 'asdfghjkl',
            'zxcvbnm', '1234567890', '0987654321'
        ]
    
    def validate_password(self, password: str, user_info: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        # Length validation
        if len(password) < self.policy.min_length:
            errors.append(f"Password must be at least {self.policy.min_length} characters long")
        
        if len(password) > self.policy.max_length:
            errors.append(f"Password must be no more than {self.policy.max_length} characters long")
        
        # Character type validation
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.policy.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.policy.require_special_chars:
            special_chars = re.findall(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password)
            if len(special_chars) < self.policy.min_special_chars:
                errors.append(f"Password must contain at least {self.policy.min_special_chars} special characters")
        
        # Common password check
        if self.policy.prevent_common_passwords and password.lower() in self.common_passwords:
            errors.append("Password is too common and not allowed")
        
        # Sequential character check
        if self.policy.prevent_sequential_chars:
            for i in range(len(password) - 2):
                if (ord(password[i+1]) == ord(password[i]) + 1 and 
                    ord(password[i+2]) == ord(password[i]) + 2):
                    errors.append("Password contains sequential characters")
                    break
        
        # Repeated character check
        if self.policy.prevent_repeated_chars:
            for i in range(len(password) - self.policy.max_repeated_chars + 1):
                if len(set(password[i:i+self.policy.max_repeated_chars])) == 1:
                    errors.append(f"Password contains more than {self.policy.max_repeated_chars} repeated characters")
                    break
        
        # Keyboard pattern check
        if self.policy.prevent_keyboard_patterns:
            password_lower = password.lower()
            for pattern in self.keyboard_patterns:
                if pattern in password_lower:
                    errors.append("Password contains keyboard patterns")
                    break
        
        # Personal information check
        if self.policy.prevent_personal_info and user_info:
            personal_info = [
                user_info.get('email', '').split('@')[0],
                user_info.get('first_name', '').lower(),
                user_info.get('last_name', '').lower(),
                user_info.get('username', '').lower()
            ]
            
            for info in personal_info:
                if info and info in password.lower():
                    errors.append("Password contains personal information")
                    break
        
        return len(errors) == 0, errors
    
    def check_password_breach(self, password: str) -> Tuple[bool, int]:
        """Check if password has been breached using HaveIBeenPwned API"""
        if not self.policy.prevent_common_passwords:
            return True, 0
        
        try:
            # Create SHA-1 hash of password
            password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = password_hash[:5]
            suffix = password_hash[5:]
            
            # Query the API
            response = requests.get(f"{self.policy.breach_api_url}{prefix}", timeout=5)
            response.raise_for_status()
            
            # Check if our hash suffix is in the response
            for line in response.text.splitlines():
                if line.startswith(suffix):
                    count = int(line.split(':')[1])
                    return False, count
            
            return True, 0
            
        except Exception as e:
            logger.warning(f"Password breach check failed: {e}")
            return True, 0  # Allow password if check fails

class RateLimiter:
    """Rate limiting implementation for authentication endpoints"""
    
    def __init__(self, policy: RateLimitPolicy):
        self.policy = policy
        self.attempts = defaultdict(lambda: deque())
        self.lock = threading.Lock()
    
    def is_rate_limited(self, identifier: str, action: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is rate limited"""
        with self.lock:
            current_time = time.time()
            key = f"{identifier}:{action}"
            
            # Clean old attempts
            while self.attempts[key] and current_time - self.attempts[key][0] > self.policy.window_size:
                self.attempts[key].popleft()
            
            # Check limits based on action
            if action == 'login':
                limit = self.policy.login_attempts_per_minute
            elif action == 'password_reset':
                limit = self.policy.password_reset_attempts_per_hour
            elif action == 'mfa':
                limit = self.policy.mfa_attempts_per_minute
            elif action == 'registration':
                limit = self.policy.registration_attempts_per_hour
            else:
                limit = self.policy.api_requests_per_minute
            
            # Check if limit exceeded
            if len(self.attempts[key]) >= limit:
                oldest_attempt = self.attempts[key][0]
                retry_after = int(self.policy.window_size - (current_time - oldest_attempt))
                
                return True, {
                    'limited': True,
                    'retry_after': retry_after,
                    'limit': limit,
                    'window': self.policy.window_size
                }
            
            # Add current attempt
            self.attempts[key].append(current_time)
            
            return False, {
                'limited': False,
                'remaining': limit - len(self.attempts[key]),
                'reset_time': int(current_time + self.policy.window_size)
            }

class AccountLockoutManager:
    """Account lockout management for failed login attempts"""
    
    def __init__(self, policy: AccountLockoutPolicy):
        self.policy = policy
        self.failed_attempts = defaultdict(lambda: {'count': 0, 'first_attempt': None, 'lockout_until': None})
        self.lock = threading.Lock()
    
    def record_failed_attempt(self, identifier: str) -> Dict[str, Any]:
        """Record a failed login attempt"""
        with self.lock:
            current_time = time.time()
            attempts = self.failed_attempts[identifier]
            
            # Initialize if first attempt
            if attempts['first_attempt'] is None:
                attempts['first_attempt'] = current_time
            
            attempts['count'] += 1
            
            # Check if account should be locked
            if attempts['count'] >= self.policy.max_failed_attempts:
                lockout_duration = self._calculate_lockout_duration(attempts['count'])
                attempts['lockout_until'] = current_time + lockout_duration
                
                return {
                    'locked': True,
                    'lockout_until': attempts['lockout_until'],
                    'lockout_duration': lockout_duration,
                    'attempts': attempts['count'],
                    'require_captcha': attempts['count'] >= self.policy.require_captcha_after,
                    'require_email_verification': attempts['count'] >= self.policy.require_email_verification_after
                }
            
            return {
                'locked': False,
                'attempts': attempts['count'],
                'remaining_attempts': self.policy.max_failed_attempts - attempts['count'],
                'require_captcha': attempts['count'] >= self.policy.require_captcha_after
            }
    
    def record_successful_attempt(self, identifier: str):
        """Record a successful login attempt and reset lockout"""
        with self.lock:
            if identifier in self.failed_attempts:
                del self.failed_attempts[identifier]
    
    def is_locked(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if account is currently locked"""
        with self.lock:
            if identifier not in self.failed_attempts:
                return False, {}
            
            attempts = self.failed_attempts[identifier]
            current_time = time.time()
            
            # Check if lockout has expired
            if attempts['lockout_until'] and current_time > attempts['lockout_until']:
                del self.failed_attempts[identifier]
                return False, {}
            
            # Account is still locked
            if attempts['lockout_until']:
                return True, {
                    'locked': True,
                    'lockout_until': attempts['lockout_until'],
                    'remaining_lockout': int(attempts['lockout_until'] - current_time),
                    'attempts': attempts['count']
                }
            
            return False, {
                'attempts': attempts['count'],
                'remaining_attempts': self.policy.max_failed_attempts - attempts['count']
            }
    
    def _calculate_lockout_duration(self, attempt_count: int) -> int:
        """Calculate lockout duration based on progressive lockout policy"""
        if not self.policy.progressive_lockout:
            return self.policy.lockout_duration
        
        duration = self.policy.lockout_duration * (self.policy.progressive_multiplier ** (attempt_count - self.policy.max_failed_attempts))
        return min(int(duration), self.policy.max_lockout_duration)

class SessionManager:
    """Secure session management for user sessions"""
    
    def __init__(self, policy: SessionPolicy, jwt_secret: str):
        self.policy = policy
        self.jwt_secret = jwt_secret
        self.active_sessions = defaultdict(list)
        self.lock = threading.Lock()
    
    def create_session(self, user_id: str, remember_me: bool = False) -> Dict[str, Any]:
        """Create a new secure session"""
        with self.lock:
            # Check concurrent session limit
            if len(self.active_sessions[user_id]) >= self.policy.max_concurrent_sessions:
                # Remove oldest session
                oldest_session = min(self.active_sessions[user_id], key=lambda s: s['created_at'])
                self.active_sessions[user_id].remove(oldest_session)
            
            # Generate session data
            session_id = secrets.token_urlsafe(32)
            current_time = time.time()
            
            # Set expiration based on remember me
            if remember_me:
                expiration = current_time + self.policy.remember_me_duration
            else:
                expiration = current_time + self.policy.session_timeout
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': current_time,
                'last_activity': current_time,
                'expires_at': expiration,
                'remember_me': remember_me,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'is_active': True
            }
            
            # Add to active sessions
            self.active_sessions[user_id].append(session_data)
            
            # Generate JWT token
            token_payload = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': current_time,
                'exp': expiration,
                'iat': current_time
            }
            
            token = jwt.encode(token_payload, self.jwt_secret, algorithm='HS256')
            
            return {
                'token': token,
                'session_id': session_id,
                'expires_at': expiration,
                'remember_me': remember_me
            }
    
    def validate_session(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate session token and return session data"""
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            session_id = payload['session_id']
            user_id = payload['user_id']
            
            with self.lock:
                # Find session in active sessions
                user_sessions = self.active_sessions.get(user_id, [])
                session_data = next((s for s in user_sessions if s['session_id'] == session_id), None)
                
                if not session_data or not session_data['is_active']:
                    return False, None
                
                current_time = time.time()
                
                # Check if session has expired
                if current_time > session_data['expires_at']:
                    self._remove_session(user_id, session_id)
                    return False, None
                
                # Check if session needs refresh
                if current_time > session_data['last_activity'] + self.policy.session_refresh_threshold:
                    session_data['last_activity'] = current_time
                    session_data['expires_at'] = current_time + self.policy.session_timeout
                
                return True, session_data
                
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
    
    def refresh_session(self, token: str) -> Optional[str]:
        """Refresh session and return new token"""
        is_valid, session_data = self.validate_session(token)
        
        if not is_valid:
            return None
        
        # Create new session with extended expiration
        return self.create_session(session_data['user_id'], session_data['remember_me'])['token']
    
    def invalidate_session(self, user_id: str, session_id: str):
        """Invalidate a specific session"""
        with self.lock:
            self._remove_session(user_id, session_id)
    
    def invalidate_all_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        with self.lock:
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
    
    def _remove_session(self, user_id: str, session_id: str):
        """Remove a session from active sessions"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id] = [
                s for s in self.active_sessions[user_id] 
                if s['session_id'] != session_id
            ]

class ActivityLogger:
    """User activity logging for security monitoring"""
    
    def __init__(self, config: AuthSecurityConfig):
        self.config = config
        self.activity_log = []
        self.lock = threading.Lock()
    
    def log_activity(self, user_id: str, action: str, details: Dict[str, Any] = None, 
                    ip_address: str = None, user_agent: str = None):
        """Log user activity for security monitoring"""
        if not self.config.activity_logging:
            return
        
        with self.lock:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'action': action,
                'ip_address': ip_address or request.remote_addr,
                'user_agent': user_agent or request.headers.get('User-Agent', ''),
                'details': details or {},
                'session_id': getattr(request, 'session_id', None)
            }
            
            self.activity_log.append(log_entry)
            
            # Keep only recent logs
            cutoff_time = datetime.utcnow() - timedelta(days=self.config.log_retention_days)
            self.activity_log = [
                entry for entry in self.activity_log
                if datetime.fromisoformat(entry['timestamp']) > cutoff_time
            ]
            
            # Log to file/system
            logger.info(f"User activity: {action} by user {user_id} from {log_entry['ip_address']}")
    
    def get_user_activity(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user activity for the specified number of days"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        with self.lock:
            return [
                entry for entry in self.activity_log
                if entry['user_id'] == user_id and 
                datetime.fromisoformat(entry['timestamp']) > cutoff_time
            ]
    
    def detect_suspicious_activity(self, user_id: str) -> List[Dict[str, Any]]:
        """Detect suspicious activity patterns"""
        if not self.config.suspicious_activity_detection:
            return []
        
        recent_activity = self.get_user_activity(user_id, days=7)
        suspicious_events = []
        
        # Check for multiple failed login attempts
        failed_logins = [a for a in recent_activity if a['action'] == 'login_failed']
        if len(failed_logins) >= 5:
            suspicious_events.append({
                'type': 'multiple_failed_logins',
                'count': len(failed_logins),
                'events': failed_logins
            })
        
        # Check for login from unusual locations
        login_locations = {}
        for activity in recent_activity:
            if activity['action'] == 'login_successful':
                ip = activity['ip_address']
                if ip not in login_locations:
                    login_locations[ip] = []
                login_locations[ip].append(activity)
        
        if len(login_locations) > 3:
            suspicious_events.append({
                'type': 'multiple_login_locations',
                'locations': len(login_locations),
                'events': list(login_locations.values())
            })
        
        # Check for rapid successive actions
        if len(recent_activity) > 20:
            suspicious_events.append({
                'type': 'high_activity_volume',
                'count': len(recent_activity),
                'period': '7 days'
            })
        
        return suspicious_events

class AuthSecurityMiddleware:
    """Authentication security middleware for MINGUS application"""
    
    def __init__(self, app: Flask, config: Optional[AuthSecurityConfig] = None):
        self.app = app
        self.config = config or self._get_default_config()
        
        # Initialize security components
        self.password_validator = PasswordValidator(self.config.password_policy)
        self.rate_limiter = RateLimiter(self.config.rate_limit_policy)
        self.lockout_manager = AccountLockoutManager(self.config.lockout_policy)
        self.session_manager = SessionManager(self.config.session_policy, self.config.jwt_secret_key)
        self.activity_logger = ActivityLogger(self.config)
        
        # Register middleware
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        
        # Register error handlers
        self.app.register_error_handler(401, self._handle_unauthorized)
        self.app.register_error_handler(403, self._handle_forbidden)
        self.app.register_error_handler(429, self._handle_rate_limited)
        
        logger.info("Authentication security middleware initialized")
    
    def _get_default_config(self) -> AuthSecurityConfig:
        """Get default authentication security configuration"""
        env = os.getenv('FLASK_ENV', 'development')
        
        if env == 'production':
            return AuthSecurityConfig(
                environment='production',
                jwt_secret_key=os.getenv('JWT_SECRET_KEY'),
                mfa_enabled=True,
                mfa_required_for_financial_actions=True,
                suspicious_activity_detection=True,
                password_breach_detection=True,
                activity_logging=True,
                breach_check_enabled=True
            )
        else:
            return AuthSecurityConfig(
                environment='development',
                jwt_secret_key='dev-secret-key-change-in-production',
                mfa_enabled=False,
                mfa_required_for_financial_actions=False,
                suspicious_activity_detection=False,
                password_breach_detection=False,
                activity_logging=True,
                breach_check_enabled=False
            )
    
    def _before_request(self):
        """Before request processing - authentication and security checks"""
        # Skip authentication for static files and health checks
        if request.endpoint in ['static', 'health_check']:
            return
        
        # Check for authentication token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            is_valid, session_data = self.session_manager.validate_session(token)
            
            if is_valid:
                g.current_user_id = session_data['user_id']
                g.session_data = session_data
                g.session_id = session_data['session_id']
                request.session_id = session_data['session_id']
            else:
                g.current_user_id = None
                g.session_data = None
        else:
            g.current_user_id = None
            g.session_data = None
        
        # Rate limiting check
        if g.current_user_id:
            identifier = g.current_user_id
        else:
            identifier = request.remote_addr
        
        # Determine action for rate limiting
        if request.endpoint in ['login', 'register', 'password_reset']:
            action = request.endpoint
        else:
            action = 'api'
        
        is_limited, rate_limit_info = self.rate_limiter.is_rate_limited(identifier, action)
        
        if is_limited:
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': rate_limit_info['retry_after'],
                'limit': rate_limit_info['limit']
            }), 429
    
    def _after_request(self, response: Response) -> Response:
        """After request processing - logging and cleanup"""
        # Log activity for authenticated users
        if hasattr(g, 'current_user_id') and g.current_user_id:
            self.activity_logger.log_activity(
                user_id=g.current_user_id,
                action=request.endpoint or 'unknown',
                details={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code
                }
            )
        
        return response
    
    def _handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        return jsonify({
            'error': 'Authentication required',
            'message': 'Please log in to access this resource'
        }), 401
    
    def _handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        return jsonify({
            'error': 'Access denied',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    def _handle_rate_limited(self, error):
        """Handle 429 Rate Limited errors"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests, please try again later'
        }), 429

class AuthSecurity:
    """Flask extension for authentication security"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.middleware = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the extension with the Flask app"""
        self.app = app
        self.middleware = AuthSecurityMiddleware(app)
        
        # Add authentication endpoints
        self._add_auth_endpoints()
        
        # Add security endpoints
        self._add_security_endpoints()
    
    def _add_auth_endpoints(self):
        """Add authentication endpoints"""
        
        @self.app.route('/auth/login', methods=['POST'])
        def login():
            """User login endpoint with security measures"""
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            remember_me = data.get('remember_me', False)
            captcha_token = data.get('captcha_token')
            
            # Rate limiting check
            is_limited, rate_limit_info = self.middleware.rate_limiter.is_rate_limited(
                request.remote_addr, 'login'
            )
            
            if is_limited:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': rate_limit_info['retry_after']
                }), 429
            
            # Check account lockout
            is_locked, lockout_info = self.middleware.lockout_manager.is_locked(email)
            
            if is_locked:
                return jsonify({
                    'error': 'Account temporarily locked',
                    'lockout_until': lockout_info['lockout_until'],
                    'remaining_lockout': lockout_info['remaining_lockout']
                }), 423
            
            # Require captcha after multiple failed attempts
            if lockout_info.get('require_captcha') and not captcha_token:
                return jsonify({
                    'error': 'Captcha required',
                    'require_captcha': True
                }), 400
            
            # Validate credentials (implement your own user validation)
            user = self._validate_user_credentials(email, password)
            
            if user:
                # Record successful login
                self.middleware.lockout_manager.record_successful_attempt(email)
                
                # Create session
                session_data = self.middleware.session_manager.create_session(
                    user['id'], remember_me
                )
                
                # Log successful login
                self.middleware.activity_logger.log_activity(
                    user_id=user['id'],
                    action='login_successful',
                    details={'email': email, 'remember_me': remember_me}
                )
                
                return jsonify({
                    'success': True,
                    'token': session_data['token'],
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'first_name': user.get('first_name'),
                        'last_name': user.get('last_name')
                    },
                    'session_expires_at': session_data['expires_at']
                })
            else:
                # Record failed login
                lockout_info = self.middleware.lockout_manager.record_failed_attempt(email)
                
                # Log failed login
                self.middleware.activity_logger.log_activity(
                    user_id='unknown',
                    action='login_failed',
                    details={'email': email, 'attempts': lockout_info['attempts']}
                )
                
                response_data = {
                    'error': 'Invalid credentials',
                    'attempts': lockout_info['attempts'],
                    'remaining_attempts': lockout_info.get('remaining_attempts', 0)
                }
                
                if lockout_info.get('require_captcha'):
                    response_data['require_captcha'] = True
                
                if lockout_info.get('locked'):
                    response_data['account_locked'] = True
                    response_data['lockout_until'] = lockout_info['lockout_until']
                
                return jsonify(response_data), 401
        
        @self.app.route('/auth/logout', methods=['POST'])
        def logout():
            """User logout endpoint"""
            auth_header = request.headers.get('Authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]
                is_valid, session_data = self.middleware.session_manager.validate_session(token)
                
                if is_valid:
                    # Invalidate session
                    self.middleware.session_manager.invalidate_session(
                        session_data['user_id'], session_data['session_id']
                    )
                    
                    # Log logout
                    self.middleware.activity_logger.log_activity(
                        user_id=session_data['user_id'],
                        action='logout'
                    )
            
            return jsonify({'success': True})
        
        @self.app.route('/auth/refresh', methods=['POST'])
        def refresh_token():
            """Refresh authentication token"""
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No token provided'}), 401
            
            token = auth_header[7:]
            new_token = self.middleware.session_manager.refresh_session(token)
            
            if new_token:
                return jsonify({
                    'success': True,
                    'token': new_token
                })
            else:
                return jsonify({'error': 'Invalid or expired token'}), 401
    
    def _add_security_endpoints(self):
        """Add security-related endpoints"""
        
        @self.app.route('/auth/validate-password', methods=['POST'])
        def validate_password():
            """Validate password strength"""
            data = request.get_json()
            password = data.get('password')
            user_info = data.get('user_info')
            
            if not password:
                return jsonify({'error': 'Password required'}), 400
            
            # Validate password strength
            is_valid, errors = self.middleware.password_validator.validate_password(password, user_info)
            
            # Check password breach
            if is_valid and self.middleware.config.password_breach_detection:
                breach_safe, breach_count = self.middleware.password_validator.check_password_breach(password)
                if not breach_safe:
                    is_valid = False
                    errors.append(f"Password has been found in {breach_count} data breaches")
            
            return jsonify({
                'valid': is_valid,
                'errors': errors,
                'strength_score': self._calculate_password_strength(password)
            })
        
        @self.app.route('/auth/activity', methods=['GET'])
        def get_user_activity():
            """Get user activity log"""
            if not hasattr(g, 'current_user_id') or not g.current_user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            days = request.args.get('days', 30, type=int)
            activity = self.middleware.activity_logger.get_user_activity(g.current_user_id, days)
            
            return jsonify({
                'activity': activity,
                'total_entries': len(activity)
            })
        
        @self.app.route('/auth/suspicious-activity', methods=['GET'])
        def check_suspicious_activity():
            """Check for suspicious activity"""
            if not hasattr(g, 'current_user_id') or not g.current_user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            suspicious_events = self.middleware.activity_logger.detect_suspicious_activity(g.current_user_id)
            
            return jsonify({
                'suspicious_events': suspicious_events,
                'total_events': len(suspicious_events)
            })
    
    def _validate_user_credentials(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate user credentials (implement with your database)"""
        # This is a placeholder - implement with your actual user database
        # Example implementation:
        """
        from your_models import User
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            return {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        return None
        """
        return None  # Placeholder
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length contribution
        if len(password) >= 12:
            score += 25
        elif len(password) >= 8:
            score += 15
        
        # Character variety contribution
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'\d', password):
            score += 15
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            score += 20
        
        # Complexity bonus
        if len(set(password)) > len(password) * 0.7:
            score += 10
        
        return min(score, 100)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user_id') or not g.current_user_id:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def require_mfa(f):
    """Decorator to require multi-factor authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user_id') or not g.current_user_id:
            abort(401)
        
        # Check if MFA is required for financial actions
        # This is a placeholder - implement your MFA logic
        if g.current_user_id and not hasattr(g, 'mfa_verified'):
            abort(403, description="Multi-factor authentication required")
        
        return f(*args, **kwargs)
    return decorated_function

def create_auth_config(environment: str = None) -> AuthSecurityConfig:
    """Create authentication security configuration"""
    if environment == 'production':
        return AuthSecurityConfig(
            environment='production',
            jwt_secret_key=os.getenv('JWT_SECRET_KEY'),
            mfa_enabled=True,
            mfa_required_for_financial_actions=True,
            suspicious_activity_detection=True,
            password_breach_detection=True,
            activity_logging=True
        )
    else:
        return AuthSecurityConfig(
            environment='development',
            jwt_secret_key='dev-secret-key-change-in-production',
            mfa_enabled=False,
            mfa_required_for_financial_actions=False,
            suspicious_activity_detection=False,
            password_breach_detection=False,
            activity_logging=True
        )

def validate_auth_config(config: AuthSecurityConfig) -> List[str]:
    """Validate authentication security configuration"""
    issues = []
    
    # Check JWT secret
    if not config.jwt_secret_key:
        issues.append("JWT secret key is required")
    
    # Check password policy
    if config.password_policy.min_length < 8:
        issues.append("Minimum password length should be at least 8 characters")
    
    if config.password_policy.min_length > config.password_policy.max_length:
        issues.append("Minimum password length cannot be greater than maximum length")
    
    # Check lockout policy
    if config.lockout_policy.max_failed_attempts < 1:
        issues.append("Maximum failed attempts must be at least 1")
    
    if config.lockout_policy.lockout_duration < 60:
        issues.append("Lockout duration should be at least 60 seconds")
    
    # Check rate limiting
    if config.rate_limit_policy.login_attempts_per_minute < 1:
        issues.append("Login attempts per minute must be at least 1")
    
    # Check session policy
    if config.session_policy.session_timeout < 300:
        issues.append("Session timeout should be at least 5 minutes")
    
    return issues 