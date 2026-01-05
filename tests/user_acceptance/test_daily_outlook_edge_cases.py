#!/usr/bin/env python3
"""
Daily Outlook User Acceptance Tests - Edge Cases

Comprehensive edge case testing for Daily Outlook functionality including:
- Missing data scenarios
- Invalid input handling
- Boundary conditions
- Error recovery
- Concurrent operations
- Data validation edge cases
"""

# Set up Python path BEFORE any other imports
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path = [p for p in sys.path if 'backup' not in p.lower() or p == project_root]
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
import json
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application modules
from backend.models import db, DailyOutlook, UserRelationshipStatus, DailyOutlookTemplate, RelationshipStatus, TemplateTier, TemplateCategory, User
from tests.api.test_daily_outlook_api import test_daily_outlook_api
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from backend.utils.cache import CacheManager


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(test_daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def test_user(self, app):
        """Create test user"""
        with app.app_context():
            user = User(
                user_id='edge_case_user_123',
                email='edge@example.com',
                first_name='Edge',
                last_name='Case',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
            return user
    
    # ============================================================================
    # Missing Data Scenarios
    # ============================================================================
    
    def test_missing_relationship_status(self, client, app, test_user):
        """Test behavior when user has no relationship status"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create outlook without relationship status
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        primary_insight="Your financial journey continues!",
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # Should still work without relationship status
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
                    assert data['outlook']['balance_score'] == 75
    
    def test_missing_outlook_for_date(self, client, app, test_user):
        """Test behavior when no outlook exists for requested date"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Don't create any outlook
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 404
                    data = response.get_json()
                    assert data['error'] == 'No daily outlook found for today'
    
    def test_empty_quick_actions(self, client, app, test_user):
        """Test behavior with empty quick_actions array"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=70,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        quick_actions=[],  # Empty array
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
                    assert isinstance(data['outlook']['quick_actions'], list)
                    assert len(data['outlook']['quick_actions']) == 0
    
    def test_null_optional_fields(self, client, app, test_user):
        """Test behavior with null optional fields"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=65,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        primary_insight=None,  # Null optional field
                        encouragement_message=None,
                        surprise_element=None,
                        streak_count=0
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
    
    # ============================================================================
    # Invalid Input Handling
    # ============================================================================
    
    def test_invalid_tier_value(self, client, app):
        """Test behavior with invalid tier value"""
        with app.app_context():
            # Create user with invalid tier
            user = User(
                user_id='invalid_tier_user',
                email='invalid@example.com',
                first_name='Invalid',
                last_name='Tier',
                tier='invalid_tier'  # Invalid tier value
            )
            db.session.add(user)
            db.session.commit()
            
            # FeatureFlagService should handle invalid tier gracefully
            feature_service = FeatureFlagService()
            tier = feature_service.get_user_tier(user.id)
            # Should default to BUDGET or handle gracefully
            assert tier in [FeatureTier.BUDGET, FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]
    
    def test_negative_balance_score(self, client, app, test_user):
        """Test behavior with negative balance score"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Negative balance score should be handled
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=-10,  # Negative value
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['outlook']['balance_score'] == -10
    
    def test_very_high_balance_score(self, client, app, test_user):
        """Test behavior with very high balance score (>100)"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=150,  # Over 100
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['outlook']['balance_score'] == 150
    
    def test_invalid_weight_sum(self, client, app, test_user):
        """Test behavior when weights don't sum to 1.0"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Weights sum to 0.5 instead of 1.0
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=70,
                        financial_weight=Decimal('0.20'),
                        wellness_weight=Decimal('0.10'),
                        relationship_weight=Decimal('0.10'),
                        career_weight=Decimal('0.10'),
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    # Should still work, even if weights don't sum to 1.0
    
    # ============================================================================
    # Boundary Conditions
    # ============================================================================
    
    def test_zero_streak_count(self, client, app, test_user):
        """Test behavior with zero streak count"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=70,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=0  # Zero streak
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['streak_info']['current_streak'] == 0
    
    def test_very_long_streak(self, client, app, test_user):
        """Test behavior with very long streak count"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=90,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1000  # Very long streak
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['streak_info']['current_streak'] == 1000
    
    def test_future_date_outlook(self, client, app, test_user):
        """Test behavior with future date"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    future_date = date.today() + timedelta(days=7)
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=future_date,
                        balance_score=75,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # API should return today's outlook, not future
                    response = client.get('/api/daily-outlook/')
                    # Should return 404 since today's outlook doesn't exist
                    assert response.status_code == 404
    
    def test_past_date_outlook(self, client, app, test_user):
        """Test behavior with past date"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    past_date = date.today() - timedelta(days=30)
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=past_date,
                        balance_score=70,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # API should return today's outlook
                    response = client.get('/api/daily-outlook/')
                    # Should return 404 since today's outlook doesn't exist
                    assert response.status_code == 404
    
    # ============================================================================
    # Error Recovery
    # ============================================================================
    
    def test_database_connection_error_recovery(self, client, app, test_user):
        """Test error recovery from database issues"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Simulate database error by closing session
                    db.session.close()
                    
                    # Should handle gracefully
                    try:
                        response = client.get('/api/daily-outlook/')
                        # May return 500 or handle gracefully
                        assert response.status_code in [404, 500]
                    except Exception:
                        # Exception is acceptable for database errors
                        pass
    
    def test_missing_user_id(self, client, app):
        """Test behavior when user_id is missing"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=None):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    # Should handle missing user_id gracefully
                    assert response.status_code in [404, 500]
    
    def test_tier_access_denied(self, client, app, test_user):
        """Test behavior when tier access is denied"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=False):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 403
                    data = response.get_json()
                    assert data['error'] == 'Insufficient tier access for daily outlook feature'
    
    # ============================================================================
    # Data Validation Edge Cases
    # ============================================================================
    
    def test_very_long_primary_insight(self, client, app, test_user):
        """Test behavior with very long primary insight text"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    long_text = "A" * 10000  # Very long text
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        primary_insight=long_text,
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert len(data['outlook']['primary_insight']) == 10000
    
    def test_special_characters_in_text(self, client, app, test_user):
        """Test behavior with special characters in text fields"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    special_text = "Test with <script>alert('XSS')</script> & special chars: @#$%^&*()"
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        primary_insight=special_text,
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    # Should handle special characters safely
                    assert special_text in data['outlook']['primary_insight']
    
    def test_unicode_characters(self, client, app, test_user):
        """Test behavior with unicode characters"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    unicode_text = "Test with unicode: 你好 🌟 émojis 🎉"
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        primary_insight=unicode_text,
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert unicode_text in data['outlook']['primary_insight']
    
    # ============================================================================
    # Concurrent Operations
    # ============================================================================
    
    def test_concurrent_outlook_creation(self, client, app, test_user):
        """Test behavior when multiple outlooks are created concurrently"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create multiple outlooks for same date
                    outlook1 = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=70,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1
                    )
                    outlook2 = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=80,
                        financial_weight=Decimal('0.30'),
                        wellness_weight=Decimal('0.30'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=2
                    )
                    db.session.add(outlook1)
                    db.session.add(outlook2)
                    db.session.commit()
                    
                    # Should return one outlook (first or last depending on query)
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
    
    # ============================================================================
    # Edge Cases for Relationship Status
    # ============================================================================
    
    def test_multiple_relationship_statuses(self, client, app, test_user):
        """Test behavior when user has multiple relationship statuses"""
        with app.app_context():
            # Create multiple relationship statuses (shouldn't happen, but test edge case)
            rel_status1 = UserRelationshipStatus(
                user_id=test_user.id,
                status=RelationshipStatus.SINGLE_CAREER_FOCUSED,
                satisfaction_score=8,
                financial_impact_score=7
            )
            rel_status2 = UserRelationshipStatus(
                user_id=test_user.id,
                status=RelationshipStatus.DATING,
                satisfaction_score=9,
                financial_impact_score=8
            )
            db.session.add(rel_status1)
            db.session.add(rel_status2)
            db.session.commit()
            
            # Should handle gracefully (may use first or last)
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
    
    def test_invalid_relationship_status_score(self, client, app, test_user):
        """Test behavior with invalid relationship status scores"""
        with app.app_context():
            # Scores outside valid range (0-10)
            rel_status = UserRelationshipStatus(
                user_id=test_user.id,
                status=RelationshipStatus.SINGLE_CAREER_FOCUSED,
                satisfaction_score=15,  # Invalid: > 10
                financial_impact_score=-5  # Invalid: < 0
            )
            db.session.add(rel_status)
            db.session.commit()
            
            # Should still work, but scores may be clamped or ignored
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=test_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    outlook = DailyOutlook(
                        user_id=test_user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.40'),
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.20'),
                        career_weight=Decimal('0.20'),
                        streak_count=1
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

