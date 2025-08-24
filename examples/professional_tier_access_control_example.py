"""
Professional Tier Access Control Example for MINGUS
Demonstrates the exact Professional tier limits and access control implementation
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

class ProfessionalTierAccessControlExample:
    """Example demonstrating Professional tier access control with exact limits"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_professional_tier_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for Professional tier demonstration"""
        # Create Professional tier with exact limits
        professional_tier = PricingTier(
            tier_type='professional',
            name='Professional',
            description='Complete solution for professionals and teams',
            monthly_price=75.00,  # Exact price specified
            yearly_price=750.00,
            max_health_checkins_per_month=-1,  # Unlimited
            max_financial_reports_per_month=-1,  # Unlimited
            max_ai_insights_per_month=-1  # Unlimited
        )
        
        self.db_session.add(professional_tier)
        self.db_session.commit()
        
        # Create sample customer
        customer = Customer(
            user_id=1,
            stripe_customer_id='cus_professional_demo',
            email='professional.user@example.com',
            name='Professional User',
            address={'country': 'US', 'state': 'CA'}
        )
        
        self.db_session.add(customer)
        self.db_session.commit()
        
        # Create Professional subscription
        subscription = Subscription(
            customer_id=customer.id,
            pricing_tier_id=professional_tier.id,
            stripe_subscription_id='sub_professional_demo',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=25),
            current_period_end=datetime.utcnow() + timedelta(days=5),
            billing_cycle='monthly',
            amount=75.00,
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
            career_risk_management_used=0,
            dedicated_account_manager_used=0
        )
        
        self.db_session.add(feature_usage)
        self.db_session.commit()
        
        self.professional_tier = professional_tier
        self.customer = customer
        self.subscription = subscription
        self.feature_usage = feature_usage
    
    def demonstrate_professional_tier_limits(self):
        """Demonstrate Professional tier feature limits"""
        print("\n=== Professional Tier ($75/month) Feature Limits ===")
        
        print(f"\n📊 Professional Tier Configuration:")
        print(f"   Monthly Price: ${self.professional_tier.monthly_price}")
        print(f"   Yearly Price: ${self.professional_tier.yearly_price}")
        print(f"   Description: {self.professional_tier.description}")
        
        print(f"\n🔐 Feature Limits:")
        print(f"   Health Check-ins: Unlimited")
        print(f"   Financial Reports: Unlimited")
        print(f"   AI Insights: Unlimited")
        print(f"   Custom Reports: Unlimited")
        print(f"   Career Risk Management: Unlimited")
        print(f"   Team Members: 10")
        print(f"   API Access: 10,000 calls/hour")
        print(f"   Support: Phone + email (unlimited)")
        print(f"   Dedicated Account Manager: 1")
        print(f"   Custom Integrations: Unlimited")
        print(f"   White Label: Unlimited")
    
    def demonstrate_unlimited_feature_access(self):
        """Demonstrate unlimited feature access"""
        print("\n=== Unlimited Feature Access ===")
        
        unlimited_features = [
            'health_checkin',
            'financial_report',
            'ai_insight',
            'custom_reports',
            'career_risk_management',
            'data_export',
            'advanced_analytics',
            'custom_integrations',
            'bulk_operations',
            'premium_support',
            'white_label'
        ]
        
        print(f"\n🔄 Testing Unlimited Feature Access:")
        
        for feature in unlimited_features:
            print(f"\n   Testing {feature.replace('_', ' ').title()}:")
            
            # Test access
            access_result = self.payment_service.check_feature_access(
                subscription_id=self.subscription.id,
                feature_type=feature
            )
            
            print(f"      Decision: {access_result['decision']}")
            print(f"      Available: {access_result.get('available', False)}")
            print(f"      Limit: {access_result.get('limit', 'unlimited')}")
            
            # Test usage
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type=feature,
                user_id=self.customer.user_id,
                metadata={'test': True, 'feature': feature}
            )
            
            print(f"      Usage Result: {usage_result['decision']}")
            if usage_result['decision'] == 'allowed':
                print(f"      ✅ Success - Unlimited access confirmed")
    
    def demonstrate_team_member_access(self):
        """Demonstrate team member access control"""
        print("\n=== Team Member Access Control ===")
        
        print(f"\n🔄 Testing Team Member Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='team_members'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/10")
        print(f"   Available: {access_result.get('available', False)}")
        
        # Test adding team members up to limit
        print(f"\n2. Adding Team Members:")
        for i in range(11):  # Try to add 11 (should fail on the 11th)
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='team_members',
                user_id=self.customer.user_id,
                metadata={'action': 'add_member', 'email': f'teammate{i+1}@example.com', 'attempt': i + 1}
            )
            
            print(f"   Attempt {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'limit_reached':
                print(f"   ❌ Limit reached at {usage_result['current_usage']}/10")
                print(f"   💡 {usage_result['upgrade_message']}")
                break
            elif usage_result['decision'] == 'allowed':
                print(f"   ✅ Success - Team member {i + 1} added")
                print(f"   Current Usage: {usage_result['current_usage']}/10")
                if usage_result.get('upgrade_recommendation'):
                    print(f"   ⚠️  Upgrade recommended: {usage_result['upgrade_recommendation']['message']}")
    
    def demonstrate_api_access(self):
        """Demonstrate API access control"""
        print("\n=== API Access Control ===")
        
        print(f"\n🔄 Testing API Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='api_access'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/10,000 per hour")
        print(f"   Available: {access_result.get('available', False)}")
        
        # Test API calls up to limit
        print(f"\n2. Making API Calls:")
        for i in range(10001):  # Try to make 10,001 calls (should fail on the 10,001st)
            if i % 2000 == 0:  # Show progress every 2000 calls
                print(f"   Progress: {i} API calls made...")
            
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='api_access',
                user_id=self.customer.user_id,
                metadata={'endpoint': '/api/v1/health_checkins', 'method': 'GET', 'attempt': i + 1}
            )
            
            if usage_result['decision'] == 'limit_reached':
                print(f"   ❌ API rate limit reached at {usage_result['current_usage']}/10,000 calls per hour")
                print(f"   💡 {usage_result['upgrade_message']}")
                break
            elif usage_result['decision'] == 'allowed':
                if i == 10000:  # Last successful call
                    print(f"   ✅ Success - {i + 1} API calls made")
                    print(f"   Current Usage: {usage_result['current_usage']}/10,000")
                    if usage_result.get('upgrade_recommendation'):
                        print(f"   ⚠️  Upgrade recommended: {usage_result['upgrade_recommendation']['message']}")
    
    def demonstrate_dedicated_account_manager(self):
        """Demonstrate dedicated account manager access"""
        print("\n=== Dedicated Account Manager Access ===")
        
        print(f"\n🔄 Testing Dedicated Account Manager Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='dedicated_account_manager'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/1")
        print(f"   Available: {access_result.get('available', False)}")
        print(f"   Feature: Dedicated account manager")
        
        # Test using dedicated account manager
        print(f"\n2. Requesting Dedicated Account Manager:")
        usage_result = self.payment_service.use_feature(
            subscription_id=self.subscription.id,
            feature_type='dedicated_account_manager',
            user_id=self.customer.user_id,
            metadata={'request_type': 'account_setup', 'priority': 'high'}
        )
        
        print(f"   Decision: {usage_result['decision']}")
        if usage_result['decision'] == 'allowed':
            print(f"   ✅ Dedicated account manager assigned")
            print(f"   Current Usage: {usage_result['current_usage']}/1")
        else:
            print(f"   ❌ Unexpected result: {usage_result['decision']}")
    
    def demonstrate_support_access(self):
        """Demonstrate support access control"""
        print("\n=== Support Access Control ===")
        
        print(f"\n🔄 Testing Support Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='support'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/unlimited")
        print(f"   Available: {access_result.get('available', False)}")
        print(f"   Support Level: Phone + email (unlimited)")
        
        # Test using support (should be unlimited)
        print(f"\n2. Requesting Support:")
        for i in range(5):  # Test multiple support requests
            usage_result = self.payment_service.use_feature(
                subscription_id=self.subscription.id,
                feature_type='support',
                user_id=self.customer.user_id,
                metadata={'support_type': 'phone', 'issue': f'support_request_{i+1}', 'priority': 'high'}
            )
            
            print(f"   Request {i + 1}: {usage_result['decision']}")
            
            if usage_result['decision'] == 'allowed':
                print(f"   ✅ Support request {i + 1} submitted via phone")
                print(f"   Current Usage: {usage_result['current_usage']}/unlimited")
            else:
                print(f"   ❌ Unexpected result: {usage_result['decision']}")
                break
    
    def demonstrate_custom_integrations(self):
        """Demonstrate custom integrations access"""
        print("\n=== Custom Integrations Access ===")
        
        print(f"\n🔄 Testing Custom Integrations Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='custom_integrations'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/unlimited")
        print(f"   Available: {access_result.get('available', False)}")
        print(f"   Feature: Custom integrations")
        
        # Test using custom integrations
        print(f"\n2. Creating Custom Integration:")
        usage_result = self.payment_service.use_feature(
            subscription_id=self.subscription.id,
            feature_type='custom_integrations',
            user_id=self.customer.user_id,
            metadata={'integration_type': 'crm', 'platform': 'salesforce', 'custom_fields': True}
        )
        
        print(f"   Decision: {usage_result['decision']}")
        if usage_result['decision'] == 'allowed':
            print(f"   ✅ Custom integration created successfully")
            print(f"   Current Usage: {usage_result['current_usage']}/unlimited")
        else:
            print(f"   ❌ Unexpected result: {usage_result['decision']}")
    
    def demonstrate_white_label_access(self):
        """Demonstrate white label access"""
        print("\n=== White Label Access ===")
        
        print(f"\n🔄 Testing White Label Access:")
        
        # Test initial access
        print(f"\n1. Initial Access Check:")
        access_result = self.payment_service.check_feature_access(
            subscription_id=self.subscription.id,
            feature_type='white_label'
        )
        
        print(f"   Decision: {access_result['decision']}")
        print(f"   Current Usage: {access_result.get('current_usage', 0)}/unlimited")
        print(f"   Available: {access_result.get('available', False)}")
        print(f"   Feature: White label branding")
        
        # Test using white label features
        print(f"\n2. Setting Up White Label:")
        usage_result = self.payment_service.use_feature(
            subscription_id=self.subscription.id,
            feature_type='white_label',
            user_id=self.customer.user_id,
            metadata={'branding': 'custom_logo', 'domain': 'app.company.com', 'colors': 'brand_colors'}
        )
        
        print(f"   Decision: {usage_result['decision']}")
        if usage_result['decision'] == 'allowed':
            print(f"   ✅ White label setup completed successfully")
            print(f"   Current Usage: {usage_result['current_usage']}/unlimited")
        else:
            print(f"   ❌ Unexpected result: {usage_result['decision']}")
    
    def demonstrate_enterprise_upgrade_prompts(self):
        """Demonstrate enterprise upgrade prompts"""
        print("\n=== Enterprise Upgrade Prompts ===")
        
        # Test enterprise upgrade scenarios
        scenarios = [
            ('team_members', 'Team member limit reached'),
            ('api_access', 'API rate limit reached')
        ]
        
        for feature, description in scenarios:
            print(f"\n🎯 {description}:")
            
            prompt = self.payment_service.generate_upgrade_prompt(
                subscription_id=self.subscription.id,
                trigger_type='feature_limit_reached'
            )
            
            if prompt['success']:
                upgrade_prompt = prompt['upgrade_prompt']
                print(f"   Title: {upgrade_prompt['title']}")
                print(f"   Message: {upgrade_prompt['message']}")
                print(f"   Urgency: {upgrade_prompt['urgency']}")
                print(f"   Type: {upgrade_prompt['type']}")
                print(f"   Benefits: {', '.join(upgrade_prompt['benefits'][:3])}...")
                print(f"   Note: Contact sales for enterprise expansion")
            else:
                print(f"   ❌ Failed: {prompt['error']}")
    
    def demonstrate_comprehensive_access_status(self):
        """Demonstrate comprehensive access status for Professional tier"""
        print("\n=== Comprehensive Access Status ===")
        
        # Get access status for all features
        access_status = self.payment_service.get_feature_access_status(
            subscription_id=self.subscription.id
        )
        
        if access_status['success']:
            print(f"\n🔐 Access Status for {self.customer.name} (Professional Tier):")
            print(f"   Tier: {access_status['tier']}")
            
            for feature, data in access_status['features'].items():
                status_icon = "✅" if data['available'] else "❌"
                access_level = data['access_level']
                
                print(f"\n   {status_icon} {feature.replace('_', ' ').title()}:")
                print(f"      Access Level: {access_level}")
                print(f"      Usage: {data['current_usage']}/{data['limit']}")
                print(f"      Available: {data['available']}")
                print(f"      Usage %: {data['usage_percentage']:.1f}%")
                
                # Show specific details for Professional tier
                if data['limit'] == -1:
                    print(f"      Note: Unlimited access")
                elif feature == 'team_members' and data['limit'] == 10:
                    print(f"      Note: Limited to 10 team members")
                elif feature == 'api_access' and data['limit'] == 10000:
                    print(f"      Note: 10,000 API calls per hour")
                elif feature == 'dedicated_account_manager' and data['limit'] == 1:
                    print(f"      Note: 1 dedicated account manager")
        else:
            print(f"   ❌ Failed to get access status: {access_status['error']}")
    
    def run_all_demonstrations(self):
        """Run all Professional tier access control demonstrations"""
        print("🚀 MINGUS Professional Tier Access Control Demonstration")
        print("=" * 65)
        
        try:
            self.demonstrate_professional_tier_limits()
            self.demonstrate_unlimited_feature_access()
            self.demonstrate_team_member_access()
            self.demonstrate_api_access()
            self.demonstrate_dedicated_account_manager()
            self.demonstrate_support_access()
            self.demonstrate_custom_integrations()
            self.demonstrate_white_label_access()
            self.demonstrate_enterprise_upgrade_prompts()
            self.demonstrate_comprehensive_access_status()
            
            print("\n✅ All Professional tier access control demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = ProfessionalTierAccessControlExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 