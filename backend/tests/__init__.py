"""
Comprehensive Testing Framework for AI Calculator

This package contains all test suites for the AI Calculator application:
- Unit tests for services, models, and utilities
- Integration tests for API endpoints and workflows
- Performance tests for load testing and optimization
- Frontend tests for React components
- A/B testing framework for statistical analysis
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
TEST_CONFIG = {
    'TESTING': True,
    'DATABASE_URL': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret-key',
    'MAIL_SUPPRESS_SEND': True,
    'STRIPE_TEST_MODE': True,
    'CELERY_ALWAYS_EAGER': True,
    'CACHE_TYPE': 'simple'
}

# Mock services for testing
MOCK_SERVICES = {
    'email': Mock(),
    'payment': Mock(),
    'analytics': Mock(),
    'notification': Mock()
}

# Test data fixtures
TEST_FIXTURES = {
    'users': [],
    'assessments': [],
    'payments': [],
    'analytics': []
}

def setup_test_environment():
    """Setup test environment with mocks and fixtures"""
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.ERROR)
    
    # Setup mock services
    for service_name, mock_service in MOCK_SERVICES.items():
        mock_service.reset_mock()
    
    return TEST_CONFIG, MOCK_SERVICES, TEST_FIXTURES

def teardown_test_environment():
    """Cleanup test environment"""
    # Clear any test data
    TEST_FIXTURES.clear()
    
    # Reset mock services
    for mock_service in MOCK_SERVICES.values():
        mock_service.reset_mock()
