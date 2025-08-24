"""
Admin Conversion Funnel Example for MINGUS
Demonstrates subscription conversion funnel analysis for administrators
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.admin_billing_dashboard import AdminBillingDashboard
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory

class AdminConversionFunnelExample:
    """Example demonstrating admin conversion funnel analysis"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_conversion_funnel_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.admin_dashboard = AdminBillingDashboard(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for conversion funnel demonstration"""
        # Create pricing tiers
        budget_tier = PricingTier(
            tier_type='budget',
            name='Budget',
            description='Basic features for individual users',
            monthly_price=15.00,
            yearly_price=150.00,
            max_health_checkins_per_month=4,
            max_financial_reports_per_month=2,
            max_ai_insights_per_month=0,
            max_custom_reports_per_month=0,
            max_team_members=0,
            max_api_calls_per_hour=0
        )
        
        mid_tier = PricingTier(
            tier_type='mid_tier',
            name='Mid-Tier',
            description='Enhanced features for serious users',
            monthly_price=35.00,
            yearly_price=350.00,
            max_health_checkins_per_month=12,
            max_financial_reports_per_month=10,
            max_ai_insights_per_month=50,
            max_custom_reports_per_month=5,
            max_team_members=0,
            max_api_calls_per_hour=0
        )
        
        professional_tier = PricingTier(
            tier_type='professional',
            name='Professional',
            description='Complete solution for professionals',
            monthly_price=75.00,
            yearly_price=750.00,
            max_health_checkins_per_month=-1,
            max_financial_reports_per_month=-1,
            max_ai_insights_per_month=-1,
            max_custom_reports_per_month=-1,
            max_team_members=10,
            max_api_calls_per_hour=10000
        )
        
        self.db_session.add_all([budget_tier, mid_tier, professional_tier])
        self.db_session.commit()
        
        # Create sample customers with conversion funnel patterns
        customers = []
        for i in range(100):  # Create 100 customers for better funnel analysis
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_funnel_{i}' if i < 80 else None,  # 80% account creation rate
                email=f'funnel.user{i}@example.com',
                name=f'Funnel User {i}',
                address={
                    'country': 'US' if i < 60 else 'CA' if i < 80 else 'UK',
                    'state': 'CA' if i < 30 else 'NY' if i < 60 else 'ON' if i < 80 else 'London',
                    'city': 'San Francisco' if i < 30 else 'New York' if i < 60 else 'Toronto' if i < 80 else 'London',
                    'zip': '94105' if i < 30 else '10001' if i < 60 else 'M5V' if i < 80 else 'SW1A'
                },
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=365 - (i * 3))  # Staggered creation dates
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with conversion funnel patterns
        subscriptions = []
        billing_records = []
        
        # Standard conversion funnel simulation
        # Stage 1: 100 website visitors (all customers)
        # Stage 2: 80 account creations (80% conversion)
        # Stage 3: 60 trial started (75% of account creations)
        # Stage 4: 45 trial completed (75% of trials)
        # Stage 5: 30 paid subscriptions (67% of completed trials)
        # Stage 6: 25 retained after 30 days (83% of paid)
        
        # Create trial subscriptions (60 customers)
        for i in range(60):
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id if i < 40 else mid_tier.id if i < 55 else professional_tier.id,
                stripe_subscription_id=f'sub_funnel_{i}',
                status='active' if i < 30 else 'canceled' if i < 45 else 'past_due',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 50 else 'annual',
                amount=15.00 if i < 40 else 35.00 if i < 55 else 75.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history for paid subscriptions
            if i < 30:  # Paid subscriptions
                billing_record = BillingHistory(
                    customer_id=customers[i].id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-001',
                    amount=subscription.amount,
                    currency='USD',
                    status='paid',
                    description=f'Subscription payment - {subscription.pricing_tier.name}',
                    created_at=datetime.utcnow() - timedelta(days=25),
                    paid_at=datetime.utcnow() - timedelta(days=25),
                    stripe_invoice_id=f'in_{subscription.id}_funnel'
                )
                billing_records.append(billing_record)
        
        # Create tier upgrade funnel simulation
        # Start with budget tier customers who upgrade
        for i in range(40, 60):  # 20 customers who started with budget
            # Create budget tier subscription (historical)
            budget_subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id=f'sub_budget_funnel_{i}',
                status='canceled',
                current_period_start=datetime.utcnow() - timedelta(days=90),
                current_period_end=datetime.utcnow() - timedelta(days=60),
                billing_cycle='monthly',
                amount=15.00,
                currency='USD',
                canceled_at=datetime.utcnow() - timedelta(days=60)
            )
            subscriptions.append(budget_subscription)
            
            # Create upgraded subscription
            upgraded_subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=mid_tier.id if i < 50 else professional_tier.id,
                stripe_subscription_id=f'sub_upgraded_funnel_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='annual' if i < 55 else 'monthly',
                amount=29.17 if i < 50 else 75.00,  # Annual equivalent for mid-tier
                currency='USD'
            )
            subscriptions.append(upgraded_subscription)
            
            # Create billing history for upgrades
            billing_record = BillingHistory(
                customer_id=customers[i].id,
                subscription_id=upgraded_subscription.id,
                invoice_number=f'INV-{upgraded_subscription.id:04d}-001',
                amount=upgraded_subscription.amount * 12 if upgraded_subscription.billing_cycle == 'annual' else upgraded_subscription.amount,
                currency='USD',
                status='paid',
                description=f'Upgrade payment - {upgraded_subscription.pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=25),
                paid_at=datetime.utcnow() - timedelta(days=25),
                stripe_invoice_id=f'in_{upgraded_subscription.id}_upgrade'
            )
            billing_records.append(billing_record)
        
        # Create trial conversion funnel simulation
        # 30 trial customers with different conversion patterns
        for i in range(60, 90):
            trial_subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id=f'sub_trial_funnel_{i}',
                status='active' if i < 75 else 'canceled',
                current_period_start=datetime.utcnow() - timedelta(days=7 if i < 75 else 3),
                current_period_end=datetime.utcnow() + timedelta(days=23 if i < 75 else 0),
                billing_cycle='monthly',
                amount=15.00,
                currency='USD'
            )
            subscriptions.append(trial_subscription)
            
            # Create billing history for converted trials
            if i < 75:  # Converted trials
                billing_record = BillingHistory(
                    customer_id=customers[i].id,
                    subscription_id=trial_subscription.id,
                    invoice_number=f'INV-{trial_subscription.id:04d}-001',
                    amount=15.00,
                    currency='USD',
                    status='paid',
                    description=f'Trial conversion payment - {trial_subscription.pricing_tier.name}',
                    created_at=datetime.utcnow() - timedelta(days=2),
                    paid_at=datetime.utcnow() - timedelta(days=2),
                    stripe_invoice_id=f'in_{trial_subscription.id}_trial'
                )
                billing_records.append(billing_record)
        
        # Create some failed payments for realistic funnel analysis
        for i in range(5):
            failed_billing = BillingHistory(
                customer_id=customers[i].id,
                subscription_id=subscriptions[i].id,
                invoice_number=f'INV-{subscriptions[i].id:04d}-FAILED',
                amount=15.00,
                currency='USD',
                status='failed',
                description=f'Failed payment - {subscriptions[i].pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=5),
                stripe_invoice_id=f'in_{subscriptions[i].id}_failed'
            )
            billing_records.append(failed_billing)
        
        self.db_session.add_all(subscriptions)
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_standard_conversion_funnel(self):
        """Demonstrate standard conversion funnel analysis"""
        print("\n=== Standard Conversion Funnel Analysis ===")
        
        print(f"\n📊 Testing Standard Conversion Funnel:")
        
        # Test 30-day standard funnel
        print(f"\n1. 30-Day Standard Conversion Funnel:")
        funnel_result = self.admin_dashboard.get_subscription_conversion_funnel(
            date_range='30d',
            funnel_type='standard'
        )
        
        if funnel_result['success']:
            funnel = funnel_result['conversion_funnel']
            
            print(f"   ✅ Standard conversion funnel retrieved")
            print(f"   📅 Date Range: {funnel['date_range']['start_date']} to {funnel['date_range']['end_date']}")
            print(f"   📊 Period: {funnel['date_range']['period']}")
            print(f"   🎯 Overall Conversion Rate: {funnel['overall_conversion_rate']:.1f}%")
            
            # Display funnel stages
            funnel_data = funnel['funnel_data']
            print(f"   📈 Funnel Stages:")
            for stage in funnel_data['funnel_stages']:
                print(f"      {stage['stage']}:")
                print(f"         Count: {stage['count']}")
                print(f"         Conversion Rate: {stage['conversion_rate']:.1f}%")
                print(f"         Drop-off Rate: {stage['drop_off_rate']:.1f}%")
            
            # Display bottleneck analysis
            bottlenecks = funnel['bottleneck_analysis']
            print(f"   ⚠️ Bottleneck Analysis:")
            if bottlenecks:
                for bottleneck in bottlenecks:
                    print(f"      {bottleneck['stage']}:")
                    print(f"         Severity: {bottleneck['severity']}")
                    print(f"         Drop-off Rate: {bottleneck['drop_off_rate']:.1f}%")
                    print(f"         Impact: {bottleneck['impact']}")
                    print(f"         Recommendation: {bottleneck['recommendation']}")
            else:
                print(f"      No significant bottlenecks identified")
            
            # Display optimization recommendations
            recommendations = funnel['optimization_recommendations']
            print(f"   💡 Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {funnel_result['error']}")
        
        # Test 90-day funnel
        print(f"\n2. 90-Day Standard Conversion Funnel:")
        funnel_result = self.admin_dashboard.get_subscription_conversion_funnel(
            date_range='90d',
            funnel_type='standard'
        )
        
        if funnel_result['success']:
            funnel = funnel_result['conversion_funnel']
            print(f"   ✅ 90-day funnel retrieved")
            print(f"   🎯 Overall Conversion Rate: {funnel['overall_conversion_rate']:.1f}%")
            print(f"   📊 Total Drop-off Rate: {funnel['funnel_data']['total_drop_off_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {funnel_result['error']}")
    
    def demonstrate_tier_upgrade_funnel(self):
        """Demonstrate tier upgrade conversion funnel"""
        print("\n=== Tier Upgrade Conversion Funnel ===")
        
        print(f"\n📊 Testing Tier Upgrade Conversion Funnel:")
        
        # Test tier upgrade funnel
        print(f"\n1. Tier Upgrade Conversion Funnel:")
        funnel_result = self.admin_dashboard.get_subscription_conversion_funnel(
            date_range='90d',
            funnel_type='tier_upgrade'
        )
        
        if funnel_result['success']:
            funnel = funnel_result['conversion_funnel']
            
            print(f"   ✅ Tier upgrade funnel retrieved")
            print(f"   📅 Date Range: {funnel['date_range']['start_date']} to {funnel['date_range']['end_date']}")
            print(f"   🎯 Overall Conversion Rate: {funnel['overall_conversion_rate']:.1f}%")
            
            # Display funnel stages
            funnel_data = funnel['funnel_data']
            print(f"   📈 Tier Upgrade Funnel Stages:")
            for stage in funnel_data['funnel_stages']:
                print(f"      {stage['stage']}:")
                print(f"         Count: {stage['count']}")
                print(f"         Conversion Rate: {stage['conversion_rate']:.1f}%")
                print(f"         Drop-off Rate: {stage['drop_off_rate']:.1f}%")
            
            # Display bottleneck analysis
            bottlenecks = funnel['bottleneck_analysis']
            print(f"   ⚠️ Upgrade Bottleneck Analysis:")
            if bottlenecks:
                for bottleneck in bottlenecks:
                    print(f"      {bottleneck['stage']}:")
                    print(f"         Severity: {bottleneck['severity']}")
                    print(f"         Drop-off Rate: {bottleneck['drop_off_rate']:.1f}%")
                    print(f"         Recommendation: {bottleneck['recommendation']}")
            else:
                print(f"      No significant upgrade bottlenecks identified")
        else:
            print(f"   ❌ Failed: {funnel_result['error']}")
    
    def demonstrate_billing_cycle_funnel(self):
        """Demonstrate billing cycle conversion funnel"""
        print("\n=== Billing Cycle Conversion Funnel ===")
        
        print(f"\n📊 Testing Billing Cycle Conversion Funnel:")
        
        # Test billing cycle funnel
        print(f"\n1. Billing Cycle Conversion Funnel:")
        funnel_result = self.admin_dashboard.get_subscription_conversion_funnel(
            date_range='90d',
            funnel_type='billing_cycle'
        )
        
        if funnel_result['success']:
            funnel = funnel_result['conversion_funnel']
            
            print(f"   ✅ Billing cycle funnel retrieved")
            print(f"   📅 Date Range: {funnel['date_range']['start_date']} to {funnel['date_range']['end_date']}")
            print(f"   🎯 Overall Conversion Rate: {funnel['overall_conversion_rate']:.1f}%")
            
            # Display funnel stages
            funnel_data = funnel['funnel_data']
            print(f"   📈 Billing Cycle Funnel Stages:")
            for stage in funnel_data['funnel_stages']:
                print(f"      {stage['stage']}:")
                print(f"         Count: {stage['count']}")
                print(f"         Conversion Rate: {stage['conversion_rate']:.1f}%")
                print(f"         Drop-off Rate: {stage['drop_off_rate']:.1f}%")
            
            # Display optimization recommendations
            recommendations = funnel['optimization_recommendations']
            print(f"   💡 Billing Cycle Optimization:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {funnel_result['error']}")
    
    def demonstrate_trial_conversion_funnel(self):
        """Demonstrate trial conversion funnel"""
        print("\n=== Trial Conversion Funnel ===")
        
        print(f"\n📊 Testing Trial Conversion Funnel:")
        
        # Test trial conversion funnel
        print(f"\n1. Trial Conversion Funnel:")
        funnel_result = self.admin_dashboard.get_subscription_conversion_funnel(
            date_range='30d',
            funnel_type='trial_conversion'
        )
        
        if funnel_result['success']:
            funnel = funnel_result['conversion_funnel']
            
            print(f"   ✅ Trial conversion funnel retrieved")
            print(f"   📅 Date Range: {funnel['date_range']['start_date']} to {funnel['date_range']['end_date']}")
            print(f"   🎯 Overall Conversion Rate: {funnel['overall_conversion_rate']:.1f}%")
            
            # Display funnel stages
            funnel_data = funnel['funnel_data']
            print(f"   📈 Trial Conversion Funnel Stages:")
            for stage in funnel_data['funnel_stages']:
                print(f"      {stage['stage']}:")
                print(f"         Count: {stage['count']}")
                print(f"         Conversion Rate: {stage['conversion_rate']:.1f}%")
                print(f"         Drop-off Rate: {stage['drop_off_rate']:.1f}%")
            
            # Display bottleneck analysis
            bottlenecks = funnel['bottleneck_analysis']
            print(f"   ⚠️ Trial Bottleneck Analysis:")
            if bottlenecks:
                for bottleneck in bottlenecks:
                    print(f"      {bottleneck['stage']}:")
                    print(f"         Severity: {bottleneck['severity']}")
                    print(f"         Drop-off Rate: {bottleneck['drop_off_rate']:.1f}%")
                    print(f"         Recommendation: {bottleneck['recommendation']}")
            else:
                print(f"      No significant trial bottlenecks identified")
        else:
            print(f"   ❌ Failed: {funnel_result['error']}")
    
    def demonstrate_conversion_funnel_trends(self):
        """Demonstrate conversion funnel trends"""
        print("\n=== Conversion Funnel Trends ===")
        
        print(f"\n📊 Testing Conversion Funnel Trends:")
        
        # Test standard funnel trends
        print(f"\n1. Standard Conversion Funnel Trends (12 months):")
        trends_result = self.admin_dashboard.get_conversion_funnel_trends(
            funnel_type='standard',
            period='12m'
        )
        
        if trends_result['success']:
            trends = trends_result['conversion_funnel_trends']
            
            print(f"   ✅ Conversion funnel trends retrieved")
            print(f"   📅 Period: {trends['period']}")
            print(f"   📊 Funnel Type: {trends['funnel_type']}")
            
            # Display trend analysis
            trend_analysis = trends['trend_analysis']
            print(f"   📈 Trend Analysis:")
            print(f"      Average Conversion Rate: {trend_analysis['average_conversion_rate']:.1f}%")
            print(f"      Trend Direction: {trend_analysis['trend_direction']}")
            print(f"      Trend Percentage: {trend_analysis['trend_percentage']:.1f}%")
            print(f"      Best Period: {trend_analysis['best_period']}")
            print(f"      Worst Period: {trend_analysis['worst_period']}")
            print(f"      Consistency Score: {trend_analysis['consistency_score']:.1f}/100")
            
            # Display monthly trends
            print(f"   📅 Monthly Conversion Rates:")
            for monthly_funnel in trends['monthly_funnels'][:6]:  # Show first 6 months
                print(f"      {monthly_funnel['period']}: {monthly_funnel['conversion_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {trends_result['error']}")
        
        # Test tier upgrade funnel trends
        print(f"\n2. Tier Upgrade Funnel Trends (12 months):")
        trends_result = self.admin_dashboard.get_conversion_funnel_trends(
            funnel_type='tier_upgrade',
            period='12m'
        )
        
        if trends_result['success']:
            trends = trends_result['conversion_funnel_trends']
            trend_analysis = trends['trend_analysis']
            
            print(f"   ✅ Tier upgrade trends retrieved")
            print(f"   📈 Trend Analysis:")
            print(f"      Average Conversion Rate: {trend_analysis['average_conversion_rate']:.1f}%")
            print(f"      Trend Direction: {trend_analysis['trend_direction']}")
            print(f"      Consistency Score: {trend_analysis['consistency_score']:.1f}/100")
        else:
            print(f"   ❌ Failed: {trends_result['error']}")
    
    def demonstrate_conversion_funnel_breakdown(self):
        """Demonstrate conversion funnel breakdown analysis"""
        print("\n=== Conversion Funnel Breakdown Analysis ===")
        
        print(f"\n📊 Testing Conversion Funnel Breakdown:")
        
        # Test tier breakdown
        print(f"\n1. Conversion Funnel Breakdown by Tier:")
        breakdown_result = self.admin_dashboard.get_conversion_funnel_breakdown(
            funnel_type='standard',
            breakdown_dimension='tier',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['conversion_funnel_breakdown']
            
            print(f"   ✅ Tier breakdown retrieved")
            print(f"   📊 Breakdown Dimension: {breakdown['breakdown_dimension']}")
            print(f"   📅 Date Range: {breakdown['date_range']}")
            
            # Display tier breakdown
            breakdown_data = breakdown['breakdown_data']
            print(f"   🏆 Tier Conversion Rates:")
            for tier_type, tier_data in breakdown_data.items():
                print(f"      {tier_data['tier_name']}:")
                print(f"         Conversion Rate: {tier_data['conversion_rate']:.1f}%")
                print(f"         Funnel Stages: {len(tier_data['funnel_data']['funnel_stages'])}")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test geographic breakdown
        print(f"\n2. Conversion Funnel Breakdown by Geographic Location:")
        breakdown_result = self.admin_dashboard.get_conversion_funnel_breakdown(
            funnel_type='standard',
            breakdown_dimension='geographic',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['conversion_funnel_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Geographic breakdown retrieved")
            print(f"   🌍 Geographic Conversion Rates:")
            for country, geo_data in breakdown_data.items():
                print(f"      {country}:")
                print(f"         Customer Count: {geo_data['customer_count']}")
                print(f"         Conversion Rate: {geo_data['conversion_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test time period breakdown
        print(f"\n3. Conversion Funnel Breakdown by Time Period:")
        breakdown_result = self.admin_dashboard.get_conversion_funnel_breakdown(
            funnel_type='standard',
            breakdown_dimension='time_period',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['conversion_funnel_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Time period breakdown retrieved")
            print(f"   📅 Weekly Conversion Rates:")
            for week_key, week_data in list(breakdown_data.items())[:4]:  # Show first 4 weeks
                print(f"      {week_data['period']}: {week_data['conversion_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test customer segment breakdown
        print(f"\n4. Conversion Funnel Breakdown by Customer Segment:")
        breakdown_result = self.admin_dashboard.get_conversion_funnel_breakdown(
            funnel_type='standard',
            breakdown_dimension='customer_segment',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['conversion_funnel_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Customer segment breakdown retrieved")
            print(f"   👥 Customer Segment Conversion Rates:")
            for segment_key, segment_data in breakdown_data.items():
                print(f"      {segment_data['segment_name']}:")
                print(f"         Conversion Rate: {segment_data['conversion_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
    
    def run_all_conversion_funnel_demonstrations(self):
        """Run all conversion funnel demonstrations"""
        print("🚀 MINGUS Admin Conversion Funnel Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_standard_conversion_funnel()
            self.demonstrate_tier_upgrade_funnel()
            self.demonstrate_billing_cycle_funnel()
            self.demonstrate_trial_conversion_funnel()
            self.demonstrate_conversion_funnel_trends()
            self.demonstrate_conversion_funnel_breakdown()
            
            print("\n✅ All conversion funnel demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = AdminConversionFunnelExample()
    example.run_all_conversion_funnel_demonstrations()

if __name__ == "__main__":
    main() 