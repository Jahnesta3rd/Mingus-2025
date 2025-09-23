#!/usr/bin/env python3
"""
Test suite for Daily Outlook API endpoints

This test suite validates all the Daily Outlook API endpoints
with proper authentication, validation, and error handling.
"""

import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
from flask import Flask
from backend.models.database import db
from backend.models.user_models import User
from backend.models.daily_outlook import DailyOutlook, UserRelationshipStatus, RelationshipStatus
from backend.api.daily_outlook_api import daily_outlook_api
from backend.auth.decorators import get_current_user_id

class TestDailyOutlookAPI:
    """Test class for Daily Outlook API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        
        db.init_app(app)
        app.register_blueprint(daily_outlook_api)
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def test_user(self, app):
        """Create test user"""
        with app.app_context():
            user = User(
                user_id='test_user_123',
                email='test@example.com',
                first_name='Test',
                last_name='User'
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def test_outlook(self, app, test_user):
        """Create test daily outlook"""
        with app.app_context():
            outlook = DailyOutlook(
                user_id=test_user.id,
                date=date.today(),
                balance_score=85,
                financial_weight=0.30,
                wellness_weight=0.25,
                relationship_weight=0.25,
                career_weight=0.20,
                primary_insight='Test insight for today',
                quick_actions=[
                    {'id': 'action_1', 'title': 'Test Action', 'description': 'Test description'}
                ],
                encouragement_message='Keep up the great work!',
                surprise_element='Did you know...',
                streak_count=5
            )
            db.session.add(outlook)
            db.session.commit()
            return outlook
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {
            'Authorization': 'Bearer test-jwt-token',
            'Content-Type': 'application/json'
        }
    
    def test_get_todays_outlook_success(self, client, test_user, test_outlook, auth_headers):
        """Test successful retrieval of today's outlook"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get('/api/daily-outlook/', headers=auth_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'outlook' in data
                assert data['outlook']['user_id'] == test_user.id
                assert data['outlook']['balance_score'] == 85
                assert 'streak_info' in data
    
    def test_get_todays_outlook_not_found(self, client, test_user, auth_headers):
        """Test when no outlook is available for today"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get('/api/daily-outlook/', headers=auth_headers)
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['error'] == 'No outlook available'
    
    def test_get_todays_outlook_unauthorized(self, client, auth_headers):
        """Test unauthorized access"""
        response = client.get('/api/daily-outlook/', headers=auth_headers)
        assert response.status_code == 401
    
    def test_get_todays_outlook_tier_restricted(self, client, test_user, auth_headers):
        """Test tier-based access restriction"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=False):
                response = client.get('/api/daily-outlook/', headers=auth_headers)
                
                assert response.status_code == 403
                data = response.get_json()
                assert data['error'] == 'Feature not available'
                assert data['upgrade_required'] is True
    
    def test_get_outlook_history_success(self, client, test_user, auth_headers):
        """Test successful retrieval of outlook history"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get('/api/daily-outlook/history', headers=auth_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'outlooks' in data
                assert 'pagination' in data
                assert 'engagement_metrics' in data
    
    def test_get_outlook_history_with_filters(self, client, test_user, auth_headers):
        """Test outlook history with date filters"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                start_date = (date.today() - timedelta(days=7)).isoformat()
                end_date = date.today().isoformat()
                
                response = client.get(
                    f'/api/daily-outlook/history?start_date={start_date}&end_date={end_date}&page=1&per_page=10',
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
    
    def test_get_outlook_history_invalid_date(self, client, test_user, auth_headers):
        """Test outlook history with invalid date format"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get(
                    '/api/daily-outlook/history?start_date=invalid-date',
                    headers=auth_headers
                )
                
                assert response.status_code == 400
                data = response.get_json()
                assert data['error'] == 'Invalid date format'
    
    def test_mark_action_completed_success(self, client, test_user, test_outlook, auth_headers):
        """Test successful action completion"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                with patch('backend.api.daily_outlook_api.validate_csrf_token', return_value=True):
                    data = {
                        'action_id': 'action_1',
                        'completion_status': True,
                        'completion_notes': 'Completed successfully'
                    }
                    
                    response = client.post(
                        '/api/daily-outlook/action-completed',
                        headers=auth_headers,
                        json=data
                    )
                    
                    assert response.status_code == 200
                    response_data = response.get_json()
                    assert response_data['success'] is True
                    assert response_data['action_id'] == 'action_1'
                    assert response_data['completion_status'] is True
    
    def test_mark_action_completed_validation_error(self, client, test_user, auth_headers):
        """Test action completion with validation error"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                with patch('backend.api.daily_outlook_api.validate_csrf_token', return_value=True):
                    data = {
                        'action_id': '',  # Invalid empty action_id
                        'completion_status': True
                    }
                    
                    response = client.post(
                        '/api/daily-outlook/action-completed',
                        headers=auth_headers,
                        json=data
                    )
                    
                    assert response.status_code == 400
                    response_data = response.get_json()
                    assert response_data['error'] == 'Validation failed'
    
    def test_submit_rating_success(self, client, test_user, test_outlook, auth_headers):
        """Test successful rating submission"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                with patch('backend.api.daily_outlook_api.validate_csrf_token', return_value=True):
                    data = {
                        'rating': 4,
                        'feedback': 'Great insights today!'
                    }
                    
                    response = client.post(
                        '/api/daily-outlook/rating',
                        headers=auth_headers,
                        json=data
                    )
                    
                    assert response.status_code == 200
                    response_data = response.get_json()
                    assert response_data['success'] is True
                    assert response_data['rating'] == 4
                    assert 'ab_test_flags' in response_data
    
    def test_submit_rating_invalid_rating(self, client, test_user, auth_headers):
        """Test rating submission with invalid rating"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                with patch('backend.api.daily_outlook_api.validate_csrf_token', return_value=True):
                    data = {
                        'rating': 6,  # Invalid rating (should be 1-5)
                        'feedback': 'Test feedback'
                    }
                    
                    response = client.post(
                        '/api/daily-outlook/rating',
                        headers=auth_headers,
                        json=data
                    )
                    
                    assert response.status_code == 400
                    response_data = response.get_json()
                    assert response_data['error'] == 'Validation failed'
    
    def test_get_streak_info_success(self, client, test_user, auth_headers):
        """Test successful streak info retrieval"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get('/api/daily-outlook/streak', headers=auth_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'streak_info' in data
                assert 'current_streak' in data['streak_info']
                assert 'milestones' in data['streak_info']
    
    def test_update_relationship_status_success(self, client, test_user, auth_headers):
        """Test successful relationship status update"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                with patch('backend.api.daily_outlook_api.validate_csrf_token', return_value=True):
                    data = {
                        'status': 'dating',
                        'satisfaction_score': 8,
                        'financial_impact_score': 6
                    }
                    
                    response = client.post(
                        '/api/relationship-status',
                        headers=auth_headers,
                        json=data
                    )
                    
                    assert response.status_code == 200
                    response_data = response.get_json()
                    assert response_data['success'] is True
                    assert 'relationship_status' in response_data
    
    def test_update_relationship_status_invalid_status(self, client, test_user, auth_headers):
        """Test relationship status update with invalid status"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                with patch('backend.api.daily_outlook_api.validate_csrf_token', return_value=True):
                    data = {
                        'status': 'invalid_status',
                        'satisfaction_score': 8,
                        'financial_impact_score': 6
                    }
                    
                    response = client.post(
                        '/api/relationship-status',
                        headers=auth_headers,
                        json=data
                    )
                    
                    assert response.status_code == 400
                    response_data = response.get_json()
                    assert response_data['error'] == 'Validation failed'
    
    def test_missing_authentication(self, client):
        """Test endpoints without authentication"""
        response = client.get('/api/daily-outlook/')
        assert response.status_code == 401
    
    def test_missing_csrf_token(self, client, test_user, auth_headers):
        """Test state-changing operations without CSRF token"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=test_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                with patch('backend.api.daily_outlook_api.validate_csrf_token', return_value=False):
                    data = {
                        'action_id': 'action_1',
                        'completion_status': True
                    }
                    
                    response = client.post(
                        '/api/daily-outlook/action-completed',
                        headers=auth_headers,
                        json=data
                    )
                    
                    assert response.status_code == 403

def run_manual_tests():
    """Run manual tests without pytest framework"""
    print("=== Daily Outlook API Manual Tests ===\n")
    
    # Test 1: Test endpoint structure
    print("1. Testing endpoint structure...")
    try:
        from backend.api.daily_outlook_api import daily_outlook_api
        print("✅ Daily outlook API blueprint imported successfully")
        print(f"   Blueprint name: {daily_outlook_api.name}")
        print(f"   URL prefix: {daily_outlook_api.url_prefix}")
        print(f"   Registered routes: {len(daily_outlook_api.decorators)}")
    except Exception as e:
        print(f"❌ Failed to import daily outlook API: {e}")
    
    # Test 2: Test model imports
    print("\n2. Testing model imports...")
    try:
        from backend.models.daily_outlook import DailyOutlook, UserRelationshipStatus, RelationshipStatus
        print("✅ Daily outlook models imported successfully")
        print(f"   DailyOutlook model: {DailyOutlook.__name__}")
        print(f"   UserRelationshipStatus model: {UserRelationshipStatus.__name__}")
        print(f"   RelationshipStatus enum: {RelationshipStatus.__name__}")
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
    
    # Test 3: Test validation schemas
    print("\n3. Testing validation schemas...")
    try:
        from backend.api.daily_outlook_api import (
            ActionCompletedSchema, RatingSchema, RelationshipStatusSchema, HistoryQuerySchema
        )
        print("✅ Validation schemas imported successfully")
        print("   - ActionCompletedSchema")
        print("   - RatingSchema")
        print("   - RelationshipStatusSchema")
        print("   - HistoryQuerySchema")
    except Exception as e:
        print(f"❌ Failed to import validation schemas: {e}")
    
    # Test 4: Test utility functions
    print("\n4. Testing utility functions...")
    try:
        from backend.api.daily_outlook_api import (
            check_user_tier_access, validate_request_data, calculate_streak_count, update_user_relationship_status
        )
        print("✅ Utility functions imported successfully")
        print("   - check_user_tier_access")
        print("   - validate_request_data")
        print("   - calculate_streak_count")
        print("   - update_user_relationship_status")
    except Exception as e:
        print(f"❌ Failed to import utility functions: {e}")
    
    # Test 5: Test authentication decorators
    print("\n5. Testing authentication decorators...")
    try:
        from backend.auth.decorators import require_auth, require_csrf, get_current_user_id
        print("✅ Authentication decorators imported successfully")
        print("   - require_auth")
        print("   - require_csrf")
        print("   - get_current_user_id")
    except Exception as e:
        print(f"❌ Failed to import authentication decorators: {e}")
    
    # Test 6: Test feature flag service
    print("\n6. Testing feature flag service...")
    try:
        from backend.services.feature_flag_service import FeatureFlagService, FeatureTier, FeatureFlag
        feature_service = FeatureFlagService()
        print("✅ Feature flag service imported successfully")
        print(f"   Available tiers: {[tier.value for tier in FeatureTier]}")
        print(f"   Available flags: {[flag.value for flag in FeatureFlag]}")
    except Exception as e:
        print(f"❌ Failed to import feature flag service: {e}")
    
    print("\n=== Manual Tests Complete ===")

if __name__ == '__main__':
    # Run manual tests
    run_manual_tests()
    
    # Example of running pytest tests (requires pytest to be installed)
    print("\n=== Running Pytest Tests ===")
    print("To run the full test suite, install pytest and run:")
    print("pytest backend/api/test_daily_outlook_api.py -v")
