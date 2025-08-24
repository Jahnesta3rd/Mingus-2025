"""
Unit tests for Communication Orchestrator Service and API
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import create_access_token

from backend.services.communication_orchestrator import (
    CommunicationOrchestrator,
    TriggerType,
    CommunicationChannel,
    CommunicationPriority,
    CommunicationRequest,
    CommunicationResult,
    send_smart_communication,
    get_communication_status,
    cancel_communication
)
from backend.routes.communication_orchestrator import (
    communication_orchestrator_bp,
    validate_trigger_type,
    validate_channel,
    validate_priority
)


class TestCommunicationOrchestrator:
    """Test CommunicationOrchestrator service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.orchestrator = CommunicationOrchestrator()
        self.user_id = 123
        self.trigger_type = TriggerType.FINANCIAL_ALERT
        self.data = {
            'amount': 100.50,
            'account': 'checking',
            'threshold': 200.00
        }
    
    def test_create_communication_request(self):
        """Test creating communication request with defaults"""
        request = self.orchestrator._create_communication_request(
            self.user_id,
            self.trigger_type,
            self.data,
            None,  # channel
            None,  # priority
            None   # scheduled_time
        )
        
        assert request.user_id == self.user_id
        assert request.trigger_type == self.trigger_type
        assert request.data == self.data
        assert request.channel == CommunicationChannel.SMS  # Default for financial alert
        assert request.priority == CommunicationPriority.CRITICAL  # Default for financial alert
        assert request.scheduled_time is None
    
    def test_get_default_priority(self):
        """Test getting default priority for trigger types"""
        assert self.orchestrator._get_default_priority(TriggerType.FINANCIAL_ALERT) == CommunicationPriority.CRITICAL
        assert self.orchestrator._get_default_priority(TriggerType.PAYMENT_REMINDER) == CommunicationPriority.HIGH
        assert self.orchestrator._get_default_priority(TriggerType.WEEKLY_CHECKIN) == CommunicationPriority.MEDIUM
        assert self.orchestrator._get_default_priority(TriggerType.MONTHLY_REPORT) == CommunicationPriority.LOW
    
    def test_get_default_channel(self):
        """Test getting default channel for trigger types"""
        assert self.orchestrator._get_default_channel(TriggerType.FINANCIAL_ALERT) == CommunicationChannel.SMS
        assert self.orchestrator._get_default_channel(TriggerType.MONTHLY_REPORT) == CommunicationChannel.EMAIL
        assert self.orchestrator._get_default_channel(TriggerType.ONBOARDING_SEQUENCE) == CommunicationChannel.BOTH
    
    @patch('backend.services.communication_orchestrator.CommunicationPreferenceService')
    def test_validate_communication_request_success(self, mock_pref_service):
        """Test successful communication request validation"""
        # Mock user preferences
        mock_prefs = {
            'sms_enabled': True,
            'email_enabled': True
        }
        mock_pref_service.return_value.get_user_communication_prefs.return_value = mock_prefs
        mock_pref_service.return_value.check_consent_for_message_type.return_value = {'can_send': True}
        
        # Mock analytics service
        with patch.object(self.orchestrator, 'analytics_service') as mock_analytics:
            mock_analytics.get_user_communication_history.return_value = []
            
            request = CommunicationRequest(
                user_id=self.user_id,
                trigger_type=self.trigger_type,
                channel=CommunicationChannel.SMS,
                priority=CommunicationPriority.CRITICAL,
                data=self.data
            )
            
            result = self.orchestrator._validate_communication_request(request)
            
            assert result['valid'] is True
    
    @patch('backend.services.communication_orchestrator.CommunicationPreferenceService')
    def test_validate_communication_request_user_not_found(self, mock_pref_service):
        """Test validation when user not found"""
        mock_pref_service.return_value.get_user_communication_prefs.return_value = None
        
        request = CommunicationRequest(
            user_id=self.user_id,
            trigger_type=self.trigger_type,
            channel=CommunicationChannel.SMS,
            priority=CommunicationPriority.CRITICAL,
            data=self.data
        )
        
        result = self.orchestrator._validate_communication_request(request)
        
        assert result['valid'] is False
        assert 'not found' in result['reason']
    
    @patch('backend.services.communication_orchestrator.CommunicationPreferenceService')
    def test_validate_communication_request_opted_out(self, mock_pref_service):
        """Test validation when user has opted out"""
        mock_prefs = {
            'sms_enabled': False,
            'email_enabled': False
        }
        mock_pref_service.return_value.get_user_communication_prefs.return_value = mock_prefs
        
        request = CommunicationRequest(
            user_id=self.user_id,
            trigger_type=self.trigger_type,
            channel=CommunicationChannel.SMS,
            priority=CommunicationPriority.CRITICAL,
            data=self.data
        )
        
        result = self.orchestrator._validate_communication_request(request)
        
        assert result['valid'] is False
        assert 'opted out' in result['reason']
    
    def test_check_frequency_limits_no_recent_communications(self):
        """Test frequency limits when no recent communications"""
        with patch.object(self.orchestrator, 'analytics_service') as mock_analytics:
            mock_analytics.get_user_communication_history.return_value = []
            
            request = CommunicationRequest(
                user_id=self.user_id,
                trigger_type=self.trigger_type,
                channel=CommunicationChannel.SMS,
                priority=CommunicationPriority.CRITICAL,
                data=self.data
            )
            
            result = self.orchestrator._check_frequency_limits(request)
            
            assert result['valid'] is True
    
    def test_check_frequency_limits_daily_limit_exceeded(self):
        """Test frequency limits when daily limit exceeded"""
        # Mock recent communications with 5 today
        mock_communications = []
        for i in range(5):
            mock_comm = Mock()
            mock_comm.sent_at = datetime.utcnow()
            mock_communications.append(mock_comm)
        
        with patch.object(self.orchestrator, 'analytics_service') as mock_analytics:
            mock_analytics.get_user_communication_history.return_value = mock_communications
            
            request = CommunicationRequest(
                user_id=self.user_id,
                trigger_type=self.trigger_type,
                channel=CommunicationChannel.SMS,
                priority=CommunicationPriority.CRITICAL,
                data=self.data
            )
            
            result = self.orchestrator._check_frequency_limits(request)
            
            assert result['valid'] is False
            assert 'Daily communication limit' in result['reason']
    
    def test_optimize_channel_selection_better_engagement(self):
        """Test channel optimization based on engagement rates"""
        mock_prefs = {
            'sms_enabled': True,
            'email_enabled': True
        }
        
        with patch.object(self.orchestrator, '_get_channel_engagement_rate') as mock_engagement:
            mock_engagement.side_effect = [0.8, 0.3]  # SMS better than email
            
            request = CommunicationRequest(
                user_id=self.user_id,
                trigger_type=self.trigger_type,
                channel=CommunicationChannel.EMAIL,  # Start with email
                priority=CommunicationPriority.CRITICAL,
                data=self.data
            )
            
            optimized_channel = self.orchestrator._optimize_channel_selection(request, mock_prefs)
            
            assert optimized_channel == CommunicationChannel.SMS
    
    def test_get_celery_task_name(self):
        """Test getting Celery task name for different trigger types"""
        request = CommunicationRequest(
            user_id=self.user_id,
            trigger_type=TriggerType.FINANCIAL_ALERT,
            channel=CommunicationChannel.SMS,
            priority=CommunicationPriority.CRITICAL,
            data=self.data
        )
        
        task_name = self.orchestrator._get_celery_task_name(request)
        
        assert 'send_critical_financial_alert' in task_name
    
    def test_estimate_communication_cost(self):
        """Test communication cost estimation"""
        sms_request = CommunicationRequest(
            user_id=self.user_id,
            trigger_type=self.trigger_type,
            channel=CommunicationChannel.SMS,
            priority=CommunicationPriority.CRITICAL,
            data=self.data
        )
        
        email_request = CommunicationRequest(
            user_id=self.user_id,
            trigger_type=self.trigger_type,
            channel=CommunicationChannel.EMAIL,
            priority=CommunicationPriority.CRITICAL,
            data=self.data
        )
        
        sms_cost = self.orchestrator._estimate_communication_cost(sms_request)
        email_cost = self.orchestrator._estimate_communication_cost(email_request)
        
        assert sms_cost == 0.05
        assert email_cost == 0.001
    
    @patch('backend.services.communication_orchestrator.execute_communication_task')
    def test_execute_communication_success(self, mock_execute_task):
        """Test successful communication execution"""
        # Mock successful task execution
        mock_task_result = Mock()
        mock_task_result.id = "task_123"
        mock_execute_task.return_value = mock_task_result
        
        request = CommunicationRequest(
            user_id=self.user_id,
            trigger_type=self.trigger_type,
            channel=CommunicationChannel.SMS,
            priority=CommunicationPriority.CRITICAL,
            data=self.data
        )
        
        result = self.orchestrator._execute_communication(request)
        
        assert result.success is True
        assert result.task_id == "task_123"
        assert result.cost == 0.05
    
    @patch('backend.services.communication_orchestrator.execute_communication_task')
    def test_execute_communication_failure_with_fallback(self, mock_execute_task):
        """Test communication execution with fallback"""
        # Mock primary task failure
        mock_execute_task.side_effect = [Exception("Primary failed"), Mock(id="fallback_123")]
        
        with patch.object(self.orchestrator, '_validate_communication_request') as mock_validate:
            mock_validate.return_value = {'valid': True}
            
            request = CommunicationRequest(
                user_id=self.user_id,
                trigger_type=self.trigger_type,
                channel=CommunicationChannel.SMS,
                priority=CommunicationPriority.CRITICAL,
                data=self.data
            )
            
            result = self.orchestrator._execute_communication(request)
            
            assert result.success is True
            assert result.fallback_used is True
            assert result.task_id == "fallback_123"
    
    @patch('backend.services.communication_orchestrator.FlaskAnalyticsService')
    def test_track_communication_analytics_success(self, mock_flask_analytics):
        """Test analytics tracking for successful communication"""
        mock_analytics_service = Mock()
        mock_flask_analytics.return_value = mock_analytics_service
        
        result = CommunicationResult(
            success=True,
            task_id="task_123",
            cost=0.05
        )
        
        request = CommunicationRequest(
            user_id=self.user_id,
            trigger_type=self.trigger_type,
            channel=CommunicationChannel.SMS,
            priority=CommunicationPriority.CRITICAL,
            data=self.data
        )
        
        self.orchestrator._track_communication_analytics(result, request)
        
        mock_analytics_service.track_message_sent.assert_called_once_with(
            user_id=self.user_id,
            channel='sms',
            message_type='financial_alert',
            cost=0.05
        )
        assert result.analytics_tracked is True


class TestCommunicationOrchestratorAPI:
    """Test Communication Orchestrator API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret'
        self.app.register_blueprint(communication_orchestrator_bp)
        self.client = self.app.test_client()
        
        # Create test JWT token
        with self.app.app_context():
            self.access_token = create_access_token(identity=1)
    
    def test_validate_trigger_type(self):
        """Test trigger type validation"""
        assert validate_trigger_type('financial_alert') == TriggerType.FINANCIAL_ALERT
        assert validate_trigger_type('payment_reminder') == TriggerType.PAYMENT_REMINDER
        
        with pytest.raises(ValueError):
            validate_trigger_type('invalid_type')
    
    def test_validate_channel(self):
        """Test channel validation"""
        assert validate_channel('sms') == CommunicationChannel.SMS
        assert validate_channel('email') == CommunicationChannel.EMAIL
        assert validate_channel('both') == CommunicationChannel.BOTH
        
        with pytest.raises(ValueError):
            validate_channel('invalid_channel')
    
    def test_validate_priority(self):
        """Test priority validation"""
        assert validate_priority('critical') == CommunicationPriority.CRITICAL
        assert validate_priority('high') == CommunicationPriority.HIGH
        assert validate_priority('medium') == CommunicationPriority.MEDIUM
        assert validate_priority('low') == CommunicationPriority.LOW
        
        with pytest.raises(ValueError):
            validate_priority('invalid_priority')
    
    @patch('backend.routes.communication_orchestrator.send_smart_communication')
    def test_send_communication_success(self, mock_send_communication):
        """Test successful communication send endpoint"""
        # Mock successful communication
        mock_result = CommunicationResult(
            success=True,
            task_id="task_123",
            cost=0.05
        )
        mock_send_communication.return_value = mock_result
        
        data = {
            'user_id': 123,
            'trigger_type': 'financial_alert',
            'data': {
                'amount': 100.50,
                'account': 'checking'
            }
        }
        
        response = self.client.post(
            '/api/communication/send',
            headers={'Authorization': f'Bearer {self.access_token}'},
            json=data
        )
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['task_id'] == "task_123"
        assert response_data['cost'] == 0.05
    
    @patch('backend.routes.communication_orchestrator.send_smart_communication')
    def test_send_communication_failure(self, mock_send_communication):
        """Test failed communication send endpoint"""
        # Mock failed communication
        mock_result = CommunicationResult(
            success=False,
            error_message="User has opted out"
        )
        mock_send_communication.return_value = mock_result
        
        data = {
            'user_id': 123,
            'trigger_type': 'financial_alert',
            'data': {
                'amount': 100.50,
                'account': 'checking'
            }
        }
        
        response = self.client.post(
            '/api/communication/send',
            headers={'Authorization': f'Bearer {self.access_token}'},
            json=data
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'opted out' in response_data['error']
    
    def test_send_communication_missing_fields(self):
        """Test communication send with missing required fields"""
        data = {
            'user_id': 123
            # Missing trigger_type and data
        }
        
        response = self.client.post(
            '/api/communication/send',
            headers={'Authorization': f'Bearer {self.access_token}'},
            json=data
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Missing required field' in response_data['error']
    
    def test_send_communication_invalid_trigger_type(self):
        """Test communication send with invalid trigger type"""
        data = {
            'user_id': 123,
            'trigger_type': 'invalid_type',
            'data': {'test': 'data'}
        }
        
        response = self.client.post(
            '/api/communication/send',
            headers={'Authorization': f'Bearer {self.access_token}'},
            json=data
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Invalid trigger type' in response_data['error']
    
    @patch('backend.routes.communication_orchestrator.get_communication_status')
    def test_get_communication_status(self, mock_get_status):
        """Test get communication status endpoint"""
        mock_status = {
            'task_id': 'task_123',
            'status': 'SUCCESS',
            'result': {'message': 'sent'}
        }
        mock_get_status.return_value = mock_status
        
        response = self.client.get(
            '/api/communication/status/task_123',
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['task_id'] == 'task_123'
        assert response_data['status'] == 'SUCCESS'
    
    @patch('backend.routes.communication_orchestrator.cancel_communication')
    def test_cancel_communication_success(self, mock_cancel):
        """Test successful communication cancellation"""
        mock_cancel.return_value = True
        
        response = self.client.post(
            '/api/communication/cancel/task_123',
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'cancelled successfully' in response_data['message']
    
    @patch('backend.routes.communication_orchestrator.cancel_communication')
    def test_cancel_communication_failure(self, mock_cancel):
        """Test failed communication cancellation"""
        mock_cancel.return_value = False
        
        response = self.client.post(
            '/api/communication/cancel/task_123',
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Failed to cancel' in response_data['error']
    
    @patch('backend.routes.communication_orchestrator.send_smart_communication')
    def test_batch_communications(self, mock_send_communication):
        """Test batch communications endpoint"""
        # Mock mixed results
        mock_send_communication.side_effect = [
            CommunicationResult(success=True, task_id="task_1", cost=0.05),
            CommunicationResult(success=False, error_message="User opted out")
        ]
        
        data = {
            'communications': [
                {
                    'user_id': 123,
                    'trigger_type': 'financial_alert',
                    'data': {'amount': 100}
                },
                {
                    'user_id': 456,
                    'trigger_type': 'weekly_checkin',
                    'data': {'message': 'check in'}
                }
            ]
        }
        
        response = self.client.post(
            '/api/communication/batch',
            headers={'Authorization': f'Bearer {self.access_token}'},
            json=data
        )
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['results']) == 2
        assert response_data['summary']['total'] == 2
        assert response_data['summary']['successful'] == 1
        assert response_data['summary']['failed'] == 1
    
    def test_get_trigger_types(self):
        """Test get trigger types endpoint"""
        response = self.client.get(
            '/api/communication/trigger-types',
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'trigger_types' in response_data
        assert len(response_data['trigger_types']) > 0
        
        # Check for specific trigger types
        trigger_values = [t['value'] for t in response_data['trigger_types']]
        assert 'financial_alert' in trigger_values
        assert 'payment_reminder' in trigger_values
        assert 'weekly_checkin' in trigger_values
    
    def test_communication_health_check(self):
        """Test communication health check endpoint"""
        response = self.client.get(
            '/api/communication/health',
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        assert response.status_code in [200, 503]  # Can be healthy or degraded
        response_data = json.loads(response.data)
        assert 'status' in response_data
        assert 'services' in response_data
        assert 'timestamp' in response_data


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @patch('backend.services.communication_orchestrator.get_communication_orchestrator')
    def test_send_smart_communication_convenience(self, mock_get_orchestrator):
        """Test send_smart_communication convenience function"""
        mock_orchestrator = Mock()
        mock_get_orchestrator.return_value = mock_orchestrator
        
        mock_result = CommunicationResult(success=True, task_id="task_123")
        mock_orchestrator.send_smart_communication.return_value = mock_result
        
        result = send_smart_communication(
            user_id=123,
            trigger_type=TriggerType.FINANCIAL_ALERT,
            data={'test': 'data'}
        )
        
        assert result.success is True
        assert result.task_id == "task_123"
        mock_orchestrator.send_smart_communication.assert_called_once()
    
    @patch('backend.services.communication_orchestrator.get_communication_orchestrator')
    def test_get_communication_status_convenience(self, mock_get_orchestrator):
        """Test get_communication_status convenience function"""
        mock_orchestrator = Mock()
        mock_get_orchestrator.return_value = mock_orchestrator
        
        mock_status = {'status': 'SUCCESS'}
        mock_orchestrator.get_communication_status.return_value = mock_status
        
        status = get_communication_status("task_123")
        
        assert status == mock_status
        mock_orchestrator.get_communication_status.assert_called_once_with("task_123")
    
    @patch('backend.services.communication_orchestrator.get_communication_orchestrator')
    def test_cancel_communication_convenience(self, mock_get_orchestrator):
        """Test cancel_communication convenience function"""
        mock_orchestrator = Mock()
        mock_get_orchestrator.return_value = mock_orchestrator
        
        mock_orchestrator.cancel_communication.return_value = True
        
        success = cancel_communication("task_123")
        
        assert success is True
        mock_orchestrator.cancel_communication.assert_called_once_with("task_123")


if __name__ == '__main__':
    pytest.main([__file__]) 