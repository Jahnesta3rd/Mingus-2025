"""
Admin Customer Lifetime Value and Tier Distribution Example for MINGUS
Demonstrates CLV metrics by tier and tier distribution/movement analysis for administrators
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

class AdminCLVTierDistributionExample:
    """Example demonstrating admin customer lifetime value and tier distribution analysis"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_clv_tier_distribution_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.admin_dashboard = AdminBillingDashboard(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for CLV and tier distribution demonstration"""
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
        
        # Create sample customers with varied characteristics
        customers = []
        for i in range(500):  # Create 500 customers for comprehensive analysis
            # Vary customer creation dates for different segments
            if i < 100:  # New customers (last 30 days)
                created_date = datetime.utcnow() - timedelta(days=15 + (i % 15))
            elif i < 250:  # Returning customers (30-90 days)
                created_date = datetime.utcnow() - timedelta(days=45 + (i % 45))
            else:  # Loyal customers (90+ days)
                created_date = datetime.utcnow() - timedelta(days=120 + (i % 240))
            
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_clv_{i}',
                email=f'clv.user{i}@example.com',
                name=f'CLV User {i}',
                address={
                    'country': 'US' if i < 300 else 'CA' if i < 400 else 'UK',
                    'state': 'CA' if i < 150 else 'NY' if i < 300 else 'ON' if i < 400 else 'London',
                    'city': 'San Francisco' if i < 150 else 'New York' if i < 300 else 'Toronto' if i < 400 else 'London',
                    'zip': '94105' if i < 150 else '10001' if i < 300 else 'M5V' if i < 400 else 'SW1A'
                },
                phone='+1-555-0123',
                created_at=created_date
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with varied distribution and CLV characteristics
        subscriptions = []
        billing_records = []
        
        # Budget tier customers (40% - 200 customers)
        for i in range(200):
            customer = customers[i]
            subscription = Subscription(
                customer_id=customer.id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id=f'sub_budget_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 150 else 'annual',
                amount=15.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history for CLV calculation
            months_active = (datetime.utcnow() - customer.created_at).days / 30.44
            for month in range(int(months_active)):
                billing_record = BillingHistory(
                    customer_id=customer.id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-{month+1:03d}',
                    amount=15.00,
                    currency='USD',
                    status='paid',
                    description=f'Monthly payment - Budget tier',
                    created_at=customer.created_at + timedelta(days=month * 30),
                    paid_at=customer.created_at + timedelta(days=month * 30),
                    stripe_invoice_id=f'in_{subscription.id}_month_{month+1}'
                )
                billing_records.append(billing_record)
        
        # Mid-tier customers (35% - 175 customers)
        for i in range(175):
            customer = customers[i + 200]
            subscription = Subscription(
                customer_id=customer.id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id=f'sub_mid_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 120 else 'annual',
                amount=35.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history for CLV calculation
            months_active = (datetime.utcnow() - customer.created_at).days / 30.44
            for month in range(int(months_active)):
                billing_record = BillingHistory(
                    customer_id=customer.id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-{month+1:03d}',
                    amount=35.00,
                    currency='USD',
                    status='paid',
                    description=f'Monthly payment - Mid-tier',
                    created_at=customer.created_at + timedelta(days=month * 30),
                    paid_at=customer.created_at + timedelta(days=month * 30),
                    stripe_invoice_id=f'in_{subscription.id}_month_{month+1}'
                )
                billing_records.append(billing_record)
        
        # Professional tier customers (25% - 125 customers)
        for i in range(125):
            customer = customers[i + 375]
            subscription = Subscription(
                customer_id=customer.id,
                pricing_tier_id=professional_tier.id,
                stripe_subscription_id=f'sub_pro_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 80 else 'annual',
                amount=75.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history for CLV calculation
            months_active = (datetime.utcnow() - customer.created_at).days / 30.44
            for month in range(int(months_active)):
                billing_record = BillingHistory(
                    customer_id=customer.id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-{month+1:03d}',
                    amount=75.00,
                    currency='USD',
                    status='paid',
                    description=f'Monthly payment - Professional tier',
                    created_at=customer.created_at + timedelta(days=month * 30),
                    paid_at=customer.created_at + timedelta(days=month * 30),
                    stripe_invoice_id=f'in_{subscription.id}_month_{month+1}'
                )
                billing_records.append(billing_record)
        
        self.db_session.add_all(subscriptions)
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_customer_lifetime_value_metrics(self):
        """Demonstrate comprehensive customer lifetime value analysis"""
        print("\n=== Customer Lifetime Value Metrics Analysis ===")
        
        print(f"\n📊 Testing Customer Lifetime Value Metrics:")
        
        # Test tier-based CLV analysis
        print(f"\n1. Customer Lifetime Value by Tier (30 days):")
        clv_result = self.admin_dashboard.get_customer_lifetime_value_metrics(
            date_range='30d',
            analysis_type='by_tier'
        )
        
        if clv_result['success']:
            clv = clv_result['customer_lifetime_value_analysis']
            
            print(f"   ✅ Tier-based CLV analysis retrieved")
            print(f"   📅 Date Range: {clv['date_range']['start_date']} to {clv['date_range']['end_date']}")
            print(f"   📊 Period: {clv['date_range']['period']}")
            print(f"   🔍 Analysis Type: {clv['analysis_type']}")
            
            # Display CLV data
            clv_data = clv['clv_data']
            print(f"   💰 Customer Lifetime Value by Tier:")
            for tier_type, tier_data in clv_data.items():
                print(f"      {tier_data['tier_name']}:")
                print(f"         Customer Count: {tier_data['customer_count']}")
                print(f"         Average CLV: ${tier_data['avg_clv']:.2f}")
                print(f"         Total CLV: ${tier_data['total_clv']:.2f}")
                print(f"         Average Lifetime: {tier_data['avg_lifetime_months']:.1f} months")
                print(f"         Average Monthly Revenue: ${tier_data['avg_monthly_revenue']:.2f}")
                
                # Display CLV distribution
                clv_dist = tier_data['clv_distribution']
                print(f"         CLV Distribution:")
                print(f"            Low Value: {clv_dist['low_value']} customers")
                print(f"            Medium Value: {clv_dist['medium_value']} customers")
                print(f"            High Value: {clv_dist['high_value']} customers")
            
            # Display CLV summary
            clv_summary = clv['clv_summary']
            print(f"   📈 CLV Summary:")
            print(f"      Total Customers: {clv_summary['total_customers']}")
            print(f"      Total CLV: ${clv_summary['total_clv']:.2f}")
            print(f"      Average CLV: ${clv_summary['avg_clv']:.2f}")
            if clv_summary['highest_clv_tier']:
                print(f"      Highest CLV Tier: {clv_summary['highest_clv_tier'][0]} (${clv_summary['highest_clv_tier'][1]:.2f})")
            if clv_summary['lowest_clv_tier']:
                print(f"      Lowest CLV Tier: {clv_summary['lowest_clv_tier'][0]} (${clv_summary['lowest_clv_tier'][1]:.2f})")
            print(f"      CLV Range: ${clv_summary['clv_range']:.2f}")
            
            # Display CLV trends
            clv_trends = clv['clv_trends']
            print(f"   📊 CLV Trends:")
            print(f"      Overall Trend: {clv_trends['overall_trend']}")
            print(f"      Growth Rate: {clv_trends['growth_rate']:.1f}%")
            print(f"      Tier Performance:")
            for tier_type, performance in clv_trends['tier_performance'].items():
                print(f"         {tier_type}: {performance['performance']} (${performance['avg_clv']:.2f}, {performance['customer_count']} customers)")
            
            # Display optimization recommendations
            recommendations = clv['optimization_recommendations']
            print(f"   💡 CLV Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {clv_result['error']}")
        
        # Test customer segment CLV analysis
        print(f"\n2. Customer Lifetime Value by Customer Segment:")
        clv_result = self.admin_dashboard.get_customer_lifetime_value_metrics(
            date_range='30d',
            analysis_type='by_customer_segment'
        )
        
        if clv_result['success']:
            clv = clv_result['customer_lifetime_value_analysis']
            clv_data = clv['clv_data']
            
            print(f"   ✅ Customer segment CLV analysis retrieved")
            print(f"   👥 Customer Lifetime Value by Segment:")
            for segment_key, segment_data in clv_data.items():
                print(f"      {segment_data['segment_name']}:")
                print(f"         Customer Count: {segment_data['customer_count']}")
                print(f"         Average CLV: ${segment_data['avg_clv']:.2f}")
                print(f"         Total CLV: ${segment_data['total_clv']:.2f}")
                print(f"         Average Lifetime: {segment_data['avg_lifetime_months']:.1f} months")
        else:
            print(f"   ❌ Failed: {clv_result['error']}")
        
        # Test geographic CLV analysis
        print(f"\n3. Customer Lifetime Value by Geographic Location:")
        clv_result = self.admin_dashboard.get_customer_lifetime_value_metrics(
            date_range='30d',
            analysis_type='by_geographic'
        )
        
        if clv_result['success']:
            clv = clv_result['customer_lifetime_value_analysis']
            clv_data = clv['clv_data']
            
            print(f"   ✅ Geographic CLV analysis retrieved")
            print(f"   🌍 Customer Lifetime Value by Geography:")
            for country, geo_data in clv_data.items():
                print(f"      {country}:")
                print(f"         Customer Count: {geo_data['customer_count']}")
                print(f"         Total Revenue: ${geo_data['total_revenue']:.2f}")
                print(f"         Average CLV: ${geo_data['avg_clv']:.2f}")
        else:
            print(f"   ❌ Failed: {clv_result['error']}")
        
        # Test billing cycle CLV analysis
        print(f"\n4. Customer Lifetime Value by Billing Cycle:")
        clv_result = self.admin_dashboard.get_customer_lifetime_value_metrics(
            date_range='30d',
            analysis_type='by_billing_cycle'
        )
        
        if clv_result['success']:
            clv = clv_result['customer_lifetime_value_analysis']
            clv_data = clv['clv_data']
            
            print(f"   ✅ Billing cycle CLV analysis retrieved")
            print(f"   💳 Customer Lifetime Value by Billing Cycle:")
            for cycle, cycle_data in clv_data.items():
                print(f"      {cycle_data['billing_cycle']}:")
                print(f"         Customer Count: {cycle_data['customer_count']}")
                print(f"         Average CLV: ${cycle_data['avg_clv']:.2f}")
                print(f"         Total CLV: ${cycle_data['total_clv']:.2f}")
                print(f"         Average Monthly Revenue: ${cycle_data['avg_monthly_revenue']:.2f}")
        else:
            print(f"   ❌ Failed: {clv_result['error']}")
    
    def demonstrate_tier_distribution_analysis(self):
        """Demonstrate comprehensive tier distribution analysis"""
        print("\n=== Tier Distribution Analysis ===")
        
        print(f"\n📊 Testing Tier Distribution Analysis:")
        
        # Test tier distribution analysis
        print(f"\n1. Tier Distribution Analysis (30 days):")
        distribution_result = self.admin_dashboard.get_tier_distribution_analysis(
            date_range='30d'
        )
        
        if distribution_result['success']:
            distribution = distribution_result['tier_distribution_analysis']
            
            print(f"   ✅ Tier distribution analysis retrieved")
            print(f"   📅 Date Range: {distribution['date_range']['start_date']} to {distribution['date_range']['end_date']}")
            print(f"   📊 Period: {distribution['date_range']['period']}")
            
            # Display distribution data
            distribution_data = distribution['distribution_data']
            print(f"   📊 Tier Distribution:")
            for tier_type, tier_data in distribution_data.items():
                if tier_type != 'total':
                    print(f"      {tier_data['tier_name']}:")
                    print(f"         Customer Count: {tier_data['customer_count']}")
                    print(f"         Percentage: {tier_data['percentage']:.1f}%")
                    print(f"         Monthly Revenue: ${tier_data['monthly_revenue']:.2f}")
                    print(f"         Yearly Revenue: ${tier_data['yearly_revenue']:.2f}")
            
            # Display total metrics
            total_data = distribution_data['total']
            print(f"   📈 Total Metrics:")
            print(f"      Total Customers: {total_data['total_customers']}")
            print(f"      Total Monthly Revenue: ${total_data['total_monthly_revenue']:.2f}")
            print(f"      Total Yearly Revenue: ${total_data['total_yearly_revenue']:.2f}")
            
            # Display distribution summary
            distribution_summary = distribution['distribution_summary']
            print(f"   📊 Distribution Summary:")
            print(f"      Total Customers: {distribution_summary['total_customers']}")
            print(f"      Total Monthly Revenue: ${distribution_summary['total_monthly_revenue']:.2f}")
            print(f"      Dominant Tier: {distribution_summary['dominant_tier']}")
            print(f"      Dominant Tier Percentage: {distribution_summary['dominant_tier_percentage']:.1f}%")
            print(f"      Distribution Evenness: {distribution_summary['distribution_evenness']:.2f}")
            print(f"      Tier Count: {distribution_summary['tier_count']}")
            
            # Display tier movement analysis
            movement_analysis = distribution['tier_movement_analysis']
            print(f"   🔄 Tier Movement Analysis:")
            
            # Upgrades
            upgrades = movement_analysis['upgrades']
            print(f"      Upgrades:")
            for upgrade_path, count in upgrades.items():
                print(f"         {upgrade_path}: {count} customers")
            
            # Downgrades
            downgrades = movement_analysis['downgrades']
            print(f"      Downgrades:")
            for downgrade_path, count in downgrades.items():
                print(f"         {downgrade_path}: {count} customers")
            
            # Cancellations
            cancellations = movement_analysis['cancellations']
            print(f"      Cancellations:")
            for tier, count in cancellations.items():
                print(f"         {tier}: {count} customers")
            
            # New subscriptions
            new_subscriptions = movement_analysis['new_subscriptions']
            print(f"      New Subscriptions:")
            for tier, count in new_subscriptions.items():
                print(f"         {tier}: {count} customers")
            
            # Movement summary
            movement_summary = movement_analysis['summary']
            print(f"      Movement Summary:")
            print(f"         Total Upgrades: {movement_summary['total_upgrades']}")
            print(f"         Total Downgrades: {movement_summary['total_downgrades']}")
            print(f"         Total Cancellations: {movement_summary['total_cancellations']}")
            print(f"         Total New Subscriptions: {movement_summary['total_new_subscriptions']}")
            print(f"         Net Movement: {movement_summary['net_movement']}")
            print(f"         Upgrade Rate: {movement_summary['upgrade_rate']:.1f}%")
            
            # Display optimization recommendations
            recommendations = distribution['optimization_recommendations']
            print(f"   💡 Distribution Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {distribution_result['error']}")
    
    def demonstrate_tier_movement_trends(self):
        """Demonstrate tier movement trends analysis"""
        print("\n=== Tier Movement Trends Analysis ===")
        
        print(f"\n📊 Testing Tier Movement Trends:")
        
        # Test tier movement trends
        print(f"\n1. Tier Movement Trends (12 months):")
        trends_result = self.admin_dashboard.get_tier_movement_trends(
            period='12m'
        )
        
        if trends_result['success']:
            trends = trends_result['tier_movement_trends']
            
            print(f"   ✅ Tier movement trends retrieved")
            print(f"   📅 Period: {trends['period']}")
            print(f"   📊 Start Date: {trends['start_date']}")
            print(f"   📊 End Date: {trends['end_date']}")
            
            # Display trend analysis
            trend_analysis = trends['trend_analysis']
            print(f"   📈 Movement Trend Analysis:")
            print(f"      Average Net Movement: {trend_analysis['avg_net_movement']:.1f}")
            print(f"      Average Movement Rate: {trend_analysis['avg_movement_rate']:.1f}%")
            print(f"      Trend Direction: {trend_analysis['trend_direction']}")
            print(f"      Best Period: {trend_analysis['best_period']}")
            print(f"      Worst Period: {trend_analysis['worst_period']}")
            
            # Display monthly movements
            print(f"   📅 Monthly Movement Summary:")
            for monthly_movement in trends['monthly_movements'][:6]:  # Show first 6 months
                movement_summary = monthly_movement['movement_summary']
                print(f"      {monthly_movement['period']}:")
                print(f"         Total Movements: {movement_summary['total_movements']}")
                print(f"         Net Movement: {movement_summary['net_movement']}")
                print(f"         Movement Rate: {movement_summary['movement_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {trends_result['error']}")
    
    def demonstrate_tier_migration_analysis(self):
        """Demonstrate tier migration analysis"""
        print("\n=== Tier Migration Analysis ===")
        
        print(f"\n📊 Testing Tier Migration Analysis:")
        
        # Test tier migration analysis
        print(f"\n1. Tier Migration Analysis (30 days):")
        migration_result = self.admin_dashboard.get_tier_migration_analysis(
            date_range='30d'
        )
        
        if migration_result['success']:
            migration = migration_result['tier_migration_analysis']
            
            print(f"   ✅ Tier migration analysis retrieved")
            print(f"   📅 Date Range: {migration['date_range']['start_date']} to {migration['date_range']['end_date']}")
            print(f"   📊 Period: {migration['date_range']['period']}")
            
            # Display migration analysis
            migration_analysis = migration['migration_analysis']
            migration_patterns = migration_analysis['migration_patterns']
            print(f"   🔄 Migration Patterns:")
            for pattern, data in migration_patterns.items():
                print(f"      {pattern}:")
                print(f"         Count: {data['count']}")
                print(f"         Percentage: {data['percentage']:.1f}%")
                print(f"         Average Time: {data['avg_time_to_upgrade'] if 'upgrade' in pattern else data['avg_time_to_downgrade']:.1f} months")
                print(f"         Common Reasons: {', '.join(data['common_reasons'])}")
            
            # Display migration summary
            migration_summary = migration_analysis['migration_summary']
            print(f"   📊 Migration Summary:")
            print(f"      Total Migrations: {migration_summary['total_migrations']}")
            print(f"      Upgrades: {migration_summary['upgrades']}")
            print(f"      Downgrades: {migration_summary['downgrades']}")
            print(f"      Upgrade Rate: {migration_summary['upgrade_rate']:.1f}%")
            print(f"      Downgrade Rate: {migration_summary['downgrade_rate']:.1f}%")
            print(f"      Net Upgrade Rate: {migration_summary['net_upgrade_rate']:.1f}%")
            
            # Display migration matrix
            migration_matrix = migration['migration_matrix']
            print(f"   📋 Migration Matrix:")
            print(f"      From/To    Budget  Mid-Tier  Professional")
            print(f"      Budget     {migration_matrix['budget']['budget']:>6}  {migration_matrix['budget']['mid_tier']:>8}  {migration_matrix['budget']['professional']:>12}")
            print(f"      Mid-Tier   {migration_matrix['mid_tier']['budget']:>6}  {migration_matrix['mid_tier']['mid_tier']:>8}  {migration_matrix['mid_tier']['professional']:>12}")
            print(f"      Professional {migration_matrix['professional']['budget']:>3}  {migration_matrix['professional']['mid_tier']:>8}  {migration_matrix['professional']['professional']:>12}")
            
            # Display migration reasons
            migration_reasons = migration['migration_reasons']
            print(f"   🔍 Migration Reasons:")
            for reason in migration_reasons:
                print(f"      {reason['reason']}:")
                print(f"         Count: {reason['count']}")
                print(f"         Percentage: {reason['percentage']:.1f}%")
                print(f"         Migration Type: {reason['migration_type']}")
                print(f"         Recommendation: {reason['recommendation']}")
            
            # Display optimization recommendations
            recommendations = migration['optimization_recommendations']
            print(f"   💡 Migration Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {migration_result['error']}")
    
    def demonstrate_tier_value_optimization(self):
        """Demonstrate tier value optimization analysis"""
        print("\n=== Tier Value Optimization Analysis ===")
        
        print(f"\n📊 Testing Tier Value Optimization:")
        
        # Test tier value optimization
        print(f"\n1. Tier Value Optimization (30 days):")
        optimization_result = self.admin_dashboard.get_tier_value_optimization(
            date_range='30d'
        )
        
        if optimization_result['success']:
            optimization = optimization_result['tier_value_optimization']
            
            print(f"   ✅ Tier value optimization retrieved")
            print(f"   📅 Date Range: {optimization['date_range']['start_date']} to {optimization['date_range']['end_date']}")
            print(f"   📊 Period: {optimization['date_range']['period']}")
            
            # Display optimization data
            optimization_data = optimization['optimization_data']
            tier_performance = optimization_data['tier_performance']
            print(f"   📊 Tier Performance:")
            for tier_type, performance in tier_performance.items():
                print(f"      {tier_type.title()}:")
                print(f"         Customer Count: {performance['customer_count']}")
                print(f"         Average CLV: ${performance['avg_clv']:.2f}")
                print(f"         Monthly Revenue: ${performance['monthly_revenue']:.2f}")
                print(f"         Revenue per Customer: ${performance['revenue_per_customer']:.2f}")
                print(f"         CLV to Revenue Ratio: {performance['clv_to_revenue_ratio']:.2f}")
                print(f"         Performance Score: {performance['performance_score']:.1f}/100")
            
            # Display value gaps
            value_gaps = optimization_data['value_gaps']
            print(f"   🔍 Value Gaps:")
            for tier_type, gap_data in value_gaps.items():
                print(f"      {tier_type.title()}:")
                print(f"         Gap Percentage: {gap_data['gap_percentage']:.1f}%")
                print(f"         Potential Value: ${gap_data['potential_value']:.2f}")
                print(f"         Recommendation: {gap_data['recommendation']}")
            
            # Display upgrade opportunities
            upgrade_opportunities = optimization['upgrade_opportunities']
            print(f"   🎯 Upgrade Opportunities:")
            for opportunity in upgrade_opportunities:
                print(f"      Customer {opportunity['customer_id']}:")
                print(f"         Current Tier: {opportunity['current_tier']}")
                print(f"         Recommended Tier: {opportunity['recommended_tier']}")
                print(f"         Reason: {opportunity['reason']}")
                print(f"         Usage Percentage: {opportunity['usage_percentage']}%")
                print(f"         Potential Value: ${opportunity['potential_value']}")
                print(f"         Confidence Score: {opportunity['confidence_score']}%")
            
            # Display retention strategies
            retention_strategies = optimization['retention_strategies']
            print(f"   🛡️ Retention Strategies:")
            for strategy in retention_strategies:
                print(f"      {strategy['title']}:")
                print(f"         Tier: {strategy['tier']}")
                print(f"         Strategy Type: {strategy['strategy_type']}")
                print(f"         Description: {strategy['description']}")
                print(f"         Actions:")
                for action in strategy['actions']:
                    print(f"            - {action}")
            
            # Display optimization recommendations
            recommendations = optimization['optimization_recommendations']
            print(f"   💡 Value Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {optimization_result['error']}")
    
    def run_all_clv_tier_distribution_demonstrations(self):
        """Run all customer lifetime value and tier distribution demonstrations"""
        print("🚀 MINGUS Admin Customer Lifetime Value and Tier Distribution Demonstration")
        print("=" * 80)
        
        try:
            self.demonstrate_customer_lifetime_value_metrics()
            self.demonstrate_tier_distribution_analysis()
            self.demonstrate_tier_movement_trends()
            self.demonstrate_tier_migration_analysis()
            self.demonstrate_tier_value_optimization()
            
            print("\n✅ All customer lifetime value and tier distribution demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = AdminCLVTierDistributionExample()
    example.run_all_clv_tier_distribution_demonstrations()

if __name__ == "__main__":
    main() 