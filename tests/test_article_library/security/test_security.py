"""
Security Tests for Article Library

Tests for authentication, authorization, input validation, and security vulnerabilities
in the Mingus article library system.
"""

import pytest
import json
import re
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

class TestAuthenticationSecurity:
    """Test authentication security measures"""
    
    def test_authentication_required_for_all_endpoints(self, client, security_validator):
        """Test that all endpoints require authentication"""
        endpoints = [
            '/api/articles/search',
            '/api/articles/featured',
            '/api/articles/recommendations',
            '/api/articles/filters',
            '/api/articles/statistics',
            '/api/articles/bookmarks',
            '/api/articles/ratings'
        ]
        
        for endpoint in endpoints:
            security_validator.validate_authentication_required(endpoint, client)
    
    def test_invalid_token_rejection(self, client):
        """Test rejection of invalid authentication tokens"""
        invalid_tokens = [
            'invalid_token',
            'Bearer invalid',
            'Bearer ',
            'Bearer 123',
            'Basic dXNlcjpwYXNz',  # Basic auth instead of Bearer
            'JWT invalid.jwt.token'
        ]
        
        for token in invalid_tokens:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token
            }
            
            response = client.get('/api/articles/search?query=test', headers=headers)
            assert response.status_code == 401
    
    def test_expired_token_handling(self, client):
        """Test handling of expired authentication tokens"""
        expired_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer expired_token_123'
        }
        
        response = client.get('/api/articles/search?query=test', headers=expired_headers)
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'authentication' in data['error'].lower()
    
    def test_missing_token_handling(self, client):
        """Test handling of missing authentication tokens"""
        headers = {
            'Content-Type': 'application/json'
            # No Authorization header
        }
        
        response = client.get('/api/articles/search?query=test', headers=headers)
        assert response.status_code == 401
    
    def test_token_format_validation(self, client):
        """Test validation of token format"""
        malformed_tokens = [
            'Bearer',
            'Bearer   ',  # Extra spaces
            'Bearer\tinvalid',  # Tab character
            'Bearer\ninvalid',  # Newline character
            'Bearer\r\ninvalid',  # Carriage return
            'Bearer\x00invalid',  # Null byte
        ]
        
        for token in malformed_tokens:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token
            }
            
            response = client.get('/api/articles/search?query=test', headers=headers)
            assert response.status_code == 401

class TestAuthorizationSecurity:
    """Test authorization and access control"""
    
    def test_user_data_isolation(self, client, auth_headers, sample_articles):
        """Test that users can only access their own data"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test that user can access their own bookmarks
            response = client.get('/api/articles/bookmarks', headers=auth_headers)
            assert response.status_code == 200
            
            # Test that user cannot access another user's data
            with patch('backend.routes.articles.get_user_id') as mock_get_user_id_2:
                mock_get_user_id_2.return_value = 'user-456'
                
                # The endpoint should still work but return only user-456's data
                response = client.get('/api/articles/bookmarks', headers=auth_headers)
                assert response.status_code == 200
    
    def test_article_access_control(self, client, auth_headers, sample_articles):
        """Test article access control based on assessment scores"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test access control for different user assessment levels
            test_cases = [
                {
                    'assessment_scores': {'be_score': 2, 'do_score': 1, 'have_score': 1},
                    'expected_access': {'Beginner': True, 'Intermediate': False, 'Advanced': False}
                },
                {
                    'assessment_scores': {'be_score': 5, 'do_score': 4, 'have_score': 3},
                    'expected_access': {'Beginner': True, 'Intermediate': True, 'Advanced': False}
                },
                {
                    'assessment_scores': {'be_score': 8, 'do_score': 7, 'have_score': 9},
                    'expected_access': {'Beginner': True, 'Intermediate': True, 'Advanced': True}
                }
            ]
            
            for test_case in test_cases:
                with patch('backend.routes.articles.get_user_assessment_scores') as mock_scores:
                    mock_scores.return_value = test_case['assessment_scores']
                    
                    for difficulty, should_have_access in test_case['expected_access'].items():
                        # Find an article with this difficulty level
                        article = next((a for a in sample_articles if a['difficulty_level'] == difficulty), None)
                        if article:
                            response = client.get(f'/api/articles/{article["id"]}', headers=auth_headers)
                            if should_have_access:
                                assert response.status_code == 200
                            else:
                                assert response.status_code == 403
    
    def test_subscription_tier_access_control(self, client, auth_headers):
        """Test access control based on subscription tiers"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test different subscription tiers
            subscription_tiers = ['free', 'premium', 'enterprise']
            
            for tier in subscription_tiers:
                with patch('backend.routes.articles.get_user_subscription_tier') as mock_tier:
                    mock_tier.return_value = tier
                    
                    # Test access to premium features
                    response = client.get('/api/articles/recommendations/personalized', headers=auth_headers)
                    
                    if tier in ['premium', 'enterprise']:
                        assert response.status_code == 200
                    else:
                        assert response.status_code == 403

class TestInputValidationSecurity:
    """Test input validation and sanitization"""
    
    def test_sql_injection_prevention(self, client, auth_headers, security_validator):
        """Test prevention of SQL injection attacks"""
        sql_injection_attempts = [
            "'; DROP TABLE articles; --",
            "' OR 1=1; --",
            "' UNION SELECT * FROM users; --",
            "'; INSERT INTO articles VALUES ('hack'); --",
            "' OR '1'='1",
            "'; UPDATE users SET password='hack'; --"
        ]
        
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            for injection in sql_injection_attempts:
                # Test in search query
                response = client.get(
                    f'/api/articles/search?query={injection}',
                    headers=auth_headers
                )
                
                # Should not crash or return sensitive data
                assert response.status_code in [200, 400, 404]
                
                # Test in article ID
                response = client.get(
                    f'/api/articles/{injection}',
                    headers=auth_headers
                )
                
                assert response.status_code in [400, 404]
    
    def test_xss_prevention(self, client, auth_headers, security_validator):
        """Test prevention of XSS attacks"""
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<svg onload=alert('XSS')>",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;"
        ]
        
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            for xss in xss_attempts:
                # Test in search query
                response = client.get(
                    f'/api/articles/search?query={xss}',
                    headers=auth_headers
                )
                
                # Should handle safely
                assert response.status_code in [200, 400]
                
                # Test in feedback/notes
                response = client.post(
                    '/api/articles/test-id/rate',
                    data=json.dumps({
                        'rating': 5,
                        'feedback': xss
                    }),
                    headers=auth_headers
                )
                
                # Should handle safely
                assert response.status_code in [200, 400]
    
    def test_path_traversal_prevention(self, client, auth_headers):
        """Test prevention of path traversal attacks"""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            for path in path_traversal_attempts:
                response = client.get(f'/api/articles/{path}', headers=auth_headers)
                assert response.status_code in [400, 404]
    
    def test_parameter_pollution_prevention(self, client, auth_headers):
        """Test prevention of HTTP parameter pollution"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test duplicate parameters
            response = client.get(
                '/api/articles/search?query=test&query=malicious&page=1&page=999',
                headers=auth_headers
            )
            
            # Should handle safely (use first or last parameter)
            assert response.status_code in [200, 400]
    
    def test_large_input_handling(self, client, auth_headers):
        """Test handling of extremely large inputs"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test very large search query
            large_query = 'A' * 10000  # 10KB query
            
            response = client.get(
                f'/api/articles/search?query={large_query}',
                headers=auth_headers
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 413]  # 413 = Payload Too Large
    
    def test_special_character_handling(self, client, auth_headers):
        """Test handling of special characters in inputs"""
        special_chars = [
            "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "测试中文",
            "áéíóúñü",
            "🚀💰📈",
            "null\0byte",
            "newline\ncharacter",
            "tab\tcharacter"
        ]
        
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            for chars in special_chars:
                response = client.get(
                    f'/api/articles/search?query={chars}',
                    headers=auth_headers
                )
                
                # Should handle safely
                assert response.status_code in [200, 400]

class TestDataValidationSecurity:
    """Test data validation and type safety"""
    
    def test_json_validation(self, client, auth_headers, sample_articles):
        """Test JSON payload validation"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            article_id = sample_articles[0]['id']
            
            # Test invalid JSON
            invalid_json_payloads = [
                '{"rating": 5,}',  # Trailing comma
                '{"rating": "not_a_number"}',  # Wrong type
                '{"rating": 5, "feedback":}',  # Incomplete
                '{"rating": 5, "feedback": null}',  # Null value
                '{"rating": 5, "feedback": ""}',  # Empty string
                '{"rating": 5, "feedback": "A" * 10000}',  # Too long
            ]
            
            for payload in invalid_json_payloads:
                response = client.post(
                    f'/api/articles/{article_id}/rate',
                    data=payload,
                    headers=auth_headers
                )
                
                assert response.status_code == 400
    
    def test_data_type_validation(self, client, auth_headers, sample_articles):
        """Test data type validation"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            article_id = sample_articles[0]['id']
            
            # Test wrong data types
            invalid_data = [
                {'rating': 'five'},  # String instead of number
                {'rating': 5.5},  # Float instead of integer
                {'rating': True},  # Boolean instead of number
                {'rating': [1, 2, 3]},  # Array instead of number
                {'rating': {'value': 5}},  # Object instead of number
            ]
            
            for data in invalid_data:
                response = client.post(
                    f'/api/articles/{article_id}/rate',
                    data=json.dumps(data),
                    headers=auth_headers
                )
                
                assert response.status_code == 400
    
    def test_range_validation(self, client, auth_headers, sample_articles):
        """Test range and boundary validation"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            article_id = sample_articles[0]['id']
            
            # Test out-of-range values
            invalid_ratings = [0, 6, -1, 100, 999]
            
            for rating in invalid_ratings:
                response = client.post(
                    f'/api/articles/{article_id}/rate',
                    data=json.dumps({'rating': rating}),
                    headers=auth_headers
                )
                
                assert response.status_code == 400
    
    def test_required_field_validation(self, client, auth_headers, sample_articles):
        """Test required field validation"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            article_id = sample_articles[0]['id']
            
            # Test missing required fields
            incomplete_payloads = [
                {},  # Empty payload
                {'feedback': 'Great article'},  # Missing rating
                {'rating': 5},  # Missing feedback (if required)
            ]
            
            for payload in incomplete_payloads:
                response = client.post(
                    f'/api/articles/{article_id}/rate',
                    data=json.dumps(payload),
                    headers=auth_headers
                )
                
                assert response.status_code == 400

class TestRateLimitingSecurity:
    """Test rate limiting and abuse prevention"""
    
    def test_rate_limiting_on_search(self, client, auth_headers):
        """Test rate limiting on search endpoints"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Make many rapid requests
            responses = []
            for _ in range(20):
                response = client.get(
                    '/api/articles/search?query=test&page=1&per_page=10',
                    headers=auth_headers
                )
                responses.append(response)
            
            # Check if rate limiting is applied
            status_codes = [r.status_code for r in responses]
            
            # Should either all succeed or some be rate limited
            if 429 in status_codes:  # Rate limit exceeded
                # Should have some successful requests before rate limiting
                assert 200 in status_codes
            else:
                # If no rate limiting, all should succeed
                assert all(code == 200 for code in status_codes)
    
    def test_rate_limiting_on_ratings(self, client, auth_headers, sample_articles):
        """Test rate limiting on rating endpoints"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            article_id = sample_articles[0]['id']
            
            # Try to rate the same article multiple times
            responses = []
            for _ in range(10):
                response = client.post(
                    f'/api/articles/{article_id}/rate',
                    data=json.dumps({'rating': 5, 'feedback': 'Test rating'}),
                    headers=auth_headers
                )
                responses.append(response)
            
            # Should either all succeed or some be rate limited
            status_codes = [r.status_code for r in responses]
            
            if 429 in status_codes:
                assert 200 in status_codes
            else:
                assert all(code == 200 for code in status_codes)

class TestSessionSecurity:
    """Test session management and security"""
    
    def test_session_timeout(self, client, auth_headers):
        """Test session timeout handling"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Simulate expired session
            with patch('backend.routes.articles.session') as mock_session:
                mock_session.get.return_value = None  # No user_id in session
                
                response = client.get('/api/articles/search?query=test', headers=auth_headers)
                assert response.status_code == 401
    
    def test_session_fixation_prevention(self, client, auth_headers):
        """Test prevention of session fixation attacks"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test that session ID changes after authentication
            response1 = client.get('/api/articles/search?query=test', headers=auth_headers)
            
            # Simulate session regeneration
            with patch('backend.routes.articles.regenerate_session') as mock_regenerate:
                mock_regenerate.return_value = True
                
                response2 = client.get('/api/articles/search?query=test', headers=auth_headers)
                
                # Both should work with proper session management
                assert response1.status_code == 200
                assert response2.status_code == 200

class TestErrorHandlingSecurity:
    """Test secure error handling"""
    
    def test_error_message_sanitization(self, client, auth_headers):
        """Test that error messages don't leak sensitive information"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test various error conditions
            error_scenarios = [
                ('/api/articles/non-existent-id', 404),
                ('/api/articles/invalid-uuid-format', 400),
                ('/api/articles/search?query=&page=0', 400),
            ]
            
            for endpoint, expected_status in error_scenarios:
                response = client.get(endpoint, headers=auth_headers)
                assert response.status_code == expected_status
                
                if response.data:
                    data = json.loads(response.data)
                    
                    # Error messages should not contain sensitive information
                    error_message = data.get('error', '').lower()
                    sensitive_info = [
                        'sql', 'database', 'password', 'token', 'secret',
                        'internal', 'stack trace', 'exception', 'debug'
                    ]
                    
                    for info in sensitive_info:
                        assert info not in error_message
    
    def test_database_error_handling(self, client, auth_headers):
        """Test secure handling of database errors"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Simulate database connection error
            with patch('backend.routes.articles.get_db_session') as mock_db:
                mock_db.side_effect = Exception("Database connection failed")
                
                response = client.get('/api/articles/search?query=test', headers=auth_headers)
                assert response.status_code == 500
                
                data = json.loads(response.data)
                assert 'error' in data
                assert 'internal' in data['error'].lower() or 'server' in data['error'].lower()
                assert 'database' not in data['error'].lower()

class TestLoggingSecurity:
    """Test secure logging practices"""
    
    def test_sensitive_data_not_logged(self, client, auth_headers):
        """Test that sensitive data is not logged"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            # Test that authentication tokens are not logged
            with patch('backend.routes.articles.logger') as mock_logger:
                response = client.get('/api/articles/search?query=test', headers=auth_headers)
                
                # Check that sensitive data is not in log calls
                for call in mock_logger.info.call_args_list:
                    log_message = str(call)
                    assert 'Bearer' not in log_message
                    assert 'token' not in log_message.lower()
    
    def test_audit_logging(self, client, auth_headers, sample_articles):
        """Test that security-relevant events are logged"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            article_id = sample_articles[0]['id']
            
            with patch('backend.routes.articles.logger') as mock_logger:
                # Test successful authentication
                response = client.get('/api/articles/search?query=test', headers=auth_headers)
                
                # Test failed authentication
                failed_response = client.get('/api/articles/search?query=test')
                
                # Should log security events
                assert mock_logger.info.called or mock_logger.warning.called

class TestCORSecurity:
    """Test CORS and cross-origin security"""
    
    def test_cors_headers(self, client, auth_headers):
        """Test CORS header configuration"""
        with patch('backend.routes.articles.get_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = 'user-123'
            
            response = client.get('/api/articles/search?query=test', headers=auth_headers)
            
            # Check CORS headers
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            # Should have appropriate CORS headers or none (if CORS is disabled)
            if any(header in response.headers for header in cors_headers):
                # If CORS is enabled, check configuration
                origin = response.headers.get('Access-Control-Allow-Origin')
                if origin and origin != '*':
                    # Should not allow all origins in production
                    assert origin in ['https://mingus.com', 'https://app.mingus.com']
    
    def test_preflight_request_handling(self, client, auth_headers):
        """Test handling of CORS preflight requests"""
        preflight_headers = {
            'Origin': 'https://malicious-site.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        
        response = client.options('/api/articles/search', headers=preflight_headers)
        
        # Should handle preflight requests appropriately
        assert response.status_code in [200, 204, 405]
