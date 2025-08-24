"""
Revenue Optimization Example for MINGUS
Demonstrates comprehensive revenue optimization including upgrade prompts,
churn prevention workflows, payment recovery automation, and revenue recognition reporting
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.revenue_optimizer import RevenueOptimizer
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory, FeatureUsage

class RevenueOptimizationExample:
    """Example demonstrating comprehensive revenue optimization"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_revenue_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        self.revenue_optimizer = RevenueOptimizer(self.db_session, self.config)
        
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
        
        # Create sample customers with different usage patterns
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
                stripe_customer_id='cus_churn123',
                email='churn.user@example.com',
                name='Churn Risk User',
                address={'country': 'US', 'state': 'FL'}
            ),
            Customer(
                user_id=5,
                stripe_customer_id='cus_recovery123',
                email='recovery.user@example.com',
                name='Payment Recovery User',
                address={'country': 'US', 'state': 'WA'}
            )
        ]
        
        for customer in customers:
            self.db_session.add(customer)
        self.db_session.commit()
        
        # Create sample subscriptions
        subscriptions = [
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
            Subscription(
                customer_id=customers[1].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_mid123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            Subscription(
                customer_id=customers[2].id,
                pricing_tier_id=professional_tier.id,
                stripe_subscription_id='sub_pro123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=99.99,
                currency='USD'
            ),
            Subscription(
                customer_id=customers[3].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_churn123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            Subscription(
                customer_id=customers[4].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_recovery123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            )
        ]
        
        for subscription in subscriptions:
            self.db_session.add(subscription)
        self.db_session.commit()
        
        # Create sample usage data
        usage_data = [
            # Budget user - high usage (upgrade candidate)
            FeatureUsage(
                subscription_id=subscriptions[0].id,
                usage_month=datetime.utcnow().month,
                usage_year=datetime.utcnow().year,
                health_checkins_used=4,  # At limit
                financial_reports_used=2,  # At limit
                ai_insights_used=0,
                api_calls_made=1500  # High API usage
            ),
            # Mid-tier user - moderate usage
            FeatureUsage(
                subscription_id=subscriptions[1].id,
                usage_month=datetime.utcnow().month,
                usage_year=datetime.utcnow().year,
                health_checkins_used=8,
                financial_reports_used=6,
                ai_insights_used=25,
                api_calls_made=5000
            ),
            # Professional user - unlimited usage
            FeatureUsage(
                subscription_id=subscriptions[2].id,
                usage_month=datetime.utcnow().month,
                usage_year=datetime.utcnow().year,
                health_checkins_used=50,
                financial_reports_used=30,
                ai_insights_used=200,
                api_calls_made=25000
            ),
            # Churn risk user - declining usage
            FeatureUsage(
                subscription_id=subscriptions[3].id,
                usage_month=datetime.utcnow().month,
                usage_year=datetime.utcnow().year,
                health_checkins_used=2,  # Low usage
                financial_reports_used=1,  # Low usage
                ai_insights_used=5,  # Low usage
                api_calls_made=200  # Low API usage
            ),
            # Payment recovery user - normal usage
            FeatureUsage(
                subscription_id=subscriptions[4].id,
                usage_month=datetime.utcnow().month,
                usage_year=datetime.utcnow().year,
                health_checkins_used=3,
                financial_reports_used=1,
                ai_insights_used=0,
                api_calls_made=800
            )
        ]
        
        for usage in usage_data:
            self.db_session.add(usage)
        self.db_session.commit()
        
        # Create sample billing history
        billing_records = []
        for i, subscription in enumerate(subscriptions):
            # Successful payments
            for j in range(3):
                billing_record = BillingHistory(
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    stripe_invoice_id=f'inv_{subscription.id}_{j}',
                    invoice_number=f'INV-{subscription.customer_id:06d}-{j+1:04d}',
                    amount_due=subscription.amount,
                    amount_paid=subscription.amount,
                    currency=subscription.currency,
                    status='succeeded',
                    paid=True,
                    invoice_date=datetime.utcnow() - timedelta(days=30 * (j + 1)),
                    due_date=datetime.utcnow() - timedelta(days=30 * (j + 1)),
                    paid_date=datetime.utcnow() - timedelta(days=30 * (j + 1)),
                    description=f'Monthly subscription fee - {subscription.pricing_tier.name}',
                    invoice_type='recurring'
                )
                billing_records.append(billing_record)
            
            # Add failed payment for recovery user
            if i == 4:  # Payment recovery user
                failed_payment = BillingHistory(
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    stripe_invoice_id=f'inv_{subscription.id}_failed',
                    invoice_number=f'INV-{subscription.customer_id:06d}-FAILED',
                    amount_due=subscription.amount,
                    amount_paid=0,
                    currency=subscription.currency,
                    status='failed',
                    paid=False,
                    invoice_date=datetime.utcnow() - timedelta(days=5),
                    due_date=datetime.utcnow() - timedelta(days=5),
                    description=f'Monthly subscription fee - {subscription.pricing_tier.name}',
                    invoice_type='recurring'
                )
                billing_records.append(failed_payment)
        
        for record in billing_records:
            self.db_session.add(record)
        self.db_session.commit()
        
        self.sample_customers = customers
        self.sample_subscriptions = subscriptions
        self.sample_usage_data = usage_data
        self.sample_billing_records = billing_records
    
    def demonstrate_upgrade_prompt_triggers(self):
        """Demonstrate upgrade prompt triggers"""
        print("\n=== Upgrade Prompt Triggers ===")
        
        # Check for upgrade opportunities across all customers
        upgrade_result = self.payment_service.check_upgrade_opportunities(include_all_customers=True)
        
        if upgrade_result['success']:
            print(f"✅ Found {upgrade_result['total_opportunities']} upgrade opportunities:")
            
            for opportunity in upgrade_result['upgrade_opportunities']:
                print(f"\n📈 {opportunity['customer_name']} ({opportunity['customer_email']}):")
                print(f"   Current tier: {opportunity['current_tier_name']} ({opportunity['current_tier']})")
                print(f"   Confidence score: {opportunity['confidence_score']:.1%}")
                print(f"   Recommended tier: {opportunity['recommended_tier'].name if opportunity['recommended_tier'] else 'None'}")
                print(f"   Estimated value: ${opportunity['estimated_value']:.2f}")
                
                print(f"   Triggers:")
                for trigger in opportunity['triggers']:
                    icon = "🔴" if trigger['type'] == 'usage_threshold' else "🟡" if trigger['type'] == 'feature_limit_reached' else "🟢"
                    print(f"     {icon} {trigger['description']}")
            
            # Generate upgrade prompt for high-confidence opportunity
            if upgrade_result['upgrade_opportunities']:
                high_confidence_opp = max(upgrade_result['upgrade_opportunities'], 
                                        key=lambda x: x['confidence_score'])
                
                if high_confidence_opp['confidence_score'] >= 0.7:
                    prompt_result = self.payment_service.generate_upgrade_prompt(
                        customer_id=high_confidence_opp['customer_id'],
                        prompt_type='usage_based'
                    )
                    
                    if prompt_result['success']:
                        prompt_data = prompt_result['prompt_data']
                        print(f"\n🎯 Generated upgrade prompt for {high_confidence_opp['customer_name']}:")
                        print(f"   Title: {prompt_data['title']}")
                        print(f"   Subtitle: {prompt_data['subtitle']}")
                        print(f"   Message: {prompt_data['message']}")
                        print(f"   CTA: {prompt_data['cta_text']} -> {prompt_data['cta_url']}")
                        print(f"   Urgency: {prompt_data['urgency']}")
                        
                        print(f"   Benefits:")
                        for benefit in prompt_data['benefits']:
                            print(f"     ✅ {benefit}")
        else:
            print(f"❌ Error checking upgrade opportunities: {upgrade_result['error']}")
    
    def demonstrate_churn_prevention_workflows(self):
        """Demonstrate churn prevention workflows"""
        print("\n=== Churn Prevention Workflows ===")
        
        # Detect churn risks across all customers
        churn_result = self.payment_service.detect_churn_risk(include_all_customers=True)
        
        if churn_result['success']:
            print(f"✅ Found {churn_result['total_risks']} customers at churn risk:")
            
            for risk in churn_result['churn_risks']:
                risk_icon = {
                    'low': '🟢',
                    'medium': '🟡', 
                    'high': '🟠',
                    'critical': '🔴'
                }.get(risk['risk_level'], '❓')
                
                print(f"\n{risk_icon} {risk['customer_name']} ({risk['customer_email']}):")
                print(f"   Risk level: {risk['risk_level']}")
                print(f"   Risk score: {risk['risk_score']:.1%}")
                print(f"   Current tier: {risk['current_tier']}")
                
                print(f"   Risk indicators:")
                for indicator in risk['risk_indicators']:
                    severity_icon = {
                        'low': '🟢',
                        'medium': '🟡',
                        'high': '🟠',
                        'critical': '🔴'
                    }.get(indicator['severity'], '❓')
                    print(f"     {severity_icon} {indicator['description']}")
                
                print(f"   Recommended actions:")
                for action in risk['recommended_actions']:
                    print(f"     📋 {action}")
            
            # Execute churn prevention workflow for high-risk customer
            if churn_result['churn_risks']:
                high_risk_customer = max(churn_result['churn_risks'], 
                                       key=lambda x: x['risk_score'])
                
                if high_risk_customer['risk_level'] in ['high', 'critical']:
                    workflow_result = self.payment_service.execute_churn_prevention_workflow(
                        customer_id=high_risk_customer['customer_id'],
                        workflow_type='automated'
                    )
                    
                    if workflow_result['success']:
                        print(f"\n🛡️ Executed churn prevention workflow for {high_risk_customer['customer_name']}:")
                        workflow_data = workflow_result['workflow_result']
                        print(f"   Workflow type: {workflow_data.get('workflow_type', 'automated')}")
                        print(f"   Actions taken: {len(workflow_data.get('actions_taken', []))}")
                        
                        for action in workflow_data.get('actions_taken', []):
                            print(f"     ✅ {action}")
                    else:
                        print(f"❌ Error executing churn prevention workflow: {workflow_result['error']}")
        else:
            print(f"❌ Error detecting churn risk: {churn_result['error']}")
    
    def demonstrate_payment_recovery_automation(self):
        """Demonstrate payment recovery automation"""
        print("\n=== Payment Recovery Automation ===")
        
        # Identify payment recovery opportunities
        recovery_result = self.payment_service.identify_payment_recovery_opportunities()
        
        if recovery_result['success']:
            print(f"✅ Found {recovery_result['total_opportunities']} payment recovery opportunities:")
            
            for opportunity in recovery_result['recovery_opportunities']:
                potential_icon = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠'
                }.get(opportunity['recovery_potential'], '❓')
                
                print(f"\n{potential_icon} {opportunity['customer_name']} ({opportunity['customer_email']}):")
                print(f"   Invoice: {opportunity['invoice_number']}")
                print(f"   Amount due: ${opportunity['amount_due']:.2f}")
                print(f"   Days overdue: {opportunity['days_overdue']}")
                print(f"   Recovery potential: {opportunity['recovery_potential']}")
                print(f"   Recovery score: {opportunity['recovery_score']:.1%}")
                print(f"   Recommended strategy: {opportunity['recommended_strategy']}")
                print(f"   Next action: {opportunity['next_action']}")
            
            # Execute payment recovery for high-potential opportunity
            if recovery_result['recovery_opportunities']:
                high_potential_opp = max(recovery_result['recovery_opportunities'], 
                                       key=lambda x: x['recovery_score'])
                
                if high_potential_opp['recovery_potential'] == 'high':
                    recovery_result = self.payment_service.execute_payment_recovery_automation(
                        customer_id=high_potential_opp['customer_id'],
                        invoice_id=high_potential_opp['invoice_id'],
                        strategy='auto'
                    )
                    
                    if recovery_result['success']:
                        print(f"\n💳 Executed payment recovery for {high_potential_opp['customer_name']}:")
                        recovery_data = recovery_result['recovery_result']
                        print(f"   Status: {recovery_data['status']}")
                        print(f"   Strategy used: {recovery_data.get('strategy', 'auto')}")
                        print(f"   Next retry: {recovery_data.get('next_retry', 'N/A')}")
                        print(f"   Message: {recovery_data.get('message', 'N/A')}")
                    else:
                        print(f"❌ Error executing payment recovery: {recovery_result['error']}")
        else:
            print(f"❌ Error identifying payment recovery opportunities: {recovery_result['error']}")
    
    def demonstrate_revenue_recognition_reporting(self):
        """Demonstrate revenue recognition reporting"""
        print("\n=== Revenue Recognition Reporting ===")
        
        # Generate revenue recognition report for current month
        start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.utcnow()
        
        report_result = self.payment_service.generate_revenue_recognition_report(
            start_date=start_date,
            end_date=end_date,
            report_type='comprehensive'
        )
        
        if report_result['success']:
            report = report_result['report']
            print(f"✅ Generated revenue recognition report:")
            print(f"   Period: {report['report_period']['start_date']} to {report['report_period']['end_date']}")
            print(f"   Generated: {report['report_period']['generated_at']}")
            
            metrics = report['revenue_metrics']
            print(f"\n📊 Revenue Metrics:")
            print(f"   Total revenue: ${metrics['total_revenue']:.2f}")
            print(f"   Recognized revenue: ${metrics['recognized_revenue']:.2f}")
            print(f"   Deferred revenue: ${report['deferred_revenue']['total_deferred']:.2f}")
            print(f"   Growth rate: {metrics['growth_rate']:.1%}")
            
            summary = report['summary']
            print(f"\n📈 Summary:")
            print(f"   Total revenue: ${summary['total_revenue']:.2f}")
            print(f"   Recognized revenue: ${summary['recognized_revenue']:.2f}")
            print(f"   Deferred revenue: ${summary['deferred_revenue']:.2f}")
            print(f"   Revenue growth: {summary['revenue_growth']:.1%}")
            
            # Show recognition schedule
            schedule = report['recognition_schedule']
            print(f"\n📅 Recognition Schedule:")
            for period, amount in schedule.items():
                print(f"   {period}: ${amount:.2f}")
        else:
            print(f"❌ Error generating revenue recognition report: {report_result['error']}")
        
        # Get revenue analytics
        analytics_result = self.payment_service.get_revenue_analytics(
            period='monthly',
            include_projections=True
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            print(f"\n📊 Revenue Analytics:")
            print(f"   Period: {analytics['period']}")
            print(f"   Date range: {analytics['start_date']} to {analytics['end_date']}")
            
            metrics = analytics['metrics']
            print(f"\n📈 Key Metrics:")
            print(f"   Total revenue: ${metrics['total_revenue']:.2f}")
            print(f"   Recurring revenue: ${metrics['recurring_revenue']:.2f}")
            print(f"   One-time revenue: ${metrics['one_time_revenue']:.2f}")
            print(f"   Average order value: ${metrics['average_order_value']:.2f}")
            print(f"   Customer count: {metrics['customer_count']}")
            print(f"   Churn rate: {metrics['churn_rate']:.1%}")
            print(f"   Upgrade rate: {metrics['upgrade_rate']:.1%}")
            print(f"   Downgrade rate: {metrics['downgrade_rate']:.1%}")
            
            # Show tier breakdown
            tier_breakdown = analytics['tier_breakdown']
            print(f"\n🏷️ Tier Breakdown:")
            for tier, data in tier_breakdown.items():
                print(f"   {tier}: ${data['revenue']:.2f} ({data['percentage']:.1%}) - {data['customers']} customers")
            
            # Show trends
            trends = analytics['trends']
            print(f"\n📈 Trends:")
            for trend, value in trends.items():
                print(f"   {trend}: {value:.1%}")
            
            # Show projections
            if 'projections' in analytics:
                projections = analytics['projections']
                print(f"\n🔮 Projections:")
                for period, projection in projections.items():
                    print(f"   {period}: ${projection['revenue']:.2f} ({projection['growth']:.1%} growth)")
        else:
            print(f"❌ Error getting revenue analytics: {analytics_result['error']}")
    
    def demonstrate_revenue_optimization_cycle(self):
        """Demonstrate complete revenue optimization cycle"""
        print("\n=== Revenue Optimization Cycle ===")
        
        # Run complete revenue optimization cycle
        cycle_result = self.payment_service.run_revenue_optimization_cycle()
        
        if cycle_result['success']:
            results = cycle_result['results']
            print(f"✅ Revenue optimization cycle completed:")
            print(f"   Upgrade opportunities: {results['upgrade_opportunities']}")
            print(f"   Churn risks: {results['churn_risks']}")
            print(f"   Recovery opportunities: {results['recovery_opportunities']}")
            print(f"   Actions taken: {results['actions_taken']}")
            
            if results['errors']:
                print(f"   Errors encountered: {len(results['errors'])}")
                for error in results['errors'][:3]:  # Show first 3 errors
                    print(f"     ❌ {error}")
            
            # Calculate potential impact
            print(f"\n📊 Potential Impact Analysis:")
            
            # Estimate upgrade revenue
            upgrade_revenue = results['upgrade_opportunities'] * 20  # Average $20 upgrade
            print(f"   Potential upgrade revenue: ${upgrade_revenue:.2f}")
            
            # Estimate churn prevention savings
            churn_savings = results['churn_risks'] * 30  # Average $30 saved per prevented churn
            print(f"   Potential churn prevention savings: ${churn_savings:.2f}")
            
            # Estimate recovery revenue
            recovery_revenue = results['recovery_opportunities'] * 15  # Average $15 recovered
            print(f"   Potential recovery revenue: ${recovery_revenue:.2f}")
            
            total_potential = upgrade_revenue + churn_savings + recovery_revenue
            print(f"   Total potential impact: ${total_potential:.2f}")
            
            # ROI calculation
            if results['actions_taken'] > 0:
                roi = (total_potential / results['actions_taken']) * 100
                print(f"   Estimated ROI per action: {roi:.1f}%")
        else:
            print(f"❌ Error running revenue optimization cycle: {cycle_result['error']}")
    
    def run_all_demonstrations(self):
        """Run all revenue optimization demonstrations"""
        print("🚀 MINGUS Revenue Optimization Demonstration")
        print("=" * 50)
        
        try:
            self.demonstrate_upgrade_prompt_triggers()
            self.demonstrate_churn_prevention_workflows()
            self.demonstrate_payment_recovery_automation()
            self.demonstrate_revenue_recognition_reporting()
            self.demonstrate_revenue_optimization_cycle()
            
            print("\n✅ All revenue optimization demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = RevenueOptimizationExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 