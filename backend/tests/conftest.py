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

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models.database import db, init_database
from backend.api import register_all_apis
from backend.middleware.security import SecurityMiddleware
from tests.db_helpers import configure_app_for_tests, ensure_all_models_imported

@pytest.fixture
def app():
    """Create Flask application for testing"""
    app = Flask(__name__)
    configure_app_for_tests(app)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    ensure_all_models_imported()
    db.init_app(app)
    
    # Register all API blueprints
    register_all_apis(app)
    
    # Initialize security middleware
    security_middleware = SecurityMiddleware()
    security_middleware.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

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
