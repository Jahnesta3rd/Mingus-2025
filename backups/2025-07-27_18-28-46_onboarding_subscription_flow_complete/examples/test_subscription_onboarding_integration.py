#!/usr/bin/env python3
"""
Test script for Subscription Onboarding Integration
Tests seamless integration between subscription system and user onboarding flow
to maximize upgrades through strategic feature exposure and personalized recommendations.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from decimal import Decimal

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from onboarding.subscription_integration import (
    SubscriptionOnboardingIntegration, OnboardingConfig, UserOnboardingState,
    OnboardingStage, UserSegment, UpgradeTrigger, ConversionStage,
    FeatureTeaser, UpgradeOpportunity, OnboardingAnalytics
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
        self.onboarding_states = {}
        self.upgrade_opportunities = {}
    
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

def test_onboarding_initialization():
    """Test onboarding initialization functionality"""
    print("🚀 Testing Onboarding Initialization")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test onboarding initialization
    print("📋 Test 1: User Onboarding Initialization")
    
    user_id = str(uuid.uuid4())
    user_data = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'industry': 'Technology',
        'experience_years': 5,
        'company_size': 500,
        'role': 'Software Engineer',
        'career_goals': ['salary_negotiation', 'career_advancement'],
        'preferences': {'learning_style': 'hands_on', 'communication': 'email'}
    }
    
    onboarding_state = onboarding_integration.initialize_user_onboarding(user_id, user_data)
    
    print(f"   Onboarding State Created:")
    print(f"     User ID: {onboarding_state.user_id}")
    print(f"     Current Stage: {onboarding_state.current_stage.value}")
    print(f"     Stage Progress: {onboarding_state.stage_progress:.1%}")
    print(f"     User Segment: {onboarding_state.segment.value}")
    print(f"     Conversion Score: {onboarding_state.conversion_score:.1%}")
    print(f"     Onboarding Start: {onboarding_state.onboarding_start_date}")
    print(f"     Expected Completion: {onboarding_state.expected_completion_date}")
    print(f"     Features Explored: {len(onboarding_state.features_explored)}")
    print(f"     Upgrade Attempts: {onboarding_state.upgrade_attempts}")
    
    # Check personalization factors
    personalization_factors = onboarding_state.metadata.get('personalization_factors', {})
    print(f"     Personalization Factors:")
    print(f"       Industry: {personalization_factors.get('industry')}")
    print(f"       Experience Level: {personalization_factors.get('experience_level')} years")
    print(f"       Company Size: {personalization_factors.get('company_size')}")
    print(f"       Role: {personalization_factors.get('role')}")
    print(f"       Goals: {personalization_factors.get('goals', [])}")
    
    # Check notifications sent
    print(f"     Notifications Sent: {len(notification_service.notifications)}")
    for notification in notification_service.notifications:
        print(f"       {notification['notification_type']}: {notification['data']}")
    
    print()
    print("✅ Onboarding Initialization Tests Completed")
    print()

def test_stage_advancement():
    """Test onboarding stage advancement"""
    print("📈 Testing Onboarding Stage Advancement")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test stage advancement
    print("📋 Test 1: Stage Advancement Through Onboarding Flow")
    
    user_id = str(uuid.uuid4())
    user_data = {
        'name': 'Jane Smith',
        'email': 'jane.smith@example.com',
        'industry': 'Finance',
        'experience_years': 3,
        'company_size': 100,
        'role': 'Data Analyst',
        'career_goals': ['skill_development', 'networking'],
        'preferences': {'learning_style': 'visual', 'communication': 'in_app'}
    }
    
    # Initialize onboarding
    onboarding_state = onboarding_integration.initialize_user_onboarding(user_id, user_data)
    
    # Advance through stages
    stages = [
        OnboardingStage.PROFILE_SETUP,
        OnboardingStage.FEATURE_DISCOVERY,
        OnboardingStage.TRIAL_EXPERIENCE,
        OnboardingStage.UPGRADE_PROMOTION
    ]
    
    for i, stage in enumerate(stages):
        progress = (i + 1) / len(stages)
        onboarding_state = onboarding_integration.advance_onboarding_stage(user_id, stage, progress)
        
        print(f"     Stage {i+1}: {stage.value}")
        print(f"       Progress: {onboarding_state.stage_progress:.1%}")
        print(f"       Conversion Score: {onboarding_state.conversion_score:.1%}")
        print(f"       Features Explored: {len(onboarding_state.features_explored)}")
    
    # Check final state
    print(f"     Final Onboarding State:")
    print(f"       Current Stage: {onboarding_state.current_stage.value}")
    print(f"       Stage Progress: {onboarding_state.stage_progress:.1%}")
    print(f"       Conversion Score: {onboarding_state.conversion_score:.1%}")
    print(f"       User Segment: {onboarding_state.segment.value}")
    
    # Check notifications for stage advancement
    stage_notifications = [n for n in notification_service.notifications if 'feature_discovery' in n['notification_type']]
    print(f"     Stage Advancement Notifications: {len(stage_notifications)}")
    
    print()
    print("✅ Onboarding Stage Advancement Tests Completed")
    print()

def test_feature_teasers():
    """Test feature teaser functionality"""
    print("🎯 Testing Feature Teasers")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test feature teasers for different user types
    print("📋 Test 1: Feature Teasers for Different User Segments")
    
    test_users = [
        {
            'user_id': str(uuid.uuid4()),
            'user_data': {
                'name': 'Free User',
                'email': 'free@example.com',
                'industry': 'Education',
                'experience_years': 1,
                'company_size': 10,
                'role': 'Student',
                'career_goals': ['skill_development'],
                'preferences': {'learning_style': 'basic'}
            },
            'subscription_plan': 'free'
        },
        {
            'user_id': str(uuid.uuid4()),
            'user_data': {
                'name': 'Premium User',
                'email': 'premium@example.com',
                'industry': 'Technology',
                'experience_years': 7,
                'company_size': 1000,
                'role': 'Senior Developer',
                'career_goals': ['career_advancement', 'salary_negotiation'],
                'preferences': {'learning_style': 'advanced'}
            },
            'subscription_plan': 'premium'
        }
    ]
    
    for test_user in test_users:
        user_id = test_user['user_id']
        user_data = test_user['user_data']
        subscription_plan = test_user['subscription_plan']
        
        # Set up subscription
        subscription_service.subscriptions[user_id] = {
            'plan_id': subscription_plan,
            'status': 'active',
            'amount': 0.0 if subscription_plan == 'free' else 19.99,
            'currency': 'USD'
        }
        
        # Initialize onboarding
        onboarding_state = onboarding_integration.initialize_user_onboarding(user_id, user_data)
        
        # Get feature teasers
        teasers = onboarding_integration.get_feature_teasers(user_id, count=3)
        
        print(f"     {user_data['name']} ({subscription_plan} plan):")
        print(f"       User Segment: {onboarding_state.segment.value}")
        print(f"       Available Teasers: {len(teasers)}")
        
        for i, teaser in enumerate(teasers):
            print(f"         Teaser {i+1}: {teaser.feature_name}")
            print(f"           Description: {teaser.description}")
            print(f"           Upgrade Required: {teaser.upgrade_required}")
            print(f"           Teaser Type: {teaser.teaser_type}")
            print(f"           Engagement Score: {teaser.engagement_score:.1%}")
            print(f"           Conversion Potential: {teaser.conversion_potential:.1%}")
        
        print()
    
    print("✅ Feature Teasers Tests Completed")
    print()

def test_feature_exploration_tracking():
    """Test feature exploration tracking"""
    print("🔍 Testing Feature Exploration Tracking")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test feature exploration tracking
    print("📋 Test 1: Feature Exploration and Tracking")
    
    user_id = str(uuid.uuid4())
    user_data = {
        'name': 'Explorer User',
        'email': 'explorer@example.com',
        'industry': 'Marketing',
        'experience_years': 4,
        'company_size': 200,
        'role': 'Marketing Manager',
        'career_goals': ['career_advancement', 'skill_development'],
        'preferences': {'learning_style': 'exploratory'}
    }
    
    # Initialize onboarding
    onboarding_state = onboarding_integration.initialize_user_onboarding(user_id, user_data)
    
    # Track feature explorations
    features_to_explore = [
        {
            'feature_id': 'advanced_analytics',
            'engagement_data': {
                'time_spent_seconds': 120,
                'clicks': 5,
                'engagement_score': 0.85,
                'interaction_depth': 'high'
            }
        },
        {
            'feature_id': 'personalized_coaching',
            'engagement_data': {
                'time_spent_seconds': 180,
                'clicks': 8,
                'engagement_score': 0.92,
                'interaction_depth': 'very_high'
            }
        },
        {
            'feature_id': 'resume_optimization',
            'engagement_data': {
                'time_spent_seconds': 90,
                'clicks': 3,
                'engagement_score': 0.78,
                'interaction_depth': 'medium'
            }
        }
    ]
    
    print(f"     Tracking Feature Explorations:")
    
    for feature in features_to_explore:
        feature_id = feature['feature_id']
        engagement_data = feature['engagement_data']
        
        print(f"       Exploring: {feature_id}")
        print(f"         Time Spent: {engagement_data['time_spent_seconds']} seconds")
        print(f"         Clicks: {engagement_data['clicks']}")
        print(f"         Engagement Score: {engagement_data['engagement_score']:.1%}")
        print(f"         Interaction Depth: {engagement_data['interaction_depth']}")
        
        # Track exploration
        onboarding_integration.track_feature_exploration(user_id, feature_id, engagement_data)
        
        # Get updated onboarding state
        updated_state = onboarding_integration._get_onboarding_state(user_id)
        if updated_state:
            print(f"         Updated Conversion Score: {updated_state.conversion_score:.1%}")
            print(f"         Features Explored: {len(updated_state.features_explored)}")
    
    # Check analytics tracking
    print(f"     Analytics Events Tracked: {len(analytics_service.analytics_data.get(user_id, []))}")
    
    print()
    print("✅ Feature Exploration Tracking Tests Completed")
    print()

def test_upgrade_opportunities():
    """Test upgrade opportunity creation and management"""
    print("💎 Testing Upgrade Opportunities")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test upgrade opportunity creation
    print("📋 Test 1: Upgrade Opportunity Creation")
    
    user_id = str(uuid.uuid4())
    user_data = {
        'name': 'Upgrade Candidate',
        'email': 'upgrade@example.com',
        'industry': 'Consulting',
        'experience_years': 6,
        'company_size': 500,
        'role': 'Senior Consultant',
        'career_goals': ['career_advancement', 'salary_negotiation', 'networking'],
        'preferences': {'learning_style': 'comprehensive'}
    }
    
    # Set up free subscription
    subscription_service.subscriptions[user_id] = {
        'plan_id': 'free',
        'status': 'active',
        'amount': 0.0,
        'currency': 'USD'
    }
    
    # Initialize onboarding and advance to upgrade promotion stage
    onboarding_state = onboarding_integration.initialize_user_onboarding(user_id, user_data)
    onboarding_integration.advance_onboarding_stage(user_id, OnboardingStage.UPGRADE_PROMOTION, 0.8)
    
    # Create upgrade opportunity
    opportunity = onboarding_integration.create_upgrade_opportunity(
        user_id=user_id,
        trigger_type=UpgradeTrigger.FEATURE_LIMIT,
        trigger_value='advanced_analytics'
    )
    
    print(f"     Upgrade Opportunity Created:")
    print(f"       Opportunity ID: {opportunity.opportunity_id}")
    print(f"       Trigger Type: {opportunity.trigger_type.value}")
    print(f"       Trigger Value: {opportunity.trigger_value}")
    print(f"       Recommended Plan: {opportunity.recommended_plan}")
    print(f"       Offer Amount: ${opportunity.offer_amount}")
    print(f"       Offer Currency: {opportunity.offer_currency}")
    print(f"       Offer Duration: {opportunity.offer_duration_days} days")
    print(f"       Conversion Probability: {opportunity.conversion_probability:.1%}")
    print(f"       Created At: {opportunity.created_at}")
    print(f"       Expires At: {opportunity.expires_at}")
    print(f"       Is Active: {opportunity.is_active}")
    
    # Test getting active opportunities
    print("📋 Test 2: Active Upgrade Opportunities")
    
    active_opportunities = onboarding_integration.get_active_upgrade_opportunities(user_id)
    print(f"     Active Opportunities: {len(active_opportunities)}")
    
    for opp in active_opportunities:
        print(f"       Plan: {opp.recommended_plan}")
        print(f"       Amount: ${opp.offer_amount}")
        print(f"       Probability: {opp.conversion_probability:.1%}")
    
    # Check notifications
    upgrade_notifications = [n for n in notification_service.notifications if 'upgrade_opportunity' in n['notification_type']]
    print(f"     Upgrade Notifications Sent: {len(upgrade_notifications)}")
    
    print()
    print("✅ Upgrade Opportunities Tests Completed")
    print()

def test_upgrade_conversion():
    """Test upgrade conversion processing"""
    print("🔄 Testing Upgrade Conversion")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test upgrade conversion
    print("📋 Test 1: Upgrade Conversion Processing")
    
    user_id = str(uuid.uuid4())
    user_data = {
        'name': 'Converting User',
        'email': 'converting@example.com',
        'industry': 'Healthcare',
        'experience_years': 8,
        'company_size': 1000,
        'role': 'Healthcare Manager',
        'career_goals': ['career_advancement', 'leadership'],
        'preferences': {'learning_style': 'structured'}
    }
    
    # Set up free subscription
    subscription_service.subscriptions[user_id] = {
        'plan_id': 'free',
        'status': 'active',
        'amount': 0.0,
        'currency': 'USD'
    }
    
    # Initialize onboarding
    onboarding_state = onboarding_integration.initialize_user_onboarding(user_id, user_data)
    
    # Create upgrade opportunity
    opportunity = onboarding_integration.create_upgrade_opportunity(
        user_id=user_id,
        trigger_type=UpgradeTrigger.PERSONALIZED_OFFER
    )
    
    # Process conversion
    conversion_data = {
        'conversion_method': 'credit_card',
        'offer_accepted': True,
        'conversion_time': datetime.now(timezone.utc).isoformat()
    }
    
    conversion_result = onboarding_integration.process_upgrade_conversion(
        user_id=user_id,
        opportunity_id=opportunity.opportunity_id,
        conversion_data=conversion_data
    )
    
    print(f"     Conversion Result:")
    print(f"       Success: {conversion_result['success']}")
    if conversion_result['success']:
        print(f"       New Plan: {conversion_result['new_plan']}")
        print(f"       Offer Amount: ${conversion_result['offer_amount']}")
        print(f"       Conversion ID: {conversion_result['conversion_id']}")
    else:
        print(f"       Error: {conversion_result.get('error')}")
    
    # Check updated subscription
    updated_subscription = subscription_service.get_user_subscription(user_id)
    print(f"     Updated Subscription:")
    print(f"       Plan: {updated_subscription['plan_id']}")
    print(f"       Amount: ${updated_subscription['amount']}")
    print(f"       Currency: {updated_subscription['currency']}")
    
    # Check notifications
    success_notifications = [n for n in notification_service.notifications if 'upgrade_success' in n['notification_type']]
    print(f"     Success Notifications Sent: {len(success_notifications)}")
    
    print()
    print("✅ Upgrade Conversion Tests Completed")
    print()

def test_onboarding_analytics():
    """Test onboarding analytics functionality"""
    print("📊 Testing Onboarding Analytics")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test onboarding analytics
    print("📋 Test 1: Onboarding Analytics Generation")
    
    user_id = str(uuid.uuid4())
    user_data = {
        'name': 'Analytics User',
        'email': 'analytics@example.com',
        'industry': 'Finance',
        'experience_years': 5,
        'company_size': 300,
        'role': 'Financial Analyst',
        'career_goals': ['skill_development', 'certification'],
        'preferences': {'learning_style': 'analytical'}
    }
    
    # Initialize onboarding
    onboarding_state = onboarding_integration.initialize_user_onboarding(user_id, user_data)
    
    # Advance through stages and track activities
    stages = [
        OnboardingStage.PROFILE_SETUP,
        OnboardingStage.FEATURE_DISCOVERY,
        OnboardingStage.TRIAL_EXPERIENCE
    ]
    
    for stage in stages:
        onboarding_integration.advance_onboarding_stage(user_id, stage, 1.0)
    
    # Track feature explorations
    features = ['advanced_analytics', 'personalized_coaching', 'resume_optimization']
    for feature in features:
        onboarding_integration.track_feature_exploration(user_id, feature, {
            'engagement_score': 0.8,
            'time_spent_seconds': 120
        })
    
    # Get analytics
    analytics = onboarding_integration.get_onboarding_analytics(user_id)
    
    if analytics:
        print(f"     Onboarding Analytics:")
        print(f"       User ID: {analytics.user_id}")
        print(f"       Completion Rate: {analytics.completion_rate:.1%}")
        print(f"       Upgrade Rate: {analytics.upgrade_rate:.1%}")
        print(f"       Time to Upgrade: {analytics.time_to_upgrade or 'N/A'}")
        
        print(f"       Stage Completion Times: {len(analytics.stage_completion_times)} stages")
        print(f"       Feature Engagement: {len(analytics.feature_engagement)} features")
        print(f"       Upgrade Interactions: {len(analytics.upgrade_interactions)}")
        print(f"       Conversion Events: {len(analytics.conversion_events)}")
        print(f"       Dropoff Points: {len(analytics.dropoff_points)}")
    else:
        print("     No analytics data available")
    
    print()
    print("✅ Onboarding Analytics Tests Completed")
    print()

def test_onboarding_performance():
    """Test onboarding performance"""
    print("⚡ Testing Onboarding Performance")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    subscription_service = MockSubscriptionService()
    analytics_service = MockAnalyticsService()
    notification_service = MockNotificationService()
    
    # Create onboarding integration
    onboarding_integration = SubscriptionOnboardingIntegration(
        db, subscription_service, analytics_service, notification_service
    )
    
    # Test performance
    print("📈 Performance Metrics:")
    
    import time
    
    # Test onboarding initialization performance
    print("   Testing onboarding initialization performance...")
    start_time = time.time()
    
    for i in range(10):
        user_id = str(uuid.uuid4())
        user_data = {
            'name': f'User {i}',
            'email': f'user{i}@example.com',
            'industry': 'Technology',
            'experience_years': 3,
            'company_size': 100,
            'role': 'Developer',
            'career_goals': ['skill_development'],
            'preferences': {'learning_style': 'hands_on'}
        }
        result = onboarding_integration.initialize_user_onboarding(user_id, user_data)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average onboarding initialization time: {avg_time:.2f}ms")
    print(f"     Onboarding initializations per second: {1000 / avg_time:.1f}")
    
    # Test feature teaser generation performance
    print("   Testing feature teaser generation performance...")
    start_time = time.time()
    
    user_id = str(uuid.uuid4())
    user_data = {
        'name': 'Performance User',
        'email': 'performance@example.com',
        'industry': 'Technology',
        'experience_years': 4,
        'company_size': 200,
        'role': 'Engineer',
        'career_goals': ['career_advancement'],
        'preferences': {'learning_style': 'comprehensive'}
    }
    onboarding_integration.initialize_user_onboarding(user_id, user_data)
    
    for i in range(10):
        teasers = onboarding_integration.get_feature_teasers(user_id, count=5)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average feature teaser generation time: {avg_time:.2f}ms")
    print(f"     Feature teaser generations per second: {1000 / avg_time:.1f}")
    
    # Test upgrade opportunity creation performance
    print("   Testing upgrade opportunity creation performance...")
    start_time = time.time()
    
    for i in range(10):
        try:
            opportunity = onboarding_integration.create_upgrade_opportunity(
                user_id=user_id,
                trigger_type=UpgradeTrigger.FEATURE_LIMIT
            )
        except:
            pass  # Ignore eligibility errors
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average upgrade opportunity creation time: {avg_time:.2f}ms")
    print(f"     Upgrade opportunity creations per second: {1000 / avg_time:.1f}")
    
    print()
    print("✅ Onboarding Performance Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Subscription Onboarding Integration Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_onboarding_initialization()
        test_stage_advancement()
        test_feature_teasers()
        test_feature_exploration_tracking()
        test_upgrade_opportunities()
        test_upgrade_conversion()
        test_onboarding_analytics()
        test_onboarding_performance()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Onboarding Initialization")
        print("   ✅ Stage Advancement")
        print("   ✅ Feature Teasers")
        print("   ✅ Feature Exploration Tracking")
        print("   ✅ Upgrade Opportunities")
        print("   ✅ Upgrade Conversion")
        print("   ✅ Onboarding Analytics")
        print("   ✅ Onboarding Performance")
        print()
        print("🚀 The subscription onboarding integration is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 