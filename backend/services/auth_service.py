"""
Authentication Service for MINGUS
Handles email verification, password reset, and token management
"""

import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from backend.models.user import User
from backend.models.auth_tokens import AuthToken
from backend.models.email_verification import EmailVerification
from backend.services.resend_email_service import resend_email_service

logger = logging.getLogger(__name__)

class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, session_factory):
        """Initialize AuthService with a session factory"""
        self.SessionLocal = session_factory
        
        # Token configuration
        self.verification_token_expiry = timedelta(hours=24)  # 24 hours
        self.password_reset_token_expiry = timedelta(hours=1)  # 1 hour
        self.max_resend_attempts = 5
        
    def _get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def _generate_secure_token(self) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(32)
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _validate_token_format(self, token: str) -> bool:
        """Validate token format"""
        if not token or len(token) < 32:
            return False
        return True
    
    def create_email_verification(self, user_id: int, email: str, ip_address: str = None, user_agent: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Create email verification for user
        
        Args:
            user_id: User ID
            email: User's email address
            ip_address: IP address of request
            user_agent: User agent of request
            
        Returns:
            Tuple of (success, message, token)
        """
        try:
            session = self._get_session()
            
            try:
                # Check if verification already exists
                existing_verification = session.query(EmailVerification).filter_by(
                    user_id=user_id
                ).first()
                
                if existing_verification:
                    # Check if we can resend
                    if not existing_verification.can_resend():
                        return False, "Please wait before requesting another verification email", None
                    
                    # Check resend limit
                    if existing_verification.resend_count >= self.max_resend_attempts:
                        return False, "Maximum resend attempts reached. Please contact support.", None
                    
                    # Update existing verification
                    token = self._generate_secure_token()
                    token_hash = self._hash_token(token)
                    
                    existing_verification.verification_token_hash = token_hash
                    existing_verification.expires_at = datetime.utcnow() + self.verification_token_expiry
                    existing_verification.increment_resend_count()
                    
                    session.commit()
                    
                    logger.info(f"Email verification resent for user {user_id}")
                    return True, "Verification email resent successfully", token
                
                # Create new verification
                token = self._generate_secure_token()
                token_hash = self._hash_token(token)
                
                new_verification = EmailVerification(
                    user_id=user_id,
                    email=email,
                    verification_token_hash=token_hash,
                    expires_at=datetime.utcnow() + self.verification_token_expiry
                )
                
                session.add(new_verification)
                session.commit()
                
                logger.info(f"Email verification created for user {user_id}")
                return True, "Verification email sent successfully", token
                
            except IntegrityError as e:
                session.rollback()
                logger.error(f"Integrity error creating email verification: {str(e)}")
                return False, "Failed to create verification", None
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error creating email verification: {str(e)}")
                return False, "Database error", None
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error creating email verification: {str(e)}")
            return False, "Unexpected error", None
    
    def verify_email(self, token: str) -> Tuple[bool, str, Optional[int]]:
        """
        Verify user email with token
        
        Args:
            token: Verification token
            
        Returns:
            Tuple of (success, message, user_id)
        """
        try:
            if not self._validate_token_format(token):
                return False, "Invalid token format", None
            
            token_hash = self._hash_token(token)
            session = self._get_session()
            
            try:
                # Find verification record
                verification = session.query(EmailVerification).filter_by(
                    verification_token_hash=token_hash
                ).first()
                
                if not verification:
                    return False, "Invalid verification token", None
                
                if verification.is_expired():
                    return False, "Verification token has expired", None
                
                if verification.is_verified():
                    return False, "Email already verified", None
                
                # Mark email as verified
                verification.mark_verified()
                
                # Update user email_verified status
                user = session.query(User).filter_by(id=verification.user_id).first()
                if user:
                    user.email_verified = True
                    user.updated_at = datetime.utcnow()
                
                session.commit()
                
                logger.info(f"Email verified for user {verification.user_id}")
                return True, "Email verified successfully", verification.user_id
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error verifying email: {str(e)}")
                return False, "Database error", None
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error verifying email: {str(e)}")
            return False, "Unexpected error", None
    
    def resend_verification_email(self, email: str, ip_address: str = None, user_agent: str = None) -> Tuple[bool, str]:
        """
        Resend verification email
        
        Args:
            email: User's email address
            ip_address: IP address of request
            user_agent: User agent of request
            
        Returns:
            Tuple of (success, message)
        """
        try:
            session = self._get_session()
            
            try:
                # Find user by email
                user = session.query(User).filter_by(email=email.lower()).first()
                if not user:
                    # Don't reveal if user exists or not
                    return True, "If the email exists, a verification email has been sent"
                
                # Check if email is already verified
                if user.email_verified:
                    return False, "Email is already verified"
                
                # Create or update verification
                success, message, token = self.create_email_verification(
                    user.id, user.email, ip_address, user_agent
                )
                
                if success and token:
                    # Send verification email
                    email_result = resend_email_service.send_verification_email(user.email, token)
                    if email_result['success']:
                        logger.info(f"Verification email resent to {email}")
                        return True, "Verification email sent successfully"
                    else:
                        logger.error(f"Failed to send verification email: {email_result.get('error')}")
                        return False, "Failed to send verification email"
                else:
                    return False, message
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error resending verification: {str(e)}")
            return False, "Unexpected error"
    
    def create_password_reset_token(self, email: str, ip_address: str = None, user_agent: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Create password reset token
        
        Args:
            email: User's email address
            ip_address: IP address of request
            user_agent: User agent of request
            
        Returns:
            Tuple of (success, message, token)
        """
        try:
            session = self._get_session()
            
            try:
                # Find user by email
                user = session.query(User).filter_by(email=email.lower()).first()
                if not user:
                    # Don't reveal if user exists or not
                    return True, "If the email exists, a password reset email has been sent", None
                
                # Check if user is active
                if not user.is_active:
                    return False, "Account is not active", None
                
                # Check for existing unused tokens
                existing_token = session.query(AuthToken).filter(
                    AuthToken.user_id == user.id,
                    AuthToken.token_type == 'password_reset',
                    AuthToken.used_at.is_(None),
                    AuthToken.expires_at > datetime.utcnow()
                ).first()
                
                if existing_token:
                    return False, "Password reset already requested. Please check your email.", None
                
                # Create new token
                token = self._generate_secure_token()
                token_hash = self._hash_token(token)
                
                new_token = AuthToken(
                    token_hash=token_hash,
                    user_id=user.id,
                    token_type='password_reset',
                    expires_at=datetime.utcnow() + self.password_reset_token_expiry,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                session.add(new_token)
                session.commit()
                
                logger.info(f"Password reset token created for user {user.id}")
                return True, "Password reset email sent successfully", token
                
            except IntegrityError as e:
                session.rollback()
                logger.error(f"Integrity error creating password reset token: {str(e)}")
                return False, "Failed to create reset token", None
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error creating password reset token: {str(e)}")
                return False, "Database error", None
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error creating password reset token: {str(e)}")
            return False, "Unexpected error", None
    
    def validate_password_reset_token(self, token: str) -> Tuple[bool, str, Optional[int]]:
        """
        Validate password reset token
        
        Args:
            token: Reset token
            
        Returns:
            Tuple of (success, message, user_id)
        """
        try:
            if not self._validate_token_format(token):
                return False, "Invalid token format", None
            
            token_hash = self._hash_token(token)
            session = self._get_session()
            
            try:
                # Find token
                auth_token = session.query(AuthToken).filter_by(
                    token_hash=token_hash,
                    token_type='password_reset'
                ).first()
                
                if not auth_token:
                    return False, "Invalid reset token", None
                
                if auth_token.is_expired():
                    return False, "Reset token has expired", None
                
                if auth_token.is_used():
                    return False, "Reset token has already been used", None
                
                # Check if user is still active
                user = session.query(User).filter_by(id=auth_token.user_id).first()
                if not user or not user.is_active:
                    return False, "User account not found or inactive", None
                
                logger.info(f"Password reset token validated for user {auth_token.user_id}")
                return True, "Token is valid", auth_token.user_id
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error validating reset token: {str(e)}")
            return False, "Unexpected error", None
    
    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user password with token
        
        Args:
            token: Reset token
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self._validate_token_format(token):
                return False, "Invalid token format"
            
            token_hash = self._hash_token(token)
            session = self._get_session()
            
            try:
                # Find token
                auth_token = session.query(AuthToken).filter_by(
                    token_hash=token_hash,
                    token_type='password_reset'
                ).first()
                
                if not auth_token:
                    return False, "Invalid reset token"
                
                if auth_token.is_expired():
                    return False, "Reset token has expired"
                
                if auth_token.is_used():
                    return False, "Reset token has already been used"
                
                # Check if user is still active
                user = session.query(User).filter_by(id=auth_token.user_id).first()
                if not user or not user.is_active:
                    return False, "User account not found or inactive"
                
                # Validate new password
                if len(new_password) < 8:
                    return False, "Password must be at least 8 characters long"
                
                # Hash new password
                password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
                
                # Update user password
                user.password_hash = password_hash
                user.updated_at = datetime.utcnow()
                
                # Mark token as used
                auth_token.mark_used()
                
                session.commit()
                
                logger.info(f"Password reset successfully for user {user.id}")
                return True, "Password reset successfully"
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error resetting password: {str(e)}")
                return False, "Database error"
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error resetting password: {str(e)}")
            return False, "Unexpected error"
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            session = self._get_session()
            cleaned_count = 0
            
            try:
                # Clean up expired auth tokens
                expired_auth_tokens = session.query(AuthToken).filter(
                    AuthToken.expires_at < datetime.utcnow()
                ).all()
                
                for token in expired_auth_tokens:
                    session.delete(token)
                    cleaned_count += 1
                
                # Clean up expired email verifications
                expired_verifications = session.query(EmailVerification).filter(
                    EmailVerification.expires_at < datetime.utcnow()
                ).all()
                
                for verification in expired_verifications:
                    session.delete(verification)
                    cleaned_count += 1
                
                session.commit()
                
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} expired tokens")
                
                return cleaned_count
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error cleaning up tokens: {str(e)}")
                return 0
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error cleaning up tokens: {str(e)}")
            return 0
    
    def get_user_verification_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's email verification status
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with verification status
        """
        try:
            session = self._get_session()
            
            try:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return {'error': 'User not found'}
                
                verification = session.query(EmailVerification).filter_by(user_id=user_id).first()
                
                return {
                    'user_id': user.id,
                    'email': user.email,
                    'email_verified': user.email_verified,
                    'verification_status': {
                        'has_verification': verification is not None,
                        'is_expired': verification.is_expired() if verification else None,
                        'can_resend': verification.can_resend() if verification else None,
                        'resend_count': verification.resend_count if verification else 0,
                        'max_resend_attempts': self.max_resend_attempts
                    } if verification else None
                }
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error getting verification status: {str(e)}")
            return {'error': 'Unexpected error'}
