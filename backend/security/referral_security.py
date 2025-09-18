#!/usr/bin/env python3
"""
Referral System Security Module
Handles fraud prevention, rate limiting, and access control for referral-gated features
"""

import hashlib
import hmac
import time
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from functools import wraps
import sqlite3
import ipaddress

logger = logging.getLogger(__name__)

class ReferralSecurityManager:
    """Manages security for referral system and feature access"""
    
    def __init__(self, db_path: str = 'referral_system.db'):
        self.db_path = db_path
        self.rate_limits = {}
        self.suspicious_ips = set()
        self.init_security_tables()
    
    def init_security_tables(self):
        """Initialize security-related database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Security events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    details TEXT,
                    severity TEXT DEFAULT 'low',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Rate limiting table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT NOT NULL,
                    action TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Fraud detection table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fraud_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    ip_address TEXT,
                    indicator_type TEXT NOT NULL,
                    details TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Blocked users/IPs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_value TEXT NOT NULL,
                    reason TEXT,
                    blocked_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_user ON security_events(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON rate_limits(identifier)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fraud_indicators_user ON fraud_indicators(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocked_entities_value ON blocked_entities(entity_value)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing security tables: {e}")
            raise
    
    def check_rate_limit(self, identifier: str, action: str, limit: int, window_minutes: int = 60) -> bool:
        """Check if action is within rate limit"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean old entries
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
            cursor.execute('''
                DELETE FROM rate_limits 
                WHERE window_start < ?
            ''', (cutoff_time,))
            
            # Check current count
            cursor.execute('''
                SELECT COUNT(*) FROM rate_limits 
                WHERE identifier = ? AND action = ? AND window_start >= ?
            ''', (identifier, action, cutoff_time))
            
            current_count = cursor.fetchone()[0]
            
            if current_count >= limit:
                conn.close()
                return False
            
            # Add current request
            cursor.execute('''
                INSERT INTO rate_limits (identifier, action)
                VALUES (?, ?)
            ''', (identifier, action))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False
    
    def log_security_event(self, event_type: str, user_id: str = None, 
                          ip_address: str = None, user_agent: str = None,
                          details: str = None, severity: str = 'low'):
        """Log security events for monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_events 
                (event_type, user_id, ip_address, user_agent, details, severity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (event_type, user_id, ip_address, user_agent, details, severity))
            
            conn.commit()
            conn.close()
            
            # Log to application logger
            logger.info(f"Security event: {event_type} - User: {user_id} - IP: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def detect_referral_fraud(self, referrer_user_id: str, referred_email: str, 
                            ip_address: str = None) -> Dict:
        """Detect potential referral fraud"""
        try:
            fraud_indicators = []
            confidence_score = 0.0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for duplicate referrals from same IP
            if ip_address:
                cursor.execute('''
                    SELECT COUNT(*) FROM referrals r
                    JOIN security_events se ON r.referrer_user_id = se.user_id
                    WHERE se.ip_address = ? AND r.created_at > datetime('now', '-24 hours')
                ''', (ip_address,))
                
                duplicate_count = cursor.fetchone()[0]
                if duplicate_count > 5:
                    fraud_indicators.append({
                        'type': 'duplicate_ip_referrals',
                        'details': f'Multiple referrals from same IP: {duplicate_count}',
                        'confidence': 0.8
                    })
                    confidence_score += 0.8
            
            # Check for rapid referrals
            cursor.execute('''
                SELECT COUNT(*) FROM referrals 
                WHERE referrer_user_id = ? AND created_at > datetime('now', '-1 hour')
            ''', (referrer_user_id,))
            
            rapid_count = cursor.fetchone()[0]
            if rapid_count > 3:
                fraud_indicators.append({
                    'type': 'rapid_referrals',
                    'details': f'Rapid referrals: {rapid_count} in 1 hour',
                    'confidence': 0.6
                })
                confidence_score += 0.6
            
            # Check for email pattern abuse
            if self._is_suspicious_email(referred_email):
                fraud_indicators.append({
                    'type': 'suspicious_email',
                    'details': f'Suspicious email pattern: {referred_email}',
                    'confidence': 0.7
                })
                confidence_score += 0.7
            
            # Check for self-referral attempts
            cursor.execute('''
                SELECT email FROM users WHERE user_id = ?
            ''', (referrer_user_id,))
            
            referrer_email = cursor.fetchone()
            if referrer_email and referrer_email[0].lower() == referred_email.lower():
                fraud_indicators.append({
                    'type': 'self_referral',
                    'details': 'Attempted self-referral',
                    'confidence': 1.0
                })
                confidence_score = 1.0
            
            # Save fraud indicators
            for indicator in fraud_indicators:
                cursor.execute('''
                    INSERT INTO fraud_indicators 
                    (user_id, ip_address, indicator_type, details, confidence_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (referrer_user_id, ip_address, indicator['type'], 
                      indicator['details'], indicator['confidence']))
            
            conn.commit()
            conn.close()
            
            return {
                'is_fraud': confidence_score > 0.7,
                'confidence_score': min(confidence_score, 1.0),
                'indicators': fraud_indicators
            }
            
        except Exception as e:
            logger.error(f"Error detecting referral fraud: {e}")
            return {'is_fraud': False, 'confidence_score': 0.0, 'indicators': []}
    
    def _is_suspicious_email(self, email: str) -> bool:
        """Check if email appears suspicious"""
        suspicious_patterns = [
            r'^test\d+@',  # test123@...
            r'^temp\d+@',  # temp456@...
            r'^fake\d+@',  # fake789@...
            r'@(10minutemail|guerrillamail|mailinator)\.',  # Temporary email services
            r'^\w+@\w+\.\w+\.\w+$',  # Multiple subdomains
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email.lower()):
                return True
        
        return False
    
    def validate_referral_code(self, referral_code: str) -> bool:
        """Validate referral code format and existence"""
        if not referral_code or len(referral_code) < 8:
            return False
        
        # Check format (alphanumeric, 8-16 characters)
        if not re.match(r'^[A-Za-z0-9]{8,16}$', referral_code):
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM users WHERE referral_code = ?
            ''', (referral_code,))
            
            exists = cursor.fetchone() is not None
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"Error validating referral code: {e}")
            return False
    
    def block_entity(self, entity_type: str, entity_value: str, 
                    reason: str, blocked_until: datetime = None):
        """Block user or IP address"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO blocked_entities 
                (entity_type, entity_value, reason, blocked_until)
                VALUES (?, ?, ?, ?)
            ''', (entity_type, entity_value, reason, blocked_until))
            
            conn.commit()
            conn.close()
            
            self.log_security_event(
                'entity_blocked', 
                details=f'{entity_type}: {entity_value} - {reason}',
                severity='high'
            )
            
        except Exception as e:
            logger.error(f"Error blocking entity: {e}")
    
    def is_entity_blocked(self, entity_type: str, entity_value: str) -> bool:
        """Check if entity is currently blocked"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM blocked_entities 
                WHERE entity_type = ? AND entity_value = ? 
                AND (blocked_until IS NULL OR blocked_until > CURRENT_TIMESTAMP)
            ''', (entity_type, entity_value))
            
            is_blocked = cursor.fetchone() is not None
            conn.close()
            
            return is_blocked
            
        except Exception as e:
            logger.error(f"Error checking entity block: {e}")
            return False
    
    def generate_secure_token(self, data: str) -> str:
        """Generate secure token for sensitive operations"""
        timestamp = str(int(time.time()))
        message = f"{data}:{timestamp}"
        secret = "mingus_referral_secret_key"  # In production, use environment variable
        
        token = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{token}:{timestamp}"
    
    def validate_secure_token(self, token: str, data: str, max_age_seconds: int = 3600) -> bool:
        """Validate secure token"""
        try:
            if ':' not in token:
                return False
            
            token_hash, timestamp = token.split(':', 1)
            current_time = int(time.time())
            token_time = int(timestamp)
            
            # Check token age
            if current_time - token_time > max_age_seconds:
                return False
            
            # Regenerate expected token
            message = f"{data}:{timestamp}"
            secret = "mingus_referral_secret_key"  # In production, use environment variable
            
            expected_token = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(token_hash, expected_token)
            
        except Exception as e:
            logger.error(f"Error validating secure token: {e}")
            return False

def require_referral_security(f):
    """Decorator for referral-gated endpoints with security checks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        security_manager = ReferralSecurityManager()
        user_id = request.headers.get('X-User-ID')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Check if IP is blocked
        if security_manager.is_entity_blocked('ip', ip_address):
            security_manager.log_security_event(
                'blocked_ip_access_attempt',
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity='high'
            )
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'code': 'BLOCKED_IP'
            }), 403
        
        # Check if user is blocked
        if user_id and security_manager.is_entity_blocked('user', user_id):
            security_manager.log_security_event(
                'blocked_user_access_attempt',
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity='high'
            )
            return jsonify({
                'success': False,
                'error': 'Account suspended',
                'code': 'BLOCKED_USER'
            }), 403
        
        # Rate limiting
        if not security_manager.check_rate_limit(
            f"{ip_address}:{user_id}", 
            request.endpoint, 
            limit=10, 
            window_minutes=60
        ):
            security_manager.log_security_event(
                'rate_limit_exceeded',
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity='medium'
            )
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'code': 'RATE_LIMIT'
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_file_upload(file, allowed_extensions: set, max_size: int) -> Dict:
    """Validate file upload for security"""
    if not file or file.filename == '':
        return {'valid': False, 'error': 'No file provided'}
    
    # Check file extension
    if '.' not in file.filename:
        return {'valid': False, 'error': 'Invalid file type'}
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension not in allowed_extensions:
        return {'valid': False, 'error': f'File type .{extension} not allowed'}
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        return {'valid': False, 'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'}
    
    # Check for suspicious content (basic)
    file_content = file.read(1024)  # Read first 1KB
    file.seek(0)  # Reset to beginning
    
    # Check for executable signatures
    executable_signatures = [b'MZ', b'\x7fELF', b'\xfe\xed\xfa', b'\xce\xfa\xed\xfe']
    if any(file_content.startswith(sig) for sig in executable_signatures):
        return {'valid': False, 'error': 'Executable files not allowed'}
    
    return {'valid': True, 'file_size': file_size, 'extension': extension}

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return ''
    
    # Limit length
    text = text[:max_length]
    
    # Remove script tags first
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()
