"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import os
import sys
import json
from datetime import datetime
from flask import Flask
from unittest.mock import Mock, patch

# Add repo root to path (not backend/ — that shadows the celery package)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.models.database import db
from backend.api import register_all_apis
from backend.middleware.security import SecurityMiddleware
from tests.db_helpers import configure_app_for_tests, initialize_shared_schema, cleanup_test_data

@pytest.fixture(scope="session", autouse=True)
def _shared_db_schema():
    initialize_shared_schema(db)
    yield

@pytest.fixture
def app(_shared_db_schema):
    """Create Flask application for testing"""
    app = Flask(__name__)
    configure_app_for_tests(app)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    db.init_app(app)
    
    # Register all API blueprints
    register_all_apis(app)
    
    # Initialize security middleware
    security_middleware = SecurityMiddleware()
    security_middleware.init_app(app)
    
    with app.app_context():
        yield app
        cleanup_test_data(db)

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def auth_headers():
    """Create authentication headers for testing"""
    return {
        'X-User-ID': 'test-user-123',
        'X-CSRF-Token': 'test-csrf-token',
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def sample_assessment_data():
    """Sample assessment data for testing"""
    return {
        'email': 'test@example.com',
        'firstName': 'John',
        'phone': '1234567890',
        'assessmentType': 'ai-risk',
        'answers': {
            'question1': 'answer1',
            'question2': 'answer2'
        }
    }

@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 30,
        'location': 'New York, NY'
    }

@pytest.fixture
def sample_vehicle_data():
    """Sample vehicle data for testing"""
    return {
        'make': 'Toyota',
        'model': 'Camry',
        'year': 2020,
        'vin': '1HGBH41JXMN109186',
        'mileage': 50000
    }

@pytest.fixture
def mock_user():
    """Mock user object"""
    user = Mock()
    user.id = 'test-user-123'
    user.email = 'test@example.com'
    user.name = 'Test User'
    return user

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock()


@pytest.fixture
def db_session(app):
    """SQLAlchemy session bound to the test Flask app."""
    with app.app_context():
        yield db.session


@pytest.fixture(autouse=True)
def celery_config():
    """Use eager execution in tests so tasks run synchronously."""
    from backend.celery import celery as celery_app

    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=False,
        broker_url="memory://",
        result_backend="cache+memory://",
    )
    return celery_app
