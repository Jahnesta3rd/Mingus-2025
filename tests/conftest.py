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

from backend.ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
from backend.ml.models.resume_parser import AdvancedResumeParser, FieldType, ExperienceLevel
from backend.ml.models.intelligent_job_matcher import IntelligentJobMatcher, CompanyTier
from backend.ml.models.job_selection_algorithm import JobSelectionAlgorithm
from backend.services.intelligent_job_matching_service import IntelligentJobMatchingService
from backend.services.career_advancement_service import CareerAdvancementService
from backend.services.resume_analysis_service import ResumeAnalysisService
from tests.test_data_generation import MockDataGenerator


@pytest.fixture(scope="session")
def mock_data_generator():
    """Provide mock data generator for all tests"""
    return MockDataGenerator()


@pytest.fixture(scope="session")
def sample_resumes(mock_data_generator):
    """Provide sample resumes for testing"""
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
    return MingusJobRecommendationEngine()


@pytest.fixture(scope="function")
def resume_parser():
    """Provide resume parser instance"""
    return AdvancedResumeParser()


@pytest.fixture(scope="function")
def job_matcher():
    """Provide job matcher instance"""
    return IntelligentJobMatcher()


@pytest.fixture(scope="function")
def job_selector():
    """Provide job selector instance"""
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
    return IntelligentJobMatchingService(mock_db_session)


@pytest.fixture(scope="function")
def career_advancement_service(mock_db_session):
    """Provide career advancement service with mock database"""
    return CareerAdvancementService(mock_db_session)


@pytest.fixture(scope="function")
def resume_analysis_service(mock_db_session):
    """Provide resume analysis service with mock database"""
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
    generator = MockDataGenerator()
    resume_data = generator.generate_resume(field, experience_level, education=education)
    return resume_data.text


def create_test_job_posting(field: FieldType, experience_level: str, 
                          location: str = "Atlanta") -> Dict[str, Any]:
    """Create a test job posting with specified parameters"""
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