"""
Pytest Configuration and Fixtures for Job Recommendation Engine Testing
Provides test data, mock services, and environment setup for comprehensive testing
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    from backend.ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
    from backend.ml.models.resume_parser import AdvancedResumeParser, FieldType, ExperienceLevel
    from backend.ml.models.intelligent_job_matcher import IntelligentJobMatcher, CompanyTier
    from backend.ml.models.job_selection_algorithm import JobSelectionAlgorithm
    HAVE_ML_STACK = True
except Exception:  # pragma: no cover - optional dependency guard (e.g., spacy not installed)
    HAVE_ML_STACK = False
    MingusJobRecommendationEngine = None
    AdvancedResumeParser = None
    IntelligentJobMatcher = None
    JobSelectionAlgorithm = None
    CompanyTier = None
    # Provide minimal stand-ins for enums used in test data when ML stack isn't available
    try:
        from enum import Enum
        class FieldType(Enum):
            DATA_ANALYSIS = "Data Analysis"
            MARKETING = "Marketing"
            SOFTWARE_DEVELOPMENT = "Software Development"
        class ExperienceLevel(Enum):
            ENTRY = "Entry"
            MID = "Mid"
            SENIOR = "Senior"
    except Exception:
        FieldType = None
        ExperienceLevel = None

# Import ML-dependent services lazily inside fixtures to avoid hard dependency at collection time


@pytest.fixture(scope="session")
def mock_data_generator():
    """Provide mock data generator for all tests"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    from tests.test_data_generation import MockDataGenerator
    return MockDataGenerator()


@pytest.fixture(scope="session")
def sample_resumes(mock_data_generator):
    """Provide sample resumes for testing"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    return [
        mock_data_generator.generate_resume(
            field=FieldType.DATA_ANALYSIS,
            experience_level=ExperienceLevel.ENTRY,
            current_salary=55000,
            education='Morehouse College'
        ),
        mock_data_generator.generate_resume(
            field=FieldType.MARKETING,
            experience_level=ExperienceLevel.MID,
            current_salary=75000,
            education='Texas Southern University'
        ),
        mock_data_generator.generate_resume(
            field=FieldType.SOFTWARE_DEVELOPMENT,
            experience_level=ExperienceLevel.SENIOR,
            current_salary=95000,
            education='Howard University'
        )
    ]


@pytest.fixture(scope="session")
def sample_job_postings(mock_data_generator):
    """Provide sample job postings for testing"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    return [
        mock_data_generator.generate_job_posting(
            field=FieldType.DATA_ANALYSIS,
            experience_level='Entry',
            location='Atlanta'
        ),
        mock_data_generator.generate_job_posting(
            field=FieldType.MARKETING,
            experience_level='Mid',
            location='Houston'
        ),
        mock_data_generator.generate_job_posting(
            field=FieldType.SOFTWARE_DEVELOPMENT,
            experience_level='Senior',
            location='Washington DC'
        )
    ]


@pytest.fixture(scope="session")
def target_demographic_data():
    """Provide target demographic data for testing"""
    return {
        'age_range': (25, 35),
        'locations': ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City'],
        'hbcus': [
            'Morehouse College', 'Spelman College', 'Howard University', 
            'Texas Southern University', 'Florida A&M University',
            'North Carolina A&T State University', 'Hampton University'
        ],
        'fields': ['Data Analysis', 'Software Development', 'Project Management', 'Marketing', 'Finance'],
        'experience_levels': ['Entry', 'Mid', 'Senior'],
        'salary_ranges': [(45000, 120000)]
    }


@pytest.fixture(scope="function")
def engine():
    """Provide job recommendation engine instance"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    return MingusJobRecommendationEngine()


@pytest.fixture(scope="function")
def resume_parser():
    """Provide resume parser instance"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    return AdvancedResumeParser()


@pytest.fixture(scope="function")
def job_matcher():
    """Provide job matcher instance"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    return IntelligentJobMatcher()


@pytest.fixture(scope="function")
def job_selector():
    """Provide job selector instance"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    return JobSelectionAlgorithm()


@pytest.fixture(scope="function")
def mock_db_session():
    """Provide mock database session"""
    mock_session = Mock()
    
    # Mock user profile
    mock_user_profile = Mock()
    mock_user_profile.current_salary = 75000
    mock_user_profile.preferred_locations = ['Atlanta', 'Houston']
    mock_user_profile.id = 1
    
    # Mock query chain
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user_profile
    
    return mock_session


@pytest.fixture(scope="function")
def intelligent_job_matching_service(mock_db_session):
    """Provide intelligent job matching service with mock database"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    from backend.services.intelligent_job_matching_service import IntelligentJobMatchingService
    return IntelligentJobMatchingService(mock_db_session)


@pytest.fixture(scope="function")
def career_advancement_service(mock_db_session):
    """Provide career advancement service with mock database"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    from backend.services.career_advancement_service import CareerAdvancementService
    return CareerAdvancementService(mock_db_session)


@pytest.fixture(scope="function")
def resume_analysis_service(mock_db_session):
    """Provide resume analysis service with mock database"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    from backend.services.resume_analysis_service import ResumeAnalysisService
    return ResumeAnalysisService(mock_db_session)


@pytest.fixture(scope="function")
def mock_api_responses():
    """Provide mock API responses for testing"""
    return {
        'job_search_success': {
            'jobs': [
                {
                    'id': 'job_1',
                    'title': 'Senior Data Analyst',
                    'company': 'TechCorp',
                    'location': 'Atlanta',
                    'salary_range': {'min': 90000, 'max': 110000, 'midpoint': 100000},
                    'skills': ['Python', 'SQL', 'Tableau'],
                    'experience_level': 'Senior',
                    'remote_work': True
                },
                {
                    'id': 'job_2',
                    'title': 'Data Scientist',
                    'company': 'DataCorp',
                    'location': 'Houston',
                    'salary_range': {'min': 95000, 'max': 120000, 'midpoint': 107500},
                    'skills': ['Python', 'Machine Learning', 'SQL'],
                    'experience_level': 'Senior',
                    'remote_work': False
                }
            ],
            'total_count': 2
        },
        'job_search_empty': {
            'jobs': [],
            'total_count': 0
        },
        'job_search_error': {
            'error': 'API rate limit exceeded',
            'status_code': 429
        }
    }


@pytest.fixture(scope="function")
def mock_database_data():
    """Provide mock database data for testing"""
    return {
        'user_profiles': [
            {
                'id': 1,
                'current_salary': 75000,
                'preferred_locations': ['Atlanta', 'Houston'],
                'field': 'Data Analysis',
                'experience_level': 'Mid'
            },
            {
                'id': 2,
                'current_salary': 65000,
                'preferred_locations': ['Washington DC'],
                'field': 'Marketing',
                'experience_level': 'Entry'
            },
            {
                'id': 3,
                'current_salary': 95000,
                'preferred_locations': ['New York City', 'Atlanta'],
                'field': 'Software Development',
                'experience_level': 'Senior'
            }
        ],
        'resume_analyses': [
            {
                'user_id': 1,
                'field_analysis': {
                    'primary_field': 'Data Analysis',
                    'confidence_score': 0.85
                },
                'experience_analysis': {
                    'level': 'Mid',
                    'total_years': 4.5
                },
                'skills_analysis': {
                    'technical_skills': {'Python': 0.8, 'SQL': 0.9, 'Tableau': 0.7},
                    'business_skills': {'Project Management': 0.6, 'Communication': 0.8}
                }
            }
        ],
        'job_recommendations': [
            {
                'user_id': 1,
                'recommendations': [
                    {
                        'job_id': 'job_1',
                        'score': 0.85,
                        'salary_increase': 0.25
                    },
                    {
                        'job_id': 'job_2',
                        'score': 0.78,
                        'salary_increase': 0.30
                    }
                ]
            }
        ]
    }


@pytest.fixture(scope="function")
def performance_targets():
    """Provide performance targets for testing"""
    return {
        'resume_processing': 2.0,      # 2 seconds max
        'income_comparison': 1.0,      # 1 second max
        'job_search': 5.0,             # 5 seconds max
        'job_selection': 2.0,          # 2 seconds max
        'total_workflow': 8.0,         # 8 seconds max
        'memory_usage': 100,           # 100MB max
        'concurrent_users': 10,        # 10 concurrent users
        'cache_hit_rate': 0.7,        # 70% cache hit rate
        'error_rate': 0.05            # 5% error rate max
    }


@pytest.fixture(scope="function")
def test_scenarios(mock_data_generator):
    """Provide comprehensive test scenarios"""
    return mock_data_generator.generate_test_scenarios(5)


@pytest.fixture(scope="function")
def demographic_test_data(mock_data_generator):
    """Provide demographic-specific test data"""
    return mock_data_generator.generate_demographic_test_data()


@pytest.fixture(scope="function")
def mock_flask_app():
    """Provide mock Flask app for API testing"""
    from backend.app import create_app
    
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    return app


@pytest.fixture(scope="function")
def flask_client(mock_flask_app):
    """Provide Flask test client"""
    return mock_flask_app.test_client()


@pytest.fixture(scope="function")
def auth_headers():
    """Provide authentication headers for API testing"""
    return {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope="function")
def mock_external_apis():
    """Provide mock external API responses"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        # Mock job search API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'jobs': [
                {
                    'id': 'job_1',
                    'title': 'Senior Data Analyst',
                    'company': 'TechCorp',
                    'location': 'Atlanta',
                    'salary': {'min': 90000, 'max': 110000},
                    'skills': ['Python', 'SQL', 'Tableau']
                }
            ]
        }
        
        # Mock salary data API
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'salary_data': {
                'median': 85000,
                'percentile_25': 75000,
                'percentile_75': 95000
            }
        }
        
        yield {
            'get': mock_get,
            'post': mock_post
        }


@pytest.fixture(scope="function")
def mock_cache():
    """Provide mock cache for testing"""
    cache = {}
    
    def get(key):
        return cache.get(key)
    
    def set(key, value, ttl=None):
        cache[key] = value
    
    def delete(key):
        if key in cache:
            del cache[key]
    
    def clear():
        cache.clear()
    
    return {
        'get': get,
        'set': set,
        'delete': delete,
        'clear': clear,
        'data': cache
    }


@pytest.fixture(scope="function")
def mock_logger():
    """Provide mock logger for testing"""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


@pytest.fixture(scope="function")
def temp_test_file():
    """Provide temporary test file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        yield f.name
    # Clean up
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture(scope="function")
def mock_metrics_collector():
    """Provide mock metrics collector"""
    metrics = {
        'processing_times': [],
        'memory_usage': [],
        'error_counts': {},
        'success_counts': {},
        'cache_hits': 0,
        'cache_misses': 0
    }
    
    def record_processing_time(component, time_taken):
        metrics['processing_times'].append({
            'component': component,
            'time': time_taken,
            'timestamp': datetime.utcnow()
        })
    
    def record_memory_usage(usage_mb):
        metrics['memory_usage'].append({
            'usage': usage_mb,
            'timestamp': datetime.utcnow()
        })
    
    def record_error(error_type):
        metrics['error_counts'][error_type] = metrics['error_counts'].get(error_type, 0) + 1
    
    def record_success(operation_type):
        metrics['success_counts'][operation_type] = metrics['success_counts'].get(operation_type, 0) + 1
    
    def record_cache_hit():
        metrics['cache_hits'] += 1
    
    def record_cache_miss():
        metrics['cache_misses'] += 1
    
    def get_metrics():
        return metrics.copy()
    
    return {
        'record_processing_time': record_processing_time,
        'record_memory_usage': record_memory_usage,
        'record_error': record_error,
        'record_success': record_success,
        'record_cache_hit': record_cache_hit,
        'record_cache_miss': record_cache_miss,
        'get_metrics': get_metrics,
        'metrics': metrics
    }


@pytest.fixture(scope="function")
def mock_user_session():
    """Provide mock user session data"""
    return {
        'user_id': 1,
        'session_id': 'test_session_123',
        'resume_text': 'Sample resume text for testing',
        'current_salary': 75000,
        'target_locations': ['Atlanta', 'Houston'],
        'risk_preference': 'balanced',
        'created_at': datetime.utcnow(),
        'status': 'active'
    }


@pytest.fixture(scope="function")
def mock_progress_tracker():
    """Provide mock progress tracker"""
    progress_data = {
        'session_id': 'test_session_123',
        'steps': {
            'resume_processing': {'status': 'pending', 'progress': 0},
            'income_analysis': {'status': 'pending', 'progress': 0},
            'job_search': {'status': 'pending', 'progress': 0},
            'job_selection': {'status': 'pending', 'progress': 0},
            'action_planning': {'status': 'pending', 'progress': 0}
        },
        'overall_progress': 0,
        'status': 'processing'
    }
    
    def update_step(step_name, status, progress):
        if step_name in progress_data['steps']:
            progress_data['steps'][step_name] = {
                'status': status,
                'progress': progress
            }
            # Update overall progress
            total_progress = sum(step['progress'] for step in progress_data['steps'].values())
            progress_data['overall_progress'] = total_progress / len(progress_data['steps'])
    
    def get_progress():
        return progress_data.copy()
    
    def reset():
        for step in progress_data['steps']:
            progress_data['steps'][step] = {'status': 'pending', 'progress': 0}
        progress_data['overall_progress'] = 0
        progress_data['status'] = 'processing'
    
    return {
        'update_step': update_step,
        'get_progress': get_progress,
        'reset': reset,
        'data': progress_data
    }


@pytest.fixture(scope="function")
def mock_error_handler():
    """Provide mock error handler"""
    errors = []
    
    def handle_error(error_type, error_message, context=None):
        errors.append({
            'type': error_type,
            'message': error_message,
            'context': context,
            'timestamp': datetime.utcnow()
        })
    
    def get_errors():
        return errors.copy()
    
    def clear_errors():
        errors.clear()
    
    return {
        'handle_error': handle_error,
        'get_errors': get_errors,
        'clear_errors': clear_errors,
        'errors': errors
    }


@pytest.fixture(scope="function")
def mock_validation_rules():
    """Provide mock validation rules"""
    return {
        'resume': {
            'min_length': 100,
            'max_length': 10000,
            'required_sections': ['experience', 'education', 'skills']
        },
        'salary': {
            'min_value': 20000,
            'max_value': 500000,
            'required': True
        },
        'locations': {
            'max_count': 5,
            'valid_locations': ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
        },
        'risk_preference': {
            'valid_values': ['conservative', 'balanced', 'aggressive'],
            'default': 'balanced'
        }
    }


@pytest.fixture(scope="function")
def mock_config():
    """Provide mock configuration"""
    return {
        'app': {
            'name': 'Mingus Job Recommendation Engine',
            'version': '1.0.0',
            'environment': 'testing'
        },
        'database': {
            'url': 'sqlite:///test.db',
            'pool_size': 5,
            'max_overflow': 10
        },
        'cache': {
            'type': 'memory',
            'ttl': 3600,
            'max_size': 1000
        },
        'api': {
            'rate_limit': 100,
            'timeout': 30,
            'retry_attempts': 3
        },
        'performance': {
            'max_processing_time': 8.0,
            'max_memory_usage': 100,
            'concurrent_users': 10
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for the test suite"""
    # Add custom markers
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
        "markers", "user_acceptance: mark test as a user acceptance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if "test_job_recommendation_engine" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_integration_workflow" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_performance_benchmarks" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "test_user_scenarios" in item.nodeid:
            item.add_marker(pytest.mark.user_acceptance)
        elif "test_data_generation" in item.nodeid:
            item.add_marker(pytest.mark.unit)


# Test data utilities
def create_test_resume(field: FieldType, experience_level: ExperienceLevel, 
                      education: str = "Morehouse College") -> str:
    """Create a test resume with specified parameters"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    from tests.test_data_generation import MockDataGenerator
    generator = MockDataGenerator()
    resume_data = generator.generate_resume(field, experience_level, education=education)
    return resume_data.text


def create_test_job_posting(field: FieldType, experience_level: str, 
                          location: str = "Atlanta") -> Dict[str, Any]:
    """Create a test job posting with specified parameters"""
    if not HAVE_ML_STACK:
        pytest.skip("ML stack not available (optional dependency)")
    from tests.test_data_generation import MockDataGenerator
    generator = MockDataGenerator()
    job_data = generator.generate_job_posting(field, experience_level, location=location)
    return {
        'title': job_data.title,
        'company': job_data.company,
        'location': job_data.location,
        'salary_range': job_data.salary_range,
        'skills': job_data.skills,
        'experience_level': job_data.experience_level,
        'company_tier': job_data.company_tier.value,
        'remote_work': job_data.remote_work
    }


def assert_performance_target(actual_time: float, target_time: float, 
                            tolerance: float = 1.5, component: str = "component"):
    """Assert that performance meets target with tolerance"""
    assert actual_time <= target_time * tolerance, \
        f"{component} took {actual_time:.3f}s, exceeding target of {target_time:.3f}s"


def assert_recommendation_quality(recommendations: List[Dict], 
                                min_count: int = 1, 
                                min_salary_increase: float = 0.15):
    """Assert that recommendations meet quality criteria"""
    assert len(recommendations) >= min_count, \
        f"Expected at least {min_count} recommendations, got {len(recommendations)}"
    
    for rec in recommendations:
        if 'salary_increase' in rec:
            assert rec['salary_increase'] >= min_salary_increase, \
                f"Salary increase {rec['salary_increase']:.2%} below minimum {min_salary_increase:.2%}"


def assert_demographic_appropriateness(result: Dict, target_demographic: Dict):
    """Assert that results are appropriate for target demographic"""
    # Check locations
    if 'career_strategy' in result:
        strategy = result['career_strategy']
        for tier in ['conservative', 'optimal', 'stretch']:
            opportunity = getattr(strategy, f'{tier}_opportunity', None)
            if opportunity and hasattr(opportunity, 'job'):
                job_location = opportunity.job.location
                assert job_location in target_demographic['locations'], \
                    f"Job location {job_location} not in target locations"


def create_mock_user_profile(user_id: int, salary: int, locations: List[str]) -> Mock:
    """Create a mock user profile for testing"""
    profile = Mock()
    profile.id = user_id
    profile.current_salary = salary
    profile.preferred_locations = locations
    profile.field = 'Data Analysis'
    profile.experience_level = 'Mid'
    return profile


def create_mock_job_score(job_data: Dict, overall_score: float = 0.8) -> Mock:
    """Create a mock job score for testing"""
    job_score = Mock()
    job_score.job = Mock()
    job_score.job.title = job_data['title']
    job_score.job.company = job_data['company']
    job_score.job.location = job_data['location']
    job_score.job.salary_range = Mock()
    job_score.job.salary_range.midpoint = job_data['salary_range']['midpoint']
    job_score.overall_score = overall_score
    job_score.salary_improvement_score = 0.8
    job_score.skills_alignment_score = 0.7
    return job_score 


@pytest.fixture(scope="function")
def user_experience_service(mock_db_session, mock_audit_service):
    """Create a UserExperienceService instance for testing"""
    from backend.frontend.user_experience import UserExperienceService
    return UserExperienceService(mock_db_session, mock_audit_service)


@pytest.fixture(scope="function")
def mock_audit_service():
    """Create a mock audit service for testing"""
    audit_service = Mock()
    audit_service.log_event = Mock()
    audit_service.track_user_action = Mock()
    audit_service.record_error = Mock()
    return audit_service

# tests/conftest.py
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app import create_app, db
from backend.models.articles import (
    Article, UserAssessmentScores, UserArticleProgress,
    ArticleFolder, ArticleBookmark, ArticleAnalytics
)
from backend.models.users import User

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'ENABLE_ARTICLE_LIBRARY': True,
        'ENABLE_AI_RECOMMENDATIONS': True,
        'ENABLE_CULTURAL_PERSONALIZATION': True,
        'ENABLE_ADVANCED_SEARCH': True,
        'ENABLE_ANALYTICS': True,
        'CACHE_TYPE': 'simple',
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'rpc://',
        'OPENAI_API_KEY': 'test-key',
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def admin_user(app):
    """Create an admin test user"""
    with app.app_context():
        user = User(
            email='admin@example.com',
            username='adminuser',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def auth_headers(test_user, client):
    """Get authentication headers for test user"""
    # Login to get JWT token
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_headers(admin_user, client):
    """Get authentication headers for admin user"""
    response = client.post('/api/auth/login', json={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    assert response.status_code == 200
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def sample_articles(app):
    """Create sample articles for testing"""
    with app.app_context():
        articles = []
        
        # Create articles for different phases and difficulties
        article_data = [
            {
                'title': 'Career Advancement Strategies for Professionals',
                'content': 'This article discusses various strategies for advancing your career in today\'s competitive market. It covers networking, skill development, and strategic positioning.',
                'url': 'https://example.com/career-advancement',
                'source': 'example.com',
                'published_date': datetime.now() - timedelta(days=5),
                'category': 'Career Development',
                'phase': 'BE',
                'difficulty': 'Intermediate',
                'cultural_relevance_score': 8.5,
                'quality_score': 0.85,
                'readability_score': 7.2,
                'summary': 'Comprehensive guide to career advancement strategies',
                'tags': ['career', 'advancement', 'professional development']
            },
            {
                'title': 'Building Wealth Through Smart Investments',
                'content': 'Learn how to build wealth through strategic investment decisions. This guide covers stocks, bonds, real estate, and alternative investments.',
                'url': 'https://example.com/investment-guide',
                'source': 'example.com',
                'published_date': datetime.now() - timedelta(days=3),
                'category': 'Financial Planning',
                'phase': 'HAVE',
                'difficulty': 'Advanced',
                'cultural_relevance_score': 9.0,
                'quality_score': 0.92,
                'readability_score': 8.1,
                'summary': 'Advanced investment strategies for wealth building',
                'tags': ['investment', 'wealth', 'financial planning']
            },
            {
                'title': 'Effective Goal Setting and Achievement',
                'content': 'Master the art of setting and achieving meaningful goals. This beginner-friendly guide provides practical steps for success.',
                'url': 'https://example.com/goal-setting',
                'source': 'example.com',
                'published_date': datetime.now() - timedelta(days=1),
                'category': 'Personal Development',
                'phase': 'DO',
                'difficulty': 'Beginner',
                'cultural_relevance_score': 7.8,
                'quality_score': 0.78,
                'readability_score': 6.5,
                'summary': 'Beginner-friendly guide to goal setting',
                'tags': ['goals', 'achievement', 'personal development']
            },
            {
                'title': 'Mindfulness and Mental Health in the Workplace',
                'content': 'Explore mindfulness techniques and mental health strategies for maintaining well-being in professional environments.',
                'url': 'https://example.com/mindfulness-workplace',
                'source': 'example.com',
                'published_date': datetime.now() - timedelta(days=2),
                'category': 'Mental Health',
                'phase': 'BE',
                'difficulty': 'Beginner',
                'cultural_relevance_score': 8.2,
                'quality_score': 0.88,
                'readability_score': 6.8,
                'summary': 'Mindfulness practices for workplace mental health',
                'tags': ['mindfulness', 'mental health', 'workplace']
            },
            {
                'title': 'Advanced Negotiation Techniques',
                'content': 'Master advanced negotiation strategies for business and personal success. Learn psychological tactics and strategic approaches.',
                'url': 'https://example.com/negotiation-techniques',
                'source': 'example.com',
                'published_date': datetime.now() - timedelta(days=4),
                'category': 'Business Skills',
                'phase': 'DO',
                'difficulty': 'Advanced',
                'cultural_relevance_score': 8.8,
                'quality_score': 0.90,
                'readability_score': 7.8,
                'summary': 'Advanced negotiation strategies and techniques',
                'tags': ['negotiation', 'business', 'communication']
            }
        ]
        
        for data in article_data:
            article = Article(**data)
            db.session.add(article)
            articles.append(article)
        
        db.session.commit()
        return articles

@pytest.fixture
def sample_assessment(app, test_user):
    """Create a sample assessment for the test user"""
    with app.app_context():
        assessment = UserAssessmentScores(
            user_id=test_user.id,
            be_score=75,
            do_score=65,
            have_score=45,
            assessment_date=datetime.now()
        )
        db.session.add(assessment)
        db.session.commit()
        return assessment

@pytest.fixture
def sample_progress(app, test_user, sample_articles):
    """Create sample reading progress for the test user"""
    with app.app_context():
        progress_entries = []
        
        # Create progress for first article
        progress1 = UserArticleProgress(
            user_id=test_user.id,
            article_id=sample_articles[0].id,
            progress_percentage=100,
            completed_at=datetime.now() - timedelta(days=1),
            time_spent_reading=1800  # 30 minutes
        )
        db.session.add(progress1)
        progress_entries.append(progress1)
        
        # Create progress for second article
        progress2 = UserArticleProgress(
            user_id=test_user.id,
            article_id=sample_articles[1].id,
            progress_percentage=50,
            started_at=datetime.now() - timedelta(hours=2),
            time_spent_reading=900  # 15 minutes
        )
        db.session.add(progress2)
        progress_entries.append(progress2)
        
        db.session.commit()
        return progress_entries

@pytest.fixture
def sample_folders(app, test_user):
    """Create sample folders for the test user"""
    with app.app_context():
        folders = []
        
        folder1 = ArticleFolder(
            user_id=test_user.id,
            name='Career Development',
            description='Articles about career advancement and professional growth'
        )
        db.session.add(folder1)
        folders.append(folder1)
        
        folder2 = ArticleFolder(
            user_id=test_user.id,
            name='Financial Planning',
            description='Articles about money management and investment'
        )
        db.session.add(folder2)
        folders.append(folder2)
        
        db.session.commit()
        return folders

@pytest.fixture
def sample_bookmarks(app, test_user, sample_articles):
    """Create sample bookmarks for the test user"""
    with app.app_context():
        bookmarks = []
        
        bookmark1 = ArticleBookmark(
            user_id=test_user.id,
            article_id=sample_articles[0].id,
            created_at=datetime.now() - timedelta(days=1)
        )
        db.session.add(bookmark1)
        bookmarks.append(bookmark1)
        
        bookmark2 = ArticleBookmark(
            user_id=test_user.id,
            article_id=sample_articles[1].id,
            created_at=datetime.now() - timedelta(hours=3)
        )
        db.session.add(bookmark2)
        bookmarks.append(bookmark2)
        
        db.session.commit()
        return bookmarks

@pytest.fixture
def sample_analytics(app, test_user, sample_articles):
    """Create sample analytics data"""
    with app.app_context():
        analytics = []
        
        # Article view analytics
        view1 = ArticleAnalytics(
            article_id=sample_articles[0].id,
            user_id=test_user.id,
            action='view',
            timestamp=datetime.now() - timedelta(hours=1)
        )
        db.session.add(view1)
        analytics.append(view1)
        
        # Article share analytics
        share1 = ArticleAnalytics(
            article_id=sample_articles[0].id,
            user_id=test_user.id,
            action='share',
            platform='twitter',
            timestamp=datetime.now() - timedelta(hours=2)
        )
        db.session.add(share1)
        analytics.append(share1)
        
        db.session.commit()
        return analytics

@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    with patch('backend.services.ai_classifier.openai.ChatCompletion.create') as mock:
        mock.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content=json.dumps({
                            'phase': 'BE',
                            'difficulty': 'Intermediate',
                            'cultural_relevance_score': 8.5,
                            'quality_score': 0.85,
                            'summary': 'Test summary',
                            'tags': ['test', 'article']
                        })
                    )
                )
            ]
        )
        yield mock

@pytest.fixture
def mock_celery():
    """Mock Celery task execution"""
    with patch('backend.celery_app.celery.delay') as mock:
        mock.return_value = Mock(id='test-task-id')
        yield mock

@pytest.fixture
def mock_redis():
    """Mock Redis cache operations"""
    with patch('backend.services.cache_service.redis_client') as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = 1
        yield mock

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch operations"""
    with patch('backend.services.search_service.elasticsearch') as mock:
        mock.search.return_value = {
            'hits': {
                'total': {'value': 1},
                'hits': [
                    {
                        '_source': {
                            'id': 1,
                            'title': 'Test Article',
                            'content': 'Test content'
                        }
                    }
                ]
            }
        }
        yield mock

@pytest.fixture
def test_database(app):
    """Provide test database session"""
    with app.app_context():
        yield db.session

@pytest.fixture(autouse=True)
def cleanup_database(app):
    """Clean up database after each test"""
    yield
    with app.app_context():
        db.session.rollback()
        # Clean up any test data that might have been created
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

# Test configuration
def pytest_configure(config):
    """Configure pytest for the test suite"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        if "test_database" in item.nodeid:
            item.add_marker(pytest.mark.database)