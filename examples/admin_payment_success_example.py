"""
Admin Payment Success Rate Example for MINGUS
Demonstrates payment success rate analysis for administrators
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

class AdminPaymentSuccessExample:
    """Example demonstrating admin payment success rate analysis"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_payment_success_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.admin_dashboard = AdminBillingDashboard(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for payment success rate demonstration"""
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
        
        # Create sample customers
        customers = []
        for i in range(300):  # Create 300 customers for better payment analysis
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_payment_{i}',
                email=f'payment.user{i}@example.com',
                name=f'Payment User {i}',
                address={
                    'country': 'US' if i < 180 else 'CA' if i < 240 else 'UK',
                    'state': 'CA' if i < 90 else 'NY' if i < 180 else 'ON' if i < 240 else 'London',
                    'city': 'San Francisco' if i < 90 else 'New York' if i < 180 else 'Toronto' if i < 240 else 'London',
                    'zip': '94105' if i < 90 else '10001' if i < 180 else 'M5V' if i < 240 else 'SW1A'
                },
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=365 - (i * 1))  # Staggered creation dates
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with various payment scenarios
        subscriptions = []
        billing_records = []
        
        # Successful payments (250 customers)
        for i in range(250):
            subscription = Subscription(
                customer_id=customers[i].id,
                pricing_tier_id=budget_tier.id if i < 120 else mid_tier.id if i < 200 else professional_tier.id,
                stripe_subscription_id=f'sub_success_{i}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 150 else 'annual',
                amount=15.00 if i < 120 else 35.00 if i < 200 else 75.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create successful billing history
            billing_record = BillingHistory(
                customer_id=customers[i].id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-001',
                amount=subscription.amount,
                currency='USD',
                status='paid',
                description=f'Successful payment - {subscription.pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=25),
                paid_at=datetime.utcnow() - timedelta(days=25),
                stripe_invoice_id=f'in_{subscription.id}_success'
            )
            billing_records.append(billing_record)
        
        # Failed payments with different reasons (50 customers)
        failure_reasons = [
            'insufficient_funds',
            'card_expired', 
            'invalid_card',
            'network_error',
            'fraud_detection',
            'bank_decline'
        ]
        
        for i in range(50):
            failure_reason = failure_reasons[i % len(failure_reasons)]
            
            subscription = Subscription(
                customer_id=customers[i + 250].id,
                pricing_tier_id=budget_tier.id if i < 25 else mid_tier.id,
                stripe_subscription_id=f'sub_failed_{i}',
                status='past_due' if i < 30 else 'canceled',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly',
                amount=15.00 if i < 25 else 35.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create failed billing history
            billing_record = BillingHistory(
                customer_id=customers[i + 250].id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-FAILED',
                amount=subscription.amount,
                currency='USD',
                status='failed',
                description=f'Failed payment - {failure_reason}',
                created_at=datetime.utcnow() - timedelta(days=5),
                stripe_invoice_id=f'in_{subscription.id}_failed'
            )
            billing_records.append(billing_record)
        
        # Pending payments (for retry analysis)
        for i in range(10):
            subscription = Subscription(
                customer_id=customers[i + 300].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id=f'sub_pending_{i}',
                status='past_due',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow(),
                billing_cycle='monthly',
                amount=15.00,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create pending billing history
            billing_record = BillingHistory(
                customer_id=customers[i + 300].id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-PENDING',
                amount=subscription.amount,
                currency='USD',
                status='pending',
                description=f'Pending payment - retry in progress',
                created_at=datetime.utcnow() - timedelta(days=2),
                stripe_invoice_id=f'in_{subscription.id}_pending'
            )
            billing_records.append(billing_record)
        
        # Add some retry attempts for failed payments
        for i in range(20):
            retry_billing = BillingHistory(
                customer_id=customers[i + 250].id,
                subscription_id=subscriptions[i + 250].id,
                invoice_number=f'INV-{subscriptions[i + 250].id:04d}-RETRY',
                amount=subscriptions[i + 250].amount,
                currency='USD',
                status='paid' if i < 12 else 'failed',  # 60% retry success rate
                description=f'Retry payment attempt',
                created_at=datetime.utcnow() - timedelta(days=1),
                paid_at=datetime.utcnow() - timedelta(days=1) if i < 12 else None,
                stripe_invoice_id=f'in_{subscriptions[i + 250].id}_retry'
            )
            billing_records.append(retry_billing)
        
        self.db_session.add_all(subscriptions)
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_payment_success_rates(self):
        """Demonstrate comprehensive payment success rate analysis"""
        print("\n=== Payment Success Rate Analysis ===")
        
        print(f"\n📊 Testing Payment Success Rates:")
        
        # Test overall payment success analysis
        print(f"\n1. Overall Payment Success Analysis (30 days):")
        success_result = self.admin_dashboard.get_payment_success_rates(
            date_range='30d',
            analysis_type='overall'
        )
        
        if success_result['success']:
            success = success_result['payment_success_analysis']
            
            print(f"   ✅ Overall payment success analysis retrieved")
            print(f"   📅 Date Range: {success['date_range']['start_date']} to {success['date_range']['end_date']}")
            print(f"   📊 Period: {success['date_range']['period']}")
            print(f"   🎯 Overall Success Rate: {success['success_rate']:.1f}%")
            
            # Display success data
            success_data = success['success_data']
            print(f"   📈 Payment Summary:")
            print(f"      Total Attempts: {success_data['total_attempts']}")
            print(f"      Successful Payments: {success_data['successful_payments']}")
            print(f"      Failed Payments: {success_data['failed_payments']}")
            print(f"      Pending Payments: {success_data['pending_payments']}")
            print(f"      Success Rate: {success_data['success_rate']:.1f}%")
            print(f"      Failure Rate: {success_data['failure_rate']:.1f}%")
            print(f"      Total Amount Attempted: ${success_data['total_amount_attempted']:,.2f}")
            print(f"      Total Amount Collected: ${success_data['total_amount_collected']:,.2f}")
            
            # Display failure analysis
            failure_analysis = success['failure_analysis']
            print(f"   🔍 Payment Failure Analysis:")
            for failure in failure_analysis:
                print(f"      {failure['reason']}:")
                print(f"         Count: {failure['count']}")
                print(f"         Percentage: {failure['percentage']:.1f}%")
                print(f"         Recommendation: {failure['recommendation']}")
            
            # Display retry analysis
            retry_analysis = success['retry_analysis']
            print(f"   🔄 Payment Retry Analysis:")
            retry_summary = retry_analysis['retry_summary']
            print(f"      Total Retries: {retry_summary['total_retries']}")
            print(f"      Successful Retries: {retry_summary['successful_retries']}")
            print(f"      Failed Retries: {retry_summary['failed_retries']}")
            print(f"      Retry Success Rate: {retry_summary['retry_success_rate']:.1f}%")
            
            # Display optimization recommendations
            recommendations = success['optimization_recommendations']
            print(f"   💡 Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {success_result['error']}")
        
        # Test tier-based payment success analysis
        print(f"\n2. Tier-Based Payment Success Analysis:")
        success_result = self.admin_dashboard.get_payment_success_rates(
            date_range='30d',
            analysis_type='by_tier'
        )
        
        if success_result['success']:
            success = success_result['payment_success_analysis']
            success_data = success['success_data']
            
            print(f"   ✅ Tier-based payment success analysis retrieved")
            print(f"   🏆 Tier Payment Success Rates:")
            for tier_type, tier_data in success_data.items():
                print(f"      {tier_data['tier_name']}:")
                print(f"         Total Attempts: {tier_data['total_attempts']}")
                print(f"         Successful Payments: {tier_data['successful_payments']}")
                print(f"         Failed Payments: {tier_data['failed_payments']}")
                print(f"         Success Rate: {tier_data['success_rate']:.1f}%")
                print(f"         Average Amount: ${tier_data['avg_amount']:.2f}")
        else:
            print(f"   ❌ Failed: {success_result['error']}")
        
        # Test billing cycle payment success analysis
        print(f"\n3. Billing Cycle Payment Success Analysis:")
        success_result = self.admin_dashboard.get_payment_success_rates(
            date_range='30d',
            analysis_type='by_billing_cycle'
        )
        
        if success_result['success']:
            success = success_result['payment_success_analysis']
            success_data = success['success_data']
            
            print(f"   ✅ Billing cycle payment success analysis retrieved")
            print(f"   💳 Billing Cycle Payment Success Rates:")
            for cycle, cycle_data in success_data.items():
                print(f"      {cycle_data['billing_cycle']}:")
                print(f"         Total Attempts: {cycle_data['total_attempts']}")
                print(f"         Successful Payments: {cycle_data['successful_payments']}")
                print(f"         Failed Payments: {cycle_data['failed_payments']}")
                print(f"         Success Rate: {cycle_data['success_rate']:.1f}%")
                print(f"         Average Amount: ${cycle_data['avg_amount']:.2f}")
        else:
            print(f"   ❌ Failed: {success_result['error']}")
        
        # Test payment method success analysis
        print(f"\n4. Payment Method Success Analysis:")
        success_result = self.admin_dashboard.get_payment_success_rates(
            date_range='30d',
            analysis_type='by_payment_method'
        )
        
        if success_result['success']:
            success = success_result['payment_success_analysis']
            success_data = success['success_data']
            
            print(f"   ✅ Payment method success analysis retrieved")
            print(f"   💳 Payment Method Success Rates:")
            for method_key, method_data in success_data.items():
                print(f"      {method_data['payment_method']}:")
                print(f"         Total Attempts: {method_data['total_attempts']}")
                print(f"         Successful Payments: {method_data['successful_payments']}")
                print(f"         Failed Payments: {method_data['failed_payments']}")
                print(f"         Success Rate: {method_data['success_rate']:.1f}%")
                print(f"         Average Amount: ${method_data['avg_amount']:.2f}")
        else:
            print(f"   ❌ Failed: {success_result['error']}")
    
    def demonstrate_payment_success_trends(self):
        """Demonstrate payment success rate trends"""
        print("\n=== Payment Success Rate Trends ===")
        
        print(f"\n📊 Testing Payment Success Trends:")
        
        # Test payment success trends
        print(f"\n1. Payment Success Trends (12 months):")
        trends_result = self.admin_dashboard.get_payment_success_trends(
            period='12m'
        )
        
        if trends_result['success']:
            trends = trends_result['payment_success_trends']
            
            print(f"   ✅ Payment success trends retrieved")
            print(f"   📅 Period: {trends['period']}")
            print(f"   📊 Start Date: {trends['start_date']}")
            print(f"   📊 End Date: {trends['end_date']}")
            
            # Display trend analysis
            trend_analysis = trends['trend_analysis']
            print(f"   📈 Trend Analysis:")
            print(f"      Average Success Rate: {trend_analysis['average_success_rate']:.1f}%")
            print(f"      Trend Direction: {trend_analysis['trend_direction']}")
            print(f"      Trend Percentage: {trend_analysis['trend_percentage']:.1f}%")
            print(f"      Best Period: {trend_analysis['best_period']}")
            print(f"      Worst Period: {trend_analysis['worst_period']}")
            
            # Display monthly trends
            print(f"   📅 Monthly Success Rates:")
            for monthly_success in trends['monthly_success'][:6]:  # Show first 6 months
                print(f"      {monthly_success['period']}: {monthly_success['success_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {trends_result['error']}")
    
    def demonstrate_payment_failure_breakdown(self):
        """Demonstrate payment failure breakdown analysis"""
        print("\n=== Payment Failure Breakdown Analysis ===")
        
        print(f"\n📊 Testing Payment Failure Breakdown:")
        
        # Test failure reason breakdown
        print(f"\n1. Payment Failure Breakdown by Reason:")
        breakdown_result = self.admin_dashboard.get_payment_failure_breakdown(
            breakdown_dimension='reason',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['payment_failure_breakdown']
            
            print(f"   ✅ Failure reason breakdown retrieved")
            print(f"   📊 Breakdown Dimension: {breakdown['breakdown_dimension']}")
            print(f"   📅 Date Range: {breakdown['date_range']}")
            
            # Display failure reasons
            breakdown_data = breakdown['breakdown_data']
            print(f"   🔍 Payment Failure Reasons:")
            for reason_key, reason_data in breakdown_data.items():
                print(f"      {reason_data['reason']}:")
                print(f"         Count: {reason_data['count']}")
                print(f"         Percentage: {reason_data['percentage']:.1f}%")
                print(f"         Average Amount: ${reason_data['avg_amount']:.2f}")
                print(f"         Recommendation: {reason_data['recommendation']}")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test geographic failure breakdown
        print(f"\n2. Payment Failure Breakdown by Geographic Location:")
        breakdown_result = self.admin_dashboard.get_payment_failure_breakdown(
            breakdown_dimension='geographic',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['payment_failure_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Geographic failure breakdown retrieved")
            print(f"   🌍 Geographic Failure Rates:")
            for country, geo_data in breakdown_data.items():
                print(f"      {country}:")
                print(f"         Total Attempts: {geo_data['total_attempts']}")
                print(f"         Failed Attempts: {geo_data['failed_attempts']}")
                print(f"         Failure Rate: {geo_data['failure_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test time period failure breakdown
        print(f"\n3. Payment Failure Breakdown by Time Period:")
        breakdown_result = self.admin_dashboard.get_payment_failure_breakdown(
            breakdown_dimension='time_period',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['payment_failure_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Time period failure breakdown retrieved")
            print(f"   📅 Weekly Failure Rates:")
            for week_key, week_data in list(breakdown_data.items())[:4]:  # Show first 4 weeks
                print(f"      {week_data['period']}: {week_data['failure_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
        
        # Test customer segment failure breakdown
        print(f"\n4. Payment Failure Breakdown by Customer Segment:")
        breakdown_result = self.admin_dashboard.get_payment_failure_breakdown(
            breakdown_dimension='customer_segment',
            date_range='30d'
        )
        
        if breakdown_result['success']:
            breakdown = breakdown_result['payment_failure_breakdown']
            breakdown_data = breakdown['breakdown_data']
            
            print(f"   ✅ Customer segment failure breakdown retrieved")
            print(f"   👥 Customer Segment Failure Rates:")
            for segment_key, segment_data in breakdown_data.items():
                print(f"      {segment_data['segment_name']}:")
                print(f"         Total Attempts: {segment_data['total_attempts']}")
                print(f"         Failed Attempts: {segment_data['failed_attempts']}")
                print(f"         Failure Rate: {segment_data['failure_rate']:.1f}%")
        else:
            print(f"   ❌ Failed: {breakdown_result['error']}")
    
    def demonstrate_payment_retry_analysis(self):
        """Demonstrate payment retry analysis"""
        print("\n=== Payment Retry Analysis ===")
        
        print(f"\n📊 Testing Payment Retry Analysis:")
        
        # Test payment retry analysis
        print(f"\n1. Payment Retry Analysis (30 days):")
        retry_result = self.admin_dashboard.get_payment_retry_analysis(
            date_range='30d'
        )
        
        if retry_result['success']:
            retry = retry_result['payment_retry_analysis']
            
            print(f"   ✅ Payment retry analysis retrieved")
            print(f"   📅 Date Range: {retry['date_range']['start_date']} to {retry['date_range']['end_date']}")
            print(f"   📊 Period: {retry['date_range']['period']}")
            
            # Display retry analysis
            retry_analysis = retry['retry_analysis']
            retry_summary = retry_analysis['retry_summary']
            print(f"   🔄 Retry Summary:")
            print(f"      Total Failed Payments: {retry_summary['total_failed_payments']}")
            print(f"      Total Retries Attempted: {retry_summary['total_retries_attempted']}")
            print(f"      Successful Retries: {retry_summary['successful_retries']}")
            print(f"      Failed Retries: {retry_summary['failed_retries']}")
            print(f"      Retry Attempt Rate: {retry_summary['retry_attempt_rate']:.1f}%")
            print(f"      Retry Success Rate: {retry_summary['retry_success_rate']:.1f}%")
            
            # Display retry attempts analysis
            attempts_analysis = retry_analysis['retry_attempts_analysis']
            print(f"   📊 Retry Attempts Analysis:")
            for attempt, data in attempts_analysis.items():
                print(f"      {attempt}:")
                print(f"         Count: {data['count']}")
                print(f"         Success Rate: {data['success_rate']:.1f}%")
                print(f"         Average Delay: {data['avg_delay_hours']} hours")
            
            # Display retry timing analysis
            timing_analysis = retry_analysis['retry_timing_analysis']
            print(f"   ⏰ Retry Timing Analysis:")
            for timing, data in timing_analysis.items():
                print(f"      {timing}:")
                print(f"         Count: {data['count']}")
                print(f"         Success Rate: {data['success_rate']:.1f}%")
                print(f"         Average Delay: {data['avg_delay_hours']} hours")
            
            # Display retry method analysis
            method_analysis = retry_analysis['retry_method_analysis']
            print(f"   💳 Retry Method Analysis:")
            for method, data in method_analysis.items():
                print(f"      {method}:")
                print(f"         Count: {data['count']}")
                print(f"         Success Rate: {data['success_rate']:.1f}%")
                print(f"         Method: {data['method']}")
            
            # Display customer communication
            communication = retry_analysis['retry_customer_communication']
            print(f"   📧 Customer Communication:")
            print(f"      Emails Sent: {communication['emails_sent']}")
            print(f"      SMS Sent: {communication['sms_sent']}")
            print(f"      Calls Made: {communication['calls_made']}")
            print(f"      Response Rate: {communication['response_rate']:.1f}%")
            
            # Display retry success rate
            retry_success_rate = retry['retry_success_rate']
            print(f"   🎯 Overall Retry Success Rate: {retry_success_rate:.1f}%")
            
            # Display optimization recommendations
            recommendations = retry['retry_optimization_recommendations']
            print(f"   💡 Retry Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {retry_result['error']}")
    
    def demonstrate_payment_performance_metrics(self):
        """Demonstrate payment performance metrics"""
        print("\n=== Payment Performance Metrics ===")
        
        print(f"\n📊 Testing Payment Performance Metrics:")
        
        # Test payment performance metrics
        print(f"\n1. Payment Performance Metrics (30 days):")
        performance_result = self.admin_dashboard.get_payment_performance_metrics(
            date_range='30d'
        )
        
        if performance_result['success']:
            performance = performance_result['payment_performance_metrics']
            
            print(f"   ✅ Payment performance metrics retrieved")
            print(f"   📅 Date Range: {performance['date_range']['start_date']} to {performance['date_range']['end_date']}")
            print(f"   📊 Period: {performance['date_range']['period']}")
            
            # Display performance metrics
            performance_metrics = performance['performance_metrics']
            print(f"   📈 Performance Metrics:")
            print(f"      Success Rate: {performance_metrics['success_rate']:.1f}%")
            print(f"      Failure Rate: {performance_metrics['failure_rate']:.1f}%")
            print(f"      Total Volume: ${performance_metrics['total_volume']:,.2f}")
            print(f"      Collected Volume: ${performance_metrics['collected_volume']:,.2f}")
            print(f"      Collection Rate: {performance_metrics['collection_rate']:.1f}%")
            print(f"      Average Transaction Value: ${performance_metrics['avg_transaction_value']:.2f}")
            
            # Display processing time metrics
            processing_time = performance_metrics['processing_time']
            print(f"   ⏱️ Processing Time Metrics:")
            print(f"      Average Processing Time: {processing_time['avg_processing_time_seconds']:.1f} seconds")
            print(f"      95th Percentile: {processing_time['p95_processing_time_seconds']:.1f} seconds")
            print(f"      99th Percentile: {processing_time['p99_processing_time_seconds']:.1f} seconds")
            
            # Display customer satisfaction metrics
            satisfaction = performance_metrics['customer_satisfaction']
            print(f"   😊 Customer Satisfaction Metrics:")
            print(f"      Payment Success Satisfaction: {satisfaction['payment_success_satisfaction']}/5")
            print(f"      Payment Failure Satisfaction: {satisfaction['payment_failure_satisfaction']}/5")
            print(f"      Overall Payment Satisfaction: {satisfaction['overall_payment_satisfaction']}/5")
            
            # Display cost metrics
            cost_metrics = performance_metrics['cost_metrics']
            print(f"   💰 Cost Metrics:")
            print(f"      Processing Fees: ${cost_metrics['processing_fees']:,.2f}")
            print(f"      Chargeback Rate: {cost_metrics['chargeback_rate']:.1f}%")
            print(f"      Refund Rate: {cost_metrics['refund_rate']:.1f}%")
            print(f"      Cost per Transaction: ${cost_metrics['cost_per_transaction']:.2f}")
            
            # Display performance score
            performance_score = performance['performance_score']
            print(f"   🎯 Overall Performance Score: {performance_score:.1f}/100")
            
            # Display optimization recommendations
            recommendations = performance['optimization_recommendations']
            print(f"   💡 Performance Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {performance_result['error']}")
    
    def run_all_payment_success_demonstrations(self):
        """Run all payment success rate demonstrations"""
        print("🚀 MINGUS Admin Payment Success Rate Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_payment_success_rates()
            self.demonstrate_payment_success_trends()
            self.demonstrate_payment_failure_breakdown()
            self.demonstrate_payment_retry_analysis()
            self.demonstrate_payment_performance_metrics()
            
            print("\n✅ All payment success rate demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = AdminPaymentSuccessExample()
    example.run_all_payment_success_demonstrations()

if __name__ == "__main__":
    main() 