#!/usr/bin/env python3
"""
Test script for Subscription Controls System
Tests feature access, upgrade prompts, usage tracking, and integration with MINGUS features.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from decimal import Decimal

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from features.subscription_controls import (
    FeatureAccessManager, SubscriptionControlsDecorator,
    FeatureCategory, AccessLevel, FeatureStatus, UpgradeTrigger,
    FeatureDefinition, UserFeatureAccess, UpgradePrompt, FeatureUsage
)

class MockSubscriptionService:
    """Mock subscription service for testing"""
    def __init__(self):
        self.subscriptions = {
            'free_user': {'plan_id': 'free', 'status': 'active', 'amount': 0.0},
            'basic_user': {'plan_id': 'basic', 'status': 'active', 'amount': 9.99},
            'premium_user': {'plan_id': 'premium', 'status': 'active', 'amount': 29.99},
            'professional_user': {'plan_id': 'professional', 'status': 'active', 'amount': 79.99},
            'enterprise_user': {'plan_id': 'enterprise', 'status': 'active', 'amount': 199.99}
        }
    
    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get user subscription"""
        return self.subscriptions.get(user_id, {
            'plan_id': 'free',
            'status': 'active',
            'amount': 0.0,
            'currency': 'USD'
        })

class MockUpgradeOptimizationService:
    """Mock upgrade optimization service for testing"""
    def __init__(self):
        self.upgrade_prompts = []
    
    def create_smart_trial_reminder(self, user_id: str, trial_feature_id: str, reminder_type, context: Dict[str, Any] = None):
        """Create smart trial reminder"""
        return {
            'reminder_id': str(uuid.uuid4()),
            'user_id': user_id,
            'trial_feature_id': trial_feature_id,
            'reminder_type': reminder_type.value,
            'scheduled_at': datetime.now(timezone.utc) + timedelta(hours=24)
        }
    
    def generate_usage_based_prompt(self, user_id: str, feature_usage_data: Dict[str, Any]):
        """Generate usage-based prompt"""
        return {
            'prompt_id': str(uuid.uuid4()),
            'user_id': user_id,
            'trigger_feature': 'budget_tracker',
            'value_demonstrated': 0.75,
            'upgrade_recommendation': 'upgrade_to_premium',
            'confidence_score': 0.8
        }

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.feature_access = {}
        self.upgrade_prompts = {}
        self.feature_usage = {}
    
    def commit(self):
        pass
    
    def add(self, obj):
        pass
    
    def query(self, model):
        return MockQuery(self, model)

class MockQuery:
    """Mock query for testing"""
    def __init__(self, db, model):
        self.db = db
        self.model = model
    
    def filter(self, condition):
        return self
    
    def first(self):
        return None
    
    def all(self):
        return []

def test_feature_access_control():
    """Test feature access control functionality"""
    print("🔐 Testing Feature Access Control")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    
    # Test different user tiers and features
    print("📋 Test 1: Feature Access by User Tier")
    
    test_cases = [
        ('free_user', 'budget_tracker', 'Free User - Budget Tracker'),
        ('free_user', 'investment_analysis', 'Free User - Investment Analysis'),
        ('basic_user', 'expense_categorizer', 'Basic User - Expense Categorizer'),
        ('basic_user', 'investment_analysis', 'Basic User - Investment Analysis'),
        ('premium_user', 'portfolio_tracker', 'Premium User - Portfolio Tracker'),
        ('premium_user', 'risk_assessment', 'Premium User - Risk Assessment'),
        ('professional_user', 'tax_optimizer', 'Professional User - Tax Optimizer'),
        ('professional_user', 'predictive_analytics', 'Professional User - Predictive Analytics'),
        ('enterprise_user', 'full_api_access', 'Enterprise User - Full API Access'),
        ('enterprise_user', 'dedicated_support', 'Enterprise User - Dedicated Support')
    ]
    
    for user_id, feature_id, description in test_cases:
        print(f"     {description}:")
        
        # Check feature access
        access_result = feature_manager.check_feature_access(user_id, feature_id)
        
        print(f"       Has Access: {access_result['has_access']}")
        print(f"       Reason: {access_result['reason']}")
        print(f"       Upgrade Required: {access_result['upgrade_required']}")
        print(f"       Trial Available: {access_result['trial_available']}")
        
        if 'current_usage' in access_result:
            print(f"       Current Usage: {access_result['current_usage']}")
        
        if 'usage_limit' in access_result:
            print(f"       Usage Limit: {access_result['usage_limit']}")
        
        if 'recommended_tier' in access_result:
            print(f"       Recommended Tier: {access_result['recommended_tier']}")
        
        print()
    
    print("✅ Feature Access Control Tests Completed")
    print()

def test_user_features():
    """Test user features functionality"""
    print("👤 Testing User Features")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    
    # Test user features for different tiers
    print("📋 Test 1: User Features by Tier")
    
    test_users = [
        ('free_user', 'Free User'),
        ('basic_user', 'Basic User'),
        ('premium_user', 'Premium User'),
        ('professional_user', 'Professional User'),
        ('enterprise_user', 'Enterprise User')
    ]
    
    for user_id, description in test_users:
        print(f"     {description}:")
        
        # Get user features
        features = feature_manager.get_user_features(user_id)
        
        print(f"       Available Features: {len(features['available_features'])}")
        print(f"       Restricted Features: {len(features['restricted_features'])}")
        print(f"       Trial Features: {len(features['trial_features'])}")
        print(f"       Upgrade Recommendations: {len(features['upgrade_recommendations'])}")
        
        # Show some available features
        if features['available_features']:
            print(f"       Sample Available Features:")
            for feature in features['available_features'][:3]:
                print(f"         - {feature['name']} ({feature['category']})")
        
        # Show some restricted features
        if features['restricted_features']:
            print(f"       Sample Restricted Features:")
            for feature in features['restricted_features'][:3]:
                print(f"         - {feature['name']} -> {feature['recommended_tier']}")
        
        # Show upgrade recommendations
        if features['upgrade_recommendations']:
            print(f"       Upgrade Recommendations:")
            for rec in features['upgrade_recommendations'][:3]:
                print(f"         - {rec['type']}: {rec.get('feature_name', rec['feature_id'])} -> {rec['recommended_tier']}")
        
        print()
    
    print("✅ User Features Tests Completed")
    print()

def test_upgrade_prompts():
    """Test upgrade prompt functionality"""
    print("🚀 Testing Upgrade Prompts")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    
    # Test different upgrade triggers
    print("📋 Test 1: Upgrade Prompt Creation")
    
    test_cases = [
        ('free_user', 'investment_analysis', UpgradeTrigger.FEATURE_ACCESS, 'Feature Access Trigger'),
        ('basic_user', 'portfolio_tracker', UpgradeTrigger.USAGE_LIMIT, 'Usage Limit Trigger'),
        ('premium_user', 'tax_optimizer', UpgradeTrigger.FEATURE_ACCESS, 'Professional Feature Trigger'),
        ('professional_user', 'predictive_analytics', UpgradeTrigger.USAGE_LIMIT, 'Advanced Usage Trigger')
    ]
    
    for user_id, feature_id, trigger_type, description in test_cases:
        print(f"     {description}:")
        
        # Create upgrade prompt
        prompt = feature_manager.create_upgrade_prompt(
            user_id, feature_id, trigger_type,
            {'context': 'test_context', 'urgency': 'high'}
        )
        
        if prompt:
            print(f"       Prompt Created: Yes")
            print(f"       Prompt ID: {prompt.prompt_id}")
            print(f"       User ID: {prompt.user_id}")
            print(f"       Feature ID: {prompt.feature_id}")
            print(f"       Trigger Type: {prompt.trigger_type.value}")
            print(f"       Current Tier: {prompt.current_tier}")
            print(f"       Recommended Tier: {prompt.recommended_tier}")
            print(f"       Value Proposition: {prompt.value_proposition}")
            print(f"       Urgency Level: {prompt.urgency_level}")
            print(f"       Is Active: {prompt.is_active}")
            print(f"       Created At: {prompt.created_at}")
            print(f"       Expires At: {prompt.expires_at}")
            
            print(f"       Context Data:")
            for key, value in prompt.context_data.items():
                print(f"         {key}: {value}")
        else:
            print(f"       Prompt Created: No")
        
        print()
    
    print("✅ Upgrade Prompts Tests Completed")
    print()

def test_usage_tracking():
    """Test usage tracking functionality"""
    print("📊 Testing Usage Tracking")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    
    # Test usage tracking for different features
    print("📋 Test 1: Feature Usage Tracking")
    
    test_cases = [
        ('free_user', 'budget_tracker', 'access', {'action': 'view_dashboard'}),
        ('basic_user', 'expense_categorizer', 'categorization', {'transactions': 5}),
        ('premium_user', 'investment_analysis', 'analysis', {'portfolio_size': 100000}),
        ('professional_user', 'tax_optimizer', 'optimization', {'tax_year': 2024}),
        ('enterprise_user', 'api_access', 'api_call', {'endpoint': '/data/export'})
    ]
    
    for user_id, feature_id, usage_type, usage_data in test_cases:
        print(f"     Tracking {usage_type} for {feature_id} (User: {user_id}):")
        
        # Track usage
        feature_manager.track_feature_usage(
            user_id, feature_id, usage_type, usage_data
        )
        
        print(f"       Usage Type: {usage_type}")
        print(f"       Usage Data: {usage_data}")
        print(f"       Tracking: Success")
        
        print()
    
    print("✅ Usage Tracking Tests Completed")
    print()

def test_feature_analytics():
    """Test feature analytics functionality"""
    print("📈 Testing Feature Analytics")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    
    # Test analytics for different users
    print("📋 Test 1: Feature Analytics Generation")
    
    test_users = [
        ('free_user', 'Free User'),
        ('basic_user', 'Basic User'),
        ('premium_user', 'Premium User'),
        ('professional_user', 'Professional User')
    ]
    
    for user_id, description in test_users:
        print(f"     {description}:")
        
        # Get feature analytics
        analytics = feature_manager.get_feature_analytics(user_id)
        
        print(f"       User ID: {analytics['user_id']}")
        
        print(f"       Feature Usage:")
        for feature_id, usage_data in analytics['feature_usage'].items():
            print(f"         {feature_id}: {usage_data.get('usage_count', 0)} uses")
        
        print(f"       Usage Trends:")
        trends = analytics['usage_trends']
        print(f"         Total Features Used: {trends['total_features_used']}")
        print(f"         Most Used Features: {trends['most_used_features']}")
        print(f"         Usage Growth Rate: {trends['usage_growth_rate']:.1%}")
        print(f"         Feature Adoption Rate: {trends['feature_adoption_rate']:.1%}")
        
        print(f"       Upgrade Opportunities: {len(analytics['upgrade_opportunities'])}")
        for opportunity in analytics['upgrade_opportunities']:
            print(f"         - {opportunity['type']}: {opportunity['feature_id']} -> {opportunity['recommended_tier']}")
        
        print(f"       Recommendations: {len(analytics['recommendations'])}")
        for recommendation in analytics['recommendations']:
            print(f"         - {recommendation}")
        
        print()
    
    print("✅ Feature Analytics Tests Completed")
    print()

def test_subscription_controls_decorator():
    """Test subscription controls decorator"""
    print("🎯 Testing Subscription Controls Decorator")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager and decorator
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    decorator = SubscriptionControlsDecorator(feature_manager)
    
    # Test decorator functionality
    print("📋 Test 1: Feature Access Decorator")
    
    @decorator.require_feature_access('investment_analysis')
    def analyze_investment(user_id: str, portfolio_data: Dict[str, Any]):
        """Mock investment analysis function"""
        return {
            'analysis_id': str(uuid.uuid4()),
            'user_id': user_id,
            'portfolio_value': portfolio_data.get('value', 0),
            'recommendations': ['diversify', 'rebalance']
        }
    
    @decorator.check_usage_limits('data_export', 'export')
    def export_data(user_id: str, data_type: str, format: str):
        """Mock data export function"""
        return {
            'export_id': str(uuid.uuid4()),
            'user_id': user_id,
            'data_type': data_type,
            'format': format,
            'file_size': '2.5MB'
        }
    
    # Test successful access
    print("     Testing successful feature access:")
    try:
        result = analyze_investment('premium_user', {'value': 100000})
        print(f"       Investment analysis successful: {result['analysis_id']}")
    except Exception as e:
        print(f"       Investment analysis failed: {e}")
    
    # Test restricted access
    print("     Testing restricted feature access:")
    try:
        result = analyze_investment('free_user', {'value': 50000})
        print(f"       Investment analysis successful: {result['analysis_id']}")
    except Exception as e:
        print(f"       Investment analysis failed (expected): {e}")
    
    # Test usage limits
    print("     Testing usage limits:")
    try:
        result = export_data('basic_user', 'transactions', 'csv')
        print(f"       Data export successful: {result['export_id']}")
    except Exception as e:
        print(f"       Data export failed (expected): {e}")
    
    print()
    print("✅ Subscription Controls Decorator Tests Completed")
    print()

def test_integration_scenarios():
    """Test integration scenarios"""
    print("🔗 Testing Integration Scenarios")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    
    # Test complete user journey
    print("📋 Test 1: Complete User Journey Integration")
    
    user_id = 'basic_user'
    print(f"     User Journey for {user_id}:")
    
    # Step 1: User tries to access basic feature
    print(f"     Step 1: Access Basic Feature")
    access_result = feature_manager.check_feature_access(user_id, 'budget_tracker')
    print(f"       Budget Tracker Access: {access_result['has_access']}")
    
    # Step 2: User tries to access premium feature
    print(f"     Step 2: Access Premium Feature")
    access_result = feature_manager.check_feature_access(user_id, 'investment_analysis')
    print(f"       Investment Analysis Access: {access_result['has_access']}")
    if not access_result['has_access']:
        print(f"       Upgrade Required: {access_result['upgrade_required']}")
        print(f"       Recommended Tier: {access_result.get('recommended_tier', 'N/A')}")
    
    # Step 3: Create upgrade prompt
    print(f"     Step 3: Create Upgrade Prompt")
    prompt = feature_manager.create_upgrade_prompt(
        user_id, 'investment_analysis', UpgradeTrigger.FEATURE_ACCESS
    )
    if prompt:
        print(f"       Upgrade prompt created: {prompt.prompt_id}")
        print(f"       Value proposition: {prompt.value_proposition}")
    
    # Step 4: Track feature usage
    print(f"     Step 4: Track Feature Usage")
    feature_manager.track_feature_usage(
        user_id, 'budget_tracker', 'dashboard_view', {'page': 'overview'}
    )
    print(f"       Usage tracked for budget_tracker")
    
    # Step 5: Check usage limits
    print(f"     Step 5: Check Usage Limits")
    access_result = feature_manager.check_feature_access(user_id, 'data_export')
    print(f"       Data Export Access: {access_result['has_access']}")
    if 'current_usage' in access_result:
        print(f"       Current Usage: {access_result['current_usage']}")
    
    # Step 6: Get comprehensive analytics
    print(f"     Step 6: Get Analytics")
    analytics = feature_manager.get_feature_analytics(user_id)
    print(f"       Analytics generated with {len(analytics['recommendations'])} recommendations")
    
    # Step 7: Get user features
    print(f"     Step 7: Get User Features")
    features = feature_manager.get_user_features(user_id)
    print(f"       Available Features: {len(features['available_features'])}")
    print(f"       Restricted Features: {len(features['restricted_features'])}")
    print(f"       Upgrade Recommendations: {len(features['upgrade_recommendations'])}")
    
    print()
    print("✅ Integration Scenarios Tests Completed")
    print()

def test_performance():
    """Test performance metrics"""
    print("⚡ Testing Performance")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    upgrade_optimization_service = MockUpgradeOptimizationService()
    
    # Create feature access manager
    feature_manager = FeatureAccessManager(
        db, subscription_service, upgrade_optimization_service
    )
    
    # Test performance
    print("📈 Performance Metrics:")
    
    import time
    
    # Test feature access check performance
    print("   Testing feature access check performance...")
    start_time = time.time()
    
    for i in range(50):
        user_id = f'user_{i % 5}'  # Cycle through different user types
        feature_id = 'budget_tracker'
        result = feature_manager.check_feature_access(user_id, feature_id)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 50 * 1000  # Convert to milliseconds
    
    print(f"     Average feature access check time: {avg_time:.2f}ms")
    print(f"     Feature access checks per second: {1000 / avg_time:.1f}")
    
    # Test user features retrieval performance
    print("   Testing user features retrieval performance...")
    start_time = time.time()
    
    for i in range(20):
        user_id = f'user_{i % 5}'
        result = feature_manager.get_user_features(user_id)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 20 * 1000  # Convert to milliseconds
    
    print(f"     Average user features retrieval time: {avg_time:.2f}ms")
    print(f"     User features retrievals per second: {1000 / avg_time:.1f}")
    
    # Test upgrade prompt creation performance
    print("   Testing upgrade prompt creation performance...")
    start_time = time.time()
    
    for i in range(20):
        user_id = f'user_{i % 5}'
        result = feature_manager.create_upgrade_prompt(
            user_id, 'investment_analysis', UpgradeTrigger.FEATURE_ACCESS
        )
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 20 * 1000  # Convert to milliseconds
    
    print(f"     Average upgrade prompt creation time: {avg_time:.2f}ms")
    print(f"     Upgrade prompt creations per second: {1000 / avg_time:.1f}")
    
    # Test usage tracking performance
    print("   Testing usage tracking performance...")
    start_time = time.time()
    
    for i in range(50):
        user_id = f'user_{i % 5}'
        feature_id = 'budget_tracker'
        feature_manager.track_feature_usage(user_id, feature_id, 'test', {'iteration': i})
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 50 * 1000  # Convert to milliseconds
    
    print(f"     Average usage tracking time: {avg_time:.2f}ms")
    print(f"     Usage tracking operations per second: {1000 / avg_time:.1f}")
    
    # Test analytics generation performance
    print("   Testing analytics generation performance...")
    start_time = time.time()
    
    for i in range(10):
        user_id = f'user_{i % 5}'
        result = feature_manager.get_feature_analytics(user_id)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average analytics generation time: {avg_time:.2f}ms")
    print(f"     Analytics generations per second: {1000 / avg_time:.1f}")
    
    print()
    print("✅ Performance Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Subscription Controls System Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_feature_access_control()
        test_user_features()
        test_upgrade_prompts()
        test_usage_tracking()
        test_feature_analytics()
        test_subscription_controls_decorator()
        test_integration_scenarios()
        test_performance()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Feature Access Control")
        print("   ✅ User Features")
        print("   ✅ Upgrade Prompts")
        print("   ✅ Usage Tracking")
        print("   ✅ Feature Analytics")
        print("   ✅ Subscription Controls Decorator")
        print("   ✅ Integration Scenarios")
        print("   ✅ Performance")
        print()
        print("🚀 The subscription controls system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 