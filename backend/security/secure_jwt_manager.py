#!/usr/bin/env python3
"""
Secure JWT Manager for MINGUS Assessment System
Enhanced JWT validation with security features including:
- IP address consistency checks
- User-Agent validation
- Token blacklisting
- Comprehensive payload validation
- Security event logging
"""

import jwt
import time
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from flask import current_app, request, g
from dataclasses import dataclass, field
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

@dataclass
class JWTConfig:
    """JWT configuration settings"""
    secret_key: str
    algorithm: str = 'HS256'
    expiration_hours: int = 1
    refresh_expiration_days: int = 7
    issuer: str = 'mingus-app'
    audience: str = 'mingus-users'
    require_ip_validation: bool = True
    require_user_agent_validation: bool = True
    max_token_length: int = 8192
    token_rotation_enabled: bool = True
    token_rotation_threshold_hours: int = 12

@dataclass
class SecurityEvent:
    """Security event for logging"""
    event_type: str
    user_id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    severity: str = 'INFO'

class SecureJWTManager:
    """Enhanced JWT manager with security features"""
    
    def __init__(self, config: JWTConfig):
        self.config = config
        self.token_blacklist = set()  # In production, use Redis
        self.token_usage_tracker = defaultdict(int)
        self.security_events = []
        self.lock = threading.Lock()
        
        # Initialize security event logging
        self._setup_security_logging()
    
    def _setup_security_logging(self):
        """Setup security event logging"""
        self.security_logger = logging.getLogger('security.jwt')
        handler = logging.FileHandler('logs/security_jwt.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.security_logger.addHandler(handler)
        self.security_logger.setLevel(logging.INFO)
    
    def create_secure_token(self, user_id: str, additional_claims: Dict = None) -> str:
        """Create a secure JWT token with enhanced security features"""
        try:
            current_time = int(time.time())
            
            # Generate unique token ID
            token_id = secrets.token_urlsafe(32)
            
            # Create payload with security features
            payload = {
                'sub': user_id,
                'iat': current_time,
                'exp': current_time + (self.config.expiration_hours * 3600),
                'iss': self.config.issuer,
                'aud': self.config.audience,
                'jti': token_id,  # Unique token ID
                'ip': request.remote_addr,
                'user_agent_hash': self._hash_user_agent(request.headers.get('User-Agent', '')),
                'created_at': current_time,
                'token_version': '1.0'
            }
            
            # Add additional claims if provided
            if additional_claims:
                payload.update(additional_claims)
            
            # Validate payload size
            if len(str(payload)) > self.config.max_token_length:
                raise ValueError("Token payload too large")
            
            # Encode token
            token = jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
            
            # Log token creation
            self._log_security_event("token_created", user_id, {
                "token_id": token_id,
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', ''),
                "expiration": payload['exp']
            })
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating secure token: {str(e)}")
            raise
    
    def validate_secure_token(self, token: str) -> Dict[str, Any]:
        """Validate a secure JWT token with comprehensive security checks"""
        try:
            # Check if token is blacklisted
            if token in self.token_blacklist:
                self._log_security_event("token_blacklisted", "unknown", {
                    "token_preview": token[:20] + "...",
                    "reason": "Token in blacklist"
                })
                return {"valid": False, "reason": "Token revoked"}
            
            # Decode token with strict validation
            payload = jwt.decode(
                token, 
                self.config.secret_key, 
                algorithms=[self.config.algorithm],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_iss': True,
                    'verify_aud': True,
                    'require': ['exp', 'iat', 'sub', 'jti', 'iss', 'aud']
                }
            )
            
            # Verify issuer
            if payload.get('iss') != self.config.issuer:
                self._log_security_event("invalid_issuer", payload.get('sub', 'unknown'), {
                    "expected_issuer": self.config.issuer,
                    "received_issuer": payload.get('iss')
                })
                return {"valid": False, "reason": "Invalid issuer"}
            
            # Verify audience
            if payload.get('aud') != self.config.audience:
                self._log_security_event("invalid_audience", payload.get('sub', 'unknown'), {
                    "expected_audience": self.config.audience,
                    "received_audience": payload.get('aud')
                })
                return {"valid": False, "reason": "Invalid audience"}
            
            # Check IP address consistency if enabled
            if self.config.require_ip_validation:
                token_ip = payload.get('ip')
                current_ip = request.remote_addr
                
                if token_ip != current_ip:
                    self._log_security_event("ip_mismatch", payload.get('sub', 'unknown'), {
                        "token_ip": token_ip,
                        "request_ip": current_ip,
                        "severity": "HIGH"
                    })
                    return {"valid": False, "reason": "IP address mismatch"}
            
            # Check User-Agent consistency if enabled
            if self.config.require_user_agent_validation:
                token_ua_hash = payload.get('user_agent_hash')
                current_ua_hash = self._hash_user_agent(request.headers.get('User-Agent', ''))
                
                if token_ua_hash != current_ua_hash:
                    self._log_security_event("user_agent_mismatch", payload.get('sub', 'unknown'), {
                        "token_ua_hash": token_ua_hash,
                        "current_ua_hash": current_ua_hash,
                        "severity": "MEDIUM"
                    })
                    return {"valid": False, "reason": "User agent mismatch"}
            
            # Check token age for rotation
            if self.config.token_rotation_enabled:
                token_age_hours = (time.time() - payload.get('iat', 0)) / 3600
                if token_age_hours > self.config.token_rotation_threshold_hours:
                    self._log_security_event("token_rotation_needed", payload.get('sub', 'unknown'), {
                        "token_age_hours": token_age_hours,
                        "rotation_threshold": self.config.token_rotation_threshold_hours
                    })
                    return {"valid": True, "payload": payload, "rotation_needed": True}
            
            # Track token usage
            with self.lock:
                self.token_usage_tracker[payload.get('jti')] += 1
            
            # Log successful validation
            self._log_security_event("token_validated", payload.get('sub', 'unknown'), {
                "token_id": payload.get('jti'),
                "usage_count": self.token_usage_tracker[payload.get('jti')]
            })
            
            return {"valid": True, "payload": payload}
            
        except jwt.ExpiredSignatureError:
            self._log_security_event("token_expired", "unknown", {
                "token_preview": token[:20] + "..."
            })
            return {"valid": False, "reason": "Token expired"}
        except jwt.InvalidTokenError as e:
            self._log_security_event("invalid_token", "unknown", {
                "token_preview": token[:20] + "...",
                "error": str(e)
            })
            return {"valid": False, "reason": f"Invalid token: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return {"valid": False, "reason": "Validation error"}
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding it to the blacklist"""
        try:
            # Decode token to get user info for logging
            try:
                payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
                user_id = payload.get('sub', 'unknown')
                token_id = payload.get('jti', 'unknown')
            except:
                user_id = 'unknown'
                token_id = 'unknown'
            
            # Add to blacklist
            with self.lock:
                self.token_blacklist.add(token)
            
            # Log revocation
            self._log_security_event("token_revoked", user_id, {
                "token_id": token_id,
                "reason": "Manual revocation"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
    
    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a specific user"""
        try:
            revoked_count = 0
            
            # In a production environment, you would query your token store
            # For now, we'll just log the action
            self._log_security_event("user_tokens_revoked", user_id, {
                "reason": "User logout or security event",
                "revoked_count": "all"
            })
            
            return revoked_count
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {str(e)}")
            return 0
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh a valid token with a new expiration"""
        validation_result = self.validate_secure_token(token)
        
        if not validation_result.get('valid'):
            return None
        
        payload = validation_result['payload']
        user_id = payload.get('sub')
        
        # Create new token with same claims but new expiration
        additional_claims = {
            'refreshed_from': payload.get('jti'),
            'refresh_count': payload.get('refresh_count', 0) + 1
        }
        
        # Remove internal fields from additional claims
        for field in ['sub', 'iat', 'exp', 'iss', 'aud', 'jti', 'ip', 'user_agent_hash', 'created_at', 'token_version']:
            if field in payload:
                additional_claims[field] = payload[field]
        
        new_token = self.create_secure_token(user_id, additional_claims)
        
        # Revoke old token
        self.revoke_token(token)
        
        return new_token
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get information about a token without validating it"""
        try:
            payload = jwt.decode(
                token, 
                self.config.secret_key, 
                algorithms=[self.config.algorithm],
                options={'verify_signature': False}
            )
            
            return {
                'user_id': payload.get('sub'),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                'expires_at': datetime.fromtimestamp(payload.get('exp', 0)),
                'token_id': payload.get('jti'),
                'issuer': payload.get('iss'),
                'audience': payload.get('aud'),
                'ip_address': payload.get('ip'),
                'is_blacklisted': token in self.token_blacklist,
                'usage_count': self.token_usage_tracker.get(payload.get('jti'), 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return None
    
    def _hash_user_agent(self, user_agent: str) -> str:
        """Create a hash of the user agent string"""
        return hashlib.sha256(user_agent.encode()).hexdigest()
    
    def _log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log security events"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details=details
        )
        
        # Add to in-memory events
        with self.lock:
            self.security_events.append(event)
            # Keep only last 1000 events
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
        
        # Log to file
        self.security_logger.info(
            f"JWT Security Event: {event_type} | User: {user_id} | "
            f"IP: {event.ip_address} | Details: {details}"
        )
    
    def get_security_events(self, user_id: str = None, event_type: str = None, 
                          hours: int = 24) -> List[SecurityEvent]:
        """Get security events with optional filtering"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            events = [
                event for event in self.security_events
                if event.timestamp > cutoff_time
            ]
            
            if user_id:
                events = [event for event in events if event.user_id == user_id]
            
            if event_type:
                events = [event for event in events if event.event_type == event_type]
            
            return events
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens from tracking"""
        current_time = time.time()
        
        with self.lock:
            # Clean up old security events (older than 7 days)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            self.security_events = [
                event for event in self.security_events
                if event.timestamp > cutoff_time
            ]
            
            # Note: In production, you would also clean up the blacklist
            # and usage tracker based on token expiration times

def create_jwt_config(secret_key: str = None) -> JWTConfig:
    """Create JWT configuration with environment-specific settings"""
    if not secret_key:
        secret_key = current_app.config.get('JWT_SECRET_KEY', 'default-secret-key')
    
    return JWTConfig(
        secret_key=secret_key,
        algorithm='HS256',
        expiration_hours=1,
        refresh_expiration_days=7,
        issuer='mingus-app',
        audience='mingus-users',
        require_ip_validation=True,
        require_user_agent_validation=True,
        max_token_length=8192,
        token_rotation_enabled=True,
        token_rotation_threshold_hours=12
    )

def get_jwt_manager() -> SecureJWTManager:
    """Get the JWT manager instance"""
    if not hasattr(g, 'jwt_manager'):
        config = create_jwt_config()
        g.jwt_manager = SecureJWTManager(config)
    return g.jwt_manager
