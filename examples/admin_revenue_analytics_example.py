"""
Admin Revenue Analytics Example for MINGUS
Demonstrates comprehensive revenue analytics and trending for administrators
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

class AdminRevenueAnalyticsExample:
    """Example demonstrating admin revenue analytics and trending"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_admin_analytics_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.admin_dashboard = AdminBillingDashboard(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for revenue analytics demonstration"""
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
        
        # Create sample customers with different subscription patterns
        customers = []
        for i in range(50):  # Create 50 customers for better analytics
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_admin_{i}',
                email=f'admin.user{i}@example.com',
                name=f'Admin User {i}',
                address={
                    'country': 'US' if i < 30 else 'CA' if i < 40 else 'UK',
                    'state': 'CA' if i < 20 else 'NY' if i < 30 else 'ON' if i < 40 else 'London',
                    'city': 'San Francisco' if i < 20 else 'New York' if i < 30 else 'Toronto' if i < 40 else 'London',
                    'zip': '94105' if i < 20 else '10001' if i < 30 else 'M5V' if i < 40 else 'SW1A'
                },
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=365 - (i * 7))  # Staggered creation dates
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with different patterns for analytics
        subscriptions = []
        billing_records = []
        
        # Budget tier subscriptions (20 customers)
        for i in range(20):
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id=f'sub_budget_admin_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 15 else 'annual',
                amount=15.00 if i < 15 else 12.50,  # Annual equivalent
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history
            for j in range(3):  # 3 months of billing history
                billing_record = BillingHistory(
                    customer_id=customers[i].id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-{j+1:03d}',
                    amount=15.00 if i < 15 else 150.00,
                    currency='USD',
                    status='paid',
                    description=f'Monthly subscription - {budget_tier.name}',
                    created_at=datetime.utcnow() - timedelta(days=90 - (j * 30)),
                    paid_at=datetime.utcnow() - timedelta(days=90 - (j * 30)),
                    stripe_invoice_id=f'in_{subscription.id}_admin_{j}'
                )
                billing_records.append(billing_record)
        
        # Mid-tier subscriptions (20 customers)
        for i in range(20, 40):
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id=f'sub_mid_tier_admin_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 30 else 'annual',
                amount=35.00 if i < 30 else 29.17,  # Annual equivalent
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history
            for j in range(3):  # 3 months of billing history
                billing_record = BillingHistory(
                    customer_id=customers[i].id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-{j+1:03d}',
                    amount=35.00 if i < 30 else 350.00,
                    currency='USD',
                    status='paid',
                    description=f'Monthly subscription - {mid_tier.name}',
                    created_at=datetime.utcnow() - timedelta(days=90 - (j * 30)),
                    paid_at=datetime.utcnow() - timedelta(days=90 - (j * 30)),
                    stripe_invoice_id=f'in_{subscription.id}_admin_{j}'
                )
                billing_records.append(billing_record)
        
        # Professional tier subscriptions (10 customers)
        for i in range(40, 50):
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=professional_tier.id,
                stripe_subscription_id=f'sub_professional_admin_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 45 else 'annual',
                amount=75.00 if i < 45 else 62.50,  # Annual equivalent
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history
            for j in range(3):  # 3 months of billing history
                billing_record = BillingHistory(
                    customer_id=customers[i].id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-{j+1:03d}',
                    amount=75.00 if i < 45 else 750.00,
                    currency='USD',
                    status='paid',
                    description=f'Monthly subscription - {professional_tier.name}',
                    created_at=datetime.utcnow() - timedelta(days=90 - (j * 30)),
                    paid_at=datetime.utcnow() - timedelta(days=90 - (j * 30)),
                    stripe_invoice_id=f'in_{subscription.id}_admin_{j}'
                )
                billing_records.append(billing_record)
        
        # Add some failed payments for realistic analytics
        for i in range(5):
            failed_billing = BillingHistory(
                customer_id=customers[i].id,
                subscription_id=subscriptions[i].id,
                invoice_number=f'INV-{subscriptions[i].id:04d}-FAILED',
                amount=15.00,
                currency='USD',
                status='failed',
                description=f'Failed payment - {budget_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=5),
                stripe_invoice_id=f'in_{subscriptions[i].id}_failed'
            )
            billing_records.append(failed_billing)
        
        # Add some canceled subscriptions
        for i in range(3):
            canceled_subscription = Subscription(
                customer_id=customers[i+45].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id=f'sub_canceled_admin_{i}',
                status='canceled',
                current_period_start=datetime.utcnow() - timedelta(days=60),
                current_period_end=datetime.utcnow() - timedelta(days=30),
                billing_cycle='monthly',
                amount=15.00,
                currency='USD',
                canceled_at=datetime.utcnow() - timedelta(days=30)
            )
            subscriptions.append(canceled_subscription)
        
        self.db_session.add_all(subscriptions)
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_revenue_analytics(self):
        """Demonstrate comprehensive revenue analytics"""
        print("\n=== Admin Revenue Analytics Demonstration ===")
        
        print(f"\n📊 Testing Revenue Analytics:")
        
        # Test 30-day revenue analytics
        print(f"\n1. 30-Day Revenue Analytics:")
        analytics_result = self.admin_dashboard.get_revenue_analytics(
            date_range='30d',
            granularity='day'
        )
        
        if analytics_result['success']:
            analytics = analytics_result['revenue_analytics']
            
            print(f"   ✅ Revenue analytics retrieved")
            print(f"   📅 Date Range: {analytics['date_range']['start_date']} to {analytics['date_range']['end_date']}")
            print(f"   📊 Period: {analytics['date_range']['period']}")
            print(f"   📈 Granularity: {analytics['date_range']['granularity']}")
            
            # Revenue metrics
            revenue_metrics = analytics['revenue_metrics']
            print(f"   💰 Revenue Metrics:")
            print(f"      Total Revenue: ${revenue_metrics['total_revenue']:.2f}")
            print(f"      MRR: ${revenue_metrics['mrr']:.2f}")
            print(f"      ARR: ${revenue_metrics['arr']:.2f}")
            print(f"      Avg Revenue per Customer: ${revenue_metrics['avg_revenue_per_customer']:.2f}")
            print(f"      Revenue Growth: {revenue_metrics['revenue_growth_percentage']:.1f}%")
            print(f"      Customer Count: {revenue_metrics['customer_count']}")
            print(f"      Transaction Count: {revenue_metrics['transaction_count']}")
            
            # Subscription metrics
            subscription_metrics = analytics['subscription_metrics']
            print(f"   📋 Subscription Metrics:")
            print(f"      Total Subscriptions: {subscription_metrics['total_subscriptions']}")
            print(f"      Active Subscriptions: {subscription_metrics['active_subscriptions']}")
            print(f"      New Subscriptions: {subscription_metrics['new_subscriptions']}")
            print(f"      Canceled Subscriptions: {subscription_metrics['canceled_subscriptions']}")
            print(f"      Churn Rate: {subscription_metrics['churn_rate_percentage']:.1f}%")
            print(f"      Subscription Growth: {subscription_metrics['subscription_growth_percentage']:.1f}%")
            print(f"      Health Score: {subscription_metrics['subscription_health_score']:.1f}/100")
            
            # Tier performance
            tier_performance = analytics['tier_performance']
            print(f"   🏆 Tier Performance:")
            for tier_type, performance in tier_performance.items():
                print(f"      {performance['tier_name']}:")
                print(f"         Total Subscriptions: {performance['total_subscriptions']}")
                print(f"         Active Subscriptions: {performance['active_subscriptions']}")
                print(f"         New Subscriptions: {performance['new_subscriptions']}")
                print(f"         Tier Revenue: ${performance['tier_revenue']:.2f}")
                print(f"         Avg Lifetime Value: ${performance['avg_lifetime_value']:.2f}")
                print(f"         Conversion Rate: {performance['conversion_rate']:.1f}%")
            
            # Payment metrics
            payment_metrics = analytics['payment_metrics']
            print(f"   💳 Payment Metrics:")
            print(f"      Total Payment Attempts: {payment_metrics['total_payment_attempts']}")
            print(f"      Successful Payments: {payment_metrics['successful_payments']}")
            print(f"      Failed Payments: {payment_metrics['failed_payments']}")
            print(f"      Success Rate: {payment_metrics['success_rate_percentage']:.1f}%")
            print(f"      Failure Rate: {payment_metrics['failure_rate_percentage']:.1f}%")
            print(f"      Avg Payment Amount: ${payment_metrics['avg_payment_amount']:.2f}")
            
            # Growth trends
            growth_trends = analytics['growth_trends']
            print(f"   📈 Growth Trends:")
            print(f"      Average Growth Rate: {growth_trends['average_growth_rate']:.1f}%")
            print(f"      Growth Periods: {len(growth_trends['months'])}")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
        
        # Test 90-day analytics with monthly granularity
        print(f"\n2. 90-Day Revenue Analytics (Monthly Granularity):")
        analytics_result = self.admin_dashboard.get_revenue_analytics(
            date_range='90d',
            granularity='month'
        )
        
        if analytics_result['success']:
            analytics = analytics_result['revenue_analytics']
            revenue_metrics = analytics['revenue_metrics']
            
            print(f"   ✅ 90-day analytics retrieved")
            print(f"   💰 Total Revenue (90d): ${revenue_metrics['total_revenue']:.2f}")
            print(f"   📊 Revenue by Period:")
            for period_data in revenue_metrics['revenue_by_period']:
                print(f"      {period_data['period']}: ${period_data['revenue']:.2f}")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
    
    def demonstrate_revenue_trending(self):
        """Demonstrate revenue trending analysis"""
        print("\n=== Revenue Trending Analysis ===")
        
        print(f"\n📈 Testing Revenue Trending:")
        
        # Test MRR trending
        print(f"\n1. MRR Trending (12 months):")
        mrr_result = self.admin_dashboard.get_revenue_trending(
            metric='mrr',
            period='12m'
        )
        
        if mrr_result['success']:
            trending = mrr_result['revenue_trending']
            
            print(f"   ✅ MRR trending retrieved")
            print(f"   📊 Metric: {trending['metric'].upper()}")
            print(f"   📅 Period: {trending['period']}")
            print(f"   📈 Trending Data:")
            
            for data_point in trending['trending_data'][:6]:  # Show first 6 data points
                print(f"      {data_point['period']}: ${data_point['mrr']:.2f}")
        else:
            print(f"   ❌ Failed: {mrr_result['error']}")
        
        # Test ARR trending
        print(f"\n2. ARR Trending (12 months):")
        arr_result = self.admin_dashboard.get_revenue_trending(
            metric='arr',
            period='12m'
        )
        
        if arr_result['success']:
            trending = arr_result['revenue_trending']
            
            print(f"   ✅ ARR trending retrieved")
            print(f"   📊 Metric: {trending['metric'].upper()}")
            print(f"   📈 Trending Data:")
            
            for data_point in trending['trending_data'][:6]:  # Show first 6 data points
                print(f"      {data_point['period']}: ${data_point['arr']:.2f}")
        else:
            print(f"   ❌ Failed: {arr_result['error']}")
        
        # Test subscription trending
        print(f"\n3. Subscription Count Trending (12 months):")
        subscription_result = self.admin_dashboard.get_revenue_trending(
            metric='subscriptions',
            period='12m'
        )
        
        if subscription_result['success']:
            trending = subscription_result['revenue_trending']
            
            print(f"   ✅ Subscription trending retrieved")
            print(f"   📊 Metric: {trending['metric'].upper()}")
            print(f"   📈 Trending Data:")
            
            for data_point in trending['trending_data'][:6]:  # Show first 6 data points
                print(f"      {data_point['period']}: {data_point['subscriptions']} subscriptions")
        else:
            print(f"   ❌ Failed: {subscription_result['error']}")
    
    def demonstrate_revenue_forecast(self):
        """Demonstrate revenue forecasting"""
        print("\n=== Revenue Forecasting ===")
        
        print(f"\n🔮 Testing Revenue Forecast:")
        
        # Test 6-month forecast
        print(f"\n1. 6-Month Revenue Forecast:")
        forecast_result = self.admin_dashboard.get_revenue_forecast(
            forecast_period='6m'
        )
        
        if forecast_result['success']:
            forecast = forecast_result['revenue_forecast']
            
            print(f"   ✅ Revenue forecast generated")
            print(f"   📅 Forecast Period: {forecast['forecast_period']}")
            print(f"   📊 Historical Data Points: {len(forecast['historical_data'])}")
            
            print(f"   📈 Forecast Data:")
            for data_point in forecast['forecast_data']:
                print(f"      {data_point['period']}: ${data_point['revenue']:.2f}")
                print(f"         Confidence: ${data_point['confidence_lower']:.2f} - ${data_point['confidence_upper']:.2f}")
            
            confidence = forecast['confidence_intervals']
            print(f"   🎯 Confidence Intervals:")
            print(f"      Average Forecast: ${confidence['average_forecast']:.2f}")
            print(f"      Standard Deviation: ${confidence['standard_deviation']:.2f}")
            print(f"      95% Confidence Lower: ${confidence['confidence_95_lower']:.2f}")
            print(f"      95% Confidence Upper: ${confidence['confidence_95_upper']:.2f}")
        else:
            print(f"   ❌ Failed: {forecast_result['error']}")
    
    def demonstrate_revenue_breakdown(self):
        """Demonstrate revenue breakdown analysis"""
        print("\n=== Revenue Breakdown Analysis ===")
        
        print(f"\n📊 Testing Revenue Breakdown:")
        
        # Test tier breakdown
        print(f"\n1. Revenue Breakdown by Tier:")
        tier_breakdown_result = self.admin_dashboard.get_revenue_breakdown(
            breakdown_type='tier',
            date_range='30d'
        )
        
        if tier_breakdown_result['success']:
            breakdown = tier_breakdown_result['revenue_breakdown']
            
            print(f"   ✅ Tier breakdown retrieved")
            print(f"   💰 Total Revenue: ${breakdown['breakdown_data']['total_revenue']:.2f}")
            print(f"   🏆 Tier Breakdown:")
            
            for tier_type, tier_data in breakdown['breakdown_data']['tier_breakdown'].items():
                print(f"      {tier_data['tier_name']}:")
                print(f"         Revenue: ${tier_data['revenue']:.2f} ({tier_data['percentage']:.1f}%)")
                print(f"         Subscriptions: {tier_data['subscription_count']}")
                print(f"         Avg Revenue per Subscription: ${tier_data['avg_revenue_per_subscription']:.2f}")
        else:
            print(f"   ❌ Failed: {tier_breakdown_result['error']}")
        
        # Test billing cycle breakdown
        print(f"\n2. Revenue Breakdown by Billing Cycle:")
        cycle_breakdown_result = self.admin_dashboard.get_revenue_breakdown(
            breakdown_type='billing_cycle',
            date_range='30d'
        )
        
        if cycle_breakdown_result['success']:
            breakdown = cycle_breakdown_result['revenue_breakdown']
            
            print(f"   ✅ Billing cycle breakdown retrieved")
            print(f"   💰 Total Revenue: ${breakdown['breakdown_data']['total_revenue']:.2f}")
            
            monthly = breakdown['breakdown_data']['monthly']
            annual = breakdown['breakdown_data']['annual']
            
            print(f"   📅 Monthly Billing:")
            print(f"      Revenue: ${monthly['revenue']:.2f} ({monthly['percentage']:.1f}%)")
            print(f"      Subscriptions: {monthly['subscription_count']}")
            
            print(f"   📅 Annual Billing:")
            print(f"      Revenue: ${annual['revenue']:.2f} ({annual['percentage']:.1f}%)")
            print(f"      Subscriptions: {annual['subscription_count']}")
        else:
            print(f"   ❌ Failed: {cycle_breakdown_result['error']}")
        
        # Test geographic breakdown
        print(f"\n3. Revenue Breakdown by Geographic Location:")
        geo_breakdown_result = self.admin_dashboard.get_revenue_breakdown(
            breakdown_type='geographic',
            date_range='30d'
        )
        
        if geo_breakdown_result['success']:
            breakdown = geo_breakdown_result['revenue_breakdown']
            
            print(f"   ✅ Geographic breakdown retrieved")
            print(f"   💰 Total Revenue: ${breakdown['breakdown_data']['total_revenue']:.2f}")
            print(f"   🌍 Geographic Breakdown:")
            
            for country, geo_data in breakdown['breakdown_data']['geographic_breakdown'].items():
                print(f"      {country}:")
                print(f"         Revenue: ${geo_data['revenue']:.2f} ({geo_data['percentage']:.1f}%)")
                print(f"         Customers: {geo_data['customer_count']}")
                print(f"         Subscriptions: {geo_data['subscription_count']}")
        else:
            print(f"   ❌ Failed: {geo_breakdown_result['error']}")
        
        # Test customer segment breakdown
        print(f"\n4. Revenue Breakdown by Customer Segment:")
        segment_breakdown_result = self.admin_dashboard.get_revenue_breakdown(
            breakdown_type='customer_segment',
            date_range='30d'
        )
        
        if segment_breakdown_result['success']:
            breakdown = segment_breakdown_result['revenue_breakdown']
            
            print(f"   ✅ Customer segment breakdown retrieved")
            print(f"   💰 Total Revenue: ${breakdown['breakdown_data']['total_revenue']:.2f}")
            print(f"   👥 Customer Segment Breakdown:")
            
            for segment, segment_data in breakdown['breakdown_data']['segment_breakdown'].items():
                print(f"      {segment_data['segment_name']}:")
                print(f"         Revenue: ${segment_data['revenue']:.2f} ({segment_data['percentage']:.1f}%)")
                print(f"         Customers: {segment_data['customer_count']}")
                print(f"         Subscriptions: {segment_data['subscription_count']}")
        else:
            print(f"   ❌ Failed: {segment_breakdown_result['error']}")
    
    def run_all_revenue_analytics_demonstrations(self):
        """Run all revenue analytics demonstrations"""
        print("🚀 MINGUS Admin Revenue Analytics Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_revenue_analytics()
            self.demonstrate_revenue_trending()
            self.demonstrate_revenue_forecast()
            self.demonstrate_revenue_breakdown()
            
            print("\n✅ All revenue analytics demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = AdminRevenueAnalyticsExample()
    example.run_all_revenue_analytics_demonstrations()

if __name__ == "__main__":
    main() 