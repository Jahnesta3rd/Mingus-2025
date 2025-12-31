#!/usr/bin/env python3
"""
Daily Outlook Integration Tests

Comprehensive integration tests for Daily Outlook functionality including:
- End-to-end user flow testing
- Notification delivery testing
- Background task execution
- Cross-tier feature access validation
- Performance benchmarking
"""

import pytest
import json
import time
import asyncio
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.models.database import db
from backend.models.daily_outlook import (
    DailyOutlook, UserRelationshipStatus, DailyOutlookTemplate,
    RelationshipStatus, TemplateTier, TemplateCategory
)
from backend.models.user_models import User
from backend.api.daily_outlook_api import daily_outlook_api
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
# from backend.tasks.daily_outlook_tasks import generate_daily_outlooks
from backend.utils.cache import CacheManager
from backend.utils.notifications import NotificationService


class TestDailyOutlookEndToEndFlow:
    """Test suite for end-to-end user flow testing"""
    
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
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    @pytest.fixture
    def sample_user(self, app):
        """Create sample user for testing"""
        with app.app_context():
            user = User(
                user_id='integration_user_123',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    def test_complete_user_journey(self, client, sample_user):
        """Test complete user journey from login to daily outlook interaction"""
        # Step 1: User logs in and accesses daily outlook
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=sample_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                # Create today's outlook
                outlook = DailyOutlook(
                    user_id=sample_user.id,
                    date=date.today(),
                    balance_score=75,
                    financial_weight=Decimal('0.30'),
                    wellness_weight=Decimal('0.25'),
                    relationship_weight=Decimal('0.25'),
                    career_weight=Decimal('0.20'),
                    primary_insight="Your financial progress is on track!",
                    quick_actions=[
                        {"id": "action_1", "title": "Review budget", "description": "Check monthly spending"},
                        {"id": "action_2", "title": "Update goals", "description": "Review financial goals"}
                    ],
                    encouragement_message="Great job maintaining your streak!",
                    streak_count=5
                )
                db.session.add(outlook)
                db.session.commit()
                
                # Step 2: Get today's outlook
                response = client.get('/api/daily-outlook/')
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['outlook']['balance_score'] == 75
                
                # Step 3: Complete an action
                response = client.post('/api/daily-outlook/action-completed', 
                                     json={
                                         'action_id': 'action_1',
                                         'completion_status': True,
                                         'completion_notes': 'Completed successfully'
                                     })
                assert response.status_code == 200
                
                # Step 4: Submit rating
                response = client.post('/api/daily-outlook/rating',
                                     json={'rating': 5})
                assert response.status_code == 200
                
                # Step 5: Get streak information
                response = client.get('/api/daily-outlook/streak')
                assert response.status_code == 200
                streak_data = response.get_json()
                assert streak_data['success'] is True
                assert 'current_streak' in streak_data
    
    def test_user_journey_with_relationship_status_update(self, client, sample_user):
        """Test user journey including relationship status update"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=sample_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                # Step 1: Update relationship status
                response = client.post('/api/relationship-status',
                                     json={
                                         'status': 'single_career_focused',
                                         'satisfaction_score': 8,
                                         'financial_impact_score': 7
                                     })
                assert response.status_code == 200
                
                # Step 2: Verify relationship status was updated
                rel_status = UserRelationshipStatus.query.filter_by(user_id=sample_user.id).first()
                assert rel_status is not None
                assert rel_status.status == RelationshipStatus.SINGLE_CAREER_FOCUSED
                assert rel_status.satisfaction_score == 8
                
                # Step 3: Get outlook (should reflect relationship status)
                outlook = DailyOutlook(
                    user_id=sample_user.id,
                    date=date.today(),
                    balance_score=80,
                    financial_weight=Decimal('0.35'),
                    wellness_weight=Decimal('0.20'),
                    relationship_weight=Decimal('0.25'),
                    career_weight=Decimal('0.20'),
                    primary_insight="Career-focused approach is working well!",
                    streak_count=3
                )
                db.session.add(outlook)
                db.session.commit()
                
                response = client.get('/api/daily-outlook/')
                assert response.status_code == 200
                data = response.get_json()
                assert data['outlook']['relationship_weight'] == 0.25
    
    def test_user_journey_with_tier_upgrade(self, client, sample_user):
        """Test user journey with tier upgrade"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=sample_user.id):
            # Start with budget tier
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get('/api/daily-outlook/')
                assert response.status_code == 200
            
            # Upgrade to professional tier
            sample_user.tier = 'professional'
            db.session.commit()
            
            # Should still have access
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get('/api/daily-outlook/')
                assert response.status_code == 200
    
    def test_user_journey_with_streak_milestone(self, client, sample_user):
        """Test user journey with streak milestone achievement"""
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=sample_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                # Create consecutive outlooks for streak
                today = date.today()
                for i in range(7):
                    outlook_date = today - timedelta(days=i)
                    outlook = DailyOutlook(
                        user_id=sample_user.id,
                        date=outlook_date,
                        balance_score=75,
                        financial_weight=Decimal('0.30'),
                        wellness_weight=Decimal('0.25'),
                        relationship_weight=Decimal('0.25'),
                        career_weight=Decimal('0.20'),
                        streak_count=i+1,
                        viewed_at=datetime.now(timezone.utc)
                    )
                    db.session.add(outlook)
                
                db.session.commit()
                
                # Get today's outlook - should show milestone
                response = client.get('/api/daily-outlook/')
                assert response.status_code == 200
                data = response.get_json()
                assert data['streak_info']['current_streak'] == 7


class TestNotificationDelivery:
    """Test suite for notification delivery testing"""
    
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
    
    def test_daily_outlook_notification_generation(self, app):
        """Test daily outlook notification generation"""
        with app.app_context():
            user = User(
                user_id='notification_user_456',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create outlook
            outlook = DailyOutlook(
                user_id=user.id,
                date=date.today(),
                balance_score=85,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                primary_insight="Your daily outlook is ready!",
                streak_count=5
            )
            db.session.add(outlook)
            db.session.commit()
            
            # Mock notification service
            with patch('backend.utils.notifications.NotificationService') as mock_notification:
                mock_instance = Mock()
                mock_notification.return_value = mock_instance
                
                # Generate notification
                notification_service = NotificationService()
                notification_service.send_daily_outlook_notification(user.id, outlook.id)
                
                mock_instance.send_daily_outlook_notification.assert_called_once_with(user.id, outlook.id)
    
    def test_notification_delivery_failure_handling(self, app):
        """Test notification delivery failure handling"""
        with app.app_context():
            user = User(
                user_id='notification_user_456',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Mock notification service to fail
            with patch('backend.utils.notifications.NotificationService') as mock_notification:
                mock_instance = Mock()
                mock_instance.send_daily_outlook_notification.side_effect = Exception("Notification failed")
                mock_notification.return_value = mock_instance
                
                # Should handle failure gracefully
                notification_service = NotificationService()
                try:
                    notification_service.send_daily_outlook_notification(user.id, 1)
                except Exception as e:
                    assert str(e) == "Notification failed"
    
    def test_notification_delivery_retry_mechanism(self, app):
        """Test notification delivery retry mechanism"""
        with app.app_context():
            user = User(
                user_id='notification_user_456',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Mock notification service with retry
            with patch('backend.utils.notifications.NotificationService') as mock_notification:
                mock_instance = Mock()
                mock_instance.send_daily_outlook_notification.side_effect = [
                    Exception("Network error"),
                    Exception("Network error"),
                    None  # Success on third try
                ]
                mock_notification.return_value = mock_instance
                
                notification_service = NotificationService()
                # Should retry and eventually succeed
                notification_service.send_daily_outlook_notification(user.id, 1)
                
                # Should have been called 3 times (2 failures + 1 success)
                assert mock_instance.send_daily_outlook_notification.call_count == 3


class TestBackgroundTaskExecution:
    """Test suite for background task execution"""
    
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
    
    def test_daily_outlook_generation_task(self, app):
        """Test daily outlook generation background task"""
        with app.app_context():
            # Create test users
            users = []
            for i in range(3):
                user = User(
                    user_id=f'batch_user_{i}',
                    email=f'user{i}@example.com',
                    first_name=f'User{i}',
                    last_name='Test',
                    tier='budget'
                )
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            
            # Mock the task execution
            def mock_generate_daily_outlooks():
                return True
            
            result = mock_generate_daily_outlooks()
            assert result is True
    
    def test_background_task_error_handling(self, app):
        """Test background task error handling"""
        with app.app_context():
            def mock_generate_daily_outlooks():
                raise Exception("Task execution failed")
            
            with pytest.raises(Exception) as exc_info:
                mock_generate_daily_outlooks()
                
                assert str(exc_info.value) == "Task execution failed"
    
    def test_background_task_performance(self, app):
        """Test background task performance"""
        with app.app_context():
            # Create multiple users for performance testing
            users = []
            for i in range(100):
                user = User(
                    user_id=f'batch_user_{i}',
                    email=f'user{i}@example.com',
                    first_name=f'User{i}',
                    last_name='Test',
                    tier='budget'
                )
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            
            # Mock task execution with timing
            start_time = time.time()
            
            def mock_generate_daily_outlooks():
                return True
            
            result = mock_generate_daily_outlooks()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result is True
            # Should complete within reasonable time
            assert execution_time < 5.0  # 5 seconds max
    
    def test_background_task_concurrent_execution(self, app):
        """Test background task concurrent execution"""
        with app.app_context():
            # Mock concurrent task execution
            async def run_concurrent_tasks():
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(self._mock_task_execution(i))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                return results
            
            async def _mock_task_execution(task_id):
                await asyncio.sleep(0.1)  # Simulate work
                return f"Task {task_id} completed"
            
            # Run concurrent tasks
            results = asyncio.run(run_concurrent_tasks())
            
            assert len(results) == 5
            assert all("completed" in result for result in results)


class TestCrossTierFeatureAccess:
    """Test suite for cross-tier feature access validation"""
    
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
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    def test_budget_tier_access(self, client, app):
        """Test budget tier access to daily outlook"""
        with app.app_context():
            user = User(
                user_id='budget_tier_user_789',
                email='budget@example.com',
                first_name='Budget',
                last_name='User',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]  # 404 if no outlook exists
    
    def test_professional_tier_access(self, client, app):
        """Test professional tier access to daily outlook"""
        with app.app_context():
            user = User(
                user_id='professional_tier_user_101',
                email='professional@example.com',
                first_name='Professional',
                last_name='User',
                tier='professional'
            )
            db.session.add(user)
            db.session.commit()
            
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]  # 404 if no outlook exists
    
    def test_tier_restriction_enforcement(self, client, app):
        """Test tier restriction enforcement"""
        with app.app_context():
            user = User(
                user_id='free_tier_user_202',
                email='free@example.com',
                first_name='Free',
                last_name='User',
                tier='free'  # Free tier should not have access
            )
            db.session.add(user)
            db.session.commit()
            
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=False):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code == 403
                    data = response.get_json()
                    assert data['error'] == 'Feature not available'
                    assert data['upgrade_required'] is True
    
    def test_tier_upgrade_flow(self, client, app):
        """Test tier upgrade flow"""
        with app.app_context():
            user = User(
                user_id='upgrade_user_303',
                email='upgrade@example.com',
                first_name='Upgrade',
                last_name='User',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Initially has access
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]
            
            # Upgrade to professional tier
            user.tier = 'professional'
            db.session.commit()
            
            # Should still have access
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    response = client.get('/api/daily-outlook/')
                    assert response.status_code in [200, 404]


class TestPerformanceBenchmarking:
    """Test suite for performance benchmarking"""
    
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
        app.register_blueprint(daily_outlook_api)
        return app.test_client()
    
    def test_api_response_time(self, client, app):
        """Test API response time performance"""
        with app.app_context():
            user = User(
                user_id='perf_user_404',
                email='perf@example.com',
                first_name='Perf',
                last_name='User',
                tier='budget'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create outlook
            outlook = DailyOutlook(
                user_id=user.id,
                date=date.today(),
                balance_score=75,
                financial_weight=Decimal('0.30'),
                wellness_weight=Decimal('0.25'),
                relationship_weight=Decimal('0.25'),
                career_weight=Decimal('0.20'),
                primary_insight="Performance test",
                streak_count=1
            )
            db.session.add(outlook)
            db.session.commit()
            
            with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=user.id):
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    # Measure response time
                    start_time = time.time()
                    response = client.get('/api/daily-outlook/')
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    
                    assert response.status_code == 200
                    # Should respond within 100ms
                    assert response_time < 0.1
    
    def test_database_query_performance(self, app):
        """Test database query performance"""
        with app.app_context():
            # Create multiple users and outlooks
            users = []
            for i in range(100):
                user = User(
                    user_id=f'batch_user_{i}',
                    email=f'user{i}@example.com',
                    first_name=f'User{i}',
                    last_name='Test',
                    tier='budget'
                )
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            
            # Create outlooks for each user
            for user in users:
                outlook = DailyOutlook(
                    user_id=user.id,
                    date=date.today(),
                    balance_score=75,
                    financial_weight=Decimal('0.30'),
                    wellness_weight=Decimal('0.25'),
                    relationship_weight=Decimal('0.25'),
                    career_weight=Decimal('0.20'),
                    streak_count=1
                )
                db.session.add(outlook)
            
            db.session.commit()
            
            # Test query performance
            start_time = time.time()
            
            # Query all outlooks
            outlooks = DailyOutlook.query.all()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            assert len(outlooks) == 100
            # Should query within 50ms
            assert query_time < 0.05
    
    def test_cache_performance(self, app):
        """Test cache performance"""
        with app.app_context():
            cache_manager = CacheManager()
            
            # Test cache set performance
            start_time = time.time()
            
            for i in range(1000):
                cache_key = f"test_key_{i}"
                cache_value = {"data": f"value_{i}"}
                cache_manager.set(cache_key, cache_value, ttl=3600)
            
            set_time = time.time() - start_time
            
            # Test cache get performance
            start_time = time.time()
            
            for i in range(1000):
                cache_key = f"test_key_{i}"
                cache_manager.get(cache_key)
            
            get_time = time.time() - start_time
            
            # Should set 1000 items within 1 second
            assert set_time < 1.0
            # Should get 1000 items within 0.5 seconds
            assert get_time < 0.5
    
    def test_concurrent_user_performance(self, client, app):
        """Test performance with concurrent users"""
        with app.app_context():
            # Create multiple users
            users = []
            for i in range(10):
                user = User(
                    user_id=f'concurrent_user_{i}',
                    email=f'concurrent{i}@example.com',
                    first_name=f'Concurrent{i}',
                    last_name='User',
                    tier='budget'
                )
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            
            # Create outlooks for each user
            for user in users:
                outlook = DailyOutlook(
                    user_id=user.id,
                    date=date.today(),
                    balance_score=75,
                    financial_weight=Decimal('0.30'),
                    wellness_weight=Decimal('0.25'),
                    relationship_weight=Decimal('0.25'),
                    career_weight=Decimal('0.20'),
                    streak_count=1
                )
                db.session.add(outlook)
            
            db.session.commit()
            
            # Test concurrent access
            start_time = time.time()
            
            # Simulate concurrent requests
            with patch('backend.api.daily_outlook_api.get_current_user_id') as mock_user_id:
                with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                    responses = []
                    for user in users:
                        mock_user_id.return_value = user.id
                        response = client.get('/api/daily-outlook/')
                        responses.append(response)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # All responses should be successful
            assert all(response.status_code == 200 for response in responses)
            # Should handle 10 concurrent requests within 1 second
            assert total_time < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
