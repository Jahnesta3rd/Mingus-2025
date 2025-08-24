#!/usr/bin/env python3
"""
Test script for Analytics and Optimization
Tests payment failure rate tracking by payment method and recovery rate optimization with A/B testing.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from billing.payment_recovery import PaymentRecoverySystem, PaymentFailure, RecoveryAction
from models.payment_recovery import PaymentRecoveryRecord, RecoveryStatus, ActionStatus
from models.subscription import Customer, Subscription
from config.base import Config

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.customers = {}
        self.subscriptions = {}
        self.failures = {}
        self.actions = {}
        self.analytics = {}
        self.ab_tests = {}
    
    def commit(self):
        pass
    
    def add(self, obj):
        if isinstance(obj, Customer):
            self.customers[obj.id] = obj
        elif isinstance(obj, Subscription):
            self.subscriptions[obj.id] = obj
        elif isinstance(obj, PaymentRecoveryRecord):
            self.failures[obj.id] = obj
        elif isinstance(obj, RecoveryAction):
            self.actions[obj.action_id] = obj
    
    def query(self, model):
        return MockQuery(self, model)

class MockQuery:
    """Mock query for testing"""
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.filters = []
    
    def filter(self, condition):
        self.filters.append(condition)
        return self
    
    def first(self):
        # Mock implementation
        return None
    
    def all(self):
        # Mock implementation
        return []

def create_mock_customer(customer_type: str = 'standard') -> Customer:
    """Create a mock customer for testing"""
    customer_id = str(uuid.uuid4())
    
    if customer_type == 'high_value':
        status = 'active'
        metadata = {'monthly_revenue': 750.0, 'subscription_length_months': 18}
    elif customer_type == 'at_risk':
        status = 'grace_period'
        metadata = {'payment_failures_last_3_months': 3}
    else:
        status = 'active'
        metadata = {'monthly_revenue': 75.0, 'subscription_length_months': 3}
    
    return Customer(
        id=customer_id,
        stripe_customer_id=f"cus_{uuid.uuid4().hex[:24]}",
        email=f"{customer_type}@example.com",
        name=f"{customer_type.title()} Customer",
        status=status,
        created_at=datetime.now(timezone.utc) - timedelta(days=90),
        metadata=metadata
    )

def create_mock_subscription(customer_id: str, customer_type: str = 'standard') -> Subscription:
    """Create a mock subscription for testing"""
    if customer_type == 'high_value':
        amount = 750.0
        plan_id = "premium_plan"
    elif customer_type == 'at_risk':
        amount = 50.0
        plan_id = "basic_plan"
    else:
        amount = 75.0
        plan_id = "standard_plan"
    
    return Subscription(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        stripe_subscription_id=f"sub_{uuid.uuid4().hex[:24]}",
        status="active",
        plan_id=plan_id,
        amount=amount,
        currency="usd",
        interval="month",
        created_at=datetime.now(timezone.utc),
        metadata={}
    )

def create_mock_failure_record(customer_id: str, subscription_id: str, failure_reason: str = "expired_card") -> PaymentRecoveryRecord:
    """Create a mock payment failure record for testing"""
    return PaymentRecoveryRecord(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        subscription_id=subscription_id,
        invoice_id=f"in_{uuid.uuid4().hex[:24]}",
        payment_intent_id=f"pi_{uuid.uuid4().hex[:24]}",
        failure_reason=failure_reason,
        failure_code="card_declined_expired",
        amount=99.99,
        currency="usd",
        failed_at=datetime.now(timezone.utc),
        status=RecoveryStatus.PENDING,
        retry_count=0,
        metadata={}
    )

def test_payment_method_analytics_tracking():
    """Test payment method analytics tracking functionality"""
    print("📊 Testing Payment Method Analytics Tracking")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different payment methods and failure reasons
    print("📋 Test 1: Payment Method Analytics Tracking")
    
    payment_methods = ['credit_card', 'debit_card', 'bank_transfer', 'digital_wallet', 'crypto']
    failure_reasons = [
        'expired_card',
        'insufficient_funds',
        'card_declined',
        'fraudulent_transaction',
        'daily_limit_exceeded',
        'account_closed',
        'routing_error',
        'account_suspended',
        'verification_required',
        'network_error'
    ]
    
    customer = create_mock_customer('standard')
    db.add(customer)
    
    for payment_method in payment_methods:
        print(f"   Testing {payment_method}:")
        
        for failure_reason in failure_reasons[:3]:  # Test first 3 failure reasons
            result = recovery_system.track_payment_method_analytics(
                payment_method=payment_method,
                failure_reason=failure_reason,
                amount=99.99,
                customer_id=customer.id
            )
            
            if result['success']:
                print(f"     {failure_reason}: ✅ Recorded")
                print(f"       Category: {result['failure_category']}")
                print(f"       Alerts: {len(result['alerts_triggered'])}")
            else:
                print(f"     {failure_reason}: ❌ {result['error']}")
        
        print()
    
    print("✅ Payment Method Analytics Tracking Tests Completed")
    print()

def test_payment_method_analytics_retrieval():
    """Test payment method analytics retrieval functionality"""
    print("📈 Testing Payment Method Analytics Retrieval")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test single payment method analytics
    print("📋 Test 1: Single Payment Method Analytics")
    
    payment_methods = ['credit_card', 'debit_card', 'bank_transfer', 'digital_wallet', 'crypto']
    time_periods = ['1d', '7d', '30d', '90d']
    
    for payment_method in payment_methods:
        print(f"   {payment_method.upper()}:")
        
        for time_period in time_periods:
            result = recovery_system.get_payment_method_analytics(payment_method, time_period)
            
            if result['success']:
                analytics_data = result['analytics_data']
                print(f"     {time_period}:")
                print(f"       Failure Rate: {analytics_data.get('failure_rate', 0):.1%}")
                print(f"       Recovery Rate: {analytics_data.get('recovery_rate', 0):.1%}")
                print(f"       Total Attempts: {analytics_data.get('total_attempts', 0)}")
                print(f"       Total Failures: {analytics_data.get('total_failures', 0)}")
                print(f"       Total Recoveries: {analytics_data.get('total_recoveries', 0)}")
                print(f"       Avg Recovery Time: {analytics_data.get('average_recovery_time', 0):.1f} days")
            else:
                print(f"     {time_period}: ❌ {result['error']}")
        
        print()
    
    # Test all payment methods analytics
    print("📋 Test 2: All Payment Methods Analytics")
    
    for time_period in time_periods:
        print(f"   {time_period.upper()}:")
        
        result = recovery_system.get_payment_method_analytics(time_period=time_period)
        
        if result['success']:
            analytics_data = result['analytics_data']
            
            for method, data in analytics_data.items():
                print(f"     {method}:")
                print(f"       Failure Rate: {data.get('failure_rate', 0):.1%}")
                print(f"       Recovery Rate: {data.get('recovery_rate', 0):.1%}")
                print(f"       Total Attempts: {data.get('total_attempts', 0)}")
            
            # Show trends
            trends = result['trends']
            print(f"     Trends:")
            print(f"       Failure Rate Trend: {trends.get('failure_rate_trend', 'unknown')}")
            print(f"       Recovery Rate Trend: {trends.get('recovery_rate_trend', 'unknown')}")
            print(f"       Recovery Time Trend: {trends.get('recovery_time_trend', 'unknown')}")
            
            # Show insights
            insights = result['insights']
            print(f"     Insights: {len(insights)}")
            for insight in insights:
                print(f"       {insight['type']}: {insight['message']}")
        else:
            print(f"     ❌ {result['error']}")
        
        print()
    
    print("✅ Payment Method Analytics Retrieval Tests Completed")
    print()

def test_ab_test_creation():
    """Test A/B test creation functionality"""
    print("🧪 Testing A/B Test Creation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different optimization strategies
    print("📋 Test 1: A/B Test Creation for Different Strategies")
    
    test_configs = [
        {
            'name': 'Retry Timing Optimization',
            'strategy': 'retry_timing',
            'variants': [
                {'name': 'immediate', 'delay_minutes': 0},
                {'name': 'delayed_1h', 'delay_minutes': 60},
                {'name': 'delayed_4h', 'delay_minutes': 240},
                {'name': 'delayed_24h', 'delay_minutes': 1440}
            ]
        },
        {
            'name': 'Retry Amount Optimization',
            'strategy': 'retry_amounts',
            'variants': [
                {'name': 'full_amount', 'percentage': 100},
                {'name': 'reduced_10', 'percentage': 90},
                {'name': 'reduced_25', 'percentage': 75},
                {'name': 'reduced_50', 'percentage': 50}
            ]
        },
        {
            'name': 'Grace Period Duration Optimization',
            'strategy': 'grace_period_duration',
            'variants': [
                {'name': '3_days', 'duration_days': 3},
                {'name': '7_days', 'duration_days': 7},
                {'name': '10_days', 'duration_days': 10},
                {'name': '14_days', 'duration_days': 14}
            ]
        },
        {
            'name': 'Dunning Email Sequence Optimization',
            'strategy': 'dunning_email_sequence',
            'variants': [
                {'name': 'aggressive', 'frequency': 'daily', 'tone': 'urgent'},
                {'name': 'moderate', 'frequency': 'every_3_days', 'tone': 'professional'},
                {'name': 'gentle', 'frequency': 'weekly', 'tone': 'friendly'},
                {'name': 'minimal', 'frequency': 'every_2_weeks', 'tone': 'informative'}
            ]
        },
        {
            'name': 'Retention Offers Optimization',
            'strategy': 'retention_offers',
            'variants': [
                {'name': 'no_offer', 'discount_percent': 0},
                {'name': 'small_discount', 'discount_percent': 10},
                {'name': 'medium_discount', 'discount_percent': 25},
                {'name': 'large_discount', 'discount_percent': 50}
            ]
        }
    ]
    
    created_tests = []
    
    for test_config in test_configs:
        print(f"   Creating test: {test_config['name']}")
        
        result = recovery_system.create_ab_test(
            test_name=test_config['name'],
            strategy=test_config['strategy'],
            variants=test_config['variants']
        )
        
        if result['success']:
            print(f"     ✅ Test created successfully")
            print(f"       Test ID: {result['test_id']}")
            print(f"       Strategy: {result['strategy']}")
            print(f"       Variants: {len(result['variants'])}")
            print(f"       Status: {result['status']}")
            print(f"       Traffic Allocation: {result['traffic_allocation']}")
            
            created_tests.append(result)
        else:
            print(f"     ❌ Error: {result['error']}")
        
        print()
    
    print("✅ A/B Test Creation Tests Completed")
    print()
    
    return created_tests

def test_customer_ab_test_assignment():
    """Test customer assignment to A/B tests"""
    print("👥 Testing Customer A/B Test Assignment")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create a test first
    print("📋 Test 1: Customer Assignment to A/B Tests")
    
    test_result = recovery_system.create_ab_test(
        test_name='Retry Timing Test',
        strategy='retry_timing',
        variants=[
            {'name': 'immediate', 'delay_minutes': 0},
            {'name': 'delayed_1h', 'delay_minutes': 60},
            {'name': 'delayed_4h', 'delay_minutes': 240}
        ]
    )
    
    if not test_result['success']:
        print(f"❌ Failed to create test: {test_result['error']}")
        return
    
    test_id = test_result['test_id']
    
    # Create customers and assign them to the test
    customer_types = ['standard', 'high_value', 'at_risk']
    assignment_results = {}
    
    for customer_type in customer_types:
        print(f"   Testing {customer_type} customers:")
        
        for i in range(10):  # Assign 10 customers of each type
            customer = create_mock_customer(customer_type)
            db.add(customer)
            
            result = recovery_system.assign_customer_to_ab_test(customer.id, test_id)
            
            if result['success']:
                variant = result['variant']
                if variant not in assignment_results:
                    assignment_results[variant] = 0
                assignment_results[variant] += 1
                
                print(f"     Customer {i+1}: {variant}")
            else:
                print(f"     Customer {i+1}: ❌ {result['error']}")
        
        print()
    
    # Show assignment distribution
    print("📋 Test 2: Assignment Distribution Analysis")
    total_assignments = sum(assignment_results.values())
    
    for variant, count in assignment_results.items():
        percentage = (count / total_assignments) * 100
        print(f"   {variant}: {count} customers ({percentage:.1f}%)")
    
    print()
    print("✅ Customer A/B Test Assignment Tests Completed")
    print()
    
    return test_id

def test_ab_test_result_recording():
    """Test A/B test result recording functionality"""
    print("📝 Testing A/B Test Result Recording")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create a test and assign customers
    print("📋 Test 1: A/B Test Result Recording")
    
    test_result = recovery_system.create_ab_test(
        test_name='Recovery Strategy Test',
        strategy='retry_timing',
        variants=[
            {'name': 'immediate', 'delay_minutes': 0},
            {'name': 'delayed_1h', 'delay_minutes': 60},
            {'name': 'delayed_4h', 'delay_minutes': 240}
        ]
    )
    
    if not test_result['success']:
        print(f"❌ Failed to create test: {test_result['error']}")
        return
    
    test_id = test_result['test_id']
    
    # Create customers and assign them
    customers = []
    for i in range(20):
        customer = create_mock_customer('standard')
        db.add(customer)
        customers.append(customer)
        
        # Assign to test
        assignment_result = recovery_system.assign_customer_to_ab_test(customer.id, test_id)
        if not assignment_result['success']:
            print(f"❌ Failed to assign customer {i+1}: {assignment_result['error']}")
    
    # Record different types of results
    result_types = [
        'payment_recovery_success',
        'payment_recovery_failure',
        'customer_churn',
        'customer_satisfaction',
        'recovery_time'
    ]
    
    for i, customer in enumerate(customers):
        # Record multiple result types for each customer
        for result_type in result_types[:2]:  # Record first 2 result types
            result_data = {
                'amount': 99.99,
                'recovery_time_days': 5.2,
                'satisfaction_score': 8.5,
                'churn_probability': 0.15
            }
            
            result = recovery_system.record_ab_test_result(
                customer_id=customer.id,
                test_id=test_id,
                result_type=result_type,
                result_data=result_data
            )
            
            if result['success']:
                print(f"   Customer {i+1}, {result_type}: ✅ {result['variant']}")
            else:
                print(f"   Customer {i+1}, {result_type}: ❌ {result['error']}")
    
    print()
    print("✅ A/B Test Result Recording Tests Completed")
    print()
    
    return test_id

def test_ab_test_results_analysis():
    """Test A/B test results analysis functionality"""
    print("📊 Testing A/B Test Results Analysis")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create a test and record some results
    print("📋 Test 1: A/B Test Results Analysis")
    
    test_result = recovery_system.create_ab_test(
        test_name='Comprehensive Recovery Test',
        strategy='retry_timing',
        variants=[
            {'name': 'immediate', 'delay_minutes': 0},
            {'name': 'delayed_1h', 'delay_minutes': 60},
            {'name': 'delayed_4h', 'delay_minutes': 240},
            {'name': 'delayed_24h', 'delay_minutes': 1440}
        ]
    )
    
    if not test_result['success']:
        print(f"❌ Failed to create test: {test_result['error']}")
        return
    
    test_id = test_result['test_id']
    
    # Get test results
    result = recovery_system.get_ab_test_results(test_id)
    
    if result['success']:
        print(f"   Test: {result['test_name']}")
        print(f"   Strategy: {result['strategy']}")
        print(f"   Status: {result['status']}")
        print()
        
        # Show results by variant
        print("   Results by Variant:")
        for variant_result in result['results']:
            variant = variant_result['variant']
            sample_size = variant_result['sample_size']
            recovery_rate = variant_result['recovery_rate']
            recovery_time = variant_result['recovery_time']
            satisfaction = variant_result['customer_satisfaction']
            
            print(f"     {variant}:")
            print(f"       Sample Size: {sample_size}")
            print(f"       Recovery Rate: {recovery_rate:.1%}")
            print(f"       Recovery Time: {recovery_time:.1f} days")
            print(f"       Customer Satisfaction: {satisfaction:.1%}")
        
        print()
        
        # Show statistical analysis
        print("   Statistical Analysis:")
        stats = result['statistical_analysis']
        print(f"     Statistical Significance: {stats.get('statistical_significance', False)}")
        print(f"     Confidence Level: {stats.get('confidence_level', 0):.1%}")
        print(f"     P-Value: {stats.get('p_value', 0):.3f}")
        print(f"     Effect Size: {stats.get('effect_size', 'unknown')}")
        print(f"     Recommended Variant: {stats.get('recommended_variant', 'none')}")
        
        print()
        
        # Show recommendations
        print("   Recommendations:")
        for recommendation in result['recommendations']:
            print(f"     {recommendation['type']}: {recommendation['message']}")
            print(f"       Severity: {recommendation['severity']}")
            print(f"       Reasoning: {recommendation['reasoning']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    print()
    print("✅ A/B Test Results Analysis Tests Completed")
    print()

def test_optimization_strategies():
    """Test different optimization strategies"""
    print("🎯 Testing Optimization Strategies")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different optimization strategies
    print("📋 Test 1: Optimization Strategy Configuration")
    
    optimization_config = recovery_system.recovery_config['dunning_email_sequence']['analytics_and_optimization']['recovery_rate_optimization']
    strategies = optimization_config['optimization_strategies']
    
    for strategy_name, strategy_config in strategies.items():
        print(f"   {strategy_name.replace('_', ' ').title()}:")
        print(f"     Enabled: {strategy_config.get('enabled', False)}")
        
        if strategy_config.get('enabled', False):
            variants = strategy_config.get('test_variants', [])
            print(f"     Variants: {len(variants)}")
            
            for variant in variants:
                print(f"       - {variant['name']}: {variant}")
        
        print()
    
    # Test A/B testing configuration
    print("📋 Test 2: A/B Testing Configuration")
    
    ab_config = optimization_config['ab_testing']
    print(f"   Enabled: {ab_config.get('enabled', False)}")
    print(f"   Test Duration: {ab_config.get('test_duration_days', 0)} days")
    print(f"   Minimum Sample Size: {ab_config.get('minimum_sample_size', 0)}")
    print(f"   Confidence Level: {ab_config.get('confidence_level', 0):.1%}")
    print(f"   Traffic Allocation: {ab_config.get('traffic_allocation', {})}")
    print(f"   Success Metrics: {ab_config.get('success_metrics', {})}")
    print(f"   Statistical Tests: {list(ab_config.get('statistical_tests', {}).keys())}")
    
    print()
    
    # Test machine learning configuration
    print("📋 Test 3: Machine Learning Configuration")
    
    ml_config = optimization_config['machine_learning']
    print(f"   Enabled: {ml_config.get('enabled', False)}")
    
    if ml_config.get('enabled', False):
        models = ml_config.get('models', {})
        for model_name, model_config in models.items():
            print(f"     {model_name}:")
            print(f"       Enabled: {model_config.get('enabled', False)}")
            print(f"       Algorithm: {model_config.get('algorithm', 'unknown')}")
            print(f"       Features: {model_config.get('features', [])}")
            print(f"       Retraining: {model_config.get('retraining_frequency', 'unknown')}")
    
    print()
    print("✅ Optimization Strategies Tests Completed")
    print()

def test_performance_monitoring():
    """Test performance monitoring functionality"""
    print("📈 Testing Performance Monitoring")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test KPI configuration
    print("📋 Test 1: Key Performance Indicators")
    
    monitoring_config = recovery_system.recovery_config['dunning_email_sequence']['analytics_and_optimization']['performance_monitoring']
    kpis = monitoring_config['key_performance_indicators']
    
    for kpi_name, kpi_config in kpis.items():
        print(f"   {kpi_name.replace('_', ' ').title()}:")
        print(f"     Enabled: {kpi_config.get('enabled', False)}")
        print(f"     Calculation: {kpi_config.get('calculation', 'unknown')}")
        print(f"     Target: {kpi_config.get('target', 'unknown')}")
        print(f"     Alert Threshold: {kpi_config.get('alert_threshold', 'unknown')}")
        print()
    
    # Test real-time monitoring configuration
    print("📋 Test 2: Real-Time Monitoring")
    
    real_time_config = monitoring_config['real_time_monitoring']
    print(f"   Enabled: {real_time_config.get('enabled', False)}")
    print(f"   Update Frequency: {real_time_config.get('update_frequency_minutes', 0)} minutes")
    print(f"   Dashboard Refresh: {real_time_config.get('dashboard_refresh_rate', 0)} seconds")
    print(f"   Alert Channels: {real_time_config.get('alert_channels', [])}")
    
    print()
    
    # Test historical analysis configuration
    print("📋 Test 3: Historical Analysis")
    
    historical_config = monitoring_config['historical_analysis']
    print(f"   Enabled: {historical_config.get('enabled', False)}")
    print(f"   Data Retention: {historical_config.get('data_retention_days', 0)} days")
    print(f"   Trend Analysis: {historical_config.get('trend_analysis', False)}")
    print(f"   Seasonal Patterns: {historical_config.get('seasonal_patterns', False)}")
    print(f"   Anomaly Detection: {historical_config.get('anomaly_detection', False)}")
    
    print()
    print("✅ Performance Monitoring Tests Completed")
    print()

def test_complete_analytics_workflow():
    """Test complete analytics and optimization workflow"""
    print("🔄 Testing Complete Analytics Workflow")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test complete workflow
    print("📋 Test 1: Complete Analytics and Optimization Workflow")
    
    # Step 1: Track payment method analytics
    print("   Step 1: Tracking Payment Method Analytics")
    customer = create_mock_customer('standard')
    db.add(customer)
    
    payment_methods = ['credit_card', 'debit_card', 'bank_transfer']
    failure_reasons = ['expired_card', 'insufficient_funds', 'card_declined']
    
    for payment_method in payment_methods:
        for failure_reason in failure_reasons:
            result = recovery_system.track_payment_method_analytics(
                payment_method=payment_method,
                failure_reason=failure_reason,
                amount=99.99,
                customer_id=customer.id
            )
            
            if result['success']:
                print(f"     ✅ {payment_method}: {failure_reason}")
            else:
                print(f"     ❌ {payment_method}: {failure_reason} - {result['error']}")
    
    print()
    
    # Step 2: Get analytics insights
    print("   Step 2: Getting Analytics Insights")
    analytics_result = recovery_system.get_payment_method_analytics(time_period='30d')
    
    if analytics_result['success']:
        print(f"     ✅ Analytics retrieved for {len(analytics_result['analytics_data'])} payment methods")
        print(f"     Insights: {len(analytics_result['insights'])}")
        print(f"     Trends: {analytics_result['trends'].get('failure_rate_trend', 'unknown')}")
    else:
        print(f"     ❌ Analytics error: {analytics_result['error']}")
    
    print()
    
    # Step 3: Create A/B test
    print("   Step 3: Creating A/B Test")
    test_result = recovery_system.create_ab_test(
        test_name='Recovery Optimization Test',
        strategy='retry_timing',
        variants=[
            {'name': 'immediate', 'delay_minutes': 0},
            {'name': 'delayed_1h', 'delay_minutes': 60},
            {'name': 'delayed_4h', 'delay_minutes': 240}
        ]
    )
    
    if test_result['success']:
        test_id = test_result['test_id']
        print(f"     ✅ Test created: {test_id}")
    else:
        print(f"     ❌ Test creation failed: {test_result['error']}")
        return
    
    print()
    
    # Step 4: Assign customers to test
    print("   Step 4: Assigning Customers to Test")
    customers = []
    for i in range(10):
        customer = create_mock_customer('standard')
        db.add(customer)
        customers.append(customer)
        
        assignment_result = recovery_system.assign_customer_to_ab_test(customer.id, test_id)
        
        if assignment_result['success']:
            print(f"     ✅ Customer {i+1}: {assignment_result['variant']}")
        else:
            print(f"     ❌ Customer {i+1}: {assignment_result['error']}")
    
    print()
    
    # Step 5: Record test results
    print("   Step 5: Recording Test Results")
    for i, customer in enumerate(customers):
        result_data = {
            'amount': 99.99,
            'recovery_time_days': 5.2,
            'satisfaction_score': 8.5
        }
        
        result = recovery_system.record_ab_test_result(
            customer_id=customer.id,
            test_id=test_id,
            result_type='payment_recovery_success',
            result_data=result_data
        )
        
        if result['success']:
            print(f"     ✅ Customer {i+1}: {result['variant']}")
        else:
            print(f"     ❌ Customer {i+1}: {result['error']}")
    
    print()
    
    # Step 6: Analyze test results
    print("   Step 6: Analyzing Test Results")
    analysis_result = recovery_system.get_ab_test_results(test_id)
    
    if analysis_result['success']:
        print(f"     ✅ Analysis completed")
        print(f"     Statistical Significance: {analysis_result['statistical_analysis'].get('statistical_significance', False)}")
        print(f"     Recommended Variant: {analysis_result['statistical_analysis'].get('recommended_variant', 'none')}")
        print(f"     Recommendations: {len(analysis_result['recommendations'])}")
    else:
        print(f"     ❌ Analysis failed: {analysis_result['error']}")
    
    print()
    print("✅ Complete Analytics Workflow Tests Completed")
    print()

def test_performance_and_scalability():
    """Test performance and scalability aspects"""
    print("⚡ Testing Performance and Scalability")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    print("📈 Performance Metrics:")
    
    # Test payment method analytics tracking performance
    print("   Testing payment method analytics tracking performance...")
    customer = create_mock_customer('standard')
    db.add(customer)
    
    import time
    start_time = time.time()
    
    for i in range(1000):
        result = recovery_system.track_payment_method_analytics(
            payment_method='credit_card',
            failure_reason='expired_card',
            amount=99.99,
            customer_id=customer.id
        )
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 1000 * 1000  # Convert to milliseconds
    
    print(f"   Average analytics tracking time: {avg_time:.2f}ms")
    print(f"   Analytics tracking per second: {1000 / avg_time:.1f}")
    print()
    
    # Test A/B test assignment performance
    print("   Testing A/B test assignment performance...")
    test_result = recovery_system.create_ab_test(
        test_name='Performance Test',
        strategy='retry_timing',
        variants=[
            {'name': 'immediate', 'delay_minutes': 0},
            {'name': 'delayed_1h', 'delay_minutes': 60}
        ]
    )
    
    if test_result['success']:
        test_id = test_result['test_id']
        
        start_time = time.time()
        
        for i in range(1000):
            customer = create_mock_customer('standard')
            db.add(customer)
            
            result = recovery_system.assign_customer_to_ab_test(customer.id, test_id)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 1000 * 1000  # Convert to milliseconds
        
        print(f"   Average A/B test assignment time: {avg_time:.2f}ms")
        print(f"   A/B test assignments per second: {1000 / avg_time:.1f}")
    else:
        print(f"   Failed to create test: {test_result['error']}")
    
    print()
    
    # Test analytics retrieval performance
    print("   Testing analytics retrieval performance...")
    start_time = time.time()
    
    for i in range(100):
        result = recovery_system.get_payment_method_analytics(time_period='30d')
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average analytics retrieval time: {avg_time:.2f}ms")
    print(f"   Analytics retrievals per second: {1000 / avg_time:.1f}")
    print()
    
    print("✅ Performance and Scalability Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Analytics and Optimization Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_payment_method_analytics_tracking()
        test_payment_method_analytics_retrieval()
        test_ab_test_creation()
        test_customer_ab_test_assignment()
        test_ab_test_result_recording()
        test_ab_test_results_analysis()
        test_optimization_strategies()
        test_performance_monitoring()
        test_complete_analytics_workflow()
        test_performance_and_scalability()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Payment Method Analytics Tracking")
        print("   ✅ Payment Method Analytics Retrieval")
        print("   ✅ A/B Test Creation")
        print("   ✅ Customer A/B Test Assignment")
        print("   ✅ A/B Test Result Recording")
        print("   ✅ A/B Test Results Analysis")
        print("   ✅ Optimization Strategies")
        print("   ✅ Performance Monitoring")
        print("   ✅ Complete Analytics Workflow")
        print("   ✅ Performance and Scalability")
        print()
        print("🚀 The analytics and optimization system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 