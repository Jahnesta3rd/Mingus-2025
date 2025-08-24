"""
Graceful Degradation Example for MINGUS
Demonstrates clear messaging, alternative suggestions, temporary access, and user education
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, FeatureUsage

class GracefulDegradationExample:
    """Example demonstrating graceful degradation with user education"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_graceful_degradation_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for graceful degradation demonstration"""
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
        for i, tier in enumerate(['budget', 'mid_tier', 'professional']):
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_{tier}_graceful_demo_{i}',
                email=f'{tier}.graceful.user{i}@example.com',
                name=f'{tier.title()} Graceful User {i}',
                address={'country': 'US', 'state': 'CA'}
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with different states
        subscriptions = []
        
        # Budget user with limit reached
        budget_subscription = Subscription(
            customer_id=customers[0].id,
            pricing_tier_id=budget_tier.id,
            stripe_subscription_id='sub_budget_limit_reached',
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
        
        # Professional user with unlimited access
        professional_subscription = Subscription(
            customer_id=customers[2].id,
            pricing_tier_id=professional_tier.id,
            stripe_subscription_id='sub_professional_unlimited',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=10),
            current_period_end=datetime.utcnow() + timedelta(days=20),
            billing_cycle='monthly',
            amount=75.00,
            currency='USD'
        )
        subscriptions.append(professional_subscription)
        
        self.db_session.add_all(subscriptions)
        self.db_session.commit()
        
        # Create feature usage records
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        # Budget user: Limit reached (4/4 health check-ins, 2/2 financial reports)
        budget_usage = FeatureUsage(
            subscription_id=budget_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=4,  # Limit reached
            financial_reports_used=2,  # Limit reached
            ai_insights_used=0,
            custom_reports_used=0,
            team_members_used=0,
            support_requests_used=1,
            career_risk_management_used=0,
            dedicated_account_manager_used=0
        )
        
        # Mid-tier user: Moderate usage (8/12 health check-ins, 6/10 financial reports)
        mid_tier_usage = FeatureUsage(
            subscription_id=mid_tier_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=8,  # 67% usage
            financial_reports_used=6,  # 60% usage
            ai_insights_used=35,  # 70% usage
            custom_reports_used=3,  # 60% usage
            team_members_used=0,
            support_requests_used=2,
            career_risk_management_used=5,
            dedicated_account_manager_used=0
        )
        
        # Professional user: Unlimited usage
        professional_usage = FeatureUsage(
            subscription_id=professional_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=25,  # Unlimited
            financial_reports_used=15,  # Unlimited
            ai_insights_used=100,  # Unlimited
            custom_reports_used=8,  # Unlimited
            team_members_used=5,  # 5/10 team members
            support_requests_used=3,  # Unlimited
            career_risk_management_used=12,  # Unlimited
            dedicated_account_manager_used=1  # 1/1 account manager
        )
        
        self.db_session.add_all([budget_usage, mid_tier_usage, professional_usage])
        self.db_session.commit()
        
        self.budget_subscription = budget_subscription
        self.mid_tier_subscription = mid_tier_subscription
        self.professional_subscription = professional_subscription
    
    def demonstrate_clear_messaging(self):
        """Demonstrate clear messaging when limits are reached"""
        print("\n=== Clear Messaging Demonstration ===")
        
        print(f"\n🔄 Testing Clear Messaging:")
        
        # Test limit reached messaging
        print(f"\n1. Limit Reached - Budget User:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='health_checkin',
            context={'user_context': 'monthly_review'}
        )
        
        if degradation_result['success']:
            graceful_info = degradation_result['graceful_degradation']
            print(f"   ✅ Graceful degradation applied")
            print(f"   📢 Message: {graceful_info['message']}")
            print(f"   💡 Suggestion: {graceful_info['suggestion']}")
            print(f"   🔄 Decision: {degradation_result['decision']}")
            
            if graceful_info.get('upgrade_prompt'):
                prompt = graceful_info['upgrade_prompt']
                print(f"   🚀 Upgrade Prompt:")
                print(f"      Title: {prompt['title']}")
                print(f"      Message: {prompt['message']}")
                print(f"      CTA: {prompt['cta_text']}")
                print(f"      Urgency: {prompt['urgency_level']}")
        else:
            print(f"   ❌ Failed: {degradation_result['error']}")
        
        # Test feature unavailable messaging
        print(f"\n2. Feature Unavailable - Budget User:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='ai_insight',
            context={'user_context': 'financial_analysis'}
        )
        
        if degradation_result['success']:
            graceful_info = degradation_result['graceful_degradation']
            print(f"   ✅ Graceful degradation applied")
            print(f"   📢 Message: {graceful_info['message']}")
            print(f"   💡 Suggestion: {graceful_info['suggestion']}")
            print(f"   🔄 Decision: {degradation_result['decision']}")
            
            if graceful_info.get('educational_content'):
                education = graceful_info['educational_content']
                print(f"   📚 Educational Content:")
                print(f"      Title: {education['title']}")
                print(f"      Content: {education['content']}")
        else:
            print(f"   ❌ Failed: {degradation_result['error']}")
    
    def demonstrate_alternative_suggestions(self):
        """Demonstrate alternative feature suggestions"""
        print("\n=== Alternative Suggestions Demonstration ===")
        
        print(f"\n🔄 Testing Alternative Suggestions:")
        
        # Test alternatives for limit reached
        print(f"\n1. Alternatives for Limit Reached:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='health_checkin'
        )
        
        if degradation_result['success']:
            graceful_info = degradation_result['graceful_degradation']
            alternatives = graceful_info.get('alternative_features', [])
            
            print(f"   ✅ Alternatives provided")
            print(f"   📋 Alternative Features:")
            for i, alt in enumerate(alternatives, 1):
                print(f"      {i}. {alt['name']} ({alt['icon']})")
                print(f"         Description: {alt['description']}")
                print(f"         Action: {alt['action']}")
                print(f"         Tier Required: {alt['tier_required']}")
        else:
            print(f"   ❌ Failed: {degradation_result['error']}")
        
        # Test alternatives for unavailable feature
        print(f"\n2. Alternatives for Unavailable Feature:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='custom_reports'
        )
        
        if degradation_result['success']:
            graceful_info = degradation_result['graceful_degradation']
            alternatives = graceful_info.get('alternative_features', [])
            
            print(f"   ✅ Alternatives provided")
            print(f"   📋 Alternative Features:")
            for i, alt in enumerate(alternatives, 1):
                print(f"      {i}. {alt['name']} ({alt['icon']})")
                print(f"         Description: {alt['description']}")
                print(f"         Action: {alt['action']}")
        else:
            print(f"   ❌ Failed: {degradation_result['error']}")
    
    def demonstrate_temporary_access(self):
        """Demonstrate temporary access for edge cases"""
        print("\n=== Temporary Access Demonstration ===")
        
        print(f"\n🔄 Testing Temporary Access:")
        
        # Test temporary access for critical feature
        print(f"\n1. Temporary Access for Critical Feature:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='health_checkin',
            context={'emergency_access': True, 'critical_need': True}
        )
        
        if degradation_result['success']:
            graceful_info = degradation_result['graceful_degradation']
            temp_access = graceful_info.get('temporary_access', False)
            
            print(f"   ✅ Temporary access evaluated")
            print(f"   🔓 Temporary Access: {temp_access}")
            
            if temp_access:
                print(f"   ⏰ Duration: {graceful_info.get('temporary_access_duration', 'N/A')}")
                print(f"   📝 Reason: {graceful_info.get('temporary_access_reason', 'N/A')}")
            else:
                print(f"   📋 Conditions for temporary access:")
                conditions = graceful_info.get('conditions', [])
                for condition in conditions:
                    print(f"      - {condition}")
        else:
            print(f"   ❌ Failed: {degradation_result['error']}")
        
        # Test temporary access for regular usage
        print(f"\n2. Temporary Access for Regular Usage:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='financial_report',
            context={'regular_usage': True}
        )
        
        if degradation_result['success']:
            graceful_info = degradation_result['graceful_degradation']
            temp_access = graceful_info.get('temporary_access', False)
            
            print(f"   ✅ Temporary access evaluated")
            print(f"   🔓 Temporary Access: {temp_access}")
            
            if not temp_access:
                print(f"   📋 Conditions for temporary access:")
                conditions = graceful_info.get('conditions', [])
                for condition in conditions:
                    print(f"      - {condition}")
        else:
            print(f"   ❌ Failed: {degradation_result['error']}")
    
    def demonstrate_user_education(self):
        """Demonstrate user education about tier benefits"""
        print("\n=== User Education Demonstration ===")
        
        print(f"\n🔄 Testing User Education:")
        
        # Test education for budget user
        print(f"\n1. Education for Budget User:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='ai_insight'
        )
        
        if degradation_result['success'] and 'user_education' in degradation_result:
            education = degradation_result['user_education']
            
            print(f"   ✅ User education provided")
            
            # Current tier info
            current_tier = education.get('current_tier_info', {})
            print(f"   📊 Current Tier Information:")
            print(f"      Name: {current_tier.get('name', 'N/A')}")
            print(f"      Description: {current_tier.get('description', 'N/A')}")
            print(f"      Best For: {current_tier.get('best_for', 'N/A')}")
            
            # Current benefits
            benefits = current_tier.get('current_benefits', [])
            print(f"      Current Benefits:")
            for benefit in benefits:
                print(f"         - {benefit}")
            
            # Limitations
            limitations = current_tier.get('limitations', [])
            print(f"      Limitations:")
            for limitation in limitations:
                print(f"         - {limitation}")
            
            # Upgrade options
            upgrade_options = education.get('upgrade_options', [])
            print(f"   🚀 Upgrade Options:")
            for option in upgrade_options:
                print(f"      {option['name']} ({option['price']})")
                print(f"         Price Difference: {option['price_difference']}")
                print(f"         Recommended For: {option['recommended_for']}")
                print(f"         Key Benefits:")
                for benefit in option['key_benefits']:
                    print(f"            - {benefit}")
            
            # Feature comparison
            feature_comparison = education.get('feature_comparison', {})
            print(f"   📈 Feature Comparison:")
            tiers = feature_comparison.get('tiers', {})
            for tier_name, tier_info in tiers.items():
                print(f"      {tier_name.title()}:")
                print(f"         Available: {tier_info.get('available', False)}")
                print(f"         Limit: {tier_info.get('limit', 'N/A')}")
                print(f"         Description: {tier_info.get('description', 'N/A')}")
            
            # Value proposition
            value_prop = education.get('value_proposition', {})
            print(f"   💎 Value Proposition:")
            print(f"      Title: {value_prop.get('title', 'N/A')}")
            print(f"      Message: {value_prop.get('message', 'N/A')}")
            print(f"      ROI Message: {value_prop.get('roi_message', 'N/A')}")
        else:
            print(f"   ❌ Failed: {degradation_result.get('error', 'No education provided')}")
        
        # Test education for mid-tier user
        print(f"\n2. Education for Mid-Tier User:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.mid_tier_subscription.id,
            feature_type='team_members'
        )
        
        if degradation_result['success'] and 'user_education' in degradation_result:
            education = degradation_result['user_education']
            
            print(f"   ✅ User education provided")
            
            # Current tier info
            current_tier = education.get('current_tier_info', {})
            print(f"   📊 Current Tier: {current_tier.get('name', 'N/A')}")
            
            # Upgrade options
            upgrade_options = education.get('upgrade_options', [])
            print(f"   🚀 Upgrade Options:")
            for option in upgrade_options:
                print(f"      {option['name']} ({option['price']})")
                print(f"         Key Benefits:")
                for benefit in option['key_benefits']:
                    print(f"            - {benefit}")
        else:
            print(f"   ❌ Failed: {degradation_result.get('error', 'No education provided')}")
    
    def demonstrate_comprehensive_graceful_degradation(self):
        """Demonstrate comprehensive graceful degradation information"""
        print("\n=== Comprehensive Graceful Degradation ===")
        
        print(f"\n🔄 Testing Comprehensive Graceful Degradation:")
        
        # Test comprehensive degradation info
        print(f"\n1. Comprehensive Degradation Info:")
        degradation_info = self.payment_service.get_graceful_degradation_info(
            subscription_id=self.budget_subscription.id,
            feature_type='health_checkin',
            access_decision='limit_reached',
            context={'user_context': 'monthly_review', 'usage_pattern': 'high'}
        )
        
        if degradation_info['success']:
            info = degradation_info['degradation_info']
            graceful_options = info.get('graceful_options', {})
            
            print(f"   ✅ Comprehensive degradation info provided")
            print(f"   📊 Subscription Status: {info['subscription_status']}")
            print(f"   🏷️  Tier Type: {info['tier_type']}")
            print(f"   🔧 Feature Type: {info['feature_type']}")
            print(f"   ⚖️  Access Decision: {info['access_decision']}")
            
            # Clear messaging
            messaging = graceful_options.get('clear_messaging', {})
            print(f"   📢 Clear Messaging:")
            print(f"      Title: {messaging.get('title', 'N/A')}")
            print(f"      Message: {messaging.get('message', 'N/A')}")
            print(f"      Subtitle: {messaging.get('subtitle', 'N/A')}")
            print(f"      Urgency: {messaging.get('urgency', 'N/A')}")
            
            # Alternative suggestions
            alternatives = graceful_options.get('alternative_suggestions', [])
            print(f"   🔄 Alternative Suggestions:")
            for alt in alternatives:
                print(f"      - {alt['name']} ({alt['icon']}): {alt['description']}")
            
            # Temporary access
            temp_access = graceful_options.get('temporary_access', {})
            print(f"   🔓 Temporary Access:")
            print(f"      Available: {temp_access.get('available', False)}")
            print(f"      Reason: {temp_access.get('reason', 'N/A')}")
            print(f"      Duration: {temp_access.get('duration', 'N/A')}")
            
            # Next steps
            next_steps = graceful_options.get('next_steps', [])
            print(f"   👣 Next Steps:")
            for step in next_steps:
                print(f"      - {step['title']} ({step['priority']} priority)")
                print(f"        Description: {step['description']}")
                print(f"        CTA: {step['cta_text']}")
        else:
            print(f"   ❌ Failed: {degradation_info['error']}")
    
    def demonstrate_edge_cases(self):
        """Demonstrate edge cases and special scenarios"""
        print("\n=== Edge Cases and Special Scenarios ===")
        
        print(f"\n🔄 Testing Edge Cases:")
        
        # Test invalid feature type
        print(f"\n1. Invalid Feature Type:")
        degradation_result = self.payment_service.check_feature_access_with_graceful_degradation(
            subscription_id=self.budget_subscription.id,
            feature_type='invalid_feature'
        )
        
        if not degradation_result['success']:
            print(f"   ✅ Graceful error handling")
            print(f"   ❌ Error: {degradation_result['error']}")
            graceful_info = degradation_result.get('graceful_degradation', {})
            print(f"   📢 Message: {graceful_info.get('message', 'N/A')}")
            print(f"   💡 Suggestion: {graceful_info.get('suggestion', 'N/A')}")
        
        # Test subscription not found
        print(f"\n2. Subscription Not Found:")
        degradation_info = self.payment_service.get_graceful_degradation_info(
            subscription_id=99999,  # Non-existent subscription
            feature_type='health_checkin',
            access_decision='limit_reached'
        )
        
        if not degradation_info['success']:
            print(f"   ✅ Graceful error handling")
            print(f"   ❌ Error: {degradation_info['error']}")
            graceful_info = degradation_info.get('graceful_degradation', {})
            print(f"   📢 Message: {graceful_info.get('message', 'N/A')}")
            print(f"   💡 Suggestion: {graceful_info.get('suggestion', 'N/A')}")
        
        # Test different access decisions
        print(f"\n3. Different Access Decisions:")
        decisions = ['limit_reached', 'feature_unavailable', 'subscription_inactive', 'trial_expired']
        
        for decision in decisions:
            print(f"\n   Testing Decision: {decision}")
            degradation_info = self.payment_service.get_graceful_degradation_info(
                subscription_id=self.budget_subscription.id,
                feature_type='health_checkin',
                access_decision=decision
            )
            
            if degradation_info['success']:
                graceful_options = degradation_info['degradation_info'].get('graceful_options', {})
                messaging = graceful_options.get('clear_messaging', {})
                print(f"      ✅ Title: {messaging.get('title', 'N/A')}")
                print(f"      📢 Message: {messaging.get('message', 'N/A')}")
                print(f"      🚨 Urgency: {messaging.get('urgency', 'N/A')}")
            else:
                print(f"      ❌ Failed: {degradation_info['error']}")
    
    def run_all_demonstrations(self):
        """Run all graceful degradation demonstrations"""
        print("🚀 MINGUS Graceful Degradation Demonstration")
        print("=" * 65)
        
        try:
            self.demonstrate_clear_messaging()
            self.demonstrate_alternative_suggestions()
            self.demonstrate_temporary_access()
            self.demonstrate_user_education()
            self.demonstrate_comprehensive_graceful_degradation()
            self.demonstrate_edge_cases()
            
            print("\n✅ All graceful degradation demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = GracefulDegradationExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 