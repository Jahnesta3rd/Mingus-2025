#!/usr/bin/env python3
"""
Test Script for Immediate Retry Workflow
========================================

This script specifically tests the immediate retry workflow for temporary failures:
- Insufficient funds scenarios
- Processing errors
- Network errors
- Timeout errors
- Immediate retry logic and configuration

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


class ImmediateRetryWorkflowTester:
    """Test class for immediate retry workflow"""
    
    def __init__(self):
        self.config = Config()
        self.db_session = None  # Would be initialized with actual database session
        self.recovery_system = None
        
        self.test_results = {
            'temporary_failure_detection_tests': [],
            'immediate_retry_config_tests': [],
            'insufficient_funds_tests': [],
            'processing_error_tests': [],
            'network_error_tests': [],
            'retry_amount_calculation_tests': [],
            'retry_decision_tests': [],
            'workflow_integration_tests': []
        }
    
    def setup_system(self):
        """Initialize payment recovery system"""
        print("🔧 Setting up Payment Recovery System for Immediate Retry Testing...")
        
        try:
            self.recovery_system = PaymentRecoverySystem(self.db_session, self.config)
            print("✅ Payment Recovery System initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up payment recovery system: {e}")
            return False
    
    def test_temporary_failure_detection(self):
        """Test temporary failure detection logic"""
        print("\n🔍 Testing Temporary Failure Detection...")
        
        test_cases = [
            {
                'name': 'Insufficient Funds Detection',
                'failure_reason': 'insufficient_funds',
                'failure_code': 'insufficient_funds',
                'expected_temporary': True,
                'expected_insufficient_funds': True
            },
            {
                'name': 'Processing Error Detection',
                'failure_reason': 'processing_error',
                'failure_code': 'processing_error',
                'expected_temporary': True,
                'expected_insufficient_funds': False
            },
            {
                'name': 'Network Error Detection',
                'failure_reason': 'network_error',
                'failure_code': 'network_error',
                'expected_temporary': True,
                'expected_insufficient_funds': False
            },
            {
                'name': 'Timeout Error Detection',
                'failure_reason': 'timeout_error',
                'failure_code': 'timeout',
                'expected_temporary': True,
                'expected_insufficient_funds': False
            },
            {
                'name': 'Card Declined (Non-Temporary)',
                'failure_reason': 'card_declined',
                'failure_code': 'card_declined',
                'expected_temporary': False,
                'expected_insufficient_funds': False
            },
            {
                'name': 'Expired Card (Non-Temporary)',
                'failure_reason': 'expired_card',
                'failure_code': 'expired_card',
                'expected_temporary': False,
                'expected_insufficient_funds': False
            },
            {
                'name': 'Fraudulent Transaction (Non-Temporary)',
                'failure_reason': 'fraudulent',
                'failure_code': 'fraudulent',
                'expected_temporary': False,
                'expected_insufficient_funds': False
            },
            {
                'name': 'Insufficient Funds in Account',
                'failure_reason': 'insufficient_funds_in_account',
                'failure_code': 'card_declined_insufficient_funds',
                'expected_temporary': True,
                'expected_insufficient_funds': True
            },
            {
                'name': 'Low Balance Scenario',
                'failure_reason': 'low_balance',
                'failure_code': 'insufficient_balance',
                'expected_temporary': True,
                'expected_insufficient_funds': True
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Test temporary failure detection
                is_temporary = self.recovery_system._is_temporary_failure(
                    test_case['failure_reason'],
                    test_case['failure_code']
                )
                
                # Test insufficient funds detection
                is_insufficient_funds = self.recovery_system._is_insufficient_funds_scenario(
                    test_case['failure_reason'],
                    test_case['failure_code']
                )
                
                # Validate results
                temporary_match = is_temporary == test_case['expected_temporary']
                insufficient_funds_match = is_insufficient_funds == test_case['expected_insufficient_funds']
                
                print(f"    🔍 Temporary Failure: {is_temporary} (Expected: {test_case['expected_temporary']})")
                print(f"    💰 Insufficient Funds: {is_insufficient_funds} (Expected: {test_case['expected_insufficient_funds']})")
                
                if temporary_match and insufficient_funds_match:
                    print(f"    ✅ Detection logic working correctly")
                else:
                    print(f"    ❌ Detection logic mismatch")
                    if not temporary_match:
                        print(f"      Temporary failure detection failed")
                    if not insufficient_funds_match:
                        print(f"      Insufficient funds detection failed")
                
                # Record test result
                self.test_results['temporary_failure_detection_tests'].append({
                    'test_name': test_case['name'],
                    'success': temporary_match and insufficient_funds_match,
                    'is_temporary': is_temporary,
                    'expected_temporary': test_case['expected_temporary'],
                    'is_insufficient_funds': is_insufficient_funds,
                    'expected_insufficient_funds': test_case['expected_insufficient_funds']
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['temporary_failure_detection_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_immediate_retry_configuration(self):
        """Test immediate retry configuration logic"""
        print("\n⚙️ Testing Immediate Retry Configuration...")
        
        test_cases = [
            {
                'name': 'Insufficient Funds Configuration',
                'failure_reason': 'insufficient_funds',
                'expected_config': {
                    'max_immediate_retries': 2,
                    'retry_delay_seconds': 60,
                    'amount_adjustment': True
                }
            },
            {
                'name': 'Processing Error Configuration',
                'failure_reason': 'processing_error',
                'expected_config': {
                    'max_immediate_retries': 3,
                    'retry_delay_seconds': 30,
                    'amount_adjustment': False
                }
            },
            {
                'name': 'Network Error Configuration',
                'failure_reason': 'network_error',
                'expected_config': {
                    'max_immediate_retries': 3,
                    'retry_delay_seconds': 15,
                    'amount_adjustment': False
                }
            },
            {
                'name': 'Timeout Error Configuration',
                'failure_reason': 'timeout_error',
                'expected_config': {
                    'max_immediate_retries': 2,
                    'retry_delay_seconds': 45,
                    'amount_adjustment': False
                }
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
                
                # Get retry configuration
                config = self.recovery_system._get_immediate_retry_config(failure)
                
                # Validate configuration
                config_matches = True
                for key, expected_value in test_case['expected_config'].items():
                    actual_value = config.get(key)
                    if actual_value != expected_value:
                        config_matches = False
                        print(f"    ❌ Config mismatch for {key}: Expected {expected_value}, Got {actual_value}")
                
                if config_matches:
                    print(f"    ✅ Configuration correct")
                    print(f"    🔄 Max Retries: {config.get('max_immediate_retries')}")
                    print(f"    ⏱️ Retry Delay: {config.get('retry_delay_seconds')} seconds")
                    print(f"    💰 Amount Adjustment: {config.get('amount_adjustment')}")
                else:
                    print(f"    ❌ Configuration mismatch")
                
                # Record test result
                self.test_results['immediate_retry_config_tests'].append({
                    'test_name': test_case['name'],
                    'success': config_matches,
                    'config': config,
                    'expected_config': test_case['expected_config']
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['immediate_retry_config_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_insufficient_funds_scenarios(self):
        """Test insufficient funds specific scenarios"""
        print("\n💰 Testing Insufficient Funds Scenarios...")
        
        test_cases = [
            {
                'name': 'Standard Insufficient Funds',
                'failure_reason': 'insufficient_funds',
                'failure_code': 'insufficient_funds',
                'original_amount': 100.00,
                'attempt_1_expected': 90.00,  # 10% reduction
                'attempt_2_expected': 80.00   # 20% reduction
            },
            {
                'name': 'Card Declined Insufficient Funds',
                'failure_reason': 'card_declined_insufficient_funds',
                'failure_code': 'card_declined_insufficient_funds',
                'original_amount': 50.00,
                'attempt_1_expected': 45.00,
                'attempt_2_expected': 40.00
            },
            {
                'name': 'Low Balance Scenario',
                'failure_reason': 'low_balance',
                'failure_code': 'insufficient_balance',
                'original_amount': 25.00,
                'attempt_1_expected': 22.50,
                'attempt_2_expected': 20.00
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Create mock failure
                failure = type('MockFailure', (), {
                    'failure_reason': test_case['failure_reason'],
                    'failure_code': test_case['failure_code'],
                    'amount': test_case['original_amount']
                })()
                
                # Test retry amount calculation
                attempt_1_amount = self.recovery_system._calculate_retry_amount(failure, 1)
                attempt_2_amount = self.recovery_system._calculate_retry_amount(failure, 2)
                
                # Validate amounts
                attempt_1_match = abs(attempt_1_amount - test_case['attempt_1_expected']) < 0.01
                attempt_2_match = abs(attempt_2_amount - test_case['attempt_2_expected']) < 0.01
                
                print(f"    💰 Original Amount: ${test_case['original_amount']:.2f}")
                print(f"    🔄 Attempt 1 Amount: ${attempt_1_amount:.2f} (Expected: ${test_case['attempt_1_expected']:.2f})")
                print(f"    🔄 Attempt 2 Amount: ${attempt_2_amount:.2f} (Expected: ${test_case['attempt_2_expected']:.2f})")
                
                if attempt_1_match and attempt_2_match:
                    print(f"    ✅ Amount calculation correct")
                else:
                    print(f"    ❌ Amount calculation mismatch")
                    if not attempt_1_match:
                        print(f"      Attempt 1 amount incorrect")
                    if not attempt_2_match:
                        print(f"      Attempt 2 amount incorrect")
                
                # Record test result
                self.test_results['insufficient_funds_tests'].append({
                    'test_name': test_case['name'],
                    'success': attempt_1_match and attempt_2_match,
                    'attempt_1_amount': attempt_1_amount,
                    'attempt_2_amount': attempt_2_amount,
                    'expected_attempt_1': test_case['attempt_1_expected'],
                    'expected_attempt_2': test_case['attempt_2_expected']
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['insufficient_funds_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_retry_decision_logic(self):
        """Test retry decision logic"""
        print("\n🤔 Testing Retry Decision Logic...")
        
        test_cases = [
            {
                'name': 'Insufficient Funds Retry Decision',
                'error_code': 'insufficient_funds',
                'error_message': 'insufficient_funds',
                'attempt_1': True,   # Should retry
                'attempt_2': False,  # Should not retry
                'attempt_3': False   # Should not retry
            },
            {
                'name': 'Processing Error Retry Decision',
                'error_code': 'processing_error',
                'error_message': 'processing_error',
                'attempt_1': True,   # Should retry
                'attempt_2': True,   # Should retry
                'attempt_3': False   # Should not retry
            },
            {
                'name': 'Card Declined Retry Decision',
                'error_code': 'card_declined',
                'error_message': 'card_declined',
                'attempt_1': False,  # Should not retry
                'attempt_2': False,  # Should not retry
                'attempt_3': False   # Should not retry
            },
            {
                'name': 'Expired Card Retry Decision',
                'error_code': 'expired_card',
                'error_message': 'expired_card',
                'attempt_1': False,  # Should not retry
                'attempt_2': False,  # Should not retry
                'attempt_3': False   # Should not retry
            },
            {
                'name': 'Fraudulent Transaction Retry Decision',
                'error_code': 'fraudulent',
                'error_message': 'fraudulent',
                'attempt_1': False,  # Should not retry
                'attempt_2': False,  # Should not retry
                'attempt_3': False   # Should not retry
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n  📋 Testing: {test_case['name']}")
                
                # Test retry decisions for each attempt
                attempt_1_decision = self.recovery_system._should_retry_immediate(
                    test_case['error_code'],
                    test_case['error_message'],
                    1
                )
                
                attempt_2_decision = self.recovery_system._should_retry_immediate(
                    test_case['error_code'],
                    test_case['error_message'],
                    2
                )
                
                attempt_3_decision = self.recovery_system._should_retry_immediate(
                    test_case['error_code'],
                    test_case['error_message'],
                    3
                )
                
                # Validate decisions
                attempt_1_match = attempt_1_decision == test_case['attempt_1']
                attempt_2_match = attempt_2_decision == test_case['attempt_2']
                attempt_3_match = attempt_3_decision == test_case['attempt_3']
                
                print(f"    🔄 Attempt 1 Retry: {attempt_1_decision} (Expected: {test_case['attempt_1']})")
                print(f"    🔄 Attempt 2 Retry: {attempt_2_decision} (Expected: {test_case['attempt_2']})")
                print(f"    🔄 Attempt 3 Retry: {attempt_3_decision} (Expected: {test_case['attempt_3']})")
                
                if attempt_1_match and attempt_2_match and attempt_3_match:
                    print(f"    ✅ Retry decision logic correct")
                else:
                    print(f"    ❌ Retry decision logic mismatch")
                    if not attempt_1_match:
                        print(f"      Attempt 1 decision incorrect")
                    if not attempt_2_match:
                        print(f"      Attempt 2 decision incorrect")
                    if not attempt_3_match:
                        print(f"      Attempt 3 decision incorrect")
                
                # Record test result
                self.test_results['retry_decision_tests'].append({
                    'test_name': test_case['name'],
                    'success': attempt_1_match and attempt_2_match and attempt_3_match,
                    'attempt_1_decision': attempt_1_decision,
                    'attempt_2_decision': attempt_2_decision,
                    'attempt_3_decision': attempt_3_decision,
                    'expected_attempt_1': test_case['attempt_1'],
                    'expected_attempt_2': test_case['attempt_2'],
                    'expected_attempt_3': test_case['attempt_3']
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['retry_decision_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def test_workflow_integration(self):
        """Test complete immediate retry workflow integration"""
        print("\n🔄 Testing Complete Immediate Retry Workflow...")
        
        test_cases = [
            {
                'name': 'Insufficient Funds Workflow',
                'customer_id': 'test_customer_insufficient',
                'subscription_id': 'test_subscription_insufficient',
                'invoice_id': 'inv_insufficient_test',
                'payment_intent_id': 'pi_insufficient_test',
                'failure_reason': 'insufficient_funds',
                'failure_code': 'insufficient_funds',
                'amount': 99.99,
                'currency': 'usd',
                'expected_temporary': True,
                'expected_immediate_retry': True
            },
            {
                'name': 'Processing Error Workflow',
                'customer_id': 'test_customer_processing',
                'subscription_id': 'test_subscription_processing',
                'invoice_id': 'inv_processing_test',
                'payment_intent_id': 'pi_processing_test',
                'failure_reason': 'processing_error',
                'failure_code': 'processing_error',
                'amount': 49.99,
                'currency': 'usd',
                'expected_temporary': True,
                'expected_immediate_retry': True
            },
            {
                'name': 'Card Declined Workflow (Non-Temporary)',
                'customer_id': 'test_customer_declined',
                'subscription_id': 'test_subscription_declined',
                'invoice_id': 'inv_declined_test',
                'payment_intent_id': 'pi_declined_test',
                'failure_reason': 'card_declined',
                'failure_code': 'card_declined',
                'amount': 29.99,
                'currency': 'usd',
                'expected_temporary': False,
                'expected_immediate_retry': False
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
                
                # Validate workflow results
                if result['success']:
                    is_temporary = result.get('is_temporary_failure', False)
                    immediate_retry_attempted = result.get('immediate_retry_attempted', False)
                    
                    print(f"    🔍 Temporary Failure: {is_temporary} (Expected: {test_case['expected_temporary']})")
                    print(f"    🔄 Immediate Retry Attempted: {immediate_retry_attempted} (Expected: {test_case['expected_immediate_retry']})")
                    
                    if is_temporary and immediate_retry_attempted:
                        retry_result = result.get('retry_result', {})
                        retry_success = retry_result.get('success', False)
                        retry_attempts = retry_result.get('retry_attempts', 0)
                        
                        print(f"    ✅ Immediate Retry Success: {retry_success}")
                        print(f"    🔄 Retry Attempts: {retry_attempts}")
                        print(f"    💰 Recovery Method: {retry_result.get('recovery_method', 'unknown')}")
                    elif not is_temporary and not immediate_retry_attempted:
                        recovery_strategy = result.get('recovery_strategy', 'unknown')
                        print(f"    📋 Standard Recovery Strategy: {recovery_strategy}")
                    
                    # Validate expectations
                    temporary_match = is_temporary == test_case['expected_temporary']
                    retry_match = immediate_retry_attempted == test_case['expected_immediate_retry']
                    
                    if temporary_match and retry_match:
                        print(f"    ✅ Workflow behavior correct")
                    else:
                        print(f"    ❌ Workflow behavior mismatch")
                        if not temporary_match:
                            print(f"      Temporary failure detection incorrect")
                        if not retry_match:
                            print(f"      Immediate retry decision incorrect")
                else:
                    print(f"    ❌ Workflow execution failed: {result.get('error')}")
                
                # Record test result
                self.test_results['workflow_integration_tests'].append({
                    'test_name': test_case['name'],
                    'success': result['success'],
                    'is_temporary_failure': result.get('is_temporary_failure', False),
                    'immediate_retry_attempted': result.get('immediate_retry_attempted', False),
                    'immediate_retry_success': result.get('immediate_retry_success', False),
                    'processing_time_ms': result.get('processing_time_ms', 0)
                })
                
            except Exception as e:
                print(f"    ❌ Test failed with exception: {e}")
                self.test_results['workflow_integration_tests'].append({
                    'test_name': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📋 IMMEDIATE RETRY WORKFLOW TEST REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        # Temporary Failure Detection Tests
        print(f"\n🔍 TEMPORARY FAILURE DETECTION TESTS")
        print("-" * 50)
        detection_tests = self.test_results['temporary_failure_detection_tests']
        for test in detection_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']}")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Detection failed')}")
        
        # Immediate Retry Configuration Tests
        print(f"\n⚙️ IMMEDIATE RETRY CONFIGURATION TESTS")
        print("-" * 50)
        config_tests = self.test_results['immediate_retry_config_tests']
        for test in config_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']}")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Configuration failed')}")
        
        # Insufficient Funds Tests
        print(f"\n💰 INSUFFICIENT FUNDS TESTS")
        print("-" * 50)
        insufficient_tests = self.test_results['insufficient_funds_tests']
        for test in insufficient_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']}")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Amount calculation failed')}")
        
        # Retry Decision Tests
        print(f"\n🤔 RETRY DECISION TESTS")
        print("-" * 50)
        decision_tests = self.test_results['retry_decision_tests']
        for test in decision_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']}")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Decision logic failed')}")
        
        # Workflow Integration Tests
        print(f"\n🔄 WORKFLOW INTEGRATION TESTS")
        print("-" * 50)
        integration_tests = self.test_results['workflow_integration_tests']
        for test in integration_tests:
            total_tests += 1
            if test['success']:
                passed_tests += 1
                print(f"✅ {test['test_name']}")
            else:
                print(f"❌ {test['test_name']} - {test.get('error', 'Workflow failed')}")
        
        # Summary
        print(f"\n" + "="*80)
        print(f"📊 TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        # Key Metrics
        print(f"\n📈 KEY METRICS")
        print("-" * 40)
        
        # Temporary failure detection accuracy
        detection_success = sum(1 for test in detection_tests if test['success'])
        detection_total = len(detection_tests)
        if detection_total > 0:
            detection_accuracy = (detection_success / detection_total) * 100
            print(f"Temporary Failure Detection Accuracy: {detection_accuracy:.1f}%")
        
        # Configuration accuracy
        config_success = sum(1 for test in config_tests if test['success'])
        config_total = len(config_tests)
        if config_total > 0:
            config_accuracy = (config_success / config_total) * 100
            print(f"Configuration Accuracy: {config_accuracy:.1f}%")
        
        # Workflow success rate
        workflow_success = sum(1 for test in integration_tests if test['success'])
        workflow_total = len(integration_tests)
        if workflow_total > 0:
            workflow_accuracy = (workflow_success / workflow_total) * 100
            print(f"Workflow Success Rate: {workflow_accuracy:.1f}%")
        
        # Save detailed report
        report_file = f"immediate_retry_workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return passed_tests == total_tests


def main():
    """Main test execution function"""
    print("🚀 Immediate Retry Workflow Test Suite")
    print("=" * 60)
    
    # Create tester instance
    tester = ImmediateRetryWorkflowTester()
    
    # Setup system
    if not tester.setup_system():
        print("❌ Failed to setup payment recovery system. Exiting.")
        return False
    
    # Run all tests
    try:
        tester.test_temporary_failure_detection()
        tester.test_immediate_retry_configuration()
        tester.test_insufficient_funds_scenarios()
        tester.test_retry_decision_logic()
        tester.test_workflow_integration()
        
        # Generate report
        success = tester.generate_test_report()
        
        if success:
            print("\n🎉 All tests passed! Immediate retry workflow is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please review the report for details.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test execution failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 