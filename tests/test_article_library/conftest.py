"""
Pytest Configuration and Fixtures for Article Library Testing Suite

This module provides shared fixtures and configuration for all article library tests.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Flask and database imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Application imports
from backend.app_factory import create_app
from backend.models.articles import (
    Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
    UserArticleProgress, UserAssessmentScores, ArticleRecommendation, ArticleAnalytics
)
from backend.models.user import User, UserProfile
from backend.services.article_search import ArticleSearchService

# Test data imports
from .fixtures.test_data import (
    SAMPLE_ARTICLES, SAMPLE_USERS, SAMPLE_ASSESSMENT_SCORES,
    SAMPLE_EMAIL_DATA, SAMPLE_DOMAIN_DATA
)

@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing"""
    app = create_app('testing')
    
    # Configure test database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['CACHE_TYPE'] = 'simple'
    
    return app

@pytest.fixture(scope="session")
def db(app):
    """Create database instance"""
    db = SQLAlchemy(app)
    
    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()

@pytest.fixture(scope="function")
def db_session(db):
    """Create database session for each test"""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.create_scoped_session(
        options={"bind": connection, "binds": {}}
    )
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture(scope="function")
def client(app):
    """Create test client"""
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="function")
def auth_headers():
    """Authentication headers for API tests"""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test_token_123'
    }

@pytest.fixture(scope="function")
def mock_user_session():
    """Mock user session data"""
    return {
        'user_id': 'test-user-123',
        'email': 'test@example.com',
        'full_name': 'Test User',
        'subscription_tier': 'premium'
    }

@pytest.fixture(scope="function")
def sample_articles(db_session):
    """Create sample articles in database"""
    articles = []
    
    for article_data in SAMPLE_ARTICLES:
        article = Article(**article_data)
        db_session.add(article)
        articles.append(article)
    
    db_session.commit()
    return articles

@pytest.fixture(scope="function")
def sample_users(db_session):
    """Create sample users in database"""
    users = []
    
    for user_data in SAMPLE_USERS:
        user = User(**user_data)
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    return users

@pytest.fixture(scope="function")
def sample_assessment_scores(db_session, sample_users):
    """Create sample assessment scores"""
    scores = []
    
    for score_data in SAMPLE_ASSESSMENT_SCORES:
        score = UserAssessmentScores(**score_data)
        db_session.add(score)
        scores.append(score)
    
    db_session.commit()
    return scores

@pytest.fixture(scope="function")
def mock_email_extractor():
    """Mock email extractor service"""
    with patch('scripts.step1_mac_email_extractor.EmailExtractor') as mock:
        extractor = mock.return_value
        extractor.extract_urls_from_email_text.return_value = [
            'https://nerdwallet.com/article/careers/salary-negotiation',
            'https://blackenterprise.com/wealth-building-strategies'
        ]
        extractor.filter_financial_urls.return_value = [
            'https://nerdwallet.com/article/careers/salary-negotiation',
            'https://blackenterprise.com/wealth-building-strategies'
        ]
        yield extractor

@pytest.fixture(scope="function")
def mock_domain_analyzer():
    """Mock domain analyzer service"""
    with patch('scripts.step2_domain_intelligence.DomainAnalyzer') as mock:
        analyzer = mock.return_value
        analyzer.analyze_domains.return_value = {
            'total_urls': 10,
            'unique_domains': 5,
            'top_domain': {'domain': 'nerdwallet.com', 'count': 4}
        }
        yield analyzer

@pytest.fixture(scope="function")
def mock_ai_classifier():
    """Mock AI classification service"""
    with patch('scripts.step4_article_classifier.ArticleClassifier') as mock:
        classifier = mock.return_value
        classifier.classify_article.return_value = {
            'primary_phase': 'DO',
            'difficulty_level': 'Intermediate',
            'confidence_score': 0.85,
            'key_topics': ['salary negotiation', 'career advancement'],
            'learning_objectives': ['Learn negotiation strategies', 'Understand market rates']
        }
        yield classifier

@pytest.fixture(scope="function")
def mock_article_scraper():
    """Mock article scraping service"""
    with patch('scripts.step3_article_scraper.ArticleScraper') as mock:
        scraper = mock.return_value
        scraper.scrape_article.return_value = {
            'title': 'How to Negotiate Your Salary',
            'content': 'Comprehensive guide to salary negotiation...',
            'author': 'Financial Expert',
            'publish_date': '2024-03-15',
            'word_count': 1500
        }
        yield scraper

@pytest.fixture(scope="function")
def mock_search_service():
    """Mock article search service"""
    with patch('backend.services.article_search.ArticleSearchService') as mock:
        service = mock.return_value
        service.search_articles.return_value = {
            'articles': SAMPLE_ARTICLES[:3],
            'total_count': 3,
            'search_time_ms': 150
        }
        service.get_recommendations.return_value = SAMPLE_ARTICLES[:5]
        yield service

@pytest.fixture(scope="function")
def mock_cache():
    """Mock cache service"""
    with patch('flask_caching.Cache') as mock:
        cache = mock.return_value
        cache.get.return_value = None
        cache.set.return_value = True
        cache.delete.return_value = True
        yield cache

@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis connection"""
    with patch('redis.Redis') as mock:
        redis_client = mock.return_value
        redis_client.get.return_value = None
        redis_client.set.return_value = True
        redis_client.delete.return_value = True
        yield redis_client

@pytest.fixture(scope="function")
def performance_benchmark():
    """Performance benchmarking fixture"""
    import time
    
    class PerformanceBenchmark:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.end_time - self.start_time
        
        def assert_faster_than(self, max_seconds):
            duration = self.stop()
            assert duration < max_seconds, f"Operation took {duration:.3f}s, expected < {max_seconds}s"
    
    return PerformanceBenchmark()

@pytest.fixture(scope="function")
def security_validator():
    """Security validation fixture"""
    class SecurityValidator:
        def validate_input_sanitization(self, input_data):
            """Validate input sanitization"""
            dangerous_patterns = [
                '<script>', 'javascript:', 'onerror=', 'onload=',
                'union select', 'drop table', 'delete from'
            ]
            
            for pattern in dangerous_patterns:
                assert pattern.lower() not in str(input_data).lower(), \
                    f"Potentially dangerous input detected: {pattern}"
        
        def validate_authentication_required(self, endpoint, client):
            """Validate authentication is required"""
            response = client.get(endpoint)
            assert response.status_code in [401, 403], \
                f"Endpoint {endpoint} should require authentication"
        
        def validate_authorization_checks(self, user_id, resource_owner_id):
            """Validate authorization checks"""
            assert user_id == resource_owner_id, \
                "User should only access their own resources"
    
    return SecurityValidator()

# Test data fixtures
@pytest.fixture(scope="session")
def test_article_data():
    """Test article data for various scenarios"""
    return {
        'be_article': {
            'url': 'https://example.com/mindset-article',
            'title': 'Building a Wealth Mindset',
            'content': 'Content about developing the right mindset...',
            'primary_phase': 'BE',
            'difficulty_level': 'Beginner',
            'demographic_relevance': 9,
            'cultural_sensitivity': 8
        },
        'do_article': {
            'url': 'https://example.com/action-article',
            'title': 'Take Action: Investment Strategies',
            'content': 'Content about taking action...',
            'primary_phase': 'DO',
            'difficulty_level': 'Intermediate',
            'demographic_relevance': 8,
            'cultural_sensitivity': 7
        },
        'have_article': {
            'url': 'https://example.com/wealth-article',
            'title': 'Building Generational Wealth',
            'content': 'Content about building wealth...',
            'primary_phase': 'HAVE',
            'difficulty_level': 'Advanced',
            'demographic_relevance': 9,
            'cultural_sensitivity': 9
        }
    }

@pytest.fixture(scope="session")
def test_user_data():
    """Test user data for various scenarios"""
    return {
        'beginner_user': {
            'email': 'beginner@example.com',
            'full_name': 'Beginner User',
            'subscription_tier': 'free',
            'assessment_scores': {'be_score': 3, 'do_score': 2, 'have_score': 1}
        },
        'intermediate_user': {
            'email': 'intermediate@example.com',
            'full_name': 'Intermediate User',
            'subscription_tier': 'premium',
            'assessment_scores': {'be_score': 7, 'do_score': 6, 'have_score': 5}
        },
        'advanced_user': {
            'email': 'advanced@example.com',
            'full_name': 'Advanced User',
            'subscription_tier': 'enterprise',
            'assessment_scores': {'be_score': 9, 'do_score': 8, 'have_score': 9}
        }
    }

# Configuration for different test types
def pytest_configure(config):
    """Configure pytest for article library testing"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "frontend: mark test as a frontend test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as a database test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection for different environments"""
    for item in items:
        # Mark slow tests
        if "performance" in item.nodeid or "e2e" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark API tests
        if "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
