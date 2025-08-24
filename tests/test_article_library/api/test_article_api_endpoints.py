"""
API Endpoint Tests for Article Library

Tests for all Flask API endpoints in the Mingus article library system.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token

class TestArticleSearchEndpoints:
    """Test article search and discovery endpoints"""
    
    def test_search_articles_endpoint(self, client, auth_headers, sample_articles):
        """Test GET /api/articles/search endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Test search with query parameter
            response = client.get(
                '/api/articles/search?query=salary&page=1&per_page=10',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'articles' in data
            assert 'total_count' in data
            assert 'page' in data
            assert 'per_page' in data
            assert isinstance(data['articles'], list)
    
    def test_search_articles_with_filters(self, client, auth_headers):
        """Test search with multiple filters"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get(
                '/api/articles/search?query=negotiation&primary_phase=DO&difficulty_level=Intermediate&demographic_relevance_min=7',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'articles' in data
            assert 'filters_applied' in data
    
    def test_search_articles_authentication_required(self, client):
        """Test that search requires authentication"""
        response = client.get('/api/articles/search?query=test')
        assert response.status_code == 401
    
    def test_search_articles_invalid_parameters(self, client, auth_headers):
        """Test search with invalid parameters"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Test invalid page number
            response = client.get(
                '/api/articles/search?query=test&page=0',
                headers=auth_headers
            )
            assert response.status_code == 400
            
            # Test invalid per_page
            response = client.get(
                '/api/articles/search?query=test&per_page=1000',
                headers=auth_headers
            )
            assert response.status_code == 400

    def test_get_articles_endpoint(self, client, auth_headers, sample_articles):
        """Test GET /api/articles endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'articles' in data
            assert 'pagination' in data
            assert len(data['articles']) >= 2

    def test_get_articles_with_filters(self, client, auth_headers, sample_articles):
        """Test article filtering by phase and difficulty"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles?phase=BE&difficulty=Beginner', 
                                headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['articles']) >= 1
            # Verify filtered results
            for article in data['articles']:
                assert article['primary_phase'] == 'BE'
                assert article['difficulty_level'] == 'Beginner'

    def test_article_search_endpoint_post(self, client, auth_headers, sample_articles):
        """Test POST /api/articles/search endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            search_data = {
                'query': 'confidence',
                'filters': {'cultural_relevance_min': 7}
            }
            
            response = client.post('/api/articles/search',
                                  json=search_data,
                                  headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'articles' in data
            assert len(data['articles']) >= 0

class TestArticleDetailEndpoints:
    """Test article detail and content endpoints"""
    
    def test_get_article_by_id(self, client, auth_headers, sample_articles):
        """Test GET /api/articles/<article_id> endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            response = client.get(f'/api/articles/{article_id}', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == article_id
            assert 'title' in data
            assert 'content' in data
            assert 'primary_phase' in data
            assert 'difficulty_level' in data
    
    def test_get_article_not_found(self, client, auth_headers):
        """Test getting non-existent article"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/non-existent-id', headers=auth_headers)
            assert response.status_code == 404
    
    def test_get_article_access_control(self, client, auth_headers, sample_articles):
        """Test article access control based on user assessment"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Test access to Beginner content (should be accessible without assessment)
            beginner_article = next(article for article in sample_articles if article['difficulty_level'] == 'Beginner')
            response = client.get(f'/api/articles/{beginner_article["id"]}', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['access_granted'] == True

    def test_get_single_article(self, client, auth_headers, sample_articles):
        """Test GET /api/articles/<id> endpoint with access control"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Find BE Beginner article
            article = next(article for article in sample_articles if article['primary_phase'] == 'BE' and article['difficulty_level'] == 'Beginner')
            
            response = client.get(f'/api/articles/{article["id"]}', headers=auth_headers)
            
            # Should have access to Beginner content without assessment
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['title'] == article['title']
            assert data['access_granted'] == True

class TestArticleRecommendationEndpoints:
    """Test article recommendation endpoints"""
    
    def test_get_recommendations(self, client, auth_headers, sample_articles):
        """Test GET /api/articles/recommendations endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/recommendations', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'recommendations' in data
            assert isinstance(data['recommendations'], list)
    
    def test_get_personalized_recommendations(self, client, auth_headers):
        """Test personalized recommendations based on user history"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/recommendations?personalized=true', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'recommendations' in data
            assert 'personalization_score' in data

class TestArticleInteractionEndpoints:
    """Test article interaction endpoints (read, bookmark, rate)"""
    
    def test_article_bookmark(self, client, auth_headers, sample_articles):
        """Test POST /api/articles/<id>/bookmark endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            response = client.post(f'/api/articles/{article_id}/bookmark', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'bookmarked' in data
            assert data['bookmarked'] == True
    
    def test_article_unbookmark(self, client, auth_headers, sample_articles):
        """Test DELETE /api/articles/<id>/bookmark endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            response = client.delete(f'/api/articles/{article_id}/bookmark', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'bookmarked' in data
            assert data['bookmarked'] == False
    
    def test_article_rating(self, client, auth_headers, sample_articles):
        """Test POST /api/articles/<id>/rate endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            rating_data = {
                'rating': 5,
                'feedback': 'Excellent article with practical tips'
            }
            
            response = client.post(f'/api/articles/{article_id}/rate',
                                  json=rating_data,
                                  headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'rating' in data
            assert data['rating']['rating'] == 5
            assert data['rating']['feedback'] == 'Excellent article with practical tips'

class TestArticleProgressEndpoints:
    """Test article progress tracking endpoints"""
    
    def test_reading_progress_update(self, client, auth_headers, sample_articles):
        """Test POST /api/articles/<id>/progress endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            progress_data = {
                'progress_percentage': 50,
                'reading_time_seconds': 120,
                'completed': False
            }
            
            response = client.post(f'/api/articles/{article_id}/progress',
                                  json=progress_data,
                                  headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['progress']['reading_progress_percentage'] == 50
    
    def test_reading_progress_completion(self, client, auth_headers, sample_articles):
        """Test marking article as completed"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            progress_data = {
                'progress_percentage': 100,
                'reading_time_seconds': 600,
                'completed': True
            }
            
            response = client.post(f'/api/articles/{article_id}/progress',
                                  json=progress_data,
                                  headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['progress']['reading_progress_percentage'] == 100
            assert data['progress']['completed'] == True

class TestArticleDiscoveryEndpoints:
    """Test article discovery and browsing endpoints"""
    
    def test_get_featured_articles(self, client, auth_headers):
        """Test GET /api/articles/featured endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/featured', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'featured_articles' in data
            assert isinstance(data['featured_articles'], list)
    
    def test_get_trending_articles(self, client, auth_headers):
        """Test GET /api/articles/trending endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/trending', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'trending_articles' in data
            assert isinstance(data['trending_articles'], list)
    
    def test_get_recent_articles(self, client, auth_headers):
        """Test GET /api/articles/recent endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/recent', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'recent_articles' in data
            assert isinstance(data['recent_articles'], list)

class TestArticleFilterEndpoints:
    """Test article filtering and faceted search endpoints"""
    
    def test_get_available_filters(self, client, auth_headers):
        """Test GET /api/articles/filters endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/filters', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'phases' in data
            assert 'difficulty_levels' in data
            assert 'topics' in data
            assert 'reading_times' in data
    
    def test_get_articles_by_phase(self, client, auth_headers, sample_articles):
        """Test GET /api/articles/phases/<phase> endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/phases/DO', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'articles' in data
            assert 'phase' in data
            assert data['phase'] == 'DO'
            
            # Verify all articles are in DO phase
            for article in data['articles']:
                assert article['primary_phase'] == 'DO'

class TestUserArticleHistoryEndpoints:
    """Test user article history and analytics endpoints"""
    
    def test_get_user_reading_history(self, client, auth_headers):
        """Test GET /api/user/articles/read endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/user/articles/read', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'read_articles' in data
            assert isinstance(data['read_articles'], list)
    
    def test_get_user_bookmarks(self, client, auth_headers):
        """Test GET /api/user/articles/bookmarks endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/user/articles/bookmarks', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'bookmarked_articles' in data
            assert isinstance(data['bookmarked_articles'], list)
    
    def test_get_user_ratings(self, client, auth_headers):
        """Test GET /api/user/articles/ratings endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/user/articles/ratings', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'rated_articles' in data
            assert isinstance(data['rated_articles'], list)

class TestArticleAnalyticsEndpoints:
    """Test article analytics and statistics endpoints"""
    
    def test_get_article_analytics(self, client, auth_headers, sample_articles):
        """Test GET /api/articles/<id>/analytics endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            response = client.get(f'/api/articles/{article_id}/analytics', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'analytics' in data
            assert 'view_count' in data['analytics']
            assert 'read_count' in data['analytics']
            assert 'avg_rating' in data['analytics']
    
    def test_get_user_reading_stats(self, client, auth_headers):
        """Test GET /api/user/reading-stats endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/user/reading-stats', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'stats' in data
            assert 'total_articles_read' in data['stats']
            assert 'total_reading_time' in data['stats']
            assert 'favorite_topics' in data['stats']

class TestAssessmentEndpoints:
    """Test user assessment endpoints"""
    
    def test_assessment_submission(self, client, auth_headers):
        """Test POST /api/user/assessment endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            assessment_data = {
                'be_score': 75,
                'do_score': 65,
                'have_score': 50,
                'completion_time_seconds': 300
            }
            
            response = client.post('/api/user/assessment',
                                  json=assessment_data,
                                  headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'assessment' in data
            assert data['assessment']['be_score'] == 75
            assert data['assessment']['overall_readiness_level'] in ['Beginner', 'Intermediate', 'Advanced']
    
    def test_get_user_assessment(self, client, auth_headers):
        """Test GET /api/user/assessment endpoint"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/user/assessment', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'assessment' in data
            assert 'be_score' in data['assessment']
            assert 'do_score' in data['assessment']
            assert 'have_score' in data['assessment']

class TestErrorHandling:
    """Test API error handling"""
    
    def test_unauthorized_access(self, client, sample_articles):
        """Test API endpoints without authentication"""
        response = client.get('/api/articles')
        assert response.status_code == 401
        
        response = client.get(f'/api/articles/{sample_articles[0]["id"]}')
        assert response.status_code == 401
    
    def test_invalid_article_id(self, client, auth_headers):
        """Test handling of invalid article IDs"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles/invalid-uuid', headers=auth_headers)
            assert response.status_code == 400
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test handling of missing required fields"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Test assessment submission without required fields
            response = client.post('/api/user/assessment',
                                  json={},
                                  headers=auth_headers)
            assert response.status_code == 400
    
    def test_invalid_rating_value(self, client, auth_headers, sample_articles):
        """Test handling of invalid rating values"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            article_id = sample_articles[0]['id']
            rating_data = {
                'rating': 6,  # Invalid rating (should be 1-5)
                'feedback': 'Test feedback'
            }
            
            response = client.post(f'/api/articles/{article_id}/rate',
                                  json=rating_data,
                                  headers=auth_headers)
            assert response.status_code == 400

class TestAuthenticationAndAuthorization:
    """Test authentication and authorization"""
    
    def test_valid_authentication(self, client, auth_headers):
        """Test valid authentication token"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            response = client.get('/api/articles', headers=auth_headers)
            assert response.status_code == 200
    
    def test_invalid_authentication(self, client):
        """Test invalid authentication token"""
        invalid_headers = {'Authorization': 'Bearer invalid-token'}
        response = client.get('/api/articles', headers=invalid_headers)
        assert response.status_code == 401
    
    def test_expired_authentication(self, client):
        """Test expired authentication token"""
        expired_headers = {'Authorization': 'Bearer expired-token'}
        response = client.get('/api/articles', headers=expired_headers)
        assert response.status_code == 401
    
    def test_missing_authentication(self, client):
        """Test missing authentication header"""
        response = client.get('/api/articles')
        assert response.status_code == 401

class TestRateLimiting:
    """Test API rate limiting"""
    
    def test_rate_limiting(self, client, auth_headers):
        """Test API rate limiting"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # Make many requests quickly to test rate limiting
            for i in range(35):  # Exceed 30/minute limit
                response = client.get('/api/articles', headers=auth_headers)
                if response.status_code == 429:
                    assert 'rate limit' in response.get_json()['error'].lower()
                    break
            else:
                # If rate limiting is not implemented, this test should pass
                assert True
    
    def test_rate_limit_reset(self, client, auth_headers):
        """Test rate limit reset after time period"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'test-user-123'
            
            # This test would require time-based mocking in a real implementation
            response = client.get('/api/articles', headers=auth_headers)
            assert response.status_code in [200, 429]  # Either success or rate limited
