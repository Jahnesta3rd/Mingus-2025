"""
Admin Churn Analysis Example for MINGUS
Demonstrates churn analysis and prevention features for administrators
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

class AdminChurnAnalysisExample:
    """Example demonstrating admin churn analysis and prevention"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_churn_analysis_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.admin_dashboard = AdminBillingDashboard(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for churn analysis demonstration"""
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
        
        # Create sample customers with churn patterns
        customers = []
        for i in range(200):  # Create 200 customers for better churn analysis
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_churn_{i}',
                email=f'churn.user{i}@example.com',
                name=f'Churn User {i}',
                address={
                    'country': 'US' if i < 120 else 'CA' if i < 160 else 'UK',
                    'state': 'CA' if i < 60 else 'NY' if i < 120 else 'ON' if i < 160 else 'London',
                    'city': 'San Francisco' if i < 60 else 'New York' if i < 120 else 'Toronto' if i < 160 else 'London',
                    'zip': '94105' if i < 60 else '10001' if i < 120 else 'M5V' if i < 160 else 'SW1A'
                },
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=365 - (i * 2))  # Staggered creation dates
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with various churn scenarios
        subscriptions = []
        billing_records = []
        
        # Active subscriptions (150 customers)
        for i in range(150):
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id if i < 80 else mid_tier.id if i < 130 else professional_tier.id,
                stripe_subscription_id=f'sub_active_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 100 else 'annual',
                amount=15.00 if i < 80 else 35.00 if i < 130 else 75.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history for active subscriptions
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
                stripe_invoice_id=f'in_{subscription.id}_active'
            )
            billing_records.append(billing_record)
        
        # Voluntarily canceled subscriptions (30 customers)
        for i in range(150, 180):
            # Create different churn reasons
            churn_reasons = ['pricing', 'features', 'competitor', 'customer_request']
            churn_reason = churn_reasons[(i - 150) % len(churn_reasons)]
            
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id if i < 165 else mid_tier.id,
                stripe_subscription_id=f'sub_voluntary_{i}',
                status='canceled',
                current_period_start=datetime.utcnow() - timedelta(days=60),
                current_period_end=datetime.utcnow() - timedelta(days=30),
                billing_cycle='monthly',
                amount=15.00 if i < 165 else 35.00,
                currency='USD',
                canceled_at=datetime.utcnow() - timedelta(days=30),
                cancel_reason=churn_reason
            )
            subscriptions.append(subscription)
            
            # Create billing history for canceled subscriptions
            billing_record = BillingHistory(
                customer_id=customers[i].id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-001',
                amount=subscription.amount,
                currency='USD',
                status='paid',
                description=f'Final payment - {subscription.pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=60),
                paid_at=datetime.utcnow() - timedelta(days=60),
                stripe_invoice_id=f'in_{subscription.id}_voluntary'
            )
            billing_records.append(billing_record)
        
        # Involuntarily canceled subscriptions (20 customers)
        for i in range(180, 200):
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id if i < 190 else mid_tier.id,
                stripe_subscription_id=f'sub_involuntary_{i}',
                status='canceled',
                current_period_start=datetime.utcnow() - timedelta(days=45),
                current_period_end=datetime.utcnow() - timedelta(days=15),
                billing_cycle='monthly',
                amount=15.00 if i < 190 else 35.00,
                currency='USD',
                canceled_at=datetime.utcnow() - timedelta(days=15),
                cancel_reason='payment_failure'
            )
            subscriptions.append(subscription)
            
            # Create failed billing history
            billing_record = BillingHistory(
                customer_id=customers[i].id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-FAILED',
                amount=subscription.amount,
                currency='USD',
                status='failed',
                description=f'Failed payment - {subscription.pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=20),
                stripe_invoice_id=f'in_{subscription.id}_failed'
            )
            billing_records.append(billing_record)
        
        # Past due subscriptions (for high-risk analysis)
        for i in range(10):
            subscription = Subscription(
                customer_id=customers[i + 100].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id=f'sub_past_due_{i}',
                status='past_due',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow(),
                billing_cycle='monthly',
                amount=15.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create failed billing history
            billing_record = BillingHistory(
                customer_id=customers[i + 100].id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-PAST_DUE',
                amount=subscription.amount,
                currency='USD',
                status='failed',
                description=f'Past due payment - {subscription.pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=5),
                stripe_invoice_id=f'in_{subscription.id}_past_due'
            )
            billing_records.append(billing_record)
        
        self.db_session.add_all(subscriptions)
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_churn_analysis(self):
        """Demonstrate comprehensive churn analysis"""
        print("\n=== Churn Analysis Demonstration ===")
        
        print(f"\n📊 Testing Churn Analysis:")
        
        # Test overall churn analysis
        print(f"\n1. Overall Churn Analysis (30 days):")
        churn_result = self.admin_dashboard.get_churn_analysis(
            date_range='30d',
            churn_type='overall'
        )
        
        if churn_result['success']:
            churn = churn_result['churn_analysis']
            
            print(f"   ✅ Overall churn analysis retrieved")
            print(f"   📅 Date Range: {churn['date_range']['start_date']} to {churn['date_range']['end_date']}")
            print(f"   📊 Period: {churn['date_range']['period']}")
            print(f"   🎯 Overall Churn Rate: {churn['churn_rate']:.1f}%")
            
            # Display churn data
            churn_data = churn['churn_data']
            print(f"   📈 Churn Breakdown:")
            print(f"      Total Churned: {churn_data['total_churned']}")
            print(f"      Voluntary Churn: {churn_data['voluntary_churn']}")
            print(f"      Involuntary Churn: {churn_data['involuntary_churn']}")
            print(f"      Total Active Start: {churn_data['total_active_start']}")
            print(f"      New Subscriptions: {churn_data['new_subscriptions']}")
            print(f"      Voluntary Rate: {churn_data['voluntary_rate']:.1f}%")
            print(f"      Involuntary Rate: {churn_data['involuntary_rate']:.1f}%")
            
            # Display churn impact
            churn_impact = churn['churn_impact']
            print(f"   💰 Churn Impact:")
            print(f"      Revenue Impact: ${churn_impact['revenue_impact']:,.2f}")
            print(f"      LTV Impact: ${churn_impact['ltv_impact']:,.2f}")
            print(f"      Acquisition Impact: ${churn_impact['acquisition_impact']:,.2f}")
            print(f"      Total Impact: ${churn_impact['total_impact']:,.2f}")
            print(f"      Avg Revenue per Customer: ${churn_impact['avg_revenue_per_customer']:.2f}")
            print(f"      Customers Lost: {churn_impact['customers_lost']}")
            
            # Display churn reasons
            churn_reasons = churn['churn_reasons']
            print(f"   🔍 Churn Reasons:")
            for reason in churn_reasons:
                print(f"      {reason['reason']}:")
                print(f"         Count: {reason['count']}")
                print(f"         Percentage: {reason['percentage']:.1f}%")
                print(f"         Recommendation: {reason['recommendation']}")
            
            # Display prevention recommendations
            recommendations = churn['prevention_recommendations']
            print(f"   💡 Prevention Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {churn_result['error']}")
        
        # Test voluntary churn analysis
        print(f"\n2. Voluntary Churn Analysis (30 days):")
        churn_result = self.admin_dashboard.get_churn_analysis(
            date_range='30d',
            churn_type='voluntary'
        )
        
        if churn_result['success']:
            churn = churn_result['churn_analysis']
            churn_data = churn['churn_data']
            
            print(f"   ✅ Voluntary churn analysis retrieved")
            print(f"   🎯 Voluntary Churn Rate: {churn['churn_rate']:.1f}%")
            print(f"   📊 Voluntary Cancellations: {churn_data['voluntary_cancellations']}")
            print(f"   📈 Churn Reasons:")
            for reason in churn_data['churn_reasons']:
                print(f"      {reason['reason']}: {reason['count']} customers")
        else:
            print(f"   ❌ Failed: {churn_result['error']}")
        
        # Test involuntary churn analysis
        print(f"\n3. Involuntary Churn Analysis (30 days):")
        churn_result = self.admin_dashboard.get_churn_analysis(
            date_range='30d',
            churn_type='involuntary'
        )
        
        if churn_result['success']:
            churn = churn_result['churn_analysis']
            churn_data = churn['churn_data']
            
            print(f"   ✅ Involuntary churn analysis retrieved")
            print(f"   🎯 Involuntary Churn Rate: {churn['churn_rate']:.1f}%")
            print(f"   📊 Payment Failures: {churn_data['payment_failures']}")
            print(f"   📊 Payment Cancellations: {churn_data['payment_cancellations']}")
            print(f"   📈 Failure Reasons:")
            for reason in churn_data['failure_reasons']:
                print(f"      {reason['reason']}: {reason['count']} customers")
        else:
            print(f"   ❌ Failed: {churn_result['error']}")
    
    def demonstrate_churn_prediction(self):
        """Demonstrate churn prediction analysis"""
        print("\n=== Churn Prediction Analysis ===")
        
        print(f"\n📊 Testing Churn Prediction:")
        
        # Test 30-day churn prediction
        print(f"\n1. 30-Day Churn Prediction:")
        prediction_result = self.admin_dashboard.get_churn_prediction(
            prediction_horizon='30d'
        )
        
        if prediction_result['success']:
            prediction = prediction_result['churn_prediction']
            prediction_data = prediction['prediction_data']
            
            print(f"   ✅ Churn prediction retrieved")
            print(f"   📅 Prediction Horizon: {prediction_data['prediction_horizon']}")
            print(f"   📊 Current Active Subscriptions: {prediction_data['current_active_subscriptions']}")
            print(f"   📈 Historical Churn Rate: {prediction_data['historical_churn_rate']:.1f}%")
            print(f"   🎯 Predicted Churn: {prediction_data['predicted_churn']} customers")
            print(f"   📊 Predicted Churn Rate: {prediction_data['predicted_churn_rate']:.1f}%")
            print(f"   🎯 Confidence Level: {prediction_data['confidence_level']}")
            
            # Display high-risk customers
            high_risk_customers = prediction['high_risk_customers']
            print(f"   ⚠️ High-Risk Customers:")
            for customer in high_risk_customers[:5]:  # Show first 5
                print(f"      Customer ID: {customer['customer_id']}")
                print(f"         Risk Factor: {customer['risk_factor']}")
                print(f"         Risk Score: {customer['risk_score']}")
                print(f"         Recommendation: {customer['recommendation']}")
            
            # Display risk factors
            risk_factors = prediction['risk_factors']
            print(f"   🔍 Risk Factors:")
            for factor in risk_factors:
                print(f"      {factor['factor']}:")
                print(f"         Risk Level: {factor['risk_level']}")
                print(f"         Count: {factor['count']}")
                print(f"         Impact: {factor['impact']}")
                print(f"         Mitigation: {factor['mitigation']}")
            
            # Display intervention strategies
            strategies = prediction['intervention_strategies']
            print(f"   🛡️ Intervention Strategies:")
            for strategy in strategies:
                print(f"      {strategy['type'].upper()}: {strategy['title']}")
                print(f"         Description: {strategy['description']}")
                print(f"         Actions:")
                for action in strategy['actions']:
                    print(f"            - {action}")
        else:
            print(f"   ❌ Failed: {prediction_result['error']}")
        
        # Test 90-day churn prediction
        print(f"\n2. 90-Day Churn Prediction:")
        prediction_result = self.admin_dashboard.get_churn_prediction(
            prediction_horizon='90d'
        )
        
        if prediction_result['success']:
            prediction = prediction_result['churn_prediction']
            prediction_data = prediction['prediction_data']
            
            print(f"   ✅ 90-day churn prediction retrieved")
            print(f"   🎯 Predicted Churn: {prediction_data['predicted_churn']} customers")
            print(f"   📊 Predicted Churn Rate: {prediction_data['predicted_churn_rate']:.1f}%")
            print(f"   🎯 Confidence Level: {prediction_data['confidence_level']}")
        else:
            print(f"   ❌ Failed: {prediction_result['error']}")
    
    def demonstrate_churn_prevention_metrics(self):
        """Demonstrate churn prevention effectiveness metrics"""
        print("\n=== Churn Prevention Metrics ===")
        
        print(f"\n📊 Testing Churn Prevention Metrics:")
        
        # Test prevention metrics
        print(f"\n1. Churn Prevention Effectiveness (30 days):")
        metrics_result = self.admin_dashboard.get_churn_prevention_metrics(
            date_range='30d'
        )
        
        if metrics_result['success']:
            metrics = metrics_result['churn_prevention_metrics']
            prevention_metrics = metrics['prevention_metrics']
            
            print(f"   ✅ Prevention metrics retrieved")
            print(f"   📅 Date Range: {metrics['date_range']['start_date']} to {metrics['date_range']['end_date']}")
            print(f"   📊 Period: {metrics['date_range']['period']}")
            
            # Display prevention metrics
            print(f"   📈 Prevention Campaign Metrics:")
            print(f"      Prevention Campaigns: {prevention_metrics['prevention_campaigns']}")
            print(f"      Successful Interventions: {prevention_metrics['successful_interventions']}")
            print(f"      Intervention Success Rate: {prevention_metrics['intervention_success_rate']:.1f}%")
            print(f"      Campaign Cost: ${prevention_metrics['campaign_cost']:,.2f}")
            print(f"      Cost per Saved Customer: ${prevention_metrics['cost_per_saved_customer']:.2f}")
            print(f"      Total Value Saved: ${prevention_metrics['total_value_saved']:,.2f}")
            print(f"      ROI: {prevention_metrics['roi']:.1f}%")
            
            # Display effectiveness score
            effectiveness_score = metrics['effectiveness_score']
            print(f"   🎯 Overall Effectiveness Score: {effectiveness_score:.1f}/100")
            
            # Display optimization recommendations
            recommendations = metrics['optimization_recommendations']
            print(f"   💡 Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {metrics_result['error']}")
    
    def demonstrate_churn_trends(self):
        """Demonstrate churn trends analysis"""
        print("\n=== Churn Trends Analysis ===")
        
        print(f"\n📊 Testing Churn Trends:")
        
        # Test churn trends
        print(f"\n1. Churn Trends (12 months):")
        trends_result = self.admin_dashboard.get_churn_trends(
            period='12m'
        )
        
        if trends_result['success']:
            trends = trends_result['churn_trends']
            
            print(f"   ✅ Churn trends retrieved")
            print(f"   📅 Period: {trends['period']}")
            print(f"   📊 Start Date: {trends['start_date']}")
            print(f"   📊 End Date: {trends['end_date']}")
            
            # Display trend analysis
            trend_analysis = trends['trend_analysis']
            print(f"   📈 Trend Analysis:")
            print(f"      Average Churn Rate: {trend_analysis['average_churn_rate']:.1f}%")
            print(f"      Trend Direction: {trend_analysis['trend_direction']}")
            print(f"      Trend Percentage: {trend_analysis['trend_percentage']:.1f}%")
            print(f"      Best Period: {trend_analysis['best_period']}")
            print(f"      Worst Period: {trend_analysis['worst_period']}")
            
            # Display monthly trends
            print(f"   📅 Monthly Churn Rates:")
            for monthly_churn in trends['monthly_churn'][:6]:  # Show first 6 months
                print(f"      {monthly_churn['period']}: {monthly_churn['churn_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {trends_result['error']}")
    
    def demonstrate_churn_breakdown(self):
        """Demonstrate churn breakdown analysis"""
        print("\n=== Churn Breakdown Analysis ===")
        
        print(f"\n📊 Testing Churn Breakdown:")
        
        # Test tier breakdown
        print(f"\n1. Churn Breakdown by Tier:")
        breakdown_result = self.admin_dashboard.get_churn_breakdown(
            breakdown_dimension='tier',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['churn_breakdown']
            
            print(f"   ✅ Tier breakdown retrieved")
            print(f"   📊 Breakdown Dimension: {breakdown['breakdown_dimension']}")
            print(f"   📅 Date Range: {breakdown['date_range']}")
            
            # Display tier breakdown
            breakdown_data = breakdown['breakdown_data']
            print(f"   🏆 Tier Churn Rates:")
            for tier_type, tier_data in breakdown_data.items():
                print(f"      {tier_data['tier_name']}:")
                print(f"         Churned Customers: {tier_data['churned_customers']}")
                print(f"         Active Customers: {tier_data['active_customers']}")
                print(f"         Churn Rate: {tier_data['churn_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test geographic breakdown
        print(f"\n2. Churn Breakdown by Geographic Location:")
        breakdown_result = self.admin_dashboard.get_churn_breakdown(
            breakdown_dimension='geographic',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['churn_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Geographic breakdown retrieved")
            print(f"   🌍 Geographic Churn Rates:")
            for country, geo_data in breakdown_data.items():
                print(f"      {country}:")
                print(f"         Churned Customers: {geo_data['churned_customers']}")
                print(f"         Active Customers: {geo_data['active_customers']}")
                print(f"         Churn Rate: {geo_data['churn_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test customer segment breakdown
        print(f"\n3. Churn Breakdown by Customer Segment:")
        breakdown_result = self.admin_dashboard.get_churn_breakdown(
            breakdown_dimension='customer_segment',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['churn_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Customer segment breakdown retrieved")
            print(f"   👥 Customer Segment Churn Rates:")
            for segment_key, segment_data in breakdown_data.items():
                print(f"      {segment_data['segment_name']}:")
                print(f"         Churned Customers: {segment_data['churned_customers']}")
                print(f"         Active Customers: {segment_data['active_customers']}")
                print(f"         Churn Rate: {segment_data['churn_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test billing cycle breakdown
        print(f"\n4. Churn Breakdown by Billing Cycle:")
        breakdown_result = self.admin_dashboard.get_churn_breakdown(
            breakdown_dimension='billing_cycle',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['churn_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Billing cycle breakdown retrieved")
            print(f"   💳 Billing Cycle Churn Rates:")
            for cycle, cycle_data in breakdown_data.items():
                print(f"      {cycle_data['billing_cycle']}:")
                print(f"         Churned Customers: {cycle_data['churned_customers']}")
                print(f"         Active Customers: {cycle_data['active_customers']}")
                print(f"         Churn Rate: {cycle_data['churn_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
    
    def run_all_churn_analysis_demonstrations(self):
        """Run all churn analysis demonstrations"""
        print("🚀 MINGUS Admin Churn Analysis Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_churn_analysis()
            self.demonstrate_churn_prediction()
            self.demonstrate_churn_prevention_metrics()
            self.demonstrate_churn_trends()
            self.demonstrate_churn_breakdown()
            
            print("\n✅ All churn analysis demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = AdminChurnAnalysisExample()
    example.run_all_churn_analysis_demonstrations()

if __name__ == "__main__":
    main() 