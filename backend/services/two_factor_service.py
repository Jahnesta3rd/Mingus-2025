"""
Two-Factor Authentication Service for MINGUS
Handles TOTP setup, verification, backup codes, and SMS fallback
"""

import logging
import secrets
import hashlib
import base64
import pyotp
import qrcode
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from backend.models.two_factor_auth import (
    TwoFactorAuth, 
    TwoFactorBackupCode, 
    TwoFactorVerificationAttempt,
    TwoFactorRecoveryRequest
)
from backend.models.user import User
from backend.security.encryption_service import get_encryption_service
from backend.security.audit_logging import AuditLoggingService
from backend.services.twilio_sms_service import TwilioSMSService
from backend.services.resend_email_service import ResendEmailService

logger = logging.getLogger(__name__)

class TwoFactorService:
    """Service class for two-factor authentication operations"""
    
    def __init__(self, session_factory):
        """Initialize TwoFactorService with a session factory"""
        self.SessionLocal = session_factory
        self.encryption_service = get_encryption_service()
        self.audit_service = AuditLoggingService()
        self.sms_service = TwilioSMSService()
        self.email_service = ResendEmailService()
        
        # 2FA Configuration
        self.totp_algorithm = 'SHA1'
        self.totp_digits = 6
        self.totp_period = 30
        self.backup_code_count = 10
        self.backup_code_length = 8
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.recovery_code_expiry = timedelta(hours=24)
    
    def _get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def _generate_totp_secret(self) -> str:
        """Generate a cryptographically secure TOTP secret"""
        return pyotp.random_base32()
    
    def _encrypt_totp_secret(self, secret: str) -> str:
        """Encrypt TOTP secret using encryption service"""
        return self.encryption_service.encrypt_field(secret, '2fa_secret')
    
    def _decrypt_totp_secret(self, encrypted_secret: str) -> str:
        """Decrypt TOTP secret using encryption service"""
        return self.encryption_service.decrypt_field(encrypted_secret, '2fa_secret')
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate backup codes for 2FA recovery"""
        codes = []
        for _ in range(self.backup_code_count):
            # Generate secure random code
            code = secrets.token_hex(self.backup_code_length // 2).upper()
            # Format as groups of 4 for readability
            formatted_code = '-'.join([code[i:i+4] for i in range(0, len(code), 4)])
            codes.append(formatted_code)
        return codes
    
    def _hash_backup_code(self, code: str) -> str:
        """Hash backup code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def _verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """Verify backup code against hash"""
        return hashlib.sha256(code.encode()).hexdigest() == hashed_code
    
    def _generate_qr_code(self, totp_uri: str) -> bytes:
        """Generate QR code for TOTP setup"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return img_byte_arr
    
    def _get_client_info(self, request) -> Dict[str, str]:
        """Extract client information from request"""
        return {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'country_code': request.headers.get('CF-IPCountry', ''),
            'city': request.headers.get('CF-IPCity', ''),
            'timezone': request.headers.get('CF-Timezone', '')
        }
    
    def setup_2fa(self, user_id: int, request) -> Dict[str, Any]:
        """
        Set up two-factor authentication for a user
        
        Args:
            user_id: User ID
            request: Flask request object
            
        Returns:
            Dictionary with setup information
        """
        try:
            session = self._get_session()
            
            # Check if user already has 2FA
            existing_2fa = session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
            if existing_2fa and existing_2fa.is_enabled:
                return {
                    'success': False,
                    'error': 'Two-factor authentication is already enabled'
                }
            
            # Generate TOTP secret
            totp_secret = self._generate_totp_secret()
            encrypted_secret = self._encrypt_totp_secret(totp_secret)
            
            # Create TOTP object
            totp = pyotp.TOTP(
                totp_secret,
                digits=self.totp_digits,
                interval=self.totp_period,
                algorithm=getattr(pyotp.algorithms, self.totp_algorithm)
            )
            
            # Generate provisioning URI
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            totp_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name="MINGUS Financial Wellness"
            )
            
            # Generate QR code
            qr_code = self._generate_qr_code(totp_uri)
            qr_code_b64 = base64.b64encode(qr_code).decode('utf-8')
            
            # Generate backup codes
            backup_codes = self._generate_backup_codes()
            
            # Create or update 2FA record
            if existing_2fa:
                existing_2fa.encrypted_totp_secret = encrypted_secret
                existing_2fa.totp_algorithm = self.totp_algorithm
                existing_2fa.totp_digits = self.totp_digits
                existing_2fa.totp_period = self.totp_period
                existing_2fa.is_enabled = False  # Not enabled until verified
                existing_2fa.is_verified = False
                two_factor_auth = existing_2fa
            else:
                two_factor_auth = TwoFactorAuth(
                    user_id=user_id,
                    encrypted_totp_secret=encrypted_secret,
                    totp_algorithm=self.totp_algorithm,
                    totp_digits=self.totp_digits,
                    totp_period=self.totp_period,
                    is_enabled=False,
                    is_verified=False
                )
                session.add(two_factor_auth)
            
            # Clear existing backup codes
            session.query(TwoFactorBackupCode).filter_by(
                two_factor_auth_id=two_factor_auth.id
            ).delete()
            
            # Create new backup codes
            for code in backup_codes:
                hashed_code = self._hash_backup_code(code)
                backup_code = TwoFactorBackupCode(
                    two_factor_auth_id=two_factor_auth.id,
                    encrypted_code_hash=hashed_code
                )
                session.add(backup_code)
            
            session.commit()
            
            # Log setup attempt
            self._log_verification_attempt(
                session, two_factor_auth.id, 'setup', True, request
            )
            
            return {
                'success': True,
                'totp_secret': totp_secret,  # Only for initial setup
                'qr_code': qr_code_b64,
                'backup_codes': backup_codes,
                'totp_uri': totp_uri,
                'message': 'Two-factor authentication setup completed. Please verify with a TOTP code.'
            }
            
        except Exception as e:
            logger.error(f"Error setting up 2FA for user {user_id}: {e}")
            if 'session' in locals():
                session.rollback()
            return {
                'success': False,
                'error': 'Failed to set up two-factor authentication'
            }
        finally:
            if 'session' in locals():
                session.close()
    
    def verify_totp(self, user_id: int, totp_code: str, request) -> Dict[str, Any]:
        """
        Verify TOTP code for 2FA setup or login
        
        Args:
            user_id: User ID
            totp_code: TOTP code from authenticator app
            request: Flask request object
            
        Returns:
            Dictionary with verification result
        """
        try:
            session = self._get_session()
            
            # Get 2FA configuration
            two_factor_auth = session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
            if not two_factor_auth:
                return {
                    'success': False,
                    'error': 'Two-factor authentication not set up'
                }
            
            # Check if account is locked out
            if two_factor_auth.is_locked_out():
                return {
                    'success': False,
                    'error': 'Account temporarily locked due to too many failed attempts',
                    'lockout_until': two_factor_auth.lockout_until.isoformat()
                }
            
            # Decrypt TOTP secret
            try:
                totp_secret = self._decrypt_totp_secret(two_factor_auth.encrypted_totp_secret)
            except Exception as e:
                logger.error(f"Error decrypting TOTP secret for user {user_id}: {e}")
                return {
                    'success': False,
                    'error': 'Authentication error'
                }
            
            # Create TOTP object
            totp = pyotp.TOTP(
                totp_secret,
                digits=two_factor_auth.totp_digits,
                interval=two_factor_auth.totp_period,
                algorithm=getattr(pyotp.algorithms, two_factor_auth.totp_algorithm)
            )
            
            # Verify TOTP code
            if totp.verify(totp_code):
                # Success - enable 2FA if this is setup verification
                if not two_factor_auth.is_enabled:
                    two_factor_auth.is_enabled = True
                    two_factor_auth.setup_completed_at = datetime.utcnow()
                
                two_factor_auth.is_verified = True
                two_factor_auth.last_used_at = datetime.utcnow()
                two_factor_auth.reset_failed_attempts()
                
                session.commit()
                
                # Log successful verification
                self._log_verification_attempt(
                    session, two_factor_auth.id, 'totp', True, request
                )
                
                return {
                    'success': True,
                    'message': 'Two-factor authentication verified successfully',
                    'is_enabled': two_factor_auth.is_enabled
                }
            else:
                # Failed verification
                self._handle_failed_attempt(session, two_factor_auth, request)
                
                return {
                    'success': False,
                    'error': 'Invalid authentication code',
                    'remaining_attempts': self.max_failed_attempts - self._get_failed_attempts(session, two_factor_auth.id)
                }
                
        except Exception as e:
            logger.error(f"Error verifying TOTP for user {user_id}: {e}")
            if 'session' in locals():
                session.rollback()
            return {
                'success': False,
                'error': 'Authentication error'
            }
        finally:
            if 'session' in locals():
                session.close()
    
    def verify_backup_code(self, user_id: int, backup_code: str, request) -> Dict[str, Any]:
        """
        Verify backup code for 2FA recovery
        
        Args:
            user_id: User ID
            backup_code: Backup code from user
            request: Flask request object
            
        Returns:
            Dictionary with verification result
        """
        try:
            session = self._get_session()
            
            # Get 2FA configuration
            two_factor_auth = session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
            if not two_factor_auth:
                return {
                    'success': False,
                    'error': 'Two-factor authentication not set up'
                }
            
            # Check if account is locked out
            if two_factor_auth.is_locked_out():
                return {
                    'success': False,
                    'error': 'Account temporarily locked due to too many failed attempts'
                }
            
            # Find unused backup code
            backup_code_record = session.query(TwoFactorBackupCode).filter_by(
                two_factor_auth_id=two_factor_auth.id,
                is_used=False
            ).first()
            
            if not backup_code_record:
                return {
                    'success': False,
                    'error': 'No backup codes available'
                }
            
            # Verify backup code
            if self._verify_backup_code(backup_code, backup_code_record.encrypted_code_hash):
                # Mark backup code as used
                client_info = self._get_client_info(request)
                backup_code_record.mark_as_used(
                    ip_address=client_info['ip_address'],
                    user_agent=client_info['user_agent']
                )
                
                # Mark 2FA as verified
                two_factor_auth.is_verified = True
                two_factor_auth.last_used_at = datetime.utcnow()
                two_factor_auth.reset_failed_attempts()
                
                session.commit()
                
                # Log successful verification
                self._log_verification_attempt(
                    session, two_factor_auth.id, 'backup_code', True, request
                )
                
                return {
                    'success': True,
                    'message': 'Backup code verified successfully',
                    'is_enabled': two_factor_auth.is_enabled
                }
            else:
                # Failed verification
                self._handle_failed_attempt(session, two_factor_auth, request)
                
                return {
                    'success': False,
                    'error': 'Invalid backup code',
                    'remaining_attempts': self.max_failed_attempts - self._get_failed_attempts(session, two_factor_auth.id)
                }
                
        except Exception as e:
            logger.error(f"Error verifying backup code for user {user_id}: {e}")
            if 'session' in locals():
                session.rollback()
            return {
                'success': False,
                'error': 'Authentication error'
            }
        finally:
            if 'session' in locals():
                session.close()
    
    def send_sms_fallback(self, user_id: int, request) -> Dict[str, Any]:
        """
        Send SMS fallback code for 2FA
        
        Args:
            user_id: User ID
            request: Flask request object
            
        Returns:
            Dictionary with SMS result
        """
        try:
            session = self._get_session()
            
            # Get user and 2FA configuration
            user = session.query(User).filter_by(id=user_id).first()
            if not user or not user.phone_number:
                return {
                    'success': False,
                    'error': 'Phone number not available for SMS fallback'
                }
            
            two_factor_auth = session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
            if not two_factor_auth:
                return {
                    'success': False,
                    'error': 'Two-factor authentication not set up'
                }
            
            # Generate SMS code
            sms_code = ''.join([secrets.choice('0123456789') for _ in range(6)])
            encrypted_sms_code = self.encryption_service.encrypt_field(sms_code, '2fa_sms')
            
            # Store SMS code
            two_factor_auth.encrypted_sms_secret = encrypted_sms_code
            two_factor_auth.sms_fallback_enabled = True
            
            session.commit()
            
            # Send SMS
            sms_result = self.sms_service.send_2fa_code(
                phone_number=user.phone_number,
                code=sms_code,
                user_name=user.full_name
            )
            
            if sms_result['success']:
                return {
                    'success': True,
                    'message': 'SMS code sent successfully',
                    'phone_number': user.phone_number[-4:]  # Show last 4 digits only
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send SMS code',
                    'details': sms_result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error sending SMS fallback for user {user_id}: {e}")
            if 'session' in locals():
                session.rollback()
            return {
                'success': False,
                'error': 'Failed to send SMS fallback'
            }
        finally:
            if 'session' in locals():
                session.close()
    
    def verify_sms_code(self, user_id: int, sms_code: str, request) -> Dict[str, Any]:
        """
        Verify SMS fallback code
        
        Args:
            user_id: User ID
            sms_code: SMS code from user
            request: Flask request object
            
        Returns:
            Dictionary with verification result
        """
        try:
            session = self._get_session()
            
            # Get 2FA configuration
            two_factor_auth = session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
            if not two_factor_auth:
                return {
                    'success': False,
                    'error': 'Two-factor authentication not set up'
                }
            
            # Check if account is locked out
            if two_factor_auth.is_locked_out():
                return {
                    'success': False,
                    'error': 'Account temporarily locked due to too many failed attempts'
                }
            
            # Decrypt SMS code
            try:
                stored_sms_code = self.encryption_service.decrypt_field(
                    two_factor_auth.encrypted_sms_secret, '2fa_sms'
                )
            except Exception as e:
                logger.error(f"Error decrypting SMS code for user {user_id}: {e}")
                return {
                    'success': False,
                    'error': 'Authentication error'
                }
            
            # Verify SMS code
            if sms_code == stored_sms_code:
                # Success
                two_factor_auth.is_verified = True
                two_factor_auth.last_used_at = datetime.utcnow()
                two_factor_auth.reset_failed_attempts()
                
                # Clear SMS code after use
                two_factor_auth.encrypted_sms_secret = None
                
                session.commit()
                
                # Log successful verification
                self._log_verification_attempt(
                    session, two_factor_auth.id, 'sms', True, request
                )
                
                return {
                    'success': True,
                    'message': 'SMS code verified successfully',
                    'is_enabled': two_factor_auth.is_enabled
                }
            else:
                # Failed verification
                self._handle_failed_attempt(session, two_factor_auth, request)
                
                return {
                    'success': False,
                    'error': 'Invalid SMS code',
                    'remaining_attempts': self.max_failed_attempts - self._get_failed_attempts(session, two_factor_auth.id)
                }
                
        except Exception as e:
            logger.error(f"Error verifying SMS code for user {user_id}: {e}")
            if 'session' in locals():
                session.rollback()
            return {
                'success': False,
                'error': 'Authentication error'
            }
        finally:
            if 'session' in locals():
                session.close()
    
    def disable_2fa(self, user_id: int, request) -> Dict[str, Any]:
        """
        Disable two-factor authentication for a user
        
        Args:
            user_id: User ID
            request: Flask request object
            
        Returns:
            Dictionary with result
        """
        try:
            session = self._get_session()
            
            # Get 2FA configuration
            two_factor_auth = session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
            if not two_factor_auth:
                return {
                    'success': False,
                    'error': 'Two-factor authentication not set up'
                }
            
            # Disable 2FA
            two_factor_auth.is_enabled = False
            two_factor_auth.is_verified = False
            two_factor_auth.setup_completed_at = None
            two_factor_auth.sms_fallback_enabled = False
            two_factor_auth.encrypted_sms_secret = None
            
            # Clear backup codes
            session.query(TwoFactorBackupCode).filter_by(
                two_factor_auth_id=two_factor_auth.id
            ).delete()
            
            session.commit()
            
            # Log disable action
            self._log_verification_attempt(
                session, two_factor_auth.id, 'disable', True, request
            )
            
            return {
                'success': True,
                'message': 'Two-factor authentication disabled successfully'
            }
            
        except Exception as e:
            logger.error(f"Error disabling 2FA for user {user_id}: {e}")
            if 'session' in locals():
                session.rollback()
            return {
                'success': False,
                'error': 'Failed to disable two-factor authentication'
            }
        finally:
            if 'session' in locals():
                session.close()
    
    def get_2fa_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get 2FA status for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with 2FA status
        """
        try:
            session = self._get_session()
            
            two_factor_auth = session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
            if not two_factor_auth:
                return {
                    'enabled': False,
                    'setup_completed': False,
                    'sms_fallback': False,
                    'backup_codes_remaining': 0
                }
            
            # Count unused backup codes
            backup_codes_remaining = session.query(TwoFactorBackupCode).filter_by(
                two_factor_auth_id=two_factor_auth.id,
                is_used=False
            ).count()
            
            return {
                'enabled': two_factor_auth.is_enabled,
                'setup_completed': two_factor_auth.setup_completed_at is not None,
                'sms_fallback': two_factor_auth.sms_fallback_enabled,
                'backup_codes_remaining': backup_codes_remaining,
                'last_used': two_factor_auth.last_used_at.isoformat() if two_factor_auth.last_used_at else None,
                'is_locked_out': two_factor_auth.is_locked_out()
            }
            
        except Exception as e:
            logger.error(f"Error getting 2FA status for user {user_id}: {e}")
            return {
                'enabled': False,
                'setup_completed': False,
                'sms_fallback': False,
                'backup_codes_remaining': 0,
                'error': 'Failed to get 2FA status'
            }
        finally:
            if 'session' in locals():
                session.close()
    
    def _handle_failed_attempt(self, session: Session, two_factor_auth: TwoFactorAuth, request) -> None:
        """Handle failed verification attempt"""
        # Log failed attempt
        self._log_verification_attempt(
            session, two_factor_auth.id, 'totp', False, request
        )
        
        # Check if we should lock out account
        failed_attempts = self._get_failed_attempts(session, two_factor_auth.id)
        if failed_attempts >= self.max_failed_attempts:
            two_factor_auth.lockout_until = datetime.utcnow() + self.lockout_duration
            logger.warning(f"Account locked for user {two_factor_auth.user_id} due to too many failed 2FA attempts")
        
        session.commit()
    
    def _get_failed_attempts(self, session: Session, two_factor_auth_id: int) -> int:
        """Get count of recent failed attempts"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
        return session.query(TwoFactorVerificationAttempt).filter(
            TwoFactorVerificationAttempt.two_factor_auth_id == two_factor_auth_id,
            TwoFactorVerificationAttempt.success == False,
            TwoFactorVerificationAttempt.attempted_at > cutoff_time
        ).count()
    
    def _log_verification_attempt(
        self, 
        session: Session, 
        two_factor_auth_id: int, 
        attempt_type: str, 
        success: bool, 
        request
    ) -> None:
        """Log verification attempt for audit purposes"""
        try:
            client_info = self._get_client_info(request)
            
            verification_attempt = TwoFactorVerificationAttempt(
                two_factor_auth_id=two_factor_auth_id,
                attempt_type=attempt_type,
                success=success,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent'],
                country_code=client_info['country_code'],
                city=client_info['city'],
                timezone=client_info['timezone']
            )
            
            session.add(verification_attempt)
            session.commit()
            
        except Exception as e:
            logger.error(f"Error logging verification attempt: {e}")
            session.rollback()
