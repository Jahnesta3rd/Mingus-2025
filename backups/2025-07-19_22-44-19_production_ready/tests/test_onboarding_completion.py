import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

from backend.routes.onboarding_completion import onboarding_completion_bp
from backend.models.user import User
from backend.models.user_preferences import UserPreferences
from backend.models.reminder_schedule import ReminderSchedule

class TestOnboardingCompletion:
    """Test cases for onboarding completion functionality."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = 1
        user.name = "Test User"
        user.email = "test@example.com"
        user.onboarding_completed = False
        user.first_checkin_scheduled = False
        user.mobile_app_downloaded = False
        return user
    
    @pytest.fixture
    def mock_preferences(self):
        """Create mock user preferences."""
        prefs = Mock(spec=UserPreferences)
        prefs.user_id = 1
        prefs.email_notifications = True
        prefs.push_notifications = True
        prefs.reminder_preferences = {
            'enabled': True,
            'frequency': 'weekly',
            'day': 'wednesday',
            'time': '10:00',
            'email': True,
            'push': True
        }
        return prefs
    
    def test_get_completion_data_success(self, client, mock_user):
        """Test successful completion data retrieval."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            with patch('backend.routes.onboarding_completion.db_session') as mock_db:
                # Mock database queries
                mock_db.query.return_value.filter.return_value.first.return_value = mock_user
                mock_db.query.return_value.filter.return_value.count.return_value = 3
                
                response = client.get('/api/onboarding/completion/data/1')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'user_name' in data
                assert 'goals_count' in data
                assert 'profile_completion' in data
                assert 'community_stats' in data
    
    def test_schedule_first_checkin_success(self, client, mock_user):
        """Test successful first check-in scheduling."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            with patch('backend.routes.onboarding_completion.db_session') as mock_db:
                # Mock database operations
                mock_db.query.return_value.filter.return_value.first.return_value = None
                mock_db.commit.return_value = None
                
                checkin_data = {
                    'user_id': '1',
                    'preferences': {
                        'enabled': True,
                        'frequency': 'weekly',
                        'day': 'wednesday',
                        'time': '10:00',
                        'email': True,
                        'push': True
                    }
                }
                
                response = client.post(
                    '/api/onboarding/completion/schedule-checkin',
                    data=json.dumps(checkin_data),
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
                assert 'scheduled_date' in data
    
    def test_save_engagement_preferences_success(self, client, mock_user):
        """Test successful engagement preferences saving."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            with patch('backend.routes.onboarding_completion.db_session') as mock_db:
                # Mock database operations
                mock_db.query.return_value.filter.return_value.first.return_value = None
                mock_db.commit.return_value = None
                
                preferences_data = {
                    'user_id': '1',
                    'preferences': {
                        'enabled': True,
                        'frequency': 'weekly',
                        'day': 'wednesday',
                        'time': '10:00',
                        'email': True,
                        'push': True
                    }
                }
                
                response = client.post(
                    '/api/onboarding/completion/preferences',
                    data=json.dumps(preferences_data),
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
    
    def test_mark_onboarding_complete_success(self, client, mock_user):
        """Test successful onboarding completion marking."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            with patch('backend.routes.onboarding_completion.db_session') as mock_db:
                # Mock database operations
                mock_db.query.return_value.filter.return_value.first.return_value = mock_user
                mock_db.commit.return_value = None
                
                completion_data = {
                    'user_id': '1',
                    'completed_at': datetime.now().isoformat()
                }
                
                response = client.post(
                    '/api/onboarding/completion/complete',
                    data=json.dumps(completion_data),
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
    
    def test_get_mobile_app_info(self, client, mock_user):
        """Test mobile app info retrieval."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            response = client.get('/api/onboarding/completion/mobile-app')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'ios_url' in data
            assert 'android_url' in data
            assert 'available' in data
            assert 'platform' in data
    
    def test_get_community_stats(self, client, mock_user):
        """Test community statistics retrieval."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            with patch('backend.routes.onboarding_completion.db_session') as mock_db:
                # Mock database queries
                mock_db.query.return_value.count.return_value = 1000
                mock_db.query.return_value.filter.return_value.count.return_value = 500
                
                response = client.get('/api/onboarding/completion/community-stats')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'total_members' in data
                assert 'active_this_week' in data
                assert 'average_savings' in data
                assert 'new_members_today' in data
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to completion endpoints."""
        # Test without authentication
        response = client.get('/api/onboarding/completion/data/1')
        assert response.status_code == 401
    
    def test_invalid_user_id(self, client, mock_user):
        """Test access with invalid user ID."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            # Try to access data for different user
            response = client.get('/api/onboarding/completion/data/999')
            assert response.status_code == 403
    
    def test_schedule_checkin_invalid_data(self, client, mock_user):
        """Test scheduling check-in with invalid data."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            invalid_data = {
                'user_id': '1',
                'preferences': {
                    'enabled': True,
                    'frequency': 'invalid_frequency'
                }
            }
            
            response = client.post(
                '/api/onboarding/completion/schedule-checkin',
                data=json.dumps(invalid_data),
                content_type='application/json'
            )
            
            # Should still work as we have fallback logic
            assert response.status_code == 200
    
    def test_welcome_email_sending(self, client, mock_user):
        """Test welcome email sending functionality."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            with patch('backend.routes.onboarding_completion.EmailService') as mock_email_service:
                mock_email_service.return_value.send_welcome_email.return_value = True
                
                email_data = {
                    'user_id': '1'
                }
                
                response = client.post(
                    '/api/onboarding/completion/welcome-email',
                    data=json.dumps(email_data),
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
    
    def test_create_reminder_success(self, client, mock_user):
        """Test successful reminder creation."""
        with patch('backend.routes.onboarding_completion.current_user', mock_user):
            with patch('backend.routes.onboarding_completion.db_session') as mock_db:
                # Mock database operations
                mock_db.commit.return_value = None
                
                reminder_data = {
                    'user_id': '1',
                    'scheduled_date': (datetime.now() + timedelta(days=7)).isoformat(),
                    'reminder_type': 'first_checkin'
                }
                
                response = client.post(
                    '/api/onboarding/completion/create-reminder',
                    data=json.dumps(reminder_data),
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
                assert 'scheduled_date' in data 