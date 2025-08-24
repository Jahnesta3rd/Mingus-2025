#!/usr/bin/env python3
"""
Test script for the enhanced customer.created webhook handler
Demonstrates how to use the handler with sample Stripe webhook data
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_customer_webhook_data() -> Dict[str, Any]:
    """Create sample Stripe customer.created webhook data"""
    return {
        "id": "evt_customer_created_1234567890",
        "object": "event",
        "type": "customer.created",
        "created": int(datetime.utcnow().timestamp()),
        "livemode": False,
        "api_version": "2020-08-27",
        "data": {
            "object": {
                "id": "cus_customer_created_001",
                "object": "customer",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "phone": "+1234567890",
                "address": {
                    "line1": "123 Main St",
                    "line2": "Apt 4B",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "US"
                },
                "tax_exempt": "none",
                "metadata": {
                    "mingus_user_id": "123",
                    "source": "webhook_test",
                    "is_new_user": "true",
                    "signup_method": "stripe_checkout"
                },
                "created": int(datetime.utcnow().timestamp()),
                "livemode": False
            }
        }
    }

def create_sample_webhook_event(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a sample webhook event object"""
    return {
        "event_id": webhook_data["id"],
        "event_type": webhook_data["type"],
        "event_data": webhook_data["data"],
        "created_at": datetime.fromtimestamp(webhook_data["created"]),
        "livemode": webhook_data["livemode"],
        "api_version": webhook_data["api_version"],
        "request_id": "req_test_1234567890",
        "source_ip": "192.168.1.1",
        "user_agent": "Stripe-Webhook/1.0"
    }

def test_customer_created_webhook():
    """Test the customer.created webhook handler"""
    try:
        # Import the webhook manager
        from backend.webhooks.stripe_webhooks import StripeWebhookManager, WebhookEvent
        from backend.config.base import Config
        from backend.models import db_session
        
        # Create sample webhook data
        webhook_data = create_sample_customer_webhook_data()
        webhook_event_data = create_sample_webhook_event(webhook_data)
        
        # Create webhook event object
        event = WebhookEvent(**webhook_event_data)
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Process the webhook
        logger.info("Processing customer.created webhook...")
        result = webhook_manager._handle_customer_created(event)
        
        # Display results
        logger.info("Webhook processing completed!")
        logger.info(f"Success: {result.success}")
        logger.info(f"Message: {result.message}")
        
        if result.success:
            logger.info("Changes made:")
            for change in result.changes:
                logger.info(f"  - {change}")
            logger.info(f"Notifications sent: {result.notifications_sent}")
        else:
            logger.error(f"Error: {result.error}")
        
        return result
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("Make sure you're running this from the correct directory")
        return None
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return None

def test_validation_functions():
    """Test the validation functions independently"""
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Test valid customer data
        valid_customer_data = {
            "id": "cus_valid_001",
            "email": "test@example.com",
            "name": "Test User",
            "metadata": {"mingus_user_id": "123"}
        }
        
        # Test validation
        validation_result = webhook_manager._validate_customer_data(valid_customer_data)
        logger.info(f"Validation result: {validation_result}")
        
        # Test invalid customer data
        invalid_customer_data = {
            "id": "invalid_id",
            "email": "invalid-email",
            "metadata": {}
        }
        
        validation_result = webhook_manager._validate_customer_data(invalid_customer_data)
        logger.info(f"Invalid data validation result: {validation_result}")
        
        # Test email validation
        test_emails = [
            "valid@example.com",
            "invalid-email",
            "test@domain",
            "user.name+tag@domain.co.uk"
        ]
        
        for email in test_emails:
            is_valid = webhook_manager._is_valid_email(email)
            logger.info(f"Email '{email}' is valid: {is_valid}")
        
    except Exception as e:
        logger.error(f"Validation test failed: {e}")

def main():
    """Main test function"""
    logger.info("Starting customer.created webhook handler tests...")
    
    # Test validation functions
    logger.info("\n=== Testing Validation Functions ===")
    test_validation_functions()
    
    # Test full webhook processing
    logger.info("\n=== Testing Full Webhook Processing ===")
    result = test_customer_created_webhook()
    
    if result and result.success:
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Some tests failed!")
    
    logger.info("\nTest completed!")

if __name__ == "__main__":
    main() 