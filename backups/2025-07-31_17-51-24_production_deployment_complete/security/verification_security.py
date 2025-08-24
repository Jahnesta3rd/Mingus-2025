"""
Phone Verification Security Module
Comprehensive security measures for phone verification system
"""

import secrets
import hashlib
import hmac
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text
import ipaddress
import requests
from functools import wraps
import threading
from collections import defaultdict

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    phone_number: Optional[str]
    details: Dict[str, Any]
    risk_score: float
    timestamp: datetime

class VerificationSecurity:
    """Comprehensive security for phone verification"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.rate_limit_cache = defaultdict(list)
        self.lock = threading.Lock()
        
        # Rate limiting configuration
        self.rate_limits = {
            'send_code': {'max_attempts': 5, 'window': 3600},  # 5 per hour
            'verify_code': {'max_attempts': 10, 'window': 3600},  # 10 per hour
            'resend_code': {'max_attempts': 3, 'window': 3600},  # 3 per hour
            'change_phone': {'max_attempts': 3, 'window': 86400},  # 3 per day
        }
        
        # Security thresholds
        self.security_thresholds = {
            'max_failed_attempts': 5,
            'captcha_trigger_attempts': 3,
            'suspicious_ip_threshold': 10,
            'suspicious_phone_threshold': 5,
            'sim_swap_detection_window': 86400,  # 24 hours
        }
        
        # CAPTCHA configuration
        self.captcha_config = {
            'enabled': True,
            'provider': 'recaptcha',  # or 'hcaptcha'
            'site_key': 'your_recaptcha_site_key',
            'secret_key': 'your_recaptcha_secret_key',
        }
    
    def generate_secure_code(self, length: int = 6) -> str:
        """
        Generate cryptographically secure verification code
        
        Args:
            length: Length of the code (default: 6)
            
        Returns:
            Cryptographically secure random code
        """
        # Use secrets module for cryptographically secure random numbers
        digits = '0123456789'
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    def hash_verification_code(self, code: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash verification code with salt for secure storage
        
        Args:
            code: Verification code to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use HMAC with SHA-256 for secure hashing
        hash_obj = hmac.new(
            salt.encode('utf-8'),
            code.encode('utf-8'),
            hashlib.sha256
        )
        
        return hash_obj.hexdigest(), salt
    
    def verify_code_hash(self, code: str, stored_hash: str, salt: str) -> bool:
        """
        Verify a code against its stored hash
        
        Args:
            code: Code to verify
            stored_hash: Stored hash to compare against
            salt: Salt used for hashing
            
        Returns:
            True if code matches hash
        """
        expected_hash, _ = self.hash_verification_code(code, salt)
        return hmac.compare_digest(expected_hash, stored_hash)
    
    def sanitize_phone_number(self, phone_number: str) -> str:
        """
        Sanitize and validate phone number
        
        Args:
            phone_number: Raw phone number input
            
        Returns:
            Sanitized phone number in E.164 format
            
        Raises:
            ValueError: If phone number is invalid
        """
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        
        # Basic validation
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Invalid phone number length")
        
        # Handle US numbers
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif len(digits_only) > 11:
            return f"+{digits_only}"
        else:
            raise ValueError("Invalid phone number format")
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format and check for suspicious patterns
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            True if valid and not suspicious
        """
        try:
            normalized = self.sanitize_phone_number(phone_number)
            
            # Check for suspicious patterns
            if self._is_suspicious_phone_number(normalized):
                return False
            
            # Basic E.164 validation
            pattern = r'^\+[1-9]\d{1,14}$'
            return bool(re.match(pattern, normalized))
            
        except ValueError:
            return False
    
    def _is_suspicious_phone_number(self, phone_number: str) -> bool:
        """
        Check for suspicious phone number patterns
        
        Args:
            phone_number: Normalized phone number
            
        Returns:
            True if suspicious
        """
        # Check for sequential digits
        digits = re.sub(r'\D', '', phone_number)
        if len(set(digits)) <= 2:  # Too few unique digits
            return True
        
        # Check for repeated patterns
        if len(digits) >= 4:
            for i in range(len(digits) - 3):
                pattern = digits[i:i+4]
                if pattern == pattern[::-1]:  # Palindrome
                    return True
        
        # Check for common test numbers
        test_patterns = [
            r'\+1234567890',
            r'\+1111111111',
            r'\+0000000000',
        ]
        
        for pattern in test_patterns:
            if re.match(pattern, phone_number):
                return True
        
        return False
    
    def check_rate_limit(self, action: str, identifier: str, ip_address: str) -> Tuple[bool, Optional[int]]:
        """
        Check rate limiting for an action
        
        Args:
            action: Type of action (send_code, verify_code, etc.)
            identifier: User identifier (user_id or phone_number)
            ip_address: IP address of the request
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        if action not in self.rate_limits:
            return True, None
        
        limit_config = self.rate_limits[action]
        current_time = time.time()
        
        with self.lock:
            # Check IP-based rate limiting
            ip_key = f"ip:{ip_address}:{action}"
            ip_attempts = self.rate_limit_cache[ip_key]
            
            # Remove old attempts outside the window
            ip_attempts = [t for t in ip_attempts if current_time - t < limit_config['window']]
            
            if len(ip_attempts) >= limit_config['max_attempts']:
                retry_after = int(limit_config['window'] - (current_time - ip_attempts[0]))
                return False, retry_after
            
            # Check identifier-based rate limiting
            id_key = f"id:{identifier}:{action}"
            id_attempts = self.rate_limit_cache[id_key]
            
            # Remove old attempts outside the window
            id_attempts = [t for t in id_attempts if current_time - t < limit_config['window']]
            
            if len(id_attempts) >= limit_config['max_attempts']:
                retry_after = int(limit_config['window'] - (current_time - id_attempts[0]))
                return False, retry_after
            
            # Record this attempt
            ip_attempts.append(current_time)
            id_attempts.append(current_time)
            
            self.rate_limit_cache[ip_key] = ip_attempts
            self.rate_limit_cache[id_key] = id_attempts
            
            return True, None
    
    def verify_captcha(self, captcha_token: str, ip_address: str) -> bool:
        """
        Verify CAPTCHA token
        
        Args:
            captcha_token: CAPTCHA token from frontend
            ip_address: IP address of the request
            
        Returns:
            True if CAPTCHA is valid
        """
        if not self.captcha_config['enabled']:
            return True
        
        try:
            # Verify with reCAPTCHA
            if self.captcha_config['provider'] == 'recaptcha':
                return self._verify_recaptcha(captcha_token, ip_address)
            elif self.captcha_config['provider'] == 'hcaptcha':
                return self._verify_hcaptcha(captcha_token, ip_address)
            else:
                logger.warning(f"Unknown CAPTCHA provider: {self.captcha_config['provider']}")
                return False
                
        except Exception as e:
            logger.error(f"CAPTCHA verification failed: {e}")
            return False
    
    def _verify_recaptcha(self, token: str, ip_address: str) -> bool:
        """Verify reCAPTCHA token"""
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': self.captcha_config['secret_key'],
                    'response': token,
                    'remoteip': ip_address
                },
                timeout=10
            )
            
            result = response.json()
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {e}")
            return False
    
    def _verify_hcaptcha(self, token: str, ip_address: str) -> bool:
        """Verify hCaptcha token"""
        try:
            response = requests.post(
                'https://hcaptcha.com/siteverify',
                data={
                    'secret': self.captcha_config['secret_key'],
                    'response': token,
                    'remoteip': ip_address
                },
                timeout=10
            )
            
            result = response.json()
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"hCaptcha verification error: {e}")
            return False
    
    def detect_sim_swap_attack(self, user_id: str, phone_number: str, ip_address: str) -> bool:
        """
        Detect potential SIM swapping attacks
        
        Args:
            user_id: User ID
            phone_number: Phone number being verified
            ip_address: IP address of the request
            
        Returns:
            True if potential SIM swap attack detected
        """
        try:
            # Check for recent phone number changes
            query = text("""
                SELECT COUNT(*) as change_count
                FROM phone_verification 
                WHERE user_id = :user_id 
                AND phone_number != :phone_number
                AND created_at >= :since_time
            """)
            
            since_time = datetime.utcnow() - timedelta(seconds=self.security_thresholds['sim_swap_detection_window'])
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'phone_number': phone_number,
                'since_time': since_time
            }).fetchone()
            
            if result and result.change_count > 2:
                return True
            
            # Check for IP address changes
            query = text("""
                SELECT COUNT(DISTINCT ip_address) as ip_count
                FROM verification_audit_log 
                WHERE user_id = :user_id 
                AND created_at >= :since_time
            """)
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'since_time': since_time
            }).fetchone()
            
            if result and result.ip_count > 3:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"SIM swap detection error: {e}")
            return False
    
    def log_security_event(self, event: SecurityEvent) -> None:
        """
        Log security event to database
        
        Args:
            event: Security event to log
        """
        try:
            query = text("""
                INSERT INTO verification_audit_log 
                (user_id, ip_address, user_agent, phone_number, event_type, 
                 event_details, risk_score, created_at)
                VALUES (:user_id, :ip_address, :user_agent, :phone_number, :event_type,
                        :event_details, :risk_score, :created_at)
            """)
            
            self.db_session.execute(query, {
                'user_id': event.user_id,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'phone_number': event.phone_number,
                'event_type': event.event_type,
                'event_details': json.dumps(event.details),
                'risk_score': event.risk_score,
                'created_at': event.timestamp
            })
            
            self.db_session.commit()
            
            # Log to application logs
            logger.info(f"Security event logged: {event.event_type} for user {event.user_id} "
                       f"from {event.ip_address} (risk: {event.risk_score})")
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            self.db_session.rollback()
    
    def calculate_risk_score(self, event_type: str, user_id: Optional[str], 
                           ip_address: str, phone_number: Optional[str], 
                           details: Dict[str, Any]) -> float:
        """
        Calculate risk score for a security event
        
        Args:
            event_type: Type of security event
            user_id: User ID (if available)
            ip_address: IP address of the request
            phone_number: Phone number (if available)
            details: Additional event details
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        risk_score = 0.0
        
        # Base risk by event type
        event_risk = {
            'failed_verification': 0.3,
            'multiple_failures': 0.6,
            'rate_limit_exceeded': 0.7,
            'suspicious_ip': 0.8,
            'suspicious_phone': 0.9,
            'sim_swap_detected': 0.95,
            'captcha_failed': 0.5,
        }
        
        risk_score += event_risk.get(event_type, 0.1)
        
        # Check for suspicious IP
        if self._is_suspicious_ip(ip_address):
            risk_score += 0.3
        
        # Check for multiple failures
        if details.get('failure_count', 0) > 3:
            risk_score += 0.2
        
        # Check for rapid requests
        if details.get('time_since_last', 0) < 5:  # Less than 5 seconds
            risk_score += 0.2
        
        # Check for known malicious patterns
        if self._has_malicious_patterns(details):
            risk_score += 0.4
        
        return min(risk_score, 1.0)
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        try:
            # Check for private/local IPs
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private or ip.is_loopback:
                return True
            
            # Check for known malicious IPs (would integrate with threat intel)
            # For now, just check for some basic patterns
            suspicious_patterns = [
                r'^0\.0\.0\.',  # Invalid IPs
                r'^255\.255\.255\.',  # Broadcast
            ]
            
            for pattern in suspicious_patterns:
                if re.match(pattern, ip_address):
                    return True
            
            return False
            
        except ValueError:
            return True
    
    def _has_malicious_patterns(self, details: Dict[str, Any]) -> bool:
        """Check for malicious patterns in request details"""
        # Check for automated behavior patterns
        user_agent = details.get('user_agent', '').lower()
        
        malicious_indicators = [
            'bot', 'crawler', 'spider', 'scraper',
            'curl', 'wget', 'python-requests',
            'headless', 'phantom', 'selenium'
        ]
        
        for indicator in malicious_indicators:
            if indicator in user_agent:
                return True
        
        # Check for rapid-fire requests
        if details.get('requests_per_minute', 0) > 60:
            return True
        
        return False
    
    def should_require_captcha(self, user_id: Optional[str], ip_address: str) -> bool:
        """
        Determine if CAPTCHA should be required
        
        Args:
            user_id: User ID (if available)
            ip_address: IP address of the request
            
        Returns:
            True if CAPTCHA should be required
        """
        try:
            # Check recent failed attempts
            query = text("""
                SELECT COUNT(*) as failed_count
                FROM verification_audit_log 
                WHERE (user_id = :user_id OR ip_address = :ip_address)
                AND event_type = 'failed_verification'
                AND created_at >= :since_time
            """)
            
            since_time = datetime.utcnow() - timedelta(hours=1)
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'ip_address': ip_address,
                'since_time': since_time
            }).fetchone()
            
            if result and result.failed_count >= self.security_thresholds['captcha_trigger_attempts']:
                return True
            
            # Check for suspicious IP
            if self._is_suspicious_ip(ip_address):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"CAPTCHA requirement check error: {e}")
            return True  # Require CAPTCHA on error for safety
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """
        Clean up old security data for GDPR compliance
        
        Args:
            days: Keep data newer than this many days
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Clean up old audit logs
            query = text("""
                DELETE FROM verification_audit_log 
                WHERE created_at < :cutoff_date
            """)
            
            result = self.db_session.execute(query, {
                'cutoff_date': cutoff_date
            })
            
            self.db_session.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old security audit records")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old security data: {e}")
            self.db_session.rollback()
            return 0 