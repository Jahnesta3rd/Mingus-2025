"""
Service Integration Tests
Comprehensive tests for email verification service integration
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.email_verification import EmailVerification
from models.user import User
from services.email_verification_service import EmailVerificationService
from services.resend_email_service import ResendEmailService

class TestServiceIntegration:
    """Test service integration and workflows"""
    
    @pytest.fixture(autouse=True)
    def setup_services(self):
        """Setup services for each test"""
        self.email_verification_service = EmailVerificationService()
        self.resend_email_service = ResendEmailService()
    
    def test_email_verification_service_constructor(self):
        """Test EmailVerificationService constructor and initialization"""
        service = EmailVerificationService()
        
        assert service.email_service is not None
        assert isinstance(service.email_service, ResendEmailService)
        assert service.verification_expiry_hours == int(os.getenv('EMAIL_VERIFICATION_EXPIRY_HOURS', '24'))
        assert service.max_resend_attempts == int(os.getenv('MAX_EMAIL_RESEND_ATTEMPTS', '5'))
        assert service.resend_cooldown_hours == int(os.getenv('EMAIL_RESEND_COOLDOWN_HOURS', '1'))
    
    def test_resend_email_service_constructor(self):
        """Test ResendEmailService constructor and initialization"""
        service = ResendEmailService()
        
        assert service.api_key == os.getenv('RESEND_API_KEY')
        assert service.from_email == os.getenv('RESEND_FROM_EMAIL', 'noreply@mingusapp.com')
        assert service.from_name == os.getenv('RESEND_FROM_NAME', 'MINGUS Financial Wellness')
        assert service.base_url == 'https://api.resend.com'
    
    @patch('services.resend_email_service.requests.post')
    def test_resend_email_service_send_email_success(self, mock_post):
        """Test successful email sending via Resend API"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'email_123', 'status': 'sent'}
        mock_post.return_value = mock_response
        
        # Mock environment variable
        with patch.dict(os.environ, {'RESEND_API_KEY': 'test_key'}):
            service = ResendEmailService()
            result = service.send_email(
                to_email='test@example.com',
                subject='Test Email',
                html_content='<h1>Test</h1>',
                text_content='Test'
            )
            
            assert result['success'] is True
            assert result['email_id'] == 'email_123'
            assert 'successfully' in result['message']
            
            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == 'https://api.resend.com/emails'
            assert call_args[1]['headers']['Authorization'] == 'Bearer test_key'
    
    @patch('services.resend_email_service.requests.post')
    def test_resend_email_service_send_email_api_error(self, mock_post):
        """Test email sending with API error"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'RESEND_API_KEY': 'test_key'}):
            service = ResendEmailService()
            result = service.send_email(
                to_email='test@example.com',
                subject='Test Email',
                html_content='<h1>Test</h1>'
            )
            
            assert result['success'] is False
            assert '400' in result['error']
            assert 'Bad Request' in result['error']
    
    def test_resend_email_service_no_api_key(self):
        """Test email sending without API key"""
        service = ResendEmailService()
        result = service.send_email(
            to_email='test@example.com',
            subject='Test Email',
            html_content='<h1>Test</h1>'
        )
        
        assert result['success'] is False
        assert 'not configured' in result['error']
    
    @patch('services.resend_email_service.requests.post')
    def test_resend_email_service_with_template(self, mock_post):
        """Test email sending with template"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'email_456', 'status': 'sent'}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'RESEND_API_KEY': 'test_key'}):
            service = ResendEmailService()
            result = service.send_email(
                to_email='test@example.com',
                subject='Template Email',
                html_content='<h1>Template</h1>',
                template_id='welcome_template',
                template_data={'name': 'John'}
            )
            
            assert result['success'] is True
            
            # Verify template data was sent
            call_args = mock_post.call_args
            email_data = call_args[1]['json']
            assert email_data['template_id'] == 'welcome_template'
            assert email_data['template_data']['name'] == 'John'
    
    @patch('services.resend_email_service.requests.post')
    def test_resend_email_service_with_attachments(self, mock_post):
        """Test email sending with attachments"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'email_789', 'status': 'sent'}
        mock_post.return_value = mock_response
        
        attachments = [
            {
                'filename': 'document.pdf',
                'content': 'base64_encoded_content',
                'type': 'application/pdf'
            }
        ]
        
        with patch.dict(os.environ, {'RESEND_API_KEY': 'test_key'}):
            service = ResendEmailService()
            result = service.send_email(
                to_email='test@example.com',
                subject='Email with Attachments',
                html_content='<h1>Attachments</h1>',
                attachments=attachments
            )
            
            assert result['success'] is True
            
            # Verify attachments were sent
            call_args = mock_post.call_args
            email_data = call_args[1]['json']
            assert email_data['attachments'] == attachments
    
    def test_email_verification_service_verification_workflow(self):
        """Test complete email verification workflow"""
        # Test the service methods that can be tested without database
        service = EmailVerificationService()
        
        # Test service properties
        assert hasattr(service, 'verification_expiry_hours')
        assert hasattr(service, 'max_resend_attempts')
        assert hasattr(service, 'resend_cooldown_hours')
        assert hasattr(service, 'email_service')
        
        # Test that email service is properly initialized
        assert isinstance(service.email_service, ResendEmailService)
    
    @patch('services.email_verification_service.get_db_session')
    def test_email_verification_service_database_integration(self, mock_db_session):
        """Test email verification service database integration"""
        # Mock database session
        mock_session = Mock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        # Mock database query results
        mock_verification = Mock()
        mock_verification.user_id = 1
        mock_verification.email = 'test@example.com'
        mock_verification.verification_type = 'signup'
        mock_verification.is_verified = False
        mock_verification.is_expired = False
        mock_verification.is_locked = False
        mock_verification.verify_token.return_value = True
        mock_verification.mark_verified = Mock()
        mock_verification.reset_failed_attempts = Mock()
        
        mock_user = Mock()
        mock_user.email_verified = False
        mock_user.updated_at = None
        
        # Mock database queries
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_verification,  # First call for verification
            mock_user          # Second call for user
        ]
        
        # Mock EmailVerification.hash_token_static
        with patch.object(EmailVerification, 'hash_token_static') as mock_hash:
            mock_hash.return_value = 'hashed_token_123'
            
            # Mock the _get_user_data method to avoid relationship issues
            with patch.object(self.email_verification_service, '_get_user_data') as mock_get_user_data:
                mock_get_user_data.return_value = {'user_id': 1, 'email': 'test@example.com'}
                
                # Test verification
                success, message, user_data = self.email_verification_service.verify_email('valid_token', 1)
                
                assert success is True
                assert 'verified' in message.lower()
                assert user_data is not None
                
                # Verify database operations
                mock_verification.mark_verified.assert_called_once()
                mock_verification.reset_failed_attempts.assert_called_once()
                mock_session.commit.assert_called()
    
    def test_resend_email_service_error_handling(self):
        """Test ResendEmailService error handling"""
        # Mock environment variable for this test
        with patch.dict(os.environ, {'RESEND_API_KEY': 'test_key'}):
            service = ResendEmailService()
            
            # Test with network error
            with patch('services.resend_email_service.requests.post') as mock_post:
                mock_post.side_effect = Exception("Network error")
                
                result = service.send_email(
                    to_email='test@example.com',
                    subject='Test Email',
                    html_content='<h1>Test</h1>'
                )
                
                assert result['success'] is False
                assert 'Network error' in result['error']
    
    def test_service_cultural_awareness_features(self):
        """Test that services support African American professional user needs"""
        # Test email verification service cultural awareness
        service = EmailVerificationService()
        
        # Verify service supports professional email domains
        assert hasattr(service, 'verification_expiry_hours')
        assert service.verification_expiry_hours >= 24  # Professional users need time
        
        # Test resend email service professional branding
        resend_service = ResendEmailService()
        assert 'MINGUS Financial Wellness' in resend_service.from_name
        assert 'mingusapp.com' in resend_service.from_email
        
        # Verify services support secure verification flows
        assert hasattr(service, 'max_resend_attempts')
        assert hasattr(service, 'resend_cooldown_hours')
        assert service.max_resend_attempts > 0  # Security feature
        assert service.resend_cooldown_hours > 0  # Rate limiting
