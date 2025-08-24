"""
Enhanced Usage Tracking Example for MINGUS
Demonstrates real-time usage tracking, monthly reset automation, analytics, and overage detection
"""
import os
import sys
from datetime import datetime, timedelta
import time

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, FeatureUsage

class EnhancedUsageTrackingExample:
    """Example demonstrating enhanced usage tracking with real-time monitoring and analytics"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_enhanced_usage_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for enhanced usage tracking demonstration"""
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
                stripe_customer_id=f'cus_{tier}_usage_demo_{i}',
                email=f'{tier}.usage.user{i}@example.com',
                name=f'{tier.title()} Usage User {i}',
                address={'country': 'US', 'state': 'CA'}
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with different usage patterns
        subscriptions = []
        
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
        
        # Professional user with unlimited usage
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
        
        # Create feature usage records with different patterns
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
        
        # Professional user: High usage (unlimited features)
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
        self.budget_usage = budget_usage
        self.mid_tier_usage = mid_tier_usage
        self.professional_usage = professional_usage
    
    def demonstrate_real_time_usage_tracking(self):
        """Demonstrate real-time usage tracking with immediate cache updates"""
        print("\n=== Real-Time Usage Tracking ===")
        
        print(f"\n🔄 Testing Real-Time Usage Tracking:")
        
        # Test tracking health check-in for budget user
        print(f"\n1. Tracking Health Check-in for Budget User:")
        tracking_result = self.payment_service.track_feature_usage_real_time(
            subscription_id=self.budget_subscription.id,
            feature_name='health_checkin',
            user_id=1,
            metadata={'checkin_type': 'daily', 'timestamp': datetime.utcnow().isoformat()}
        )
        
        if tracking_result['success']:
            print(f"   ✅ Usage tracked successfully")
            print(f"   Current Usage: {tracking_result['current_usage']}/4")
            print(f"   Usage Percentage: {tracking_result['usage_percentage']:.1f}%")
            print(f"   Decision: {tracking_result['decision']}")
        else:
            print(f"   ❌ Failed: {tracking_result['error']}")
        
        # Test tracking AI insight for mid-tier user
        print(f"\n2. Tracking AI Insight for Mid-Tier User:")
        tracking_result = self.payment_service.track_feature_usage_real_time(
            subscription_id=self.mid_tier_subscription.id,
            feature_name='ai_insight',
            user_id=2,
            metadata={'insight_type': 'spending_pattern', 'timestamp': datetime.utcnow().isoformat()}
        )
        
        if tracking_result['success']:
            print(f"   ✅ Usage tracked successfully")
            print(f"   Current Usage: {tracking_result['current_usage']}/50")
            print(f"   Usage Percentage: {tracking_result['usage_percentage']:.1f}%")
            print(f"   Decision: {tracking_result['decision']}")
        else:
            print(f"   ❌ Failed: {tracking_result['error']}")
        
        # Test tracking unlimited feature for professional user
        print(f"\n3. Tracking Unlimited Feature for Professional User:")
        tracking_result = self.payment_service.track_feature_usage_real_time(
            subscription_id=self.professional_subscription.id,
            feature_name='health_checkin',
            user_id=3,
            metadata={'checkin_type': 'advanced', 'timestamp': datetime.utcnow().isoformat()}
        )
        
        if tracking_result['success']:
            print(f"   ✅ Usage tracked successfully")
            print(f"   Current Usage: {tracking_result['current_usage']} (unlimited)")
            print(f"   Usage Percentage: {tracking_result['usage_percentage']:.1f}%")
            print(f"   Decision: {tracking_result['decision']}")
        else:
            print(f"   ❌ Failed: {tracking_result['error']}")
    
    def demonstrate_real_time_usage_monitoring(self):
        """Demonstrate real-time usage monitoring from cache"""
        print("\n=== Real-Time Usage Monitoring ===")
        
        print(f"\n🔄 Testing Real-Time Usage Monitoring:")
        
        # Test getting real-time usage for budget user
        print(f"\n1. Real-Time Usage for Budget User:")
        usage_data = self.payment_service.get_real_time_usage(
            subscription_id=self.budget_subscription.id
        )
        
        if usage_data['success']:
            print(f"   ✅ Real-time usage retrieved")
            print(f"   Cache Hit: {usage_data.get('cache_hit', False)}")
            print(f"   Last Updated: {usage_data.get('last_updated', 'N/A')}")
            
            usage = usage_data['usage']
            print(f"   Health Check-ins: {usage.get('health_checkin_used', 0)}")
            print(f"   Financial Reports: {usage.get('financial_report_used', 0)}")
            print(f"   Support Requests: {usage.get('support_requests_used', 0)}")
        else:
            print(f"   ❌ Failed: {usage_data['error']}")
        
        # Test getting specific feature usage
        print(f"\n2. Specific Feature Usage (Health Check-ins):")
        feature_usage = self.payment_service.get_real_time_usage(
            subscription_id=self.budget_subscription.id,
            feature_name='health_checkin'
        )
        
        if feature_usage['success']:
            print(f"   ✅ Feature usage retrieved")
            print(f"   Usage: {feature_usage['usage']}")
            print(f"   Cache Hit: {feature_usage.get('cache_hit', False)}")
        else:
            print(f"   ❌ Failed: {feature_usage['error']}")
    
    def demonstrate_usage_limits_and_overages(self):
        """Demonstrate usage limits and overage detection"""
        print("\n=== Usage Limits and Overage Detection ===")
        
        print(f"\n🔄 Testing Usage Limits and Overages:")
        
        # Test budget user limits
        print(f"\n1. Budget User Limits and Overages:")
        limits_result = self.payment_service.check_usage_limits_and_overages(
            subscription_id=self.budget_subscription.id
        )
        
        if limits_result['success']:
            analysis = limits_result['usage_analysis']
            print(f"   ✅ Analysis completed")
            print(f"   Tier: {analysis['tier']}")
            print(f"   Total Overages: {analysis['total_overages']}")
            print(f"   Total Overage Cost: ${analysis['total_overage_cost']:.2f}")
            
            if analysis['warnings']:
                print(f"   ⚠️  Warnings: {len(analysis['warnings'])}")
                for warning in analysis['warnings']:
                    print(f"      - {warning['message']}")
            
            if analysis['critical_alerts']:
                print(f"   🚨 Critical Alerts: {len(analysis['critical_alerts'])}")
                for alert in analysis['critical_alerts']:
                    print(f"      - {alert['message']}")
            
            # Show feature details
            for feature_name, feature_data in analysis['features'].items():
                if feature_data['current_usage'] > 0:
                    print(f"   📊 {feature_name}: {feature_data['current_usage']}/{feature_data['limit']} ({feature_data['usage_percentage']:.1f}%)")
                    if feature_data['is_overage']:
                        print(f"      💰 Overage: {feature_data['overage_amount']} units, Cost: ${feature_data['overage_cost']:.2f}")
        else:
            print(f"   ❌ Failed: {limits_result['error']}")
        
        # Test mid-tier user limits
        print(f"\n2. Mid-Tier User Limits and Overages:")
        limits_result = self.payment_service.check_usage_limits_and_overages(
            subscription_id=self.mid_tier_subscription.id
        )
        
        if limits_result['success']:
            analysis = limits_result['usage_analysis']
            print(f"   ✅ Analysis completed")
            print(f"   Tier: {analysis['tier']}")
            print(f"   Total Overages: {analysis['total_overages']}")
            print(f"   Total Overage Cost: ${analysis['total_overage_cost']:.2f}")
            
            if analysis['warnings']:
                print(f"   ⚠️  Warnings: {len(analysis['warnings'])}")
                for warning in analysis['warnings']:
                    print(f"      - {warning['message']}")
        else:
            print(f"   ❌ Failed: {limits_result['error']}")
    
    def demonstrate_usage_analytics(self):
        """Demonstrate comprehensive usage analytics"""
        print("\n=== Usage Analytics and Reporting ===")
        
        print(f"\n🔄 Testing Usage Analytics:")
        
        # Test comprehensive analytics
        print(f"\n1. Comprehensive Usage Analytics:")
        analytics_result = self.payment_service.get_comprehensive_usage_analytics(
            date_range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow())
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            print(f"   ✅ Analytics generated")
            print(f"   Total Records: {analytics['total_records']}")
            print(f"   Generated At: {analytics_result['generated_at']}")
            
            # Show feature usage summary
            print(f"\n   📊 Feature Usage Summary:")
            for feature_name, data in analytics['feature_usage'].items():
                if data['total_usage'] > 0:
                    print(f"      {feature_name}:")
                    print(f"        Total Usage: {data['total_usage']}")
                    print(f"        Average Usage: {data['average_usage']:.1f}")
                    print(f"        Max Usage: {data['max_usage']}")
                    print(f"        Min Usage: {data['min_usage']}")
            
            # Show monthly trends
            print(f"\n   📈 Monthly Trends:")
            for month, data in analytics['monthly_trends'].items():
                print(f"      {month}: {data['total_usage']} total usage, {data['subscription_count']} subscriptions")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
        
        # Test subscription-specific analytics
        print(f"\n2. Subscription-Specific Analytics:")
        analytics_result = self.payment_service.get_comprehensive_usage_analytics(
            subscription_id=self.budget_subscription.id
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            print(f"   ✅ Subscription analytics generated")
            print(f"   Total Records: {analytics['total_records']}")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
    
    def demonstrate_overage_reporting(self):
        """Demonstrate overage reporting and analysis"""
        print("\n=== Overage Reporting and Analysis ===")
        
        print(f"\n🔄 Testing Overage Reporting:")
        
        # Test comprehensive overage report
        print(f"\n1. Comprehensive Overage Report:")
        overage_result = self.payment_service.get_overage_report(
            date_range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow())
        )
        
        if overage_result['success']:
            overage_report = overage_result['overage_report']
            print(f"   ✅ Overage report generated")
            print(f"   Total Overages: {overage_report['total_overages']}")
            print(f"   Total Overage Cost: ${overage_report['total_overage_cost']:.2f}")
            print(f"   Subscriptions with Overages: {len(overage_report['subscription_overages'])}")
            
            # Show feature overages
            print(f"\n   📊 Feature Overages:")
            for feature_name, data in overage_report['feature_overages'].items():
                if data['total_overages'] > 0:
                    print(f"      {feature_name}:")
                    print(f"        Total Overages: {data['total_overages']}")
                    print(f"        Total Cost: ${data['total_overage_cost']:.2f}")
                    print(f"        Subscriptions Affected: {data['subscriptions_affected']}")
            
            # Show subscription overages
            print(f"\n   👥 Subscription Overages:")
            for sub_id, sub_data in overage_report['subscription_overages'].items():
                print(f"      Subscription {sub_id} ({sub_data['customer_email']}):")
                print(f"        Tier: {sub_data['tier']}")
                print(f"        Total Overage Cost: ${sub_data['total_overage_cost']:.2f}")
                for overage in sub_data['overages']:
                    print(f"        - {overage['feature_name']}: {overage['overage_amount']} over, ${overage['overage_cost']:.2f}")
        else:
            print(f"   ❌ Failed: {overage_result['error']}")
    
    def demonstrate_usage_dashboard(self):
        """Demonstrate comprehensive usage dashboard"""
        print("\n=== Usage Dashboard ===")
        
        print(f"\n🔄 Testing Usage Dashboard:")
        
        # Test comprehensive dashboard data
        print(f"\n1. Comprehensive Dashboard Data:")
        dashboard_result = self.payment_service.get_usage_dashboard_data(
            date_range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow())
        )
        
        if dashboard_result['success']:
            dashboard_data = dashboard_result['dashboard_data']
            summary = dashboard_data['summary']
            
            print(f"   ✅ Dashboard data generated")
            print(f"   📊 Summary Statistics:")
            print(f"      Total Features Tracked: {summary['total_features_tracked']}")
            print(f"      Total Subscriptions: {summary['total_subscriptions']}")
            print(f"      Active Subscriptions: {summary['active_subscriptions']}")
            print(f"      Subscriptions with Overages: {summary['subscriptions_with_overages']}")
            print(f"      Total Overage Cost: ${summary['total_overage_cost']:.2f}")
            
            # Show analytics summary
            analytics = dashboard_data['analytics']
            if analytics.get('feature_usage'):
                print(f"\n   📈 Analytics Summary:")
                for feature_name, data in analytics['feature_usage'].items():
                    if data['total_usage'] > 0:
                        print(f"      {feature_name}: {data['total_usage']} total usage")
            
            # Show overage summary
            overage_report = dashboard_data['overage_report']
            if overage_report.get('feature_overages'):
                print(f"\n   💰 Overage Summary:")
                for feature_name, data in overage_report['feature_overages'].items():
                    if data['total_overages'] > 0:
                        print(f"      {feature_name}: {data['total_overages']} overages, ${data['total_overage_cost']:.2f}")
        else:
            print(f"   ❌ Failed: {dashboard_result['error']}")
        
        # Test subscription-specific dashboard
        print(f"\n2. Subscription-Specific Dashboard:")
        dashboard_result = self.payment_service.get_usage_dashboard_data(
            subscription_id=self.budget_subscription.id
        )
        
        if dashboard_result['success']:
            dashboard_data = dashboard_result['dashboard_data']
            real_time_usage = dashboard_data['real_time_usage']
            
            print(f"   ✅ Subscription dashboard generated")
            print(f"   📊 Real-Time Usage:")
            for key, value in real_time_usage.items():
                if key.endswith('_used') and value > 0:
                    feature_name = key.replace('_used', '').replace('_', ' ').title()
                    print(f"      {feature_name}: {value}")
        else:
            print(f"   ❌ Failed: {dashboard_result['error']}")
    
    def demonstrate_monthly_reset_simulation(self):
        """Demonstrate monthly reset simulation"""
        print("\n=== Monthly Reset Simulation ===")
        
        print(f"\n🔄 Testing Monthly Reset Simulation:")
        
        # Show current usage before reset
        print(f"\n1. Current Usage Before Reset:")
        for subscription in [self.budget_subscription, self.mid_tier_subscription, self.professional_subscription]:
            usage_data = self.payment_service.get_real_time_usage(subscription.id)
            if usage_data['success']:
                usage = usage_data['usage']
                print(f"   📊 Subscription {subscription.id} ({subscription.pricing_tier.tier_type}):")
                print(f"      Health Check-ins: {usage.get('health_checkin_used', 0)}")
                print(f"      Financial Reports: {usage.get('financial_report_used', 0)}")
                print(f"      AI Insights: {usage.get('ai_insight_used', 0)}")
        
        # Simulate monthly reset (this would normally happen automatically)
        print(f"\n2. Simulating Monthly Reset:")
        print(f"   🔄 Monthly reset would automatically:")
        print(f"      - Create new usage records for the new month")
        print(f"      - Reset all usage counters to zero")
        print(f"      - Archive previous month's usage data")
        print(f"      - Send reset notifications to users")
        print(f"      - Update analytics and reporting")
        
        # Show what the reset would look like
        print(f"\n3. Post-Reset Usage (Simulated):")
        for subscription in [self.budget_subscription, self.mid_tier_subscription, self.professional_subscription]:
            print(f"   📊 Subscription {subscription.id} ({subscription.pricing_tier.tier_type}):")
            print(f"      Health Check-ins: 0 (reset)")
            print(f"      Financial Reports: 0 (reset)")
            print(f"      AI Insights: 0 (reset)")
    
    def demonstrate_automated_monitoring(self):
        """Demonstrate automated monitoring capabilities"""
        print("\n=== Automated Monitoring ===")
        
        print(f"\n🔄 Testing Automated Monitoring:")
        
        print(f"\n1. Real-Time Monitoring Features:")
        print(f"   🔍 Continuous monitoring every 30 seconds")
        print(f"   📊 Usage cache updates in real-time")
        print(f"   ⚠️  Automatic overage detection")
        print(f"   📧 Automated notifications")
        print(f"   📈 Performance tracking")
        
        print(f"\n2. Monitoring Triggers:")
        print(f"   🎯 80% usage threshold warnings")
        print(f"   🚨 95% usage threshold critical alerts")
        print(f"   💰 Overage detection and cost calculation")
        print(f"   📅 Monthly reset automation")
        print(f"   📊 Analytics generation")
        
        print(f"\n3. Notification Types:")
        print(f"   📧 Email notifications for warnings")
        print(f"   🚨 Critical alerts for high usage")
        print(f"   💰 Overage cost notifications")
        print(f"   📅 Monthly reset confirmations")
        print(f"   📊 Usage summary reports")
    
    def run_all_demonstrations(self):
        """Run all enhanced usage tracking demonstrations"""
        print("🚀 MINGUS Enhanced Usage Tracking Demonstration")
        print("=" * 65)
        
        try:
            self.demonstrate_real_time_usage_tracking()
            self.demonstrate_real_time_usage_monitoring()
            self.demonstrate_usage_limits_and_overages()
            self.demonstrate_usage_analytics()
            self.demonstrate_overage_reporting()
            self.demonstrate_usage_dashboard()
            self.demonstrate_monthly_reset_simulation()
            self.demonstrate_automated_monitoring()
            
            print("\n✅ All enhanced usage tracking demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = EnhancedUsageTrackingExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 