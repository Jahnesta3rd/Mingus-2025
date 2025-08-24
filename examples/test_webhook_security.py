#!/usr/bin/env python3
"""
Test script for enhanced webhook security and reliability features
Demonstrates signature verification, rate limiting, duplicate detection, and security validation
"""

import json
import logging
import time
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_webhook_payload() -> bytes:
    """Create a test webhook payload"""
    payload = {
        "id": "evt_test_webhook_1234567890",
        "object": "event",
        "type": "customer.created",
        "created": int(time.time()),
        "livemode": False,
        "api_version": "2020-08-27",
        "data": {
            "object": {
                "id": "cus_test_customer_001",
                "object": "customer",
                "email": "test@example.com",
                "name": "Test Customer",
                "metadata": {
                    "mingus_user_id": "123",
                    "source": "test"
                }
            }
        }
    }
    return json.dumps(payload).encode('utf-8')

def create_test_signature(payload: bytes, timestamp: int, secret: str) -> str:
    """Create a test Stripe webhook signature"""
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"t={timestamp},v1={signature}"

def create_invalid_signature(payload: bytes, timestamp: int, secret: str) -> str:
    """Create an invalid signature for testing"""
    # Use wrong secret to create invalid signature
    wrong_secret = "wrong_secret"
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    signature = hmac.new(
        wrong_secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"t={timestamp},v1={signature}"

def test_signature_verification():
    """Test enhanced signature verification"""
    logger.info("=== Testing Enhanced Signature Verification ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Create test payload and signature
        payload = create_test_webhook_payload()
        timestamp = int(time.time())
        secret = config.STRIPE_WEBHOOK_SECRET or "whsec_test_secret"
        
        # Test valid signature
        valid_signature = create_test_signature(payload, timestamp, secret)
        result = webhook_manager._verify_webhook_signature_enhanced(payload, valid_signature)
        
        logger.info(f"Valid signature test: {result}")
        assert result['valid'], "Valid signature should pass verification"
        
        # Test invalid signature
        invalid_signature = create_invalid_signature(payload, timestamp, secret)
        result = webhook_manager._verify_webhook_signature_enhanced(payload, invalid_signature)
        
        logger.info(f"Invalid signature test: {result}")
        assert not result['valid'], "Invalid signature should fail verification"
        
        # Test old timestamp
        old_timestamp = int(time.time()) - 400  # 6+ minutes old
        old_signature = create_test_signature(payload, old_timestamp, secret)
        result = webhook_manager._verify_webhook_signature_enhanced(payload, old_signature)
        
        logger.info(f"Old timestamp test: {result}")
        assert not result['valid'], "Old timestamp should fail verification"
        
        # Test malformed signature
        malformed_signature = "invalid_signature_format"
        result = webhook_manager._verify_webhook_signature_enhanced(payload, malformed_signature)
        
        logger.info(f"Malformed signature test: {result}")
        assert not result['valid'], "Malformed signature should fail verification"
        
        logger.info("✅ All signature verification tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Signature verification test failed: {e}")

def test_rate_limiting():
    """Test rate limiting functionality"""
    logger.info("=== Testing Rate Limiting ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        test_ip = "192.168.1.100"
        
        # Test normal rate limiting
        for i in range(5):
            result = webhook_manager._check_rate_limit(test_ip)
            logger.info(f"Rate limit check {i+1}: {result}")
            assert result, f"Rate limit check {i+1} should pass"
        
        # Test rate limit exceeded (if configured)
        if hasattr(config, 'WEBHOOK_RATE_LIMIT') and config.WEBHOOK_RATE_LIMIT:
            # Make many requests to trigger rate limiting
            for i in range(config.WEBHOOK_RATE_LIMIT + 10):
                result = webhook_manager._check_rate_limit(test_ip)
                if not result:
                    logger.info(f"Rate limit exceeded at request {i+1}")
                    break
        
        logger.info("✅ Rate limiting tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")

def test_duplicate_detection():
    """Test duplicate event detection"""
    logger.info("=== Testing Duplicate Event Detection ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager, WebhookEvent
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Create test event
        event = WebhookEvent(
            event_id="evt_test_duplicate_001",
            event_type="customer.created",
            event_data={"object": {"id": "cus_test"}},
            created_at=datetime.utcnow(),
            livemode=False,
            api_version="2020-08-27",
            request_id="req_test_001",
            source_ip="192.168.1.100",
            user_agent="test-agent"
        )
        
        # Test first occurrence
        is_duplicate = webhook_manager._is_duplicate_event(event)
        logger.info(f"First occurrence test: {is_duplicate}")
        assert not is_duplicate, "First occurrence should not be duplicate"
        
        # Test duplicate detection
        is_duplicate = webhook_manager._is_duplicate_event(event)
        logger.info(f"Duplicate detection test: {is_duplicate}")
        assert is_duplicate, "Second occurrence should be duplicate"
        
        # Test different event
        different_event = WebhookEvent(
            event_id="evt_test_duplicate_002",
            event_type="customer.created",
            event_data={"object": {"id": "cus_test"}},
            created_at=datetime.utcnow(),
            livemode=False,
            api_version="2020-08-27",
            request_id="req_test_002",
            source_ip="192.168.1.100",
            user_agent="test-agent"
        )
        
        is_duplicate = webhook_manager._is_duplicate_event(different_event)
        logger.info(f"Different event test: {is_duplicate}")
        assert not is_duplicate, "Different event should not be duplicate"
        
        logger.info("✅ Duplicate detection tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Duplicate detection test failed: {e}")

def test_security_validation():
    """Test security validation features"""
    logger.info("=== Testing Security Validation ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Test valid security validation
        payload = create_test_webhook_payload()
        signature = "t=1234567890,v1=test_signature"
        source_ip = "192.168.1.100"
        user_agent = "Stripe-Webhook/1.0"
        
        result = webhook_manager._validate_webhook_security(payload, signature, source_ip, user_agent)
        logger.info(f"Valid security validation test: {result}")
        
        # Test oversized payload
        oversized_payload = b"x" * (1024 * 1024 + 1)  # 1MB + 1 byte
        result = webhook_manager._validate_webhook_security(oversized_payload, signature, source_ip, user_agent)
        logger.info(f"Oversized payload test: {result}")
        assert not result['valid'], "Oversized payload should fail validation"
        
        # Test invalid signature format
        invalid_signature = "invalid_format"
        result = webhook_manager._validate_webhook_security(payload, invalid_signature, source_ip, user_agent)
        logger.info(f"Invalid signature format test: {result}")
        assert not result['valid'], "Invalid signature format should fail validation"
        
        logger.info("✅ Security validation tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Security validation test failed: {e}")

def test_event_validation():
    """Test webhook event validation"""
    logger.info("=== Testing Event Validation ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager, WebhookEvent
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Test valid event
        valid_event = WebhookEvent(
            event_id="evt_test_valid_001",
            event_type="customer.created",
            event_data={"object": {"id": "cus_test"}},
            created_at=datetime.utcnow(),
            livemode=False,
            api_version="2020-08-27",
            request_id="req_test_001",
            source_ip="192.168.1.100",
            user_agent="test-agent"
        )
        
        result = webhook_manager._validate_webhook_event(valid_event)
        logger.info(f"Valid event test: {result}")
        assert result['valid'], "Valid event should pass validation"
        
        # Test old event
        old_event = WebhookEvent(
            event_id="evt_test_old_001",
            event_type="customer.created",
            event_data={"object": {"id": "cus_test"}},
            created_at=datetime.fromtimestamp(time.time() - 7200),  # 2 hours old
            livemode=False,
            api_version="2020-08-27",
            request_id="req_test_002",
            source_ip="192.168.1.100",
            user_agent="test-agent"
        )
        
        result = webhook_manager._validate_webhook_event(old_event)
        logger.info(f"Old event test: {result}")
        assert not result['valid'], "Old event should fail validation"
        
        # Test invalid event data structure
        invalid_event = WebhookEvent(
            event_id="evt_test_invalid_001",
            event_type="customer.created",
            event_data="invalid_data",  # Should be dict
            created_at=datetime.utcnow(),
            livemode=False,
            api_version="2020-08-27",
            request_id="req_test_003",
            source_ip="192.168.1.100",
            user_agent="test-agent"
        )
        
        result = webhook_manager._validate_webhook_event(invalid_event)
        logger.info(f"Invalid event data test: {result}")
        assert not result['valid'], "Invalid event data should fail validation"
        
        logger.info("✅ Event validation tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Event validation test failed: {e}")

def test_full_webhook_processing():
    """Test full webhook processing with security features"""
    logger.info("=== Testing Full Webhook Processing ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Create test payload and signature
        payload = create_test_webhook_payload()
        timestamp = int(time.time())
        secret = config.STRIPE_WEBHOOK_SECRET or "whsec_test_secret"
        signature = create_test_signature(payload, timestamp, secret)
        
        # Test successful processing
        result = webhook_manager.process_webhook(
            payload=payload,
            signature=signature,
            source_ip="192.168.1.100",
            user_agent="Stripe-Webhook/1.0",
            request_id="req_test_full_001"
        )
        
        logger.info(f"Full webhook processing test: {result}")
        
        # Test processing with invalid signature
        invalid_signature = create_invalid_signature(payload, timestamp, secret)
        result = webhook_manager.process_webhook(
            payload=payload,
            signature=invalid_signature,
            source_ip="192.168.1.100",
            user_agent="Stripe-Webhook/1.0",
            request_id="req_test_full_002"
        )
        
        logger.info(f"Invalid signature processing test: {result}")
        assert not result.success, "Invalid signature should cause processing failure"
        
        logger.info("✅ Full webhook processing tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Full webhook processing test failed: {e}")

def main():
    """Main test function"""
    logger.info("Starting enhanced webhook security and reliability tests...")
    
    # Run all tests
    test_signature_verification()
    test_rate_limiting()
    test_duplicate_detection()
    test_security_validation()
    test_event_validation()
    test_full_webhook_processing()
    
    logger.info("🎉 All webhook security and reliability tests completed!")

if __name__ == "__main__":
    main() 