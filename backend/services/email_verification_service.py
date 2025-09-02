"""
Email Verification Service for MINGUS Flask Application
Comprehensive service for managing email verification with security and cultural awareness
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, func

# Use absolute imports for compatibility with test environment
try:
    from models.email_verification import EmailVerification
    from models.user import User
    from models.audit import AuditLog
    from database import get_db_session
    from .resend_email_service import ResendEmailService
except ImportError:
    # Fallback for production environment
    from ..models.email_verification import EmailVerification
    from ..models.user import User
    from ..models.audit import AuditLog
    from ..database import get_db_session
    from .resend_email_service import ResendEmailService

logger = logging.getLogger(__name__)

class EmailVerificationService:
    """Service for managing email verification processes"""
    
    def __init__(self):
        self.email_service = ResendEmailService()
        self.verification_expiry_hours = int(os.getenv('EMAIL_VERIFICATION_EXPIRY_HOURS', '24'))
        self.max_resend_attempts = int(os.getenv('MAX_EMAIL_RESEND_ATTEMPTS', '5'))
        self.resend_cooldown_hours = int(os.getenv('EMAIL_RESEND_COOLDOWN_HOURS', '1'))
        
    def create_verification(self, user_id: int, email: str, verification_type: str = 'signup',
                           old_email: str = None, ip_address: str = None, 
                           user_agent: str = None) -> Tuple[EmailVerification, str]:
        """
        Create a new email verification record
        
        Args:
            user_id: User ID
            email: Email to verify
            verification_type: Type of verification (signup, email_change, password_reset)
            old_email: Previous email (for email change verification)
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Tuple of (EmailVerification object, plaintext token)
        """
        try:
            with get_db_session() as db:
                # Check if user already has a verification record
                existing_verification = db.query(EmailVerification).filter(
                    EmailVerification.user_id == user_id,
                    EmailVerification.verification_type == verification_type
                ).first()
                
                if existing_verification:
                    # Update existing verification
                    existing_verification.email = email
                    existing_verification.old_email = old_email
                    existing_verification.expires_at = datetime.utcnow() + timedelta(hours=self.verification_expiry_hours)
                    existing_verification.resend_count = 0
                    existing_verification.last_resend_at = None
                    existing_verification.failed_attempts = 0
                    existing_verification.locked_until = None
                    existing_verification.ip_address = ip_address
                    existing_verification.user_agent = user_agent
                    
                    # Generate new token
                    new_token = existing_verification.generate_token()
                    existing_verification.verification_token_hash = existing_verification.hash_token(new_token)
                    
                    db.commit()
                    
                    # Log the verification creation
                    self._log_verification_event(
                        db, user_id, 'verification_created', 
                        {'verification_type': verification_type, 'email': email}, True
                    )
                    
                    return existing_verification, new_token
                else:
                    # Create new verification record
                    verification, token = EmailVerification.create_verification(
                        user_id=user_id,
                        email=email,
                        verification_type=verification_type,
                        old_email=old_email,
                        expires_in_hours=self.verification_expiry_hours
                    )
                    
                    verification.ip_address = ip_address
                    verification.user_agent = user_agent
                    
                    db.add(verification)
                    db.commit()
                    
                    # Log the verification creation
                    self._log_verification_event(
                        db, user_id, 'verification_created', 
                        {'verification_type': verification_type, 'email': email}, True
                    )
                    
                    return verification, token
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error creating verification for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating verification for user {user_id}: {e}")
            raise
    
    def verify_email(self, token: str, user_id: int = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Verify an email using the provided token
        
        Args:
            token: Verification token
            user_id: Optional user ID for additional validation
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            with get_db_session() as db:
                # Find verification record by token hash
                token_hash = EmailVerification.hash_token_static(token)
                verification = db.query(EmailVerification).filter(
                    EmailVerification.verification_token_hash == token_hash
                ).first()
                
                if not verification:
                    self._log_verification_event(
                        db, user_id, 'verification_failed', 
                        {'reason': 'invalid_token'}, False
                    )
                    return False, "Invalid or expired verification token", None
                
                # Additional user validation if user_id provided
                if user_id and verification.user_id != user_id:
                    self._log_verification_event(
                        db, verification.user_id, 'verification_failed', 
                        {'reason': 'user_mismatch'}, False
                    )
                    return False, "Verification token does not match user", None
                
                # Check if already verified
                if verification.is_verified:
                    return True, "Email already verified", self._get_user_data(db, verification.user_id)
                
                # Check if expired
                if verification.is_expired:
                    verification.record_failed_attempt()
                    db.commit()
                    
                    self._log_verification_event(
                        db, verification.user_id, 'verification_failed', 
                        {'reason': 'expired_token'}, False
                    )
                    return False, "Verification token has expired", None
                
                # Check if locked
                if verification.is_locked:
                    self._log_verification_event(
                        db, verification.user_id, 'verification_failed', 
                        {'reason': 'account_locked'}, False
                    )
                    return False, "Account temporarily locked due to multiple failed attempts", None
                
                # Verify the token
                if not verification.verify_token(token):
                    verification.record_failed_attempt()
                    db.commit()
                    
                    self._log_verification_event(
                        db, verification.user_id, 'verification_failed', 
                        {'reason': 'invalid_token'}, False
                    )
                    return False, "Invalid verification token", None
                
                # Mark as verified
                verification.mark_verified()
                verification.reset_failed_attempts()
                
                # Update user's email_verified status
                user = db.query(User).filter(User.id == verification.user_id).first()
                if user:
                    user.email_verified = True
                    user.updated_at = datetime.utcnow()
                
                db.commit()
                
                # Log successful verification
                self._log_verification_event(
                    db, verification.user_id, 'verification_successful', 
                    {'verification_type': verification.verification_type, 'email': verification.email}, True
                )
                
                return True, "Email verified successfully", self._get_user_data(db, verification.user_id)
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during verification: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during verification: {e}")
            raise
    
    def resend_verification(self, user_id: int, email: str = None) -> Tuple[bool, str]:
        """
        Resend verification email
        
        Args:
            user_id: User ID
            email: Optional email override
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_session() as db:
                verification = db.query(EmailVerification).filter(
                    EmailVerification.user_id == user_id
                ).first()
                
                if not verification:
                    return False, "No verification record found"
                
                if verification.is_verified:
                    return False, "Email already verified"
                
                if not verification.can_resend:
                    if verification.resend_count >= self.max_resend_attempts:
                        return False, "Maximum resend attempts reached for today"
                    else:
                        return False, "Please wait before requesting another verification email"
                
                # Generate new token and update
                new_token = verification.generate_token()
                verification.verification_token_hash = verification.hash_token(new_token)
                verification.expires_at = datetime.utcnow() + timedelta(hours=self.verification_expiry_hours)
                verification.increment_resend_count()
                
                db.commit()
                
                # Send verification email
                success = self._send_verification_email(
                    verification.email, new_token, verification.verification_type, user_id
                )
                
                if success:
                    self._log_verification_event(
                        db, user_id, 'verification_resent', 
                        {'resend_count': verification.resend_count}, True
                    )
                    return True, "Verification email sent successfully"
                else:
                    return False, "Failed to send verification email"
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error resending verification for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error resending verification for user {user_id}: {e}")
            raise
    
    def change_email_verification(self, user_id: int, new_email: str, 
                                 current_password: str) -> Tuple[bool, str]:
        """
        Initiate email change verification process
        
        Args:
            user_id: User ID
            new_email: New email address
            current_password: Current password for verification
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_session() as db:
                # Get current user
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False, "User not found"
                
                # Verify current password (you'll need to implement password verification)
                # if not user.verify_password(current_password):
                #     return False, "Current password is incorrect"
                
                # Check if new email is already in use
                existing_user = db.query(User).filter(User.email == new_email).first()
                if existing_user and existing_user.id != user_id:
                    return False, "Email address is already in use"
                
                # Create verification for email change
                verification, token = self.create_verification(
                    user_id=user_id,
                    email=new_email,
                    verification_type='email_change',
                    old_email=user.email
                )
                
                # Send verification email
                success = self._send_verification_email(
                    new_email, token, 'email_change', user_id
                )
                
                if success:
                    self._log_verification_event(
                        db, user_id, 'email_change_initiated', 
                        {'old_email': user.email, 'new_email': new_email}, True
                    )
                    return True, "Verification email sent to new address"
                else:
                    return False, "Failed to send verification email"
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error during email change verification: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during email change verification: {e}")
            raise
    
    def complete_email_change(self, token: str, user_id: int) -> Tuple[bool, str]:
        """
        Complete email change after verification
        
        Args:
            token: Verification token
            user_id: User ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_session() as db:
                # Verify the token
                success, message, user_data = self.verify_email(token, user_id)
                
                if not success:
                    return False, message
                
                # Get verification record
                verification = db.query(EmailVerification).filter(
                    EmailVerification.user_id == user_id,
                    EmailVerification.verification_type == 'email_change'
                ).first()
                
                if not verification or not verification.is_verified:
                    return False, "Email change verification not found or incomplete"
                
                # Update user's email
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    old_email = user.email
                    user.email = verification.email
                    user.updated_at = datetime.utcnow()
                    
                    db.commit()
                    
                    # Log email change
                    self._log_verification_event(
                        db, user_id, 'email_change_completed', 
                        {'old_email': old_email, 'new_email': verification.email}, True
                    )
                    
                    return True, "Email changed successfully"
                
                return False, "User not found"
                
        except SQLAlchemyError as e:
            logger.error(f"Database error completing email change: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error completing email change: {e}")
            raise
    
    def get_verification_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get current verification status for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with verification status information
        """
        try:
            with get_db_session() as db:
                verification = db.query(EmailVerification).filter(
                    EmailVerification.user_id == user_id
                ).first()
                
                if not verification:
                    return {
                        'verified': False,
                        'verification_type': None,
                        'can_resend': False,
                        'expires_at': None,
                        'resend_count': 0,
                        'remaining_attempts': 5
                    }
                
                return verification.to_dict()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting verification status: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting verification status: {e}")
            raise
    
    def cleanup_expired_verifications(self) -> int:
        """
        Clean up expired verification records
        
        Returns:
            Number of records cleaned up
        """
        try:
            with get_db_session() as db:
                expired_count = db.query(EmailVerification).filter(
                    EmailVerification.expires_at < datetime.utcnow(),
                    EmailVerification.verified_at.is_(None)
                ).delete()
                
                db.commit()
                
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired verification records")
                
                return expired_count
                
        except SQLAlchemyError as e:
            logger.error(f"Database error cleaning up expired verifications: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error cleaning up expired verifications: {e}")
            raise
    
    def _send_verification_email(self, email: str, token: str, verification_type: str, 
                                user_id: int) -> bool:
        """Send verification email using Resend service"""
        try:
            # Get user details for personalization
            with get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                user_name = user.full_name if user else "there"
            
            # Generate verification URL
            base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{base_url}/verify-email?token={token}&type={verification_type}"
            
            # Send email based on verification type
            if verification_type == 'email_change':
                subject = "Verify Your New Email Address - Mingus"
                success = self.email_service.send_email_change_verification(
                    email, user_name, verification_url
                )
            else:
                subject = "Verify Your Email Address - Mingus"
                success = self.email_service.send_verification_email(
                    email, user_name, verification_url
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending verification email to {email}: {e}")
            return False
    
    def _get_user_data(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data for response"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'email_verified': user.email_verified
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return None
    
    def _log_verification_event(self, db: Session, user_id: int, event_type: str, 
                               event_data: Dict[str, Any], success: bool) -> None:
        """Log verification events for audit purposes"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=event_type,
                details=event_data,
                ip_address=event_data.get('ip_address'),
                user_agent=event_data.get('user_agent'),
                success=success,
                timestamp=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging verification event: {e}")
            # Don't fail the main operation if logging fails
