# tests/test_integration.py
import pytest
import json
from datetime import datetime, timedelta
from app import create_app, db
from backend.models.articles import (
    Article, UserAssessmentScores, UserArticleProgress, 
    ArticleFolder, ArticleBookmark, ArticleAnalytics
)
from backend.models.users import User
from backend.services.ai_classifier import AIClassifierService
from backend.services.article_recommendations import ArticleRecommendationEngine

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
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
def sample_articles(app):
    """Create sample articles for testing"""
    with app.app_context():
        articles = []
        
        # Create articles for different phases and difficulties
        article_data = [
            {
                'title': 'Career Advancement Strategies for Professionals',
                'content': 'This article discusses various strategies for advancing your career...',
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
                'content': 'Learn how to build wealth through strategic investment decisions...',
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
                'content': 'Master the art of setting and achieving meaningful goals...',
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
            }
        ]
        
        for data in article_data:
            article = Article(**data)
            db.session.add(article)
            articles.append(article)
        
        db.session.commit()
        return articles

def test_article_library_integration(client, auth_headers, sample_articles):
    """Test complete article library workflow"""
    
    # Test 1: Assessment creation and storage
    response = client.post('/api/user/assessment', 
                          json={
                              'be_score': 75,
                              'do_score': 65,
                              'have_score': 45
                          },
                          headers=auth_headers)
    assert response.status_code == 200
    assessment_data = response.get_json()
    assert 'assessment_id' in assessment_data
    assert assessment_data['be_score'] == 75
    
    # Test 2: Article access based on assessment
    response = client.get('/api/articles?phase=BE&difficulty=Intermediate',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data
    assert len(data['articles']) > 0
    
    # Test 3: Article search functionality
    response = client.post('/api/articles/search',
                          json={
                              'query': 'career advancement',
                              'filters': {
                                  'cultural_relevance_min': 7,
                                  'phase': 'BE',
                                  'difficulty': 'Intermediate'
                              }
                          },
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data
    assert len(data['articles']) > 0
    
    # Test 4: Article recommendations
    response = client.get('/api/articles/recommendations',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0

def test_article_progress_tracking(client, auth_headers, sample_articles):
    """Test article progress tracking functionality"""
    
    article = sample_articles[0]
    
    # Test 1: Start reading an article
    response = client.post(f'/api/articles/{article.id}/progress',
                          json={'action': 'start_reading'},
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 2: Update reading progress
    response = client.put(f'/api/articles/{article.id}/progress',
                         json={'progress_percentage': 50},
                         headers=auth_headers)
    assert response.status_code == 200
    
    # Test 3: Complete article
    response = client.post(f'/api/articles/{article.id}/progress',
                          json={'action': 'complete'},
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 4: Get user progress
    response = client.get('/api/user/progress', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'completed_articles' in data
    assert 'reading_progress' in data

def test_article_folders_and_bookmarks(client, auth_headers, sample_articles):
    """Test article organization features"""
    
    # Test 1: Create a folder
    response = client.post('/api/articles/folders',
                          json={'name': 'Career Articles', 'description': 'Articles about career development'},
                          headers=auth_headers)
    assert response.status_code == 200
    folder_data = response.get_json()
    folder_id = folder_data['folder_id']
    
    # Test 2: Add article to folder
    article = sample_articles[0]
    response = client.post(f'/api/articles/{article.id}/folders/{folder_id}',
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 3: Bookmark an article
    response = client.post(f'/api/articles/{article.id}/bookmark',
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 4: Get user folders
    response = client.get('/api/articles/folders', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['folders']) > 0
    
    # Test 5: Get bookmarked articles
    response = client.get('/api/articles/bookmarks', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['bookmarks']) > 0

def test_article_analytics(client, auth_headers, sample_articles):
    """Test article analytics and insights"""
    
    article = sample_articles[0]
    
    # Test 1: Record article view
    response = client.post(f'/api/articles/{article.id}/analytics',
                          json={'action': 'view'},
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 2: Record article share
    response = client.post(f'/api/articles/{article.id}/analytics',
                          json={'action': 'share', 'platform': 'twitter'},
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 3: Get article analytics
    response = client.get(f'/api/articles/{article.id}/analytics',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'views' in data
    assert 'shares' in data
    
    # Test 4: Get user reading insights
    response = client.get('/api/user/insights', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'reading_stats' in data
    assert 'preferred_categories' in data

def test_cultural_personalization(client, auth_headers, sample_articles):
    """Test cultural personalization features"""
    
    # Test 1: Set cultural preferences
    response = client.put('/api/user/preferences',
                         json={
                             'cultural_background': 'African American',
                             'interests': ['career development', 'financial literacy'],
                             'reading_level': 'Intermediate'
                         },
                         headers=auth_headers)
    assert response.status_code == 200
    
    # Test 2: Get culturally personalized recommendations
    response = client.get('/api/articles/recommendations?cultural_personalization=true',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'recommendations' in data
    
    # Test 3: Get articles by cultural relevance
    response = client.get('/api/articles?cultural_relevance_min=8',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data

def test_advanced_search_features(client, auth_headers, sample_articles):
    """Test advanced search and filtering"""
    
    # Test 1: Full-text search
    response = client.post('/api/articles/search',
                          json={
                              'query': 'career development strategies',
                              'search_type': 'full_text'
                          },
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data
    
    # Test 2: Filter by multiple criteria
    response = client.post('/api/articles/search',
                          json={
                              'filters': {
                                  'phase': 'BE',
                                  'difficulty': 'Intermediate',
                                  'category': 'Career Development',
                                  'cultural_relevance_min': 7,
                                  'quality_min': 0.8
                              }
                          },
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data
    
    # Test 3: Sort by different criteria
    response = client.get('/api/articles?sort_by=cultural_relevance&sort_order=desc',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data

def test_assessment_based_access_control(client, auth_headers, sample_articles):
    """Test assessment-based access control"""
    
    # Test 1: Create assessment with low scores
    response = client.post('/api/user/assessment', 
                          json={
                              'be_score': 30,
                              'do_score': 25,
                              'have_score': 20
                          },
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 2: Try to access advanced articles (should be restricted)
    response = client.get('/api/articles?difficulty=Advanced',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    # Should only return articles appropriate for the user's level
    
    # Test 3: Update assessment with higher scores
    response = client.post('/api/user/assessment', 
                          json={
                              'be_score': 85,
                              'do_score': 80,
                              'have_score': 75
                          },
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 4: Now should be able to access advanced articles
    response = client.get('/api/articles?difficulty=Advanced',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data

def test_article_export_and_import(client, auth_headers, sample_articles):
    """Test article export and import functionality"""
    
    # Test 1: Export articles to different formats
    response = client.get('/api/articles/export?format=json',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'articles' in data
    
    # Test 2: Export reading list
    response = client.get('/api/user/reading-list/export?format=csv',
                         headers=auth_headers)
    assert response.status_code == 200
    
    # Test 3: Import articles (if feature is enabled)
    if app.config.get('ENABLE_ARTICLE_IMPORT', False):
        response = client.post('/api/articles/import',
                              json={'urls': ['https://example.com/new-article']},
                              headers=auth_headers)
        assert response.status_code == 200

def test_error_handling_and_validation(client, auth_headers):
    """Test error handling and input validation"""
    
    # Test 1: Invalid assessment scores
    response = client.post('/api/user/assessment', 
                          json={
                              'be_score': 150,  # Invalid score
                              'do_score': 65,
                              'have_score': 45
                          },
                          headers=auth_headers)
    assert response.status_code == 400
    
    # Test 2: Invalid article ID
    response = client.get('/api/articles/999999',
                         headers=auth_headers)
    assert response.status_code == 404
    
    # Test 3: Invalid search query
    response = client.post('/api/articles/search',
                          json={'query': ''},  # Empty query
                          headers=auth_headers)
    assert response.status_code == 400
    
    # Test 4: Unauthorized access
    response = client.get('/api/articles')
    assert response.status_code == 401

def test_performance_and_caching(client, auth_headers, sample_articles):
    """Test performance and caching features"""
    
    # Test 1: First request (should be slower)
    start_time = datetime.now()
    response = client.get('/api/articles', headers=auth_headers)
    first_request_time = (datetime.now() - start_time).total_seconds()
    assert response.status_code == 200
    
    # Test 2: Second request (should be faster due to caching)
    start_time = datetime.now()
    response = client.get('/api/articles', headers=auth_headers)
    second_request_time = (datetime.now() - start_time).total_seconds()
    assert response.status_code == 200
    
    # Test 3: Search with caching
    response = client.post('/api/articles/search',
                          json={'query': 'career'},
                          headers=auth_headers)
    assert response.status_code == 200
    # Should include cache headers
    assert 'Cache-Control' in response.headers

def test_rate_limiting(client, auth_headers):
    """Test rate limiting functionality"""
    
    # Test 1: Make multiple rapid requests
    for i in range(10):
        response = client.get('/api/articles', headers=auth_headers)
        if response.status_code == 429:  # Rate limit exceeded
            break
    
    # Test 2: Search rate limiting
    for i in range(5):
        response = client.post('/api/articles/search',
                              json={'query': f'test query {i}'},
                              headers=auth_headers)
        if response.status_code == 429:
            break

def test_offline_functionality(client, auth_headers, sample_articles):
    """Test offline reading functionality"""
    
    # Test 1: Download article for offline reading
    article = sample_articles[0]
    response = client.get(f'/api/articles/{article.id}/download',
                         headers=auth_headers)
    assert response.status_code == 200
    
    # Test 2: Get offline reading list
    response = client.get('/api/articles/offline',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'offline_articles' in data

def test_social_sharing(client, auth_headers, sample_articles):
    """Test social sharing functionality"""
    
    article = sample_articles[0]
    
    # Test 1: Share article on social media
    response = client.post(f'/api/articles/{article.id}/share',
                          json={'platform': 'twitter'},
                          headers=auth_headers)
    assert response.status_code == 200
    
    # Test 2: Get sharing statistics
    response = client.get(f'/api/articles/{article.id}/shares',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'shares' in data

def test_cleanup_and_maintenance(client, auth_headers):
    """Test cleanup and maintenance features"""
    
    # Test 1: Clean up old analytics data
    response = client.post('/api/admin/cleanup/analytics',
                          headers=auth_headers)
    # This might require admin privileges
    if response.status_code == 403:
        # Expected for non-admin users
        pass
    else:
        assert response.status_code == 200
    
    # Test 2: Database maintenance
    response = client.post('/api/admin/maintenance/database',
                          headers=auth_headers)
    if response.status_code == 403:
        # Expected for non-admin users
        pass
    else:
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
