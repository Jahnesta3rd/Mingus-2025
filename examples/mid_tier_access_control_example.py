"""
Mid-Tier Access Control Example for MINGUS
Demonstrates the exact Mid-Tier limits and access control implementation
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.feature_access_service import FeatureType, AccessDecision
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, FeatureUsage

class MidTierAccessControlExample:
    """Example demonstrating Mid-Tier access control with exact limits"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_mid_tier_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for Mid-Tier demonstration"""
        # Create Mid-Tier with exact limits
        mid_tier = PricingTier(
            tier_type='mid_tier',
            name='Mid-Tier',
            description='Advanced features for serious users',
            monthly_price=35.00,  # Exact price specified
            yearly_price=350.00,
            max_health_checkins_per_month=12,
            max_financial_reports_per_month=10,
            max_ai_insights_per_month=50
        )
        
        self.db_session.add(mid_tier)
        self.db_session.commit()
        
        # Create sample customer
        customer = Customer(
            user_id=1,
            stripe_customer_id='cus_mid_tier_demo',
            email='mid_tier.user@example.com',
            name='Mid-Tier User',
            address={'country': 'US', 'state': 'NY'}
        )
        
        self.db_session.add(customer)
        self.db_session.commit()
        
        # Create Mid-Tier subscription
        subscription = Subscription(
            customer_id=customer.id,
            pricing_tier_id=mid_tier.id,
            stripe_subscription_id='sub_mid_tier_demo',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=20),
            current_period_end=datetime.utcnow() + timedelta(days=10),
            billing_cycle='monthly',
            amount=35.00,
            currency='USD'
        )
        
        self.db_session.add(subscription)
        self.db_session.commit()
        
        # Create feature usage record
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        feature_usage = FeatureUsage(
            subscription_id=subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=0,
            financial_reports_used=0,
            ai_insights_used=0,
            custom_reports_used=0,
            team_members_used=0,
            support_requests_used=0,
            career_risk_management_used=0
        )
        
        self.db_session.add(feature_usage)
        self.db_session.commit()
        
        self.mid_tier = mid_tier
        self.customer = customer
        self.subscription = subscription
        self.feature_usage = feature_usage
    
    def demonstrate_mid_tier_limits(self):
        """Demonstrate Mid-Tier feature limits"""
        print("\n=== Mid-Tier ($35/month) Feature Limits ===")
        
        print(f"\n📊 Mid-Tier Configuration:")
        print(f"   Monthly Price: ${self.mid_tier.monthly_price}")
        print(f"   Yearly Price: ${self.mid_tier.yearly_price}")
        print(f"   Description: {self.mid_tier.description}")
        
        print(f"\n🔐 Feature Limits:")
        print(f"   Health Check-ins: {self.mid_tier.max_health_checkins_per_month} per month")
        print(f"   Financial Reports: {self.mid_tier.max_financial_reports_per_month} per month")
        print(f"   AI Insights: {self.mid_tier.max_ai_insights_per_month} per month")
        print(f"   Custom Reports: 5 per month")
        print(f"   Career Risk Management: Unlimited")
        print(f"   Team Members: 0")
        print(f"   API Access: None")
        print(f"   Support: Priority email (3 requests per month)")
    
    def demonstrate_health_checkin_access(self):
        """Demonstrate health check-in access control"""
        print("\n=== Health Check-in Access Control ===")
        
        print(f"\n🔄 Testing Health Check-in Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='health_checkin'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/12")
        print(f"   Available: {access_result.get('available', False)}")
        
        # Test using health check-ins up to limit
        print(f"\n2. Using Health Check-ins:")
        for i in range(13):  # Try to use 13 (should fail on the 13th)
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='health_checkin',
                user_id=self.customer.user_id,
                metadata={'checkin_type': 'daily', 'attempt': i + 1}
            )
            
            print(f"   Attempt {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'limit_reached':
                print(f"   ❌ Limit reached at {usage_result['current_usage']}/12")
                print(f"   💡 {usage_result['upgrade_message']}")
                break
            elif usage_result['decision'] == 'allowed':
                print(f"   ✅ Success - Usage: {usage_result['current_usage']}/12")
                if usage_result.get('upgrade_recommendation'):
                    print(f"   ⚠️  Upgrade recommended: {usage_result['upgrade_recommendation']['message']}")
    
    def demonstrate_financial_report_access(self):
        """Demonstrate financial report access control"""
        print("\n=== Financial Report Access Control ===")
        
        print(f"\n🔄 Testing Financial Report Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='financial_report'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/10")
        print(f"   Available: {access_result.get('available', False)}")
        
        # Test using financial reports up to limit
        print(f"\n2. Using Financial Reports:")
        for i in range(11):  # Try to use 11 (should fail on the 11th)
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='financial_report',
                user_id=self.customer.user_id,
                metadata={'report_type': 'monthly_summary', 'attempt': i + 1}
            )
            
            print(f"   Attempt {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'limit_reached':
                print(f"   ❌ Limit reached at {usage_result['current_usage']}/10")
                print(f"   💡 {usage_result['upgrade_message']}")
                break
            elif usage_result['decision'] == 'allowed':
                print(f"   ✅ Success - Usage: {usage_result['current_usage']}/10")
                if usage_result.get('upgrade_recommendation'):
                    print(f"   ⚠️  Upgrade recommended: {usage_result['upgrade_recommendation']['message']}")
    
    def demonstrate_ai_insight_access(self):
        """Demonstrate AI insight access control"""
        print("\n=== AI Insight Access Control ===")
        
        print(f"\n🔄 Testing AI Insight Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='ai_insight'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/50")
        print(f"   Available: {access_result.get('available', False)}")
        
        # Test using AI insights up to limit
        print(f"\n2. Using AI Insights:")
        for i in range(51):  # Try to use 51 (should fail on the 51st)
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='ai_insight',
                user_id=self.customer.user_id,
                metadata={'insight_type': 'spending_pattern', 'attempt': i + 1}
            )
            
            print(f"   Attempt {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'limit_reached':
                print(f"   ❌ Limit reached at {usage_result['current_usage']}/50")
                print(f"   💡 {usage_result['upgrade_message']}")
                break
            elif usage_result['decision'] == 'allowed':
                print(f"   ✅ Success - Usage: {usage_result['current_usage']}/50")
                if usage_result.get('upgrade_recommendation'):
                    print(f"   ⚠️  Upgrade recommended: {usage_result['upgrade_recommendation']['message']}")
    
    def demonstrate_custom_report_access(self):
        """Demonstrate custom report access control"""
        print("\n=== Custom Report Access Control ===")
        
        print(f"\n🔄 Testing Custom Report Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='custom_reports'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/5")
        print(f"   Available: {access_result.get('available', False)}")
        
        # Test using custom reports up to limit
        print(f"\n2. Using Custom Reports:")
        for i in range(6):  # Try to use 6 (should fail on the 6th)
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='custom_reports',
                user_id=self.customer.user_id,
                metadata={'report_type': 'custom_spending_analysis', 'attempt': i + 1}
            )
            
            print(f"   Attempt {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'limit_reached':
                print(f"   ❌ Limit reached at {usage_result['current_usage']}/5")
                print(f"   💡 {usage_result['upgrade_message']}")
                break
            elif usage_result['decision'] == 'allowed':
                print(f"   ✅ Success - Usage: {usage_result['current_usage']}/5")
                if usage_result.get('upgrade_recommendation'):
                    print(f"   ⚠️  Upgrade recommended: {usage_result['upgrade_recommendation']['message']}")
    
    def demonstrate_career_risk_management_access(self):
        """Demonstrate career risk management access control"""
        print("\n=== Career Risk Management Access Control ===")
        
        print(f"\n🔄 Testing Career Risk Management Access:")
        
        # Test initial access (should be unlimited)
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='career_risk_management'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/unlimited")
        print(f"   Available: {access_result.get('available', False)}")
        print(f"   Limit: {access_result.get('limit', 'unlimited')}")
        
        # Test using career risk management (should be unlimited)
        print(f"\n2. Using Career Risk Management:")
        for i in range(5):  # Test multiple uses
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='career_risk_management',
                user_id=self.customer.user_id,
                metadata={'risk_type': 'job_security', 'attempt': i + 1}
            )
            
            print(f"   Attempt {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'allowed':
                print(f"   ✅ Success - Usage: {usage_result['current_usage']}/unlimited")
            else:
                print(f"   ❌ Unexpected result: {usage_result['decision']}")
                break
    
    def demonstrate_team_member_access(self):
        """Demonstrate team member access control"""
        print("\n=== Team Member Access Control ===")
        
        print(f"\n🔄 Testing Team Member Access:")
        
        # Test access (should be denied for Mid-Tier)
        print(f"\n1. Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='team_members'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/0")
        print(f"   Available: {access_result.get('available', False)}")
        
        if access_result['decision'] == 'upgrade_required':
            print(f"   🔒 {access_result['message']}")
            print(f"   Benefits: {', '.join(access_result['upgrade_benefits'])}")
        
        # Test adding team member (should be denied)
        print(f"\n2. Attempting to Add Team Member:")
        usage_result = self.payment_service.use_feature(
            subscription_id=self.subscription.id,
            feature_type='team_members',
            user_id=self.customer.user_id,
            metadata={'action': 'add_member', 'email': 'teammate@example.com'}
        )
        
        print(f"   Decision: {usage_result['decision']}")
        if usage_result['decision'] == 'upgrade_required':
            print(f"   🔒 {usage_result['message']}")
            print(f"   Benefits: {', '.join(usage_result['upgrade_benefits'])}")
    
    def demonstrate_api_access(self):
        """Demonstrate API access control"""
        print("\n=== API Access Control ===")
        
        print(f"\n🔄 Testing API Access:")
        
        # Test access (should be denied for Mid-Tier)
        print(f"\n1. Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='api_access'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/0")
        print(f"   Available: {access_result.get('available', False)}")
        
        if access_result['decision'] == 'upgrade_required':
            print(f"   🔒 {access_result['message']}")
            print(f"   Benefits: {', '.join(access_result['upgrade_benefits'])}")
        
        # Test API call (should be denied)
        print(f"\n2. Attempting API Call:")
        usage_result = self.payment_service.use_feature(
            subscription_id=self.subscription.id,
            feature_type='api_access',
            user_id=self.customer.user_id,
            metadata={'endpoint': '/api/v1/health_checkins', 'method': 'POST'}
        )
        
        print(f"   Decision: {usage_result['decision']}")
        if usage_result['decision'] == 'upgrade_required':
            print(f"   🔒 {usage_result['message']}")
            print(f"   Benefits: {', '.join(usage_result['upgrade_benefits'])}")
    
    def demonstrate_support_access(self):
        """Demonstrate support access control"""
        print("\n=== Support Access Control ===")
        
        print(f"\n🔄 Testing Support Access:")
        
        # Test initial access (should be allowed for Mid-Tier - priority email)
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='support'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/3")
        print(f"   Available: {access_result.get('available', False)}")
        print(f"   Support Level: Priority email")
        
        # Test using support up to limit
        print(f"\n2. Requesting Support:")
        for i in range(4):  # Try to use 4 (should fail on the 4th)
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='support',
                user_id=self.customer.user_id,
                metadata={'support_type': 'priority_email', 'issue': 'billing_question', 'attempt': i + 1}
            )
            
            print(f"   Attempt {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'allowed':
                print(f"   ✅ Priority email support request submitted")
                print(f"   Current Usage: {usage_result['current_usage']}/3")
                if usage_result.get('upgrade_recommendation'):
                    print(f"   ⚠️  Upgrade recommended: {usage_result['upgrade_recommendation']['message']}")
            elif usage_result['decision'] == 'limit_reached':
                print(f"   ❌ Support limit reached")
                print(f"   💡 {usage_result['upgrade_message']}")
                break
    
    def demonstrate_upgrade_prompts(self):
        """Demonstrate upgrade prompts for Mid-Tier"""
        print("\n=== Upgrade Prompts for Mid-Tier ===")
        
        # Test different upgrade scenarios
        scenarios = [
            ('feature_limit_reached', 'Feature limit reached'),
            ('premium_feature_access', 'Premium feature access'),
            ('usage_threshold', 'Usage threshold exceeded')
        ]
        
        for trigger_type, description in scenarios:
            print(f"\n🎯 {description}:")
            
            prompt = self.payment_service.generate_upgrade_prompt(
                subscription_id=self.subscription.id,
                trigger_type=trigger_type
            )
            
            if prompt['success']:
                upgrade_prompt = prompt['upgrade_prompt']
                print(f"   Title: {upgrade_prompt['title']}")
                print(f"   Message: {upgrade_prompt['message']}")
                print(f"   Urgency: {upgrade_prompt['urgency']}")
                print(f"   Type: {upgrade_prompt['type']}")
                print(f"   Benefits: {', '.join(upgrade_prompt['benefits'][:3])}...")
                print(f"   Pricing: ${upgrade_prompt['pricing']['monthly']}/month")
            else:
                print(f"   ❌ Failed: {prompt['error']}")
    
    def demonstrate_comprehensive_access_status(self):
        """Demonstrate comprehensive access status for Mid-Tier"""
        print("\n=== Comprehensive Access Status ===")
        
        # Get access status for all features
        access_status = self.payment_service.get_feature_access_status(
            subscription_id=self.subscription.id
        )
        
        if access_status['success']:
            print(f"\n🔐 Access Status for {self.customer.name} (Mid-Tier):")
            print(f"   Tier: {access_status['tier']}")
            
            for feature, data in access_status['features'].items():
                status_icon = "✅" if data['available'] else "❌"
                access_level = data['access_level']
                
                print(f"\n   {status_icon} {feature.replace('_', ' ').title()}:")
                print(f"      Access Level: {access_level}")
                print(f"      Usage: {data['current_usage']}/{data['limit']}")
                print(f"      Available: {data['available']}")
                print(f"      Usage %: {data['usage_percentage']:.1f}%")
                
                # Show specific details for Mid-Tier
                if feature == 'health_checkin' and data['limit'] == 12:
                    print(f"      Note: Limited to 12 check-ins per month")
                elif feature == 'financial_report' and data['limit'] == 10:
                    print(f"      Note: Limited to 10 reports per month")
                elif feature == 'ai_insight' and data['limit'] == 50:
                    print(f"      Note: Limited to 50 AI insights per month")
                elif feature == 'custom_reports' and data['limit'] == 5:
                    print(f"      Note: Limited to 5 custom reports per month")
                elif feature == 'career_risk_management' and data['limit'] == -1:
                    print(f"      Note: Unlimited career risk management")
                elif feature == 'team_members' and data['limit'] == 0:
                    print(f"      Note: Not available in Mid-Tier")
                elif feature == 'api_access' and data['limit'] == 0:
                    print(f"      Note: Not available in Mid-Tier")
                elif feature == 'support' and data['limit'] == 3:
                    print(f"      Note: Priority email support (3 requests per month)")
        else:
            print(f"   ❌ Failed to get access status: {access_status['error']}")
    
    def run_all_demonstrations(self):
        """Run all Mid-Tier access control demonstrations"""
        print("🚀 MINGUS Mid-Tier Access Control Demonstration")
        print("=" * 60)
        
        try:
            self.demonstrate_mid_tier_limits()
            self.demonstrate_health_checkin_access()
            self.demonstrate_financial_report_access()
            self.demonstrate_ai_insight_access()
            self.demonstrate_custom_report_access()
            self.demonstrate_career_risk_management_access()
            self.demonstrate_team_member_access()
            self.demonstrate_api_access()
            self.demonstrate_support_access()
            self.demonstrate_upgrade_prompts()
            self.demonstrate_comprehensive_access_status()
            
            print("\n✅ All Mid-Tier access control demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = MidTierAccessControlExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 