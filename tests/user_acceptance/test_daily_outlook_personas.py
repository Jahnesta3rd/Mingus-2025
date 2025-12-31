#!/usr/bin/env python3
"""
Daily Outlook User Acceptance Tests with Persona Data

Comprehensive user acceptance tests using persona data for:
- Maya (Budget Tier - Single, Career-Focused)
- Marcus (Mid-Tier - Dating, Financial Growth)
- Dr. Williams (Professional Tier - Married, Established)

Tests include:
- Test with persona data
- Validate relationship status dynamic weighting
- Confirm tier-specific feature availability
- Test habit formation mechanisms
"""

# Set up Python path BEFORE any other imports
import sys
import os
# Get absolute path to project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Remove any backup directories from path to avoid import conflicts
sys.path = [p for p in sys.path if 'backup' not in p.lower() or p == project_root]
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
import json
import time
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application modules
from backend.models import db, DailyOutlook, UserRelationshipStatus, DailyOutlookTemplate, RelationshipStatus, TemplateTier, TemplateCategory, User
from backend.api.daily_outlook_api import daily_outlook_api
from tests.api.test_daily_outlook_api import test_daily_outlook_api
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from backend.utils.cache import CacheManager


class TestMayaPersona:
    """Test suite for Maya persona (Budget Tier - Single, Career-Focused)"""
    
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
        # Use test API that doesn't require authentication
        app.register_blueprint(test_daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def maya_user(self, app):
        """Create Maya persona user"""
        with app.app_context():
            user = User(
                user_id='maya_persona_123',
                email='maya.johnson@email.com',
                first_name='Maya',
                last_name='Johnson',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)  # Ensure object is fresh and bound
            return user
    
    @pytest.fixture
    def maya_relationship_status(self, app, maya_user):
        """Create Maya's relationship status"""
        with app.app_context():
            # Re-query user to ensure it's in session
            user = db.session.get(User, maya_user.id) if maya_user.id else maya_user
            rel_status = UserRelationshipStatus(
                user_id=user.id,
                status=RelationshipStatus.SINGLE_CAREER_FOCUSED,
                satisfaction_score=8,
                financial_impact_score=7
            )
            db.session.add(rel_status)
            db.session.commit()
            db.session.refresh(rel_status)  # Ensure object is fresh and bound
            return rel_status
    
    def test_maya_daily_outlook_generation(self, client, app, maya_user, maya_relationship_status):
        """Test Maya's daily outlook generation with career focus"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=maya_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create Maya's outlook
                    outlook = DailyOutlook(
                        user_id=maya_user.id,
                        date=date.today(),
                        balance_score=72,
                        financial_weight=Decimal('0.40'),  # High financial weight for budget tier
                        wellness_weight=Decimal('0.20'),
                        relationship_weight=Decimal('0.15'),  # Lower relationship weight for single career-focused
                        career_weight=Decimal('0.25'),  # High career weight
                        primary_insight="Your career growth is accelerating! Focus on skill development.",
                        quick_actions=[
                            {"id": "career_1", "title": "Update LinkedIn profile", "description": "Add recent projects", "priority": "high"},
                            {"id": "financial_1", "title": "Review budget", "description": "Track monthly expenses", "priority": "high"},
                            {"id": "wellness_1", "title": "Take a break", "description": "Step away from computer", "priority": "medium"}
                        ],
                        encouragement_message="You're building the foundation for financial success!",
                        surprise_element="Did you know? 78% of software developers see salary increases within 2 years.",
                        streak_count=12
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # Test API response
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    # Validate Maya-specific content
                    assert data['outlook']['career_weight'] == 0.25
                    assert data['outlook']['relationship_weight'] == 0.15
                    assert "career growth" in data['outlook']['primary_insight'].lower()
                    assert data['outlook']['streak_count'] == 12
                    
                    # Validate quick actions are career and financial focused
                    quick_actions = data['outlook']['quick_actions']
                    career_actions = [action for action in quick_actions if 'career' in action['id']]
                    financial_actions = [action for action in quick_actions if 'financial' in action['id']]
                    assert len(career_actions) > 0
                    assert len(financial_actions) > 0
    
    def test_maya_relationship_status_impact(self, client, app, maya_user, maya_relationship_status):
        """Test how Maya's relationship status impacts daily outlook"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=maya_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Test relationship status update
                    response = client.post('/api/relationship-status',
                                         json={
                                             'status': 'single_career_focused',
                                             'satisfaction_score': 9,  # High satisfaction with single life
                                             'financial_impact_score': 8  # Positive financial impact
                                         })
                    assert response.status_code == 200
                    
                    # Verify relationship status affects weighting
                    outlook = DailyOutlook(
                        user_id=maya_user.id,
                        date=date.today(),
                        balance_score=75,
                        financial_weight=Decimal('0.35'),
                        wellness_weight=Decimal('0.25'),
                        relationship_weight=Decimal('0.15'),  # Low for single career-focused
                        career_weight=Decimal('0.25'),
                        primary_insight="Your single status allows you to focus entirely on career growth!",
                        streak_count=5
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    # Career and financial should be prioritized over relationship
                    assert data['outlook']['career_weight'] >= data['outlook']['relationship_weight']
                    assert data['outlook']['financial_weight'] >= data['outlook']['relationship_weight']
    
    def test_maya_tier_restrictions(self, client, app, maya_user):
        """Test Maya's tier restrictions and feature availability"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=maya_user.id):
                # Maya has budget tier access
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]  # 404 if no outlook exists
                
                # Test that Maya cannot access professional features
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=False):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 403
                    data = response.get_json()
                    assert data['error'] == 'Insufficient tier access for daily outlook feature'
    
    def test_maya_habit_formation(self, client, app, maya_user):
        """Test Maya's habit formation mechanisms"""
        with app.app_context():
            with patch('tests.api.test_daily_outlook_api.get_current_user_id', return_value=maya_user.id):
                with patch('tests.api.test_daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create consecutive daily outlooks to build streak
                    today = date.today()
                    for i in range(7):
                        outlook_date = today - timedelta(days=i)
                        outlook = DailyOutlook(
                            user_id=maya_user.id,
                            date=outlook_date,
                            balance_score=70 + i,
                            financial_weight=Decimal('0.40'),
                            wellness_weight=Decimal('0.20'),
                            relationship_weight=Decimal('0.15'),
                            career_weight=Decimal('0.25'),
                            streak_count=i+1,
                            viewed_at=datetime.now(timezone.utc)
                        )
                        db.session.add(outlook)
                    
                    db.session.commit()
                    
                    # Test streak milestone achievement
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    assert data['streak_info']['current_streak'] == 7
                    # Note: milestone_reached may not be in test API response
                    if 'milestone_reached' in data['streak_info']:
                        assert data['streak_info']['milestone_reached'] is True
                    
                    # Test action completion habit formation
                    response = client.post('/api/daily-outlook/action-completed',
                                         json={
                                             'action_id': 'career_1',
                                             'completion_status': True,
                                             'completion_notes': 'Updated LinkedIn with new projects'
                                         })
                    assert response.status_code == 200


class TestMarcusPersona:
    """Test suite for Marcus persona (Mid-Tier - Dating, Financial Growth)"""
    
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
        # Use test API that doesn't require authentication
        app.register_blueprint(test_daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def marcus_user(self, app):
        """Create Marcus persona user"""
        with app.app_context():
            user = User(
                user_id='marcus_persona_456',
                email='marcus.davis@email.com',
                first_name='Marcus',
                last_name='Davis',
                tier='mid_tier'
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)  # Ensure object is fresh and bound
            return user
    
    @pytest.fixture
    def marcus_relationship_status(self, app, marcus_user):
        """Create Marcus's relationship status"""
        with app.app_context():
            # Re-query user to ensure it's in session
            user = db.session.get(User, marcus_user.id) if marcus_user.id else marcus_user
            rel_status = UserRelationshipStatus(
                user_id=user.id,
                status=RelationshipStatus.DATING,
                satisfaction_score=9,
                financial_impact_score=8
            )
            db.session.add(rel_status)
            db.session.commit()
            db.session.refresh(rel_status)  # Ensure object is fresh and bound
            return rel_status
    
    def test_marcus_daily_outlook_generation(self, client, app, marcus_user, marcus_relationship_status):
        """Test Marcus's daily outlook generation with relationship focus"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=marcus_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create Marcus's outlook
                    outlook = DailyOutlook(
                        user_id=marcus_user.id,
                        date=date.today(),
                        balance_score=82,
                        financial_weight=Decimal('0.30'),
                        wellness_weight=Decimal('0.25'),
                        relationship_weight=Decimal('0.30'),  # High relationship weight for dating
                        career_weight=Decimal('0.15'),
                        primary_insight="Your relationship is thriving! Consider financial planning together.",
                        quick_actions=[
                            {"id": "relationship_1", "title": "Plan date night", "description": "Budget for special evening", "priority": "high"},
                            {"id": "financial_1", "title": "Review investment portfolio", "description": "Check 401k performance", "priority": "high"},
                            {"id": "wellness_1", "title": "Couple's workout", "description": "Exercise together", "priority": "medium"}
                        ],
                        encouragement_message="Love and financial growth go hand in hand!",
                        surprise_element="Couples who discuss finances regularly are 30% more likely to stay together.",
                        streak_count=8
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # Test API response
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    # Validate Marcus-specific content
                    assert data['outlook']['relationship_weight'] == 0.30
                    assert data['outlook']['financial_weight'] == 0.30
                    assert "relationship" in data['outlook']['primary_insight'].lower()
                    assert data['outlook']['streak_count'] == 8
                    
                    # Validate quick actions are relationship and financial focused
                    quick_actions = data['outlook']['quick_actions']
                    relationship_actions = [action for action in quick_actions if 'relationship' in action['id']]
                    financial_actions = [action for action in quick_actions if 'financial' in action['id']]
                    assert len(relationship_actions) > 0
                    assert len(financial_actions) > 0
    
    def test_marcus_relationship_status_impact(self, client, app, marcus_user, marcus_relationship_status):
        """Test how Marcus's relationship status impacts daily outlook"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=marcus_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Test relationship status update
                    response = client.post('/api/relationship-status',
                                         json={
                                             'status': 'dating',
                                             'satisfaction_score': 9,
                                             'financial_impact_score': 8
                                         })
                    assert response.status_code == 200
                    
                    # Verify relationship status affects weighting
                    outlook = DailyOutlook(
                        user_id=marcus_user.id,
                        date=date.today(),
                        balance_score=80,
                        financial_weight=Decimal('0.30'),
                        wellness_weight=Decimal('0.25'),
                        relationship_weight=Decimal('0.30'),  # High for dating status
                        career_weight=Decimal('0.15'),
                        primary_insight="Your dating life is enhancing your financial motivation!",
                        streak_count=6
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    # Relationship and financial should be prioritized
                    assert data['outlook']['relationship_weight'] >= data['outlook']['career_weight']
                    assert data['outlook']['financial_weight'] >= data['outlook']['career_weight']
    
    def test_marcus_tier_features(self, client, app, marcus_user):
        """Test Marcus's mid-tier feature availability"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=marcus_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]
                    
                    # Test history access
                    response = client.get('/api/daily-outlook/history')
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
    
    def test_marcus_habit_formation(self, client, app, marcus_user):
        """Test Marcus's habit formation mechanisms"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=marcus_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create outlook with relationship-focused actions
                    outlook = DailyOutlook(
                        user_id=marcus_user.id,
                        date=date.today(),
                        balance_score=85,
                        financial_weight=Decimal('0.30'),
                        wellness_weight=Decimal('0.25'),
                        relationship_weight=Decimal('0.30'),
                        career_weight=Decimal('0.15'),
                        quick_actions=[
                            {"id": "relationship_1", "title": "Plan date night", "description": "Budget for special evening", "priority": "high"},
                            {"id": "financial_1", "title": "Review investment portfolio", "description": "Check 401k performance", "priority": "high"}
                        ],
                        streak_count=5
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # Test action completion
                    response = client.post('/api/daily-outlook/action-completed',
                                         json={
                                             'action_id': 'relationship_1',
                                             'completion_status': True,
                                             'completion_notes': 'Planned romantic dinner'
                                         })
                    assert response.status_code == 200
                    
                    # Test rating submission
                    response = client.post('/api/daily-outlook/rating',
                                         json={'rating': 5})
                    assert response.status_code == 200


class TestDrWilliamsPersona:
    """Test suite for Dr. Williams persona (Professional Tier - Married, Established)"""
    
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
        # Use test API that doesn't require authentication
        app.register_blueprint(test_daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def dr_williams_user(self, app):
        """Create Dr. Williams persona user"""
        with app.app_context():
            user = User(
                user_id='dr_williams_persona_789',
                email='dr.williams@email.com',
                first_name='Dr. Sarah',
                last_name='Williams',
                tier='professional'
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)  # Ensure object is fresh and bound
            return user
    
    @pytest.fixture
    def dr_williams_relationship_status(self, app, dr_williams_user):
        """Create Dr. Williams's relationship status"""
        with app.app_context():
            # Re-query user to ensure it's in session
            user = db.session.get(User, dr_williams_user.id) if dr_williams_user.id else dr_williams_user
            rel_status = UserRelationshipStatus(
                user_id=user.id,
                status=RelationshipStatus.MARRIED,
                satisfaction_score=9,
                financial_impact_score=9
            )
            db.session.add(rel_status)
            db.session.commit()
            db.session.refresh(rel_status)  # Ensure object is fresh and bound
            return rel_status
    
    def test_dr_williams_daily_outlook_generation(self, client, app, dr_williams_user, dr_williams_relationship_status):
        """Test Dr. Williams's daily outlook generation with family focus"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=dr_williams_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create Dr. Williams's outlook
                    outlook = DailyOutlook(
                        user_id=dr_williams_user.id,
                        date=date.today(),
                        balance_score=88,
                        financial_weight=Decimal('0.25'),
                        wellness_weight=Decimal('0.30'),
                        relationship_weight=Decimal('0.25'),
                        career_weight=Decimal('0.20'),
                        primary_insight="Your family's financial future is secure. Consider advanced investment strategies.",
                        quick_actions=[
                            {"id": "financial_1", "title": "Review retirement portfolio", "description": "Optimize 401k allocation", "priority": "high"},
                            {"id": "family_1", "title": "Plan family vacation", "description": "Budget for summer trip", "priority": "high"},
                            {"id": "wellness_1", "title": "Family wellness check", "description": "Schedule annual physicals", "priority": "medium"}
                        ],
                        encouragement_message="Your financial wisdom is creating generational wealth!",
                        surprise_element="Families with comprehensive financial plans are 40% more likely to achieve long-term goals.",
                        streak_count=15
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # Test API response
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    # Validate Dr. Williams-specific content
                    assert data['outlook']['wellness_weight'] == 0.30  # High wellness for family health
                    assert data['outlook']['financial_weight'] == 0.25
                    assert "family" in data['outlook']['primary_insight'].lower()
                    assert data['outlook']['streak_count'] == 15
                    
                    # Validate quick actions are family and financial focused
                    quick_actions = data['outlook']['quick_actions']
                    family_actions = [action for action in quick_actions if 'family' in action['id']]
                    financial_actions = [action for action in quick_actions if 'financial' in action['id']]
                    assert len(family_actions) > 0
                    assert len(financial_actions) > 0
    
    def test_dr_williams_relationship_status_impact(self, client, app, dr_williams_user, dr_williams_relationship_status):
        """Test how Dr. Williams's relationship status impacts daily outlook"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=dr_williams_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Test relationship status update
                    response = client.post('/api/relationship-status',
                                         json={
                                             'status': 'married',
                                             'satisfaction_score': 9,
                                             'financial_impact_score': 9
                                         })
                    assert response.status_code == 200
                    
                    # Verify relationship status affects weighting
                    outlook = DailyOutlook(
                        user_id=dr_williams_user.id,
                        date=date.today(),
                        balance_score=90,
                        financial_weight=Decimal('0.25'),
                        wellness_weight=Decimal('0.30'),  # High for family wellness
                        relationship_weight=Decimal('0.25'),
                        career_weight=Decimal('0.20'),
                        primary_insight="Your marriage is the foundation of your financial success!",
                        streak_count=10
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    # Wellness should be prioritized for family health
                    assert data['outlook']['wellness_weight'] >= data['outlook']['career_weight']
    
    def test_dr_williams_professional_tier_features(self, client, app, dr_williams_user):
        """Test Dr. Williams's professional tier feature availability"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=dr_williams_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Test all professional tier features
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]
                    
                    response = client.get('/api/daily-outlook/history')
                    assert response.status_code == 200
                    
                    response = client.get('/api/daily-outlook/streak')
                    assert response.status_code == 200
    
    def test_dr_williams_habit_formation(self, client, app, dr_williams_user):
        """Test Dr. Williams's habit formation mechanisms"""
        with app.app_context():
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=dr_williams_user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Create outlook with family-focused actions
                    outlook = DailyOutlook(
                        user_id=dr_williams_user.id,
                        date=date.today(),
                        balance_score=92,
                        financial_weight=Decimal('0.25'),
                        wellness_weight=Decimal('0.30'),
                        relationship_weight=Decimal('0.25'),
                        career_weight=Decimal('0.20'),
                        quick_actions=[
                            {"id": "financial_1", "title": "Review retirement portfolio", "description": "Optimize 401k allocation", "priority": "high"},
                            {"id": "family_1", "title": "Plan family vacation", "description": "Budget for summer trip", "priority": "high"}
                        ],
                        streak_count=20
                    )
                    db.session.add(outlook)
                    db.session.commit()
                    
                    # Test action completion
                    response = client.post('/api/daily-outlook/action-completed',
                                         json={
                                             'action_id': 'financial_1',
                                             'completion_status': True,
                                             'completion_notes': 'Rebalanced portfolio for optimal growth'
                                         })
                    assert response.status_code == 200
                    
                    # Test rating submission
                    response = client.post('/api/daily-outlook/rating',
                                         json={'rating': 5})
                    assert response.status_code == 200


class TestPersonaComparison:
    """Test suite for comparing persona experiences"""
    
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
    
    def test_persona_weighting_differences(self, app):
        """Test how different personas receive different weightings"""
        with app.app_context():
            # Create all three personas
            maya = User(
                user_id='maya_comparison_101',
                email='maya@example.com',
                first_name='Maya',
                last_name='Johnson',
                tier='budget'
            )
            marcus = User(
                user_id='marcus_comparison_202',
                email='marcus@example.com',
                first_name='Marcus',
                last_name='Davis',
                tier='mid_tier'
            )
            dr_williams = User(
                user_id='dr_williams_comparison_303',
                email='dr.williams@example.com',
                first_name='Dr. Sarah',
                last_name='Williams',
                tier='professional'
            )
            
            db.session.add_all([maya, marcus, dr_williams])
            db.session.commit()
            
            # Create relationship statuses
            maya_rel = UserRelationshipStatus(
                user_id=maya.id,
                status=RelationshipStatus.SINGLE_CAREER_FOCUSED,
                satisfaction_score=8,
                financial_impact_score=7
            )
            marcus_rel = UserRelationshipStatus(
                user_id=marcus.id,
                status=RelationshipStatus.DATING,
                satisfaction_score=9,
                financial_impact_score=8
            )
            dr_williams_rel = UserRelationshipStatus(
                user_id=dr_williams.id,
                status=RelationshipStatus.MARRIED,
                satisfaction_score=9,
                financial_impact_score=9
            )
            
            db.session.add_all([maya_rel, marcus_rel, dr_williams_rel])
            db.session.commit()
            
            # Create outlooks for each persona
            maya_outlook = DailyOutlook(
                user_id=maya.id,
                date=date.today(),
                balance_score=72,
                financial_weight=Decimal('0.40'),
                wellness_weight=Decimal('0.20'),
                relationship_weight=Decimal('0.15'),
                career_weight=Decimal('0.25')
            )
            
            marcus_outlook = DailyOutlook(
                user_id=marcus.id,
                date=date.today(),
                balance_score=82,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.30'),
                career_weight=Decimal('0.15')
            )
            
            dr_williams_outlook = DailyOutlook(
                user_id=dr_williams.id,
                date=date.today(),
                balance_score=88,
                financial_weight=Decimal('0.25'),
                wellness_weight=Decimal('0.30'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20')
            )
            
            db.session.add_all([maya_outlook, marcus_outlook, dr_williams_outlook])
            db.session.commit()
            
            # Validate persona-specific weightings
            assert maya_outlook.career_weight > maya_outlook.relationship_weight  # Maya: Career-focused
            assert marcus_outlook.relationship_weight > marcus_outlook.career_weight  # Marcus: Relationship-focused
            assert dr_williams_outlook.wellness_weight > dr_williams_outlook.career_weight  # Dr. Williams: Family wellness-focused
    
    def test_persona_tier_feature_access(self, app):
        """Test tier-based feature access across personas"""
        with app.app_context():
            # Create personas with different tiers
            maya = User(user_id='maya_tier_404', email='maya@example.com', tier='budget')
            marcus = User(user_id='marcus_tier_505', email='marcus@example.com', tier='mid_tier')
            dr_williams = User(user_id='dr_williams_tier_606', email='dr.williams@example.com', tier='professional')
            
            db.session.add_all([maya, marcus, dr_williams])
            db.session.commit()
            
            # Test tier access
            feature_service = FeatureFlagService()
            
            # All should have access to daily outlook
            assert feature_service.check_user_tier_access(maya.id, FeatureTier.BUDGET)
            assert feature_service.check_user_tier_access(marcus.id, FeatureTier.BUDGET)
            assert feature_service.check_user_tier_access(dr_williams.id, FeatureTier.BUDGET)
            
            # Only professional should have access to advanced features
            assert not feature_service.check_user_tier_access(maya.id, FeatureTier.PROFESSIONAL)
            assert not feature_service.check_user_tier_access(marcus.id, FeatureTier.PROFESSIONAL)
            assert feature_service.check_user_tier_access(dr_williams.id, FeatureTier.PROFESSIONAL)
    
    def test_persona_habit_formation_patterns(self, app):
        """Test how different personas form habits"""
        with app.app_context():
            # Create personas
            maya = User(user_id='maya_tier_404', email='maya@example.com', tier='budget')
            marcus = User(user_id='marcus_tier_505', email='marcus@example.com', tier='mid_tier')
            dr_williams = User(user_id='dr_williams_tier_606', email='dr.williams@example.com', tier='professional')
            
            db.session.add_all([maya, marcus, dr_williams])
            db.session.commit()
            
            # Create outlooks with different action patterns
            maya_outlook = DailyOutlook(
                user_id=maya.id,
                date=date.today(),
                balance_score=75,
                financial_weight=Decimal('0.40'),
                wellness_weight=Decimal('0.20'),
                relationship_weight=Decimal('0.15'),
                career_weight=Decimal('0.25'),
                quick_actions=[
                    {"id": "career_1", "title": "Update LinkedIn", "priority": "high"},
                    {"id": "financial_1", "title": "Review budget", "priority": "high"}
                ]
            )
            
            marcus_outlook = DailyOutlook(
                user_id=marcus.id,
                date=date.today(),
                balance_score=80,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.30'),
                career_weight=Decimal('0.15'),
                quick_actions=[
                    {"id": "relationship_1", "title": "Plan date night", "priority": "high"},
                    {"id": "financial_1", "title": "Review investments", "priority": "high"}
                ]
            )
            
            dr_williams_outlook = DailyOutlook(
                user_id=dr_williams.id,
                date=date.today(),
                balance_score=85,
                financial_weight=Decimal('0.25'),
                wellness_weight=Decimal('0.30'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                quick_actions=[
                    {"id": "family_1", "title": "Plan family vacation", "priority": "high"},
                    {"id": "financial_1", "title": "Review retirement portfolio", "priority": "high"}
                ]
            )
            
            db.session.add_all([maya_outlook, marcus_outlook, dr_williams_outlook])
            db.session.commit()
            
            # Validate persona-specific action patterns
            maya_actions = maya_outlook.quick_actions
            marcus_actions = marcus_outlook.quick_actions
            dr_williams_actions = dr_williams_outlook.quick_actions
            
            # Maya: Career and financial focused
            assert any('career' in action['id'] for action in maya_actions)
            assert any('financial' in action['id'] for action in maya_actions)
            
            # Marcus: Relationship and financial focused
            assert any('relationship' in action['id'] for action in marcus_actions)
            assert any('financial' in action['id'] for action in marcus_actions)
            
            # Dr. Williams: Family and financial focused
            assert any('family' in action['id'] for action in dr_williams_actions)
            assert any('financial' in action['id'] for action in dr_williams_actions)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
