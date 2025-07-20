import os
import pytest
from app import create_app

# Set test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['SUPABASE_URL'] = 'https://test-project.supabase.co'
os.environ['SUPABASE_KEY'] = 'test-key'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    app = create_app('testing')
    return app

@pytest.fixture
def test_client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def supabase_client(app):
    """Get the mock Supabase client from the app."""
    return app.supabase_client

@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    return {
        'Authorization': 'Bearer test_token',
        'user_id': 'test_user_id'
    }

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    ) 