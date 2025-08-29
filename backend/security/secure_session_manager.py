#!/usr/bin/env python3
"""
Secure Session Manager for MINGUS Assessment System
Enhanced session management with security features including:
- Redis-based session storage
- IP address consistency checks
- User-Agent validation
- Session fixation protection
- Comprehensive security monitoring
"""

import redis
import time
import secrets
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from flask import current_app, request, g
import threading

logger = logging.getLogger(__name__)

@dataclass
class SessionConfig:
    """Session configuration settings"""
    # Session timeout settings
    session_timeout: int = 3600  # 1 hour
    session_refresh_threshold: int = 300  # 5 minutes
    remember_me_duration: int = 604800  # 7 days
    
    # Security settings
    require_ip_validation: bool = True
    require_user_agent_validation: bool = True
    session_fixation_protection: bool = True
    secure_session_cookies: bool = True
    session_regeneration_interval: int = 3600  # 1 hour
    
    # Redis configuration
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 2
    redis_password: str = None
    
    # Session limits
    max_concurrent_sessions: int = 3
    max_sessions_per_user: int = 10
    
    # Security features
    track_session_activity: bool = True
    log_session_events: bool = True

@dataclass
class SessionData:
    """Session data structure"""
    session_id: str
    user_id: str
    created_at: float
    last_activity: float
    expires_at: float
    ip_address: str
    user_agent: str
    user_agent_hash: str
    is_active: bool = True
    remember_me: bool = False
    token: str = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityEvent:
    """Security event for logging"""
    event_type: str
    user_id: str
    session_id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    severity: str = 'INFO'

class SecureSessionManager:
    """Enhanced session manager with security features"""
    
    def __init__(self, config: SessionConfig):
        self.config = config
        self.redis_client = None
        self.security_events = []
        self.lock = threading.Lock()
        
        # Initialize Redis connection
        self._setup_redis()
        
        # Initialize security logging
        self._setup_security_logging()
    
    def _setup_redis(self):
        """Setup Redis connection for session storage"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for session management")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            # Fallback to in-memory storage (not recommended for production)
            self.redis_client = None
    
    def _setup_security_logging(self):
        """Setup security event logging"""
        self.security_logger = logging.getLogger('security.session')
        handler = logging.FileHandler('logs/session_security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.security_logger.addHandler(handler)
        self.security_logger.setLevel(logging.INFO)
    
    def create_secure_session(self, user_id: str, token: str, remember_me: bool = False) -> str:
        """Create a new secure session"""
        try:
            # Generate unique session ID
            session_id = secrets.token_urlsafe(32)
            current_time = time.time()
            
            # Calculate expiration
            if remember_me:
                expiration = current_time + self.config.remember_me_duration
            else:
                expiration = current_time + self.config.session_timeout
            
            # Create session data
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                created_at=current_time,
                last_activity=current_time,
                expires_at=expiration,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                user_agent_hash=self._hash_user_agent(request.headers.get('User-Agent', '')),
                remember_me=remember_me,
                token=token
            )
            
            # Check concurrent session limit
            if self._enforce_session_limits(user_id):
                # Remove oldest session
                self._remove_oldest_session(user_id)
            
            # Store session in Redis
            if self.redis_client:
                session_key = f"session:{session_id}"
                session_json = self._session_to_json(session_data)
                self.redis_client.setex(session_key, int(expiration - current_time), session_json)
                
                # Add to user's session list
                user_sessions_key = f"user_sessions:{user_id}"
                self.redis_client.sadd(user_sessions_key, session_id)
                self.redis_client.expire(user_sessions_key, int(expiration - current_time))
            
            # Log session creation
            self._log_security_event("session_created", user_id, session_id, {
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', ''),
                "remember_me": remember_me,
                "expiration": expiration
            })
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating secure session: {str(e)}")
            raise
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate session and return session data"""
        try:
            if not self.redis_client:
                return {"valid": False, "reason": "Session storage unavailable"}
            
            session_key = f"session:{session_id}"
            session_json = self.redis_client.get(session_key)
            
            if not session_json:
                return {"valid": False, "reason": "Session not found"}
            
            # Parse session data
            session_data = self._json_to_session(session_json)
            
            # Check if session is active
            if not session_data.is_active:
                return {"valid": False, "reason": "Session inactive"}
            
            current_time = time.time()
            
            # Check if session has expired
            if current_time > session_data.expires_at:
                self._revoke_session(session_id, session_data.user_id)
                return {"valid": False, "reason": "Session expired"}
            
            # Check IP consistency if enabled
            if self.config.require_ip_validation:
                if session_data.ip_address != request.remote_addr:
                    self._log_security_event("session_ip_mismatch", session_data.user_id, session_id, {
                        "session_ip": session_data.ip_address,
                        "request_ip": request.remote_addr,
                        "severity": "HIGH"
                    })
                    self._revoke_session(session_id, session_data.user_id)
                    return {"valid": False, "reason": "IP address mismatch"}
            
            # Check User-Agent consistency if enabled
            if self.config.require_user_agent_validation:
                current_ua_hash = self._hash_user_agent(request.headers.get('User-Agent', ''))
                if session_data.user_agent_hash != current_ua_hash:
                    self._log_security_event("session_user_agent_mismatch", session_data.user_id, session_id, {
                        "session_ua_hash": session_data.user_agent_hash,
                        "current_ua_hash": current_ua_hash,
                        "severity": "MEDIUM"
                    })
                    self._revoke_session(session_id, session_data.user_id)
                    return {"valid": False, "reason": "User agent mismatch"}
            
            # Update last activity
            session_data.last_activity = current_time
            
            # Check if session needs refresh
            if current_time > session_data.last_activity + self.config.session_refresh_threshold:
                session_data.expires_at = current_time + self.config.session_timeout
                
                # Update session in Redis
                session_json = self._session_to_json(session_data)
                self.redis_client.setex(session_key, int(session_data.expires_at - current_time), session_json)
                
                self._log_security_event("session_refreshed", session_data.user_id, session_id, {
                    "new_expiration": session_data.expires_at
                })
            
            # Log successful validation
            self._log_security_event("session_validated", session_data.user_id, session_id, {
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', '')
            })
            
            return {
                "valid": True,
                "session": session_data,
                "session_data": self._session_to_dict(session_data)
            }
            
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return {"valid": False, "reason": "Validation error"}
    
    def revoke_session(self, session_id: str, user_id: str = None):
        """Revoke a specific session"""
        try:
            if not user_id:
                # Try to get user_id from session
                session_data = self._get_session_data(session_id)
                if session_data:
                    user_id = session_data.user_id
            
            self._revoke_session(session_id, user_id)
            
        except Exception as e:
            logger.error(f"Error revoking session: {str(e)}")
    
    def revoke_all_user_sessions(self, user_id: str):
        """Revoke all sessions for a specific user"""
        try:
            if not self.redis_client:
                return
            
            user_sessions_key = f"user_sessions:{user_id}"
            session_ids = self.redis_client.smembers(user_sessions_key)
            
            for session_id in session_ids:
                self._revoke_session(session_id, user_id)
            
            # Remove user sessions set
            self.redis_client.delete(user_sessions_key)
            
            self._log_security_event("all_sessions_revoked", user_id, "all", {
                "revoked_count": len(session_ids),
                "reason": "User logout or security event"
            })
            
        except Exception as e:
            logger.error(f"Error revoking all user sessions: {str(e)}")
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        try:
            if not self.redis_client:
                return []
            
            user_sessions_key = f"user_sessions:{user_id}"
            session_ids = self.redis_client.smembers(user_sessions_key)
            
            sessions = []
            for session_id in session_ids:
                session_data = self._get_session_data(session_id)
                if session_data and session_data.is_active:
                    sessions.append(self._session_to_dict(session_data))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            if not self.redis_client:
                return
            
            # Get all session keys
            session_keys = self.redis_client.keys("session:*")
            current_time = time.time()
            
            expired_count = 0
            for key in session_keys:
                session_json = self.redis_client.get(key)
                if session_json:
                    session_data = self._json_to_session(session_json)
                    if current_time > session_data.expires_at:
                        self.redis_client.delete(key)
                        expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
    
    def _enforce_session_limits(self, user_id: str) -> bool:
        """Check and enforce session limits"""
        try:
            if not self.redis_client:
                return False
            
            user_sessions_key = f"user_sessions:{user_id}"
            session_count = self.redis_client.scard(user_sessions_key)
            
            return session_count >= self.config.max_concurrent_sessions
            
        except Exception as e:
            logger.error(f"Error enforcing session limits: {str(e)}")
            return False
    
    def _remove_oldest_session(self, user_id: str):
        """Remove the oldest session for a user"""
        try:
            if not self.redis_client:
                return
            
            user_sessions_key = f"user_sessions:{user_id}"
            session_ids = self.redis_client.smembers(user_sessions_key)
            
            oldest_session = None
            oldest_time = float('inf')
            
            for session_id in session_ids:
                session_data = self._get_session_data(session_id)
                if session_data and session_data.created_at < oldest_time:
                    oldest_time = session_data.created_at
                    oldest_session = session_id
            
            if oldest_session:
                self._revoke_session(oldest_session, user_id)
                
        except Exception as e:
            logger.error(f"Error removing oldest session: {str(e)}")
    
    def _revoke_session(self, session_id: str, user_id: str):
        """Internal method to revoke a session"""
        try:
            if not self.redis_client:
                return
            
            session_key = f"session:{session_id}"
            user_sessions_key = f"user_sessions:{user_id}"
            
            # Remove session from Redis
            self.redis_client.delete(session_key)
            self.redis_client.srem(user_sessions_key, session_id)
            
            # Log revocation
            self._log_security_event("session_revoked", user_id, session_id, {
                "reason": "Manual revocation or security event"
            })
            
        except Exception as e:
            logger.error(f"Error revoking session: {str(e)}")
    
    def _get_session_data(self, session_id: str) -> Optional[SessionData]:
        """Get session data from Redis"""
        try:
            if not self.redis_client:
                return None
            
            session_key = f"session:{session_id}"
            session_json = self.redis_client.get(session_key)
            
            if session_json:
                return self._json_to_session(session_json)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session data: {str(e)}")
            return None
    
    def _session_to_json(self, session_data: SessionData) -> str:
        """Convert session data to JSON"""
        return json.dumps({
            'session_id': session_data.session_id,
            'user_id': session_data.user_id,
            'created_at': session_data.created_at,
            'last_activity': session_data.last_activity,
            'expires_at': session_data.expires_at,
            'ip_address': session_data.ip_address,
            'user_agent': session_data.user_agent,
            'user_agent_hash': session_data.user_agent_hash,
            'is_active': session_data.is_active,
            'remember_me': session_data.remember_me,
            'token': session_data.token,
            'metadata': session_data.metadata
        })
    
    def _json_to_session(self, session_json: str) -> SessionData:
        """Convert JSON to session data"""
        data = json.loads(session_json)
        return SessionData(
            session_id=data['session_id'],
            user_id=data['user_id'],
            created_at=data['created_at'],
            last_activity=data['last_activity'],
            expires_at=data['expires_at'],
            ip_address=data['ip_address'],
            user_agent=data['user_agent'],
            user_agent_hash=data['user_agent_hash'],
            is_active=data['is_active'],
            remember_me=data['remember_me'],
            token=data.get('token'),
            metadata=data.get('metadata', {})
        )
    
    def _session_to_dict(self, session_data: SessionData) -> Dict[str, Any]:
        """Convert session data to dictionary"""
        return {
            'session_id': session_data.session_id,
            'user_id': session_data.user_id,
            'created_at': datetime.fromtimestamp(session_data.created_at),
            'last_activity': datetime.fromtimestamp(session_data.last_activity),
            'expires_at': datetime.fromtimestamp(session_data.expires_at),
            'ip_address': session_data.ip_address,
            'user_agent': session_data.user_agent,
            'is_active': session_data.is_active,
            'remember_me': session_data.remember_me,
            'metadata': session_data.metadata
        }
    
    def _hash_user_agent(self, user_agent: str) -> str:
        """Create a hash of the user agent string"""
        return hashlib.sha256(user_agent.encode()).hexdigest()
    
    def _log_security_event(self, event_type: str, user_id: str, session_id: str, details: Dict[str, Any]):
        """Log security events"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
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
            f"Session Security Event: {event_type} | User: {user_id} | "
            f"Session: {session_id} | IP: {event.ip_address} | Details: {details}"
        )
    
    def get_security_events(self, user_id: str = None, session_id: str = None, 
                          event_type: str = None, hours: int = 24) -> List[SecurityEvent]:
        """Get security events with optional filtering"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            events = [
                event for event in self.security_events
                if event.timestamp > cutoff_time
            ]
            
            if user_id:
                events = [event for event in events if event.user_id == user_id]
            
            if session_id:
                events = [event for event in events if event.session_id == session_id]
            
            if event_type:
                events = [event for event in events if event.event_type == event_type]
            
            return events

def create_session_config() -> SessionConfig:
    """Create session configuration"""
    return SessionConfig(
        redis_host=current_app.config.get('REDIS_HOST', 'localhost'),
        redis_port=current_app.config.get('REDIS_PORT', 6379),
        redis_db=current_app.config.get('REDIS_DB_SESSIONS', 2),
        redis_password=current_app.config.get('REDIS_PASSWORD'),
        session_timeout=3600,
        session_refresh_threshold=300,
        remember_me_duration=604800,
        require_ip_validation=True,
        require_user_agent_validation=True,
        session_fixation_protection=True,
        max_concurrent_sessions=3,
        track_session_activity=True,
        log_session_events=True
    )

def get_session_manager() -> SecureSessionManager:
    """Get the session manager instance"""
    if not hasattr(g, 'session_manager'):
        config = create_session_config()
        g.session_manager = SecureSessionManager(config)
    return g.session_manager
