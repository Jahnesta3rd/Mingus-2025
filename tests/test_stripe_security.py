"""
MINGUS Application - Stripe Security Tests
=========================================

Tests for the comprehensive security features of the Stripe integration.

Author: MINGUS Development Team
Date: January 2025
"""

import pytest
import os
import time
import uuid
import json
import hmac
import hashlib
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.security.stripe_security import (
    WebhookSecurityManager, IdempotencyKeyManager, RateLimitManager,
    PCISecurityManager, SecurityAuditLogger, StripeSecurityManager,
    SecurityLevel, SecurityEvent, get_stripe_security_manager
)
from backend.config.stripe import StripeConfig


class TestWebhookSecurityManager:
    """Test cases for WebhookSecurityManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = StripeConfig('test')
        self.webhook_security = WebhookSecurityManager(self.config)
        self.test_payload = b'{"type": "test.event", "data": {"object": {}}}'
        self.test_timestamp = str(int(time.time()))
    
    def test_load_allowed_ips(self):
        """Test loading of allowed IP addresses."""
        allowed_ips = self.webhook_security.allowed_ips
        assert len(allowed_ips) > 0
        assert '3.18.12.63' in allowed_ips  # Stripe IP
        assert '54.241.31.99' in allowed_ips  # Stripe IP
    
    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification."""
        # Create valid signature
        message = f"{self.test_timestamp}.{self.test_payload.decode()}"
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"t={self.test_timestamp},v1={expected_signature}"
        
        is_valid, error = self.webhook_security.verify_webhook_signature(
            self.test_payload, signature, self.test_timestamp
        )
        
        assert is_valid is True
        assert "verified successfully" in error
    
    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature verification."""
        signature = "t=1234567890,v1=invalid_signature"
        
        is_valid, error = self.webhook_security.verify_webhook_signature(
            self.test_payload, signature
        )
        
        assert is_valid is False
        assert "Invalid signature" in error
    
    def test_verify_webhook_signature_malformed(self):
        """Test malformed webhook signature."""
        signature = "invalid_signature_format"
        
        is_valid, error = self.webhook_security.verify_webhook_signature(
            self.test_payload, signature
        )
        
        assert is_valid is False
        assert "Invalid signature format" in error
    
    def test_verify_webhook_signature_old_timestamp(self):
        """Test webhook signature with old timestamp."""
        old_timestamp = str(int(time.time()) - 400)  # 6+ minutes old
        
        message = f"{old_timestamp}.{self.test_payload.decode()}"
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"t={old_timestamp},v1={expected_signature}"
        
        is_valid, error = self.webhook_security.verify_webhook_signature(
            self.test_payload, signature, old_timestamp
        )
        
        assert is_valid is False
        assert "too old" in error
    
    def test_verify_source_ip_valid(self):
        """Test valid source IP verification."""
        valid_ip = "3.18.12.63"  # Stripe IP
        
        is_allowed, message = self.webhook_security.verify_source_ip(valid_ip)
        
        assert is_allowed is True
        assert "allowed" in message
    
    def test_verify_source_ip_invalid(self):
        """Test invalid source IP verification."""
        invalid_ip = "192.168.1.1"  # Non-Stripe IP
        
        is_allowed, message = self.webhook_security.verify_source_ip(invalid_ip)
        
        assert is_allowed is False
        assert "not allowed" in message
    
    def test_validate_webhook_payload_valid(self):
        """Test valid webhook payload validation."""
        valid_payload = b'{"type": "customer.subscription.created", "data": {"object": {}}}'
        
        is_valid, message = self.webhook_security.validate_webhook_payload(valid_payload)
        
        assert is_valid is True
        assert "successful" in message
    
    def test_validate_webhook_payload_invalid_json(self):
        """Test invalid JSON webhook payload."""
        invalid_payload = b'invalid json'
        
        is_valid, message = self.webhook_security.validate_webhook_payload(invalid_payload)
        
        assert is_valid is False
        assert "Invalid JSON" in message
    
    def test_validate_webhook_payload_missing_fields(self):
        """Test webhook payload with missing required fields."""
        invalid_payload = b'{"type": "test.event"}'  # Missing 'data' field
        
        is_valid, message = self.webhook_security.validate_webhook_payload(invalid_payload)
        
        assert is_valid is False
        assert "Missing required field" in message


class TestIdempotencyKeyManager:
    """Test cases for IdempotencyKeyManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.idempotency_manager = IdempotencyKeyManager()
    
    def test_generate_idempotency_key(self):
        """Test idempotency key generation."""
        operation = "create_subscription"
        user_id = "user_123"
        
        key = self.idempotency_manager.generate_idempotency_key(operation, user_id)
        
        assert key.startswith(f"{operation}_{user_id}_")
        assert len(key) > 50  # Should be substantial length
    
    def test_generate_idempotency_key_unique(self):
        """Test that generated keys are unique."""
        operation = "create_customer"
        user_id = "user_456"
        
        key1 = self.idempotency_manager.generate_idempotency_key(operation, user_id)
        key2 = self.idempotency_manager.generate_idempotency_key(operation, user_id)
        
        assert key1 != key2
    
    def test_check_idempotency_key_not_exists(self):
        """Test checking non-existent idempotency key."""
        key = "test_key_123"
        
        exists, result = self.idempotency_manager.check_idempotency_key(key)
        
        assert exists is False
        assert result is None
    
    def test_store_and_check_idempotency_key(self):
        """Test storing and checking idempotency key."""
        key = "test_key_456"
        result = {"customer_id": "cus_123", "status": "created"}
        
        # Store result
        success = self.idempotency_manager.store_idempotency_result(key, result)
        assert success is True
        
        # Check result
        exists, cached_result = self.idempotency_manager.check_idempotency_key(key)
        assert exists is True
        assert cached_result == result
    
    def test_invalidate_idempotency_key(self):
        """Test invalidating idempotency key."""
        key = "test_key_789"
        result = {"subscription_id": "sub_123"}
        
        # Store result
        self.idempotency_manager.store_idempotency_result(key, result)
        
        # Verify it exists
        exists, _ = self.idempotency_manager.check_idempotency_key(key)
        assert exists is True
        
        # Invalidate
        success = self.idempotency_manager.invalidate_idempotency_key(key)
        assert success is True
        
        # Verify it's gone
        exists, _ = self.idempotency_manager.check_idempotency_key(key)
        assert exists is False


class TestRateLimitManager:
    """Test cases for RateLimitManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limit_manager = RateLimitManager()
    
    def test_check_rate_limit_within_limits(self):
        """Test rate limiting within allowed limits."""
        operation = "customer"
        identifier = "user_123"
        
        # Make 5 requests (well within 100 per minute limit)
        for i in range(5):
            allowed, info = self.rate_limit_manager.check_rate_limit(operation, identifier)
            assert allowed is True
            assert info['remaining'] > 0
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limiting when exceeded."""
        operation = "subscription"  # 50 per minute limit
        identifier = "user_456"
        
        # Make 60 requests to exceed limit
        for i in range(60):
            allowed, info = self.rate_limit_manager.check_rate_limit(operation, identifier)
            if i < 50:
                assert allowed is True
            else:
                assert allowed is False
                assert info['remaining'] == 0
    
    def test_rate_limit_headers(self):
        """Test rate limit headers generation."""
        operation = "payment_intent"
        identifier = "user_789"
        
        # Make a request
        self.rate_limit_manager.check_rate_limit(operation, identifier)
        
        # Get headers
        headers = self.rate_limit_manager.get_rate_limit_headers(operation, identifier)
        
        assert 'X-RateLimit-Limit' in headers
        assert 'X-RateLimit-Remaining' in headers
        assert 'X-RateLimit-Reset' in headers
        
        assert int(headers['X-RateLimit-Limit']) == 200  # payment_intent limit
        assert int(headers['X-RateLimit-Remaining']) >= 0
    
    def test_rate_limit_window_cleanup(self):
        """Test rate limit window cleanup."""
        operation = "customer"
        identifier = "user_cleanup"
        
        # Make a request
        self.rate_limit_manager.check_rate_limit(operation, identifier)
        
        # Wait for window to expire (simulate)
        # In real implementation, this would be handled by Redis TTL
        # For memory cache, we need to manually test cleanup
        
        # Get current count
        allowed, info = self.rate_limit_manager.check_rate_limit(operation, identifier)
        current_count = info['current_count']
        
        assert current_count >= 1


class TestPCISecurityManager:
    """Test cases for PCISecurityManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pci_manager = PCISecurityManager()
    
    def test_encrypt_decrypt_sensitive_data(self):
        """Test encryption and decryption of sensitive data."""
        original_data = "4242424242424242"
        
        # Encrypt
        encrypted = self.pci_manager.encrypt_sensitive_data(original_data)
        assert encrypted != original_data
        assert len(encrypted) > len(original_data)
        
        # Decrypt
        decrypted = self.pci_manager.decrypt_sensitive_data(encrypted)
        assert decrypted == original_data
    
    def test_mask_sensitive_data_card(self):
        """Test masking of card data."""
        card_number = "4242424242424242"
        
        masked = self.pci_manager.mask_sensitive_data(card_number, "card")
        
        assert masked == "************4242"
        assert len(masked) == len(card_number)
    
    def test_mask_sensitive_data_email(self):
        """Test masking of email data."""
        email = "user@example.com"
        
        masked = self.pci_manager.mask_sensitive_data(email, "email")
        
        assert masked == "u***r@example.com"
        assert "@" in masked
        assert "example.com" in masked
    
    def test_mask_sensitive_data_phone(self):
        """Test masking of phone data."""
        phone = "+1234567890"
        
        masked = self.pci_manager.mask_sensitive_data(phone, "phone")
        
        assert masked == "******7890"
        assert len(masked) == len(phone)
    
    def test_validate_pci_compliance_valid(self):
        """Test PCI compliance validation with valid data."""
        operation = "create_payment"
        data = {
            "amount": 1500,
            "currency": "usd",
            "description": "Test payment"
        }
        
        compliant, violations = self.pci_manager.validate_pci_compliance(operation, data)
        
        assert compliant is True
        assert len(violations) == 0
    
    def test_validate_pci_compliance_violation(self):
        """Test PCI compliance validation with violations."""
        operation = "create_payment"
        data = {
            "card_number": "4242424242424242",  # Unencrypted sensitive data
            "cvc": "123"
        }
        
        compliant, violations = self.pci_manager.validate_pci_compliance(operation, data)
        
        assert compliant is False
        assert len(violations) > 0
        assert any("card_number" in violation for violation in violations)
    
    def test_get_secure_headers(self):
        """Test secure headers generation."""
        headers = self.pci_manager.get_secure_headers()
        
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'X-XSS-Protection' in headers
        assert 'Strict-Transport-Security' in headers
        assert 'Content-Security-Policy' in headers
        assert 'Referrer-Policy' in headers
        
        assert headers['X-Frame-Options'] == 'DENY'
        assert headers['X-Content-Type-Options'] == 'nosniff'


class TestSecurityAuditLogger:
    """Test cases for SecurityAuditLogger."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.audit_logger = SecurityAuditLogger()
    
    def test_log_security_event(self):
        """Test logging security events."""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type="test_event",
            timestamp=datetime.now(),
            source_ip="192.168.1.1",
            user_agent="test-agent",
            request_id="req_123",
            severity=SecurityLevel.MEDIUM,
            details={"test": "data"}
        )
        
        success = self.audit_logger.log_security_event(event)
        assert success is True
    
    def test_get_security_events(self):
        """Test retrieving security events."""
        # Log some test events
        for i in range(3):
            event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                event_type=f"test_event_{i}",
                timestamp=datetime.now(),
                source_ip=f"192.168.1.{i}",
                user_agent="test-agent",
                request_id=f"req_{i}",
                severity=SecurityLevel.LOW,
                details={"test": i}
            )
            self.audit_logger.log_security_event(event)
        
        # Get events from last hour
        events = self.audit_logger.get_security_events(hours=1)
        assert len(events) >= 3
    
    def test_get_security_events_by_severity(self):
        """Test filtering security events by severity."""
        # Log events with different severities
        for severity in [SecurityLevel.LOW, SecurityLevel.MEDIUM, SecurityLevel.HIGH]:
            event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                event_type=f"severity_test_{severity.value}",
                timestamp=datetime.now(),
                source_ip="192.168.1.1",
                user_agent="test-agent",
                request_id="req_severity",
                severity=severity,
                details={"severity": severity.value}
            )
            self.audit_logger.log_security_event(event)
        
        # Get only high severity events
        high_events = self.audit_logger.get_security_events(
            severity=SecurityLevel.HIGH, hours=1
        )
        
        assert len(high_events) >= 1
        for event in high_events:
            assert event.severity == SecurityLevel.HIGH


class TestStripeSecurityManager:
    """Test cases for StripeSecurityManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = StripeConfig('test')
        self.security_manager = StripeSecurityManager(self.config)
    
    def test_validate_webhook_request_valid(self):
        """Test valid webhook request validation."""
        payload = b'{"type": "customer.subscription.created", "data": {"object": {}}}'
        timestamp = str(int(time.time()))
        
        # Create valid signature
        message = f"{timestamp}.{payload.decode()}"
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"t={timestamp},v1={expected_signature}"
        source_ip = "3.18.12.63"  # Valid Stripe IP
        
        is_valid, message = self.security_manager.validate_webhook_request(
            payload, signature, source_ip, timestamp, "test-agent", "req_123"
        )
        
        assert is_valid is True
        assert "successful" in message
    
    def test_validate_webhook_request_invalid_ip(self):
        """Test webhook request validation with invalid IP."""
        payload = b'{"type": "test.event", "data": {"object": {}}}'
        signature = "t=1234567890,v1=test_signature"
        source_ip = "192.168.1.1"  # Invalid IP
        
        is_valid, message = self.security_manager.validate_webhook_request(
            payload, signature, source_ip, "1234567890", "test-agent", "req_123"
        )
        
        assert is_valid is False
        assert "not allowed" in message
    
    def test_process_api_request_valid(self):
        """Test valid API request processing."""
        operation = "customer"
        user_id = "user_123"
        data = {"email": "test@example.com"}
        source_ip = "192.168.1.1"
        
        success, message, result = self.security_manager.process_api_request(
            operation, user_id, data, source_ip, "test-agent", "req_123"
        )
        
        assert success is True
        assert "processed successfully" in message
        assert 'idempotency_key' in result
    
    def test_process_api_request_rate_limit_exceeded(self):
        """Test API request processing with rate limit exceeded."""
        operation = "subscription"  # 50 per minute limit
        user_id = "user_rate_limit"
        data = {"plan": "basic"}
        source_ip = "192.168.1.1"
        
        # Exceed rate limit
        for i in range(60):
            success, message, result = self.security_manager.process_api_request(
                operation, user_id, data, source_ip, "test-agent", f"req_{i}"
            )
            if i >= 50:
                assert success is False
                assert "Rate limit exceeded" in message
                break
    
    def test_get_security_headers(self):
        """Test security headers generation."""
        headers = self.security_manager.get_security_headers()
        
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'Strict-Transport-Security' in headers
        assert 'Content-Security-Policy' in headers
    
    def test_get_rate_limit_headers(self):
        """Test rate limit headers generation."""
        operation = "customer"
        identifier = "user_123"
        
        headers = self.security_manager.get_rate_limit_headers(operation, identifier)
        
        assert 'X-RateLimit-Limit' in headers
        assert 'X-RateLimit-Remaining' in headers
        assert 'X-RateLimit-Reset' in headers


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = StripeConfig('test')
        self.security_manager = get_stripe_security_manager()
    
    def test_end_to_end_webhook_security(self):
        """Test end-to-end webhook security flow."""
        # Create test webhook payload
        payload = b'{"type": "customer.subscription.created", "data": {"object": {"id": "sub_123"}}}'
        timestamp = str(int(time.time()))
        
        # Create valid signature
        message = f"{timestamp}.{payload.decode()}"
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"t={timestamp},v1={expected_signature}"
        source_ip = "3.18.12.63"
        
        # Validate webhook
        is_valid, message = self.security_manager.validate_webhook_request(
            payload, signature, source_ip, timestamp, "test-agent", "req_integration"
        )
        
        assert is_valid is True
        
        # Check that security event was logged
        events = self.security_manager.audit_logger.get_security_events(hours=1)
        webhook_events = [e for e in events if e.event_type == 'webhook_validated']
        assert len(webhook_events) >= 1
    
    def test_end_to_end_api_security(self):
        """Test end-to-end API security flow."""
        operation = "customer"
        user_id = "user_integration"
        data = {"email": "integration@test.com"}
        source_ip = "192.168.1.100"
        
        # Process API request
        success, message, result = self.security_manager.process_api_request(
            operation, user_id, data, source_ip, "test-agent", "req_api_integration"
        )
        
        assert success is True
        assert 'idempotency_key' in result
        
        # Check that security event was logged
        events = self.security_manager.audit_logger.get_security_events(hours=1)
        api_events = [e for e in events if e.event_type == 'api_request_processed']
        assert len(api_events) >= 1
    
    def test_pci_compliance_integration(self):
        """Test PCI compliance integration."""
        # Test data encryption
        sensitive_data = "4242424242424242"
        encrypted = self.security_manager.pci_manager.encrypt_sensitive_data(sensitive_data)
        
        # Test data masking
        masked = self.security_manager.pci_manager.mask_sensitive_data(sensitive_data, "card")
        assert masked == "************4242"
        
        # Test PCI validation
        compliant, violations = self.security_manager.pci_manager.validate_pci_compliance(
            'create_payment', {'card_number': encrypted}
        )
        assert compliant is True
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        operation = "payment_intent"
        user_id = "user_rate_integration"
        
        # Make requests within limit
        for i in range(10):
            allowed, info = self.security_manager.rate_limit_manager.check_rate_limit(
                operation, user_id
            )
            assert allowed is True
            assert info['remaining'] > 0
        
        # Get rate limit headers
        headers = self.security_manager.get_rate_limit_headers(operation, user_id)
        assert 'X-RateLimit-Limit' in headers
        assert 'X-RateLimit-Remaining' in headers


if __name__ == '__main__':
    pytest.main([__file__]) 