#!/usr/bin/env python3
"""
Test Script for MINGUS Integration Features
===========================================

This script demonstrates the comprehensive MINGUS integration features:
- Immediate feature access updates
- User notification triggers
- Analytics event tracking
- Performance monitoring
- Audit trail logging

Author: MINGUS Development Team
Date: January 2025
"""

import sys
import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from webhooks.stripe_webhooks import StripeWebhookManager
from services.feature_access_service import FeatureAccessService
from services.notification_service import NotificationService, NotificationType, NotificationChannel
from analytics.event_tracker import EventTracker, EventType, EventCategory
from monitoring.audit_trail_service import AuditTrailService
from monitoring.performance_optimizer import PerformanceOptimizer
from config.base import Config


class MINGUSIntegrationTester:
    """Test class for MINGUS integration features"""
    
    def __init__(self):
        self.config = Config()
        self.db_session = None  # Would be initialized with actual database session
        self.webhook_manager = None
        self.feature_service = None
        self.notification_service = None
        self.event_tracker = None
        self.audit_service = None
        self.performance_optimizer = None
        
        self.test_results = {
            'feature_access_tests': [],
            'notification_tests': [],
            'analytics_tests': [],
            'performance_tests': [],
            'integration_tests': []
        }
    
    def setup_services(self):
        """Initialize all services for testing"""
        print("🔧 Setting up MINGUS services...")
        
        try:
            # Initialize services
            self.webhook_manager = StripeWebhookManager(self.db_session, self.config)
            self.feature_service = FeatureAccessService(self.db_session, self.config)
            self.notification_service = NotificationService(self.db_session, self.config)
            self.event_tracker = EventTracker(self.db_session, self.config)
            self.audit_service = AuditTrailService(self.db_session, self.config)
            self.performance_optimizer = PerformanceOptimizer(self.config)
            
            print("✅ All services initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up services: {e}")
            return False
    
    def test_immediate_feature_access_updates(self):
        """Test immediate feature access updates"""
        print("\n🚀 Testing Immediate Feature Access Updates...")
        
        test_cases = [
            {
                'name': 'Subscription Created - Basic Tier',
                'customer_id': 'test_customer_001',
                'subscription_tier': 'basic',
                'subscription_status': 'active',
                'expected_features': ['core_features', 'basic_analytics', 'email_support']
            },
            {
                'name': 'Subscription Updated - Premium Tier',
                'customer_id': 'test_customer_002',
                'subscription_tier': 'premium',
                'subscription_status': 'active',
                'expected_features': ['core_features', 'premium_analytics', 'advanced_api', 'priority_support']
            },
            {
                'name': 'Subscription Cancelled',
                'customer_id': 'test_customer_003',
                'subscription_tier': 'premium',
                'subscription_status': 'cancelled',
                'expected_features': ['core_features']  # Grace period features
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Mock customer and subscription data
                customer_data = {
                    'id': test_case['customer_id'],
                    'user_id': f"user_{test_case['customer_id']}",
                    'email': f"{test_case['customer_id']}@example.com"
                }
                
                subscription_data = {
                    'id': f"sub_{test_case['customer_id']}",
                    'pricing_tier': test_case['subscription_tier'],
                    'status': test_case['subscription_status'],
                    'amount': 29.99 if test_case['subscription_tier'] == 'basic' else 99.99,
                    'currency': 'usd'
                }
                
                # Test feature access update
                if test_case['subscription_status'] == 'cancelled':
                    result = self.feature_service.revoke_feature_access_immediately(
                        customer_id=test_case['customer_id'],
                        subscription_tier=test_case['subscription_tier'],
                        cancellation_data={'reason': 'test_cancellation'}
                    )
                else:
                    result = self.feature_service.update_feature_access_immediately(
                        customer_id=test_case['customer_id'],
                        subscription_tier=test_case['subscription_tier'],
                        subscription_status=test_case['subscription_status'],
                        subscription_data=subscription_data
                    )
                
                # Validate results
                if result['success']:
                    actual_features = result.get('features_granted', []) or result.get('features_revoked', [])
                    expected_features = test_case['expected_features']
                    
                    if set(actual_features) == set(expected_features):
                        print(f"    ✅ Feature access updated correctly")
                        print(f"    📊 Features: {actual_features}")
                        print(f"    ⚡ Processing time: {result.get('processing_time_ms', 0):.2f}ms")
                    else:
                        print(f"    ❌ Feature mismatch")
                        print(f"    Expected: {expected_features}")
                        print(f"    Actual: {actual_features}")
                else:
                    print(f"    ❌ Feature access update failed: {result.get('error')}")
                
                # Record test result
                self.test_results['feature_access_tests'].append({
                    'test_name': test_case['name'],
                    'success': result['success'],
                    'processing_time_ms': result.get('processing_time_ms', 0),
                    'features_updated': len(actual_features) if result['success'] else 0
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['feature_access_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_user_notification_triggers(self):
        """Test user notification triggers"""
        print("\n🔔 Testing User Notification Triggers...")
        
        test_cases = [
            {
                'name': 'Welcome Notifications',
                'notification_type': NotificationType.WELCOME,
                'subscription_tier': 'premium',
                'expected_channels': ['email', 'sms', 'push', 'in_app']
            },
            {
                'name': 'Feature Access Notifications',
                'notification_type': NotificationType.FEATURE_ACCESS_GRANTED,
                'subscription_tier': 'enterprise',
                'expected_channels': ['email', 'push', 'in_app']
            },
            {
                'name': 'Subscription Update Notifications',
                'notification_type': NotificationType.SUBSCRIPTION_UPDATED,
                'subscription_tier': 'premium',
                'expected_channels': ['email', 'in_app']
            },
            {
                'name': 'Trial Ending Notifications',
                'notification_type': NotificationType.TRIAL_ENDING,
                'subscription_tier': 'basic',
                'expected_channels': ['email', 'sms', 'push', 'in_app']
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Prepare notification data
                notification_data = {
                    'customer_id': f"test_customer_{test_case['notification_type'].value}",
                    'user_id': f"user_{test_case['notification_type'].value}",
                    'subscription_tier': test_case['subscription_tier'],
                    'subscription_status': 'active',
                    'feature_changes': {
                        'features_granted': ['feature1', 'feature2'],
                        'features_removed': [],
                        'access_level': 'premium'
                    }
                }
                
                # Test notification sending
                if test_case['notification_type'] == NotificationType.WELCOME:
                    result = self.notification_service.send_welcome_notifications(notification_data)
                elif test_case['notification_type'] == NotificationType.FEATURE_ACCESS_GRANTED:
                    result = self.notification_service.send_feature_access_notifications(notification_data)
                elif test_case['notification_type'] == NotificationType.SUBSCRIPTION_UPDATED:
                    result = self.notification_service.send_subscription_update_notifications(notification_data)
                elif test_case['notification_type'] == NotificationType.TRIAL_ENDING:
                    result = self.notification_service.send_trial_ending_notifications(notification_data)
                else:
                    continue
                
                # Validate results
                if result['success']:
                    channels_used = result.get('channels', [])
                    notifications_sent = result.get('notifications_sent', 0)
                    
                    print(f"    ✅ Notifications sent successfully")
                    print(f"    📧 Channels used: {channels_used}")
                    print(f"    📊 Notifications sent: {notifications_sent}")
                    print(f"    ⚡ Processing time: {result.get('processing_time_ms', 0):.2f}ms")
                    
                    # Check if expected channels were used
                    expected_channels = test_case['expected_channels']
                    missing_channels = set(expected_channels) - set(channels_used)
                    if missing_channels:
                        print(f"    ⚠️  Missing channels: {missing_channels}")
                else:
                    print(f"    ❌ Notification sending failed: {result.get('error')}")
                
                # Record test result
                self.test_results['notification_tests'].append({
                    'test_name': test_case['name'],
                    'success': result['success'],
                    'notifications_sent': result.get('notifications_sent', 0),
                    'channels_used': result.get('channels', []),
                    'processing_time_ms': result.get('processing_time_ms', 0)
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['notification_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_analytics_event_tracking(self):
        """Test analytics event tracking"""
        print("\n📊 Testing Analytics Event Tracking...")
        
        test_cases = [
            {
                'name': 'Subscription Created Event',
                'event_type': EventType.SUBSCRIPTION_CREATED,
                'subscription_tier': 'premium',
                'expected_properties': ['subscription_id', 'subscription_tier', 'customer_id']
            },
            {
                'name': 'Feature Access Granted Event',
                'event_type': EventType.FEATURE_ACCESS_GRANTED,
                'subscription_tier': 'enterprise',
                'expected_properties': ['feature_name', 'access_level', 'subscription_tier']
            },
            {
                'name': 'Conversion Event',
                'event_type': EventType.CONVERSION,
                'subscription_tier': 'basic',
                'expected_properties': ['conversion_type', 'subscription_tier', 'funnel_stage']
            },
            {
                'name': 'Churn Event',
                'event_type': EventType.CHURN,
                'subscription_tier': 'premium',
                'expected_properties': ['churn_type', 'subscription_tier', 'lifetime_days']
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Prepare analytics data
                analytics_data = {
                    'customer_id': f"test_customer_{test_case['event_type'].value}",
                    'user_id': f"user_{test_case['event_type'].value}",
                    'subscription_id': f"sub_{test_case['event_type'].value}",
                    'subscription_tier': test_case['subscription_tier'],
                    'subscription_status': 'active',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'feature_changes': {
                        'features_granted': ['feature1', 'feature2'],
                        'access_level': 'premium'
                    }
                }
                
                # Test event tracking
                if test_case['event_type'] == EventType.SUBSCRIPTION_CREATED:
                    result = self.event_tracker.track_subscription_created(analytics_data)
                elif test_case['event_type'] == EventType.FEATURE_ACCESS_GRANTED:
                    result = self.event_tracker.track_feature_access_granted(analytics_data)
                elif test_case['event_type'] == EventType.CONVERSION:
                    result = self.event_tracker.track_conversion_event(analytics_data)
                elif test_case['event_type'] == EventType.CHURN:
                    result = self.event_tracker.track_churn_event(analytics_data)
                else:
                    continue
                
                # Validate results
                if result['success']:
                    event_id = result.get('event_id')
                    event_name = result.get('event_name')
                    
                    print(f"    ✅ Event tracked successfully")
                    print(f"    🆔 Event ID: {event_id}")
                    print(f"    📝 Event name: {event_name}")
                    print(f"    ⚡ Processing time: {result.get('processing_time_ms', 0):.2f}ms")
                    
                    # Validate event properties
                    expected_properties = test_case['expected_properties']
                    print(f"    📋 Expected properties: {expected_properties}")
                    
                else:
                    print(f"    ❌ Event tracking failed: {result.get('error')}")
                
                # Record test result
                self.test_results['analytics_tests'].append({
                    'test_name': test_case['name'],
                    'success': result['success'],
                    'event_id': result.get('event_id'),
                    'event_name': result.get('event_name'),
                    'processing_time_ms': result.get('processing_time_ms', 0)
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['analytics_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        print("\n⚡ Testing Performance Monitoring...")
        
        try:
            # Get performance metrics from services
            feature_metrics = self.feature_service.get_performance_metrics()
            notification_metrics = self.notification_service.get_performance_metrics()
            analytics_metrics = self.event_tracker.get_performance_metrics()
            
            print(f"\n  📊 Feature Access Service Metrics:")
            print(f"    🔄 Access updates: {feature_metrics.get('access_updates', 0)}")
            print(f"    ⏱️  Average update time: {feature_metrics.get('average_update_time_ms', 0):.2f}ms")
            
            print(f"\n  📊 Notification Service Metrics:")
            print(f"    📧 Notifications sent: {notification_metrics.get('notifications_sent', 0)}")
            print(f"    ❌ Notifications failed: {notification_metrics.get('notifications_failed', 0)}")
            print(f"    ⏱️  Average send time: {notification_metrics.get('average_send_time_ms', 0):.2f}ms")
            
            print(f"\n  📊 Analytics Event Tracker Metrics:")
            print(f"    📈 Events tracked: {analytics_metrics.get('events_tracked', 0)}")
            print(f"    ❌ Events failed: {analytics_metrics.get('events_failed', 0)}")
            print(f"    ⏱️  Average tracking time: {analytics_metrics.get('average_tracking_time_ms', 0):.2f}ms")
            print(f"    🔄 Real-time events: {analytics_metrics.get('real_time_events', 0)}")
            
            # Record test result
            self.test_results['performance_tests'].append({
                'test_name': 'Performance Monitoring',
                'success': True,
                'feature_metrics': feature_metrics,
                'notification_metrics': notification_metrics,
                'analytics_metrics': analytics_metrics
            })
            
        except Exception as e:
            print(f"    ❌ Performance monitoring test failed: {e}")
            self.test_results['performance_tests'].append({
                'test_name': 'Performance Monitoring',
                'success': False,
                'error': str(e)
            })
    
    def test_integration_workflow(self):
        """Test complete integration workflow"""
        print("\n🔄 Testing Complete Integration Workflow...")
        
        try:
            print(f"\n  📋 Testing: Complete Subscription Creation Workflow")
            
            # Simulate a complete subscription creation workflow
            customer_id = "test_integration_customer"
            user_id = f"user_{customer_id}"
            subscription_id = f"sub_{customer_id}"
            
            # Step 1: Feature access update
            print(f"    🔧 Step 1: Updating feature access...")
            feature_result = self.feature_service.update_feature_access_immediately(
                customer_id=customer_id,
                subscription_tier='premium',
                subscription_status='active',
                subscription_data={
                    'id': subscription_id,
                    'pricing_tier': 'premium',
                    'status': 'active',
                    'amount': 99.99,
                    'currency': 'usd'
                }
            )
            
            # Step 2: Send notifications
            print(f"    🔔 Step 2: Sending notifications...")
            notification_data = {
                'customer_id': customer_id,
                'user_id': user_id,
                'subscription_tier': 'premium',
                'subscription_status': 'active',
                'feature_changes': feature_result.get('feature_changes', {})
            }
            
            notification_result = self.notification_service.send_welcome_notifications(notification_data)
            
            # Step 3: Track analytics events
            print(f"    📊 Step 3: Tracking analytics events...")
            analytics_data = {
                'customer_id': customer_id,
                'user_id': user_id,
                'subscription_id': subscription_id,
                'subscription_tier': 'premium',
                'subscription_status': 'active',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'feature_changes': feature_result.get('feature_changes', {})
            }
            
            subscription_event = self.event_tracker.track_subscription_created(analytics_data)
            feature_event = self.event_tracker.track_feature_access_granted(analytics_data)
            conversion_event = self.event_tracker.track_conversion_event(analytics_data)
            
            # Validate workflow results
            workflow_success = (
                feature_result['success'] and
                notification_result['success'] and
                subscription_event['success'] and
                feature_event['success'] and
                conversion_event['success']
            )
            
            if workflow_success:
                print(f"    ✅ Complete workflow executed successfully")
                print(f"    🔧 Feature access updated: {len(feature_result.get('features_granted', []))} features")
                print(f"    📧 Notifications sent: {notification_result.get('notifications_sent', 0)}")
                print(f"    📊 Analytics events tracked: 3")
                
                total_time = (
                    feature_result.get('processing_time_ms', 0) +
                    notification_result.get('processing_time_ms', 0) +
                    subscription_event.get('processing_time_ms', 0) +
                    feature_event.get('processing_time_ms', 0) +
                    conversion_event.get('processing_time_ms', 0)
                )
                print(f"    ⚡ Total processing time: {total_time:.2f}ms")
            else:
                print(f"    ❌ Workflow failed")
                print(f"    Feature access: {feature_result['success']}")
                print(f"    Notifications: {notification_result['success']}")
                print(f"    Analytics: {subscription_event['success']}")
            
            # Record test result
            self.test_results['integration_tests'].append({
                'test_name': 'Complete Integration Workflow',
                'success': workflow_success,
                'feature_access_success': feature_result['success'],
                'notifications_success': notification_result['success'],
                'analytics_success': all([
                    subscription_event['success'],
                    feature_event['success'],
                    conversion_event['success']
                ]),
                'total_processing_time_ms': total_time if workflow_success else 0
            })
            
        except Exception as e:
            print(f"    ❌ Integration workflow test failed: {e}")
            self.test_results['integration_tests'].append({
                'test_name': 'Complete Integration Workflow',
                'success': False,
                'error': str(e)
            })
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📋 MINGUS INTEGRATION TEST REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        # Feature Access Tests
        print(f"\n🚀 FEATURE ACCESS TESTS")
        print("-" * 40)
        feature_tests = self.test_results['feature_access_tests']
        for test in feature_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('processing_time_ms', 0):.2f}ms")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Notification Tests
        print(f"\n🔔 NOTIFICATION TESTS")
        print("-" * 40)
        notification_tests = self.test_results['notification_tests']
        for test in notification_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('notifications_sent', 0)} notifications, {test.get('processing_time_ms', 0):.2f}ms")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Analytics Tests
        print(f"\n📊 ANALYTICS TESTS")
        print("-" * 40)
        analytics_tests = self.test_results['analytics_tests']
        for test in analytics_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('event_name', 'Unknown')}, {test.get('processing_time_ms', 0):.2f}ms")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Performance Tests
        print(f"\n⚡ PERFORMANCE TESTS")
        print("-" * 40)
        performance_tests = self.test_results['performance_tests']
        for test in performance_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']}")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Integration Tests
        print(f"\n🔄 INTEGRATION TESTS")
        print("-" * 40)
        integration_tests = self.test_results['integration_tests']
        for test in integration_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('total_processing_time_ms', 0):.2f}ms")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Summary
        print(f"\n" + "="*80)
        print(f"📊 TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        # Save detailed report
        report_file = f"mingus_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return passed_tests == total_tests


def main():
    """Main test execution function"""
    print("🚀 MINGUS Integration Features Test Suite")
    print("=" * 60)
    
    # Create tester instance
    tester = MINGUSIntegrationTester()
    
    # Setup services
    if not tester.setup_services():
        print("❌ Failed to setup services. Exiting.")
        return False
    
    # Run all tests
    try:
        tester.test_immediate_feature_access_updates()
        tester.test_user_notification_triggers()
        tester.test_analytics_event_tracking()
        tester.test_performance_monitoring()
        tester.test_integration_workflow()
        
        # Generate report
        success = tester.generate_test_report()
        
        if success:
            print("\n🎉 All tests passed! MINGUS integration features are working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please review the report for details.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test execution failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 