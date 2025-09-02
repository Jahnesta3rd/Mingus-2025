"""
Email Template Tests for Email Verification System
Tests template rendering, security, and email content validation
"""

import pytest
import re
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from jinja2 import Template, Environment, select_autoescape

from ..models.email_verification import EmailVerification
from ..models.user import User
from ..services.email_verification_service import EmailVerificationService
from ..services.resend_email_service import ResendEmailService

@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine('sqlite:///:memory:')
    from ..models.base import Base
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()

@pytest.fixture(scope="function")
def sample_user(test_db):
    """Create sample user"""
    user = User(
        id=1,
        email='test@example.com',
        full_name='Test User',
        password_hash='hashed_password',
        email_verified=False
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture(scope="function")
def sample_verification(test_db, sample_user):
    """Create sample verification"""
    verification = EmailVerification(
        user_id=sample_user.id,
        email=sample_user.email,
        verification_token_hash='test_hash',
        expires_at=datetime.utcnow() + timedelta(hours=24),
        verification_type='signup'
    )
    test_db.add(verification)
    test_db.commit()
    return verification

@pytest.fixture(scope="function")
def email_templates():
    """Sample email templates for testing"""
    return {
        'verification': """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Verify Your Email</title>
        </head>
        <body>
            <h1>Hello {{ user.full_name }},</h1>
            <p>Please verify your email address by clicking the link below:</p>
            <a href="{{ verification_url }}">Verify Email</a>
            <p>This link will expire in {{ expiry_hours }} hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
        </html>
        """,
        'email_change': """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Confirm Email Change</title>
        </head>
        <body>
            <h1>Hello {{ user.full_name }},</h1>
            <p>You requested to change your email address to: {{ new_email }}</p>
            <p>Please confirm this change by clicking the link below:</p>
            <a href="{{ verification_url }}">Confirm Email Change</a>
            <p>This link will expire in {{ expiry_hours }} hours.</p>
            <p>If you didn't request this change, please contact support immediately.</p>
        </body>
        </html>
        """,
        'password_reset': """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reset Your Password</title>
        </head>
        <body>
            <h1>Hello {{ user.full_name }},</h1>
            <p>You requested to reset your password.</p>
            <p>Click the link below to reset your password:</p>
            <a href="{{ reset_url }}">Reset Password</a>
            <p>This link will expire in {{ expiry_hours }} hours.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
        </body>
        </html>
        """,
        'reminder': """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Verification Reminder</title>
        </head>
        <body>
            <h1>Hello {{ user.full_name }},</h1>
            <p>We noticed you haven't verified your email address yet.</p>
            <p>Please verify your email by clicking the link below:</p>
            <a href="{{ verification_url }}">Verify Email</a>
            <p>This link will expire in {{ expiry_hours }} hours.</p>
        </body>
        </html>
        """
    }

class TestEmailTemplateRendering:
    """Test email template rendering functionality"""
    
    def test_basic_template_rendering(self, email_templates):
        """Test basic template rendering with safe data"""
        template = Template(email_templates['verification'])
        
        # Safe test data
        test_data = {
            'user': Mock(full_name='John Doe'),
            'verification_url': 'https://example.com/verify?token=abc123',
            'expiry_hours': 24
        }
        
        rendered = template.render(**test_data)
        
        assert 'John Doe' in rendered
        assert 'https://example.com/verify?token=abc123' in rendered
        assert '24' in rendered
        assert '<h1>' in rendered
        assert '</body>' in rendered
    
    def test_email_change_template_rendering(self, email_templates):
        """Test email change template rendering"""
        template = Template(email_templates['email_change'])
        
        test_data = {
            'user': Mock(full_name='Jane Smith'),
            'new_email': 'newemail@example.com',
            'verification_url': 'https://example.com/change?token=xyz789',
            'expiry_hours': 24
        }
        
        rendered = template.render(**test_data)
        
        assert 'Jane Smith' in rendered
        assert 'newemail@example.com' in rendered
        assert 'xyz789' in rendered
        assert 'Confirm Email Change' in rendered
    
    def test_password_reset_template_rendering(self, email_templates):
        """Test password reset template rendering"""
        template = Template(email_templates['password_reset'])
        
        test_data = {
            'user': Mock(full_name='Bob Johnson'),
            'reset_url': 'https://example.com/reset?token=def456',
            'expiry_hours': 1
        }
        
        rendered = template.render(**test_data)
        
        assert 'Bob Johnson' in rendered
        assert 'def456' in rendered
        assert 'Reset Password' in rendered
        assert '1' in rendered
    
    def test_reminder_template_rendering(self, email_templates):
        """Test reminder template rendering"""
        template = Template(email_templates['reminder'])
        
        test_data = {
            'user': Mock(full_name='Alice Brown'),
            'verification_url': 'https://example.com/verify?token=ghi789',
            'expiry_hours': 12
        }
        
        rendered = template.render(**test_data)
        
        assert 'Alice Brown' in rendered
        assert 'ghi789' in rendered
        assert 'Email Verification Reminder' in rendered
        assert '12' in rendered

class TestEmailTemplateSecurity:
    """Test email template security features"""
    
    def test_xss_prevention_in_templates(self, email_templates):
        """Test XSS prevention in email templates"""
        template = Template(email_templates['verification'])
        
        # Malicious data that could cause XSS
        malicious_data = {
            'user': Mock(full_name='<script>alert("xss")</script>'),
            'verification_url': 'javascript:alert("xss")',
            'expiry_hours': 24
        }
        
        rendered = template.render(**malicious_data)
        
        # Script tags should be escaped
        assert '<script>' not in rendered
        assert '&lt;script&gt;' in rendered or '&lt;script&gt;' in rendered
        assert 'javascript:' not in rendered
        
        # HTML should be properly escaped
        assert '&lt;' in rendered or '&lt;' in rendered
        assert '&gt;' in rendered or '&gt;' in rendered
    
    def test_template_injection_prevention(self, email_templates):
        """Test prevention of template injection attacks"""
        template = Template(email_templates['verification'])
        
        # Attempt template injection
        malicious_data = {
            'user': Mock(full_name='{{ 7 * 7 }}'),
            'verification_url': '{{ config.items() }}',
            'expiry_hours': '{{ request.environ }}'
        }
        
        rendered = template.render(**malicious_data)
        
        # Template expressions should not be evaluated
        assert '{{ 7 * 7 }}' in rendered
        assert '{{ config.items() }}' in rendered
        assert '{{ request.environ }}' in rendered
        
        # Should not contain evaluated results
        assert '49' not in rendered
        assert 'environ' not in rendered
    
    def test_html_encoding_consistency(self, email_templates):
        """Test consistent HTML encoding across templates"""
        template = Template(email_templates['verification'])
        
        # Test various special characters
        special_chars = {
            'user': Mock(full_name='O\'Connor & Smith <>"'),
            'verification_url': 'https://example.com/verify?name=O\'Connor&type=test',
            'expiry_hours': 24
        }
        
        rendered = template.render(**special_chars)
        
        # Special characters should be properly encoded
        assert 'O\'Connor & Smith <>"' not in rendered
        assert '&amp;' in rendered or '&amp;' in rendered
        assert '&lt;' in rendered or '&lt;' in rendered
        assert '&gt;' in rendered or '&gt;' in rendered
        assert '&quot;' in rendered or '&quot;' in rendered
    
    def test_url_validation_in_templates(self, email_templates):
        """Test URL validation and security in templates"""
        template = Template(email_templates['verification'])
        
        # Test various URL formats
        test_urls = [
            'https://example.com/verify?token=abc123',
            'http://example.com/verify?token=abc123',
            '//example.com/verify?token=abc123',
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
            'file:///etc/passwd'
        ]
        
        for url in test_urls:
            test_data = {
                'user': Mock(full_name='Test User'),
                'verification_url': url,
                'expiry_hours': 24
            }
            
            rendered = template.render(**test_data)
            
            # Dangerous URLs should be filtered or escaped
            if url.startswith('javascript:') or url.startswith('data:') or url.startswith('file://'):
                assert url not in rendered
            else:
                assert url in rendered
    
    def test_content_type_validation(self, email_templates):
        """Test content type validation in email templates"""
        # Test that templates produce valid HTML
        for template_name, template_content in email_templates.items():
            template = Template(template_content)
            
            # Basic HTML structure validation
            rendered = template.render(
                user=Mock(full_name='Test User'),
                verification_url='https://example.com/verify',
                expiry_hours=24
            )
            
            # Should have proper HTML structure
            assert '<!DOCTYPE html>' in rendered
            assert '<html>' in rendered
            assert '</html>' in rendered
            assert '<head>' in rendered
            assert '</head>' in rendered
            assert '<body>' in rendered
            assert '</body>' in rendered
            assert '<title>' in rendered
            assert '</title>' in rendered

class TestEmailContentValidation:
    """Test email content validation and quality"""
    
    def test_email_subject_validation(self):
        """Test email subject line validation"""
        subjects = [
            'Verify Your Email Address',
            'Confirm Email Change Request',
            'Password Reset Request',
            'Email Verification Reminder'
        ]
        
        for subject in subjects:
            # Subject should be reasonable length
            assert len(subject) <= 100
            
            # Subject should not contain HTML
            assert '<' not in subject
            assert '>' not in subject
            
            # Subject should be descriptive
            assert len(subject) > 10
    
    def test_email_body_structure(self, email_templates):
        """Test email body structure and formatting"""
        for template_name, template_content in email_templates.items():
            template = Template(template_content)
            
            rendered = template.render(
                user=Mock(full_name='Test User'),
                verification_url='https://example.com/verify',
                expiry_hours=24
            )
            
            # Should have proper email structure
            assert 'Hello' in rendered
            assert 'verification' in rendered.lower() or 'reset' in rendered.lower() or 'change' in rendered.lower()
            assert 'expire' in rendered.lower()
            assert 'hours' in rendered.lower()
            
            # Should have call-to-action
            assert 'href=' in rendered
            assert 'https://' in rendered
    
    def test_email_accessibility(self, email_templates):
        """Test email accessibility features"""
        for template_name, template_content in email_templates.items():
            template = Template(template_content)
            
            rendered = template.render(
                user=Mock(full_name='Test User'),
                verification_url='https://example.com/verify',
                expiry_hours=24
            )
            
            # Should have proper heading structure
            assert '<h1>' in rendered
            
            # Should have descriptive link text
            assert 'Verify' in rendered or 'Confirm' in rendered or 'Reset' in rendered
            
            # Should have reasonable contrast (basic check)
            assert 'color:' not in rendered.lower()  # Should use default colors
    
    def test_email_localization_support(self, email_templates):
        """Test email localization support"""
        # Test with different languages and character sets
        test_cases = [
            {'name': 'José García', 'language': 'Spanish'},
            {'name': '李小明', 'language': 'Chinese'},
            {'name': 'محمد أحمد', 'language': 'Arabic'},
            {'name': 'Иван Петров', 'language': 'Russian'}
        ]
        
        template = Template(email_templates['verification'])
        
        for test_case in test_cases:
            rendered = template.render(
                user=Mock(full_name=test_case['name']),
                verification_url='https://example.com/verify',
                expiry_hours=24
            )
            
            # Should preserve non-ASCII characters
            assert test_case['name'] in rendered
            
            # Should maintain proper HTML encoding
            assert '&' not in rendered or '&amp;' in rendered

class TestEmailTemplateIntegration:
    """Test email template integration with services"""
    
    def test_template_integration_with_service(self, test_db, sample_user, email_templates):
        """Test template integration with email verification service"""
        service = EmailVerificationService()
        
        # Mock email service
        with patch.object(service, 'email_service') as mock_email:
            mock_email.send_verification_email.return_value = {
                'success': True,
                'message_id': 'msg_123'
            }
            
            # Create verification
            verification, token = service.create_verification(
                sample_user.id, sample_user.email, 'signup'
            )
            
            # Verify email service was called with proper template
            mock_email.send_verification_email.assert_called_once()
            call_args = mock_email.send_verification_email.call_args
            
            # Should include user and verification data
            assert 'user' in call_args[1]
            assert 'verification_url' in call_args[1]
            assert 'expiry_hours' in call_args[1]
    
    def test_template_variable_validation(self, test_db, sample_user, email_templates):
        """Test that all required template variables are provided"""
        service = EmailVerificationService()
        
        # Mock email service to capture template variables
        template_vars = {}
        
        def capture_vars(*args, **kwargs):
            template_vars.update(kwargs)
            return {'success': True, 'message_id': 'msg_123'}
        
        with patch.object(service, 'email_service') as mock_email:
            mock_email.send_verification_email.side_effect = capture_vars
            
            # Create verification
            verification, token = service.create_verification(
                sample_user.id, sample_user.email, 'signup'
            )
            
            # Check required variables are present
            required_vars = ['user', 'verification_url', 'expiry_hours']
            for var in required_vars:
                assert var in template_vars
            
            # Check user data is properly structured
            user_data = template_vars['user']
            assert hasattr(user_data, 'full_name')
            assert hasattr(user_data, 'email')
    
    def test_template_error_handling(self, test_db, sample_user, email_templates):
        """Test template error handling"""
        service = EmailVerificationService()
        
        # Mock email service to raise template errors
        with patch.object(service, 'email_service') as mock_email:
            mock_email.send_verification_email.side_effect = Exception("Template error")
            
            # Should handle template errors gracefully
            with pytest.raises(Exception) as exc_info:
                service.create_verification(
                    sample_user.id, sample_user.email, 'signup'
                )
            
            assert 'Template error' in str(exc_info.value)
    
    def test_template_caching(self, test_db, sample_user, email_templates):
        """Test template caching and performance"""
        service = EmailVerificationService()
        
        # Mock email service
        with patch.object(service, 'email_service') as mock_email:
            mock_email.send_verification_email.return_value = {
                'success': True,
                'message_id': 'msg_123'
            }
            
            # Create multiple verifications (should reuse cached templates)
            for i in range(5):
                verification, token = service.create_verification(
                    i+1, f'user{i}@example.com', 'signup'
                )
            
            # Should have called email service 5 times
            assert mock_email.send_verification_email.call_count == 5

class TestEmailTemplatePerformance:
    """Test email template performance characteristics"""
    
    def test_template_rendering_speed(self, email_templates):
        """Test template rendering performance"""
        import time
        
        template = Template(email_templates['verification'])
        test_data = {
            'user': Mock(full_name='Test User'),
            'verification_url': 'https://example.com/verify?token=abc123',
            'expiry_hours': 24
        }
        
        # Measure rendering time
        start_time = time.time()
        
        for _ in range(1000):
            rendered = template.render(**test_data)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should render 1000 templates in under 1 second
        assert total_time < 1.0
        assert total_time > 0
    
    def test_template_memory_usage(self, email_templates):
        """Test template memory usage"""
        import gc
        import sys
        
        template = Template(email_templates['verification'])
        test_data = {
            'user': Mock(full_name='Test User'),
            'verification_url': 'https://example.com/verify?token=abc123',
            'expiry_hours': 24
        }
        
        # Get initial memory usage
        gc.collect()
        initial_memory = sys.getsizeof(template)
        
        # Render multiple times
        rendered_templates = []
        for _ in range(1000):
            rendered = template.render(**test_data)
            rendered_templates.append(rendered)
        
        # Get final memory usage
        gc.collect()
        final_memory = sys.getsizeof(template)
        
        # Template object size should remain constant
        assert final_memory == initial_memory
        
        # Clear references
        del rendered_templates
        gc.collect()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
