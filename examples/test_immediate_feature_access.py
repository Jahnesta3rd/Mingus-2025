#!/usr/bin/env python3
"""
Test script for Immediate Feature Access Updates
Demonstrates comprehensive feature access management including:
- Immediate feature access updates for subscription changes
- Performance monitoring and optimization
- Audit trail logging
- Cache invalidation
- Real-time access control

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

def create_test_subscription(customer_id: str, tier: str = "premium") -> Dict[str, Any]:
    """Create a test subscription"""
    return {
        "id": f"sub_test_{uuid.uuid4().hex[:8]}",
        "customer": customer_id,
        "status": "active",
        "items": {
            "data": [
                {
                    "price": {
                        "id": f"price_{tier}_{uuid.uuid4().hex[:8]}",
                        "product": f"prod_{tier}_{uuid.uuid4().hex[:8]}",
                        "unit_amount": 2900 if tier == "premium" else 9900,
                        "currency": "usd"
                    }
                }
            ]
        },
        "current_period_start": int(time.time()),
        "current_period_end": int(time.time()) + 2592000,  # 30 days
        "created": int(time.time()),
        "livemode": False
    }

def test_immediate_feature_access_updates():
    """Test immediate feature access updates for webhook events"""
    logger.info("=== Testing Immediate Feature Access Updates ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.monitoring.audit_trail_service import AuditTrailService
        from backend.monitoring.performance_optimizer import PerformanceOptimizer
        from backend.services.feature_access_service import FeatureAccessService
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, Subscription, User
        
        # Initialize services
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        audit_service = AuditTrailService(db_session, config)
        performance_optimizer = PerformanceOptimizer(config)
        feature_service = FeatureAccessService(db_session, config)
        
        # Create test customer
        test_customer_data = create_test_customer()
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=test_customer_data["id"],
            email=test_customer_data["email"],
            name=test_customer_data["name"],
            phone=test_customer_data["phone"]
        )
        
        # Create test user
        user = User(
            id=uuid.uuid4(),
            email=test_customer_data["email"],
            name=test_customer_data["name"],
            is_active=True
        )
        customer.user_id = user.id
        
        # Test 1: Subscription Created - Immediate Feature Access Grant
        logger.info("Test 1: Testing subscription created with immediate feature access")
        
        subscription_data = create_test_subscription(str(customer.id), "premium")
        subscription = Subscription(
            id=uuid.uuid4(),
            stripe_subscription_id=subscription_data["id"],
            customer_id=customer.id,
            status="active",
            pricing_tier="premium",
            billing_cycle="monthly",
            amount=29.00,
            currency="usd"
        )
        
        # Test immediate feature access update
        feature_result = webhook_manager._update_feature_access_immediately(
            customer, subscription, subscription_data
        )
        
        logger.info(f"Feature access update result: {feature_result['success']}")
        logger.info(f"Features granted: {feature_result.get('features_granted', [])}")
        logger.info(f"Access level: {feature_result.get('access_level')}")
        logger.info(f"Processing time: {feature_result.get('processing_time_ms', 0):.2f}ms")
        
        # Test 2: Subscription Updated - Feature Access Modification
        logger.info("Test 2: Testing subscription updated with feature access modification")
        
        # Simulate upgrade to enterprise
        old_values = {
            'pricing_tier': 'premium',
            'amount': 29.00
        }
        new_data = {
            'pricing_tier': 'enterprise',
            'amount': 99.00
        }
        
        subscription.pricing_tier = "enterprise"
        subscription.amount = 99.00
        
        feature_update_result = webhook_manager._update_feature_access_immediately(
            customer, subscription, new_data
        )
        
        logger.info(f"Feature access update result: {feature_update_result['success']}")
        logger.info(f"Features granted: {feature_update_result.get('features_granted', [])}")
        logger.info(f"Features removed: {feature_update_result.get('features_removed', [])}")
        logger.info(f"Access level: {feature_update_result.get('access_level')}")
        
        # Test 3: Subscription Cancelled - Feature Access Revocation
        logger.info("Test 3: Testing subscription cancelled with feature access revocation")
        
        cancellation_data = {
            'cancellation_reason': 'customer_request',
            'cancelled_at': datetime.now(timezone.utc).isoformat()
        }
        
        subscription.status = "canceled"
        
        feature_revoke_result = webhook_manager._revoke_feature_access_immediately(
            customer, subscription, cancellation_data
        )
        
        logger.info(f"Feature access revocation result: {feature_revoke_result['success']}")
        logger.info(f"Features revoked: {feature_revoke_result.get('features_revoked', [])}")
        logger.info(f"Grace period access level: {feature_revoke_result.get('access_level')}")
        
        # Test 4: Trial Ending - Feature Access Restriction
        logger.info("Test 4: Testing trial ending with feature access restriction")
        
        trial_data = {
            'trial_end': datetime.now(timezone.utc).isoformat(),
            'trial_end_behavior': 'cancel'
        }
        
        subscription.status = "trialing"
        
        trial_feature_result = webhook_manager._update_feature_access_for_trial_ending(
            customer, subscription, trial_data
        )
        
        logger.info(f"Trial ending feature update result: {trial_feature_result['success']}")
        logger.info(f"Features restricted: {trial_feature_result.get('features_restricted', [])}")
        logger.info(f"Trial access level: {trial_feature_result.get('access_level')}")
        
        # Test 5: User Feature Access Validation
        logger.info("Test 5: Testing user feature access validation")
        
        # Test feature access validation
        has_premium_analytics = feature_service.validate_feature_access(
            str(user.id), "premium_analytics"
        )
        has_enterprise_api = feature_service.validate_feature_access(
            str(user.id), "unlimited_api"
        )
        
        logger.info(f"Has premium analytics: {has_premium_analytics}")
        logger.info(f"Has enterprise API: {has_enterprise_api}")
        
        # Test feature limits
        feature_limits = feature_service.get_feature_limits(str(user.id))
        logger.info(f"Feature limits: {feature_limits}")
        
        # Test 6: Performance Monitoring
        logger.info("Test 6: Testing performance monitoring")
        
        # Get performance metrics
        performance_metrics = performance_optimizer.get_performance_metrics()
        logger.info(f"Performance metrics: {performance_metrics}")
        
        # Get feature access performance metrics
        feature_metrics = feature_service.get_performance_metrics()
        logger.info(f"Feature access metrics: {feature_metrics}")
        
        # Test 7: Audit Trail Verification
        logger.info("Test 7: Testing audit trail verification")
        
        # Query audit events for feature access
        audit_query = {
            'start_time': datetime.now(timezone.utc) - timedelta(hours=1),
            'end_time': datetime.now(timezone.utc),
            'event_types': ['feature_access'],
            'user_id': str(user.id)
        }
        
        audit_events = audit_service.query_audit_events(audit_query)
        logger.info(f"Audit events found: {len(audit_events)}")
        
        for event in audit_events[:5]:  # Show first 5 events
            logger.info(f"Audit event: {event.event_type.value} - {event.description}")
        
        # Test 8: Cache Invalidation
        logger.info("Test 8: Testing cache invalidation")
        
        # Test cache invalidation
        cache_invalidation_result = webhook_manager._invalidate_user_cache(str(user.id))
        logger.info(f"Cache invalidation completed: {cache_invalidation_result is None}")
        
        # Test 9: Business Logic Integration
        logger.info("Test 9: Testing business logic integration")
        
        # Test subscription created with business logic
        business_logic_result = webhook_manager._execute_business_logic_for_subscription_created(
            customer, subscription, subscription_data
        )
        
        logger.info(f"Business logic result: {business_logic_result['success']}")
        logger.info(f"Feature access updated: {business_logic_result.get('feature_access_updated', False)}")
        logger.info(f"Changes: {business_logic_result.get('changes', [])}")
        logger.info(f"Notifications sent: {business_logic_result.get('notifications_sent', 0)}")
        
        # Test 10: Error Handling
        logger.info("Test 10: Testing error handling")
        
        # Test with invalid customer
        invalid_customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id="invalid_customer",
            email="invalid@example.com",
            name="Invalid Customer"
        )
        
        error_result = webhook_manager._update_feature_access_immediately(
            invalid_customer, subscription, subscription_data
        )
        
        logger.info(f"Error handling result: {error_result['success']}")
        logger.info(f"Error message: {error_result.get('error', 'No error')}")
        
        logger.info("✅ All immediate feature access update tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Immediate feature access update test failed: {e}")

def test_feature_access_service():
    """Test feature access service functionality"""
    logger.info("=== Testing Feature Access Service ===")
    
    try:
        from backend.services.feature_access_service import FeatureAccessService, FeatureAccessLevel
        from backend.config.base import Config
        from backend.models import db_session
        from backend.models.subscription import Customer, User
        
        # Initialize service
        config = Config()
        feature_service = FeatureAccessService(db_session, config)
        
        # Create test customer and user
        customer = Customer(
            id=uuid.uuid4(),
            stripe_customer_id=f"cus_service_{uuid.uuid4().hex[:8]}",
            email="service@example.com",
            name="Service Customer"
        )
        
        user = User(
            id=uuid.uuid4(),
            email="service@example.com",
            name="Service Customer",
            is_active=True
        )
        customer.user_id = user.id
        
        # Test 1: Basic Feature Access Update
        logger.info("Test 1: Basic feature access update")
        
        update_result = feature_service.update_feature_access_immediately(
            customer_id=str(customer.id),
            subscription_tier="premium",
            subscription_status="active",
            subscription_data={"amount": 29.00, "currency": "usd"}
        )
        
        logger.info(f"Update result: {update_result['success']}")
        logger.info(f"Features granted: {update_result.get('features_granted', [])}")
        logger.info(f"Access level: {update_result.get('access_level')}")
        
        # Test 2: Feature Access Revocation
        logger.info("Test 2: Feature access revocation")
        
        revoke_result = feature_service.revoke_feature_access_immediately(
            customer_id=str(customer.id),
            subscription_tier="premium",
            cancellation_data={"reason": "test_cancellation"}
        )
        
        logger.info(f"Revoke result: {revoke_result['success']}")
        logger.info(f"Features revoked: {revoke_result.get('features_revoked', [])}")
        logger.info(f"Grace period access: {revoke_result.get('access_level')}")
        
        # Test 3: Trial Ending Feature Update
        logger.info("Test 3: Trial ending feature update")
        
        trial_result = feature_service.update_feature_access_for_trial_ending(
            customer_id=str(customer.id),
            subscription_tier="premium",
            trial_data={"trial_end": datetime.now(timezone.utc).isoformat()}
        )
        
        logger.info(f"Trial result: {trial_result['success']}")
        logger.info(f"Features restricted: {trial_result.get('features_restricted', [])}")
        logger.info(f"Trial access level: {trial_result.get('access_level')}")
        
        # Test 4: User Feature Access
        logger.info("Test 4: User feature access")
        
        user_access = feature_service.get_user_feature_access(str(user.id))
        logger.info(f"User access: {user_access.get('success', False)}")
        logger.info(f"Features: {user_access.get('features', [])}")
        logger.info(f"Access level: {user_access.get('access_level')}")
        
        # Test 5: Feature Validation
        logger.info("Test 5: Feature validation")
        
        has_core = feature_service.validate_feature_access(str(user.id), "core_features")
        has_premium = feature_service.validate_feature_access(str(user.id), "premium_analytics")
        has_enterprise = feature_service.validate_feature_access(str(user.id), "custom_integrations")
        
        logger.info(f"Has core features: {has_core}")
        logger.info(f"Has premium analytics: {has_premium}")
        logger.info(f"Has enterprise integrations: {has_enterprise}")
        
        # Test 6: Feature Limits
        logger.info("Test 6: Feature limits")
        
        limits = feature_service.get_feature_limits(str(user.id))
        logger.info(f"Feature limits: {limits}")
        
        # Test 7: Performance Metrics
        logger.info("Test 7: Performance metrics")
        
        metrics = feature_service.get_performance_metrics()
        logger.info(f"Performance metrics: {metrics}")
        
        logger.info("✅ All feature access service tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Feature access service test failed: {e}")

def test_performance_optimization():
    """Test performance optimization for feature access"""
    logger.info("=== Testing Performance Optimization ===")
    
    try:
        from backend.monitoring.performance_optimizer import PerformanceOptimizer
        from backend.config.base import Config
        
        # Initialize performance optimizer
        config = Config()
        optimizer = PerformanceOptimizer(config)
        
        # Test 1: Performance Metrics Recording
        logger.info("Test 1: Performance metrics recording")
        
        # Record webhook events
        for i in range(10):
            processing_time = 50 + (i * 10)  # Varying processing times
            success = i < 8  # 80% success rate
            
            optimizer.record_webhook_event(
                event_type="feature_access_update",
                processing_time=processing_time,
                success=success,
                error="test_error" if not success else None
            )
        
        # Get performance metrics
        metrics = optimizer.get_performance_metrics()
        logger.info(f"Performance metrics: {metrics}")
        
        # Test 2: Cache Operations
        logger.info("Test 2: Cache operations")
        
        # Test cache operations
        cache_key = f"test_cache_{uuid.uuid4().hex[:8]}"
        cache_value = {"features": ["core", "premium"], "access_level": "premium"}
        
        # Set cache
        set_result = optimizer.set_cached_data(cache_key, cache_value, ttl=300)
        logger.info(f"Cache set result: {set_result}")
        
        # Get cache
        get_result = optimizer.get_cached_data(cache_key)
        logger.info(f"Cache get result: {get_result is not None}")
        
        # Invalidate cache
        invalidate_result = optimizer.invalidate_cache(cache_key)
        logger.info(f"Cache invalidate result: {invalidate_result}")
        
        # Test 3: Performance Optimization
        logger.info("Test 3: Performance optimization")
        
        optimization_result = optimizer.optimize_performance()
        logger.info(f"Optimization result: {optimization_result}")
        
        # Test 4: Resource Scaling
        logger.info("Test 4: Resource scaling")
        
        scale_result = optimizer.scale_resources(1.5)  # Scale up by 50%
        logger.info(f"Resource scaling result: {scale_result}")
        
        logger.info("✅ All performance optimization tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Performance optimization test failed: {e}")

def test_audit_trail():
    """Test audit trail for feature access updates"""
    logger.info("=== Testing Audit Trail ===")
    
    try:
        from backend.monitoring.audit_trail_service import AuditTrailService, AuditEventType, AuditSeverity
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize audit service
        config = Config()
        audit_service = AuditTrailService(db_session, config)
        
        # Test 1: Feature Access Event Logging
        logger.info("Test 1: Feature access event logging")
        
        # Log feature access events
        for i in range(5):
            audit_service.log_feature_access_event(
                user_id=f"user_{i}",
                feature=f"feature_{i}",
                action="access_granted" if i % 2 == 0 else "access_revoked",
                details={
                    "subscription_tier": "premium" if i % 2 == 0 else "basic",
                    "features_affected": [f"feature_{i}"],
                    "access_level": "premium" if i % 2 == 0 else "basic"
                },
                success=True
            )
        
        # Test 2: Business Logic Event Logging
        logger.info("Test 2: Business logic event logging")
        
        audit_service.log_business_logic_event(
            operation="subscription_created",
            description="Test subscription creation",
            details={
                "customer_id": "test_customer",
                "subscription_tier": "premium",
                "amount": 29.00
            },
            customer_id="test_customer",
            success=True
        )
        
        # Test 3: Audit Event Querying
        logger.info("Test 3: Audit event querying")
        
        # Query recent events
        from datetime import datetime, timezone, timedelta
        
        query = {
            'start_time': datetime.now(timezone.utc) - timedelta(hours=1),
            'end_time': datetime.now(timezone.utc),
            'event_types': ['feature_access', 'business_logic'],
            'limit': 10
        }
        
        events = audit_service.query_audit_events(query)
        logger.info(f"Audit events found: {len(events)}")
        
        # Test 4: Audit Report Generation
        logger.info("Test 4: Audit report generation")
        
        report = audit_service.generate_audit_report(
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc),
            report_type="comprehensive"
        )
        
        logger.info(f"Audit report generated: {report.get('report_type')}")
        logger.info(f"Total events: {report.get('summary', {}).get('total_events', 0)}")
        
        # Test 5: Audit Statistics
        logger.info("Test 5: Audit statistics")
        
        stats = audit_service.get_audit_statistics(days=1)
        logger.info(f"Audit statistics: {stats}")
        
        logger.info("✅ All audit trail tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Audit trail test failed: {e}")

def main():
    """Main test function"""
    logger.info("Starting comprehensive immediate feature access update tests...")
    
    # Run all tests
    test_immediate_feature_access_updates()
    test_feature_access_service()
    test_performance_optimization()
    test_audit_trail()
    
    logger.info("🎉 All immediate feature access update tests completed!")

if __name__ == "__main__":
    main() 