"""
Test Email Verification Service
Test-compatible version of the email verification service
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.email_verification import EmailVerification
from models.user import User

class TestEmailVerificationService:
    """Test-compatible email verification service"""
    
    def __init__(self):
        self.verification_expiry_hours = int(os.getenv('EMAIL_VERIFICATION_EXPIRY_HOURS', '24'))
        self.max_resend_attempts = int(os.getenv('MAX_EMAIL_RESEND_ATTEMPTS', '5'))
        self.resend_cooldown_hours = int(os.getenv('EMAIL_RESEND_COOLDOWN_HOURS', '1'))
        
    def create_verification(self, user_id: int, email: str, verification_type: str = 'signup',
                           old_email: str = None, ip_address: str = None, 
                           user_agent: str = None) -> Tuple[EmailVerification, str]:
        """Create a new email verification record for testing"""
        try:
            # Create verification record directly
            verification, token = EmailVerification.create_verification(
                user_id=user_id,
                email=email,
                verification_type=verification_type,
                old_email=old_email,
                expires_in_hours=self.verification_expiry_hours
            )
            
            verification.ip_address = ip_address
            verification.user_agent = user_agent
            
            return verification, token
                    
        except Exception as e:
            raise Exception(f"Error creating verification: {e}")
    
    def verify_email(self, token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Verify email with token for testing"""
        try:
            # For testing, we'll simulate verification
            # In a real implementation, this would query the database
            return True, "Email verified successfully", {
                'user_id': 1,
                'email': 'test@example.com',
                'verified_at': datetime.utcnow()
            }
        except Exception as e:
            return False, f"Verification failed: {e}", None
    
    def get_verification_status(self, user_id: int) -> Dict[str, Any]:
        """Get verification status for testing"""
        return {
            'user_id': user_id,
            'is_verified': True,
            'verification_type': 'signup',
            'verified_at': datetime.utcnow().isoformat()
        }
    
    def change_email_verification(self, user_id: int, new_email: str, 
                                 current_password: str) -> Tuple[bool, str]:
        """Initiate email change verification for testing"""
        try:
            # Simulate email change verification
            return True, "Email change verification initiated"
        except Exception as e:
            return False, f"Email change verification failed: {e}"
    
    def complete_email_change(self, token: str, user_id: int) -> Tuple[bool, str]:
        """Complete email change for testing"""
        try:
            # Simulate email change completion
            return True, "Email changed successfully"
        except Exception as e:
            return False, f"Email change failed: {e}"

    def _complete_email_change(self, token: str, user_id: int) -> Tuple[bool, str]:
        """Helper method to complete email change for testing"""
        try:
            # Simulate email change completion
            return True, "Email changed successfully"
        except Exception as e:
            return False, f"Email change failed: {e}"
    
    def _get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Helper method to get user data for testing"""
        return {
            'user_id': user_id,
            'email': 'test@example.com',
            'verified_at': datetime.utcnow().isoformat()
        }
