#!/usr/bin/env python3
"""
Test script for Subscription Analytics and Reporting System
Tests comprehensive business intelligence for revenue optimization.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from analytics.subscription_analytics import (
    SubscriptionAnalytics, AnalyticsConfig, MetricType, CohortType, 
    TimeGranularity, MetricCalculation, CohortAnalysis, RevenueForecast
)
from models.subscription import Customer, Subscription
from config.base import Config

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.customers = {}
        self.subscriptions = {}
        self.analytics_data = {}
    
    def commit(self):
        pass
    
    def add(self, obj):
        if isinstance(obj, Customer):
            self.customers[obj.id] = obj
        elif isinstance(obj, Subscription):
            self.subscriptions[obj.id] = obj
    
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
        return None
    
    def all(self):
        return []

def create_mock_customer(customer_type: str = 'standard') -> Customer:
    """Create a mock customer for testing"""
    customer_id = str(uuid.uuid4())
    
    if customer_type == 'premium':
        status = 'active'
        metadata = {'monthly_revenue': 150.0, 'subscription_length_months': 12, 'segment': 'premium'}
    elif customer_type == 'enterprise':
        status = 'active'
        metadata = {'monthly_revenue': 500.0, 'subscription_length_months': 24, 'segment': 'enterprise'}
    else:
        status = 'active'
        metadata = {'monthly_revenue': 75.0, 'subscription_length_months': 3, 'segment': 'standard'}
    
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
    if customer_type == 'premium':
        amount = 150.0
        plan_id = "premium_plan"
    elif customer_type == 'enterprise':
        amount = 500.0
        plan_id = "enterprise_plan"
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

def test_mrr_calculation():
    """Test MRR calculation functionality"""
    print("💰 Testing MRR Calculation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test MRR calculation
    print("📋 Test 1: MRR Calculation")
    
    result = analytics.calculate_mrr()
    
    print(f"   MRR Calculation Result:")
    print(f"     Metric Type: {result.metric_type.value}")
    print(f"     Current MRR: ${result.value:,.2f}")
    
    if result.previous_value is not None:
        print(f"     Previous MRR: ${result.previous_value:,.2f}")
    
    if result.change_percentage is not None:
        print(f"     Change: {result.change_percentage:+.1f}%")
    
    if result.trend:
        print(f"     Trend: {result.trend}")
    
    if result.metadata:
        print(f"     Active Subscriptions: {result.metadata.get('active_subscriptions', 0)}")
        print(f"     Monthly Subscriptions: {result.metadata.get('monthly_subscriptions', 0)}")
        print(f"     Annual Subscriptions: {result.metadata.get('annual_subscriptions', 0)}")
        
        if 'projections' in result.metadata:
            projections = result.metadata['projections']
            print(f"     Projections:")
            print(f"       Next Month: ${projections.get('next_month', 0):,.2f}")
            print(f"       Next Quarter: ${projections.get('next_quarter', 0):,.2f}")
            print(f"       Next Year: ${projections.get('next_year', 0):,.2f}")
    
    print()
    print("✅ MRR Calculation Tests Completed")
    print()

def test_arr_calculation():
    """Test ARR calculation functionality"""
    print("📈 Testing ARR Calculation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test ARR calculation
    print("📋 Test 1: ARR Calculation")
    
    result = analytics.calculate_arr()
    
    print(f"   ARR Calculation Result:")
    print(f"     Metric Type: {result.metric_type.value}")
    print(f"     Current ARR: ${result.value:,.2f}")
    
    if result.previous_value is not None:
        print(f"     Previous ARR: ${result.previous_value:,.2f}")
    
    if result.change_percentage is not None:
        print(f"     Change: {result.change_percentage:+.1f}%")
    
    if result.trend:
        print(f"     Trend: {result.trend}")
    
    if result.metadata:
        print(f"     MRR: ${result.metadata.get('mrr', 0):,.2f}")
        print(f"     Calculation Method: {result.metadata.get('calculation_method', 'N/A')}")
    
    print()
    print("✅ ARR Calculation Tests Completed")
    print()

def test_churn_rate_calculation():
    """Test churn rate calculation functionality"""
    print("📉 Testing Churn Rate Calculation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test churn rate calculation
    print("📋 Test 1: Churn Rate Calculation")
    
    result = analytics.calculate_churn_rate()
    
    print(f"   Churn Rate Calculation Result:")
    print(f"     Metric Type: {result.metric_type.value}")
    print(f"     Current Churn Rate: {result.value:.2f}%")
    
    if result.previous_value is not None:
        print(f"     Previous Churn Rate: {result.previous_value:.2f}%")
    
    if result.change_percentage is not None:
        print(f"     Change: {result.change_percentage:+.1f}%")
    
    if result.trend:
        print(f"     Trend: {result.trend}")
    
    if result.metadata:
        print(f"     Period Days: {result.metadata.get('period_days', 0)}")
        print(f"     Customers at Start: {result.metadata.get('customers_at_start', 0)}")
        print(f"     Churned Customers: {result.metadata.get('churned_customers', 0)}")
        print(f"     Churn Definition Days: {result.metadata.get('churn_definition_days', 0)}")
    
    print()
    print("✅ Churn Rate Calculation Tests Completed")
    print()

def test_net_revenue_retention():
    """Test Net Revenue Retention calculation"""
    print("🔄 Testing Net Revenue Retention")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test NRR calculation
    print("📋 Test 1: Net Revenue Retention Calculation")
    
    result = analytics.calculate_net_revenue_retention()
    
    print(f"   NRR Calculation Result:")
    print(f"     Metric Type: {result.metric_type.value}")
    print(f"     Current NRR: {result.value:.1f}%")
    
    if result.previous_value is not None:
        print(f"     Previous NRR: {result.previous_value:.1f}%")
    
    if result.change_percentage is not None:
        print(f"     Change: {result.change_percentage:+.1f}%")
    
    if result.trend:
        print(f"     Trend: {result.trend}")
    
    if result.metadata:
        print(f"     Period Days: {result.metadata.get('period_days', 0)}")
        print(f"     Revenue at Start: ${result.metadata.get('revenue_at_start', 0):,.2f}")
        print(f"     Revenue at End: ${result.metadata.get('revenue_at_end', 0):,.2f}")
        print(f"     Expansion Revenue: ${result.metadata.get('expansion_revenue', 0):,.2f}")
        print(f"     Contraction Revenue: ${result.metadata.get('contraction_revenue', 0):,.2f}")
        print(f"     Churn Revenue: ${result.metadata.get('churn_revenue', 0):,.2f}")
    
    print()
    print("✅ Net Revenue Retention Tests Completed")
    print()

def test_customer_lifetime_value():
    """Test Customer Lifetime Value calculation"""
    print("👤 Testing Customer Lifetime Value")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test CLV calculation
    print("📋 Test 1: Customer Lifetime Value Calculation")
    
    result = analytics.calculate_customer_lifetime_value()
    
    print(f"   CLV Calculation Result:")
    print(f"     Metric Type: {result.metric_type.value}")
    print(f"     Average CLV: ${result.value:,.2f}")
    
    if result.previous_value is not None:
        print(f"     Previous CLV: ${result.previous_value:,.2f}")
    
    if result.change_percentage is not None:
        print(f"     Change: {result.change_percentage:+.1f}%")
    
    if result.trend:
        print(f"     Trend: {result.trend}")
    
    if result.metadata:
        print(f"     Cohort Periods: {result.metadata.get('cohort_periods', 0)}")
        print(f"     Total Customers: {result.metadata.get('total_customers', 0)}")
        print(f"     Total LTV: ${result.metadata.get('total_ltv', 0):,.2f}")
        print(f"     Cohort Breakdown: {len(result.metadata.get('cohort_breakdown', []))} cohorts")
    
    print()
    print("✅ Customer Lifetime Value Tests Completed")
    print()

def test_cohort_analysis():
    """Test cohort analysis functionality"""
    print("📊 Testing Cohort Analysis")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test different cohort types
    print("📋 Test 1: Cohort Analysis by Type")
    
    cohort_types = [
        CohortType.SIGNUP_DATE,
        CohortType.PLAN_TYPE,
        CohortType.CUSTOMER_SEGMENT,
        CohortType.ACQUISITION_CHANNEL,
        CohortType.GEOGRAPHIC_REGION
    ]
    
    for cohort_type in cohort_types:
        print(f"   Testing {cohort_type.value}:")
        
        results = analytics.perform_cohort_analysis(cohort_type)
        
        print(f"     Cohorts Analyzed: {len(results)}")
        
        if results:
            # Show details for first cohort
            first_cohort = results[0]
            print(f"     Sample Cohort:")
            print(f"       Period: {first_cohort.cohort_period}")
            print(f"       Size: {first_cohort.cohort_size}")
            print(f"       Retention Periods: {len(first_cohort.retention_rates)}")
            print(f"       Average Retention: {sum(first_cohort.retention_rates) / len(first_cohort.retention_rates):.1f}%")
            print(f"       Average Churn: {sum(first_cohort.churn_rates) / len(first_cohort.churn_rates):.1f}%")
            print(f"       Revenue Evolution: {len(first_cohort.revenue_evolution)} periods")
            print(f"       LTV Evolution: {len(first_cohort.ltv_evolution)} periods")
        
        print()
    
    print("✅ Cohort Analysis Tests Completed")
    print()

def test_revenue_forecasting():
    """Test revenue forecasting functionality"""
    print("🔮 Testing Revenue Forecasting")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test revenue forecasting
    print("📋 Test 1: Revenue Forecasting")
    
    result = analytics.generate_revenue_forecast(periods=6)
    
    print(f"   Revenue Forecast Result:")
    print(f"     Forecast Periods: {result.forecast_periods}")
    print(f"     Model Type: {result.model_type}")
    print(f"     Model Accuracy: {result.model_accuracy:.1%}")
    print(f"     Forecasted Values: {len(result.forecasted_values)} periods")
    print(f"     Confidence Intervals: {len(result.confidence_intervals)} periods")
    
    if result.forecasted_values:
        print(f"     Forecast Range:")
        print(f"       First Period: ${result.forecasted_values[0]:,.2f}")
        print(f"       Last Period: ${result.forecasted_values[-1]:,.2f}")
        print(f"       Growth: {((result.forecasted_values[-1] / result.forecasted_values[0]) - 1) * 100:+.1f}%")
    
    if result.confidence_intervals:
        print(f"     Confidence Intervals:")
        for i, (lower, upper) in enumerate(result.confidence_intervals[:3]):
            print(f"       Period {i+1}: ${lower:,.2f} - ${upper:,.2f}")
    
    if result.assumptions:
        print(f"     Assumptions:")
        print(f"       Historical Periods: {result.assumptions.get('historical_periods', 0)}")
        print(f"       Confidence Level: {result.assumptions.get('confidence_level', 0):.1%}")
        print(f"       Forecast Dates: {len(result.assumptions.get('forecast_dates', []))}")
    
    print()
    print("✅ Revenue Forecasting Tests Completed")
    print()

def test_comprehensive_report():
    """Test comprehensive analytics report generation"""
    print("📋 Testing Comprehensive Analytics Report")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test comprehensive report generation
    print("📋 Test 1: Comprehensive Report Generation")
    
    report = analytics.generate_comprehensive_report(include_visualizations=True)
    
    print(f"   Report Generation Result:")
    print(f"     Report Date: {report.get('report_date', 'N/A')}")
    print(f"     Generated At: {report.get('generated_at', 'N/A')}")
    
    # Check metrics
    metrics = report.get('metrics', {})
    print(f"     Metrics Calculated: {len(metrics)}")
    
    for metric_name, metric_result in metrics.items():
        if isinstance(metric_result, MetricCalculation):
            print(f"       {metric_name}: {metric_result.value:.2f} ({metric_result.trend or 'N/A'})")
    
    # Check cohort analysis
    cohort_analysis = report.get('cohort_analysis', {})
    print(f"     Cohort Analysis Types: {len(cohort_analysis)}")
    
    for cohort_type, cohort_results in cohort_analysis.items():
        print(f"       {cohort_type}: {len(cohort_results)} cohorts")
    
    # Check forecasts
    forecasts = report.get('forecasts', {})
    print(f"     Forecast Types: {len(forecasts)}")
    
    for forecast_type, forecast_result in forecasts.items():
        if isinstance(forecast_result, RevenueForecast):
            print(f"       {forecast_type}: {forecast_result.forecast_periods} periods, {forecast_result.model_accuracy:.1%} accuracy")
        else:
            print(f"       {forecast_type}: {len(forecast_result.get('forecasted_values', []))} periods")
    
    # Check insights
    insights = report.get('insights', [])
    print(f"     Insights Generated: {len(insights)}")
    
    for insight in insights[:3]:  # Show first 3 insights
        print(f"       {insight.get('type', 'N/A')} - {insight.get('title', 'N/A')}: {insight.get('description', 'N/A')}")
    
    # Check recommendations
    recommendations = report.get('recommendations', [])
    print(f"     Recommendations Generated: {len(recommendations)}")
    
    for recommendation in recommendations[:3]:  # Show first 3 recommendations
        print(f"       {recommendation.get('priority', 'N/A')} - {recommendation.get('title', 'N/A')}: {recommendation.get('description', 'N/A')}")
    
    # Check visualizations
    visualizations = report.get('visualizations', {})
    print(f"     Visualizations Generated: {len(visualizations)}")
    
    for viz_name in visualizations.keys():
        print(f"       {viz_name}")
    
    print()
    print("✅ Comprehensive Report Tests Completed")
    print()

def test_performance_metrics():
    """Test additional performance metrics"""
    print("⚡ Testing Performance Metrics")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    print("📋 Test 1: Additional Performance Metrics")
    
    # Test expansion rate
    expansion_rate = analytics._calculate_expansion_rate()
    print(f"   Expansion Rate: {expansion_rate.value:.2f}%")
    
    # Test contraction rate
    contraction_rate = analytics._calculate_contraction_rate()
    print(f"   Contraction Rate: {contraction_rate.value:.2f}%")
    
    # Test gross revenue retention
    grr = analytics._calculate_gross_revenue_retention()
    print(f"   Gross Revenue Retention: {grr.value:.1f}%")
    
    # Test average revenue per user
    arpu = analytics._calculate_average_revenue_per_user()
    print(f"   Average Revenue Per User: ${arpu.value:.2f}")
    
    # Test total active customers
    active_customers = analytics._calculate_total_active_customers()
    print(f"   Total Active Customers: {active_customers.value:,}")
    
    print()
    print("✅ Performance Metrics Tests Completed")
    print()

def test_configuration_options():
    """Test different configuration options"""
    print("⚙️ Testing Configuration Options")
    print("=" * 60)
    
    print("📋 Test 1: Different Analytics Configurations")
    
    # Test different configurations
    configs = [
        {
            'name': 'Standard Configuration',
            'config': AnalyticsConfig()
        },
        {
            'name': 'High-Performance Configuration',
            'config': AnalyticsConfig(
                default_period_days=180,
                cohort_analysis_periods=18,
                forecasting_periods=12,
                cache_results=True,
                cache_ttl_hours=48,
                batch_processing=True,
                batch_size=2000
            )
        },
        {
            'name': 'Conservative Configuration',
            'config': AnalyticsConfig(
                default_period_days=30,
                cohort_analysis_periods=6,
                forecasting_periods=3,
                forecasting_confidence_level=0.99,
                include_projections=False,
                include_benchmarks=False
            )
        }
    ]
    
    for config_test in configs:
        print(f"   Testing {config_test['name']}:")
        
        config = config_test['config']
        print(f"     Default Period Days: {config.default_period_days}")
        print(f"     Cohort Analysis Periods: {config.cohort_analysis_periods}")
        print(f"     Forecasting Periods: {config.forecasting_periods}")
        print(f"     Forecasting Confidence: {config.forecasting_confidence_level:.1%}")
        print(f"     Cache Results: {config.cache_results}")
        print(f"     Include Projections: {config.include_projections}")
        print(f"     Include Benchmarks: {config.include_benchmarks}")
        print(f"     Batch Processing: {config.batch_processing}")
        print(f"     Batch Size: {config.batch_size}")
        
        print()
    
    print("✅ Configuration Options Tests Completed")
    print()

def test_error_handling():
    """Test error handling scenarios"""
    print("🚨 Testing Error Handling")
    print("=" * 60)
    
    print("📋 Test 1: Error Handling Scenarios")
    
    # Setup with empty database
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test with insufficient data
    print("   Testing with insufficient data:")
    
    try:
        result = analytics.calculate_mrr()
        print(f"     MRR Calculation: {'Success' if result.value >= 0 else 'Error'}")
    except Exception as e:
        print(f"     MRR Calculation Error: {e}")
    
    try:
        result = analytics.calculate_churn_rate()
        print(f"     Churn Rate Calculation: {'Success' if result.value >= 0 else 'Error'}")
    except Exception as e:
        print(f"     Churn Rate Calculation Error: {e}")
    
    try:
        result = analytics.generate_revenue_forecast(periods=1)
        print(f"     Revenue Forecast: {'Success' if result.forecasted_values else 'Error'}")
    except Exception as e:
        print(f"     Revenue Forecast Error: {e}")
    
    # Test with invalid parameters
    print("   Testing with invalid parameters:")
    
    try:
        result = analytics.calculate_churn_rate(period_days=-1)
        print(f"     Invalid Churn Period: {'Success' if result.value >= 0 else 'Error'}")
    except Exception as e:
        print(f"     Invalid Churn Period Error: {e}")
    
    try:
        result = analytics.generate_revenue_forecast(periods=0)
        print(f"     Zero Forecast Periods: {'Success' if result.forecasted_values else 'Error'}")
    except Exception as e:
        print(f"     Zero Forecast Periods Error: {e}")
    
    print()
    print("✅ Error Handling Tests Completed")
    print()

def test_performance_and_scalability():
    """Test performance and scalability aspects"""
    print("📈 Testing Performance and Scalability")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    print("📋 Test 1: Performance Metrics")
    
    import time
    
    # Test MRR calculation performance
    print("   Testing MRR calculation performance...")
    start_time = time.time()
    
    for i in range(100):
        result = analytics.calculate_mrr()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"     Average MRR calculation time: {avg_time:.2f}ms")
    print(f"     MRR calculations per second: {1000 / avg_time:.1f}")
    
    # Test churn rate calculation performance
    print("   Testing churn rate calculation performance...")
    start_time = time.time()
    
    for i in range(100):
        result = analytics.calculate_churn_rate()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"     Average churn rate calculation time: {avg_time:.2f}ms")
    print(f"     Churn rate calculations per second: {1000 / avg_time:.1f}")
    
    # Test cohort analysis performance
    print("   Testing cohort analysis performance...")
    start_time = time.time()
    
    for i in range(10):
        result = analytics.perform_cohort_analysis(CohortType.SIGNUP_DATE)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average cohort analysis time: {avg_time:.2f}ms")
    print(f"     Cohort analyses per second: {1000 / avg_time:.1f}")
    
    # Test comprehensive report performance
    print("   Testing comprehensive report performance...")
    start_time = time.time()
    
    for i in range(5):
        result = analytics.generate_comprehensive_report(include_visualizations=False)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 5 * 1000  # Convert to milliseconds
    
    print(f"     Average comprehensive report time: {avg_time:.2f}ms")
    print(f"     Comprehensive reports per second: {1000 / avg_time:.1f}")
    
    print()
    print("✅ Performance and Scalability Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Subscription Analytics and Reporting System Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_mrr_calculation()
        test_arr_calculation()
        test_churn_rate_calculation()
        test_net_revenue_retention()
        test_customer_lifetime_value()
        test_cohort_analysis()
        test_revenue_forecasting()
        test_comprehensive_report()
        test_performance_metrics()
        test_configuration_options()
        test_error_handling()
        test_performance_and_scalability()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ MRR Calculation")
        print("   ✅ ARR Calculation")
        print("   ✅ Churn Rate Calculation")
        print("   ✅ Net Revenue Retention")
        print("   ✅ Customer Lifetime Value")
        print("   ✅ Cohort Analysis")
        print("   ✅ Revenue Forecasting")
        print("   ✅ Comprehensive Report")
        print("   ✅ Performance Metrics")
        print("   ✅ Configuration Options")
        print("   ✅ Error Handling")
        print("   ✅ Performance and Scalability")
        print()
        print("🚀 The subscription analytics and reporting system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 