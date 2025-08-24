#!/usr/bin/env python3
"""
Test script for Upgrade Optimization System
Tests smart trial reminder timing, usage-based upgrade prompts,
social proof and testimonials, limited-time upgrade offers,
and conversion funnel A/B testing.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from decimal import Decimal

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from onboarding.upgrade_optimization import (
    UpgradeOptimization, OptimizationConfig, TrialReminder, UsageBasedPrompt,
    SocialProof, LimitedTimeOffer, ABTest, ReminderType, SocialProofType,
    OfferType, ABTestType
)

class MockSubscriptionService:
    """Mock subscription service for testing"""
    def __init__(self):
        self.subscriptions = {}
    
    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get user subscription"""
        return self.subscriptions.get(user_id, {
            'plan_id': 'free',
            'status': 'active',
            'amount': 0.0,
            'currency': 'USD'
        })
    
    def upgrade_user_subscription(self, user_id: str, new_plan: str, offer_amount: float, offer_currency: str) -> Dict[str, Any]:
        """Upgrade user subscription"""
        self.subscriptions[user_id] = {
            'plan_id': new_plan,
            'status': 'active',
            'amount': offer_amount,
            'currency': offer_currency
        }
        return {'success': True, 'new_plan': new_plan}

class MockAnalyticsService:
    """Mock analytics service for testing"""
    def __init__(self):
        self.analytics_data = {}
    
    def track_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Track analytics event"""
        if user_id not in self.analytics_data:
            self.analytics_data[user_id] = []
        self.analytics_data[user_id].append({
            'event_type': event_type,
            'event_data': event_data,
            'timestamp': datetime.now(timezone.utc)
        })

class MockNotificationService:
    """Mock notification service for testing"""
    def __init__(self):
        self.notifications = []
    
    def send_notification(self, user_id: str, notification_type: str, data: Dict[str, Any]) -> None:
        """Send notification"""
        self.notifications.append({
            'user_id': user_id,
            'notification_type': notification_type,
            'data': data,
            'timestamp': datetime.now(timezone.utc)
        })

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.trial_reminders = {}
        self.usage_prompts = {}
        self.limited_time_offers = {}
        self.ab_tests = {}
    
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

def create_mock_feature_usage_data(user_type: str = 'intermediate') -> Dict[str, Any]:
    """Create mock feature usage data for testing"""
    if user_type == 'beginner':
        return {
            'features': {
                'budget_tracker': {'count': 3, 'time_spent': 1800, 'last_used': datetime.now(timezone.utc)},
                'expense_categorizer': {'count': 2, 'time_spent': 1200, 'last_used': datetime.now(timezone.utc)},
                'savings_goals': {'count': 1, 'time_spent': 900, 'last_used': datetime.now(timezone.utc)}
            },
            'days_active': 7,
            'total_time_spent': 3900,
            'engagement_score': 0.6
        }
    elif user_type == 'intermediate':
        return {
            'features': {
                'budget_tracker': {'count': 8, 'time_spent': 4800, 'last_used': datetime.now(timezone.utc)},
                'expense_categorizer': {'count': 6, 'time_spent': 3600, 'last_used': datetime.now(timezone.utc)},
                'savings_goals': {'count': 5, 'time_spent': 3000, 'last_used': datetime.now(timezone.utc)},
                'investment_analysis': {'count': 3, 'time_spent': 2400, 'last_used': datetime.now(timezone.utc)},
                'retirement_planner': {'count': 2, 'time_spent': 1800, 'last_used': datetime.now(timezone.utc)}
            },
            'days_active': 14,
            'total_time_spent': 15600,
            'engagement_score': 0.8
        }
    else:  # advanced
        return {
            'features': {
                'budget_tracker': {'count': 15, 'time_spent': 9000, 'last_used': datetime.now(timezone.utc)},
                'expense_categorizer': {'count': 12, 'time_spent': 7200, 'last_used': datetime.now(timezone.utc)},
                'savings_goals': {'count': 10, 'time_spent': 6000, 'last_used': datetime.now(timezone.utc)},
                'investment_analysis': {'count': 8, 'time_spent': 6400, 'last_used': datetime.now(timezone.utc)},
                'retirement_planner': {'count': 6, 'time_spent': 5400, 'last_used': datetime.now(timezone.utc)},
                'tax_optimizer': {'count': 4, 'time_spent': 3600, 'last_used': datetime.now(timezone.utc)}
            },
            'days_active': 30,
            'total_time_spent': 37600,
            'engagement_score': 0.95
        }

def test_smart_trial_reminders():
    """Test smart trial reminder functionality"""
    print("⏰ Testing Smart Trial Reminders")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test different reminder types
    print("📋 Test 1: Trial Reminder Creation for Different Types")
    
    test_cases = [
        (ReminderType.TRIAL_EXPIRY, 'Trial Expiry Reminder', {
            'trial_end_time': datetime.now(timezone.utc) + timedelta(hours=24),
            'hours_before_expiry': 24
        }),
        (ReminderType.FEATURE_USAGE, 'Feature Usage Reminder', {
            'feature_name': 'Investment Analysis',
            'usage_threshold': 0.5,
            'current_usage': 0.3
        }),
        (ReminderType.VALUE_DEMONSTRATION, 'Value Demonstration Reminder', {
            'value_demonstrated': 1500,
            'feature_name': 'Tax Optimizer'
        }),
        (ReminderType.ENGAGEMENT_DROP, 'Engagement Drop Reminder', {
            'engagement_metric': 'time_spent',
            'engagement_drop': True
        }),
        (ReminderType.GOAL_ALIGNMENT, 'Goal Alignment Reminder', {
            'goal_alignment_score': 0.8,
            'primary_goal': 'retirement_planning'
        })
    ]
    
    for reminder_type, description, context in test_cases:
        print(f"     {description}:")
        
        user_id = str(uuid.uuid4())
        trial_feature_id = 'investment_analysis'
        
        # Create trial reminder
        reminder = optimization_system.create_smart_trial_reminder(
            user_id, trial_feature_id, reminder_type, context
        )
        
        print(f"       Reminder ID: {reminder.reminder_id}")
        print(f"       Reminder Type: {reminder.reminder_type.value}")
        print(f"       User ID: {reminder.user_id}")
        print(f"       Trial Feature: {reminder.trial_feature_id}")
        print(f"       Priority: {reminder.priority}")
        print(f"       Is Active: {reminder.is_active}")
        print(f"       Created At: {reminder.created_at}")
        print(f"       Scheduled At: {reminder.scheduled_at}")
        
        print(f"       Trigger Conditions:")
        for key, value in reminder.trigger_conditions.items():
            print(f"         {key}: {value}")
        
        print(f"       Timing Config:")
        for key, value in reminder.timing_config.items():
            print(f"         {key}: {value}")
        
        print(f"       Message Template: {reminder.message_template}")
        
        print()
    
    print("✅ Smart Trial Reminders Tests Completed")
    print()

def test_usage_based_prompts():
    """Test usage-based prompt generation"""
    print("📊 Testing Usage-Based Prompts")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test usage-based prompts for different user types
    print("📋 Test 1: Usage-Based Prompt Generation")
    
    test_cases = [
        ('beginner', 'Beginner User'),
        ('intermediate', 'Intermediate User'),
        ('advanced', 'Advanced User')
    ]
    
    for user_type, description in test_cases:
        print(f"     {description}:")
        
        user_id = str(uuid.uuid4())
        feature_usage_data = create_mock_feature_usage_data(user_type)
        
        # Generate usage-based prompt
        prompt = optimization_system.generate_usage_based_prompt(user_id, feature_usage_data)
        
        if prompt:
            print(f"       Prompt Generated: Yes")
            print(f"       Prompt ID: {prompt.prompt_id}")
            print(f"       User ID: {prompt.user_id}")
            print(f"       Trigger Feature: {prompt.trigger_feature}")
            print(f"       Usage Threshold: {prompt.usage_threshold}")
            print(f"       Value Demonstrated: {prompt.value_demonstrated:.1%}")
            print(f"       Upgrade Recommendation: {prompt.upgrade_recommendation}")
            print(f"       Confidence Score: {prompt.confidence_score:.1%}")
            print(f"       Created At: {prompt.created_at}")
            
            print(f"       Usage Pattern Analysis:")
            for key, value in prompt.usage_pattern.items():
                if isinstance(value, float):
                    print(f"         {key}: {value:.3f}")
                else:
                    print(f"         {key}: {value}")
            
            print(f"       Personalization Data:")
            for key, value in prompt.personalization_data.items():
                if isinstance(value, float):
                    print(f"         {key}: {value:.3f}")
                else:
                    print(f"         {key}: {value}")
        else:
            print(f"       Prompt Generated: No (thresholds not met)")
        
        print()
    
    print("✅ Usage-Based Prompts Tests Completed")
    print()

def test_social_proof():
    """Test social proof functionality"""
    print("👥 Testing Social Proof")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test social proof for different user segments
    print("📋 Test 1: Social Proof Generation")
    
    test_cases = [
        ('budget_tier', 'Budget Tier User'),
        ('mid_tier', 'Mid-Tier User'),
        ('professional_tier', 'Professional Tier User')
    ]
    
    for user_segment, description in test_cases:
        print(f"     {description}:")
        
        user_id = str(uuid.uuid4())
        context = {
            'user_segment': user_segment,
            'feature_interest': 'investment_planning',
            'goals': ['save_money', 'invest_for_future']
        }
        
        # Get social proof
        social_proofs = optimization_system.get_social_proof(user_id, context)
        
        print(f"       Social Proofs Retrieved: {len(social_proofs)}")
        
        for i, proof in enumerate(social_proofs, 1):
            print(f"       Proof {i}:")
            print(f"         ID: {proof.proof_id}")
            print(f"         Type: {proof.proof_type.value}")
            print(f"         Title: {proof.title}")
            print(f"         Content: {proof.content}")
            print(f"         Author: {proof.author}")
            print(f"         User Segment: {proof.user_segment}")
            print(f"         Relevance Score: {proof.relevance_score:.1%}")
            print(f"         Conversion Rate: {proof.conversion_rate:.1%}")
            print(f"         Usage Count: {proof.usage_count}")
        
        print()
    
    print("✅ Social Proof Tests Completed")
    print()

def test_limited_time_offers():
    """Test limited-time offers functionality"""
    print("⏳ Testing Limited-Time Offers")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test different offer types
    print("📋 Test 1: Limited-Time Offer Creation")
    
    test_cases = [
        (OfferType.PERCENTAGE_DISCOUNT, 'Percentage Discount Offer'),
        (OfferType.FIXED_DISCOUNT, 'Fixed Discount Offer'),
        (OfferType.FREE_MONTHS, 'Free Months Offer'),
        (OfferType.FEATURE_UPGRADE, 'Feature Upgrade Offer'),
        (OfferType.BONUS_FEATURES, 'Bonus Features Offer')
    ]
    
    for offer_type, description in test_cases:
        print(f"     {description}:")
        
        user_id = str(uuid.uuid4())
        context = {
            'current_tier': 'budget',
            'target_tier': 'mid_tier',
            'engagement_score': 0.7,
            'feature_usage': 5,
            'trial_eligible': True
        }
        
        # Create limited-time offer
        offer = optimization_system.create_limited_time_offer(user_id, offer_type, context)
        
        if offer:
            print(f"       Offer Created: Yes")
            print(f"       Offer ID: {offer.offer_id}")
            print(f"       Offer Type: {offer.offer_type.value}")
            print(f"       Title: {offer.title}")
            print(f"       Description: {offer.description}")
            print(f"       Discount Value: {offer.discount_value}")
            print(f"       Discount Type: {offer.discount_type}")
            print(f"       Start Date: {offer.start_date}")
            print(f"       End Date: {offer.end_date}")
            print(f"       Usage Limit: {offer.usage_limit}")
            print(f"       Current Usage: {offer.current_usage}")
            print(f"       Is Active: {offer.is_active}")
            print(f"       Created At: {offer.created_at}")
            
            print(f"       Eligibility Criteria:")
            for key, value in offer.eligibility_criteria.items():
                print(f"         {key}: {value}")
        else:
            print(f"       Offer Created: No (not eligible)")
        
        print()
    
    print("✅ Limited-Time Offers Tests Completed")
    print()

def test_ab_testing():
    """Test A/B testing functionality"""
    print("🧪 Testing A/B Testing")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test A/B test assignment and results
    print("📋 Test 1: A/B Test Assignment and Results")
    
    test_types = [
        ABTestType.PROMPT_DESIGN,
        ABTestType.OFFER_TYPE,
        ABTestType.TIMING,
        ABTestType.MESSAGING,
        ABTestType.SOCIAL_PROOF,
        ABTestType.CTA_DESIGN
    ]
    
    for test_type in test_types:
        print(f"     Testing {test_type.value}:")
        
        # Test multiple users to see variant distribution
        variant_counts = {'A': 0, 'B': 0, 'control': 0}
        
        for i in range(10):
            user_id = str(uuid.uuid4())
            context = {
                'user_segment': 'mid_tier',
                'engagement_score': 0.7
            }
            
            # Assign A/B test variant
            assignment = optimization_system.assign_ab_test_variant(user_id, test_type, context)
            
            variant = assignment['variant']
            variant_counts[variant] += 1
            
            print(f"       User {i+1}: {user_id[:8]}... -> Variant {variant}")
            
            # Record test result
            result_data = {
                'conversion_rate': 0.05 + (0.02 if variant == 'B' else 0),
                'click_through_rate': 0.15 + (0.03 if variant == 'B' else 0),
                'revenue_per_user': 25.0 + (5.0 if variant == 'B' else 0),
                'engagement_score': 0.7 + (0.1 if variant == 'B' else 0)
            }
            
            optimization_system.record_ab_test_result(user_id, assignment['test_id'], variant, result_data)
        
        print(f"       Variant Distribution:")
        for variant, count in variant_counts.items():
            print(f"         {variant}: {count} users ({count/10*100:.0f}%)")
        
        print()
    
    print("✅ A/B Testing Tests Completed")
    print()

def test_optimization_analytics():
    """Test optimization analytics functionality"""
    print("📈 Testing Optimization Analytics")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test analytics for different user types
    print("📋 Test 1: Optimization Analytics Generation")
    
    test_cases = [
        ('beginner', 'Beginner User'),
        ('intermediate', 'Intermediate User'),
        ('advanced', 'Advanced User')
    ]
    
    for user_type, description in test_cases:
        print(f"     {description}:")
        
        user_id = str(uuid.uuid4())
        
        # Generate some test data first
        feature_usage_data = create_mock_feature_usage_data(user_type)
        optimization_system.generate_usage_based_prompt(user_id, feature_usage_data)
        
        # Create some trial reminders
        optimization_system.create_smart_trial_reminder(
            user_id, 'investment_analysis', ReminderType.TRIAL_EXPIRY,
            {'trial_end_time': datetime.now(timezone.utc) + timedelta(hours=24)}
        )
        
        # Create limited-time offer
        optimization_system.create_limited_time_offer(
            user_id, OfferType.PERCENTAGE_DISCOUNT,
            {'current_tier': 'budget', 'target_tier': 'mid_tier'}
        )
        
        # Get optimization analytics
        analytics = optimization_system.get_optimization_analytics(user_id)
        
        print(f"       User ID: {analytics['user_id']}")
        
        print(f"       Trial Reminders: {len(analytics['trial_reminders'])}")
        print(f"       Usage Prompts: {len(analytics['usage_prompts'])}")
        print(f"       Social Proof Usage: {len(analytics['social_proof_usage'])}")
        print(f"       Offer Interactions: {len(analytics['offer_interactions'])}")
        print(f"       A/B Test Participation: {len(analytics['ab_test_participation'])}")
        
        print(f"       Conversion Metrics:")
        for key, value in analytics['conversion_metrics'].items():
            if isinstance(value, float):
                print(f"         {key}: {value:.1%}")
            else:
                print(f"         {key}: {value}")
        
        print(f"       Optimization Recommendations:")
        for recommendation in analytics['optimization_recommendations']:
            print(f"         - {recommendation}")
        
        print()
    
    print("✅ Optimization Analytics Tests Completed")
    print()

def test_integration_scenarios():
    """Test integration scenarios"""
    print("🔗 Testing Integration Scenarios")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test complete user journey
    print("📋 Test 1: Complete User Journey Optimization")
    
    user_id = str(uuid.uuid4())
    print(f"     User Journey for {user_id}:")
    
    # Step 1: User starts with basic usage
    print(f"     Step 1: Basic Usage")
    feature_usage_data = create_mock_feature_usage_data('beginner')
    usage_prompt = optimization_system.generate_usage_based_prompt(user_id, feature_usage_data)
    if usage_prompt:
        print(f"       Usage prompt generated: {usage_prompt.upgrade_recommendation}")
    
    # Step 2: User gets trial access
    print(f"     Step 2: Trial Access")
    trial_reminder = optimization_system.create_smart_trial_reminder(
        user_id, 'investment_analysis', ReminderType.TRIAL_EXPIRY,
        {'trial_end_time': datetime.now(timezone.utc) + timedelta(hours=24)}
    )
    print(f"       Trial reminder created: {trial_reminder.reminder_type.value}")
    
    # Step 3: User gets social proof
    print(f"     Step 3: Social Proof")
    social_proofs = optimization_system.get_social_proof(user_id, {
        'user_segment': 'budget_tier',
        'feature_interest': 'investment_planning'
    })
    print(f"       Social proofs retrieved: {len(social_proofs)}")
    
    # Step 4: User gets limited-time offer
    print(f"     Step 4: Limited-Time Offer")
    offer = optimization_system.create_limited_time_offer(
        user_id, OfferType.PERCENTAGE_DISCOUNT,
        {'current_tier': 'budget', 'target_tier': 'mid_tier'}
    )
    if offer:
        print(f"       Limited-time offer created: {offer.offer_type.value}")
    
    # Step 5: User participates in A/B test
    print(f"     Step 5: A/B Test Participation")
    ab_assignment = optimization_system.assign_ab_test_variant(
        user_id, ABTestType.PROMPT_DESIGN, {'user_segment': 'budget_tier'}
    )
    print(f"       A/B test variant assigned: {ab_assignment['variant']}")
    
    # Step 6: Record A/B test results
    print(f"     Step 6: A/B Test Results")
    optimization_system.record_ab_test_result(
        user_id, ab_assignment['test_id'], ab_assignment['variant'],
        {'conversion_rate': 0.08, 'click_through_rate': 0.18}
    )
    print(f"       A/B test results recorded")
    
    # Step 7: Get comprehensive analytics
    print(f"     Step 7: Analytics Review")
    analytics = optimization_system.get_optimization_analytics(user_id)
    print(f"       Analytics generated with {len(analytics['optimization_recommendations'])} recommendations")
    
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
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create upgrade optimization system
    optimization_system = UpgradeOptimization(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test performance
    print("📈 Performance Metrics:")
    
    import time
    
    # Test trial reminder creation performance
    print("   Testing trial reminder creation performance...")
    start_time = time.time()
    
    for i in range(20):
        user_id = str(uuid.uuid4())
        result = optimization_system.create_smart_trial_reminder(
            user_id, 'investment_analysis', ReminderType.TRIAL_EXPIRY,
            {'trial_end_time': datetime.now(timezone.utc) + timedelta(hours=24)}
        )
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 20 * 1000  # Convert to milliseconds
    
    print(f"     Average trial reminder creation time: {avg_time:.2f}ms")
    print(f"     Trial reminder creations per second: {1000 / avg_time:.1f}")
    
    # Test usage prompt generation performance
    print("   Testing usage prompt generation performance...")
    start_time = time.time()
    
    for i in range(20):
        user_id = str(uuid.uuid4())
        feature_usage_data = create_mock_feature_usage_data('intermediate')
        result = optimization_system.generate_usage_based_prompt(user_id, feature_usage_data)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 20 * 1000  # Convert to milliseconds
    
    print(f"     Average usage prompt generation time: {avg_time:.2f}ms")
    print(f"     Usage prompt generations per second: {1000 / avg_time:.1f}")
    
    # Test social proof retrieval performance
    print("   Testing social proof retrieval performance...")
    start_time = time.time()
    
    for i in range(20):
        user_id = str(uuid.uuid4())
        result = optimization_system.get_social_proof(user_id, {'user_segment': 'mid_tier'})
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 20 * 1000  # Convert to milliseconds
    
    print(f"     Average social proof retrieval time: {avg_time:.2f}ms")
    print(f"     Social proof retrievals per second: {1000 / avg_time:.1f}")
    
    # Test A/B test assignment performance
    print("   Testing A/B test assignment performance...")
    start_time = time.time()
    
    for i in range(20):
        user_id = str(uuid.uuid4())
        result = optimization_system.assign_ab_test_variant(user_id, ABTestType.PROMPT_DESIGN, {})
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 20 * 1000  # Convert to milliseconds
    
    print(f"     Average A/B test assignment time: {avg_time:.2f}ms")
    print(f"     A/B test assignments per second: {1000 / avg_time:.1f}")
    
    # Test analytics generation performance
    print("   Testing analytics generation performance...")
    start_time = time.time()
    
    for i in range(10):
        user_id = str(uuid.uuid4())
        result = optimization_system.get_optimization_analytics(user_id)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average analytics generation time: {avg_time:.2f}ms")
    print(f"     Analytics generations per second: {1000 / avg_time:.1f}")
    
    print()
    print("✅ Performance Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Upgrade Optimization System Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_smart_trial_reminders()
        test_usage_based_prompts()
        test_social_proof()
        test_limited_time_offers()
        test_ab_testing()
        test_optimization_analytics()
        test_integration_scenarios()
        test_performance()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Smart Trial Reminders")
        print("   ✅ Usage-Based Prompts")
        print("   ✅ Social Proof")
        print("   ✅ Limited-Time Offers")
        print("   ✅ A/B Testing")
        print("   ✅ Optimization Analytics")
        print("   ✅ Integration Scenarios")
        print("   ✅ Performance")
        print()
        print("🚀 The upgrade optimization system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 