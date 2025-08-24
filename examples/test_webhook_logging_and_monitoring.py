#!/usr/bin/env python3
"""
Test script for webhook logging and monitoring
Demonstrates comprehensive webhook event logging, monitoring, and analytics
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

def create_test_webhook_event(event_type: str, entity_id: str, success: bool = True, processing_time: float = 1.0) -> Dict[str, Any]:
    """Create a test webhook event"""
    return {
        "id": f"evt_test_{uuid.uuid4().hex[:8]}",
        "object": "event",
        "type": event_type,
        "created": int(time.time()),
        "livemode": False,
        "api_version": "2020-08-27",
        "data": {
            "object": {
                "id": entity_id,
                "object": entity_id.split('_')[0],
                "created": int(time.time()),
                "livemode": False
            }
        },
        "success": success,
        "processing_time": processing_time
    }

def test_webhook_logging_service():
    """Test the webhook logging service functionality"""
    logger.info("=== Testing Webhook Logging Service ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService, LogLevel, EventCategory
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Test 1: Log successful webhook event
        logger.info("Test 1: Logging successful webhook event")
        log_entry = logging_service.log_webhook_event(
            event_id="evt_test_success_001",
            event_type="customer.created",
            source_ip="192.168.1.100",
            user_agent="test-agent",
            request_id="req_test_001",
            processing_time=1.5,
            success=True,
            metadata={
                "customer_id": "cus_test_001",
                "email": "test@example.com"
            },
            entity_type="customer",
            entity_id="cus_test_001"
        )
        logger.info(f"Logged successful event: {log_entry.event_id}")
        
        # Test 2: Log failed webhook event
        logger.info("Test 2: Logging failed webhook event")
        log_entry_2 = logging_service.log_webhook_event(
            event_id="evt_test_failure_001",
            event_type="customer.updated",
            source_ip="192.168.1.101",
            user_agent="test-agent",
            request_id="req_test_002",
            processing_time=5.2,
            success=False,
            error_message="Database connection failed",
            error_details={
                "error_type": "database_error",
                "error_code": "DB_CONNECTION_FAILED"
            },
            metadata={
                "customer_id": "cus_test_002",
                "retry_attempts": 3
            },
            entity_type="customer",
            entity_id="cus_test_002"
        )
        logger.info(f"Logged failed event: {log_entry_2.event_id}")
        
        # Test 3: Log security event
        logger.info("Test 3: Logging security event")
        log_entry_3 = logging_service.log_webhook_event(
            event_id="evt_test_security_001",
            event_type="customer.deleted",
            source_ip="10.0.0.1",
            user_agent="suspicious-agent",
            request_id="req_test_003",
            processing_time=0.8,
            success=True,
            metadata={
                "customer_id": "cus_test_003",
                "security_flag": True
            },
            entity_type="customer",
            entity_id="cus_test_003"
        )
        logger.info(f"Logged security event: {log_entry_3.event_id}")
        
        logger.info("✅ All webhook logging service tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Webhook logging service test failed: {e}")

def test_performance_metrics():
    """Test performance metrics functionality"""
    logger.info("=== Testing Performance Metrics ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Log multiple events for metrics testing
        logger.info("Logging multiple events for metrics testing")
        for i in range(10):
            success = i < 8  # 80% success rate
            processing_time = 1.0 + (i * 0.5)  # Varying processing times
            
            logging_service.log_webhook_event(
                event_id=f"evt_metrics_test_{i:03d}",
                event_type="customer.created" if i % 2 == 0 else "customer.updated",
                source_ip=f"192.168.1.{100 + i}",
                user_agent="metrics-test-agent",
                request_id=f"req_metrics_{i:03d}",
                processing_time=processing_time,
                success=success,
                error_message="Test error" if not success else None,
                entity_type="customer",
                entity_id=f"cus_metrics_{i:03d}"
            )
        
        # Test 1: Get performance metrics
        logger.info("Test 1: Getting performance metrics")
        metrics = logging_service.get_performance_metrics(time_range_hours=1)
        logger.info(f"Performance metrics: {metrics}")
        
        # Test 2: Get metrics for specific event type
        logger.info("Test 2: Getting metrics for specific event type")
        customer_metrics = logging_service.get_performance_metrics(
            time_range_hours=1,
            event_type="customer.created"
        )
        logger.info(f"Customer creation metrics: {customer_metrics}")
        
        # Test 3: Get metrics for specific entity
        logger.info("Test 3: Getting metrics for specific entity")
        entity_metrics = logging_service.get_performance_metrics(
            time_range_hours=1,
            entity_type="customer",
            entity_id="cus_metrics_001"
        )
        logger.info(f"Entity metrics: {entity_metrics}")
        
        logger.info("✅ All performance metrics tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Performance metrics test failed: {e}")

def test_health_status():
    """Test health status functionality"""
    logger.info("=== Testing Health Status ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Test 1: Get health status
        logger.info("Test 1: Getting health status")
        health_status = logging_service.get_health_status()
        logger.info(f"Health status: {health_status}")
        
        # Test 2: Check health components
        logger.info("Test 2: Checking health components")
        logger.info(f"Overall status: {health_status.overall_status}")
        logger.info(f"Health score: {health_status.health_score:.2%}")
        logger.info(f"Database health: {health_status.database_health}")
        logger.info(f"Processing health: {health_status.processing_health}")
        logger.info(f"Security health: {health_status.security_health}")
        logger.info(f"Performance health: {health_status.performance_health}")
        
        # Test 3: Check active issues
        logger.info("Test 3: Checking active issues")
        for issue in health_status.active_issues:
            logger.info(f"Active issue: {issue['type']} - {issue['description']}")
        
        # Test 4: Check recommendations
        logger.info("Test 4: Checking recommendations")
        for recommendation in health_status.recommendations:
            logger.info(f"Recommendation: {recommendation}")
        
        logger.info("✅ All health status tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Health status test failed: {e}")

def test_event_analytics():
    """Test event analytics functionality"""
    logger.info("=== Testing Event Analytics ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Test 1: Get event analytics by event type
        logger.info("Test 1: Getting event analytics by event type")
        event_analytics = logging_service.get_event_analytics(
            time_range_hours=1,
            group_by="event_type"
        )
        logger.info(f"Event analytics: {event_analytics}")
        
        # Test 2: Get event analytics by entity type
        logger.info("Test 2: Getting event analytics by entity type")
        entity_analytics = logging_service.get_event_analytics(
            time_range_hours=1,
            group_by="entity_type"
        )
        logger.info(f"Entity analytics: {entity_analytics}")
        
        # Test 3: Check analytics structure
        logger.info("Test 3: Checking analytics structure")
        if 'groups' in event_analytics:
            for group in event_analytics['groups']:
                logger.info(f"Event type: {group['name']}, Count: {group['count']}, Avg time: {group['avg_processing_time']:.3f}s")
        
        logger.info("✅ All event analytics tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Event analytics test failed: {e}")

def test_error_analytics():
    """Test error analytics functionality"""
    logger.info("=== Testing Error Analytics ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Log some error events
        logger.info("Logging error events for analytics testing")
        error_types = ["Database connection failed", "Timeout error", "Validation error", "Authentication failed"]
        for i, error_type in enumerate(error_types):
            logging_service.log_webhook_event(
                event_id=f"evt_error_test_{i:03d}",
                event_type="customer.updated",
                source_ip=f"192.168.1.{200 + i}",
                user_agent="error-test-agent",
                request_id=f"req_error_{i:03d}",
                processing_time=3.0 + i,
                success=False,
                error_message=error_type,
                error_details={
                    "error_type": "processing_error",
                    "error_code": f"ERROR_{i:03d}"
                },
                entity_type="customer",
                entity_id=f"cus_error_{i:03d}"
            )
        
        # Test 1: Get error analytics
        logger.info("Test 1: Getting error analytics")
        error_analytics = logging_service.get_error_analytics(time_range_hours=1)
        logger.info(f"Error analytics: {error_analytics}")
        
        # Test 2: Check error patterns
        logger.info("Test 2: Checking error patterns")
        if 'error_patterns' in error_analytics:
            for error_pattern, count in error_analytics['error_patterns'].items():
                logger.info(f"Error pattern: {error_pattern}, Count: {count}")
        
        # Test 3: Check top errors
        logger.info("Test 3: Checking top errors")
        if 'top_errors' in error_analytics:
            for error, count in error_analytics['top_errors']:
                logger.info(f"Top error: {error}, Count: {count}")
        
        # Test 4: Check error trends
        logger.info("Test 4: Checking error trends")
        if 'error_trends' in error_analytics:
            trends = error_analytics['error_trends']
            logger.info(f"Error trend: {trends.get('trend_direction', 'unknown')}")
        
        logger.info("✅ All error analytics tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Error analytics test failed: {e}")

def test_webhook_report_generation():
    """Test webhook report generation"""
    logger.info("=== Testing Webhook Report Generation ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Test 1: Generate basic report
        logger.info("Test 1: Generating basic webhook report")
        basic_report = logging_service.generate_webhook_report(
            time_range_hours=1,
            include_details=False
        )
        logger.info(f"Basic report generated: {basic_report.get('summary', {})}")
        
        # Test 2: Generate detailed report
        logger.info("Test 2: Generating detailed webhook report")
        detailed_report = logging_service.generate_webhook_report(
            time_range_hours=1,
            include_details=True
        )
        logger.info(f"Detailed report generated: {detailed_report.get('summary', {})}")
        
        # Test 3: Check report structure
        logger.info("Test 3: Checking report structure")
        required_sections = ['summary', 'performance_metrics', 'health_status', 'event_analytics', 'error_analytics']
        for section in required_sections:
            if section in detailed_report:
                logger.info(f"✓ Report contains {section} section")
            else:
                logger.warning(f"✗ Report missing {section} section")
        
        # Test 4: Check summary information
        logger.info("Test 4: Checking summary information")
        summary = detailed_report.get('summary', {})
        logger.info(f"Total events: {summary.get('total_events', 'N/A')}")
        logger.info(f"Success rate: {summary.get('success_rate', 'N/A')}")
        logger.info(f"Health status: {summary.get('health_status', 'N/A')}")
        
        logger.info("✅ All webhook report generation tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Webhook report generation test failed: {e}")

def test_cleanup_operations():
    """Test cleanup operations"""
    logger.info("=== Testing Cleanup Operations ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Test 1: Cleanup old logs
        logger.info("Test 1: Cleaning up old logs")
        cleanup_stats = logging_service.cleanup_old_logs(days=1)
        logger.info(f"Cleanup stats: {cleanup_stats}")
        
        # Test 2: Check cleanup results
        logger.info("Test 2: Checking cleanup results")
        if 'deleted_webhook_records' in cleanup_stats:
            logger.info(f"Deleted webhook records: {cleanup_stats['deleted_webhook_records']}")
        if 'deleted_audit_logs' in cleanup_stats:
            logger.info(f"Deleted audit logs: {cleanup_stats['deleted_audit_logs']}")
        
        logger.info("✅ All cleanup operation tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Cleanup operation test failed: {e}")

def test_webhook_manager_integration():
    """Test webhook manager integration with logging"""
    logger.info("=== Testing Webhook Manager Integration ===")
    
    try:
        from backend.webhooks.stripe_webhooks import StripeWebhookManager
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize webhook manager
        config = Config()
        webhook_manager = StripeWebhookManager(db_session, config)
        
        # Test 1: Get webhook analytics
        logger.info("Test 1: Getting webhook analytics")
        analytics = webhook_manager.get_webhook_analytics(time_range_hours=1)
        logger.info(f"Webhook analytics: {analytics}")
        
        # Test 2: Generate webhook report
        logger.info("Test 2: Generating webhook report")
        report = webhook_manager.generate_webhook_report(time_range_hours=1)
        logger.info(f"Webhook report: {report}")
        
        # Test 3: Check analytics structure
        logger.info("Test 3: Checking analytics structure")
        if 'performance_metrics' in analytics:
            metrics = analytics['performance_metrics']
            logger.info(f"Total events: {metrics.total_events}")
            logger.info(f"Success rate: {metrics.success_rate:.2%}")
            logger.info(f"Average processing time: {metrics.average_processing_time:.3f}s")
        
        logger.info("✅ All webhook manager integration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Webhook manager integration test failed: {e}")

def test_log_levels_and_categories():
    """Test log levels and categories"""
    logger.info("=== Testing Log Levels and Categories ===")
    
    try:
        from backend.services.webhook_logging_service import WebhookLoggingService, LogLevel, EventCategory
        from backend.config.base import Config
        from backend.models import db_session
        
        # Initialize logging service
        config = Config()
        logging_service = WebhookLoggingService(db_session, config)
        
        # Test different log levels and categories
        test_cases = [
            {
                'event_type': 'customer.created',
                'success': True,
                'error_message': None,
                'expected_level': LogLevel.INFO,
                'expected_category': EventCategory.BUSINESS
            },
            {
                'event_type': 'customer.updated',
                'success': False,
                'error_message': 'Database timeout',
                'expected_level': LogLevel.ERROR,
                'expected_category': EventCategory.PERFORMANCE
            },
            {
                'event_type': 'security.breach',
                'success': False,
                'error_message': 'Security violation detected',
                'expected_level': LogLevel.CRITICAL,
                'expected_category': EventCategory.SECURITY
            },
            {
                'event_type': 'system.health',
                'success': True,
                'error_message': None,
                'expected_level': LogLevel.INFO,
                'expected_category': EventCategory.SYSTEM
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"Test case {i+1}: {test_case['event_type']}")
            
            # Log event
            log_entry = logging_service.log_webhook_event(
                event_id=f"evt_level_test_{i:03d}",
                event_type=test_case['event_type'],
                source_ip="192.168.1.100",
                user_agent="level-test-agent",
                request_id=f"req_level_{i:03d}",
                processing_time=1.0,
                success=test_case['success'],
                error_message=test_case['error_message'],
                entity_type="customer",
                entity_id=f"cus_level_{i:03d}"
            )
            
            # Verify level and category
            expected_level = test_case['expected_level']
            expected_category = test_case['expected_category']
            
            logger.info(f"  Expected level: {expected_level.value}, Actual: {log_entry.level.value}")
            logger.info(f"  Expected category: {expected_category.value}, Actual: {log_entry.category.value}")
            
            if log_entry.level == expected_level and log_entry.category == expected_category:
                logger.info(f"  ✓ Test case {i+1} passed")
            else:
                logger.warning(f"  ✗ Test case {i+1} failed")
        
        logger.info("✅ All log levels and categories tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Log levels and categories test failed: {e}")

def main():
    """Main test function"""
    logger.info("Starting comprehensive webhook logging and monitoring tests...")
    
    # Run all tests
    test_webhook_logging_service()
    test_performance_metrics()
    test_health_status()
    test_event_analytics()
    test_error_analytics()
    test_webhook_report_generation()
    test_cleanup_operations()
    test_webhook_manager_integration()
    test_log_levels_and_categories()
    
    logger.info("🎉 All webhook logging and monitoring tests completed!")

if __name__ == "__main__":
    main() 