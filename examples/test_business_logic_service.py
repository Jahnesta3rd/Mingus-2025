#!/usr/bin/env python3
"""
Test script for Business Logic Service
Demonstrates feature access control updates and user notifications for billing events
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_customer() -> Dict[str, Any]:
    """Create a test customer"""
    return {
        "id": f"cus_test_{uuid.uuid4().hex[:8]}",
        "email": "test@example.com",
        "name": "Test Customer",
        "phone": "+1234567890",
        "created": int(time.time()),
        "livemode": False
    }

def create_test_subscription(customer_id: str, pricing_tier: str = "premium") -> Dict[str, Any]:
    """Create a test subscription"""
    return {
        "id": f"sub_test_{uuid.uuid4().hex[:8]}",
        "customer": customer_id,
        "status": "active",
        "current_period_start": int(time.time()),
        "current_period_end": int(time.time() + 30 * 24 * 3600),  # 30 days
        "trial_end": None,
        "cancel_at_period_end": False,
        "items": {
            "data": [
                {
                    "id": f"si_test_{uuid.uuid4().hex[:8]}",
                    "price": {
                        "id": f"price_test_{uuid.uuid4().hex[:8]}",
                        "unit_amount": 2900,  # $29.00
                        "currency": "usd",
                        "recurring": {
                            "interval": "month"
                        }
                    }
                }
            ]
        },
        "metadata": {
            "pricing_tier": pricing_tier,
            "features": "advanced_analytics,custom_reports,priority_support"
        }
    }

def create_test_invoice(customer_id: str, subscription_id: str, status: str = "paid") -> Dict[str, Any]:
    """Create a test invoice"""
    return {
        "id": f"in_test_{uuid.uuid4().hex[:8]}",
        "customer": customer_id,
        "subscription": subscription_id,
        "status": status,
        "amount_paid": 2900,
        "amount_due": 2900,
        "currency": "usd",
        "created": int(time.time()),
        "due_date": int(time.time() + 7 * 24 * 3600),  # 7 days
        "hosted_invoice_url": "https://invoice.stripe.com/i/test",
        "invoice_pdf": "https://pay.stripe.com/invoice/test/pdf"
    }

def test_business_logic_service():
    """Test the business logic service functionality"""
    logger.info("=== Testing Business Logic Service ===")
    
    try:
        from backend.services.business_logic_service import BusinessLogicService, FeatureAccessLevel, NotificationType
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, Subscription, PricingTier, BillingHistory
        
        # Initialize business logic service
        config = Config()
        business_logic_service = BusinessLogicService(db_session, config)
        
        # Test 1: Feature access control for subscription creation
        logger.info("Test 1: Testing feature access control for subscription creation")
        
        # Create test customer
        test_customer_data = create_test_customer()
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=test_customer_data["id"],
            email=test_customer_data["email"],
            name=test_customer_data["name"],
            phone=test_customer_data["phone"]
        )
        
        # Create test subscription
        test_subscription_data = create_test_subscription(test_customer_data["id"], "premium")
        subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=test_subscription_data["id"],
            customer_id=customer.id,
            status=test_subscription_data["status"],
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd"
        )
        
        # Test feature access update
        feature_update = business_logic_service._update_feature_access_for_subscription(
            customer, subscription, test_subscription_data
        )
        
        logger.info(f"Feature access updated: {feature_update.reason}")
        logger.info(f"Features added: {feature_update.features_added}")
        logger.info(f"Features removed: {feature_update.features_removed}")
        logger.info(f"Access level: {feature_update.access_level.value}")
        
        # Test 2: User notifications for subscription creation
        logger.info("Test 2: Testing user notifications for subscription creation")
        
        welcome_notifications = business_logic_service._send_subscription_welcome_notifications(
            customer, subscription, test_subscription_data
        )
        
        logger.info(f"Welcome notifications sent: {len(welcome_notifications)}")
        for notification in welcome_notifications:
            logger.info(f"  Notification type: {notification.notification_type.value}")
            logger.info(f"  Subject: {notification.subject}")
            logger.info(f"  Priority: {notification.priority}")
            logger.info(f"  Channels: {notification.channels}")
        
        # Test 3: Payment success notifications
        logger.info("Test 3: Testing payment success notifications")
        
        # Create test billing record
        billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=subscription.id,
            stripe_invoice_id=f"in_test_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="paid",
            payment_date=datetime.now(timezone.utc)
        )
        
        payment_data = {
            "payment_method": "card",
            "payment_intent": f"pi_test_{uuid.uuid4().hex[:8]}",
            "receipt_url": "https://receipt.stripe.com/test"
        }
        
        payment_notifications = business_logic_service._send_payment_success_notifications(
            customer, billing_record, payment_data
        )
        
        logger.info(f"Payment success notifications sent: {len(payment_notifications)}")
        for notification in payment_notifications:
            logger.info(f"  Notification type: {notification.notification_type.value}")
            logger.info(f"  Subject: {notification.subject}")
            logger.info(f"  Priority: {notification.priority}")
        
        # Test 4: Payment failure notifications
        logger.info("Test 4: Testing payment failure notifications")
        
        failed_billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=subscription.id,
            stripe_invoice_id=f"in_test_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="failed",
            payment_date=None
        )
        
        failure_data = {
            "failure_reason": "insufficient_funds",
            "payment_method": "card",
            "next_payment_attempt": int(time.time() + 24 * 3600)  # 24 hours
        }
        
        failure_notifications = business_logic_service._send_payment_failure_notifications(
            customer, failed_billing_record, failure_data
        )
        
        logger.info(f"Payment failure notifications sent: {len(failure_notifications)}")
        for notification in failure_notifications:
            logger.info(f"  Notification type: {notification.notification_type.value}")
            logger.info(f"  Subject: {notification.subject}")
            logger.info(f"  Priority: {notification.priority}")
        
        # Test 5: Subscription cancellation notifications
        logger.info("Test 5: Testing subscription cancellation notifications")
        
        cancellation_data = {
            "reason": "customer_request",
            "effective_date": datetime.now(timezone.utc) + timedelta(days=30),
            "cancelled_at": datetime.now(timezone.utc)
        }
        
        cancellation_notifications = business_logic_service._send_cancellation_notifications(
            customer, subscription, cancellation_data
        )
        
        logger.info(f"Cancellation notifications sent: {len(cancellation_notifications)}")
        for notification in cancellation_notifications:
            logger.info(f"  Notification type: {notification.notification_type.value}")
            logger.info(f"  Subject: {notification.subject}")
            logger.info(f"  Priority: {notification.priority}")
        
        # Test 6: Trial ending notifications
        logger.info("Test 6: Testing trial ending notifications")
        
        trial_subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_trial_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="trialing",
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd",
            trial_end=datetime.now(timezone.utc) + timedelta(days=3)
        )
        
        trial_data = {
            "trial_end_date": trial_subscription.trial_end.isoformat(),
            "days_remaining": 3
        }
        
        trial_notifications = business_logic_service._send_trial_ending_notifications(
            customer, trial_subscription, trial_data
        )
        
        logger.info(f"Trial ending notifications sent: {len(trial_notifications)}")
        for notification in trial_notifications:
            logger.info(f"  Notification type: {notification.notification_type.value}")
            logger.info(f"  Subject: {notification.subject}")
            logger.info(f"  Priority: {notification.priority}")
        
        logger.info("✅ All business logic service tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Business logic service test failed: {e}")

def test_feature_access_control():
    """Test feature access control functionality"""
    logger.info("=== Testing Feature Access Control ===")
    
    try:
        from backend.services.business_logic_service import BusinessLogicService, FeatureAccessLevel
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, Subscription
        
        # Initialize business logic service
        config = Config()
        business_logic_service = BusinessLogicService(db_session, config)
        
        # Test 1: Basic tier feature access
        logger.info("Test 1: Testing basic tier feature access")
        
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_basic_{uuid.uuid4().hex[:8]}",
            email="basic@example.com",
            name="Basic Customer"
        )
        
        basic_subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_basic_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="active",
            pricing_tier="basic",
            billing_cycle="monthly",
            amount=9.00,
            currency="usd"
        )
        
        basic_subscription_data = {
            "id": basic_subscription.stripe_subscription_id,
            "status": "active",
            "metadata": {"pricing_tier": "basic"}
        }
        
        basic_feature_update = business_logic_service._update_feature_access_for_subscription(
            customer, basic_subscription, basic_subscription_data
        )
        
        logger.info(f"Basic tier features: {basic_feature_update.features_added}")
        logger.info(f"Basic tier access level: {basic_feature_update.access_level.value}")
        
        # Test 2: Premium tier feature access
        logger.info("Test 2: Testing premium tier feature access")
        
        premium_subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_premium_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="active",
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd"
        )
        
        premium_subscription_data = {
            "id": premium_subscription.stripe_subscription_id,
            "status": "active",
            "metadata": {"pricing_tier": "premium"}
        }
        
        premium_feature_update = business_logic_service._update_feature_access_for_subscription(
            customer, premium_subscription, premium_subscription_data
        )
        
        logger.info(f"Premium tier features: {premium_feature_update.features_added}")
        logger.info(f"Premium tier access level: {premium_feature_update.access_level.value}")
        
        # Test 3: Enterprise tier feature access
        logger.info("Test 3: Testing enterprise tier feature access")
        
        enterprise_subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_enterprise_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="active",
            pricing_tier="enterprise",
            billing_cycle="monthly",
            amount=99.00,
            currency="usd"
        )
        
        enterprise_subscription_data = {
            "id": enterprise_subscription.stripe_subscription_id,
            "status": "active",
            "metadata": {"pricing_tier": "enterprise"}
        }
        
        enterprise_feature_update = business_logic_service._update_feature_access_for_subscription(
            customer, enterprise_subscription, enterprise_subscription_data
        )
        
        logger.info(f"Enterprise tier features: {enterprise_feature_update.features_added}")
        logger.info(f"Enterprise tier access level: {enterprise_feature_update.access_level.value}")
        
        # Test 4: Feature access downgrade for cancellation
        logger.info("Test 4: Testing feature access downgrade for cancellation")
        
        cancellation_data = {
            "reason": "customer_request",
            "effective_date": datetime.now(timezone.utc) + timedelta(days=30)
        }
        
        downgrade_update = business_logic_service._downgrade_feature_access_for_cancellation(
            customer, enterprise_subscription, cancellation_data
        )
        
        logger.info(f"Downgrade reason: {downgrade_update.reason}")
        logger.info(f"Features removed: {downgrade_update.features_removed}")
        logger.info(f"New access level: {downgrade_update.access_level.value}")
        
        logger.info("✅ All feature access control tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Feature access control test failed: {e}")

def test_notification_templates():
    """Test notification template functionality"""
    logger.info("=== Testing Notification Templates ===")
    
    try:
        from backend.services.business_logic_service import BusinessLogicService
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, Subscription, BillingHistory
        
        # Initialize business logic service
        config = Config()
        business_logic_service = BusinessLogicService(db_session, config)
        
        # Create test customer
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_template_{uuid.uuid4().hex[:8]}",
            email="template@example.com",
            name="Template Customer"
        )
        
        # Test 1: Welcome message template
        logger.info("Test 1: Testing welcome message template")
        
        subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_template_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="active",
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd",
            next_billing_date=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        subscription_data = {
            "id": subscription.stripe_subscription_id,
            "status": "active",
            "metadata": {"pricing_tier": "premium"}
        }
        
        welcome_message = business_logic_service._get_welcome_message(
            customer, subscription, subscription_data
        )
        
        logger.info("Welcome message:")
        logger.info(welcome_message)
        
        # Test 2: Payment success message template
        logger.info("Test 2: Testing payment success message template")
        
        billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=subscription.id,
            stripe_invoice_id=f"in_template_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="paid",
            payment_date=datetime.now(timezone.utc),
            next_billing_date=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        payment_data = {
            "payment_method": "card",
            "receipt_url": "https://receipt.stripe.com/test"
        }
        
        payment_message = business_logic_service._get_payment_success_message(
            customer, billing_record, payment_data
        )
        
        logger.info("Payment success message:")
        logger.info(payment_message)
        
        # Test 3: Payment failure message template
        logger.info("Test 3: Testing payment failure message template")
        
        failed_billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=subscription.id,
            stripe_invoice_id=f"in_failed_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="failed"
        )
        
        failure_data = {
            "failure_reason": "insufficient_funds"
        }
        
        failure_message = business_logic_service._get_payment_failure_message(
            customer, failed_billing_record, failure_data
        )
        
        logger.info("Payment failure message:")
        logger.info(failure_message)
        
        # Test 4: Cancellation message template
        logger.info("Test 4: Testing cancellation message template")
        
        cancellation_data = {
            "reason": "customer_request",
            "effective_date": datetime.now(timezone.utc) + timedelta(days=30)
        }
        
        cancellation_message = business_logic_service._get_cancellation_message(
            customer, subscription, cancellation_data
        )
        
        logger.info("Cancellation message:")
        logger.info(cancellation_message)
        
        # Test 5: Trial ending message template
        logger.info("Test 5: Testing trial ending message template")
        
        trial_subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_trial_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="trialing",
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd",
            trial_end=datetime.now(timezone.utc) + timedelta(days=3)
        )
        
        trial_data = {
            "trial_end_date": trial_subscription.trial_end.isoformat(),
            "days_remaining": 3
        }
        
        trial_message = business_logic_service._get_trial_ending_message(
            customer, trial_subscription, trial_data
        )
        
        logger.info("Trial ending message:")
        logger.info(trial_message)
        
        # Test 6: Feature access message template
        logger.info("Test 6: Testing feature access message template")
        
        feature_message = business_logic_service._get_feature_access_message(
            customer, subscription
        )
        
        logger.info("Feature access message:")
        logger.info(feature_message)
        
        logger.info("✅ All notification template tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Notification template test failed: {e}")

def test_business_logic_integration():
    """Test business logic integration with webhook handlers"""
    logger.info("=== Testing Business Logic Integration ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, Subscription, BillingHistory
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Create test customer
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_integration_{uuid.uuid4().hex[:8]}",
            email="integration@example.com",
            name="Integration Customer"
        )
        
        # Test 1: Business logic for subscription creation
        logger.info("Test 1: Testing business logic for subscription creation")
        
        subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_integration_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="active",
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd"
        )
        
        subscription_data = {
            "id": subscription.stripe_subscription_id,
            "status": "active",
            "metadata": {"pricing_tier": "premium"}
        }
        
        creation_result = webhook_manager._execute_business_logic_for_subscription_created(
            customer, subscription, subscription_data
        )
        
        logger.info(f"Subscription creation business logic result: {creation_result['success']}")
        logger.info(f"Changes: {creation_result['changes']}")
        logger.info(f"Notifications sent: {creation_result['notifications_sent']}")
        
        # Test 2: Business logic for payment success
        logger.info("Test 2: Testing business logic for payment success")
        
        billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=subscription.id,
            stripe_invoice_id=f"in_integration_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="paid",
            payment_date=datetime.now(timezone.utc)
        )
        
        payment_data = {
            "payment_method": "card",
            "receipt_url": "https://receipt.stripe.com/test"
        }
        
        payment_result = webhook_manager._execute_business_logic_for_payment_succeeded(
            customer, billing_record, payment_data
        )
        
        logger.info(f"Payment success business logic result: {payment_result['success']}")
        logger.info(f"Changes: {payment_result['changes']}")
        logger.info(f"Notifications sent: {payment_result['notifications_sent']}")
        
        # Test 3: Business logic for subscription cancellation
        logger.info("Test 3: Testing business logic for subscription cancellation")
        
        cancellation_data = {
            "reason": "customer_request",
            "effective_date": datetime.now(timezone.utc) + timedelta(days=30)
        }
        
        cancellation_result = webhook_manager._execute_business_logic_for_subscription_cancelled(
            customer, subscription, cancellation_data
        )
        
        logger.info(f"Subscription cancellation business logic result: {cancellation_result['success']}")
        logger.info(f"Changes: {cancellation_result['changes']}")
        logger.info(f"Notifications sent: {cancellation_result['notifications_sent']}")
        
        logger.info("✅ All business logic integration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Business logic integration test failed: {e}")

def test_feature_configurations():
    """Test feature configurations"""
    logger.info("=== Testing Feature Configurations ===")
    
    try:
        from backend.services.business_logic_service import BusinessLogicService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize business logic service
        config = Config()
        business_logic_service = BusinessLogicService(db_session, config)
        
        # Test feature configurations for each tier
        tiers = ['basic', 'premium', 'enterprise', 'unlimited']
        
        for tier in tiers:
            logger.info(f"Testing {tier} tier configuration:")
            
            if tier in business_logic_service.feature_configs:
                tier_config = business_logic_service.feature_configs[tier]
                
                logger.info(f"  Features: {tier_config['features']}")
                logger.info(f"  Limits: {tier_config['limits']}")
                
                # Test feature count
                feature_count = len(tier_config['features'])
                logger.info(f"  Feature count: {feature_count}")
                
                # Test limits
                for limit_name, limit_value in tier_config['limits'].items():
                    if limit_value == -1:
                        logger.info(f"  {limit_name}: Unlimited")
                    else:
                        logger.info(f"  {limit_name}: {limit_value}")
            else:
                logger.warning(f"  No configuration found for {tier} tier")
        
        logger.info("✅ All feature configuration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Feature configuration test failed: {e}")

def main():
    """Main test function"""
    logger.info("Starting comprehensive business logic service tests...")
    
    # Run all tests
    test_business_logic_service()
    test_feature_access_control()
    test_notification_templates()
    test_business_logic_integration()
    test_feature_configurations()
    
    logger.info("🎉 All business logic service tests completed!")

if __name__ == "__main__":
    main() 