"""
Pytest configuration and fixtures for Meme Splash Page tests
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import Flask app and models
from backend.app_factory import create_app
from backend.models.meme_models import Meme, UserMemePreferences, UserMemeHistory
from backend.models.user import User
from backend.services.meme_service import MemeService


@pytest.fixture(scope="session")
def test_app():
    """Create a test Flask application"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Use in-memory SQLite for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False}
    }
    
    return app


@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    engine = create_engine('sqlite:///:memory:', poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    from backend.models.meme_models import Base
    Base.metadata.create_all(bind=engine)
    
    return engine, TestingSessionLocal


@pytest.fixture
def db_session(test_db):
    """Create a database session for each test"""
    engine, TestingSessionLocal = test_db
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def meme_service(db_session):
    """Create a MemeService instance for testing"""
    return MemeService(db_session)


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        id=123,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_memes(db_session):
    """Create sample memes for testing"""
    memes = [
        {
            'id': 'meme-1',
            'image_url': 'https://example.com/meme1.jpg',
            'category': 'monday_career',
            'caption_text': 'Monday motivation: Building wealth one paycheck at a time',
            'alt_text': 'A person in business attire flexing muscles',
            'priority': 9,
            'is_active': True,
            'engagement_score': 0.8
        },
        {
            'id': 'meme-2',
            'image_url': 'https://example.com/meme2.jpg',
            'category': 'tuesday_health',
            'caption_text': 'Your health is an investment, not an expense',
            'alt_text': 'A person exercising with dollar signs',
            'priority': 8,
            'is_active': True,
            'engagement_score': 0.7
        },
        {
            'id': 'meme-3',
            'image_url': 'https://example.com/meme3.jpg',
            'category': 'wednesday_home',
            'caption_text': 'Your home is more than shelter, it\'s an investment',
            'alt_text': 'A house with a growth chart',
            'priority': 7,
            'is_active': True,
            'engagement_score': 0.6
        },
        {
            'id': 'meme-4',
            'image_url': 'https://example.com/meme4.jpg',
            'category': 'monday_career',
            'caption_text': 'Side hustle life: Because one income stream is never enough',
            'alt_text': 'Multiple streams flowing into one bucket',
            'priority': 6,
            'is_active': False,  # Inactive meme
            'engagement_score': 0.5
        }
    ]
    
    created_memes = []
    for meme_data in memes:
        meme = Meme(**meme_data)
        db_session.add(meme)
        created_memes.append(meme)
    
    db_session.commit()
    return created_memes


@pytest.fixture
def sample_user_preferences(db_session, sample_user):
    """Create sample user preferences for testing"""
    prefs = UserMemePreferences(
        id='prefs-1',
        user_id=sample_user.id,
        memes_enabled=True,
        preferred_categories=['monday_career', 'tuesday_health'],
        frequency_setting='daily',
        custom_frequency_days=1,
        last_meme_shown_at=datetime.utcnow() - timedelta(hours=2)
    )
    db_session.add(prefs)
    db_session.commit()
    db_session.refresh(prefs)
    return prefs


@pytest.fixture
def sample_user_history(db_session, sample_user, sample_memes):
    """Create sample user interaction history for testing"""
    history_entries = [
        {
            'id': 'history-1',
            'user_id': sample_user.id,
            'meme_id': sample_memes[0].id,
            'interaction_type': 'view',
            'time_spent_seconds': 15,
            'source_page': 'meme_splash',
            'created_at': datetime.utcnow() - timedelta(days=1)
        },
        {
            'id': 'history-2',
            'user_id': sample_user.id,
            'meme_id': sample_memes[1].id,
            'interaction_type': 'like',
            'time_spent_seconds': 30,
            'source_page': 'meme_splash',
            'created_at': datetime.utcnow() - timedelta(days=2)
        },
        {
            'id': 'history-3',
            'user_id': sample_user.id,
            'meme_id': sample_memes[0].id,
            'interaction_type': 'skip',
            'time_spent_seconds': 5,
            'source_page': 'meme_splash',
            'created_at': datetime.utcnow() - timedelta(days=3)
        }
    ]
    
    created_history = []
    for history_data in history_entries:
        history = UserMemeHistory(**history_data)
        db_session.add(history)
        created_history.append(history)
    
    db_session.commit()
    return created_history


@pytest.fixture
def mock_flask_session():
    """Mock Flask session for testing"""
    with patch('backend.routes.meme_routes.session') as mock_session:
        mock_session.get.return_value = 123  # Default user ID
        yield mock_session


@pytest.fixture
def mock_request():
    """Mock Flask request for testing"""
    with patch('backend.routes.meme_routes.request') as mock_request:
        mock_request.remote_addr = '127.0.0.1'
        mock_request.headers = {
            'User-Agent': 'Mozilla/5.0 (Test Browser)',
            'X-Session-ID': 'test-session-123'
        }
        mock_request.is_json = True
        mock_request.get_json.return_value = {}
        yield mock_request


@pytest.fixture
def test_client(test_app):
    """Create a test client for Flask app"""
    with test_app.test_client() as client:
        with test_app.app_context():
            yield client


@pytest.fixture
def auth_headers():
    """Headers for authenticated requests"""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
    }


@pytest.fixture
def sample_meme_data():
    """Sample meme data for API testing"""
    return {
        'id': 'test-meme-123',
        'image_url': 'https://example.com/test-meme.jpg',
        'caption': 'Test meme caption for API testing',
        'category': 'monday_career',
        'alt_text': 'Test meme alt text',
        'tags': ['test', 'api', 'meme']
    }


@pytest.fixture
def sample_preferences_data():
    """Sample preferences data for API testing"""
    return {
        'memes_enabled': True,
        'preferred_categories': ['monday_career', 'tuesday_health'],
        'frequency_setting': 'daily',
        'custom_frequency_days': 1
    }


@pytest.fixture
def sample_analytics_data():
    """Sample analytics data for API testing"""
    return {
        'meme_id': 'test-meme-123',
        'interaction_type': 'viewed',
        'time_spent_seconds': 15,
        'source_page': 'meme_splash'
    }


@pytest.fixture
def performance_test_data():
    """Data for performance testing"""
    return {
        'num_users': 100,
        'num_memes': 50,
        'num_interactions': 1000,
        'test_duration_seconds': 30
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for testing"""
    with patch('backend.services.meme_service.requests') as mock_requests, \
         patch('backend.services.meme_service.redis') as mock_redis, \
         patch('backend.services.meme_service.logging') as mock_logging:
        
        # Mock requests
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {'status': 'ok'}
        
        # Mock Redis
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = True
        mock_redis.from_url.return_value = mock_redis_client
        
        # Mock logging
        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger
        
        yield {
            'requests': mock_requests,
            'redis': mock_redis,
            'logging': mock_logging
        }


@pytest.fixture
def test_data_directory():
    """Create a temporary directory for test data files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data files
        test_files = {
            'sample_memes.json': json.dumps([
                {
                    'id': 'test-meme-1',
                    'image_url': 'https://example.com/meme1.jpg',
                    'category': 'monday_career',
                    'caption': 'Test meme 1',
                    'alt_text': 'Test meme 1 alt text'
                },
                {
                    'id': 'test-meme-2',
                    'image_url': 'https://example.com/meme2.jpg',
                    'category': 'tuesday_health',
                    'caption': 'Test meme 2',
                    'alt_text': 'Test meme 2 alt text'
                }
            ]),
            'user_preferences.json': json.dumps({
                'memes_enabled': True,
                'preferred_categories': ['monday_career', 'tuesday_health'],
                'frequency_setting': 'daily'
            }),
            'analytics_data.json': json.dumps([
                {
                    'meme_id': 'test-meme-1',
                    'interaction_type': 'viewed',
                    'timestamp': '2024-01-01T00:00:00Z'
                }
            ])
        }
        
        for filename, content in test_files.items():
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
        
        yield temp_dir


@pytest.fixture
def mock_image_processing():
    """Mock image processing functions"""
    with patch('PIL.Image') as mock_pil, \
         patch('cv2.imread') as mock_cv2, \
         patch('backend.services.meme_service.resize_image') as mock_resize:
        
        # Mock PIL Image
        mock_image = Mock()
        mock_image.size = (800, 600)
        mock_image.save.return_value = None
        mock_pil.open.return_value = mock_image
        
        # Mock OpenCV
        mock_cv2.return_value = Mock()
        
        # Mock resize function
        mock_resize.return_value = mock_image
        
        yield {
            'pil': mock_pil,
            'cv2': mock_cv2,
            'resize': mock_resize
        }


# Test data constants
MEME_CATEGORIES = [
    'monday_career', 'tuesday_health', 'wednesday_home',
    'thursday_relationships', 'friday_entertainment',
    'saturday_kids', 'sunday_faith'
]

INTERACTION_TYPES = ['viewed', 'skipped', 'continued', 'liked', 'shared', 'reported']

FREQUENCY_SETTINGS = ['daily', 'weekly', 'disabled', 'custom']

# Edge case data
@pytest.fixture
def edge_case_data():
    """Data for testing edge cases"""
    return {
        'empty_categories': [],
        'all_categories': MEME_CATEGORIES,
        'invalid_category': 'invalid_category',
        'very_long_caption': 'A' * 1000,
        'special_characters': 'Test meme with émojis 🎉 and symbols @#$%',
        'html_injection': '<script>alert("xss")</script>',
        'sql_injection': "'; DROP TABLE memes; --",
        'very_large_image_url': 'https://example.com/' + 'a' * 1000 + '.jpg',
        'negative_priority': -1,
        'zero_priority': 0,
        'very_high_priority': 999999
    }


@pytest.fixture
def load_test_data():
    """Data for load testing"""
    return {
        'concurrent_users': [10, 50, 100, 200],
        'request_rates': [10, 50, 100, 200],  # requests per second
        'test_durations': [30, 60, 120],  # seconds
        'memory_thresholds': {
            'cpu_percent': 80,
            'memory_percent': 85,
            'response_time_ms': 1000
        }
    }


@pytest.fixture
def accessibility_test_data():
    """Data for accessibility testing"""
    return {
        'screen_readers': ['NVDA', 'JAWS', 'VoiceOver'],
        'color_contrast_ratios': [3.0, 4.5, 7.0],
        'font_sizes': ['small', 'medium', 'large'],
        'keyboard_shortcuts': ['Tab', 'Enter', 'Space', 'Escape', 'Arrow keys'],
        'aria_labels': [
            'continue-button',
            'skip-button',
            'opt-out-button',
            'meme-image',
            'meme-caption'
        ]
    }
