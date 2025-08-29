"""
Comprehensive Test Configuration and Fixtures

Provides test data, mock services, and environment setup for the complete MINGUS test suite.
"""

import pytest
import tempfile
import os
import json
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

# Flask and API testing
from flask import Flask
from flask.testing import FlaskClient
import requests

# Database testing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Frontend testing
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

# Performance testing
import psutil
import memory_profiler
import cProfile
import pstats

# Security testing
import jwt
import bcrypt
from cryptography.fernet import Fernet

# Analytics testing
import analytics
# from analytics import Analytics  # Commented out as it's not available

# Import application modules
try:
    from backend.app_factory import create_app
    from backend.services.assessment_scoring_service import AssessmentScoringService
    from backend.models.assessment_models import UserAssessment, AssessmentResult
    from backend.utils.auth import create_access_token, verify_token
    from backend.utils.validation import validate_json_schema
    from backend.database import get_db_session
    HAVE_BACKEND = True
except ImportError:
    HAVE_BACKEND = False

try:
    from frontend.src.components.assessments.AssessmentFlow import AssessmentFlow
    from frontend.src.components.assessments.AssessmentQuestion import AssessmentQuestion
    from frontend.src.components.LandingPage import LandingPage
    HAVE_FRONTEND = True
except ImportError:
    HAVE_FRONTEND = False

# Test configuration
TEST_CONFIG = {
    'DATABASE_URL': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret-key-for-testing-only',
    'JWT_SECRET_KEY': 'test-jwt-secret-key-for-testing-only',
    'TEST_USER_EMAIL': 'test@mingus.com',
    'TEST_USER_PASSWORD': 'testpassword123',
    'PERFORMANCE_THRESHOLDS': {
        'income_comparison_ms': 45,
        'page_load_seconds': 3.0,
        'assessment_submission_ms': 2000,
        'database_query_ms': 100
    },
    'SECURITY_THRESHOLDS': {
        'max_login_attempts': 5,
        'rate_limit_requests_per_minute': 60,
        'session_timeout_minutes': 30
    }
}

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG

@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing"""
    if not HAVE_BACKEND:
        pytest.skip("Backend not available")
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DATABASE_URL': TEST_CONFIG['DATABASE_URL'],
        'SECRET_KEY': TEST_CONFIG['SECRET_KEY'],
        'JWT_SECRET_KEY': TEST_CONFIG['JWT_SECRET_KEY']
    })
    
    with app.app_context():
        # Initialize database
        from backend.database import init_db
        init_db()
        yield app

@pytest.fixture(scope="function")
def client(app):
    """Create Flask test client"""
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        session = get_db_session()
        yield session
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def auth_headers():
    """Create authenticated request headers"""
    token = create_access_token(
        data={'sub': TEST_CONFIG['TEST_USER_EMAIL']},
        secret_key=TEST_CONFIG['JWT_SECRET_KEY']
    )
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture(scope="session")
def sample_assessment_data():
    """Provide sample assessment data for testing"""
    return {
        'current_salary': 75000,
        'field': 'software_development',
        'experience_level': 'mid',
        'company_size': 'medium',
        'location': 'San Francisco, CA',
        'industry': 'Technology',
        'skills': ['Python', 'React', 'AWS'],
        'required_skills': ['Python', 'JavaScript'],
        'relationship_status': 'married',
        'financial_stress_frequency': 'sometimes',
        'emotional_triggers': ['after_arguments'],
        'education_level': 'bachelors',
        'age_group': '25-35'
    }

@pytest.fixture(scope="session")
def sample_user_data():
    """Provide sample user data for testing"""
    return {
        'email': TEST_CONFIG['TEST_USER_EMAIL'],
        'password': TEST_CONFIG['TEST_USER_PASSWORD'],
        'first_name': 'Test',
        'last_name': 'User',
        'age_group': '25-35',
        'education_level': 'bachelors',
        'location': 'San Francisco, CA'
    }

@pytest.fixture(scope="session")
def assessment_scoring_service():
    """Create assessment scoring service instance"""
    if not HAVE_BACKEND:
        pytest.skip("Backend not available")
    return AssessmentScoringService()

@pytest.fixture(scope="session")
def mock_analytics():
    """Create mock analytics service"""
    mock_analytics = Mock()  # Remove spec=Analytics since it's not available
    mock_analytics.track = Mock()
    mock_analytics.identify = Mock()
    mock_analytics.page = Mock()
    return mock_analytics

@pytest.fixture(scope="session")
def mock_payment_processor():
    """Create mock payment processor"""
    mock_processor = Mock()
    mock_processor.create_payment_intent = Mock(return_value={
        'id': 'pi_test_123',
        'client_secret': 'pi_test_secret_123',
        'amount': 2000,
        'currency': 'usd'
    })
    mock_processor.confirm_payment = Mock(return_value={'status': 'succeeded'})
    return mock_processor

@pytest.fixture(scope="session")
def mock_email_service():
    """Create mock email service"""
    mock_email = Mock()
    mock_email.send_welcome_email = Mock(return_value=True)
    mock_email.send_assessment_results = Mock(return_value=True)
    mock_email.send_payment_confirmation = Mock(return_value=True)
    return mock_email

@pytest.fixture(scope="session")
def webdriver_options():
    """Create webdriver options for cross-browser testing"""
    options = {
        'chrome': Options(),
        'firefox': FirefoxOptions(),
        'safari': SafariOptions(),
        'edge': EdgeOptions()
    }
    
    # Common options
    for browser_options in options.values():
        browser_options.add_argument('--headless')
        browser_options.add_argument('--no-sandbox')
        browser_options.add_argument('--disable-dev-shm-usage')
        browser_options.add_argument('--disable-gpu')
        browser_options.add_argument('--window-size=1920,1080')
    
    return options

@pytest.fixture(scope="function")
def chrome_driver(webdriver_options):
    """Create Chrome webdriver for testing"""
    try:
        driver = webdriver.Chrome(options=webdriver_options['chrome'])
        driver.implicitly_wait(10)
        yield driver
    finally:
        driver.quit()

@pytest.fixture(scope="function")
def firefox_driver(webdriver_options):
    """Create Firefox webdriver for testing"""
    try:
        driver = webdriver.Firefox(options=webdriver_options['firefox'])
        driver.implicitly_wait(10)
        yield driver
    finally:
        driver.quit()

@pytest.fixture(scope="function")
def safari_driver(webdriver_options):
    """Create Safari webdriver for testing"""
    try:
        driver = webdriver.Safari(options=webdriver_options['safari'])
        driver.implicitly_wait(10)
        yield driver
    finally:
        driver.quit()

@pytest.fixture(scope="function")
def edge_driver(webdriver_options):
    """Create Edge webdriver for testing"""
    try:
        driver = webdriver.Edge(options=webdriver_options['edge'])
        driver.implicitly_wait(10)
        yield driver
    finally:
        driver.quit()

@pytest.fixture(scope="session")
def performance_monitor():
    """Create performance monitoring utility"""
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}
        
        def start_timer(self, name):
            self.metrics[name] = {'start': time.time()}
        
        def end_timer(self, name):
            if name in self.metrics:
                self.metrics[name]['end'] = time.time()
                self.metrics[name]['duration'] = (
                    self.metrics[name]['end'] - self.metrics[name]['start']
                )
        
        def get_duration(self, name):
            return self.metrics.get(name, {}).get('duration', 0)
        
        def get_memory_usage(self):
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
    
    return PerformanceMonitor()

@pytest.fixture(scope="session")
def security_scanner():
    """Create security scanning utility"""
    class SecurityScanner:
        def __init__(self):
            self.vulnerabilities = []
        
        def scan_sql_injection(self, input_data):
            sql_patterns = ["'", "DROP", "DELETE", "INSERT", "UPDATE", "SELECT"]
            for pattern in sql_patterns:
                if pattern.lower() in str(input_data).lower():
                    self.vulnerabilities.append(f"Potential SQL injection: {pattern}")
            return len(self.vulnerabilities) == 0
        
        def scan_xss(self, input_data):
            xss_patterns = ["<script>", "javascript:", "onerror=", "onload="]
            for pattern in xss_patterns:
                if pattern.lower() in str(input_data).lower():
                    self.vulnerabilities.append(f"Potential XSS: {pattern}")
            return len(self.vulnerabilities) == 0
        
        def scan_csrf(self, headers):
            if 'X-CSRF-Token' not in headers:
                self.vulnerabilities.append("Missing CSRF token")
            return len(self.vulnerabilities) == 0
        
        def get_vulnerabilities(self):
            return self.vulnerabilities.copy()
    
    return SecurityScanner()

@pytest.fixture(scope="session")
def mathematical_validator():
    """Create mathematical validation utility"""
    class MathematicalValidator:
        def __init__(self):
            self.calculation_errors = []
        
        def validate_salary_improvement_score(self, current_salary, target_salary, expected_score):
            """Validate salary improvement score calculation"""
            improvement_percentage = ((target_salary - current_salary) / current_salary) * 100
            
            if improvement_percentage >= 45:
                expected = 1.0
            elif improvement_percentage >= 35:
                expected = 0.9
            elif improvement_percentage >= 25:
                expected = 0.8
            elif improvement_percentage >= 15:
                expected = 0.7
            elif improvement_percentage >= 5:
                expected = 0.6
            else:
                expected = 0.5
            
            if abs(expected - expected_score) > 0.01:
                self.calculation_errors.append(
                    f"Salary improvement score mismatch: expected {expected}, got {expected_score}"
                )
            return abs(expected - expected_score) <= 0.01
        
        def validate_relationship_scoring(self, status, stress_frequency, triggers, expected_points):
            """Validate relationship scoring calculation"""
            relationship_points = {
                'single': 0, 'dating': 2, 'serious': 4, 
                'married': 6, 'complicated': 8
            }
            
            stress_points = {
                'never': 0, 'rarely': 2, 'sometimes': 4,
                'often': 6, 'always': 8
            }
            
            trigger_points = {
                'after_breakup': 3, 'after_arguments': 3,
                'when_lonely': 2, 'when_jealous': 2, 'social_pressure': 2
            }
            
            calculated_points = (
                relationship_points.get(status, 0) +
                stress_points.get(stress_frequency, 0) +
                sum(trigger_points.get(trigger, 0) for trigger in triggers)
            )
            
            if calculated_points != expected_points:
                self.calculation_errors.append(
                    f"Relationship scoring mismatch: expected {expected_points}, got {calculated_points}"
                )
            return calculated_points == expected_points
        
        def validate_percentile_calculation(self, salary, demographic_data, expected_percentile):
            """Validate percentile calculation"""
            # Simplified percentile calculation for testing
            sorted_salaries = sorted(demographic_data)
            position = 0
            for i, s in enumerate(sorted_salaries):
                if salary >= s:
                    position = i + 1
            
            calculated_percentile = (position / len(sorted_salaries)) * 100
            
            if abs(calculated_percentile - expected_percentile) > 1.0:
                self.calculation_errors.append(
                    f"Percentile calculation mismatch: expected {expected_percentile}, got {calculated_percentile}"
                )
            return abs(calculated_percentile - expected_percentile) <= 1.0
        
        def get_errors(self):
            return self.calculation_errors.copy()
    
    return MathematicalValidator()

@pytest.fixture(scope="session")
def load_test_executor():
    """Create load testing executor"""
    return ThreadPoolExecutor(max_workers=10)

@pytest.fixture(scope="session")
def test_data_generator():
    """Create test data generator"""
    class TestDataGenerator:
        def __init__(self):
            self.salary_ranges = {
                'entry': (40000, 60000),
                'mid': (60000, 90000),
                'senior': (90000, 130000),
                'lead': (130000, 180000),
                'executive': (180000, 300000)
            }
            
            self.fields = [
                'software_development', 'data_analysis', 'project_management',
                'marketing', 'finance', 'sales', 'operations', 'hr'
            ]
            
            self.locations = [
                'San Francisco, CA', 'New York, NY', 'Austin, TX',
                'Seattle, WA', 'Boston, MA', 'Denver, CO'
            ]
        
        def generate_assessment_data(self, **kwargs):
            """Generate random assessment data"""
            import random
            
            data = {
                'current_salary': random.randint(40000, 200000),
                'field': random.choice(self.fields),
                'experience_level': random.choice(['entry', 'mid', 'senior', 'lead', 'executive']),
                'company_size': random.choice(['startup', 'small', 'medium', 'large', 'enterprise']),
                'location': random.choice(self.locations),
                'relationship_status': random.choice(['single', 'dating', 'serious', 'married', 'complicated']),
                'financial_stress_frequency': random.choice(['never', 'rarely', 'sometimes', 'often', 'always']),
                'emotional_triggers': random.sample(['after_breakup', 'after_arguments', 'when_lonely', 'when_jealous', 'social_pressure'], 
                                                  random.randint(0, 3)),
                'education_level': random.choice(['high_school', 'some_college', 'bachelors', 'masters', 'doctorate']),
                'age_group': random.choice(['18-24', '25-35', '36-45', '46-55', '55+'])
            }
            
            # Override with provided kwargs
            data.update(kwargs)
            return data
        
        def generate_user_data(self, **kwargs):
            """Generate random user data"""
            import random
            
            data = {
                'email': f'test{random.randint(1000, 9999)}@mingus.com',
                'password': 'testpassword123',
                'first_name': f'Test{random.randint(1, 100)}',
                'last_name': f'User{random.randint(1, 100)}',
                'age_group': random.choice(['18-24', '25-35', '36-45', '46-55', '55+']),
                'education_level': random.choice(['high_school', 'some_college', 'bachelors', 'masters', 'doctorate']),
                'location': random.choice(self.locations)
            }
            
            data.update(kwargs)
            return data
    
    return TestDataGenerator()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "backend: mark test as backend API test"
    )
    config.addinivalue_line(
        "markers", "frontend: mark test as frontend component test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "analytics: mark test as analytics verification test"
    )
    config.addinivalue_line(
        "markers", "mathematical: mark test as mathematical accuracy test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
