"""
Phone Verification Service
Handles SMS verification for phone numbers during onboarding
"""

import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import re

class VerificationService:
    """Service for handling phone verification"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
        self.max_resends = 3
        
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
                        'error': 'Maximum verification attempts reached. Please try again later.'
                    }
                
                # Check if code is still valid
                if existing_verification['code_expires_at'] > datetime.utcnow():
                    return {
                        'success': False,
                        'error': 'Verification code already sent. Please wait before requesting a new one.'
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
            
            # TODO: Integrate with actual SMS service (Twilio, AWS SNS, etc.)
            # For now, we'll simulate sending the SMS
            self._send_sms_simulation(normalized_phone, verification_code)
            
            logger.info(f"Verification code sent to {normalized_phone} for user {user_id}")
            
            return {
                'success': True,
                'verification_id': verification_id,
                'expires_at': expires_at.isoformat(),
                'attempts': (existing_verification['attempts'] + 1) if existing_verification else 1
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
                    'error': 'Maximum verification attempts reached. Please request a new code.'
                }
            
            # Verify the code
            code_hash = self.hash_verification_code(code)
            if verification['verification_code_hash'] == code_hash:
                # Mark as verified
                self._mark_verification_success(verification['id'])
                
                # Update user profile with verified phone number
                self._update_user_phone_verification(user_id, normalized_phone)
                
                logger.info(f"Phone verification successful for user {user_id}")
                
                return {
                    'success': True,
                    'message': 'Phone number verified successfully'
                }
            else:
                # Increment attempt count
                self._increment_attempt_count(verification['id'])
                
                remaining_attempts = self.max_attempts - (verification['attempts'] + 1)
                
                return {
                    'success': False,
                    'error': f'Invalid verification code. {remaining_attempts} attempts remaining.',
                    'remaining_attempts': remaining_attempts
                }
                
        except Exception as e:
            logger.error(f"Error verifying code: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to verify code'
            }
    
    def resend_verification_code(self, user_id: str, phone_number: str) -> Dict[str, Any]:
        """
        Resend verification code
        
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
            if existing_verification['attempts'] >= self.max_attempts:
                return {
                    'success': False,
                    'error': 'Maximum verification attempts reached. Please try again later.'
                }
            
            # Check if enough time has passed since last send (rate limiting)
            time_since_last_send = datetime.utcnow() - existing_verification['code_sent_at']
            if time_since_last_send < timedelta(minutes=1):
                return {
                    'success': False,
                    'error': 'Please wait at least 1 minute before requesting a new code.'
                }
            
            # Send new verification code
            return self.send_verification_code(user_id, phone_number)
            
        except Exception as e:
            logger.error(f"Error resending verification code: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to resend verification code'
            }
    
    def _get_existing_verification(self, user_id: str, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get existing verification attempt for user and phone number"""
        try:
            query = text("""
                SELECT id, user_id, phone_number, verification_code_hash, 
                       code_sent_at, code_expires_at, attempts, status
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
                    'status': result.status
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
                       code_sent_at, code_expires_at, attempts, status
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
                    'status': result.status
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest verification: {str(e)}")
            return None
    
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
                        attempts = attempts + 1,
                        updated_at = NOW()
                    WHERE user_id = :user_id AND phone_number = :phone_number
                    RETURNING id
                """)
            else:
                # Insert new record
                query = text("""
                    INSERT INTO phone_verification 
                    (user_id, phone_number, verification_code_hash, code_expires_at, attempts)
                    VALUES (:user_id, :phone_number, :code_hash, :expires_at, 1)
                    ON CONFLICT (user_id, phone_number) 
                    DO UPDATE SET 
                        verification_code_hash = :code_hash,
                        code_sent_at = NOW(),
                        code_expires_at = :expires_at,
                        attempts = 1,
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