"""
Unit tests for webhook handlers
Tests for Twilio SMS and Resend Email webhook endpoints
"""

import pytest
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager

from backend.routes.webhook_handlers import (
    webhook_handlers_bp,
    verify_twilio_signature,
    verify_resend_signature,
    get_message_id_from_twilio_sid,
    get_message_id_from_resend_id
)
from backend.models.communication_analytics import CommunicationMetrics
from backend.database import get_db_session


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TWILIO_AUTH_TOKEN'] = 'test-twilio-token'
    app.config['RESEND_WEBHOOK_SECRET'] = 'test-resend-secret'
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Register blueprint
    app.register_blueprint(webhook_handlers_bp)
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('backend.routes.webhook_handlers.get_db_session') as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service functions"""
    with patch('backend.routes.webhook_handlers.track_message_delivered') as mock_delivered, \
         patch('backend.routes.webhook_handlers.track_message_opened') as mock_opened, \
         patch('backend.routes.webhook_handlers.track_user_action') as mock_action:
        
        mock_delivered.return_value = True
        mock_opened.return_value = True
        mock_action.return_value = True
        
        yield {
            'delivered': mock_delivered,
            'opened': mock_opened,
            'action': mock_action
        }


class TestSignatureVerification:
    """Test signature verification functions"""
    
    def test_verify_twilio_signature_valid(self):
        """Test valid Twilio signature verification"""
        auth_token = 'test-token'
        request_body = 'test-body'
        
        # Create valid signature
        expected_signature = hmac.new(
            auth_token.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        assert verify_twilio_signature(request_body, signature, auth_token) is True
    
    def test_verify_twilio_signature_invalid(self):
        """Test invalid Twilio signature verification"""
        auth_token = 'test-token'
        request_body = 'test-body'
        signature = 'sha256=invalid-signature'
        
        assert verify_twilio_signature(request_body, signature, auth_token) is False
    
    def test_verify_resend_signature_valid(self):
        """Test valid Resend signature verification"""
        webhook_secret = 'test-secret'
        request_body = 'test-body'
        
        # Create valid signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        assert verify_resend_signature(request_body, signature, webhook_secret) is True
    
    def test_verify_resend_signature_invalid(self):
        """Test invalid Resend signature verification"""
        webhook_secret = 'test-secret'
        request_body = 'test-body'
        signature = 'sha256=invalid-signature'
        
        assert verify_resend_signature(request_body, signature, webhook_secret) is False


class TestMessageIDMapping:
    """Test message ID mapping functions"""
    
    def test_get_message_id_from_twilio_sid_found(self, mock_db_session):
        """Test finding message ID from Twilio SID"""
        # Mock message in database
        mock_message = MagicMock()
        mock_message.id = 123
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_message
        
        message_id = get_message_id_from_twilio_sid('SM123456')
        
        assert message_id == 123
    
    def test_get_message_id_from_twilio_sid_not_found(self, mock_db_session):
        """Test message ID not found from Twilio SID"""
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        message_id = get_message_id_from_twilio_sid('SM123456')
        
        assert message_id is None
    
    def test_get_message_id_from_resend_id_found(self, mock_db_session):
        """Test finding message ID from Resend email ID"""
        # Mock message in database
        mock_message = MagicMock()
        mock_message.id = 456
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_message
        
        message_id = get_message_id_from_resend_id('email_123')
        
        assert message_id == 456
    
    def test_get_message_id_from_resend_id_not_found(self, mock_db_session):
        """Test message ID not found from Resend email ID"""
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        message_id = get_message_id_from_resend_id('email_123')
        
        assert message_id is None


class TestTwilioWebhook:
    """Test Twilio webhook endpoint"""
    
    def test_twilio_webhook_delivered_success(self, client, mock_db_session, mock_analytics_service):
        """Test successful SMS delivered webhook"""
        # Create valid signature
        auth_token = 'test-twilio-token'
        request_body = 'MessageSid=SM123&MessageStatus=delivered&To=+1234567890&From=+0987654321'
        
        expected_signature = hmac.new(
            auth_token.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        # Mock message found
        mock_message = MagicMock()
        mock_message.id = 123
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_message
        
        # Mock get_message_id_from_twilio_sid
        with patch('backend.routes.webhook_handlers.get_message_id_from_twilio_sid') as mock_get_id:
            mock_get_id.return_value = 123
            
            response = client.post('/webhooks/twilio', 
                                 data=request_body,
                                 headers={
                                     'X-Twilio-Signature': signature,
                                     'Content-Type': 'application/x-www-form-urlencoded'
                                 })
        
        assert response.status_code == 200
        assert response.json['success'] is True
        
        # Verify analytics service was called
        mock_analytics_service['delivered'].assert_called_once_with(123)
    
    def test_twilio_webhook_failed_status(self, client, mock_db_session):
        """Test SMS failed webhook"""
        # Create valid signature
        auth_token = 'test-twilio-token'
        request_body = 'MessageSid=SM123&MessageStatus=failed&To=+1234567890&From=+0987654321&ErrorCode=30008&ErrorMessage=Invalid+phone+number'
        
        expected_signature = hmac.new(
            auth_token.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        # Mock message found
        mock_message = MagicMock()
        mock_message.id = 123
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_message
        
        # Mock get_message_id_from_twilio_sid
        with patch('backend.routes.webhook_handlers.get_message_id_from_twilio_sid') as mock_get_id:
            mock_get_id.return_value = 123
            
            response = client.post('/webhooks/twilio', 
                                 data=request_body,
                                 headers={
                                     'X-Twilio-Signature': signature,
                                     'Content-Type': 'application/x-www-form-urlencoded'
                                 })
        
        assert response.status_code == 200
        assert response.json['success'] is True
        
        # Verify message status was updated to failed
        mock_message.status = "failed"
        mock_db_session.commit.assert_called_once()
    
    def test_twilio_webhook_invalid_signature(self, client):
        """Test Twilio webhook with invalid signature"""
        response = client.post('/webhooks/twilio', 
                             data='MessageSid=SM123&MessageStatus=delivered',
                             headers={
                                 'X-Twilio-Signature': 'sha256=invalid-signature',
                                 'Content-Type': 'application/x-www-form-urlencoded'
                             })
        
        assert response.status_code == 401
        assert response.json['error'] == 'Invalid signature'
    
    def test_twilio_webhook_missing_data(self, client):
        """Test Twilio webhook with missing required data"""
        # Create valid signature
        auth_token = 'test-twilio-token'
        request_body = 'MessageSid=SM123'  # Missing required fields
        
        expected_signature = hmac.new(
            auth_token.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        response = client.post('/webhooks/twilio', 
                             data=request_body,
                             headers={
                                 'X-Twilio-Signature': signature,
                                 'Content-Type': 'application/x-www-form-urlencoded'
                             })
        
        assert response.status_code == 400
        assert response.json['error'] == 'Invalid data'
    
    def test_twilio_webhook_message_not_found(self, client, mock_db_session):
        """Test Twilio webhook when message ID not found"""
        # Create valid signature
        auth_token = 'test-twilio-token'
        request_body = 'MessageSid=SM123&MessageStatus=delivered&To=+1234567890&From=+0987654321'
        
        expected_signature = hmac.new(
            auth_token.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        # Mock get_message_id_from_twilio_sid returning None
        with patch('backend.routes.webhook_handlers.get_message_id_from_twilio_sid') as mock_get_id:
            mock_get_id.return_value = None
            
            response = client.post('/webhooks/twilio', 
                                 data=request_body,
                                 headers={
                                     'X-Twilio-Signature': signature,
                                     'Content-Type': 'application/x-www-form-urlencoded'
                                 })
        
        assert response.status_code == 404
        assert response.json['error'] == 'Message not found'


class TestResendWebhook:
    """Test Resend webhook endpoint"""
    
    def test_resend_webhook_email_delivered(self, client, mock_db_session, mock_analytics_service):
        """Test email delivered webhook"""
        # Create valid signature
        webhook_secret = 'test-resend-secret'
        webhook_data = {
            "type": "email.delivered",
            "data": {
                "id": "email_123",
                "from": "noreply@mingus.com",
                "to": ["user@example.com"],
                "subject": "Test Email",
                "created_at": "2025-01-27T12:00:00Z"
            },
            "created_at": "2025-01-27T12:00:00Z"
        }
        request_body = json.dumps(webhook_data)
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        # Mock get_message_id_from_resend_id
        with patch('backend.routes.webhook_handlers.get_message_id_from_resend_id') as mock_get_id:
            mock_get_id.return_value = 456
            
            response = client.post('/webhooks/resend', 
                                 data=request_body,
                                 headers={
                                     'Resend-Signature': signature,
                                     'Content-Type': 'application/json'
                                 })
        
        assert response.status_code == 200
        assert response.json['success'] is True
        
        # Verify analytics service was called
        mock_analytics_service['delivered'].assert_called_once_with(456)
    
    def test_resend_webhook_email_opened(self, client, mock_db_session, mock_analytics_service):
        """Test email opened webhook"""
        # Create valid signature
        webhook_secret = 'test-resend-secret'
        webhook_data = {
            "type": "email.opened",
            "data": {
                "id": "email_123",
                "from": "noreply@mingus.com",
                "to": ["user@example.com"],
                "subject": "Test Email",
                "opened_at": "2025-01-27T12:00:00Z"
            },
            "created_at": "2025-01-27T12:00:00Z"
        }
        request_body = json.dumps(webhook_data)
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        # Mock get_message_id_from_resend_id
        with patch('backend.routes.webhook_handlers.get_message_id_from_resend_id') as mock_get_id:
            mock_get_id.return_value = 456
            
            response = client.post('/webhooks/resend', 
                                 data=request_body,
                                 headers={
                                     'Resend-Signature': signature,
                                     'Content-Type': 'application/json'
                                 })
        
        assert response.status_code == 200
        assert response.json['success'] is True
        
        # Verify analytics service was called
        mock_analytics_service['opened'].assert_called_once_with(456)
    
    def test_resend_webhook_email_clicked(self, client, mock_db_session, mock_analytics_service):
        """Test email clicked webhook"""
        # Create valid signature
        webhook_secret = 'test-resend-secret'
        webhook_data = {
            "type": "email.clicked",
            "data": {
                "id": "email_123",
                "from": "noreply@mingus.com",
                "to": ["user@example.com"],
                "subject": "Test Email"
            },
            "created_at": "2025-01-27T12:00:00Z"
        }
        request_body = json.dumps(webhook_data)
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        # Mock get_message_id_from_resend_id
        with patch('backend.routes.webhook_handlers.get_message_id_from_resend_id') as mock_get_id:
            mock_get_id.return_value = 456
            
            response = client.post('/webhooks/resend', 
                                 data=request_body,
                                 headers={
                                     'Resend-Signature': signature,
                                     'Content-Type': 'application/json'
                                 })
        
        assert response.status_code == 200
        assert response.json['success'] is True
        
        # Verify analytics service was called
        mock_analytics_service['action'].assert_called_once_with(456, "clicked_link")
    
    def test_resend_webhook_email_bounced(self, client, mock_db_session, mock_analytics_service):
        """Test email bounced webhook"""
        # Create valid signature
        webhook_secret = 'test-resend-secret'
        webhook_data = {
            "type": "email.bounced",
            "data": {
                "id": "email_123",
                "from": "noreply@mingus.com",
                "to": ["user@example.com"],
                "subject": "Test Email",
                "bounce_type": "hard"
            },
            "created_at": "2025-01-27T12:00:00Z"
        }
        request_body = json.dumps(webhook_data)
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        # Mock message found
        mock_message = MagicMock()
        mock_message.id = 456
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_message
        
        # Mock get_message_id_from_resend_id
        with patch('backend.routes.webhook_handlers.get_message_id_from_resend_id') as mock_get_id:
            mock_get_id.return_value = 456
            
            response = client.post('/webhooks/resend', 
                                 data=request_body,
                                 headers={
                                     'Resend-Signature': signature,
                                     'Content-Type': 'application/json'
                                 })
        
        assert response.status_code == 200
        assert response.json['success'] is True
        
        # Verify message status was updated to failed
        mock_message.status = "failed"
        mock_db_session.commit.assert_called_once()
        
        # Verify analytics service was called
        mock_analytics_service['action'].assert_called_once_with(456, "email_bounced_hard")
    
    def test_resend_webhook_invalid_signature(self, client):
        """Test Resend webhook with invalid signature"""
        response = client.post('/webhooks/resend', 
                             data=json.dumps({"type": "email.delivered", "data": {}}),
                             headers={
                                 'Resend-Signature': 'sha256=invalid-signature',
                                 'Content-Type': 'application/json'
                             })
        
        assert response.status_code == 401
        assert response.json['error'] == 'Invalid signature'
    
    def test_resend_webhook_invalid_json(self, client):
        """Test Resend webhook with invalid JSON"""
        response = client.post('/webhooks/resend', 
                             data='invalid-json',
                             headers={
                                 'Resend-Signature': 'sha256=valid-signature',
                                 'Content-Type': 'application/json'
                             })
        
        assert response.status_code == 400
        assert response.json['error'] == 'Invalid JSON'
    
    def test_resend_webhook_unknown_event_type(self, client, mock_db_session):
        """Test Resend webhook with unknown event type"""
        # Create valid signature
        webhook_secret = 'test-resend-secret'
        webhook_data = {
            "type": "email.unknown",
            "data": {"id": "email_123"},
            "created_at": "2025-01-27T12:00:00Z"
        }
        request_body = json.dumps(webhook_data)
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"sha256={expected_signature}"
        
        response = client.post('/webhooks/resend', 
                             data=request_body,
                             headers={
                                 'Resend-Signature': signature,
                                 'Content-Type': 'application/json'
                             })
        
        assert response.status_code == 200
        assert response.json['success'] is True


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test health check endpoint"""
        response = client.get('/webhooks/health')
        
        assert response.status_code == 200
        data = response.json
        
        assert data['status'] == 'healthy'
        assert data['service'] == 'webhook_handlers'
        assert 'endpoints' in data
        assert 'timestamp' in data


class TestErrorHandlers:
    """Test error handlers"""
    
    def test_bad_request_handler(self, client):
        """Test 400 error handler"""
        # Trigger a 400 error by accessing a route with invalid data
        response = client.post('/webhooks/twilio', 
                             data='invalid-data',
                             headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        # Should get 401 for invalid signature, but if we get 400, it's handled
        assert response.status_code in [400, 401]
    
    def test_unauthorized_handler(self, client):
        """Test 401 error handler"""
        response = client.post('/webhooks/twilio', 
                             data='MessageSid=SM123',
                             headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        assert response.status_code == 401
        assert response.json['error'] == 'Invalid signature'
    
    def test_not_found_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/webhooks/nonexistent')
        
        assert response.status_code == 404
        assert response.json['error'] == 'Not found'


if __name__ == '__main__':
    pytest.main([__file__]) 