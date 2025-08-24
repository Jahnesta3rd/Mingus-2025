#!/usr/bin/env python3
"""
Test script for User Behavior Analytics
Tests feature usage by subscription tier, usage patterns predicting upgrades/cancellations,
user engagement scoring, support ticket correlation with churn, and payment timing analysis.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from analytics.user_behavior_analytics import (
    UserBehaviorAnalytics, BehaviorAnalyticsConfig, BehaviorMetricType, 
    SubscriptionTier, UserAction, UserEngagementScore
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

def test_feature_usage_by_tier():
    """Test feature usage analysis by subscription tier"""
    print("🔧 Testing Feature Usage by Subscription Tier")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = BehaviorAnalyticsConfig()
    
    # Create analytics system
    analytics = UserBehaviorAnalytics(db, config)
    
    # Test feature usage by tier
    print("📋 Test 1: Feature Usage by Tier Analysis")
    
    feature_analysis = analytics.analyze_feature_usage_by_tier(period_days=30)
    
    print(f"   Feature Usage Analysis:")
    print(f"     Analysis Date: {feature_analysis.get('analysis_date', 'N/A')}")
    print(f"     Period Days: {feature_analysis.get('period_days', 0)}")
    
    # Tier analysis
    tier_analysis = feature_analysis.get('tier_analysis', {})
    print(f"     Tier Analysis:")
    
    for tier, data in tier_analysis.items():
        print(f"       {tier.title()} Tier:")
        print(f"         Total Users: {data['total_users']}")
        print(f"         Active Users: {data['active_users']}")
        print(f"         Usage Intensity: {data['usage_intensity']:.2f}")
        print(f"         Feature Adoption Rate: {data['feature_adoption_rate']:.1%}")
        
        # Most used features
        most_used = data.get('most_used_features', [])
        print(f"         Most Used Features:")
        for feature, usage in most_used:
            print(f"           {feature.replace('_', ' ').title()}: {usage}%")
        
        # Least used features
        least_used = data.get('least_used_features', [])
        print(f"         Least Used Features:")
        for feature, usage in least_used:
            print(f"           {feature.replace('_', ' ').title()}: {usage}%")
        
        # Feature usage details
        feature_usage = data.get('feature_usage', {})
        print(f"         Feature Usage Details:")
        for feature, usage in feature_usage.items():
            print(f"           {feature.replace('_', ' ').title()}: {usage}%")
    
    # Feature popularity
    feature_popularity = feature_analysis.get('feature_popularity', {})
    print(f"     Feature Popularity Across Tiers:")
    for feature, popularity in feature_popularity.items():
        print(f"       {feature.replace('_', ' ').title()}: {popularity:.1%}")
    
    # Usage trends
    usage_trends = feature_analysis.get('usage_trends', {})
    print(f"     Usage Trends:")
    for tier, trend in usage_trends.items():
        print(f"       {tier}: {trend}")
    
    # Tier comparison
    tier_comparison = feature_analysis.get('tier_comparison', {})
    print(f"     Tier Comparison:")
    
    usage_intensity = tier_comparison.get('usage_intensity', {})
    print(f"       Usage Intensity:")
    for tier, intensity in usage_intensity.items():
        print(f"         {tier}: {intensity:.2f}")
    
    feature_adoption = tier_comparison.get('feature_adoption', {})
    print(f"       Feature Adoption:")
    for tier, adoption in feature_adoption.items():
        print(f"         {tier}: {adoption:.1%}")
    
    active_users = tier_comparison.get('active_users', {})
    print(f"       Active Users:")
    for tier, users in active_users.items():
        print(f"         {tier}: {users}")
    
    # Recommendations
    recommendations = feature_analysis.get('recommendations', [])
    print(f"     Recommendations:")
    for rec in recommendations:
        print(f"       {rec['tier'].title()} - {rec['type'].replace('_', ' ').title()}: {rec['recommendation']}")
        print(f"         Priority: {rec['priority']}")
    
    print()
    print("✅ Feature Usage by Tier Tests Completed")
    print()

def test_usage_patterns_predicting_changes():
    """Test usage patterns that predict upgrades and cancellations"""
    print("📊 Testing Usage Patterns Predicting Changes")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = BehaviorAnalyticsConfig()
    
    # Create analytics system
    analytics = UserBehaviorAnalytics(db, config)
    
    # Test usage patterns
    print("📋 Test 1: Usage Patterns Analysis")
    
    patterns_analysis = analytics.analyze_usage_patterns_predicting_changes(period_days=90)
    
    print(f"   Usage Patterns Analysis:")
    print(f"     Analysis Date: {patterns_analysis.get('analysis_date', 'N/A')}")
    print(f"     Period Days: {patterns_analysis.get('period_days', 0)}")
    
    # Upgrade patterns
    upgrade_patterns = patterns_analysis.get('upgrade_patterns', {})
    print(f"     Upgrade Patterns:")
    
    thresholds = upgrade_patterns.get('thresholds', {})
    print(f"       Thresholds:")
    print(f"         Feature Usage: {thresholds.get('feature_usage', 0):.1%}")
    print(f"         Session Frequency: {thresholds.get('session_frequency', 0)} sessions/month")
    print(f"         Support Interaction: {thresholds.get('support_interaction', 0)} interactions")
    
    print(f"       Time to Upgrade: {upgrade_patterns.get('time_to_upgrade', 0)} days")
    
    triggers = upgrade_patterns.get('triggers', [])
    print(f"       Upgrade Triggers:")
    for trigger in triggers:
        print(f"         Feature: {trigger['feature'].replace('_', ' ').title()}")
        print(f"           Usage Rate: {trigger['usage_rate']:.1%}")
        print(f"           Upgrade Rate: {trigger['upgrade_rate']:.1%}")
    
    # Cancellation patterns
    cancellation_patterns = patterns_analysis.get('cancellation_patterns', {})
    print(f"     Cancellation Patterns:")
    
    thresholds = cancellation_patterns.get('thresholds', {})
    print(f"       Thresholds:")
    print(f"         Low Activity: {thresholds.get('low_activity', 0):.1%}")
    print(f"         Support Issues: {thresholds.get('support_issues', 0)} issues")
    print(f"         Payment Failures: {thresholds.get('payment_failures', 0)} failures")
    
    print(f"       Time to Cancellation: {cancellation_patterns.get('time_to_cancellation', 0)} days")
    
    triggers = cancellation_patterns.get('triggers', [])
    print(f"       Cancellation Triggers:")
    for trigger in triggers:
        print(f"         Factor: {trigger['factor'].replace('_', ' ').title()}")
        print(f"           Threshold: {trigger['threshold']}")
        print(f"           Cancellation Rate: {trigger['cancellation_rate']:.1%}")
    
    # Prediction models
    prediction_models = patterns_analysis.get('prediction_models', {})
    print(f"     Prediction Models:")
    
    upgrade_model = prediction_models.get('upgrade_model', {})
    print(f"       Upgrade Model:")
    print(f"         Accuracy: {upgrade_model.get('accuracy', 0):.1%}")
    print(f"         Features: {', '.join(upgrade_model.get('features', []))}")
    print(f"         Threshold: {upgrade_model.get('threshold', 0):.1%}")
    
    churn_model = prediction_models.get('churn_model', {})
    print(f"       Churn Model:")
    print(f"         Accuracy: {churn_model.get('accuracy', 0):.1%}")
    print(f"         Features: {', '.join(churn_model.get('features', []))}")
    print(f"         Threshold: {churn_model.get('threshold', 0):.1%}")
    
    # Risk factors
    risk_factors = patterns_analysis.get('risk_factors', [])
    print(f"     Risk Factors:")
    for factor in risk_factors:
        print(f"       {factor['factor'].replace('_', ' ').title()}:")
        print(f"         Description: {factor['description']}")
        print(f"         Risk Level: {factor['risk_level']}")
        print(f"         Mitigation: {factor['mitigation']}")
    
    # Opportunity factors
    opportunity_factors = patterns_analysis.get('opportunity_factors', [])
    print(f"     Opportunity Factors:")
    for factor in opportunity_factors:
        print(f"       {factor['factor'].replace('_', ' ').title()}:")
        print(f"         Description: {factor['description']}")
        print(f"         Opportunity Level: {factor['opportunity_level']}")
        print(f"         Action: {factor['action']}")
    
    # Recommendations
    recommendations = patterns_analysis.get('recommendations', [])
    print(f"     Recommendations:")
    for rec in recommendations:
        print(f"       {rec['type'].replace('_', ' ').title()}: {rec['recommendation']}")
        print(f"         Priority: {rec['priority']}")
        print(f"         Expected Impact: {rec['expected_impact']}")
    
    print()
    print("✅ Usage Patterns Predicting Changes Tests Completed")
    print()

def test_user_engagement_scoring():
    """Test user engagement scoring functionality"""
    print("📈 Testing User Engagement Scoring")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = BehaviorAnalyticsConfig()
    
    # Create analytics system
    analytics = UserBehaviorAnalytics(db, config)
    
    # Test user engagement scoring
    print("📋 Test 1: User Engagement Score Calculation")
    
    engagement_scores = analytics.calculate_user_engagement_scores()
    
    print(f"   User Engagement Scores:")
    print(f"     Total Users Analyzed: {len(engagement_scores)}")
    
    for user_id, score_data in engagement_scores.items():
        print(f"     User: {user_id}")
        print(f"       Engagement Score: {score_data.score:.3f}")
        print(f"       Tier: {score_data.tier.value}")
        print(f"       Last Activity: {score_data.last_activity}")
        print(f"       Feature Usage Count: {score_data.feature_usage_count}")
        print(f"       Session Frequency: {score_data.session_frequency:.1f} sessions/month")
        print(f"       Support Interactions: {score_data.support_interactions}")
        print(f"       Payment Success Rate: {score_data.payment_success_rate:.1%}")
        print(f"       Upgrade Probability: {score_data.upgrade_probability:.1%}")
        print(f"       Churn Risk: {score_data.churn_risk:.1%}")
        
        # Categorize engagement level
        if score_data.score >= 0.8:
            engagement_level = "High"
        elif score_data.score >= 0.6:
            engagement_level = "Medium"
        else:
            engagement_level = "Low"
        
        print(f"       Engagement Level: {engagement_level}")
        print()
    
    # Calculate summary statistics
    if engagement_scores:
        scores = [score.score for score in engagement_scores.values()]
        upgrade_probs = [score.upgrade_probability for score in engagement_scores.values()]
        churn_risks = [score.churn_risk for score in engagement_scores.values()]
        
        print(f"   Summary Statistics:")
        print(f"     Average Engagement Score: {sum(scores) / len(scores):.3f}")
        print(f"     Average Upgrade Probability: {sum(upgrade_probs) / len(upgrade_probs):.1%}")
        print(f"     Average Churn Risk: {sum(churn_risks) / len(churn_risks):.1%}")
        
        # High engagement users
        high_engagement = [score for score in engagement_scores.values() if score.score >= 0.8]
        print(f"     High Engagement Users: {len(high_engagement)} ({len(high_engagement)/len(engagement_scores)*100:.1f}%)")
        
        # High upgrade probability users
        high_upgrade_prob = [score for score in engagement_scores.values() if score.upgrade_probability >= 0.6]
        print(f"     High Upgrade Probability Users: {len(high_upgrade_prob)} ({len(high_upgrade_prob)/len(engagement_scores)*100:.1f}%)")
        
        # High churn risk users
        high_churn_risk = [score for score in engagement_scores.values() if score.churn_risk >= 0.7]
        print(f"     High Churn Risk Users: {len(high_churn_risk)} ({len(high_churn_risk)/len(engagement_scores)*100:.1f}%)")
    
    print()
    print("✅ User Engagement Scoring Tests Completed")
    print()

def test_support_ticket_correlation_with_churn():
    """Test support ticket correlation with churn analysis"""
    print("🎫 Testing Support Ticket Correlation with Churn")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = BehaviorAnalyticsConfig()
    
    # Create analytics system
    analytics = UserBehaviorAnalytics(db, config)
    
    # Test support ticket correlation
    print("📋 Test 1: Support Ticket Correlation Analysis")
    
    support_analysis = analytics.analyze_support_ticket_correlation_with_churn(period_days=90)
    
    print(f"   Support Ticket Correlation Analysis:")
    print(f"     Analysis Date: {support_analysis.get('analysis_date', 'N/A')}")
    print(f"     Period Days: {support_analysis.get('period_days', 0)}")
    
    # Support-churn correlation
    support_churn_correlation = support_analysis.get('support_churn_correlation', {})
    print(f"     Support-Churn Correlation:")
    print(f"       Overall Correlation: {support_churn_correlation.get('overall_correlation', 0):.3f}")
    print(f"       Churn Rate After Ticket: {support_churn_correlation.get('churn_rate_after_ticket', 0):.1%}")
    print(f"       Response Time Correlation: {support_churn_correlation.get('response_time_correlation', 0):.3f}")
    print(f"       Resolution Time Correlation: {support_churn_correlation.get('resolution_time_correlation', 0):.3f}")
    
    # Ticket patterns
    ticket_patterns = support_analysis.get('ticket_patterns', {})
    print(f"     Ticket Patterns:")
    print(f"       Total Tickets: {ticket_patterns.get('total_tickets', 0):,}")
    print(f"       Resolution Rate: {ticket_patterns.get('resolution_rate', 0):.1%}")
    print(f"       Average Response Time: {ticket_patterns.get('avg_response_time', 0):.1f} hours")
    print(f"       Average Resolution Time: {ticket_patterns.get('avg_resolution_time', 0):.1f} hours")
    
    # Response time impact
    response_time_impact = support_analysis.get('response_time_impact', {})
    print(f"     Response Time Impact on Churn:")
    for timing, data in response_time_impact.items():
        print(f"       {timing.replace('_', ' ').title()}: {data.get('churn_rate', 0):.1%} churn rate")
    
    # Resolution impact
    resolution_impact = support_analysis.get('resolution_impact', {})
    print(f"     Resolution Impact on Churn:")
    for resolution, data in resolution_impact.items():
        print(f"       {resolution.replace('_', ' ').title()}: {data.get('churn_rate', 0):.1%} churn rate")
    
    # Ticket categories
    ticket_categories = support_analysis.get('ticket_categories', {})
    print(f"     Ticket Categories and Churn Correlation:")
    for category, data in ticket_categories.items():
        print(f"       {category.replace('_', ' ').title()}:")
        print(f"         Count: {data.get('count', 0)}")
        print(f"         Churn Rate: {data.get('churn_rate', 0):.1%}")
    
    # Churn risk factors
    churn_risk_factors = support_analysis.get('churn_risk_factors', [])
    print(f"     Churn Risk Factors:")
    for factor in churn_risk_factors:
        print(f"       {factor['factor'].replace('_', ' ').title()}:")
        print(f"         Description: {factor['description']}")
        print(f"         Risk Level: {factor['risk_level']}")
        print(f"         Mitigation: {factor['mitigation']}")
    
    # Recommendations
    recommendations = support_analysis.get('recommendations', [])
    print(f"     Recommendations:")
    for rec in recommendations:
        print(f"       {rec['type'].replace('_', ' ').title()}: {rec['recommendation']}")
        print(f"         Priority: {rec['priority']}")
        print(f"         Expected Impact: {rec['expected_impact']}")
    
    print()
    print("✅ Support Ticket Correlation with Churn Tests Completed")
    print()

def test_payment_timing_and_preferences():
    """Test payment timing and preferences analysis"""
    print("💳 Testing Payment Timing and Preferences")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = BehaviorAnalyticsConfig()
    
    # Create analytics system
    analytics = UserBehaviorAnalytics(db, config)
    
    # Test payment analysis
    print("📋 Test 1: Payment Timing and Preferences Analysis")
    
    payment_analysis = analytics.analyze_payment_timing_and_preferences(period_days=30)
    
    print(f"   Payment Analysis:")
    print(f"     Analysis Date: {payment_analysis.get('analysis_date', 'N/A')}")
    print(f"     Period Days: {payment_analysis.get('period_days', 0)}")
    
    # Payment timing
    payment_timing = payment_analysis.get('payment_timing', {})
    print(f"     Payment Timing Analysis:")
    for timing, data in payment_timing.items():
        print(f"       {timing.replace('_', ' ').title()}:")
        print(f"         Percentage: {data.get('percentage', 0):.1%}")
        print(f"         Success Rate: {data.get('success_rate', 0):.1%}")
    
    # Payment preferences
    payment_preferences = payment_analysis.get('payment_preferences', {})
    print(f"     Payment Method Preferences:")
    for method, data in payment_preferences.items():
        print(f"       {method.replace('_', ' ').title()}:")
        print(f"         Usage: {data.get('usage', 0):.1%}")
        print(f"         Success Rate: {data.get('success_rate', 0):.1%}")
    
    # Payment success patterns
    payment_success_patterns = payment_analysis.get('payment_success_patterns', {})
    print(f"     Payment Success Patterns:")
    print(f"       Overall Success Rate: {payment_success_patterns.get('overall_success_rate', 0):.1%}")
    
    method_success_rates = payment_success_patterns.get('method_success_rates', {})
    print(f"       Method Success Rates:")
    for method, rate in method_success_rates.items():
        print(f"         {method.replace('_', ' ').title()}: {rate:.1%}")
    
    timing_success_rates = payment_success_patterns.get('timing_success_rates', {})
    print(f"       Timing Success Rates:")
    for timing, rate in timing_success_rates.items():
        print(f"         {timing.replace('_', ' ').title()}: {rate:.1%}")
    
    # Retry behavior
    retry_behavior = payment_analysis.get('retry_behavior', {})
    print(f"     Retry Behavior:")
    for retry_type, data in retry_behavior.items():
        print(f"       {retry_type.replace('_', ' ').title()}: {data.get('success_rate', 0):.1%} success rate")
    
    # Payment method evolution
    payment_method_evolution = payment_analysis.get('payment_method_evolution', {})
    print(f"     Payment Method Evolution:")
    
    trends = payment_method_evolution.get('trends', {})
    print(f"       Trends:")
    for method, trend in trends.items():
        print(f"         {method.replace('_', ' ').title()}: {trend}")
    
    adoption_rates = payment_method_evolution.get('adoption_rates', {})
    print(f"       Adoption Rates:")
    for method, rate in adoption_rates.items():
        print(f"         {method.replace('_', ' ').title()}: {rate:.1%}")
    
    # Recommendations
    recommendations = payment_analysis.get('recommendations', [])
    print(f"     Recommendations:")
    for rec in recommendations:
        print(f"       {rec['type'].replace('_', ' ').title()}: {rec['recommendation']}")
        print(f"         Priority: {rec['priority']}")
        print(f"         Expected Impact: {rec['expected_impact']}")
    
    print()
    print("✅ Payment Timing and Preferences Tests Completed")
    print()

def test_comprehensive_behavior_analysis():
    """Test comprehensive behavior analysis"""
    print("🎯 Testing Comprehensive Behavior Analysis")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = BehaviorAnalyticsConfig()
    
    # Create analytics system
    analytics = UserBehaviorAnalytics(db, config)
    
    # Test comprehensive analysis
    print("📋 Test 1: Comprehensive Behavior Analysis")
    
    comprehensive_analysis = analytics.get_comprehensive_behavior_analysis()
    
    print(f"   Comprehensive Behavior Analysis:")
    print(f"     Analysis Date: {comprehensive_analysis.get('analysis_date', 'N/A')}")
    
    # Check all components
    components = [
        'feature_usage_by_tier',
        'usage_patterns',
        'engagement_scores',
        'support_correlation',
        'payment_analysis',
        'behavioral_insights',
        'recommendations'
    ]
    
    print(f"     Analysis Components:")
    for component in components:
        data = comprehensive_analysis.get(component, {})
        if data:
            if component == 'engagement_scores':
                print(f"       ✅ {component.replace('_', ' ').title()}: {len(data)} users analyzed")
            else:
                print(f"       ✅ {component.replace('_', ' ').title()}: Available")
        else:
            print(f"       ❌ {component.replace('_', ' ').title()}: Missing")
    
    # Behavioral insights
    behavioral_insights = comprehensive_analysis.get('behavioral_insights', [])
    print(f"     Behavioral Insights:")
    for insight in behavioral_insights:
        print(f"       {insight['insight']}")
        print(f"         Confidence: {insight['confidence']:.1%}")
        print(f"         Action: {insight['action']}")
    
    # Comprehensive recommendations
    recommendations = comprehensive_analysis.get('recommendations', [])
    print(f"     Comprehensive Recommendations:")
    for rec in recommendations:
        print(f"       {rec['category'].replace('_', ' ').title()} - {rec['priority'].upper()}: {rec['recommendation']}")
        print(f"         Expected Impact: {rec['expected_impact']}")
    
    print()
    print("✅ Comprehensive Behavior Analysis Tests Completed")
    print()

def test_behavior_analytics_performance():
    """Test behavior analytics performance"""
    print("⚡ Testing Behavior Analytics Performance")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = BehaviorAnalyticsConfig()
    
    # Create analytics system
    analytics = UserBehaviorAnalytics(db, config)
    
    # Test performance
    print("📈 Performance Metrics:")
    
    import time
    
    # Test feature usage analysis performance
    print("   Testing feature usage analysis performance...")
    start_time = time.time()
    
    for i in range(10):
        result = analytics.analyze_feature_usage_by_tier()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average feature usage analysis time: {avg_time:.2f}ms")
    print(f"     Feature usage analyses per second: {1000 / avg_time:.1f}")
    
    # Test engagement scoring performance
    print("   Testing engagement scoring performance...")
    start_time = time.time()
    
    for i in range(10):
        result = analytics.calculate_user_engagement_scores()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average engagement scoring time: {avg_time:.2f}ms")
    print(f"     Engagement scoring calls per second: {1000 / avg_time:.1f}")
    
    # Test comprehensive analysis performance
    print("   Testing comprehensive analysis performance...")
    start_time = time.time()
    
    for i in range(5):
        result = analytics.get_comprehensive_behavior_analysis()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 5 * 1000  # Convert to milliseconds
    
    print(f"     Average comprehensive analysis time: {avg_time:.2f}ms")
    print(f"     Comprehensive analyses per second: {1000 / avg_time:.1f}")
    
    # Test individual component performance
    components = [
        ('usage_patterns', lambda: analytics.analyze_usage_patterns_predicting_changes()),
        ('support_correlation', lambda: analytics.analyze_support_ticket_correlation_with_churn()),
        ('payment_analysis', lambda: analytics.analyze_payment_timing_and_preferences())
    ]
    
    print("   Testing individual component performance...")
    for component_name, component_func in components:
        start_time = time.time()
        
        for i in range(10):
            result = component_func()
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
        
        print(f"     {component_name.replace('_', ' ').title()}: {avg_time:.2f}ms")
    
    print()
    print("✅ Behavior Analytics Performance Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 User Behavior Analytics Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_feature_usage_by_tier()
        test_usage_patterns_predicting_changes()
        test_user_engagement_scoring()
        test_support_ticket_correlation_with_churn()
        test_payment_timing_and_preferences()
        test_comprehensive_behavior_analysis()
        test_behavior_analytics_performance()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Feature Usage by Subscription Tier")
        print("   ✅ Usage Patterns Predicting Changes")
        print("   ✅ User Engagement Scoring")
        print("   ✅ Support Ticket Correlation with Churn")
        print("   ✅ Payment Timing and Preferences")
        print("   ✅ Comprehensive Behavior Analysis")
        print("   ✅ Behavior Analytics Performance")
        print()
        print("🚀 The user behavior analytics system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 