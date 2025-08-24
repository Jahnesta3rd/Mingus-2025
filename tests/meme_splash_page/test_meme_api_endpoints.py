"""
API endpoint tests for meme routes
Tests all meme-related API endpoints with various scenarios.
"""

import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime

from backend.routes.meme_routes import meme_bp


class TestMemeAPIEndpoints:
    """Test class for meme API endpoints"""

    def test_get_user_meme_success(self, test_client, mock_flask_session, sample_meme_data):
        """Test successful GET /api/user-meme/<user_id>"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.select_best_meme_for_user.return_value = sample_meme_data
            mock_service.return_value = mock_service_instance
            
            response = test_client.get('/api/user-meme/123')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'meme' in data
            assert data['meme']['id'] == sample_meme_data['id']

    def test_get_user_meme_unauthorized(self, test_client):
        """Test GET /api/user-meme/<user_id> without authentication"""
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = None
            
            response = test_client.get('/api/user-meme/123')
            
            assert response.status_code == 401

    def test_get_user_meme_forbidden(self, test_client, mock_flask_session):
        """Test GET /api/user-meme/<user_id> with wrong user ID"""
        with patch('backend.routes.meme_routes.session') as mock_session:
            mock_session.get.return_value = 456  # Different user ID
            
            response = test_client.get('/api/user-meme/123')
            
            assert response.status_code == 403

    def test_get_user_meme_no_meme_available(self, test_client, mock_flask_session):
        """Test GET /api/user-meme/<user_id> when no meme is available"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.select_best_meme_for_user.return_value = None
            mock_service.return_value = mock_service_instance
            
            response = test_client.get('/api/user-meme/123')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['meme'] is None

    def test_track_meme_analytics_success(self, test_client, mock_flask_session, sample_analytics_data):
        """Test successful POST /api/meme-analytics"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.record_user_interaction.return_value = Mock(id='history-123')
            mock_service.return_value = mock_service_instance
            
            response = test_client.post(
                '/api/meme-analytics',
                json=sample_analytics_data,
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True

    def test_track_meme_analytics_invalid_interaction(self, test_client, mock_flask_session):
        """Test POST /api/meme-analytics with invalid interaction type"""
        invalid_data = {
            'meme_id': 'test-meme-123',
            'interaction_type': 'invalid_type'
        }
        
        response = test_client.post(
            '/api/meme-analytics',
            json=invalid_data,
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_track_meme_analytics_missing_fields(self, test_client, mock_flask_session):
        """Test POST /api/meme-analytics with missing required fields"""
        incomplete_data = {
            'meme_id': 'test-meme-123'
            # Missing interaction_type
        }
        
        response = test_client.post(
            '/api/meme-analytics',
            json=incomplete_data,
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_get_user_preferences_success(self, test_client, mock_flask_session, sample_preferences_data):
        """Test successful GET /api/user-meme-preferences/<user_id>"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_user_preferences.return_value = Mock(
                memes_enabled=True,
                preferred_categories_list=['monday_career'],
                frequency_setting='daily',
                last_meme_shown_at=datetime.utcnow()
            )
            mock_service_instance.get_user_meme_stats.return_value = {
                'total_interactions': 10,
                'interactions_by_type': {'view': 5, 'like': 3},
                'favorite_categories': ['monday_career']
            }
            mock_service.return_value = mock_service_instance
            
            response = test_client.get('/api/user-meme-preferences/123')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'preferences' in data
            assert 'analytics' in data

    def test_get_user_preferences_creates_defaults(self, test_client, mock_flask_session):
        """Test GET /api/user-meme-preferences/<user_id> creates default preferences"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_user_preferences.return_value = None
            mock_service_instance.create_user_preferences.return_value = Mock(
                memes_enabled=True,
                preferred_categories_list=[],
                frequency_setting='daily'
            )
            mock_service_instance.get_user_meme_stats.return_value = {
                'total_interactions': 0,
                'interactions_by_type': {},
                'favorite_categories': []
            }
            mock_service.return_value = mock_service_instance
            
            response = test_client.get('/api/user-meme-preferences/123')
            
            assert response.status_code == 200
            mock_service_instance.create_user_preferences.assert_called_once()

    def test_update_user_preferences_success(self, test_client, mock_flask_session, sample_preferences_data):
        """Test successful PUT /api/user-meme-preferences/<user_id>"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.update_user_preferences.return_value = Mock(
                memes_enabled=True,
                preferred_categories_list=['monday_career'],
                frequency_setting='daily'
            )
            mock_service.return_value = mock_service_instance
            
            response = test_client.put(
                '/api/user-meme-preferences/123',
                json=sample_preferences_data,
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True

    def test_update_user_preferences_invalid_frequency(self, test_client, mock_flask_session):
        """Test PUT /api/user-meme-preferences/<user_id> with invalid frequency"""
        invalid_data = {
            'frequency_setting': 'invalid_frequency'
        }
        
        response = test_client.put(
            '/api/user-meme-preferences/123',
            json=invalid_data,
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_update_user_preferences_invalid_categories(self, test_client, mock_flask_session):
        """Test PUT /api/user-meme-preferences/<user_id> with invalid categories"""
        invalid_data = {
            'preferred_categories': ['invalid_category']
        }
        
        response = test_client.put(
            '/api/user-meme-preferences/123',
            json=invalid_data,
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_health_check_endpoint(self, test_client):
        """Test GET /api/meme-health"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_all_active_memes.return_value = [Mock(), Mock()]
            mock_service.return_value = mock_service_instance
            
            response = test_client.get('/api/meme-health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            assert data['service'] == 'meme-api'

    def test_rate_limiting(self, test_client, mock_flask_session):
        """Test rate limiting on endpoints"""
        # Make multiple requests quickly
        responses = []
        for i in range(60):  # Exceed rate limit
            response = test_client.get('/api/user-meme/123')
            responses.append(response.status_code)
        
        # Check if any requests were rate limited
        assert 429 in responses

    def test_error_handling_404(self, test_client):
        """Test 404 error handling"""
        response = test_client.get('/api/non-existent-endpoint')
        assert response.status_code == 404

    def test_error_handling_500(self, test_client, mock_flask_session):
        """Test 500 error handling"""
        with patch('backend.routes.meme_routes.MemeService') as mock_service:
            mock_service.side_effect = Exception("Database error")
            
            response = test_client.get('/api/user-meme/123')
            
            assert response.status_code == 500

    def test_cors_headers(self, test_client, mock_flask_session):
        """Test CORS headers are present"""
        response = test_client.get('/api/user-meme/123')
        
        # Check for CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_content_type_validation(self, test_client, mock_flask_session):
        """Test content type validation for POST/PUT requests"""
        # Test without proper content type
        response = test_client.post(
            '/api/meme-analytics',
            data='{"test": "data"}',
            content_type='text/plain'
        )
        
        assert response.status_code == 400

    def test_json_validation(self, test_client, mock_flask_session):
        """Test JSON validation for POST/PUT requests"""
        # Test with invalid JSON
        response = test_client.post(
            '/api/meme-analytics',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_admin_endpoints_unauthorized(self, test_client):
        """Test admin endpoints without proper authorization"""
        response = test_client.get('/api/admin/memes')
        assert response.status_code == 401

    def test_analytics_endpoint_unauthorized(self, test_client):
        """Test analytics endpoint without proper authorization"""
        response = test_client.get('/api/admin/meme-analytics')
        assert response.status_code == 401
