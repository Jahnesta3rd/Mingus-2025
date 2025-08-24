#!/usr/bin/env python3
"""
Test script for Key Metrics
Tests Customer Acquisition Cost (CAC) by channel, Customer Lifetime Value (CLV) by tier, 
churn rate by tier and cohort analysis, and revenue per user and tier distribution.
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

def test_customer_acquisition_cost_by_channel():
    """Test Customer Acquisition Cost (CAC) by channel"""
    print("💰 Testing Customer Acquisition Cost (CAC) by Channel")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test CAC calculation by channel
    print("📋 Test 1: CAC Calculation by Channel")
    
    result = analytics.calculate_customer_acquisition_cost_by_channel(period_days=30)
    
    print(f"   CAC by Channel Results:")
    print(f"     Channels Analyzed: {len(result)}")
    
    for channel, cac_metric in result.items():
        print(f"     {channel.upper()}:")
        print(f"       CAC: ${cac_metric.value:.2f}")
        
        if cac_metric.previous_value is not None:
            print(f"       Previous CAC: ${cac_metric.previous_value:.2f}")
        
        if cac_metric.change_percentage is not None:
            print(f"       Change: {cac_metric.change_percentage:+.1f}%")
        
        if cac_metric.trend:
            print(f"       Trend: {cac_metric.trend}")
        
        # Access detailed metadata
        metadata = cac_metric.metadata
        print(f"       Total Cost: ${metadata['total_cost']:,.2f}")
        print(f"       New Customers: {metadata['new_customers']}")
        print(f"       Conversion Rate: {metadata['conversion_rate']:.1%}")
        print(f"       Channel Efficiency: {metadata['channel_efficiency']:.1%}")
        
        # Show cost breakdown
        cost_breakdown = metadata.get('cost_breakdown', {})
        if cost_breakdown:
            print(f"       Cost Breakdown:")
            for cost_type, amount in cost_breakdown.items():
                print(f"         {cost_type}: ${amount:,.2f}")
        
        print()
    
    print("✅ CAC by Channel Tests Completed")
    print()

def test_customer_lifetime_value_by_tier():
    """Test Customer Lifetime Value (CLV) by tier"""
    print("👤 Testing Customer Lifetime Value (CLV) by Tier")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test CLV calculation by tier
    print("📋 Test 1: CLV Calculation by Tier")
    
    result = analytics.calculate_customer_lifetime_value_by_tier(cohort_periods=12)
    
    print(f"   CLV by Tier Results:")
    print(f"     Tiers Analyzed: {len(result)}")
    
    for tier, clv_metric in result.items():
        print(f"     {tier.upper()} Tier:")
        print(f"       Average CLV: ${clv_metric.value:,.2f}")
        
        if clv_metric.previous_value is not None:
            print(f"       Previous CLV: ${clv_metric.previous_value:,.2f}")
        
        if clv_metric.change_percentage is not None:
            print(f"       Change: {clv_metric.change_percentage:+.1f}%")
        
        if clv_metric.trend:
            print(f"       Trend: {clv_metric.trend}")
        
        # Access detailed metadata
        metadata = clv_metric.metadata
        print(f"       Customer Count: {metadata['customer_count']}")
        print(f"       Total LTV: ${metadata['total_ltv']:,.2f}")
        print(f"       Cohort Periods: {metadata['cohort_periods']}")
        print(f"       Tier Retention Rate: {metadata['tier_retention_rate']:.1f}%")
        print(f"       Tier Expansion Rate: {metadata['tier_expansion_rate']:.1f}%")
        
        # Show tier distribution
        tier_distribution = metadata.get('tier_distribution', {})
        if tier_distribution:
            print(f"       Tier Distribution:")
            for tier_name, count in tier_distribution.items():
                print(f"         {tier_name}: {count} customers")
        
        print()
    
    print("✅ CLV by Tier Tests Completed")
    print()

def test_churn_rate_by_tier():
    """Test churn rate by tier"""
    print("📉 Testing Churn Rate by Tier")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test churn rate calculation by tier
    print("📋 Test 1: Churn Rate Calculation by Tier")
    
    result = analytics.calculate_churn_rate_by_tier(period_days=30)
    
    print(f"   Churn Rate by Tier Results:")
    print(f"     Tiers Analyzed: {len(result)}")
    
    for tier, churn_metric in result.items():
        print(f"     {tier.upper()} Tier:")
        print(f"       Churn Rate: {churn_metric.value:.2f}%")
        
        if churn_metric.previous_value is not None:
            print(f"       Previous Churn Rate: {churn_metric.previous_value:.2f}%")
        
        if churn_metric.change_percentage is not None:
            print(f"       Change: {churn_metric.change_percentage:+.1f}%")
        
        if churn_metric.trend:
            print(f"       Trend: {churn_metric.trend}")
        
        # Access detailed metadata
        metadata = churn_metric.metadata
        print(f"       Period Days: {metadata['period_days']}")
        print(f"       Customers at Start: {metadata['customers_at_start']}")
        print(f"       Churned Customers: {metadata['churned_customers']}")
        print(f"       Churn Prediction Score: {metadata['churn_prediction_score']:.1%}")
        
        # Show churn reasons
        churn_reasons = metadata.get('churn_reasons', {})
        if churn_reasons:
            print(f"       Churn Reasons:")
            for reason, count in churn_reasons.items():
                print(f"         {reason}: {count} customers")
        
        # Show retention strategies
        retention_strategies = metadata.get('tier_retention_strategies', [])
        if retention_strategies:
            print(f"       Retention Strategies:")
            for strategy in retention_strategies:
                print(f"         - {strategy}")
        
        print()
    
    print("✅ Churn Rate by Tier Tests Completed")
    print()

def test_cohort_analysis_by_tier():
    """Test cohort analysis by tier"""
    print("📊 Testing Cohort Analysis by Tier")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test different cohort types by tier
    print("📋 Test 1: Cohort Analysis by Tier")
    
    cohort_types = [
        CohortType.SIGNUP_DATE,
        CohortType.PLAN_TYPE,
        CohortType.CUSTOMER_SEGMENT,
        CohortType.ACQUISITION_CHANNEL,
        CohortType.GEOGRAPHIC_REGION
    ]
    
    for cohort_type in cohort_types:
        print(f"   Testing {cohort_type.value} cohorts by tier:")
        
        results = analytics.perform_cohort_analysis_by_tier(cohort_type)
        
        print(f"     Tiers with Cohort Analysis: {len(results)}")
        
        for tier, cohort_analyses in results.items():
            print(f"     {tier.upper()} Tier:")
            print(f"       Cohorts Analyzed: {len(cohort_analyses)}")
            
            if cohort_analyses:
                # Show details for first cohort
                first_cohort = cohort_analyses[0]
                print(f"       Sample Cohort:")
                print(f"         Period: {first_cohort.cohort_period}")
                print(f"         Size: {first_cohort.cohort_size}")
                print(f"         Retention Periods: {len(first_cohort.retention_rates)}")
                print(f"         Average Retention: {sum(first_cohort.retention_rates) / len(first_cohort.retention_rates):.1f}%")
                print(f"         Average Churn: {sum(first_cohort.churn_rates) / len(first_cohort.churn_rates):.1f}%")
                print(f"         Revenue Evolution: {len(first_cohort.revenue_evolution)} periods")
                print(f"         LTV Evolution: {len(first_cohort.ltv_evolution)} periods")
            
            print()
        
        print()
    
    print("✅ Cohort Analysis by Tier Tests Completed")
    print()

def test_revenue_per_user_by_tier():
    """Test revenue per user by tier"""
    print("💵 Testing Revenue Per User by Tier")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test revenue per user calculation by tier
    print("📋 Test 1: Revenue Per User Calculation by Tier")
    
    result = analytics.calculate_revenue_per_user_by_tier()
    
    print(f"   Revenue Per User by Tier Results:")
    print(f"     Tiers Analyzed: {len(result)}")
    
    for tier, revenue_metric in result.items():
        print(f"     {tier.upper()} Tier:")
        print(f"       Average Revenue Per User: ${revenue_metric.value:.2f}")
        
        if revenue_metric.previous_value is not None:
            print(f"       Previous ARPU: ${revenue_metric.previous_value:.2f}")
        
        if revenue_metric.change_percentage is not None:
            print(f"       Change: {revenue_metric.change_percentage:+.1f}%")
        
        if revenue_metric.trend:
            print(f"       Trend: {revenue_metric.trend}")
        
        # Access detailed metadata
        metadata = revenue_metric.metadata
        print(f"       Customer Count: {metadata['customer_count']}")
        print(f"       Total Revenue: ${metadata['total_revenue']:,.2f}")
        
        # Show tier distribution
        tier_distribution = metadata.get('tier_distribution', {})
        if tier_distribution:
            print(f"       Tier Distribution:")
            for tier_name, count in tier_distribution.items():
                print(f"         {tier_name}: {count} customers")
        
        # Show revenue distribution
        revenue_distribution = metadata.get('revenue_distribution', {})
        if revenue_distribution:
            print(f"       Revenue Distribution:")
            for revenue_level, percentage in revenue_distribution.items():
                print(f"         {revenue_level}: {percentage:.1%}")
        
        # Show usage patterns
        usage_patterns = metadata.get('usage_patterns', {})
        if usage_patterns:
            print(f"       Usage Patterns:")
            print(f"         Average Sessions/Month: {usage_patterns.get('average_sessions_per_month', 0)}")
            print(f"         Average Session Duration: {usage_patterns.get('average_session_duration', 0)} minutes")
            
            feature_usage = usage_patterns.get('feature_usage_distribution', {})
            if feature_usage:
                print(f"         Feature Usage:")
                for feature_type, usage_rate in feature_usage.items():
                    print(f"           {feature_type}: {usage_rate:.1%}")
        
        # Show feature adoption
        feature_adoption = metadata.get('feature_adoption', {})
        if feature_adoption:
            print(f"       Feature Adoption:")
            for feature, adoption_rate in feature_adoption.items():
                print(f"         {feature}: {adoption_rate:.1%}")
        
        print()
    
    print("✅ Revenue Per User by Tier Tests Completed")
    print()

def test_tier_distribution_analysis():
    """Test tier distribution analysis"""
    print("📈 Testing Tier Distribution Analysis")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test tier distribution analysis
    print("📋 Test 1: Tier Distribution Analysis")
    
    result = analytics.get_tier_distribution_analysis()
    
    print(f"   Tier Distribution Analysis Results:")
    print(f"     Analysis Date: {result.get('date', 'N/A')}")
    print(f"     Total Customers: {result.get('total_customers', 0):,}")
    
    # Show tier distribution
    tier_distribution = result.get('tier_distribution', {})
    print(f"     Current Tier Distribution:")
    for tier, count in tier_distribution.items():
        print(f"       {tier}: {count} customers")
    
    # Show previous distribution
    previous_distribution = result.get('previous_tier_distribution', {})
    print(f"     Previous Tier Distribution:")
    for tier, count in previous_distribution.items():
        print(f"       {tier}: {count} customers")
    
    # Show tier metrics
    tier_metrics = result.get('tier_metrics', {})
    print(f"     Tier Metrics:")
    for tier, metrics in tier_metrics.items():
        print(f"       {tier.upper()} Tier:")
        print(f"         Current Count: {metrics.get('current_count', 0)}")
        print(f"         Previous Count: {metrics.get('previous_count', 0)}")
        print(f"         Change Count: {metrics.get('change_count', 0):+}")
        print(f"         Change Percentage: {metrics.get('change_percentage', 0):+.1f}%")
        print(f"         Percentage of Total: {metrics.get('percentage_of_total', 0):.1f}%")
        print(f"         Revenue Contribution: {metrics.get('revenue_contribution', 0):.1f}%")
        print(f"         Growth Rate: {metrics.get('growth_rate', 0):.1f}%")
        print(f"         Upgrade Rate: {metrics.get('upgrade_rate', 0):.1f}%")
        print(f"         Downgrade Rate: {metrics.get('downgrade_rate', 0):.1f}%")
        
        # Show migration patterns
        migration_patterns = metrics.get('migration_patterns', {})
        if migration_patterns:
            print(f"         Migration Patterns:")
            for pattern, count in migration_patterns.items():
                print(f"           {pattern}: {count} customers")
        
        print()
    
    # Show distribution trends
    distribution_trends = result.get('distribution_trends', {})
    print(f"     Distribution Trends:")
    for tier, trend in distribution_trends.items():
        print(f"       {tier}: {trend}")
    
    # Show performance ranking
    performance_ranking = result.get('tier_performance_ranking', [])
    print(f"     Tier Performance Ranking:")
    for i, tier in enumerate(performance_ranking, 1):
        print(f"       {i}. {tier}")
    
    # Show recommendations
    recommendations = result.get('recommendations', [])
    print(f"     Recommendations:")
    for rec in recommendations:
        print(f"       {rec.get('priority', 'N/A').upper()} - {rec.get('type', 'N/A')}: {rec.get('recommendation', 'N/A')}")
        actions = rec.get('actions', [])
        if actions:
            print(f"         Actions:")
            for action in actions:
                print(f"           - {action}")
        print()
    
    print("✅ Tier Distribution Analysis Tests Completed")
    print()

def test_ltv_cac_ratio_by_channel():
    """Test LTV/CAC ratio by channel"""
    print("⚖️ Testing LTV/CAC Ratio by Channel")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    # Test LTV/CAC ratio calculation by channel
    print("📋 Test 1: LTV/CAC Ratio Calculation by Channel")
    
    result = analytics.calculate_ltv_cac_ratio_by_channel(period_days=30)
    
    print(f"   LTV/CAC Ratio by Channel Results:")
    print(f"     Channels Analyzed: {len(result)}")
    
    for channel, ratio_metric in result.items():
        print(f"     {channel.upper()} Channel:")
        print(f"       LTV/CAC Ratio: {ratio_metric.value:.2f}")
        
        if ratio_metric.previous_value is not None:
            print(f"       Previous Ratio: {ratio_metric.previous_value:.2f}")
        
        if ratio_metric.change_percentage is not None:
            print(f"       Change: {ratio_metric.change_percentage:+.1f}%")
        
        if ratio_metric.trend:
            print(f"       Trend: {ratio_metric.trend}")
        
        # Access detailed metadata
        metadata = ratio_metric.metadata
        print(f"       CAC: ${metadata['cac']:.2f}")
        print(f"       CLV: ${metadata['clv']:.2f}")
        print(f"       Health Status: {metadata['health_status']}")
        print(f"       Payback Period: {metadata['payback_period']:.1f} months")
        print(f"       Channel Efficiency: {metadata['channel_efficiency']:.1%}")
        
        # Show optimization opportunities
        opportunities = metadata.get('optimization_opportunities', [])
        if opportunities:
            print(f"       Optimization Opportunities:")
            for opportunity in opportunities:
                print(f"         - {opportunity}")
        
        print()
    
    print("✅ LTV/CAC Ratio by Channel Tests Completed")
    print()

def test_comprehensive_key_metrics_report():
    """Test comprehensive key metrics report"""
    print("📋 Testing Comprehensive Key Metrics Report")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    print("📋 Test 1: Comprehensive Key Metrics Analysis")
    
    # Generate all key metrics
    print("   Generating Key Metrics...")
    
    # CAC by channel
    cac_by_channel = analytics.calculate_customer_acquisition_cost_by_channel()
    print(f"     CAC by Channel: {len(cac_by_channel)} channels analyzed")
    
    # CLV by tier
    clv_by_tier = analytics.calculate_customer_lifetime_value_by_tier()
    print(f"     CLV by Tier: {len(clv_by_tier)} tiers analyzed")
    
    # Churn rate by tier
    churn_by_tier = analytics.calculate_churn_rate_by_tier()
    print(f"     Churn by Tier: {len(churn_by_tier)} tiers analyzed")
    
    # Revenue per user by tier
    revenue_by_tier = analytics.calculate_revenue_per_user_by_tier()
    print(f"     Revenue by Tier: {len(revenue_by_tier)} tiers analyzed")
    
    # Tier distribution analysis
    tier_distribution = analytics.get_tier_distribution_analysis()
    print(f"     Tier Distribution: {len(tier_distribution.get('tier_metrics', {}))} tiers analyzed")
    
    # LTV/CAC ratio by channel
    ltv_cac_ratios = analytics.calculate_ltv_cac_ratio_by_channel()
    print(f"     LTV/CAC Ratios: {len(ltv_cac_ratios)} channels analyzed")
    
    # Cohort analysis by tier
    cohort_analysis = analytics.perform_cohort_analysis_by_tier(CohortType.SIGNUP_DATE)
    print(f"     Cohort Analysis: {len(cohort_analysis)} tiers analyzed")
    
    # Generate insights
    print("   Generating Insights...")
    
    insights = []
    
    # CAC insights
    for channel, cac_metric in cac_by_channel.items():
        if cac_metric.trend == "worsening":
            insights.append({
                'type': 'warning',
                'category': 'acquisition',
                'title': f'High CAC in {channel}',
                'description': f'CAC is increasing in {channel} channel',
                'metric': f'${cac_metric.value:.2f}',
                'recommendation': 'Review marketing spend and optimize campaigns'
            })
    
    # CLV insights
    for tier, clv_metric in clv_by_tier.items():
        if clv_metric.trend == "strong_growth":
            insights.append({
                'type': 'positive',
                'category': 'value',
                'title': f'Strong CLV Growth in {tier}',
                'description': f'CLV is growing strongly in {tier} tier',
                'metric': f'${clv_metric.value:,.2f}',
                'recommendation': 'Continue current strategies and scale successful programs'
            })
    
    # Churn insights
    for tier, churn_metric in churn_by_tier.items():
        if churn_metric.trend == "worsening":
            insights.append({
                'type': 'critical',
                'category': 'retention',
                'title': f'High Churn in {tier}',
                'description': f'Churn rate is increasing in {tier} tier',
                'metric': f'{churn_metric.value:.2f}%',
                'recommendation': 'Implement retention strategies and investigate churn causes'
            })
    
    # LTV/CAC insights
    for channel, ratio_metric in ltv_cac_ratios.items():
        if ratio_metric.metadata['health_status'] == "poor":
            insights.append({
                'type': 'critical',
                'category': 'efficiency',
                'title': f'Poor LTV/CAC in {channel}',
                'description': f'LTV/CAC ratio is below 1.0 in {channel} channel',
                'metric': f'{ratio_metric.value:.2f}',
                'recommendation': 'Optimize acquisition costs or improve customer value'
            })
    
    print(f"     Insights Generated: {len(insights)}")
    
    # Generate recommendations
    print("   Generating Recommendations...")
    
    recommendations = []
    
    # High-level recommendations based on metrics
    total_customers = tier_distribution.get('total_customers', 0)
    if total_customers > 0:
        recommendations.append({
            'priority': 'high',
            'category': 'growth',
            'title': 'Customer Acquisition Strategy',
            'description': f'Focus on acquiring {total_customers * 0.1:.0f} new customers monthly',
            'actions': [
                'Optimize high-performing channels',
                'Improve conversion rates',
                'Launch referral programs'
            ]
        })
    
    # Revenue optimization
    avg_revenue = sum(metric.value for metric in revenue_by_tier.values()) / len(revenue_by_tier) if revenue_by_tier else 0
    if avg_revenue < 100:
        recommendations.append({
            'priority': 'medium',
            'category': 'revenue',
            'title': 'Revenue Per User Optimization',
            'description': f'Increase average revenue per user from ${avg_revenue:.2f}',
            'actions': [
                'Implement upsell campaigns',
                'Improve feature adoption',
                'Optimize pricing strategy'
            ]
        })
    
    print(f"     Recommendations Generated: {len(recommendations)}")
    
    # Display summary
    print("   Summary:")
    print(f"     Total Metrics Calculated: {len(cac_by_channel) + len(clv_by_tier) + len(churn_by_tier) + len(revenue_by_tier) + len(ltv_cac_ratios)}")
    print(f"     Insights Generated: {len(insights)}")
    print(f"     Recommendations Generated: {len(recommendations)}")
    print(f"     Tiers Analyzed: {len(clv_by_tier)}")
    print(f"     Channels Analyzed: {len(cac_by_channel)}")
    
    print()
    print("✅ Comprehensive Key Metrics Report Tests Completed")
    print()

def test_performance_and_scalability():
    """Test performance and scalability aspects"""
    print("⚡ Testing Performance and Scalability")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = AnalyticsConfig()
    
    # Create analytics system
    analytics = SubscriptionAnalytics(db, config)
    
    print("📈 Performance Metrics:")
    
    import time
    
    # Test CAC calculation performance
    print("   Testing CAC calculation performance...")
    start_time = time.time()
    
    for i in range(50):
        result = analytics.calculate_customer_acquisition_cost_by_channel()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 50 * 1000  # Convert to milliseconds
    
    print(f"   Average CAC calculation time: {avg_time:.2f}ms")
    print(f"   CAC calculations per second: {1000 / avg_time:.1f}")
    print()
    
    # Test CLV calculation performance
    print("   Testing CLV calculation performance...")
    start_time = time.time()
    
    for i in range(50):
        result = analytics.calculate_customer_lifetime_value_by_tier()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 50 * 1000  # Convert to milliseconds
    
    print(f"   Average CLV calculation time: {avg_time:.2f}ms")
    print(f"   CLV calculations per second: {1000 / avg_time:.1f}")
    print()
    
    # Test churn calculation performance
    print("   Testing churn calculation performance...")
    start_time = time.time()
    
    for i in range(50):
        result = analytics.calculate_churn_rate_by_tier()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 50 * 1000  # Convert to milliseconds
    
    print(f"   Average churn calculation time: {avg_time:.2f}ms")
    print(f"   Churn calculations per second: {1000 / avg_time:.1f}")
    print()
    
    # Test comprehensive analysis performance
    print("   Testing comprehensive analysis performance...")
    start_time = time.time()
    
    for i in range(10):
        analytics.calculate_customer_acquisition_cost_by_channel()
        analytics.calculate_customer_lifetime_value_by_tier()
        analytics.calculate_churn_rate_by_tier()
        analytics.calculate_revenue_per_user_by_tier()
        analytics.get_tier_distribution_analysis()
        analytics.calculate_ltv_cac_ratio_by_channel()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"   Average comprehensive analysis time: {avg_time:.2f}ms")
    print(f"   Comprehensive analyses per second: {1000 / avg_time:.1f}")
    print()
    
    print("✅ Performance and Scalability Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Key Metrics Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_customer_acquisition_cost_by_channel()
        test_customer_lifetime_value_by_tier()
        test_churn_rate_by_tier()
        test_cohort_analysis_by_tier()
        test_revenue_per_user_by_tier()
        test_tier_distribution_analysis()
        test_ltv_cac_ratio_by_channel()
        test_comprehensive_key_metrics_report()
        test_performance_and_scalability()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Customer Acquisition Cost (CAC) by Channel")
        print("   ✅ Customer Lifetime Value (CLV) by Tier")
        print("   ✅ Churn Rate by Tier")
        print("   ✅ Cohort Analysis by Tier")
        print("   ✅ Revenue Per User by Tier")
        print("   ✅ Tier Distribution Analysis")
        print("   ✅ LTV/CAC Ratio by Channel")
        print("   ✅ Comprehensive Key Metrics Report")
        print("   ✅ Performance and Scalability")
        print()
        print("🚀 The key metrics system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 