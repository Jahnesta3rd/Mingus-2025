#!/usr/bin/env python3
"""
Brute Force Protection System for MINGUS Assessment System
Comprehensive protection against brute force attacks with:
- Redis-based attempt tracking
- Progressive lockout policies
- IP and user-based protection
- Security event logging
- Integration with assessment submission protection
"""

import redis
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from flask import current_app, request, g
import threading
import json

logger = logging.getLogger(__name__)

@dataclass
class BruteForceConfig:
    """Brute force protection configuration"""
    # Login protection
    max_login_attempts: int = 5
    login_lockout_duration: int = 300  # 5 minutes
    login_window_size: int = 900  # 15 minutes
    
    # Assessment submission protection
    max_assessment_attempts: int = 10
    assessment_lockout_duration: int = 600  # 10 minutes
    assessment_window_size: int = 3600  # 1 hour
    
    # Password reset protection
    max_password_reset_attempts: int = 3
    password_reset_lockout_duration: int = 1800  # 30 minutes
    password_reset_window_size: int = 3600  # 1 hour
    
    # Progressive lockout settings
    progressive_lockout_enabled: bool = True
    progressive_multiplier: float = 2.0
    max_lockout_duration: int = 86400  # 24 hours
    
    # Redis configuration
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 1
    redis_password: str = None
    
    # Security features
    require_captcha_after: int = 3
    require_email_verification_after: int = 10
    suspicious_activity_threshold: int = 20
    ip_whitelist: List[str] = field(default_factory=list)
    user_whitelist: List[str] = field(default_factory=list)

@dataclass
class SecurityEvent:
    """Security event for logging"""
    event_type: str
    identifier: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    severity: str = 'INFO'

class BruteForceProtection:
    """Comprehensive brute force protection system"""
    
    def __init__(self, config: BruteForceConfig):
        self.config = config
        self.redis_client = None
        self.security_events = []
        self.lock = threading.Lock()
        
        # Initialize Redis connection
        self._setup_redis()
        
        # Initialize security logging
        self._setup_security_logging()
    
    def _setup_redis(self):
        """Setup Redis connection for attempt tracking"""
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
            logger.info("Redis connection established for brute force protection")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            # Fallback to in-memory storage (not recommended for production)
            self.redis_client = None
    
    def _setup_security_logging(self):
        """Setup security event logging"""
        self.security_logger = logging.getLogger('security.brute_force')
        handler = logging.FileHandler('logs/brute_force_security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.security_logger.addHandler(handler)
        self.security_logger.setLevel(logging.INFO)
    
    def is_locked_out(self, identifier: str, action_type: str = 'login') -> bool:
        """Check if identifier is currently locked out"""
        try:
            if not self.redis_client:
                return False
            
            lockout_key = f"lockout:{action_type}:{identifier}"
            return self.redis_client.exists(lockout_key) > 0
            
        except Exception as e:
            logger.error(f"Error checking lockout status: {str(e)}")
            return False
    
    def get_lockout_info(self, identifier: str, action_type: str = 'login') -> Dict[str, Any]:
        """Get detailed lockout information"""
        try:
            if not self.redis_client:
                return {"locked": False}
            
            lockout_key = f"lockout:{action_type}:{identifier}"
            attempts_key = f"attempts:{action_type}:{identifier}"
            
            # Check if locked out
            lockout_ttl = self.redis_client.ttl(lockout_key)
            if lockout_ttl > 0:
                return {
                    "locked": True,
                    "remaining_lockout": lockout_ttl,
                    "lockout_until": datetime.utcnow() + timedelta(seconds=lockout_ttl)
                }
            
            # Get attempt count
            attempts = int(self.redis_client.get(attempts_key) or 0)
            attempts_ttl = self.redis_client.ttl(attempts_key)
            
            return {
                "locked": False,
                "attempts": attempts,
                "attempts_reset_in": attempts_ttl if attempts_ttl > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting lockout info: {str(e)}")
            return {"locked": False}
    
    def record_failed_attempt(self, identifier: str, action_type: str = 'login') -> Dict[str, Any]:
        """Record a failed attempt and check for lockout"""
        try:
            if not self.redis_client:
                return {"locked": False, "attempts": 1}
            
            # Check if identifier is whitelisted
            if self._is_whitelisted(identifier):
                return {"locked": False, "attempts": 0, "whitelisted": True}
            
            attempts_key = f"attempts:{action_type}:{identifier}"
            lockout_key = f"lockout:{action_type}:{identifier}"
            
            # Get configuration for action type
            config = self._get_action_config(action_type)
            
            # Increment attempt counter
            attempts = self.redis_client.incr(attempts_key)
            self.redis_client.expire(attempts_key, config['window_size'])
            
            # Check if lockout threshold reached
            if attempts >= config['max_attempts']:
                lockout_duration = self._calculate_lockout_duration(attempts, action_type)
                
                # Set lockout
                self.redis_client.setex(lockout_key, lockout_duration, "locked")
                
                # Log security event
                self._log_security_event("account_locked", identifier, {
                    "action_type": action_type,
                    "attempts": attempts,
                    "lockout_duration": lockout_duration,
                    "ip_address": request.remote_addr,
                    "severity": "HIGH"
                })
                
                return {
                    "locked": True,
                    "attempts": attempts,
                    "lockout_duration": lockout_duration,
                    "require_captcha": attempts >= self.config.require_captcha_after,
                    "require_email_verification": attempts >= self.config.require_email_verification_after
                }
            
            # Log failed attempt
            self._log_security_event("failed_attempt", identifier, {
                "action_type": action_type,
                "attempts": attempts,
                "max_attempts": config['max_attempts'],
                "ip_address": request.remote_addr
            })
            
            return {
                "locked": False,
                "attempts": attempts,
                "remaining_attempts": config['max_attempts'] - attempts,
                "require_captcha": attempts >= self.config.require_captcha_after
            }
            
        except Exception as e:
            logger.error(f"Error recording failed attempt: {str(e)}")
            return {"locked": False, "attempts": 1}
    
    def record_successful_attempt(self, identifier: str, action_type: str = 'login'):
        """Record a successful attempt and clear lockout"""
        try:
            if not self.redis_client:
                return
            
            attempts_key = f"attempts:{action_type}:{identifier}"
            lockout_key = f"lockout:{action_type}:{identifier}"
            
            # Clear attempt counter and lockout
            self.redis_client.delete(attempts_key, lockout_key)
            
            # Log successful attempt
            self._log_security_event("successful_attempt", identifier, {
                "action_type": action_type,
                "ip_address": request.remote_addr
            })
            
        except Exception as e:
            logger.error(f"Error recording successful attempt: {str(e)}")
    
    def check_assessment_submission_protection(self, user_id: str, assessment_id: str) -> Dict[str, Any]:
        """Check if assessment submission is allowed"""
        try:
            identifier = f"{user_id}:{assessment_id}"
            
            # Check if locked out
            if self.is_locked_out(identifier, 'assessment'):
                return {
                    "allowed": False,
                    "reason": "Assessment submission temporarily blocked",
                    "action_type": "assessment"
                }
            
            # Get current attempt count
            lockout_info = self.get_lockout_info(identifier, 'assessment')
            
            return {
                "allowed": True,
                "attempts": lockout_info.get("attempts", 0),
                "max_attempts": self.config.max_assessment_attempts
            }
            
        except Exception as e:
            logger.error(f"Error checking assessment submission protection: {str(e)}")
            return {"allowed": True}
    
    def record_assessment_submission(self, user_id: str, assessment_id: str, success: bool = True):
        """Record assessment submission attempt"""
        try:
            identifier = f"{user_id}:{assessment_id}"
            
            if success:
                self.record_successful_attempt(identifier, 'assessment')
            else:
                self.record_failed_attempt(identifier, 'assessment')
                
        except Exception as e:
            logger.error(f"Error recording assessment submission: {str(e)}")
    
    def get_suspicious_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get suspicious activity patterns"""
        try:
            if not self.redis_client:
                return []
            
            suspicious_events = []
            cutoff_time = time.time() - (hours * 3600)
            
            # Get all keys
            all_keys = self.redis_client.keys("*")
            
            for key in all_keys:
                if key.startswith("attempts:"):
                    # Parse key to get identifier and action type
                    parts = key.split(":")
                    if len(parts) >= 3:
                        action_type = parts[1]
                        identifier = ":".join(parts[2:])
                        
                        # Get attempt count
                        attempts = int(self.redis_client.get(key) or 0)
                        
                        if attempts >= self.config.suspicious_activity_threshold:
                            suspicious_events.append({
                                "identifier": identifier,
                                "action_type": action_type,
                                "attempts": attempts,
                                "key": key
                            })
            
            return suspicious_events
            
        except Exception as e:
            logger.error(f"Error getting suspicious activity: {str(e)}")
            return []
    
    def clear_lockout(self, identifier: str, action_type: str = 'login'):
        """Manually clear a lockout (admin function)"""
        try:
            if not self.redis_client:
                return
            
            attempts_key = f"attempts:{action_type}:{identifier}"
            lockout_key = f"lockout:{action_type}:{identifier}"
            
            # Clear both keys
            self.redis_client.delete(attempts_key, lockout_key)
            
            # Log admin action
            self._log_security_event("lockout_cleared", identifier, {
                "action_type": action_type,
                "cleared_by": "admin",
                "ip_address": request.remote_addr
            })
            
        except Exception as e:
            logger.error(f"Error clearing lockout: {str(e)}")
    
    def add_to_whitelist(self, identifier: str, whitelist_type: str = 'ip'):
        """Add identifier to whitelist"""
        try:
            if whitelist_type == 'ip':
                self.config.ip_whitelist.append(identifier)
            elif whitelist_type == 'user':
                self.config.user_whitelist.append(identifier)
            
            # Log whitelist addition
            self._log_security_event("whitelist_added", identifier, {
                "whitelist_type": whitelist_type,
                "added_by": "admin"
            })
            
        except Exception as e:
            logger.error(f"Error adding to whitelist: {str(e)}")
    
    def remove_from_whitelist(self, identifier: str, whitelist_type: str = 'ip'):
        """Remove identifier from whitelist"""
        try:
            if whitelist_type == 'ip':
                if identifier in self.config.ip_whitelist:
                    self.config.ip_whitelist.remove(identifier)
            elif whitelist_type == 'user':
                if identifier in self.config.user_whitelist:
                    self.config.user_whitelist.remove(identifier)
            
            # Log whitelist removal
            self._log_security_event("whitelist_removed", identifier, {
                "whitelist_type": whitelist_type,
                "removed_by": "admin"
            })
            
        except Exception as e:
            logger.error(f"Error removing from whitelist: {str(e)}")
    
    def _get_action_config(self, action_type: str) -> Dict[str, Any]:
        """Get configuration for specific action type"""
        configs = {
            'login': {
                'max_attempts': self.config.max_login_attempts,
                'lockout_duration': self.config.login_lockout_duration,
                'window_size': self.config.login_window_size
            },
            'assessment': {
                'max_attempts': self.config.max_assessment_attempts,
                'lockout_duration': self.config.assessment_lockout_duration,
                'window_size': self.config.assessment_window_size
            },
            'password_reset': {
                'max_attempts': self.config.max_password_reset_attempts,
                'lockout_duration': self.config.password_reset_lockout_duration,
                'window_size': self.config.password_reset_window_size
            }
        }
        
        return configs.get(action_type, configs['login'])
    
    def _calculate_lockout_duration(self, attempt_count: int, action_type: str) -> int:
        """Calculate lockout duration based on progressive lockout policy"""
        config = self._get_action_config(action_type)
        base_duration = config['lockout_duration']
        
        if not self.config.progressive_lockout_enabled:
            return base_duration
        
        # Calculate progressive duration
        progressive_duration = base_duration * (self.config.progressive_multiplier ** 
                                              (attempt_count - config['max_attempts']))
        
        return min(int(progressive_duration), self.config.max_lockout_duration)
    
    def _is_whitelisted(self, identifier: str) -> bool:
        """Check if identifier is whitelisted"""
        # Check IP whitelist
        if request.remote_addr in self.config.ip_whitelist:
            return True
        
        # Check user whitelist (for user-based identifiers)
        if identifier in self.config.user_whitelist:
            return True
        
        return False
    
    def _log_security_event(self, event_type: str, identifier: str, details: Dict[str, Any]):
        """Log security events"""
        event = SecurityEvent(
            event_type=event_type,
            identifier=identifier,
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
            f"Brute Force Security Event: {event_type} | Identifier: {identifier} | "
            f"IP: {event.ip_address} | Details: {details}"
        )
    
    def get_security_events(self, identifier: str = None, event_type: str = None, 
                          hours: int = 24) -> List[SecurityEvent]:
        """Get security events with optional filtering"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            events = [
                event for event in self.security_events
                if event.timestamp > cutoff_time
            ]
            
            if identifier:
                events = [event for event in events if event.identifier == identifier]
            
            if event_type:
                events = [event for event in events if event.event_type == event_type]
            
            return events
    
    def cleanup_old_data(self):
        """Clean up old security data"""
        try:
            if not self.redis_client:
                return
            
            # Clean up old security events (older than 7 days)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            with self.lock:
                self.security_events = [
                    event for event in self.security_events
                    if event.timestamp > cutoff_time
                ]
            
            # Note: Redis keys have TTL set, so they will expire automatically
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")

def create_brute_force_config() -> BruteForceConfig:
    """Create brute force protection configuration"""
    return BruteForceConfig(
        redis_host=current_app.config.get('REDIS_HOST', 'localhost'),
        redis_port=current_app.config.get('REDIS_PORT', 6379),
        redis_db=current_app.config.get('REDIS_DB_BRUTE_FORCE', 1),
        redis_password=current_app.config.get('REDIS_PASSWORD'),
        max_login_attempts=5,
        login_lockout_duration=300,
        max_assessment_attempts=10,
        assessment_lockout_duration=600,
        progressive_lockout_enabled=True,
        require_captcha_after=3,
        require_email_verification_after=10
    )

def get_brute_force_protection() -> BruteForceProtection:
    """Get the brute force protection instance"""
    if not hasattr(g, 'brute_force_protection'):
        config = create_brute_force_config()
        g.brute_force_protection = BruteForceProtection(config)
    return g.brute_force_protection
