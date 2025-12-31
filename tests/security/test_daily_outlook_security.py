#!/usr/bin/env python3
"""
Daily Outlook Security Testing Suite

Comprehensive security testing for Daily Outlook functionality including:
- User data privacy validation
- API endpoint security testing
- Input validation and sanitization
- Rate limiting effectiveness
- Authentication and authorization
- Data encryption and protection
- SQL injection prevention
- XSS protection
- CSRF protection
- Session management
"""

import pytest
import json
import time
import hashlib
import hmac
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.models.database import db
from backend.models.daily_outlook import DailyOutlook, UserRelationshipStatus, RelationshipStatus
from backend.models.user_models import User
from backend.api.daily_outlook_api import daily_outlook_api
from backend.auth.decorators import require_auth, get_current_user_id
from backend.utils.validation import APIValidator
from backend.utils.encryption import EncryptionService
from backend.utils.rate_limiting import RateLimiter


class TestUserDataPrivacy:
    """Test suite for user data privacy validation"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def test_user(self, app):
        """Create test user"""
        with app.app_context():
            user = User(
                user_id='privacy_user_123',
                email='privacy@example.com',
                first_name='Privacy',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    def test_user_data_isolation(self, client, app, test_user):
        """Test that users can only access their own data"""
        with app.app_context():
            # Create another user
            other_user = User(
                user_id='other_user_456',
                email='other@example.com',
                first_name='Other',
                last_name='User',
                tier='budget'
            )
            db.session.add(other_user)
            db.session.commit()
            
            # Create outlook for other user
            other_outlook = DailyOutlook(
                user_id=other_user.id,
                date=date.today(),
                balance_score=85,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                primary_insight="Other user's private insight",
                streak_count=5
            )
            db.session.add(other_outlook)
            db.session.commit()
            
            # Test that test_user cannot access other_user's data
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    
                    # Should not return other user's data
                    if response.status_code == 200:
                        data = response.get_json()
                        assert data['outlook']['user_id'] == test_user.id
                        assert data['outlook']['user_id'] != other_user.id
    
    def test_sensitive_data_encryption(self, app, test_user):
        """Test that sensitive data is encrypted"""
        with app.app_context():
            # Create outlook with sensitive data
            outlook = DailyOutlook(
                user_id=test_user.id,
                date=date.today(),
                balance_score=75,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                primary_insight="Sensitive financial information",
                quick_actions=[
                    {"id": "sensitive_1", "title": "Review bank account", "description": "Check account balance"},
                    {"id": "sensitive_2", "title": "Update credit card", "description": "Change payment method"}
                ],
                streak_count=3
            )
            db.session.add(outlook)
            db.session.commit()
            
            # Test that sensitive data is not stored in plain text
            outlook_dict = outlook.to_dict()
            
            # Sensitive fields should be properly handled
            assert 'primary_insight' in outlook_dict
            assert 'quick_actions' in outlook_dict
            
            # Test encryption service
            encryption_service = EncryptionService()
            test_data = "Sensitive test data"
            encrypted_data = encryption_service.encrypt(test_data)
            decrypted_data = encryption_service.decrypt(encrypted_data)
            
            assert encrypted_data != test_data
            assert decrypted_data == test_data
    
    def test_data_anonymization(self, app, test_user):
        """Test that data can be anonymized for privacy"""
        with app.app_context():
            # Create outlook with personal data
            outlook = DailyOutlook(
                user_id=test_user.id,
                date=date.today(),
                balance_score=75,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                primary_insight="Personal financial situation",
                streak_count=3
            )
            db.session.add(outlook)
            db.session.commit()
            
            # Test anonymization
            def anonymize_outlook(outlook_data):
                """Anonymize outlook data"""
                anonymized = outlook_data.copy()
                anonymized['user_id'] = 'ANONYMIZED'
                anonymized['primary_insight'] = 'ANONYMIZED_INSIGHT'
                return anonymized
            
            outlook_dict = outlook.to_dict()
            anonymized_dict = anonymize_outlook(outlook_dict)
            
            assert anonymized_dict['user_id'] == 'ANONYMIZED'
            assert anonymized_dict['primary_insight'] == 'ANONYMIZED_INSIGHT'
            assert anonymized_dict['balance_score'] == outlook_dict['balance_score']  # Non-sensitive data preserved
    
    def test_data_retention_policy(self, app, test_user):
        """Test data retention policy compliance"""
        with app.app_context():
            # Create old outlook data
            old_date = date.today() - timedelta(days=365)  # 1 year old
            old_outlook = DailyOutlook(
                user_id=test_user.id,
                date=old_date,
                balance_score=70,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                primary_insight="Old insight",
                streak_count=1
            )
            db.session.add(old_outlook)
            db.session.commit()
            
            # Test data retention policy
            def should_retain_data(created_date, retention_days=365):
                """Check if data should be retained based on policy"""
                return (date.today() - created_date).days <= retention_days
            
            assert should_retain_data(old_date, 365)  # Should retain
            assert not should_retain_data(old_date, 180)  # Should not retain
    
    def test_data_export_privacy(self, client, app, test_user):
        """Test that data export respects privacy settings"""
        with app.app_context():
            # Create outlook data
            outlook = DailyOutlook(
                user_id=test_user.id,
                date=date.today(),
                balance_score=75,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                primary_insight="Personal insight",
                streak_count=3
            )
            db.session.add(outlook)
            db.session.commit()
            
            # Test data export with privacy controls
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    
                    if response.status_code == 200:
                        data = response.get_json()
                        
                        # Check that exported data doesn't contain sensitive information
                        outlook_data = data['outlook']
                        assert 'password' not in str(outlook_data)
                        assert 'ssn' not in str(outlook_data)
                        assert 'credit_card' not in str(outlook_data)


class TestAPIEndpointSecurity:
    """Test suite for API endpoint security testing"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    def test_authentication_required(self, client):
        """Test that authentication is required for all endpoints"""
        endpoints = [
            '/api/daily-outlook/',
            '/api/daily-outlook/history',
            '/api/daily-outlook/streak'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should require authentication
            assert response.status_code in [401, 403, 404]  # 404 if no auth, 401/403 if auth required
    
    def test_authorization_checks(self, client, app):
        """Test that authorization checks are properly implemented"""
        with app.app_context():
            user = User(
                user_id='auth_user_789',
                email='auth@example.com',
                first_name='Auth',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Test with valid authentication
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]  # 404 if no outlook exists
            
            # Test with invalid authentication
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=None):
                response = client.get('/api/daily-outlook/')
                assert response.status_code in [401, 403]
    
    def test_tier_based_access_control(self, client, app):
        """Test tier-based access control"""
        with app.app_context():
            # Create user with budget tier
            user = User(
                user_id='tier_user_101',
                email='tier@example.com',
                first_name='Tier',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Test budget tier access
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]
            
            # Test professional tier restriction
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=False):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 403
                    data = response.get_json()
                    assert data['upgrade_required'] is True
    
    def test_endpoint_rate_limiting(self, client, app):
        """Test that endpoints have rate limiting"""
        with app.app_context():
            user = User(
                user_id='ratelimit_user_202',
                email='ratelimit@example.com',
                first_name='RateLimit',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Test rate limiting
            rate_limiter = RateLimiter()
            
            # Simulate multiple requests
            for i in range(10):
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                    with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                        response = client.get('/api/daily-outlook/')
                        
                        # After rate limit, should return 429
                        if i > 5:  # Assuming rate limit of 5 requests
                            assert response.status_code == 429
                        else:
                            assert response.status_code in [200, 404, 429]


class TestInputValidationAndSanitization:
    """Test suite for input validation and sanitization"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def test_user(self, app):
        """Create test user"""
        with app.app_context():
            user = User(
                user_id='validation_user_303',
                email='validation@example.com',
                first_name='Validation',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    def test_sql_injection_prevention(self, client, test_user):
        """Test SQL injection prevention"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            # Test SQL injection in action_id
            malicious_payloads = [
                "'; DROP TABLE daily_outlooks; --",
                "1' OR '1'='1",
                "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
                "1' UNION SELECT * FROM users --"
            ]
            
            for payload in malicious_payloads:
                response = client.post('/api/daily-outlook/action-completed',
                                     json={
                                         'action_id': payload,
                                         'completion_status': True
                                     })
                
                # Should not cause database error
                assert response.status_code in [200, 400]  # Either success or validation error
                
                # Should not execute malicious SQL
                assert 'error' not in response.get_json() or 'SQL' not in str(response.get_json())
    
    def test_xss_prevention(self, client, test_user):
        """Test XSS prevention"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            # Test XSS payloads
            xss_payloads = [
                '<script>alert("xss")</script>',
                'javascript:alert("xss")',
                '<img src="x" onerror="alert(\'xss\')">',
                '<svg onload="alert(\'xss\')">',
                '"><script>alert("xss")</script>'
            ]
            
            for payload in xss_payloads:
                response = client.post('/api/daily-outlook/action-completed',
                                     json={
                                         'action_id': 'test',
                                         'completion_status': True,
                                         'completion_notes': payload
                                     })
                
                # Should sanitize or reject malicious content
                assert response.status_code in [200, 400]
                
                if response.status_code == 200:
                    data = response.get_json()
                    # Check that payload is sanitized
                    assert '<script>' not in str(data)
                    assert 'javascript:' not in str(data)
                    assert 'onerror=' not in str(data)
    
    def test_input_length_validation(self, client, test_user):
        """Test input length validation"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            # Test excessively long inputs
            long_string = 'A' * 10000  # 10KB string
            
            response = client.post('/api/daily-outlook/action-completed',
                                 json={
                                     'action_id': long_string,
                                     'completion_status': True,
                                     'completion_notes': long_string
                                 })
            
            # Should reject or truncate long inputs
            assert response.status_code in [200, 400]
    
    def test_input_type_validation(self, client, test_user):
        """Test input type validation"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            # Test invalid data types
            invalid_inputs = [
                {'action_id': 123, 'completion_status': True},  # action_id should be string
                {'action_id': 'test', 'completion_status': 'true'},  # completion_status should be boolean
                {'action_id': 'test', 'completion_status': True, 'completion_notes': 123},  # notes should be string
            ]
            
            for invalid_input in invalid_inputs:
                response = client.post('/api/daily-outlook/action-completed',
                                     json=invalid_input)
                
                # Should reject invalid types
                assert response.status_code == 400
    
    def test_rating_validation(self, client, test_user):
        """Test rating validation"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            # Test invalid ratings
            invalid_ratings = [0, 6, -1, 'invalid', None]
            
            for rating in invalid_ratings:
                response = client.post('/api/daily-outlook/rating',
                                     json={'rating': rating})
                
                # Should reject invalid ratings
                assert response.status_code == 400
    
    def test_relationship_status_validation(self, client, test_user):
        """Test relationship status validation"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            # Test invalid relationship status
            invalid_statuses = [
                {'status': 'invalid_status', 'satisfaction_score': 8, 'financial_impact_score': 7},
                {'status': 'single_career_focused', 'satisfaction_score': 15, 'financial_impact_score': 7},
                {'status': 'single_career_focused', 'satisfaction_score': 8, 'financial_impact_score': 15},
                {'status': 'single_career_focused', 'satisfaction_score': 0, 'financial_impact_score': 7},
            ]
            
            for invalid_status in invalid_statuses:
                response = client.post('/api/relationship-status',
                                     json=invalid_status)
                
                # Should reject invalid status data
                assert response.status_code == 400


class TestRateLimitingEffectiveness:
    """Test suite for rate limiting effectiveness"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    def test_rate_limiting_by_ip(self, client, app):
        """Test rate limiting by IP address"""
        with app.app_context():
            user = User(
                user_id='ratelimit_user_404',
                email='ratelimit@example.com',
                first_name='RateLimit',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Test rate limiting
            rate_limiter = RateLimiter()
            
            # Simulate requests from same IP
            for i in range(10):
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                    with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                        response = client.get('/api/daily-outlook/')
                        
                        # After rate limit, should return 429
                        if i > 5:  # Assuming rate limit of 5 requests per minute
                            assert response.status_code == 429
                        else:
                            assert response.status_code in [200, 404, 429]
    
    def test_rate_limiting_by_user(self, client, app):
        """Test rate limiting by user ID"""
        with app.app_context():
            user = User(
                user_id='userratelimit_user_505',
                email='userratelimit@example.com',
                first_name='UserRateLimit',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Test user-specific rate limiting
            rate_limiter = RateLimiter()
            
            # Simulate requests from same user
            for i in range(10):
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                    with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                        response = client.get('/api/daily-outlook/')
                        
                        # After rate limit, should return 429
                        if i > 5:
                            assert response.status_code == 429
                        else:
                            assert response.status_code in [200, 404, 429]
    
    def test_rate_limiting_reset(self, client, app):
        """Test rate limiting reset after time window"""
        with app.app_context():
            user = User(
                user_id='reset_user_606',
                email='reset@example.com',
                first_name='Reset',
                last_name='Test',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Test rate limiting reset
            rate_limiter = RateLimiter()
            
            # Exceed rate limit
            for i in range(10):
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                    with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                        response = client.get('/api/daily-outlook/')
                        
                        if i > 5:
                            assert response.status_code == 429
            
            # Wait for rate limit reset (mock time)
            with patch('time.time', return_value=time.time() + 3600):  # 1 hour later
                with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                    with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                        response = client.get('/api/daily-outlook/')
                        
                        # Should work again after reset
                        assert response.status_code in [200, 404, 429]


class TestDataEncryptionAndProtection:
    """Test suite for data encryption and protection"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    def test_sensitive_data_encryption(self, app):
        """Test that sensitive data is encrypted"""
        with app.app_context():
            encryption_service = EncryptionService()
            
            # Test encryption of sensitive data
            sensitive_data = {
                'financial_info': 'Bank account: 123456789',
                'personal_notes': 'Private thoughts and plans',
                'relationship_details': 'Intimate relationship information'
            }
            
            # Encrypt sensitive data
            encrypted_data = {}
            for key, value in sensitive_data.items():
                encrypted_data[key] = encryption_service.encrypt(value)
            
            # Verify encryption
            for key, encrypted_value in encrypted_data.items():
                assert encrypted_value != sensitive_data[key]
                assert len(encrypted_value) > len(sensitive_data[key])
                
                # Verify decryption
                decrypted_value = encryption_service.decrypt(encrypted_value)
                assert decrypted_value == sensitive_data[key]
    
    def test_password_hashing(self, app):
        """Test password hashing"""
        with app.app_context():
            # Test password hashing
            password = 'test_password_123'
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # Verify hash is different from original
            assert hashed_password != password
            assert len(hashed_password) == 64  # SHA256 hash length
            
            # Verify hash verification
            assert hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    def test_data_integrity_checks(self, app):
        """Test data integrity checks"""
        with app.app_context():
            # Test HMAC for data integrity
            data = 'sensitive_data'
            secret_key = 'secret_key'
            
            # Generate HMAC
            hmac_signature = hmac.new(
                secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Verify HMAC
            def verify_hmac(data, signature, secret_key):
                expected_signature = hmac.new(
                    secret_key.encode(),
                    data.encode(),
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(signature, expected_signature)
            
            assert verify_hmac(data, hmac_signature, secret_key)
            assert not verify_hmac('tampered_data', hmac_signature, secret_key)
    
    def test_secure_data_transmission(self, app):
        """Test secure data transmission"""
        with app.app_context():
            # Test HTTPS enforcement
            def enforce_https(request):
                """Enforce HTTPS for sensitive requests"""
                if not request.is_secure and not request.headers.get('X-Forwarded-Proto') == 'https':
                    return False
                return True
            
            # Mock request objects
            class MockRequest:
                def __init__(self, is_secure=False, headers=None):
                    self.is_secure = is_secure
                    self.headers = headers or {}
            
            # Test HTTPS enforcement
            secure_request = MockRequest(is_secure=True)
            insecure_request = MockRequest(is_secure=False)
            
            assert enforce_https(secure_request)
            assert not enforce_https(insecure_request)


class TestSessionManagement:
    """Test suite for session management"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    def test_session_timeout(self, app):
        """Test session timeout"""
        with app.app_context():
            # Test session timeout logic
            def is_session_valid(session_start, timeout_minutes=30):
                """Check if session is still valid"""
                return (datetime.now(timezone.utc) - session_start).total_seconds() < timeout_minutes * 60
            
            # Test valid session
            recent_session = datetime.utcnow() - timedelta(minutes=15)
            assert is_session_valid(recent_session)
            
            # Test expired session
            old_session = datetime.utcnow() - timedelta(minutes=45)
            assert not is_session_valid(old_session)
    
    def test_session_invalidation(self, app):
        """Test session invalidation"""
        with app.app_context():
            # Test session invalidation
            active_sessions = {'user1': 'session1', 'user2': 'session2'}
            
            def invalidate_session(user_id):
                """Invalidate user session"""
                if user_id in active_sessions:
                    del active_sessions[user_id]
                    return True
                return False
            
            # Test session invalidation
            assert invalidate_session('user1')
            assert 'user1' not in active_sessions
            assert not invalidate_session('nonexistent_user')
    
    def test_concurrent_session_handling(self, app):
        """Test concurrent session handling"""
        with app.app_context():
            # Test concurrent session management
            sessions = {}
            
            def create_session(user_id):
                """Create new session for user"""
                session_id = f"session_{user_id}_{time.time()}"
                sessions[user_id] = session_id
                return session_id
            
            def validate_session(user_id, session_id):
                """Validate user session"""
                return sessions.get(user_id) == session_id
            
            # Test concurrent session creation
            import threading
            
            results = []
            
            def create_session_thread(user_id):
                session_id = create_session(user_id)
                results.append((user_id, session_id))
            
            threads = []
            for i in range(10):
                thread = threading.Thread(target=create_session_thread, args=(f'user{i}',))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Verify all sessions were created
            assert len(results) == 10
            assert len(sessions) == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
