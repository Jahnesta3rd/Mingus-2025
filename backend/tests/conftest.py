"""
Pytest configuration and fixtures for MINGUS testing

This file contains:
- Pytest configuration
- Database fixtures
- Mock service fixtures
- Test data fixtures
- Authentication fixtures
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Any, Generator

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Import models and services
from models import Base, User, EmailVerification
from models.assessment_models import Assessment
from models.assessment_analytics_models import AssessmentAnalyticsEvent as AssessmentAnalytics
from services.assessment_scoring_service import AssessmentScoringService
from services.email_automation_service import EmailAutomationService
from services.ai_calculator_payment_service import AICalculatorPaymentService
from services.ai_calculator_analytics_service import AICalculatorAnalyticsService

# Test configuration
@pytest.fixture(scope="session")
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'MAIL_SUPPRESS_SEND': True,
        'STRIPE_TEST_MODE': True,
        'CELERY_ALWAYS_EAGER': True,
        'CACHE_TYPE': 'simple',
        'REDIS_URL': 'redis://localhost:6379/1',
        'EMAIL_VERIFICATION_SECRET': 'test-verification-secret'
    })
    
    # Initialize extensions
    db = SQLAlchemy(app)
    jwt = JWTManager(app)
    CORS(app)
    
    return app

@pytest.fixture(scope="function")
def test_db():
    """Create test database with minimal tables for email verification testing"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Import only the models needed for email verification testing
    from models.base import Base
    from models.user import User
    from models.email_verification import EmailVerification
    
    # Create only the required tables
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()

@pytest.fixture(scope="function")
def mock_email_service():
    """Mock email service"""
    with patch('backend.services.email_automation_service.EmailAutomationService') as mock:
        service = mock.return_value
        service.send_assessment_email.return_value = True
        service.send_payment_confirmation.return_value = True
        service.send_analytics_report.return_value = True
        yield service

@pytest.fixture(scope="function")
def mock_payment_service():
    """Mock payment service"""
    with patch('backend.services.ai_calculator_payment_service.AICalculatorPaymentService') as mock:
        service = mock.return_value
        service.process_payment.return_value = {
            'success': True,
            'transaction_id': 'test_txn_123',
            'amount': 29.99
        }
        service.create_customer.return_value = {
            'customer_id': 'cus_test123',
            'email': 'test@example.com'
        }
        yield service

@pytest.fixture(scope="function")
def mock_analytics_service():
    """Mock analytics service"""
    with patch('backend.services.ai_calculator_analytics_service.AICalculatorAnalyticsService') as mock:
        service = mock.return_value
        service.track_assessment_completion.return_value = True
        service.track_payment_event.return_value = True
        service.generate_insights.return_value = {
            'insights': ['Test insight 1', 'Test insight 2'],
            'metrics': {'completion_rate': 0.85}
        }
        yield service

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create test user"""
    user = User(
        id='test_user_123',
        email='test@example.com',
        first_name='Test',
        last_name='User',
        subscription_tier='basic',
        created_at=datetime.utcnow(),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_assessment_data():
    """Test assessment data fixture"""
    return {
        'current_salary': 75000,
        'field': 'software_development',
        'experience_level': 'mid',
        'company_size': 'large',
        'location': 'urban',
        'industry': 'technology',
        'skills': ['python', 'javascript', 'react'],
        'required_skills': ['python', 'javascript', 'react', 'node.js'],
        'daily_tasks': {
            'coding': True,
            'meetings': True,
            'documentation': False,
            'testing': True
        },
        'work_environment': {
            'ai_usage': 'moderate',
            'remote_work': True,
            'team_size': 'medium'
        },
        'skills_and_concerns': {
            'tech_skills': ['python', 'javascript'],
            'soft_skills': ['communication', 'leadership'],
            'concerns': ['automation', 'skill_gaps']
        }
    }

@pytest.fixture(scope="function")
def test_assessment(db_session, test_user, test_assessment_data):
    """Create test assessment"""
    assessment = Assessment(
        id='test_assessment_123',
        user_id=test_user.id,
        assessment_type='job_risk',
        data=test_assessment_data,
        created_at=datetime.utcnow(),
        status='completed'
    )
    db_session.add(assessment)
    db_session.commit()
    return assessment

@pytest.fixture(scope="function")
def mock_stripe():
    """Mock Stripe API"""
    with patch('stripe.PaymentIntent.create') as mock_create, \
         patch('stripe.Customer.create') as mock_customer, \
         patch('stripe.Webhook.construct_event') as mock_webhook:
        
        mock_create.return_value = Mock(
            id='pi_test_123',
            status='succeeded',
            amount=2999,
            currency='usd'
        )
        
        mock_customer.return_value = Mock(
            id='cus_test_123',
            email='test@example.com'
        )
        
        mock_webhook.return_value = Mock(
            type='payment_intent.succeeded',
            data=Mock(object=Mock(id='pi_test_123'))
        )
        
        yield {
            'create': mock_create,
            'customer': mock_customer,
            'webhook': mock_webhook
        }

@pytest.fixture(scope="function")
def mock_celery():
    """Mock Celery tasks"""
    with patch('backend.celery_app.celery.send_task') as mock_send_task:
        mock_send_task.return_value = Mock(id='task_123')
        yield mock_send_task

@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis cache"""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        yield mock_redis

@pytest.fixture(scope="function")
def test_client(app):
    """Test client fixture"""
    return app.test_client()

@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Authentication headers fixture"""
    # In a real implementation, you'd generate a JWT token
    return {
        'Authorization': f'Bearer test_token_{test_user.id}',
        'Content-Type': 'application/json'
    }

# Performance testing fixtures
@pytest.fixture(scope="function")
def load_test_data():
    """Generate load test data"""
    return {
        'concurrent_users': 100,
        'requests_per_user': 10,
        'test_duration': 300,  # 5 minutes
        'ramp_up_time': 60,    # 1 minute
        'target_response_time': 2000  # 2 seconds
    }

# A/B testing fixtures
@pytest.fixture(scope="function")
def ab_test_config():
    """A/B test configuration"""
    return {
        'test_id': 'calculator_ui_v2',
        'variants': ['control', 'treatment'],
        'traffic_split': [0.5, 0.5],
        'metrics': ['conversion_rate', 'completion_time', 'user_satisfaction'],
        'confidence_level': 0.95,
        'minimum_sample_size': 1000
    }

# Test data generators
def generate_test_users(count: int = 10) -> List[Dict[str, Any]]:
    """Generate test user data"""
    users = []
    for i in range(count):
        users.append({
            'id': f'test_user_{i}',
            'email': f'test{i}@example.com',
            'first_name': f'Test{i}',
            'last_name': f'User{i}',
            'subscription_tier': 'basic' if i % 3 == 0 else 'premium' if i % 3 == 1 else 'enterprise',
            'created_at': datetime.utcnow() - timedelta(days=i)
        })
    return users

def generate_test_assessments(count: int = 50) -> List[Dict[str, Any]]:
    """Generate test assessment data"""
    fields = ['software_development', 'data_analysis', 'marketing', 'finance', 'sales']
    experience_levels = ['entry', 'mid', 'senior', 'executive']
    
    assessments = []
    for i in range(count):
        assessments.append({
            'id': f'test_assessment_{i}',
            'user_id': f'test_user_{i % 10}',
            'assessment_type': 'job_risk',
            'data': {
                'current_salary': 50000 + (i * 5000),
                'field': fields[i % len(fields)],
                'experience_level': experience_levels[i % len(experience_levels)],
                'company_size': 'large' if i % 2 == 0 else 'medium',
                'location': 'urban' if i % 3 == 0 else 'suburban',
                'industry': 'technology'
            },
            'created_at': datetime.utcnow() - timedelta(hours=i),
            'status': 'completed'
        })
    return assessments

# Fixture for test data
@pytest.fixture(scope="session")
def test_data():
    """Comprehensive test data fixture"""
    return {
        'users': generate_test_users(100),
        'assessments': generate_test_assessments(500),
        'payments': [
            {
                'id': f'payment_{i}',
                'user_id': f'test_user_{i % 10}',
                'amount': 29.99,
                'currency': 'usd',
                'status': 'succeeded',
                'created_at': datetime.utcnow() - timedelta(days=i)
            }
            for i in range(50)
        ]
    }
