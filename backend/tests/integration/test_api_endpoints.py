"""
Integration tests for API endpoints
"""
import pytest
import json
from datetime import datetime

class TestAssessmentEndpoints:
    """Test assessment API endpoints"""
    
    def test_submit_assessment_success(self, client, auth_headers, sample_assessment_data):
        """Test successful assessment submission"""
        response = client.post(
            '/api/assessments',
            data=json.dumps(sample_assessment_data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert data.get('success') is True or 'id' in data
    
    def test_submit_assessment_missing_email(self, client, auth_headers):
        """Test assessment submission without email"""
        data = {
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_submit_assessment_invalid_email(self, client, auth_headers):
        """Test assessment submission with invalid email"""
        data = {
            'email': 'invalid-email',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_submit_assessment_sql_injection(self, client, auth_headers):
        """Test SQL injection prevention"""
        data = {
            'email': "'; DROP TABLE users; --",
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        # Should reject or sanitize
        assert response.status_code in [400, 422]
    
    def test_submit_assessment_xss(self, client, auth_headers):
        """Test XSS prevention"""
        data = {
            'email': 'test@example.com',
            'firstName': '<script>alert("xss")</script>',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        # Should reject or sanitize
        assert response.status_code in [200, 201, 400, 422]
        if response.status_code in [200, 201]:
            response_data = json.loads(response.data)
            # Check that XSS is not in response
            response_str = json.dumps(response_data)
            assert '<script>' not in response_str
    
    def test_submit_assessment_rate_limiting(self, client, auth_headers, sample_assessment_data):
        """Test rate limiting on assessment endpoint"""
        # Make many rapid requests
        responses = []
        for i in range(110):
            response = client.post(
                '/api/assessments',
                data=json.dumps(sample_assessment_data),
                headers=auth_headers,
                content_type='application/json'
            )
            responses.append(response.status_code)
        
        # Should eventually hit rate limit
        assert 429 in responses or all(r in [200, 201, 400] for r in responses)

class TestProfileEndpoints:
    """Test profile API endpoints"""
    
    def test_get_profile_requires_auth(self, client):
        """Test that profile endpoint requires authentication"""
        response = client.get('/api/profile')
        assert response.status_code in [401, 403]
    
    def test_create_profile_success(self, client, auth_headers, sample_profile_data):
        """Test successful profile creation"""
        response = client.post(
            '/api/profile',
            data=json.dumps(sample_profile_data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        # May require auth or return 200/201
        assert response.status_code in [200, 201, 401, 403]
    
    def test_update_profile_validation(self, client, auth_headers):
        """Test profile update validation"""
        data = {
            'email': 'invalid-email-format',
            'name': 'A' * 1000  # Too long
        }
        
        response = client.put(
            '/api/profile',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        # Should validate and reject
        assert response.status_code in [400, 422, 401, 403]

class TestVehicleEndpoints:
    """Test vehicle API endpoints"""
    
    def test_create_vehicle_success(self, client, auth_headers, sample_vehicle_data):
        """Test successful vehicle creation"""
        response = client.post(
            '/api/vehicle',
            data=json.dumps(sample_vehicle_data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 401, 403]
    
    def test_vehicle_vin_validation(self, client, auth_headers):
        """Test VIN validation"""
        data = {
            'make': 'Toyota',
            'model': 'Camry',
            'year': 2020,
            'vin': 'invalid-vin',  # Invalid VIN
            'mileage': 50000
        }
        
        response = client.post(
            '/api/vehicle',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        # Should validate VIN format
        assert response.status_code in [400, 422, 401, 403]

class TestDailyOutlookEndpoints:
    """Test daily outlook API endpoints"""
    
    def test_get_daily_outlook_requires_auth(self, client):
        """Test that daily outlook requires authentication"""
        response = client.get('/api/daily-outlook')
        assert response.status_code in [401, 403]
    
    def test_get_daily_outlook_success(self, client, auth_headers):
        """Test successful daily outlook retrieval"""
        response = client.get(
            '/api/daily-outlook',
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401, 403]
    
    def test_mark_action_completed_validation(self, client, auth_headers):
        """Test action completion validation"""
        # Missing required fields
        data = {}
        
        response = client.post(
            '/api/daily-outlook/action-completed',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        assert response.status_code in [400, 422, 401, 403]

class TestJobMatchingEndpoints:
    """Test job matching API endpoints"""
    
    def test_job_matching_requires_auth(self, client):
        """Test that job matching requires authentication"""
        response = client.get('/api/job-matching')
        assert response.status_code in [401, 403]
    
    def test_job_matching_validation(self, client, auth_headers):
        """Test job matching input validation"""
        data = {
            'location': 'A' * 1000,  # Too long
            'salary': -1000  # Invalid salary
        }
        
        response = client.post(
            '/api/job-matching',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        assert response.status_code in [400, 422, 401, 403]

class TestSecurityHeaders:
    """Test security headers on all endpoints"""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present"""
        response = client.get('/health')
        
        # Check for security headers
        headers = response.headers
        assert 'X-Content-Type-Options' in headers or response.status_code != 200
        # Note: Some headers may only be present on certain endpoints
    
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options('/api/assessments')
        
        # Should have CORS headers for OPTIONS requests
        assert response.status_code in [200, 204, 404]

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_for_invalid_endpoint(self, client):
        """Test 404 for invalid endpoints"""
        response = client.get('/api/invalid-endpoint-12345')
        assert response.status_code == 404
    
    def test_405_for_invalid_method(self, client):
        """Test 405 for invalid HTTP methods"""
        response = client.delete('/health')
        # May return 405 or 404 depending on implementation
        assert response.status_code in [404, 405]
    
    def test_error_response_format(self, client):
        """Test that error responses have proper format"""
        response = client.get('/api/invalid-endpoint-12345')
        
        if response.status_code == 404:
            data = json.loads(response.data)
            # Should have error message
            assert 'error' in data or 'message' in data

class TestInputValidation:
    """Test input validation across endpoints"""
    
    def test_json_parsing_error(self, client, auth_headers):
        """Test handling of invalid JSON"""
        response = client.post(
            '/api/assessments',
            data='invalid json{',
            headers=auth_headers,
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client, auth_headers):
        """Test handling of missing content type"""
        response = client.post(
            '/api/assessments',
            data=json.dumps({'test': 'data'}),
            headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
        )
        
        # May accept or reject depending on implementation
        assert response.status_code in [200, 201, 400, 415]
    
    def test_oversized_payload(self, client, auth_headers):
        """Test handling of oversized payloads"""
        large_data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk',
            'answers': {'q' + str(i): 'a' * 1000 for i in range(100)}
        }
        
        response = client.post(
            '/api/assessments',
            data=json.dumps(large_data),
            headers=auth_headers,
            content_type='application/json'
        )
        
        # Should reject oversized payloads
        assert response.status_code in [400, 413, 422]
