"""
Phone Verification Service
Handles SMS verification for phone numbers during onboarding
"""

import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import re
import json

class VerificationService:
    """Service for handling phone verification with smart resend functionality"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
        self.max_resends = 3
        
        # Smart resend configuration
        self.resend_delays = [60, 120, 300]  # Progressive delays in seconds
        self.session_timeout = 3600  # 1 hour session timeout
        
    def generate_verification_code(self) -> str:
        """Generate a random 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=self.code_length))
    
    def hash_verification_code(self, code: str) -> str:
        """Hash verification code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number to E.164 format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        
        # Handle US numbers
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif len(digits_only) > 11:
            return f"+{digits_only}"
        else:
            # Return as is if it doesn't match expected patterns
            return phone_number
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        normalized = self.normalize_phone_number(phone_number)
        # Basic E.164 validation
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, normalized))
    
    def get_resend_delay(self, resend_count: int) -> int:
        """Get delay for next resend based on attempt count"""
        if resend_count < len(self.resend_delays):
            return self.resend_delays[resend_count]
        return self.resend_delays[-1]  # Use max delay for subsequent attempts
    
    def get_resend_message(self, resend_count: int) -> str:
        """Get appropriate message for resend attempt"""
        messages = [
            "We've sent a new verification code to your phone.",
            "Another verification code has been sent. Please check your messages.",
            "Final verification code sent. If you don't receive it, please try a different contact method."
        ]
        return messages[min(resend_count, len(messages) - 1)]
    
    def get_alternative_contact_message(self, resend_count: int) -> str:
        """Get message suggesting alternative contact methods"""
        if resend_count >= 2:
            return "Having trouble receiving SMS? You can try email verification or contact support."
        return ""
    
    def send_verification_code(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """
        Send verification code to phone number
        
        Args:
            user_id: User ID
            phone_number: Phone number to send code to
            
        Returns:
            Dict with success status and metadata
        """
        try:
            # Validate phone number
            if not self.validate_phone_number(phone_number):
                return {
                    'success': False,
                    'error': 'Invalid phone number format'
                }
            
            normalized_phone = self.normalize_phone_number(phone_number)
            
            # Check for existing verification attempts
            existing_verification = self._get_existing_verification(user_id, normalized_phone)
            
            if existing_verification:
                # Check if we can resend
                if existing_verification['attempts'] >= self.max_attempts:
                    return {
                        'success': False,
                        'error': 'Maximum verification attempts reached. Please try again later.',
                        'suggest_alternative': True
                    }
                
                # Check if code is still valid and within cooldown
                if existing_verification['code_expires_at'] > datetime.utcnow():
                    time_since_last_send = datetime.utcnow() - existing_verification['code_sent_at']
                    resend_delay = self.get_resend_delay(existing_verification['resend_count'])
                    
                    if time_since_last_send < timedelta(seconds=resend_delay):
                        remaining_seconds = resend_delay - int(time_since_last_send.total_seconds())
                        return {
                            'success': False,
                            'error': f'Please wait {remaining_seconds} seconds before requesting a new code.',
                            'cooldown_remaining': remaining_seconds,
                            'resend_count': existing_verification['resend_count']
                        }
            
            # Generate new verification code
            verification_code = self.generate_verification_code()
            code_hash = self.hash_verification_code(verification_code)
            expires_at = datetime.utcnow() + timedelta(minutes=self.code_expiry_minutes)
            
            # Store verification attempt
            verification_id = self._store_verification_attempt(
                user_id=user_id,
                phone_number=normalized_phone,
                code_hash=code_hash,
                expires_at=expires_at,
                is_resend=existing_verification is not None
            )
            
            # Track analytics
            self._track_verification_analytics(user_id, 'send_code', {
                'phone_number': normalized_phone,
                'resend_count': (existing_verification['resend_count'] + 1) if existing_verification else 1,
                'is_resend': existing_verification is not None
            })
            
            # TODO: Integrate with actual SMS service (Twilio, AWS SNS, etc.)
            # For now, we'll simulate sending the SMS
            self._send_sms_simulation(normalized_phone, verification_code)
            
            resend_count = (existing_verification['resend_count'] + 1) if existing_verification else 1
            next_delay = self.get_resend_delay(resend_count)
            
            logger.info(f"Verification code sent to {normalized_phone} for user {user_id} (attempt {resend_count})")
            
            return {
                'success': True,
                'message': self.get_resend_message(resend_count - 1),
                'verification_id': verification_id,
                'expires_at': expires_at.isoformat(),
                'resend_count': resend_count,
                'next_resend_delay': next_delay,
                'alternative_contact_message': self.get_alternative_contact_message(resend_count),
                'can_change_phone': resend_count >= 2
            }
            
        except Exception as e:
            logger.error(f"Error sending verification code: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to send verification code'
            }
    
    def verify_code(self, user_id: str, phone_number: str, code: str) -> Dict[str, Any]:
        """
        Verify the provided code
        
        Args:
            user_id: User ID
            phone_number: Phone number
            code: Verification code to verify
            
        Returns:
            Dict with verification result
        """
        try:
            normalized_phone = self.normalize_phone_number(phone_number)
            
            # Get the most recent verification attempt
            verification = self._get_latest_verification(user_id, normalized_phone)
            
            if not verification:
                return {
                    'success': False,
                    'error': 'No verification code found. Please request a new code.'
                }
            
            # Check if code has expired
            if verification['code_expires_at'] < datetime.utcnow():
                return {
                    'success': False,
                    'error': 'Verification code has expired. Please request a new code.'
                }
            
            # Check if maximum attempts reached
            if verification['attempts'] >= self.max_attempts:
                return {
                    'success': False,
                    'error': 'Maximum verification attempts reached. Please request a new code.',
                    'suggest_alternative': True
                }
            
            # Verify the code
            code_hash = self.hash_verification_code(code)
            if verification['verification_code_hash'] == code_hash:
                # Mark as verified
                self._mark_verification_success(verification['id'])
                
                # Update user profile with verified phone number
                self._update_user_phone_verification(user_id, normalized_phone)
                
                # Track analytics
                self._track_verification_analytics(user_id, 'verify_success', {
                    'phone_number': normalized_phone,
                    'attempts_used': verification['attempts'] + 1
                })
                
                logger.info(f"Phone verification successful for user {user_id}")
                
                return {
                    'success': True,
                    'message': 'Phone number verified successfully'
                }
            else:
                # Increment attempt count
                self._increment_attempt_count(verification['id'])
                
                remaining_attempts = self.max_attempts - (verification['attempts'] + 1)
                
                # Track analytics
                self._track_verification_analytics(user_id, 'verify_failed', {
                    'phone_number': normalized_phone,
                    'attempts_used': verification['attempts'] + 1,
                    'remaining_attempts': remaining_attempts
                })
                
                return {
                    'success': False,
                    'error': f'Invalid verification code. {remaining_attempts} attempts remaining.',
                    'remaining_attempts': remaining_attempts,
                    'suggest_alternative': remaining_attempts == 0
                }
                
        except Exception as e:
            logger.error(f"Error verifying code: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to verify code'
            }
    
    def resend_verification_code(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """
        Resend verification code with smart delay management
        
        Args:
            user_id: User ID
            phone_number: Phone number
            
        Returns:
            Dict with resend result
        """
        try:
            normalized_phone = self.normalize_phone_number(phone_number)
            
            # Get existing verification
            existing_verification = self._get_latest_verification(user_id, normalized_phone)
            
            if not existing_verification:
                return {
                    'success': False,
                    'error': 'No verification code found. Please request a new code.'
                }
            
            # Check if we can resend
            if existing_verification['resend_count'] >= self.max_resends:
                return {
                    'success': False,
                    'error': 'Maximum resend attempts reached. Please try a different contact method.',
                    'suggest_alternative': True
                }
            
            # Check if enough time has passed since last send (progressive delay)
            time_since_last_send = datetime.utcnow() - existing_verification['code_sent_at']
            required_delay = self.get_resend_delay(existing_verification['resend_count'])
            
            if time_since_last_send < timedelta(seconds=required_delay):
                remaining_seconds = required_delay - int(time_since_last_send.total_seconds())
                return {
                    'success': False,
                    'error': f'Please wait {remaining_seconds} seconds before requesting a new code.',
                    'cooldown_remaining': remaining_seconds,
                    'resend_count': existing_verification['resend_count']
                }
            
            # Send new verification code
            return self.send_verification_code(user_id, phone_number)
            
        except Exception as e:
            logger.error(f"Error resending verification code: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to resend verification code'
            }
    
    def get_verification_status(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """
        Get current verification status and attempt history
        
        Args:
            user_id: User ID
            phone_number: Phone number
            
        Returns:
            Dict with verification status and history
        """
        try:
            normalized_phone = self.normalize_phone_number(phone_number)
            
            # Get current verification
            current_verification = self._get_latest_verification(user_id, normalized_phone)
            
            if not current_verification:
                return {
                    'has_active_verification': False,
                    'can_send_code': True
                }
            
            # Calculate cooldown
            time_since_last_send = datetime.utcnow() - current_verification['code_sent_at']
            required_delay = self.get_resend_delay(current_verification['resend_count'])
            cooldown_remaining = max(0, required_delay - int(time_since_last_send.total_seconds()))
            
            # Get attempt history
            attempt_history = self._get_attempt_history(user_id, normalized_phone)
            
            return {
                'has_active_verification': True,
                'can_send_code': cooldown_remaining == 0 and current_verification['resend_count'] < self.max_resends,
                'cooldown_remaining': cooldown_remaining,
                'resend_count': current_verification['resend_count'],
                'max_resends': self.max_resends,
                'attempts_used': current_verification['attempts'],
                'max_attempts': self.max_attempts,
                'code_expires_at': current_verification['code_expires_at'].isoformat(),
                'attempt_history': attempt_history,
                'suggest_alternative': current_verification['resend_count'] >= 2,
                'can_change_phone': current_verification['resend_count'] >= 2
            }
            
        except Exception as e:
            logger.error(f"Error getting verification status: {str(e)}")
            return {
                'has_active_verification': False,
                'can_send_code': True,
                'error': 'Failed to get verification status'
            }
    
    def change_phone_number(self, user_id: str, old_phone: str, new_phone: str) -> Dict[str, Any]:
        """
        Change phone number for verification
        
        Args:
            user_id: User ID
            old_phone: Current phone number
            new_phone: New phone number
            
        Returns:
            Dict with change result
        """
        try:
            # Validate new phone number
            if not self.validate_phone_number(new_phone):
                return {
                    'success': False,
                    'error': 'Invalid phone number format'
                }
            
            normalized_new_phone = self.normalize_phone_number(new_phone)
            normalized_old_phone = self.normalize_phone_number(old_phone)
            
            # Check if new phone is already verified for this user
            existing_verification = self._get_latest_verification(user_id, normalized_new_phone)
            if existing_verification and existing_verification['status'] == 'verified':
                return {
                    'success': False,
                    'error': 'This phone number is already verified for your account.'
                }
            
            # Invalidate old verification attempts
            self._invalidate_old_verifications(user_id, normalized_old_phone)
            
            # Track analytics
            self._track_verification_analytics(user_id, 'change_phone', {
                'old_phone': normalized_old_phone,
                'new_phone': normalized_new_phone
            })
            
            logger.info(f"Phone number changed for user {user_id}: {normalized_old_phone} -> {normalized_new_phone}")
            
            return {
                'success': True,
                'message': 'Phone number changed successfully. You can now request a new verification code.',
                'new_phone': normalized_new_phone
            }
            
        except Exception as e:
            logger.error(f"Error changing phone number: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to change phone number'
            }
    
    def _get_existing_verification(self, user_id: str, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get existing verification attempt for user and phone number"""
        try:
            query = text("""
                SELECT id, user_id, phone_number, verification_code_hash, 
                       code_sent_at, code_expires_at, attempts, status, resend_count
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
                    'code_sent_at': result.code_sent_at,
                    'code_expires_at': result.code_expires_at,
                    'attempts': result.attempts,
                    'status': result.status,
                    'resend_count': result.resend_count or 0
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting existing verification: {str(e)}")
            return None
    
    def _get_latest_verification(self, user_id: str, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get the latest verification attempt for user and phone number"""
        try:
            query = text("""
                SELECT id, user_id, phone_number, verification_code_hash, 
                       code_sent_at, code_expires_at, attempts, status, resend_count
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
                    'code_sent_at': result.code_sent_at,
                    'code_expires_at': result.code_expires_at,
                    'attempts': result.attempts,
                    'status': result.status,
                    'resend_count': result.resend_count or 0
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest verification: {str(e)}")
            return None
    
    def _get_attempt_history(self, user_id: str, phone_number: str) -> List[Dict[str, Any]]:
        """Get attempt history for user and phone number"""
        try:
            query = text("""
                SELECT id, code_sent_at, attempts, status, resend_count, created_at
                FROM phone_verification 
                WHERE user_id = :user_id AND phone_number = :phone_number
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            results = self.db_session.execute(query, {
                'user_id': user_id,
                'phone_number': phone_number
            }).fetchall()
            
            history = []
            for result in results:
                history.append({
                    'id': result.id,
                    'sent_at': result.code_sent_at.isoformat(),
                    'attempts': result.attempts,
                    'status': result.status,
                    'resend_count': result.resend_count or 0,
                    'created_at': result.created_at.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting attempt history: {str(e)}")
            return []
    
    def _store_verification_attempt(self, user_id: str, phone_number: str, code_hash: str, 
                                  expires_at: datetime, is_resend: bool = False) -> str:
        """Store verification attempt in database"""
        try:
            if is_resend:
                # Update existing record
                query = text("""
                    UPDATE phone_verification 
                    SET verification_code_hash = :code_hash,
                        code_sent_at = NOW(),
                        code_expires_at = :expires_at,
                        attempts = 0,
                        resend_count = resend_count + 1,
                        updated_at = NOW()
                    WHERE user_id = :user_id AND phone_number = :phone_number
                    RETURNING id
                """)
            else:
                # Insert new record
                query = text("""
                    INSERT INTO phone_verification 
                    (user_id, phone_number, verification_code_hash, code_expires_at, attempts, resend_count)
                    VALUES (:user_id, :phone_number, :code_hash, :expires_at, 0, 1)
                    ON CONFLICT (user_id, phone_number) 
                    DO UPDATE SET 
                        verification_code_hash = :code_hash,
                        code_sent_at = NOW(),
                        code_expires_at = :expires_at,
                        attempts = 0,
                        resend_count = 1,
                        updated_at = NOW()
                    RETURNING id
                """)
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'phone_number': phone_number,
                'code_hash': code_hash,
                'expires_at': expires_at
            }).fetchone()
            
            self.db_session.commit()
            
            verification_id = str(result.id) if result else None
            logger.info(f"Stored verification attempt: {verification_id}")
            return verification_id
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error storing verification attempt: {str(e)}")
            raise
    
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
            
            logger.info(f"Marked verification {verification_id} as successful")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error marking verification success: {str(e)}")
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
            
            logger.info(f"Incremented attempt count for verification {verification_id}")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error incrementing attempt count: {str(e)}")
            raise
    
    def _invalidate_old_verifications(self, user_id: str, phone_number: str) -> None:
        """Invalidate old verification attempts for a phone number"""
        try:
            query = text("""
                UPDATE phone_verification 
                SET status = 'expired', updated_at = NOW()
                WHERE user_id = :user_id AND phone_number = :phone_number
            """)
            
            self.db_session.execute(query, {
                'user_id': user_id,
                'phone_number': phone_number
            })
            self.db_session.commit()
            
            logger.info(f"Invalidated old verifications for user {user_id}, phone {phone_number}")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error invalidating old verifications: {str(e)}")
            raise
    
    def _track_verification_analytics(self, user_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Track verification analytics"""
        try:
            # Store analytics in verification_analytics table
            query = text("""
                INSERT INTO verification_analytics 
                (user_id, event_type, event_data, created_at)
                VALUES (:user_id, :event_type, :event_data, NOW())
            """)
            
            self.db_session.execute(query, {
                'user_id': user_id,
                'event_type': event_type,
                'event_data': json.dumps(data)
            })
            self.db_session.commit()
            
            logger.info(f"Tracked verification analytics: {event_type} for user {user_id}")
            
        except Exception as e:
            # Don't fail the main operation if analytics tracking fails
            logger.warning(f"Failed to track verification analytics: {str(e)}")
    
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