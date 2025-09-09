#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Splash Page Test Configuration
Pytest configuration and fixtures for meme splash page testing
"""

import pytest
import sqlite3
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from meme_selector import MemeSelector
from backend.api.meme_endpoints import meme_api
from flask import Flask
from tests.meme_splash.fixtures.test_data import MemeTestData, DatabaseTestSetup

@pytest.fixture(scope="session")
def test_database():
    """Create a test database for the entire test session"""
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    # Set up database with test data
    DatabaseTestSetup.create_test_database(test_db.name)
    
    yield test_db.name
    
    # Cleanup
    if os.path.exists(test_db.name):
        os.unlink(test_db.name)

@pytest.fixture(scope="session")
def performance_test_database():
    """Create a test database with performance test data"""
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    # Set up database with performance test data
    DatabaseTestSetup.create_test_database(test_db.name, include_performance_data=True)
    
    yield test_db.name
    
    # Cleanup
    if os.path.exists(test_db.name):
        os.unlink(test_db.name)

@pytest.fixture
def empty_database():
    """Create an empty test database"""
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    # Set up empty database
    DatabaseTestSetup.create_empty_database(test_db.name)
    
    yield test_db.name
    
    # Cleanup
    if os.path.exists(test_db.name):
        os.unlink(test_db.name)

@pytest.fixture
def meme_selector(test_database):
    """Create a MemeSelector instance with test database"""
    return MemeSelector(test_database)

@pytest.fixture
def performance_meme_selector(performance_test_database):
    """Create a MemeSelector instance with performance test database"""
    return MemeSelector(performance_test_database)

@pytest.fixture
def flask_app(test_database):
    """Create a Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(meme_api)
    app.config['TESTING'] = True
    
    # Mock database path
    with patch('backend.api.meme_endpoints.DB_PATH', test_database):
        yield app

@pytest.fixture
def test_client(flask_app):
    """Create a test client for the Flask app"""
    return flask_app.test_client()

@pytest.fixture
def sample_meme_data():
    """Provide sample meme data for testing"""
    return MemeTestData.SAMPLE_MEMES[0]

@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing"""
    return MemeTestData.SAMPLE_USERS[0]

@pytest.fixture
def sample_session_data():
    """Provide sample session data for testing"""
    return MemeTestData.SAMPLE_SESSIONS[0]

@pytest.fixture
def mock_meme_response():
    """Provide mock meme API response"""
    return {
        'id': 1,
        'image_url': 'https://example.com/meme1.jpg',
        'category': 'faith',
        'caption': 'Sunday motivation: Trust the process',
        'alt_text': 'Faith meme showing trust',
        'is_active': True,
        'created_at': '2024-01-15T10:30:00Z',
        'updated_at': '2024-01-15T10:30:00Z'
    }

@pytest.fixture
def mock_analytics_response():
    """Provide mock analytics API response"""
    return {
        'success': True,
        'message': 'Analytics tracked successfully'
    }

@pytest.fixture
def mock_error_response():
    """Provide mock error API response"""
    return {
        'error': 'Internal server error',
        'message': 'Failed to fetch meme'
    }

@pytest.fixture
def test_headers():
    """Provide test headers for API requests"""
    return {
        'X-User-ID': 'test_user_123',
        'X-Session-ID': 'test_session_456',
        'Content-Type': 'application/json',
        'User-Agent': 'Test Browser'
    }

@pytest.fixture
def mock_database_connection(test_database):
    """Mock database connection for testing"""
    with patch('backend.api.meme_endpoints.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        yield mock_conn, mock_cursor

@pytest.fixture
def mock_fetch():
    """Mock fetch function for frontend testing"""
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        yield mock_get, mock_post

@pytest.fixture
def performance_benchmarks():
    """Provide performance benchmarks for testing"""
    return {
        'meme_selection_time': 0.1,  # seconds
        'api_response_time': 0.5,    # seconds
        'database_query_time': 0.05, # seconds
        'image_load_time': 2.0,      # seconds
        'component_render_time': 0.1 # seconds
    }

@pytest.fixture
def load_test_scenarios():
    """Provide load test scenarios"""
    return {
        'light_load': {
            'concurrent_users': 10,
            'requests_per_user': 5,
            'duration_minutes': 1
        },
        'medium_load': {
            'concurrent_users': 50,
            'requests_per_user': 10,
            'duration_minutes': 5
        },
        'heavy_load': {
            'concurrent_users': 100,
            'requests_per_user': 20,
            'duration_minutes': 10
        }
    }

@pytest.fixture
def memory_limits():
    """Provide memory usage limits for testing"""
    return {
        'max_memory_increase_mb': 10,
        'max_memory_usage_mb': 100,
        'gc_threshold_mb': 50
    }

@pytest.fixture(autouse=True)
def cleanup_timers():
    """Clean up timers after each test"""
    yield
    # Cleanup code here if needed

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test"""
    yield
    # Reset mocks here if needed

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "frontend: mark test as a frontend test"
    )
    config.addinivalue_line(
        "markers", "backend: mark test as a backend test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths"""
    for item in items:
        # Add markers based on file path
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "frontend" in item.nodeid:
            item.add_marker(pytest.mark.frontend)
        if "backend" in item.nodeid:
            item.add_marker(pytest.mark.backend)

# Custom pytest hooks
def pytest_html_report_title(report):
    """Set custom title for HTML reports"""
    report.title = "Meme Splash Page Test Report"

def pytest_html_results_table_header(cells):
    """Customize HTML report table headers"""
    cells.insert(2, html.th('Description'))
    cells.insert(3, html.th('Duration', class_='sortable time', col='time'))
    cells.pop()

def pytest_html_results_table_row(report, cells):
    """Customize HTML report table rows"""
    cells.insert(2, html.td(report.description))
    cells.insert(3, html.td(datetime.now(), class_='col-time'))
    cells.pop()

# Test data generators
@pytest.fixture
def generate_test_memes():
    """Generate test memes for testing"""
    def _generate(count=10):
        memes = []
        categories = ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
        
        for i in range(count):
            category = categories[i % len(categories)]
            memes.append({
                'id': i + 1,
                'image_url': f'https://example.com/test_meme_{i}.jpg',
                'category': category,
                'caption': f'Test meme {i} for {category}',
                'alt_text': f'Alt text for test meme {i}',
                'is_active': 1,
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z'
            })
        
        return memes
    
    return _generate

@pytest.fixture
def generate_test_users():
    """Generate test users for testing"""
    def _generate(count=5):
        users = []
        
        for i in range(count):
            users.append({
                'id': i + 1,
                'username': f'test_user_{i}',
                'email': f'test{i}@example.com',
                'created_at': '2024-01-01T00:00:00Z'
            })
        
        return users
    
    return _generate

# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Provide a performance timer utility"""
    import time
    
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return PerformanceTimer()

# Memory testing utilities
@pytest.fixture
def memory_monitor():
    """Provide a memory monitoring utility"""
    import psutil
    import os
    
    class MemoryMonitor:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.initial_memory = None
        
        def start_monitoring(self):
            self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        def get_memory_usage(self):
            return self.process.memory_info().rss / 1024 / 1024  # MB
        
        def get_memory_increase(self):
            if self.initial_memory:
                return self.get_memory_usage() - self.initial_memory
            return None
    
    return MemoryMonitor()

# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment"""
    # Set environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    
    yield
    
    # Cleanup environment variables
    if 'FLASK_ENV' in os.environ:
        del os.environ['FLASK_ENV']
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
