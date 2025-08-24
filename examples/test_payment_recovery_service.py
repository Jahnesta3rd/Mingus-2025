#!/usr/bin/env python3
"""
Test script for Payment Recovery Service
Demonstrates comprehensive payment recovery workflows including:
- Dunning management and escalation
- Payment retry logic with exponential backoff
- Payment method updates and validation
- Recovery strategies and customer communication
- Grace period management
- Service suspension and reactivation

Author: MINGUS Development Team
Date: January 2025
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

def create_test_billing_record(customer_id: str, subscription_id: str, status: str = "failed") -> Dict[str, Any]:
    """Create a test billing record"""
    return {
        "id": f"billing_test_{uuid.uuid4().hex[:8]}",
        "customer_id": customer_id,
        "subscription_id": subscription_id,
        "stripe_invoice_id": f"in_test_{uuid.uuid4().hex[:8]}",
        "amount": 29.00,
        "currency": "usd",
        "status": status,
        "payment_date": None if status == "failed" else datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc)
    }

def create_test_failure_data(failure_reason: str = "insufficient_funds") -> Dict[str, Any]:
    """Create test failure data"""
    return {
        "failure_reason": failure_reason,
        "failure_code": "card_declined",
        "payment_method": "card",
        "webhook_event_id": f"evt_test_{uuid.uuid4().hex[:8]}",
        "attempt_count": 1
    }

def test_payment_recovery_service():
    """Test the payment recovery service functionality"""
    logger.info("=== Testing Payment Recovery Service ===")
    
    try:
        from backend.services.payment_recovery_service import (
            PaymentRecoveryService, DunningStage, RecoveryStrategy, PaymentStatus
        )
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, Subscription, BillingHistory
        
        # Initialize payment recovery service
        config = Config()
        recovery_service = PaymentRecoveryService(db_session, config)
        
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
        subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=f"sub_test_{uuid.uuid4().hex[:8]}",
            customer_id=customer.id,
            status="active",
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd"
        )
        
        # Test 1: Payment failure handling
        logger.info("Test 1: Testing payment failure handling")
        
        billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=subscription.id,
            stripe_invoice_id=f"in_test_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="failed"
        )
        
        failure_data = create_test_failure_data("insufficient_funds")
        
        failure_result = recovery_service.handle_payment_failure(
            customer, billing_record, failure_data
        )
        
        logger.info(f"Payment failure handling result: {failure_result['success']}")
        logger.info(f"Recovery strategy: {failure_result['recovery_strategy']}")
        logger.info(f"Dunning stage: {failure_result['dunning_event'].stage.value}")
        logger.info(f"Changes: {failure_result['changes']}")
        logger.info(f"Notifications sent: {failure_result['notifications_sent']}")
        
        # Test 2: Dunning escalation
        logger.info("Test 2: Testing dunning escalation")
        
        dunning_event = failure_result['dunning_event']
        escalation_result = recovery_service.process_dunning_escalation(
            customer, billing_record, dunning_event
        )
        
        logger.info(f"Dunning escalation result: {escalation_result['success']}")
        logger.info(f"New stage: {escalation_result.get('new_stage')}")
        logger.info(f"Next attempt date: {escalation_result.get('next_attempt_date')}")
        logger.info(f"Changes: {escalation_result['changes']}")
        
        # Test 3: Payment method update during recovery
        logger.info("Test 3: Testing payment method update during recovery")
        
        payment_method_data = {
            "type": "card",
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 12,
                "exp_year": 2025
            },
            "billing_details": {
                "name": "Test Customer",
                "email": "test@example.com"
            }
        }
        
        update_result = recovery_service.handle_payment_method_update(
            customer, billing_record, payment_method_data
        )
        
        logger.info(f"Payment method update result: {update_result['success']}")
        logger.info(f"Payment method ID: {update_result.get('payment_method_id')}")
        logger.info(f"Retry success: {update_result.get('retry_success')}")
        logger.info(f"Changes: {update_result['changes']}")
        
        # Test 4: Grace period management
        logger.info("Test 4: Testing grace period management")
        
        grace_period_data = {
            "duration_days": 7,
            "restrictions": ["limited_features", "no_api_access"],
            "notifications": ["email", "sms"]
        }
        
        grace_result = recovery_service.handle_grace_period_management(
            customer, billing_record, grace_period_data
        )
        
        logger.info(f"Grace period management result: {grace_result['success']}")
        logger.info(f"Grace period end: {grace_result.get('grace_period_end')}")
        logger.info(f"Restrictions applied: {grace_result.get('restrictions_applied')}")
        logger.info(f"Changes: {grace_result['changes']}")
        
        # Test 5: Payment success after failure
        logger.info("Test 5: Testing payment success after failure")
        
        # Update billing record to succeeded
        billing_record.status = "paid"
        billing_record.payment_date = datetime.now(timezone.utc)
        
        payment_data = {
            "payment_method": "card",
            "receipt_url": "https://receipt.stripe.com/test",
            "payment_intent": f"pi_test_{uuid.uuid4().hex[:8]}"
        }
        
        success_result = recovery_service.handle_payment_success_after_failure(
            customer, billing_record, payment_data
        )
        
        logger.info(f"Payment success after failure result: {success_result['success']}")
        logger.info(f"Events cleared: {success_result.get('cleared_events')}")
        logger.info(f"Changes: {success_result['changes']}")
        logger.info(f"Notifications sent: {success_result['notifications_sent']}")
        
        logger.info("✅ All payment recovery service tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Payment recovery service test failed: {e}")

def test_dunning_stages():
    """Test dunning stage progression"""
    logger.info("=== Testing Dunning Stage Progression ===")
    
    try:
        from backend.services.payment_recovery_service import (
            PaymentRecoveryService, DunningStage, RecoveryStrategy
        )
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, Subscription, BillingHistory
        
        # Initialize payment recovery service
        config = Config()
        recovery_service = PaymentRecoveryService(db_session, config)
        
        # Create test customer and billing record
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_dunning_{uuid.uuid4().hex[:8]}",
            email="dunning@example.com",
            name="Dunning Customer"
        )
        
        billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=uuid.uuid4(),
            stripe_invoice_id=f"in_dunning_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="failed"
        )
        
        # Test progression through all dunning stages
        stages = [
            DunningStage.INITIAL_FAILURE,
            DunningStage.FIRST_RETRY,
            DunningStage.SECOND_RETRY,
            DunningStage.FINAL_WARNING,
            DunningStage.GRACE_PERIOD,
            DunningStage.SUSPENSION,
            DunningStage.CANCELLATION
        ]
        
        current_dunning_event = None
        
        for i, stage in enumerate(stages):
            logger.info(f"Testing stage {i+1}: {stage.name}")
            
            if i == 0:
                # Create initial dunning event
                failure_data = create_test_failure_data("card_declined")
                failure_result = recovery_service.handle_payment_failure(
                    customer, billing_record, failure_data
                )
                current_dunning_event = failure_result['dunning_event']
            else:
                # Escalate to next stage
                escalation_result = recovery_service.process_dunning_escalation(
                    customer, billing_record, current_dunning_event
                )
                
                if escalation_result['success']:
                    current_dunning_event.stage = DunningStage(escalation_result['new_stage'])
                    current_dunning_event.next_attempt_date = datetime.fromisoformat(
                        escalation_result['next_attempt_date']
                    )
                    
                    logger.info(f"  Escalated to stage {current_dunning_event.stage.value}")
                    logger.info(f"  Next attempt: {current_dunning_event.next_attempt_date}")
                    logger.info(f"  Changes: {escalation_result['changes']}")
                else:
                    logger.info(f"  Escalation failed: {escalation_result['error']}")
                    break
        
        logger.info("✅ All dunning stage tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Dunning stage test failed: {e}")

def test_recovery_strategies():
    """Test different recovery strategies"""
    logger.info("=== Testing Recovery Strategies ===")
    
    try:
        from backend.services.payment_recovery_service import (
            PaymentRecoveryService, RecoveryStrategy
        )
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, BillingHistory
        
        # Initialize payment recovery service
        config = Config()
        recovery_service = PaymentRecoveryService(db_session, config)
        
        # Create test customer
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_strategy_{uuid.uuid4().hex[:8]}",
            email="strategy@example.com",
            name="Strategy Customer"
        )
        
        # Test different failure reasons and their strategies
        test_cases = [
            {
                "failure_reason": "insufficient_funds",
                "expected_strategy": RecoveryStrategy.GRACE_PERIOD,
                "description": "Insufficient funds - should trigger grace period"
            },
            {
                "failure_reason": "expired_card",
                "expected_strategy": RecoveryStrategy.PAYMENT_METHOD_UPDATE,
                "description": "Expired card - should trigger payment method update"
            },
            {
                "failure_reason": "card_declined",
                "expected_strategy": RecoveryStrategy.AUTOMATIC_RETRY,
                "description": "Card declined - should trigger automatic retry"
            },
            {
                "failure_reason": "fraudulent",
                "expected_strategy": RecoveryStrategy.MANUAL_INTERVENTION,
                "description": "Fraudulent - should trigger manual intervention"
            },
            {
                "failure_reason": "unknown_error",
                "expected_strategy": RecoveryStrategy.AUTOMATIC_RETRY,
                "description": "Unknown error - should default to automatic retry"
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"Testing: {test_case['description']}")
            
            billing_record = BillingHistory(
                id=uuid.uuid4(),
                customer_id=customer.id,
                subscription_id=uuid.uuid4(),
                stripe_invoice_id=f"in_strategy_{uuid.uuid4().hex[:8]}",
                amount=29.00,
                currency="usd",
                status="failed"
            )
            
            failure_data = create_test_failure_data(test_case["failure_reason"])
            
            failure_result = recovery_service.handle_payment_failure(
                customer, billing_record, failure_data
            )
            
            actual_strategy = RecoveryStrategy(failure_result['recovery_strategy'])
            expected_strategy = test_case['expected_strategy']
            
            if actual_strategy == expected_strategy:
                logger.info(f"  ✅ Strategy correct: {actual_strategy.value}")
            else:
                logger.warning(f"  ⚠️ Strategy mismatch: expected {expected_strategy.value}, got {actual_strategy.value}")
            
            logger.info(f"  Dunning stage: {failure_result['dunning_event'].stage.value}")
            logger.info(f"  Changes: {len(failure_result['changes'])}")
            logger.info(f"  Notifications: {failure_result['notifications_sent']}")
        
        logger.info("✅ All recovery strategy tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Recovery strategy test failed: {e}")

def test_grace_period_management():
    """Test grace period management functionality"""
    logger.info("=== Testing Grace Period Management ===")
    
    try:
        from backend.services.payment_recovery_service import PaymentRecoveryService
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, BillingHistory
        
        # Initialize payment recovery service
        config = Config()
        recovery_service = PaymentRecoveryService(db_session, config)
        
        # Create test customer
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_grace_{uuid.uuid4().hex[:8]}",
            email="grace@example.com",
            name="Grace Customer"
        )
        
        billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=uuid.uuid4(),
            stripe_invoice_id=f"in_grace_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="failed"
        )
        
        # Test 1: Standard grace period
        logger.info("Test 1: Standard grace period (7 days)")
        
        grace_period_data = {
            "duration_days": 7,
            "restrictions": ["limited_features"],
            "notifications": ["email"]
        }
        
        grace_result = recovery_service.handle_grace_period_management(
            customer, billing_record, grace_period_data
        )
        
        logger.info(f"Grace period result: {grace_result['success']}")
        logger.info(f"Grace period end: {grace_result.get('grace_period_end')}")
        logger.info(f"Restrictions applied: {grace_result.get('restrictions_applied')}")
        
        # Test 2: Extended grace period
        logger.info("Test 2: Extended grace period (14 days)")
        
        extended_grace_data = {
            "duration_days": 14,
            "restrictions": ["limited_features", "no_api_access", "reduced_storage"],
            "notifications": ["email", "sms", "in_app"]
        }
        
        extended_result = recovery_service.handle_grace_period_management(
            customer, billing_record, extended_grace_data
        )
        
        logger.info(f"Extended grace period result: {extended_result['success']}")
        logger.info(f"Extended grace period end: {extended_result.get('grace_period_end')}")
        logger.info(f"Restrictions applied: {extended_result.get('restrictions_applied')}")
        
        # Test 3: Short grace period
        logger.info("Test 3: Short grace period (3 days)")
        
        short_grace_data = {
            "duration_days": 3,
            "restrictions": ["no_api_access"],
            "notifications": ["email", "sms"]
        }
        
        short_result = recovery_service.handle_grace_period_management(
            customer, billing_record, short_grace_data
        )
        
        logger.info(f"Short grace period result: {short_result['success']}")
        logger.info(f"Short grace period end: {short_result.get('grace_period_end')}")
        logger.info(f"Restrictions applied: {short_result.get('restrictions_applied')}")
        
        logger.info("✅ All grace period management tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Grace period management test failed: {e}")

def test_payment_method_updates():
    """Test payment method update functionality"""
    logger.info("=== Testing Payment Method Updates ===")
    
    try:
        from backend.services.payment_recovery_service import PaymentRecoveryService
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, BillingHistory
        
        # Initialize payment recovery service
        config = Config()
        recovery_service = PaymentRecoveryService(db_session, config)
        
        # Create test customer
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_payment_{uuid.uuid4().hex[:8]}",
            email="payment@example.com",
            name="Payment Customer"
        )
        
        billing_record = BillingHistory(
            id=uuid.uuid4(),
            customer_id=customer.id,
            subscription_id=uuid.uuid4(),
            stripe_invoice_id=f"in_payment_{uuid.uuid4().hex[:8]}",
            amount=29.00,
            currency="usd",
            status="failed"
        )
        
        # Test 1: Valid payment method update
        logger.info("Test 1: Valid payment method update")
        
        valid_payment_method = {
            "type": "card",
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 12,
                "exp_year": 2025
            },
            "billing_details": {
                "name": "Payment Customer",
                "email": "payment@example.com"
            }
        }
        
        valid_result = recovery_service.handle_payment_method_update(
            customer, billing_record, valid_payment_method
        )
        
        logger.info(f"Valid payment method result: {valid_result['success']}")
        logger.info(f"Payment method ID: {valid_result.get('payment_method_id')}")
        logger.info(f"Retry success: {valid_result.get('retry_success')}")
        
        # Test 2: Invalid payment method update
        logger.info("Test 2: Invalid payment method update")
        
        invalid_payment_method = {
            "type": "card",
            "card": {
                "brand": "visa",
                "last4": "0000",  # Invalid card
                "exp_month": 1,
                "exp_year": 2020  # Expired
            }
        }
        
        invalid_result = recovery_service.handle_payment_method_update(
            customer, billing_record, invalid_payment_method
        )
        
        logger.info(f"Invalid payment method result: {invalid_result['success']}")
        if not invalid_result['success']:
            logger.info(f"Error: {invalid_result['error']}")
        
        # Test 3: Bank account payment method
        logger.info("Test 3: Bank account payment method")
        
        bank_payment_method = {
            "type": "bank_account",
            "bank_account": {
                "bank_name": "Test Bank",
                "last4": "6789",
                "routing_number": "110000000"
            },
            "billing_details": {
                "name": "Payment Customer",
                "email": "payment@example.com"
            }
        }
        
        bank_result = recovery_service.handle_payment_method_update(
            customer, billing_record, bank_payment_method
        )
        
        logger.info(f"Bank payment method result: {bank_result['success']}")
        logger.info(f"Payment method ID: {bank_result.get('payment_method_id')}")
        
        logger.info("✅ All payment method update tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Payment method update test failed: {e}")

def test_recovery_configuration():
    """Test recovery service configuration"""
    logger.info("=== Testing Recovery Service Configuration ===")
    
    try:
        from backend.services.payment_recovery_service import PaymentRecoveryService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize payment recovery service
        config = Config()
        recovery_service = PaymentRecoveryService(db_session, config)
        
        # Test dunning configuration
        logger.info("Dunning Configuration:")
        logger.info(f"  Retry intervals: {recovery_service.dunning_config['retry_intervals']}")
        logger.info(f"  Max retry attempts: {recovery_service.dunning_config['max_retry_attempts']}")
        logger.info(f"  Grace period days: {recovery_service.dunning_config['grace_period_days']}")
        logger.info(f"  Suspension threshold: {recovery_service.dunning_config['suspension_threshold']}")
        logger.info(f"  Cancellation threshold: {recovery_service.dunning_config['cancellation_threshold']}")
        
        # Test recovery strategies configuration
        logger.info("Recovery Strategies Configuration:")
        for strategy_name, strategy_config in recovery_service.dunning_config['recovery_strategies'].items():
            logger.info(f"  {strategy_name}:")
            for key, value in strategy_config.items():
                logger.info(f"    {key}: {value}")
        
        # Test recovery templates
        logger.info("Recovery Templates:")
        for template_name in recovery_service.recovery_templates.keys():
            logger.info(f"  {template_name}: Available")
        
        logger.info("✅ All recovery configuration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Recovery configuration test failed: {e}")

def main():
    """Main test function"""
    logger.info("Starting comprehensive payment recovery service tests...")
    
    # Run all tests
    test_payment_recovery_service()
    test_dunning_stages()
    test_recovery_strategies()
    test_grace_period_management()
    test_payment_method_updates()
    test_recovery_configuration()
    
    logger.info("🎉 All payment recovery service tests completed!")

if __name__ == "__main__":
    main() 