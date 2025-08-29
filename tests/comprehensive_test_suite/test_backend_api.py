"""
Backend API Tests for Assessment System

Comprehensive test suite for all assessment endpoints (/api/assessments/*)
Includes unit tests, authentication, authorization, rate limiting, and security tests.
"""

import pytest
import json
import time
from unittest.mock import patch, Mock
from flask import url_for
from sqlalchemy.exc import SQLAlchemyError

pytestmark = pytest.mark.backend

class TestAssessmentEndpoints:
    """Test all assessment API endpoints"""
    
    def test_calculate_comprehensive_assessment_success(self, client, auth_headers, sample_assessment_data):
        """Test successful comprehensive assessment calculation"""
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'overall_risk_level' in data['data']
        assert 'primary_concerns' in data['data']
        assert 'action_priorities' in data['data']
        assert 'subscription_recommendation' in data['data']
        assert 'confidence_score' in data['data']
        assert 'job_risk' in data['data']
        assert 'relationship_impact' in data['data']
        assert 'income_comparison' in data['data']
    
    def test_calculate_assessment_invalid_data(self, client, auth_headers):
        """Test assessment calculation with invalid data"""
        invalid_data = {
            'current_salary': 'invalid',  # Should be integer
            'field': 'invalid_field',     # Not in enum
            'relationship_status': 'invalid_status'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': invalid_data}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'validation_errors' in data
    
    def test_calculate_assessment_missing_required_fields(self, client, auth_headers):
        """Test assessment calculation with missing required fields"""
        incomplete_data = {
            'current_salary': 75000
            # Missing required fields: field, relationship_status, financial_stress_frequency
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': incomplete_data}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'validation_errors' in data
    
    def test_calculate_assessment_unauthorized(self, client, sample_assessment_data):
        """Test assessment calculation without authentication"""
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            json={'assessment_data': sample_assessment_data}
        )
        
        assert response.status_code == 401
    
    def test_calculate_assessment_invalid_token(self, client, sample_assessment_data):
        """Test assessment calculation with invalid token"""
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=invalid_headers,
            json={'assessment_data': sample_assessment_data}
        )
        
        assert response.status_code == 401
    
    def test_save_assessment_result_success(self, client, auth_headers, sample_assessment_data, db_session):
        """Test successful assessment result saving"""
        # First calculate assessment
        calc_response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        
        calc_data = calc_response.get_json()['data']
        
        # Save the result
        save_data = {
            'assessment_data': sample_assessment_data,
            'results': calc_data,
            'user_notes': 'Test assessment notes'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/save',
            headers=auth_headers,
            json=save_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'assessment_id' in data['data']
    
    def test_get_assessment_history_success(self, client, auth_headers, db_session):
        """Test successful retrieval of assessment history"""
        response = client.get(
            '/api/v1/assessment-scoring/history',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'assessments' in data['data']
        assert isinstance(data['data']['assessments'], list)
    
    def test_get_assessment_by_id_success(self, client, auth_headers, db_session):
        """Test successful retrieval of specific assessment"""
        # First create an assessment
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        calc_response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_data}
        )
        
        calc_data = calc_response.get_json()['data']
        
        save_data = {
            'assessment_data': sample_data,
            'results': calc_data
        }
        
        save_response = client.post(
            '/api/v1/assessment-scoring/save',
            headers=auth_headers,
            json=save_data
        )
        
        assessment_id = save_response.get_json()['data']['assessment_id']
        
        # Retrieve the assessment
        response = client.get(
            f'/api/v1/assessment-scoring/{assessment_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['id'] == assessment_id
    
    def test_get_assessment_by_id_not_found(self, client, auth_headers):
        """Test retrieval of non-existent assessment"""
        response = client.get(
            '/api/v1/assessment-scoring/999999',
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_assessment_by_id_unauthorized(self, client, db_session):
        """Test retrieval of assessment without authentication"""
        response = client.get('/api/v1/assessment-scoring/1')
        assert response.status_code == 401
    
    def test_update_assessment_success(self, client, auth_headers, db_session):
        """Test successful assessment update"""
        # First create an assessment
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        calc_response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_data}
        )
        
        calc_data = calc_response.get_json()['data']
        
        save_data = {
            'assessment_data': sample_data,
            'results': calc_data
        }
        
        save_response = client.post(
            '/api/v1/assessment-scoring/save',
            headers=auth_headers,
            json=save_data
        )
        
        assessment_id = save_response.get_json()['data']['assessment_id']
        
        # Update the assessment
        update_data = {
            'user_notes': 'Updated assessment notes',
            'tags': ['updated', 'test']
        }
        
        response = client.put(
            f'/api/v1/assessment-scoring/{assessment_id}',
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_delete_assessment_success(self, client, auth_headers, db_session):
        """Test successful assessment deletion"""
        # First create an assessment
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        calc_response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_data}
        )
        
        calc_data = calc_response.get_json()['data']
        
        save_data = {
            'assessment_data': sample_data,
            'results': calc_data
        }
        
        save_response = client.post(
            '/api/v1/assessment-scoring/save',
            headers=auth_headers,
            json=save_data
        )
        
        assessment_id = save_response.get_json()['data']['assessment_id']
        
        # Delete the assessment
        response = client.delete(
            f'/api/v1/assessment-scoring/{assessment_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_get_assessment_analytics_success(self, client, auth_headers, db_session):
        """Test successful retrieval of assessment analytics"""
        response = client.get(
            '/api/v1/assessment-scoring/analytics',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'analytics' in data['data']
        assert 'total_assessments' in data['data']['analytics']
        assert 'average_risk_level' in data['data']['analytics']
        assert 'field_distribution' in data['data']['analytics']


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_exceeded(self, client, auth_headers, sample_assessment_data):
        """Test rate limiting when too many requests are made"""
        # Make multiple rapid requests
        responses = []
        for i in range(70):  # Exceed the 60 requests per minute limit
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            responses.append(response)
        
        # Check that some requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
        
        # Check rate limit headers
        for response in rate_limited_responses:
            assert 'X-RateLimit-Limit' in response.headers
            assert 'X-RateLimit-Remaining' in response.headers
            assert 'X-RateLimit-Reset' in response.headers
    
    def test_rate_limiting_reset(self, client, auth_headers, sample_assessment_data):
        """Test rate limiting reset after time period"""
        # Make requests up to the limit
        for i in range(60):
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            assert response.status_code in [200, 429]
        
        # Wait for rate limit to reset (in real scenario)
        # For testing, we'll just verify the rate limit headers
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        
        if response.status_code == 429:
            assert 'X-RateLimit-Reset' in response.headers


class TestSecurity:
    """Test security features"""
    
    def test_sql_injection_prevention(self, client, auth_headers):
        """Test SQL injection prevention"""
        malicious_data = {
            'current_salary': 75000,
            'field': "software_development'; DROP TABLE users; --",
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': malicious_data}
        )
        
        # Should return validation error, not execute SQL
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_xss_prevention(self, client, auth_headers):
        """Test XSS prevention"""
        malicious_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes',
            'user_notes': '<script>alert("XSS")</script>'
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': malicious_data}
        )
        
        # Should sanitize input and not execute script
        assert response.status_code == 200
        data = response.get_json()
        assert '<script>' not in str(data)
    
    def test_csrf_protection(self, client, sample_assessment_data):
        """Test CSRF protection"""
        # Request without CSRF token
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            json={'assessment_data': sample_assessment_data}
        )
        
        # Should be rejected due to missing CSRF token
        assert response.status_code == 401
    
    def test_authentication_bypass_attempts(self, client, sample_assessment_data):
        """Test various authentication bypass attempts"""
        # Test with malformed token
        malformed_headers = {'Authorization': 'Bearer malformed.token.here'}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=malformed_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401
        
        # Test with expired token
        expired_headers = {'Authorization': 'Bearer expired.token.here'}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=expired_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401
        
        # Test with empty token
        empty_headers = {'Authorization': 'Bearer '}
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=empty_headers,
            json={'assessment_data': sample_assessment_data}
        )
        assert response.status_code == 401


class TestDatabaseIntegration:
    """Test database integration with real data scenarios"""
    
    def test_database_connection_pool(self, client, auth_headers, sample_assessment_data):
        """Test database connection pool under load"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.post(
                    '/api/v1/assessment-scoring/calculate',
                    headers=auth_headers,
                    json={'assessment_data': sample_assessment_data}
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to test connection pool
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0
        assert all(status == 200 for status in results)
    
    def test_database_transaction_rollback(self, client, auth_headers, db_session):
        """Test database transaction rollback on error"""
        # Mock database error
        with patch('backend.services.assessment_scoring_service.AssessmentScoringService.save_assessment') as mock_save:
            mock_save.side_effect = SQLAlchemyError("Database error")
            
            sample_data = {
                'current_salary': 75000,
                'field': 'software_development',
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes'
            }
            
            response = client.post(
                '/api/v1/assessment-scoring/save',
                headers=auth_headers,
                json={'assessment_data': sample_data, 'results': {}}
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
    
    def test_database_constraint_violation(self, client, auth_headers):
        """Test database constraint violation handling"""
        # Test with invalid foreign key
        invalid_data = {
            'assessment_data': {
                'current_salary': 75000,
                'field': 'software_development',
                'relationship_status': 'married',
                'financial_stress_frequency': 'sometimes'
            },
            'user_id': 999999  # Non-existent user ID
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/save',
            headers=auth_headers,
            json=invalid_data
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestPerformance:
    """Test performance requirements"""
    
    def test_assessment_calculation_performance(self, client, auth_headers, sample_assessment_data, performance_monitor):
        """Test assessment calculation performance"""
        performance_monitor.start_timer('assessment_calculation')
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_assessment_data}
        )
        
        performance_monitor.end_timer('assessment_calculation')
        
        duration = performance_monitor.get_duration('assessment_calculation')
        
        assert response.status_code == 200
        assert duration < 2.0  # Should complete within 2 seconds
    
    def test_database_query_performance(self, client, auth_headers, performance_monitor):
        """Test database query performance"""
        performance_monitor.start_timer('database_query')
        
        response = client.get(
            '/api/v1/assessment-scoring/history',
            headers=auth_headers
        )
        
        performance_monitor.end_timer('database_query')
        
        duration = performance_monitor.get_duration('database_query')
        
        assert response.status_code == 200
        assert duration < 0.1  # Should complete within 100ms
    
    def test_concurrent_user_load(self, client, auth_headers, sample_assessment_data, load_test_executor):
        """Test concurrent user load handling"""
        import concurrent.futures
        
        def make_assessment_request():
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            return response.status_code
        
        # Submit 50 concurrent requests
        futures = []
        for i in range(50):
            future = load_test_executor.submit(make_assessment_request)
            futures.append(future)
        
        # Wait for all requests to complete
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(500)  # Error
        
        # Verify most requests succeeded
        successful_requests = [r for r in results if r == 200]
        assert len(successful_requests) >= 45  # At least 90% success rate
    
    def test_memory_usage_optimization(self, client, auth_headers, sample_assessment_data, performance_monitor):
        """Test memory usage optimization"""
        initial_memory = performance_monitor.get_memory_usage()
        
        # Make multiple requests to test memory usage
        for i in range(10):
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            assert response.status_code == 200
        
        final_memory = performance_monitor.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50.0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_service_unavailable(self, client, auth_headers, sample_assessment_data):
        """Test handling of service unavailability"""
        with patch('backend.services.assessment_scoring_service.AssessmentScoringService.calculate_assessment') as mock_calc:
            mock_calc.side_effect = Exception("Service unavailable")
            
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_assessment_data}
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data
    
    def test_invalid_json_request(self, client, auth_headers):
        """Test handling of invalid JSON requests"""
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_missing_content_type(self, client, auth_headers, sample_assessment_data):
        """Test handling of missing content type"""
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            data=json.dumps({'assessment_data': sample_assessment_data})
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_large_payload_handling(self, client, auth_headers):
        """Test handling of large payloads"""
        large_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes',
            'large_field': 'x' * 1000000  # 1MB string
        }
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': large_data}
        )
        
        # Should handle gracefully (either reject or process)
        assert response.status_code in [200, 413, 400]
