"""
Smart Upgrade Prompts Example for MINGUS
Demonstrates smart upgrade prompts with usage tracking, contextual suggestions, and A/B testing
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.feature_access_service import FeatureType, UpgradePromptType, ABTestVariant
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, FeatureUsage

class SmartUpgradePromptsExample:
    """Example demonstrating smart upgrade prompts with A/B testing and contextual suggestions"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_smart_prompts_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for smart upgrade prompts demonstration"""
        # Create pricing tiers
        budget_tier = PricingTier(
            tier_type='budget',
            name='Budget',
            description='Basic features for individual users',
            monthly_price=15.00,
            yearly_price=150.00,
            max_health_checkins_per_month=4,
            max_financial_reports_per_month=2,
            max_ai_insights_per_month=0
        )
        
        mid_tier = PricingTier(
            tier_type='mid_tier',
            name='Mid-Tier',
            description='Enhanced features for serious users',
            monthly_price=35.00,
            yearly_price=350.00,
            max_health_checkins_per_month=12,
            max_financial_reports_per_month=10,
            max_ai_insights_per_month=50
        )
        
        professional_tier = PricingTier(
            tier_type='professional',
            name='Professional',
            description='Complete solution for professionals',
            monthly_price=75.00,
            yearly_price=750.00,
            max_health_checkins_per_month=-1,
            max_financial_reports_per_month=-1,
            max_ai_insights_per_month=-1
        )
        
        self.db_session.add_all([budget_tier, mid_tier, professional_tier])
        self.db_session.commit()
        
        # Create sample customers
        customers = []
        for i, tier in enumerate(['budget', 'mid_tier']):
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_{tier}_demo_{i}',
                email=f'{tier}.user{i}@example.com',
                name=f'{tier.title()} User {i}',
                address={'country': 'US', 'state': 'NY'}
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with different usage patterns
        subscriptions = []
        feature_usages = []
        
        # Budget user with high usage (approaching limits)
        budget_subscription = Subscription(
            customer_id=customers[0].id,
            pricing_tier_id=budget_tier.id,
            stripe_subscription_id='sub_budget_high_usage',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=20),
            current_period_end=datetime.utcnow() + timedelta(days=10),
            billing_cycle='monthly',
            amount=15.00,
            currency='USD'
        )
        subscriptions.append(budget_subscription)
        
        # Mid-tier user with moderate usage
        mid_tier_subscription = Subscription(
            customer_id=customers[1].id,
            pricing_tier_id=mid_tier.id,
            stripe_subscription_id='sub_mid_tier_moderate',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=15),
            billing_cycle='monthly',
            amount=35.00,
            currency='USD'
        )
        subscriptions.append(mid_tier_subscription)
        
        self.db_session.add_all(subscriptions)
        self.db_session.commit()
        
        # Create feature usage records
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        # Budget user: High usage (3/4 health check-ins, 1/2 financial reports)
        budget_usage = FeatureUsage(
            subscription_id=budget_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=3,  # 75% usage - approaching limit
            financial_reports_used=1,  # 50% usage
            ai_insights_used=0,
            custom_reports_used=0,
            team_members_used=0,
            support_requests_used=1,  # Used support
            career_risk_management_used=0,
            dedicated_account_manager_used=0
        )
        feature_usages.append(budget_usage)
        
        # Mid-tier user: Moderate usage (8/12 health check-ins, 6/10 financial reports)
        mid_tier_usage = FeatureUsage(
            subscription_id=mid_tier_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=8,  # 67% usage
            financial_reports_used=6,  # 60% usage
            ai_insights_used=35,  # 70% usage - approaching limit
            custom_reports_used=3,  # 60% usage
            team_members_used=0,
            support_requests_used=2,  # Used support
            career_risk_management_used=5,
            dedicated_account_manager_used=0
        )
        feature_usages.append(mid_tier_usage)
        
        self.db_session.add_all(feature_usages)
        self.db_session.commit()
        
        self.budget_subscription = budget_subscription
        self.mid_tier_subscription = mid_tier_subscription
        self.budget_usage = budget_usage
        self.mid_tier_usage = mid_tier_usage
    
    def demonstrate_usage_approaching_limits_prompts(self):
        """Demonstrate upgrade prompts for usage approaching limits"""
        print("\n=== Usage Approaching Limits Prompts ===")
        
        print(f"\n🔄 Testing Budget Tier - Health Check-ins Approaching Limit:")
        
        # Test health check-ins approaching limit (3/4 = 75%)
        prompt_result = self.payment_service.generate_smart_upgrade_prompt(
            subscription_id=self.budget_subscription.id,
            feature_type='health_checkin'
        )
        
        if prompt_result['success']:
            prompt = prompt_result['upgrade_prompt']
            print(f"   ✅ Smart prompt generated successfully")
            print(f"   Title: {prompt['title']}")
            print(f"   Message: {prompt['message']}")
            print(f"   Type: {prompt['type']}")
            print(f"   Urgency: {prompt['urgency']}")
            print(f"   A/B Variant: {prompt_result['ab_variant']}")
            print(f"   Benefits: {', '.join(prompt['benefits'][:3])}...")
        else:
            print(f"   ❌ Failed: {prompt_result['error']}")
        
        print(f"\n🔄 Testing Mid-Tier - AI Insights Approaching Limit:")
        
        # Test AI insights approaching limit (35/50 = 70%)
        prompt_result = self.payment_service.generate_smart_upgrade_prompt(
            subscription_id=self.mid_tier_subscription.id,
            feature_type='ai_insight'
        )
        
        if prompt_result['success']:
            prompt = prompt_result['upgrade_prompt']
            print(f"   ✅ Smart prompt generated successfully")
            print(f"   Title: {prompt['title']}")
            print(f"   Message: {prompt['message']}")
            print(f"   Type: {prompt['type']}")
            print(f"   Urgency: {prompt['urgency']}")
            print(f"   A/B Variant: {prompt_result['ab_variant']}")
            print(f"   Benefits: {', '.join(prompt['benefits'][:3])}...")
        else:
            print(f"   ❌ Failed: {prompt_result['error']}")
    
    def demonstrate_limit_reached_prompts(self):
        """Demonstrate upgrade prompts for limits reached"""
        print("\n=== Limit Reached Prompts ===")
        
        # Simulate reaching the limit by temporarily updating usage
        original_usage = self.budget_usage.health_checkins_used
        self.budget_usage.health_checkins_used = 4  # 100% usage
        self.db_session.commit()
        
        print(f"\n🔄 Testing Budget Tier - Health Check-ins Limit Reached:")
        
        prompt_result = self.payment_service.generate_smart_upgrade_prompt(
            subscription_id=self.budget_subscription.id,
            feature_type='health_checkin'
        )
        
        if prompt_result['success']:
            prompt = prompt_result['upgrade_prompt']
            print(f"   ✅ Limit reached prompt generated")
            print(f"   Title: {prompt['title']}")
            print(f"   Message: {prompt['message']}")
            print(f"   Type: {prompt['type']}")
            print(f"   Urgency: {prompt['urgency']}")
            print(f"   A/B Variant: {prompt_result['ab_variant']}")
        else:
            print(f"   ❌ Failed: {prompt_result['error']}")
        
        # Restore original usage
        self.budget_usage.health_checkins_used = original_usage
        self.db_session.commit()
    
    def demonstrate_feature_unavailable_prompts(self):
        """Demonstrate upgrade prompts for unavailable features"""
        print("\n=== Feature Unavailable Prompts ===")
        
        print(f"\n🔄 Testing Budget Tier - AI Insights Unavailable:")
        
        # Test AI insights (not available in Budget tier)
        prompt_result = self.payment_service.generate_smart_upgrade_prompt(
            subscription_id=self.budget_subscription.id,
            feature_type='ai_insight'
        )
        
        if prompt_result['success']:
            prompt = prompt_result['upgrade_prompt']
            print(f"   ✅ Feature unavailable prompt generated")
            print(f"   Title: {prompt['title']}")
            print(f"   Message: {prompt['message']}")
            print(f"   Type: {prompt['type']}")
            print(f"   Urgency: {prompt['urgency']}")
            print(f"   A/B Variant: {prompt_result['ab_variant']}")
        else:
            print(f"   ❌ Failed: {prompt_result['error']}")
        
        print(f"\n🔄 Testing Mid-Tier - Team Members Unavailable:")
        
        # Test team members (not available in Mid-tier)
        prompt_result = self.payment_service.generate_smart_upgrade_prompt(
            subscription_id=self.mid_tier_subscription.id,
            feature_type='team_members'
        )
        
        if prompt_result['success']:
            prompt = prompt_result['upgrade_prompt']
            print(f"   ✅ Feature unavailable prompt generated")
            print(f"   Title: {prompt['title']}")
            print(f"   Message: {prompt['message']}")
            print(f"   Type: {prompt['type']}")
            print(f"   Urgency: {prompt['urgency']}")
            print(f"   A/B Variant: {prompt_result['ab_variant']}")
        else:
            print(f"   ❌ Failed: {prompt_result['error']}")
    
    def demonstrate_contextual_prompts(self):
        """Demonstrate contextual upgrade prompts"""
        print("\n=== Contextual Upgrade Prompts ===")
        
        print(f"\n🔄 Testing Budget Tier - Contextual Prompt:")
        
        # Test contextual prompt without specific feature
        prompt_result = self.payment_service.generate_smart_upgrade_prompt(
            subscription_id=self.budget_subscription.id,
            context={'user_behavior': 'high_usage'}
        )
        
        if prompt_result['success']:
            prompt = prompt_result['upgrade_prompt']
            print(f"   ✅ Contextual prompt generated")
            print(f"   Title: {prompt['title']}")
            print(f"   Message: {prompt['message']}")
            print(f"   Type: {prompt['type']}")
            print(f"   Urgency: {prompt['urgency']}")
            print(f"   A/B Variant: {prompt_result['ab_variant']}")
        else:
            print(f"   ❌ Failed: {prompt_result['error']}")
        
        print(f"\n🔄 Testing Mid-Tier - Contextual Prompt:")
        
        # Test contextual prompt for mid-tier user
        prompt_result = self.payment_service.generate_smart_upgrade_prompt(
            subscription_id=self.mid_tier_subscription.id,
            context={'user_behavior': 'power_user'}
        )
        
        if prompt_result['success']:
            prompt = prompt_result['upgrade_prompt']
            print(f"   ✅ Contextual prompt generated")
            print(f"   Title: {prompt['title']}")
            print(f"   Message: {prompt['message']}")
            print(f"   Type: {prompt['type']}")
            print(f"   Urgency: {prompt['urgency']}")
            print(f"   A/B Variant: {prompt_result['ab_variant']}")
        else:
            print(f"   ❌ Failed: {prompt_result['error']}")
    
    def demonstrate_ab_testing(self):
        """Demonstrate A/B testing for upgrade prompts"""
        print("\n=== A/B Testing Demonstration ===")
        
        print(f"\n🔄 Testing A/B Test Variants:")
        
        # Test multiple prompts to see different A/B variants
        variants_seen = set()
        
        for i in range(10):
            prompt_result = self.payment_service.generate_smart_upgrade_prompt(
                subscription_id=self.budget_subscription.id,
                feature_type='health_checkin'
            )
            
            if prompt_result['success']:
                variant = prompt_result['ab_variant']
                variants_seen.add(variant)
                prompt = prompt_result['upgrade_prompt']
                
                if i < 3:  # Show first 3 examples
                    print(f"   Example {i + 1}:")
                    print(f"      Variant: {variant}")
                    print(f"      Title: {prompt['title']}")
                    print(f"      CTA: {prompt.get('cta_text', 'N/A')}")
                    print(f"      Urgency Level: {prompt.get('urgency_level', 'N/A')}")
        
        print(f"\n   📊 A/B Variants Observed: {', '.join(variants_seen)}")
        print(f"   📊 Total Variants: {len(variants_seen)}")
    
    def demonstrate_usage_approaching_limits_check(self):
        """Demonstrate checking for usage approaching limits"""
        print("\n=== Usage Approaching Limits Check ===")
        
        print(f"\n🔄 Checking Budget Tier Usage:")
        
        limits_result = self.payment_service.check_usage_approaching_limits(
            subscription_id=self.budget_subscription.id
        )
        
        if limits_result['success']:
            approaching_limits = limits_result['approaching_limits']
            print(f"   ✅ Found {len(approaching_limits)} features approaching limits")
            
            for limit_info in approaching_limits:
                print(f"   📊 {limit_info['feature']}: {limit_info['current_usage']}/{limit_info['limit']} ({limit_info['usage_percentage']:.1f}%)")
                
                if limit_info['upgrade_prompt']['success']:
                    prompt = limit_info['upgrade_prompt']['upgrade_prompt']
                    print(f"      💡 Upgrade Prompt: {prompt['title']}")
        else:
            print(f"   ❌ Failed: {limits_result['error']}")
        
        print(f"\n🔄 Checking Mid-Tier Usage:")
        
        limits_result = self.payment_service.check_usage_approaching_limits(
            subscription_id=self.mid_tier_subscription.id
        )
        
        if limits_result['success']:
            approaching_limits = limits_result['approaching_limits']
            print(f"   ✅ Found {len(approaching_limits)} features approaching limits")
            
            for limit_info in approaching_limits:
                print(f"   📊 {limit_info['feature']}: {limit_info['current_usage']}/{limit_info['limit']} ({limit_info['usage_percentage']:.1f}%)")
                
                if limit_info['upgrade_prompt']['success']:
                    prompt = limit_info['upgrade_prompt']['upgrade_prompt']
                    print(f"      💡 Upgrade Prompt: {prompt['title']}")
        else:
            print(f"   ❌ Failed: {limits_result['error']}")
    
    def demonstrate_contextual_suggestions(self):
        """Demonstrate contextual upgrade suggestions"""
        print("\n=== Contextual Upgrade Suggestions ===")
        
        print(f"\n🔄 Getting Budget Tier Suggestions:")
        
        suggestions_result = self.payment_service.get_contextual_upgrade_suggestions(
            subscription_id=self.budget_subscription.id,
            user_context={'team_size': 1, 'integration_needs': False}
        )
        
        if suggestions_result['success']:
            suggestions = suggestions_result['suggestions']
            print(f"   ✅ Found {len(suggestions)} contextual suggestions")
            
            for suggestion in suggestions:
                print(f"   💡 {suggestion['type']}: {suggestion['message']}")
                print(f"      Recommendation: {suggestion['recommendation']}")
                print(f"      Priority: {suggestion['priority']}")
        else:
            print(f"   ❌ Failed: {suggestions_result['error']}")
        
        print(f"\n🔄 Getting Mid-Tier Suggestions:")
        
        suggestions_result = self.payment_service.get_contextual_upgrade_suggestions(
            subscription_id=self.mid_tier_subscription.id,
            user_context={'team_size': 3, 'integration_needs': True}
        )
        
        if suggestions_result['success']:
            suggestions = suggestions_result['suggestions']
            print(f"   ✅ Found {len(suggestions)} contextual suggestions")
            
            for suggestion in suggestions:
                print(f"   💡 {suggestion['type']}: {suggestion['message']}")
                print(f"      Recommendation: {suggestion['recommendation']}")
                print(f"      Priority: {suggestion['priority']}")
        else:
            print(f"   ❌ Failed: {suggestions_result['error']}")
    
    def demonstrate_upgrade_prompt_analytics(self):
        """Demonstrate upgrade prompt analytics"""
        print("\n=== Upgrade Prompt Analytics ===")
        
        print(f"\n🔄 Getting Analytics:")
        
        analytics_result = self.payment_service.get_upgrade_prompt_analytics(
            date_range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow())
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            print(f"   ✅ Analytics retrieved successfully")
            print(f"   📊 Total Displays: {analytics['total_displays']}")
            print(f"   📊 Conversion Rate: {analytics['conversion_rate']:.2f}%")
            print(f"   📊 Variant Performance: {len(analytics['variant_performance'])} variants")
            print(f"   📊 Feature Performance: {len(analytics['feature_performance'])} features")
            print(f"   📊 Time Performance: {len(analytics['time_performance'])} time periods")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
    
    def demonstrate_comprehensive_smart_prompts(self):
        """Demonstrate comprehensive smart upgrade prompt scenarios"""
        print("\n=== Comprehensive Smart Prompts ===")
        
        scenarios = [
            {
                'name': 'Budget User - High Usage Pattern',
                'subscription_id': self.budget_subscription.id,
                'feature_type': 'health_checkin',
                'context': {'user_behavior': 'high_usage', 'session_duration': 'long'}
            },
            {
                'name': 'Mid-Tier User - Power User Pattern',
                'subscription_id': self.mid_tier_subscription.id,
                'feature_type': 'ai_insight',
                'context': {'user_behavior': 'power_user', 'feature_depth': 'advanced'}
            },
            {
                'name': 'Budget User - Team Collaboration Need',
                'subscription_id': self.budget_subscription.id,
                'feature_type': 'team_members',
                'context': {'team_size': 3, 'collaboration_needs': True}
            },
            {
                'name': 'Mid-Tier User - API Integration Need',
                'subscription_id': self.mid_tier_subscription.id,
                'feature_type': 'api_access',
                'context': {'integration_needs': True, 'workflow_automation': True}
            }
        ]
        
        for scenario in scenarios:
            print(f"\n🎯 Scenario: {scenario['name']}")
            
            prompt_result = self.payment_service.generate_smart_upgrade_prompt(
                subscription_id=scenario['subscription_id'],
                feature_type=scenario['feature_type'],
                context=scenario['context']
            )
            
            if prompt_result['success']:
                prompt = prompt_result['upgrade_prompt']
                print(f"   ✅ Smart prompt generated")
                print(f"   Title: {prompt['title']}")
                print(f"   Type: {prompt['type']}")
                print(f"   Urgency: {prompt['urgency']}")
                print(f"   A/B Variant: {prompt_result['ab_variant']}")
                print(f"   Benefits: {', '.join(prompt['benefits'][:2])}...")
            else:
                print(f"   ❌ Failed: {prompt_result['error']}")
    
    def run_all_demonstrations(self):
        """Run all smart upgrade prompt demonstrations"""
        print("🚀 MINGUS Smart Upgrade Prompts Demonstration")
        print("=" * 60)
        
        try:
            self.demonstrate_usage_approaching_limits_prompts()
            self.demonstrate_limit_reached_prompts()
            self.demonstrate_feature_unavailable_prompts()
            self.demonstrate_contextual_prompts()
            self.demonstrate_ab_testing()
            self.demonstrate_usage_approaching_limits_check()
            self.demonstrate_contextual_suggestions()
            self.demonstrate_upgrade_prompt_analytics()
            self.demonstrate_comprehensive_smart_prompts()
            
            print("\n✅ All smart upgrade prompt demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = SmartUpgradePromptsExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 