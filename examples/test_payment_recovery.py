#!/usr/bin/env python3
"""
Test Script for Payment Recovery System
=======================================

This script demonstrates the comprehensive payment recovery system:
- Payment failure handling
- Recovery strategy determination
- Dunning management
- Payment retry mechanisms
- Grace period management
- Recovery analytics

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

from billing.payment_recovery import PaymentRecoverySystem, PaymentStatus, DunningStage, RecoveryStrategy
from config.base import Config


class PaymentRecoveryTester:
    """Test class for payment recovery system"""
    
    def __init__(self):
        self.config = Config()
        self.db_session = None  # Would be initialized with actual database session
        self.recovery_system = None
        
        self.test_results = {
            'failure_handling_tests': [],
            'recovery_strategy_tests': [],
            'dunning_tests': [],
            'retry_tests': [],
            'grace_period_tests': [],
            'analytics_tests': [],
            'integration_tests': []
        }
    
    def setup_system(self):
        """Initialize payment recovery system"""
        print("🔧 Setting up Payment Recovery System...")
        
        try:
            self.recovery_system = PaymentRecoverySystem(self.db_session, self.config)
            print("✅ Payment Recovery System initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up payment recovery system: {e}")
            return False
    
    def test_payment_failure_handling(self):
        """Test payment failure handling"""
        print("\n🚨 Testing Payment Failure Handling...")
        
        test_cases = [
            {
                'name': 'Card Declined Failure',
                'customer_id': 'test_customer_001',
                'subscription_id': 'test_subscription_001',
                'invoice_id': 'inv_test_001',
                'payment_intent_id': 'pi_test_001',
                'failure_reason': 'card_declined',
                'failure_code': 'card_declined',
                'amount': 29.99,
                'currency': 'usd',
                'expected_strategy': RecoveryStrategy.AUTOMATIC_RETRY
            },
            {
                'name': 'Insufficient Funds Failure',
                'customer_id': 'test_customer_002',
                'subscription_id': 'test_subscription_002',
                'invoice_id': 'inv_test_002',
                'payment_intent_id': 'pi_test_002',
                'failure_reason': 'insufficient_funds',
                'failure_code': 'insufficient_funds',
                'amount': 99.99,
                'currency': 'usd',
                'expected_strategy': RecoveryStrategy.AUTOMATIC_RETRY
            },
            {
                'name': 'Expired Card Failure',
                'customer_id': 'test_customer_003',
                'subscription_id': 'test_subscription_003',
                'invoice_id': 'inv_test_003',
                'payment_intent_id': 'pi_test_003',
                'failure_reason': 'expired_card',
                'failure_code': 'expired_card',
                'amount': 199.99,
                'currency': 'usd',
                'expected_strategy': RecoveryStrategy.PAYMENT_METHOD_UPDATE
            },
            {
                'name': 'Fraudulent Transaction',
                'customer_id': 'test_customer_004',
                'subscription_id': 'test_subscription_004',
                'invoice_id': 'inv_test_004',
                'payment_intent_id': 'pi_test_004',
                'failure_reason': 'fraudulent',
                'failure_code': 'fraudulent',
                'amount': 299.99,
                'currency': 'usd',
                'expected_strategy': RecoveryStrategy.MANUAL_INTERVENTION
            },
            {
                'name': 'Processing Error',
                'customer_id': 'test_customer_005',
                'subscription_id': 'test_subscription_005',
                'invoice_id': 'inv_test_005',
                'payment_intent_id': 'pi_test_005',
                'failure_reason': 'processing_error',
                'failure_code': 'processing_error',
                'amount': 49.99,
                'currency': 'usd',
                'expected_strategy': RecoveryStrategy.AUTOMATIC_RETRY
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Handle payment failure
                result = self.recovery_system.handle_payment_failure(
                    customer_id=test_case['customer_id'],
                    subscription_id=test_case['subscription_id'],
                    invoice_id=test_case['invoice_id'],
                    payment_intent_id=test_case['payment_intent_id'],
                    failure_reason=test_case['failure_reason'],
                    failure_code=test_case['failure_code'],
                    amount=test_case['amount'],
                    currency=test_case['currency']
                )
                
                # Validate results
                if result['success']:
                    failure_id = result.get('failure_id')
                    recovery_strategy = result.get('recovery_strategy')
                    immediate_actions = result.get('immediate_actions', {})
                    scheduled_actions = result.get('scheduled_actions', {})
                    
                    print(f"    ✅ Payment failure handled successfully")
                    print(f"    🆔 Failure ID: {failure_id}")
                    print(f"    🎯 Recovery Strategy: {recovery_strategy}")
                    print(f"    ⚡ Immediate Actions: {immediate_actions.get('actions_executed', 0)}")
                    print(f"    📅 Scheduled Actions: {scheduled_actions.get('actions_scheduled', 0)}")
                    print(f"    ⏱️  Processing Time: {result.get('processing_time_ms', 0):.2f}ms")
                    
                    # Validate strategy
                    if recovery_strategy == test_case['expected_strategy'].value:
                        print(f"    ✅ Correct recovery strategy determined")
                    else:
                        print(f"    ⚠️  Strategy mismatch - Expected: {test_case['expected_strategy'].value}, Got: {recovery_strategy}")
                else:
                    print(f"    ❌ Payment failure handling failed: {result.get('error')}")
                
                # Record test result
                self.test_results['failure_handling_tests'].append({
                    'test_name': test_case['name'],
                    'success': result['success'],
                    'failure_id': result.get('failure_id'),
                    'recovery_strategy': result.get('recovery_strategy'),
                    'processing_time_ms': result.get('processing_time_ms', 0)
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['failure_handling_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_recovery_strategies(self):
        """Test recovery strategy determination"""
        print("\n🎯 Testing Recovery Strategy Determination...")
        
        test_cases = [
            {
                'name': 'Card Declined Strategy',
                'failure_reason': 'card_declined',
                'expected_strategies': ['automatic_retry', 'payment_method_update', 'grace_period']
            },
            {
                'name': 'Insufficient Funds Strategy',
                'failure_reason': 'insufficient_funds',
                'expected_strategies': ['automatic_retry', 'partial_payment', 'payment_plan']
            },
            {
                'name': 'Expired Card Strategy',
                'failure_reason': 'expired_card',
                'expected_strategies': ['payment_method_update', 'grace_period']
            },
            {
                'name': 'Fraudulent Strategy',
                'failure_reason': 'fraudulent',
                'expected_strategies': ['manual_intervention']
            },
            {
                'name': 'Processing Error Strategy',
                'failure_reason': 'processing_error',
                'expected_strategies': ['automatic_retry', 'manual_intervention']
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Create mock failure
                failure = type('MockFailure', (), {
                    'failure_reason': test_case['failure_reason'],
                    'customer_id': 'test_customer',
                    'amount': 99.99
                })()
                
                # Determine strategy
                strategy = self.recovery_system._determine_recovery_strategy(failure)
                
                # Validate strategy
                if strategy.value in test_case['expected_strategies']:
                    print(f"    ✅ Correct strategy determined: {strategy.value}")
                else:
                    print(f"    ⚠️  Unexpected strategy: {strategy.value}")
                    print(f"    Expected one of: {test_case['expected_strategies']}")
                
                # Record test result
                self.test_results['recovery_strategy_tests'].append({
                    'test_name': test_case['name'],
                    'success': strategy.value in test_case['expected_strategies'],
                    'determined_strategy': strategy.value,
                    'expected_strategies': test_case['expected_strategies']
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['recovery_strategy_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_dunning_management(self):
        """Test dunning management"""
        print("\n📧 Testing Dunning Management...")
        
        test_cases = [
            {
                'name': 'Soft Failure Dunning',
                'stage': DunningStage.SOFT_FAILURE,
                'delay_days': 0,
                'notification_type': 'immediate_notification',
                'retry_attempt': True
            },
            {
                'name': 'Hard Failure Dunning',
                'stage': DunningStage.HARD_FAILURE,
                'delay_days': 1,
                'notification_type': 'payment_failed_notification',
                'retry_attempt': True
            },
            {
                'name': 'Dunning Stage 1',
                'stage': DunningStage.DUNNING_1,
                'delay_days': 3,
                'notification_type': 'dunning_notification_1',
                'retry_attempt': True
            },
            {
                'name': 'Dunning Stage 2',
                'stage': DunningStage.DUNNING_2,
                'delay_days': 7,
                'notification_type': 'dunning_notification_2',
                'retry_attempt': True
            },
            {
                'name': 'Final Notice',
                'stage': DunningStage.FINAL_NOTICE,
                'delay_days': 30,
                'notification_type': 'final_notice',
                'retry_attempt': False
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Get dunning schedule
                schedule = self.recovery_system.dunning_schedule.get(test_case['stage'])
                
                if schedule:
                    # Validate schedule properties
                    delay_match = schedule.delay_days == test_case['delay_days']
                    notification_match = schedule.notification_type == test_case['notification_type']
                    retry_match = schedule.retry_attempt == test_case['retry_attempt']
                    
                    print(f"    📅 Delay Days: {schedule.delay_days} (Expected: {test_case['delay_days']})")
                    print(f"    📧 Notification Type: {schedule.notification_type}")
                    print(f"    🔄 Retry Attempt: {schedule.retry_attempt}")
                    
                    if delay_match and notification_match and retry_match:
                        print(f"    ✅ Dunning schedule configured correctly")
                    else:
                        print(f"    ⚠️  Schedule configuration mismatch")
                        
                    # Record test result
                    self.test_results['dunning_tests'].append({
                        'test_name': test_case['name'],
                        'success': delay_match and notification_match and retry_match,
                        'delay_days': schedule.delay_days,
                        'notification_type': schedule.notification_type,
                        'retry_attempt': schedule.retry_attempt
                    })
                else:
                    print(f"    ❌ Dunning schedule not found for stage: {test_case['stage']}")
                    self.test_results['dunning_tests'].append({
                        'test_name': test_case['name'],
                        'success': False,
                        'error': 'Schedule not found'
                    })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['dunning_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_payment_retry(self):
        """Test payment retry mechanisms"""
        print("\n🔄 Testing Payment Retry Mechanisms...")
        
        test_cases = [
            {
                'name': 'First Retry Attempt',
                'failure_id': 'test_failure_001',
                'retry_count': 0,
                'expected_retry': True
            },
            {
                'name': 'Second Retry Attempt',
                'failure_id': 'test_failure_002',
                'retry_count': 1,
                'expected_retry': True
            },
            {
                'name': 'Max Retries Reached',
                'failure_id': 'test_failure_003',
                'retry_count': 5,
                'expected_retry': False
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Test retry logic
                max_retries = self.recovery_system.recovery_config['max_retry_attempts']
                can_retry = test_case['retry_count'] < max_retries
                
                if can_retry == test_case['expected_retry']:
                    print(f"    ✅ Retry logic correct")
                    print(f"    🔄 Retry Count: {test_case['retry_count']}")
                    print(f"    📊 Max Retries: {max_retries}")
                    print(f"    ✅ Can Retry: {can_retry}")
                else:
                    print(f"    ⚠️  Retry logic mismatch")
                    print(f"    Expected: {test_case['expected_retry']}, Got: {can_retry}")
                
                # Record test result
                self.test_results['retry_tests'].append({
                    'test_name': test_case['name'],
                    'success': can_retry == test_case['expected_retry'],
                    'retry_count': test_case['retry_count'],
                    'max_retries': max_retries,
                    'can_retry': can_retry
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['retry_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_grace_period_management(self):
        """Test grace period management"""
        print("\n⏰ Testing Grace Period Management...")
        
        test_cases = [
            {
                'name': 'Standard Grace Period',
                'customer_id': 'test_customer_grace_001',
                'grace_period_days': 7,
                'expected_success': True
            },
            {
                'name': 'Extended Grace Period',
                'customer_id': 'test_customer_grace_002',
                'grace_period_days': 14,
                'expected_success': True
            },
            {
                'name': 'Enterprise Grace Period',
                'customer_id': 'test_customer_grace_003',
                'grace_period_days': 30,
                'expected_success': True
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Manage grace period
                result = self.recovery_system.manage_grace_period(
                    customer_id=test_case['customer_id'],
                    grace_period_days=test_case['grace_period_days']
                )
                
                # Validate results
                if result['success']:
                    grace_period_days = result.get('grace_period_days')
                    grace_period_end = result.get('grace_period_end')
                    subscriptions_updated = result.get('subscriptions_updated', 0)
                    notifications_sent = result.get('notification_sent', 0)
                    
                    print(f"    ✅ Grace period managed successfully")
                    print(f"    ⏰ Grace Period Days: {grace_period_days}")
                    print(f"    📅 Grace Period End: {grace_period_end}")
                    print(f"    🔄 Subscriptions Updated: {subscriptions_updated}")
                    print(f"    📧 Notifications Sent: {notifications_sent}")
                else:
                    print(f"    ❌ Grace period management failed: {result.get('error')}")
                
                # Record test result
                self.test_results['grace_period_tests'].append({
                    'test_name': test_case['name'],
                    'success': result['success'],
                    'grace_period_days': result.get('grace_period_days'),
                    'subscriptions_updated': result.get('subscriptions_updated', 0),
                    'notifications_sent': result.get('notification_sent', 0)
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['grace_period_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_recovery_analytics(self):
        """Test recovery analytics"""
        print("\n📊 Testing Recovery Analytics...")
        
        try:
            # Get recovery analytics
            analytics = self.recovery_system.get_recovery_analytics(days=30)
            
            if analytics['success']:
                total_failures = analytics.get('total_failures', 0)
                successful_recoveries = analytics.get('successful_recoveries', 0)
                failed_recoveries = analytics.get('failed_recoveries', 0)
                recovery_rate = analytics.get('recovery_rate', 0)
                total_revenue_at_risk = analytics.get('total_revenue_at_risk', 0)
                recovered_revenue = analytics.get('recovered_revenue', 0)
                revenue_recovery_rate = analytics.get('revenue_recovery_rate', 0)
                failure_reasons = analytics.get('failure_reasons', {})
                strategy_effectiveness = analytics.get('strategy_effectiveness', {})
                
                print(f"    ✅ Recovery analytics retrieved successfully")
                print(f"    📈 Total Failures: {total_failures}")
                print(f"    ✅ Successful Recoveries: {successful_recoveries}")
                print(f"    ❌ Failed Recoveries: {failed_recoveries}")
                print(f"    📊 Recovery Rate: {recovery_rate:.2f}%")
                print(f"    💰 Total Revenue at Risk: ${total_revenue_at_risk:.2f}")
                print(f"    💰 Recovered Revenue: ${recovered_revenue:.2f}")
                print(f"    📊 Revenue Recovery Rate: {revenue_recovery_rate:.2f}%")
                print(f"    📋 Failure Reasons: {len(failure_reasons)} categories")
                print(f"    🎯 Strategy Effectiveness: {len(strategy_effectiveness)} strategies")
                
                # Record test result
                self.test_results['analytics_tests'].append({
                    'test_name': 'Recovery Analytics',
                    'success': True,
                    'total_failures': total_failures,
                    'successful_recoveries': successful_recoveries,
                    'recovery_rate': recovery_rate,
                    'revenue_recovery_rate': revenue_recovery_rate
                })
            else:
                print(f"    ❌ Analytics retrieval failed: {analytics.get('error')}")
                self.test_results['analytics_tests'].append({
                    'test_name': 'Recovery Analytics',
                    'success': False,
                    'error': analytics.get('error')
                })
                
        except Exception as e:
            print(f"    ❌ Analytics test failed with exception: {e}")
            self.test_results['analytics_tests'].append({
                'test_name': 'Recovery Analytics',
                'success': False,
                'error': str(e)
            })
    
    def test_integration_workflow(self):
        """Test complete integration workflow"""
        print("\n🔄 Testing Complete Integration Workflow...")
        
        try:
            print(f"\n  📋 Testing: Complete Payment Recovery Workflow")
            
            # Step 1: Handle payment failure
            print(f"    🔧 Step 1: Handling payment failure...")
            failure_result = self.recovery_system.handle_payment_failure(
                customer_id='test_integration_customer',
                subscription_id='test_integration_subscription',
                invoice_id='inv_integration_test',
                payment_intent_id='pi_integration_test',
                failure_reason='card_declined',
                failure_code='card_declined',
                amount=99.99,
                currency='usd'
            )
            
            # Step 2: Process recovery actions
            print(f"    🔄 Step 2: Processing recovery actions...")
            recovery_result = self.recovery_system.process_recovery_actions()
            
            # Step 3: Update payment method
            print(f"    💳 Step 3: Updating payment method...")
            payment_method_result = self.recovery_system.update_payment_method(
                customer_id='test_integration_customer',
                new_payment_method_id='pm_test_updated'
            )
            
            # Step 4: Manage grace period
            print(f"    ⏰ Step 4: Managing grace period...")
            grace_period_result = self.recovery_system.manage_grace_period(
                customer_id='test_integration_customer',
                grace_period_days=7
            )
            
            # Step 5: Get analytics
            print(f"    📊 Step 5: Getting recovery analytics...")
            analytics_result = self.recovery_system.get_recovery_analytics(days=30)
            
            # Validate workflow results
            workflow_success = (
                failure_result['success'] and
                recovery_result['success'] and
                payment_method_result['success'] and
                grace_period_result['success'] and
                analytics_result['success']
            )
            
            if workflow_success:
                print(f"    ✅ Complete workflow executed successfully")
                print(f"    🔧 Failure handled: {failure_result.get('failure_id')}")
                print(f"    🔄 Actions processed: {recovery_result.get('processed_actions', 0)}")
                print(f"    💳 Payment method updated: {payment_method_result.get('payment_method_updated')}")
                print(f"    ⏰ Grace period managed: {grace_period_result.get('grace_period_days')} days")
                print(f"    📊 Analytics retrieved: {analytics_result.get('total_failures', 0)} failures")
            else:
                print(f"    ❌ Workflow failed")
                print(f"    Failure handling: {failure_result['success']}")
                print(f"    Recovery processing: {recovery_result['success']}")
                print(f"    Payment method update: {payment_method_result['success']}")
                print(f"    Grace period management: {grace_period_result['success']}")
                print(f"    Analytics retrieval: {analytics_result['success']}")
            
            # Record test result
            self.test_results['integration_tests'].append({
                'test_name': 'Complete Integration Workflow',
                'success': workflow_success,
                'failure_handling_success': failure_result['success'],
                'recovery_processing_success': recovery_result['success'],
                'payment_method_update_success': payment_method_result['success'],
                'grace_period_success': grace_period_result['success'],
                'analytics_success': analytics_result['success']
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
        print("📋 PAYMENT RECOVERY SYSTEM TEST REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        # Failure Handling Tests
        print(f"\n🚨 FAILURE HANDLING TESTS")
        print("-" * 40)
        failure_tests = self.test_results['failure_handling_tests']
        for test in failure_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('processing_time_ms', 0):.2f}ms")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Recovery Strategy Tests
        print(f"\n🎯 RECOVERY STRATEGY TESTS")
        print("-" * 40)
        strategy_tests = self.test_results['recovery_strategy_tests']
        for test in strategy_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('determined_strategy', 'Unknown')}")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Dunning Tests
        print(f"\n📧 DUNNING TESTS")
        print("-" * 40)
        dunning_tests = self.test_results['dunning_tests']
        for test in dunning_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('delay_days', 0)} days")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Retry Tests
        print(f"\n🔄 RETRY TESTS")
        print("-" * 40)
        retry_tests = self.test_results['retry_tests']
        for test in retry_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('retry_count', 0)} retries")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Unknown error')}")
        
        # Grace Period Tests
        print(f"\n⏰ GRACE PERIOD TESTS")
        print("-" * 40)
        grace_tests = self.test_results['grace_period_tests']
        for test in grace_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']} - {test.get('grace_period_days', 0)} days")
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
                recovery_rate = test.get('recovery_rate', 0)
                print(f"✅ {test['test_name']} - {recovery_rate:.2f}% recovery rate")
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
                print(f"✅ {test['test_name']}")
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
        
        # Performance Metrics
        print(f"\n📈 PERFORMANCE METRICS")
        print("-" * 40)
        metrics = self.recovery_system.get_performance_metrics()
        print(f"Recovery Attempts: {metrics.get('recovery_attempts', 0)}")
        print(f"Successful Recoveries: {metrics.get('successful_recoveries', 0)}")
        print(f"Failed Recoveries: {metrics.get('failed_recoveries', 0)}")
        print(f"Recovery Rate: {metrics.get('recovery_rate', 0):.2f}%")
        print(f"Average Recovery Time: {metrics.get('average_recovery_time_days', 0):.2f} days")
        print(f"Revenue Recovered: ${metrics.get('revenue_recovered', 0):.2f}")
        
        # Save detailed report
        report_file = f"payment_recovery_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return passed_tests == total_tests


def main():
    """Main test execution function"""
    print("🚀 Payment Recovery System Test Suite")
    print("=" * 60)
    
    # Create tester instance
    tester = PaymentRecoveryTester()
    
    # Setup system
    if not tester.setup_system():
        print("❌ Failed to setup payment recovery system. Exiting.")
        return False
    
    # Run all tests
    try:
        tester.test_payment_failure_handling()
        tester.test_recovery_strategies()
        tester.test_dunning_management()
        tester.test_payment_retry()
        tester.test_grace_period_management()
        tester.test_recovery_analytics()
        tester.test_integration_workflow()
        
        # Generate report
        success = tester.generate_test_report()
        
        if success:
            print("\n🎉 All tests passed! Payment recovery system is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please review the report for details.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test execution failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 