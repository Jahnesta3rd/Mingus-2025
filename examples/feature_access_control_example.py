"""
Feature Access Control Example for MINGUS
Demonstrates comprehensive tier-based access control system that enforces subscription limits
and drives upgrade conversions through smart access management
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.feature_access_service import FeatureAccessService, FeatureType, AccessDecision, UpgradeTrigger
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, FeatureUsage

class FeatureAccessControlExample:
    """Example demonstrating comprehensive feature access control"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_feature_access_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        self.feature_access = FeatureAccessService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for demonstration"""
        # Create pricing tiers
        budget_tier = PricingTier(
            tier_type='budget',
            name='Budget',
            description='Perfect for individuals getting started',
            monthly_price=9.99,
            yearly_price=99.99,
            max_health_checkins_per_month=4,
            max_financial_reports_per_month=2,
            max_ai_insights_per_month=0
        )
        
        mid_tier = PricingTier(
            tier_type='mid_tier',
            name='Mid-Tier',
            description='Advanced features for serious users',
            monthly_price=29.99,
            yearly_price=299.99,
            max_health_checkins_per_month=12,
            max_financial_reports_per_month=10,
            max_ai_insights_per_month=50
        )
        
        professional_tier = PricingTier(
            tier_type='professional',
            name='Professional',
            description='Complete solution for professionals',
            monthly_price=99.99,
            yearly_price=999.99,
            max_health_checkins_per_month=-1,  # Unlimited
            max_financial_reports_per_month=-1,  # Unlimited
            max_ai_insights_per_month=-1  # Unlimited
        )
        
        self.db_session.add_all([budget_tier, mid_tier, professional_tier])
        self.db_session.commit()
        
        # Create sample customers
        customers = [
            Customer(
                user_id=1,
                stripe_customer_id='cus_budget123',
                email='budget.user@example.com',
                name='Budget User',
                address={'country': 'US', 'state': 'CA'}
            ),
            Customer(
                user_id=2,
                stripe_customer_id='cus_mid123',
                email='mid.user@example.com',
                name='Mid-Tier User',
                address={'country': 'US', 'state': 'NY'}
            ),
            Customer(
                user_id=3,
                stripe_customer_id='cus_pro123',
                email='pro.user@example.com',
                name='Professional User',
                address={'country': 'US', 'state': 'TX'}
            ),
            Customer(
                user_id=4,
                stripe_customer_id='cus_heavy123',
                email='heavy.user@example.com',
                name='Heavy User',
                address={'country': 'US', 'state': 'FL'}
            )
        ]
        
        for customer in customers:
            self.db_session.add(customer)
        self.db_session.commit()
        
        # Create sample subscriptions
        subscriptions = [
            # Budget subscription with some usage
            Subscription(
                customer_id=customers[0].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_budget123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            ),
            # Mid-tier subscription with high usage
            Subscription(
                customer_id=customers[1].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_mid123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=20),
                current_period_end=datetime.utcnow() + timedelta(days=10),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            # Professional subscription
            Subscription(
                customer_id=customers[2].id,
                pricing_tier_id=professional_tier.id,
                stripe_subscription_id='sub_pro123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=25),
                current_period_end=datetime.utcnow() + timedelta(days=5),
                billing_cycle='monthly',
                amount=99.99,
                currency='USD'
            ),
            # Heavy usage budget user (likely to upgrade)
            Subscription(
                customer_id=customers[3].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_heavy123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=10),
                current_period_end=datetime.utcnow() + timedelta(days=20),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            )
        ]
        
        for subscription in subscriptions:
            self.db_session.add(subscription)
        self.db_session.commit()
        
        # Create sample feature usage
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        usage_records = [
            # Budget user with moderate usage
            FeatureUsage(
                subscription_id=subscriptions[0].id,
                usage_month=current_month,
                usage_year=current_year,
                health_checkins_used=3,
                financial_reports_used=1,
                ai_insights_used=0
            ),
            # Mid-tier user with high usage (near limits)
            FeatureUsage(
                subscription_id=subscriptions[1].id,
                usage_month=current_month,
                usage_year=current_year,
                health_checkins_used=10,
                financial_reports_used=8,
                ai_insights_used=45
            ),
            # Professional user with unlimited usage
            FeatureUsage(
                subscription_id=subscriptions[2].id,
                usage_month=current_month,
                usage_year=current_year,
                health_checkins_used=25,
                financial_reports_used=15,
                ai_insights_used=100
            ),
            # Heavy budget user (at limits)
            FeatureUsage(
                subscription_id=subscriptions[3].id,
                usage_month=current_month,
                usage_year=current_year,
                health_checkins_used=4,  # At limit
                financial_reports_used=2,  # At limit
                ai_insights_used=0
            )
        ]
        
        for usage in usage_records:
            self.db_session.add(usage)
        self.db_session.commit()
        
        self.sample_customers = customers
        self.sample_subscriptions = subscriptions
        self.sample_tiers = [budget_tier, mid_tier, professional_tier]
    
    def demonstrate_feature_access_control(self):
        """Demonstrate feature access control system"""
        print("\n=== Feature Access Control System ===")
        
        # Test different subscription tiers
        for i, subscription in enumerate(self.sample_subscriptions):
            customer = self.sample_customers[i]
            print(f"\n📊 Testing {customer.name} ({subscription.pricing_tier.name}):")
            
            # Test health checkin access
            health_result = self.payment_service.check_feature_access(
                subscription_id=subscription.id,
                feature_type='health_checkin'
            )
            
            print(f"   Health Checkin Access: {health_result['decision']}")
            if health_result['success']:
                print(f"   Current Usage: {health_result.get('current_usage', 0)}")
                print(f"   Limit: {health_result.get('limit', 'unlimited')}")
                if health_result.get('upgrade_recommended'):
                    print(f"   ⚠️  Upgrade Recommended!")
            
            # Test AI insight access
            ai_result = self.payment_service.check_feature_access(
                subscription_id=subscription.id,
                feature_type='ai_insight'
            )
            
            print(f"   AI Insight Access: {ai_result['decision']}")
            if ai_result['decision'] == 'upgrade_required':
                print(f"   💡 {ai_result['message']}")
    
    def demonstrate_feature_usage_tracking(self):
        """Demonstrate feature usage tracking"""
        print("\n=== Feature Usage Tracking ===")
        
        # Test using features
        test_subscription = self.sample_subscriptions[0]  # Budget user
        
        print(f"\n🔄 Testing Feature Usage for {test_subscription.customer.name}:")
        
        # Try to use health checkin
        health_usage = self.payment_service.use_feature(
            subscription_id=test_subscription.id,
            feature_type='health_checkin',
            user_id=test_subscription.customer.user_id,
            metadata={'source': 'demo', 'checkin_type': 'daily'}
        )
        
        print(f"   Health Checkin Usage: {health_usage['decision']}")
        if health_usage['success']:
            print(f"   Current Usage: {health_usage['current_usage']}")
            if health_usage.get('upgrade_recommendation'):
                print(f"   💡 {health_usage['upgrade_recommendation']['message']}")
        
        # Try to use AI insight (should be denied for budget tier)
        ai_usage = self.payment_service.use_feature(
            subscription_id=test_subscription.id,
            feature_type='ai_insight',
            user_id=test_subscription.customer.user_id,
            metadata={'source': 'demo', 'insight_type': 'spending_pattern'}
        )
        
        print(f"   AI Insight Usage: {ai_usage['decision']}")
        if ai_usage['decision'] == 'upgrade_required':
            print(f"   🔒 {ai_usage['message']}")
            print(f"   Benefits: {', '.join(ai_usage['upgrade_benefits'])}")
    
    def demonstrate_upgrade_prompts(self):
        """Demonstrate upgrade prompt generation"""
        print("\n=== Upgrade Prompt Generation ===")
        
        # Test different upgrade scenarios
        scenarios = [
            ('limit_reached', 'Feature limit reached'),
            ('usage_threshold', 'Usage threshold exceeded'),
            ('premium_feature_access', 'Premium feature access')
        ]
        
        for trigger_type, description in scenarios:
            print(f"\n🎯 {description}:")
            
            # Test with heavy budget user (most likely to upgrade)
            heavy_user = self.sample_subscriptions[3]
            
            prompt = self.payment_service.generate_upgrade_prompt(
                subscription_id=heavy_user.id,
                trigger_type=trigger_type
            )
            
            if prompt['success']:
                upgrade_prompt = prompt['upgrade_prompt']
                print(f"   Title: {upgrade_prompt['title']}")
                print(f"   Message: {upgrade_prompt['message']}")
                print(f"   Urgency: {upgrade_prompt['urgency']}")
                print(f"   Benefits: {', '.join(upgrade_prompt['benefits'][:2])}...")
                print(f"   Pricing: ${upgrade_prompt['pricing']['monthly']}/month")
            else:
                print(f"   ❌ Failed: {prompt['error']}")
    
    def demonstrate_upgrade_opportunities(self):
        """Demonstrate upgrade opportunity detection"""
        print("\n=== Upgrade Opportunity Detection ===")
        
        # Check upgrade opportunities for all subscriptions
        opportunities = self.payment_service.check_upgrade_opportunities(
            include_all_subscriptions=True
        )
        
        if opportunities['success']:
            print(f"\n🔍 Found {opportunities['total_opportunities']} upgrade opportunities:")
            
            for opportunity in opportunities['opportunities']:
                subscription = self.sample_subscriptions[opportunity['subscription_id'] - 1]
                customer = self.sample_customers[opportunity['subscription_id'] - 1]
                
                print(f"\n   📈 {customer.name} ({subscription.pricing_tier.name}):")
                print(f"      Trigger: {opportunity['trigger_type']}")
                print(f"      Priority: {opportunity['priority']}")
                
                if 'feature' in opportunity:
                    print(f"      Feature: {opportunity['feature']}")
                if 'usage_percentage' in opportunity:
                    print(f"      Usage: {opportunity['usage_percentage']:.1f}%")
        else:
            print(f"   ❌ Failed to check opportunities: {opportunities['error']}")
    
    def demonstrate_feature_analytics(self):
        """Demonstrate feature usage analytics"""
        print("\n=== Feature Usage Analytics ===")
        
        # Get analytics for individual subscription
        test_subscription = self.sample_subscriptions[1]  # Mid-tier user
        
        analytics = self.payment_service.get_feature_usage_analytics(
            subscription_id=test_subscription.id
        )
        
        if analytics['success']:
            print(f"\n📊 Analytics for {test_subscription.customer.name}:")
            analytics_data = analytics['analytics']
            
            print(f"   Tier: {analytics_data['tier']}")
            print(f"   Upgrade Potential: {analytics_data['upgrade_potential']}")
            print(f"   High Usage Features: {', '.join(analytics_data['high_usage_features'])}")
            
            print(f"\n   Usage Summary:")
            for feature, data in analytics_data['usage_summary'].items():
                print(f"      {feature}: {data['used']}/{data['limit']} ({data['percentage']:.1f}%)")
        else:
            print(f"   ❌ Failed to get analytics: {analytics['error']}")
        
        # Get aggregate analytics
        aggregate_analytics = self.payment_service.get_feature_usage_analytics()
        
        if aggregate_analytics['success']:
            print(f"\n📈 Aggregate Analytics:")
            agg_data = aggregate_analytics['analytics']
            
            print(f"   Total Subscriptions: {agg_data['total_subscriptions']}")
            print(f"   Average Health Checkins: {agg_data['average_usage']['health_checkins']:.1f}")
            print(f"   Average Financial Reports: {agg_data['average_usage']['financial_reports']:.1f}")
            print(f"   Average AI Insights: {agg_data['average_usage']['ai_insights']:.1f}")
    
    def demonstrate_access_status(self):
        """Demonstrate comprehensive access status"""
        print("\n=== Comprehensive Access Status ===")
        
        # Get access status for all features
        test_subscription = self.sample_subscriptions[0]  # Budget user
        
        access_status = self.payment_service.get_feature_access_status(
            subscription_id=test_subscription.id
        )
        
        if access_status['success']:
            print(f"\n🔐 Access Status for {test_subscription.customer.name}:")
            print(f"   Tier: {access_status['tier']}")
            
            for feature, data in access_status['features'].items():
                status_icon = "✅" if data['available'] else "❌"
                print(f"   {status_icon} {feature}:")
                print(f"      Access Level: {data['access_level']}")
                print(f"      Usage: {data['current_usage']}/{data['limit']}")
                print(f"      Available: {data['available']}")
                print(f"      Usage %: {data['usage_percentage']:.1f}%")
        else:
            print(f"   ❌ Failed to get access status: {access_status['error']}")
    
    def demonstrate_upgrade_recommendations(self):
        """Demonstrate personalized upgrade recommendations"""
        print("\n=== Personalized Upgrade Recommendations ===")
        
        # Get recommendations for heavy budget user
        heavy_user = self.sample_subscriptions[3]
        
        recommendations = self.payment_service.get_upgrade_recommendations(
            subscription_id=heavy_user.id
        )
        
        if recommendations['success']:
            print(f"\n💡 Recommendations for {heavy_user.customer.name}:")
            print(f"   Total Recommendations: {recommendations['total_recommendations']}")
            print(f"   High Priority: {recommendations['high_priority_count']}")
            
            for i, rec in enumerate(recommendations['recommendations'], 1):
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
                print(f"\n   {i}. {priority_icon} {rec['type'].replace('_', ' ').title()}:")
                print(f"      {rec['message']}")
                print(f"      Priority: {rec['priority']}")
                
                if 'feature' in rec:
                    print(f"      Feature: {rec['feature']}")
                if 'usage_percentage' in rec:
                    print(f"      Usage: {rec['usage_percentage']:.1f}%")
        else:
            print(f"   ❌ Failed to get recommendations: {recommendations['error']}")
    
    def demonstrate_feature_limit_enforcement(self):
        """Demonstrate feature limit enforcement"""
        print("\n=== Feature Limit Enforcement ===")
        
        # Test limit enforcement for heavy budget user
        heavy_user = self.sample_subscriptions[3]
        
        enforcement = self.payment_service.enforce_feature_limits(
            subscription_id=heavy_user.id
        )
        
        if enforcement['success']:
            print(f"\n⚖️  Limit Enforcement for {heavy_user.customer.name}:")
            print(f"   Total Violations: {enforcement['total_violations']}")
            
            if enforcement['violations']:
                print(f"\n   Violations Found:")
                for violation in enforcement['violations']:
                    print(f"      {violation['feature']}: {violation['used']}/{violation['limit']} (+{violation['excess']} over)")
                
                print(f"\n   Upgrade Prompts Generated: {len(enforcement['upgrade_prompts'])}")
                for i, prompt in enumerate(enforcement['upgrade_prompts'], 1):
                    print(f"      {i}. {prompt['title']}")
            else:
                print(f"   ✅ No violations found")
        else:
            print(f"   ❌ Failed to enforce limits: {enforcement['error']}")
    
    def demonstrate_conversion_drivers(self):
        """Demonstrate conversion drivers and strategies"""
        print("\n=== Conversion Drivers and Strategies ===")
        
        # Test different conversion scenarios
        scenarios = [
            ('budget_user_limit', 'Budget user hitting limits'),
            ('mid_tier_threshold', 'Mid-tier user near thresholds'),
            ('premium_feature', 'Accessing premium features')
        ]
        
        for scenario_name, description in scenarios:
            print(f"\n🎯 {description}:")
            
            if scenario_name == 'budget_user_limit':
                subscription = self.sample_subscriptions[3]  # Heavy budget user
            elif scenario_name == 'mid_tier_threshold':
                subscription = self.sample_subscriptions[1]  # Mid-tier user
            else:
                subscription = self.sample_subscriptions[0]  # Budget user
            
            # Generate upgrade prompt
            prompt = self.payment_service.generate_upgrade_prompt(
                subscription_id=subscription.id
            )
            
            if prompt['success']:
                upgrade_prompt = prompt['upgrade_prompt']
                print(f"   Strategy: {upgrade_prompt['type']}")
                print(f"   Urgency: {upgrade_prompt['urgency']}")
                print(f"   Message: {upgrade_prompt['message']}")
                
                # Show conversion benefits
                print(f"   Key Benefits:")
                for benefit in upgrade_prompt['benefits'][:3]:
                    print(f"      • {benefit}")
                
                # Show pricing comparison
                current_tier = subscription.pricing_tier
                target_tier = prompt['upgrade_target']
                print(f"   Pricing: ${current_tier.monthly_price} → ${upgrade_prompt['pricing']['monthly']}/month")
            else:
                print(f"   ❌ Failed: {prompt['error']}")
    
    def run_all_demonstrations(self):
        """Run all feature access control demonstrations"""
        print("🚀 MINGUS Feature Access Control System Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_feature_access_control()
            self.demonstrate_feature_usage_tracking()
            self.demonstrate_upgrade_prompts()
            self.demonstrate_upgrade_opportunities()
            self.demonstrate_feature_analytics()
            self.demonstrate_access_status()
            self.demonstrate_upgrade_recommendations()
            self.demonstrate_feature_limit_enforcement()
            self.demonstrate_conversion_drivers()
            
            print("\n✅ All feature access control demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = FeatureAccessControlExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 