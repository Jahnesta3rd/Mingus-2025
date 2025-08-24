"""
Secure Phone Verification Service
Enhanced verification service with comprehensive security measures
"""

import secrets
import hashlib
import hmac
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text
import requests
from functools import wraps

from .verification_security import VerificationSecurity, SecurityEvent

class SecureVerificationService:
    """Enhanced verification service with comprehensive security"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.security = VerificationSecurity(db_session)
        
        # Configuration
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
        self.max_resends = 3
        
        # Smart resend configuration
        self.resend_delays = [60, 120, 300]  # Progressive delays in seconds
        self.session_timeout = 3600  # 1 hour session timeout
        
        # CAPTCHA configuration
        self.captcha_config = {
            'enabled': True,
            'provider': 'recaptcha',
            'site_key': 'your_recaptcha_site_key',
            'secret_key': 'your_recaptcha_secret_key',
        }
    
    def get_client_ip(self, request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (for proxy/load balancer setups)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr
    
    def get_user_agent(self, request) -> str:
        """Extract user agent from request"""
        return request.headers.get('User-Agent', 'Unknown')
    
    def log_security_event(self, request, event_type: str, user_id: Optional[str] = None, 
                          phone_number: Optional[str] = None, details: Dict[str, Any] = None) -> None:
        """Log security event with request context"""
        ip_address = self.get_client_ip(request)
        user_agent = self.get_user_agent(request)
        
        event_details = details or {}
        event_details.update({
            'user_agent': user_agent,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        risk_score = self.security.calculate_risk_score(
            event_type, user_id, ip_address, phone_number, event_details
        )
        
        security_event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            phone_number=phone_number,
            details=event_details,
            risk_score=risk_score,
            timestamp=datetime.utcnow()
        )
        
        self.security.log_security_event(security_event)
    
    def check_rate_limit(self, request, action: str, identifier: str) -> Tuple[bool, Optional[int]]:
        """Check rate limiting with request context"""
        ip_address = self.get_client_ip(request)
        return self.security.check_rate_limit(action, identifier, ip_address)
    
    def should_require_captcha(self, request, user_id: Optional[str] = None) -> bool:
        """Determine if CAPTCHA should be required"""
        ip_address = self.get_client_ip(request)
        return self.security.should_require_captcha(user_id, ip_address)
    
    def verify_captcha(self, request, captcha_token: str) -> bool:
        """Verify CAPTCHA token"""
        ip_address = self.get_client_ip(request)
        return self.security.verify_captcha(captcha_token, ip_address)
    
    def send_verification_code(self, request, user_id: str, phone_number: str, 
                              captcha_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Send verification code with comprehensive security checks
        
        Args:
            request: Flask request object
            user_id: User ID
            phone_number: Phone number to send code to
            captcha_token: CAPTCHA token if required
            
        Returns:
            Dict with success status and metadata
        """
        try:
            ip_address = self.get_client_ip(request)
            user_agent = self.get_user_agent(request)
            
            # Log the attempt
            self.log_security_event(
                request, 'send_code_attempt', user_id, phone_number,
                {'phone_number': phone_number}
            )
            
            # Check rate limiting
            allowed, retry_after = self.check_rate_limit(request, 'send_code', user_id)
            if not allowed:
                self.log_security_event(
                    request, 'rate_limit_exceeded', user_id, phone_number,
                    {'retry_after': retry_after}
                )
                return {
                    'success': False,
                    'error': 'Too many attempts. Please try again later.',
                    'retry_after': retry_after,
                    'error_type': 'rate_limit'
                }
            
            # Validate phone number
            if not self.security.validate_phone_number(phone_number):
                self.log_security_event(
                    request, 'invalid_phone', user_id, phone_number,
                    {'phone_number': phone_number}
                )
                return {
                    'success': False,
                    'error': 'Invalid phone number format.',
                    'error_type': 'phone_invalid'
                }
            
            normalized_phone = self.security.sanitize_phone_number(phone_number)
            
            # Check for SIM swap attacks
            if self.security.detect_sim_swap_attack(user_id, normalized_phone, ip_address):
                self.log_security_event(
                    request, 'sim_swap_detected', user_id, normalized_phone,
                    {'ip_address': ip_address}
                )
                return {
                    'success': False,
                    'error': 'Suspicious activity detected. Please contact support.',
                    'error_type': 'sim_swap_detected'
                }
            
            # Check if CAPTCHA is required
            if self.should_require_captcha(request, user_id):
                if not captcha_token:
                    return {
                        'success': False,
                        'error': 'CAPTCHA verification required.',
                        'error_type': 'captcha_required',
                        'captcha_required': True
                    }
                
                if not self.verify_captcha(request, captcha_token):
                    self.log_security_event(
                        request, 'captcha_failed', user_id, normalized_phone,
                        {'captcha_token': captcha_token}
                    )
                    return {
                        'success': False,
                        'error': 'CAPTCHA verification failed.',
                        'error_type': 'captcha_failed'
                    }
            
            # Generate secure verification code
            verification_code = self.security.generate_secure_code(self.code_length)
            code_hash, salt = self.security.hash_verification_code(verification_code)
            expires_at = datetime.utcnow() + timedelta(minutes=self.code_expiry_minutes)
            
            # Store verification attempt with security context
            verification_id = self._store_secure_verification_attempt(
                user_id=user_id,
                phone_number=normalized_phone,
                code_hash=code_hash,
                salt=salt,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                captcha_verified=bool(captcha_token)
            )
            
            # Calculate risk score for this verification
            risk_score = self.security.calculate_risk_score(
                'send_code', user_id, ip_address, normalized_phone,
                {'verification_id': verification_id}
            )
            
            # Update verification with risk score
            self._update_verification_risk_score(verification_id, risk_score)
            
            # Log successful send
            self.log_security_event(
                request, 'send_code_success', user_id, normalized_phone,
                {'verification_id': verification_id, 'risk_score': risk_score}
            )
            
            # TODO: Integrate with actual SMS service
            self._send_sms_simulation(normalized_phone, verification_code)
            
            return {
                'success': True,
                'message': 'Verification code sent successfully.',
                'verification_id': verification_id,
                'expires_at': expires_at.isoformat(),
                'risk_score': risk_score
            }
            
        except Exception as e:
            logger.error(f"Error sending verification code: {str(e)}")
            self.log_security_event(
                request, 'send_code_error', user_id, phone_number,
                {'error': str(e)}
            )
            return {
                'success': False,
                'error': 'Failed to send verification code.',
                'error_type': 'server_error'
            }
    
    def verify_code(self, request, user_id: str, phone_number: str, 
                   verification_code: str) -> Dict[str, Any]:
        """
        Verify code with security checks
        
        Args:
            request: Flask request object
            user_id: User ID
            phone_number: Phone number
            verification_code: Code to verify
            
        Returns:
            Dict with verification result
        """
        try:
            ip_address = self.get_client_ip(request)
            user_agent = self.get_user_agent(request)
            
            # Log verification attempt
            self.log_security_event(
                request, 'verify_attempt', user_id, phone_number,
                {'code_length': len(verification_code)}
            )
            
            # Check rate limiting
            allowed, retry_after = self.check_rate_limit(request, 'verify_code', user_id)
            if not allowed:
                self.log_security_event(
                    request, 'rate_limit_exceeded', user_id, phone_number,
                    {'retry_after': retry_after}
                )
                return {
                    'success': False,
                    'error': 'Too many verification attempts. Please try again later.',
                    'retry_after': retry_after,
                    'error_type': 'rate_limit'
                }
            
            normalized_phone = self.security.sanitize_phone_number(phone_number)
            
            # Get the most recent verification attempt
            verification = self._get_latest_verification(user_id, normalized_phone)
            
            if not verification:
                self.log_security_event(
                    request, 'verify_failed', user_id, normalized_phone,
                    {'reason': 'no_verification_found'}
                )
                return {
                    'success': False,
                    'error': 'No verification code found. Please request a new code.',
                    'error_type': 'no_verification'
                }
            
            # Check if code has expired
            if verification['code_expires_at'] < datetime.utcnow():
                self.log_security_event(
                    request, 'verify_failed', user_id, normalized_phone,
                    {'reason': 'code_expired'}
                )
                return {
                    'success': False,
                    'error': 'Verification code has expired. Please request a new code.',
                    'error_type': 'expired_code'
                }
            
            # Check if maximum attempts reached
            if verification['attempts'] >= self.max_attempts:
                self.log_security_event(
                    request, 'verify_failed', user_id, normalized_phone,
                    {'reason': 'max_attempts_reached', 'attempts': verification['attempts']}
                )
                return {
                    'success': False,
                    'error': 'Maximum verification attempts reached. Please request a new code.',
                    'error_type': 'max_attempts'
                }
            
            # Verify the code
            if self.security.verify_code_hash(verification_code, verification['verification_code_hash'], verification['salt']):
                # Mark as verified
                self._mark_verification_success(verification['id'])
                
                # Update user profile with verified phone number
                self._update_user_phone_verification(user_id, normalized_phone)
                
                # Log successful verification
                self.log_security_event(
                    request, 'verify_success', user_id, normalized_phone,
                    {'verification_id': verification['id'], 'attempts_used': verification['attempts'] + 1}
                )
                
                return {
                    'success': True,
                    'message': 'Phone number verified successfully.'
                }
            else:
                # Increment attempt count
                self._increment_attempt_count(verification['id'])
                
                remaining_attempts = self.max_attempts - (verification['attempts'] + 1)
                
                # Log failed verification
                self.log_security_event(
                    request, 'verify_failed', user_id, normalized_phone,
                    {'reason': 'invalid_code', 'remaining_attempts': remaining_attempts}
                )
                
                return {
                    'success': False,
                    'error': f'Invalid verification code. {remaining_attempts} attempts remaining.',
                    'remaining_attempts': remaining_attempts,
                    'error_type': 'invalid_code'
                }
                
        except Exception as e:
            logger.error(f"Error verifying code: {str(e)}")
            self.log_security_event(
                request, 'verify_error', user_id, phone_number,
                {'error': str(e)}
            )
            return {
                'success': False,
                'error': 'Failed to verify code.',
                'error_type': 'server_error'
            }
    
    def _store_secure_verification_attempt(self, user_id: str, phone_number: str, 
                                         code_hash: str, salt: str, expires_at: datetime,
                                         ip_address: str, user_agent: str, 
                                         captcha_verified: bool) -> str:
        """Store verification attempt with security context"""
        try:
            query = text("""
                INSERT INTO phone_verification 
                (user_id, phone_number, verification_code_hash, salt, code_expires_at, 
                 attempts, resend_count, ip_address, user_agent, captcha_verified)
                VALUES (:user_id, :phone_number, :code_hash, :salt, :expires_at, 
                        0, 1, :ip_address, :user_agent, :captcha_verified)
                RETURNING id
            """)
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'phone_number': phone_number,
                'code_hash': code_hash,
                'salt': salt,
                'expires_at': expires_at,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'captcha_verified': captcha_verified
            }).fetchone()
            
            self.db_session.commit()
            return str(result.id) if result else None
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error storing secure verification attempt: {str(e)}")
            raise
    
    def _get_latest_verification(self, user_id: str, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get the latest verification attempt with security context"""
        try:
            query = text("""
                SELECT id, user_id, phone_number, verification_code_hash, salt,
                       code_sent_at, code_expires_at, attempts, status, resend_count,
                       ip_address, user_agent, captcha_verified, risk_score
                FROM phone_verification 
                WHERE user_id = :user_id AND phone_number = :phone_number
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'phone_number': phone_number
            }).fetchone()
            
            if result:
                return {
                    'id': result.id,
                    'user_id': result.user_id,
                    'phone_number': result.phone_number,
                    'verification_code_hash': result.verification_code_hash,
                    'salt': result.salt,
                    'code_sent_at': result.code_sent_at,
                    'code_expires_at': result.code_expires_at,
                    'attempts': result.attempts,
                    'status': result.status,
                    'resend_count': result.resend_count,
                    'ip_address': result.ip_address,
                    'user_agent': result.user_agent,
                    'captcha_verified': result.captcha_verified,
                    'risk_score': result.risk_score
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest verification: {str(e)}")
            return None
    
    def _update_verification_risk_score(self, verification_id: str, risk_score: float) -> None:
        """Update verification with risk score"""
        try:
            query = text("""
                UPDATE phone_verification 
                SET risk_score = :risk_score, updated_at = NOW()
                WHERE id = :verification_id
            """)
            
            self.db_session.execute(query, {
                'verification_id': verification_id,
                'risk_score': risk_score
            })
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error updating risk score: {str(e)}")
            self.db_session.rollback()
    
    def _mark_verification_success(self, verification_id: str) -> None:
        """Mark verification as successful"""
        try:
            query = text("""
                UPDATE phone_verification 
                SET status = 'verified', updated_at = NOW()
                WHERE id = :verification_id
            """)
            
            self.db_session.execute(query, {'verification_id': verification_id})
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error marking verification success: {str(e)}")
            self.db_session.rollback()
            raise
    
    def _increment_attempt_count(self, verification_id: str) -> None:
        """Increment attempt count for verification"""
        try:
            query = text("""
                UPDATE phone_verification 
                SET attempts = attempts + 1, 
                    last_attempt_at = NOW(),
                    updated_at = NOW()
                WHERE id = :verification_id
            """)
            
            self.db_session.execute(query, {'verification_id': verification_id})
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error incrementing attempt count: {str(e)}")
            self.db_session.rollback()
            raise
    
    def _update_user_phone_verification(self, user_id: str, phone_number: str) -> None:
        """Update user profile with verified phone number"""
        try:
            # This would update the user_profiles table
            # For now, just log the verification
            logger.info(f"Updated user {user_id} with verified phone {phone_number}")
            
            # TODO: Add actual user profile update logic here
            # query = text("""
            #     UPDATE user_profiles 
            #     SET phone_number = :phone_number, 
            #         phone_verified = true,
            #         phone_verified_at = NOW()
            #     WHERE user_id = :user_id
            # """)
            # 
            # self.db_session.execute(query, {
            #     'user_id': user_id,
            #     'phone_number': phone_number
            # })
            # self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error updating user phone verification: {str(e)}")
            raise
    
    def _send_sms_simulation(self, phone_number: str, code: str) -> None:
        """Simulate sending SMS (replace with actual SMS service)"""
        # TODO: Replace with actual SMS service integration
        # Examples: Twilio, AWS SNS, SendGrid, etc.
        logger.info(f"SMS SIMULATION: Code {code} sent to {phone_number}")
        logger.info("In production, integrate with SMS service like Twilio or AWS SNS")
    
    def get_security_summary(self, user_id: str) -> Dict[str, Any]:
        """Get security summary for a user"""
        try:
            query = text("""
                SELECT * FROM user_security_summary WHERE user_id = :user_id
            """)
            
            result = self.db_session.execute(query, {'user_id': user_id}).fetchone()
            
            if result:
                return {
                    'user_id': result.user_id,
                    'total_verifications': result.total_verifications,
                    'successful_verifications': result.successful_verifications,
                    'failed_verifications': result.failed_verifications,
                    'unique_ips': result.unique_ips,
                    'unique_phones': result.unique_phones,
                    'last_verification': result.last_verification.isoformat() if result.last_verification else None,
                    'avg_risk_score': float(result.avg_risk_score) if result.avg_risk_score else 0.0
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting security summary: {str(e)}")
            return {} 