"""
Automated Workflows Example for MINGUS
Demonstrates comprehensive automated workflows including trial expiration notifications,
payment failure recovery, subscription renewals, upgrade/downgrade confirmations,
and cancellation surveys with retention offers
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.automated_workflows import AutomatedWorkflowManager, WorkflowType, WorkflowStatus
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory, FeatureUsage

class AutomatedWorkflowsExample:
    """Example demonstrating comprehensive automated workflows"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_workflows_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        self.workflow_manager = AutomatedWorkflowManager(self.db_session, self.config)
        
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
                stripe_customer_id='cus_trial123',
                email='trial.user@example.com',
                name='Trial User',
                address={'country': 'US', 'state': 'CA'}
            ),
            Customer(
                user_id=2,
                stripe_customer_id='cus_payment123',
                email='payment.user@example.com',
                name='Payment User',
                address={'country': 'US', 'state': 'NY'}
            ),
            Customer(
                user_id=3,
                stripe_customer_id='cus_renewal123',
                email='renewal.user@example.com',
                name='Renewal User',
                address={'country': 'US', 'state': 'TX'}
            ),
            Customer(
                user_id=4,
                stripe_customer_id='cus_upgrade123',
                email='upgrade.user@example.com',
                name='Upgrade User',
                address={'country': 'US', 'state': 'FL'}
            ),
            Customer(
                user_id=5,
                stripe_customer_id='cus_cancel123',
                email='cancel.user@example.com',
                name='Cancel User',
                address={'country': 'US', 'state': 'WA'}
            )
        ]
        
        for customer in customers:
            self.db_session.add(customer)
        self.db_session.commit()
        
        # Create sample subscriptions
        subscriptions = [
            # Trial subscription (expiring soon)
            Subscription(
                customer_id=customers[0].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_trial123',
                status='trialing',
                trial_start=datetime.utcnow() - timedelta(days=11),
                trial_end=datetime.utcnow() + timedelta(days=1),  # Expires tomorrow
                current_period_start=datetime.utcnow() - timedelta(days=11),
                current_period_end=datetime.utcnow() + timedelta(days=1),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            ),
            # Active subscription with failed payment
            Subscription(
                customer_id=customers[1].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_payment123',
                status='past_due',
                current_period_start=datetime.utcnow() - timedelta(days=35),
                current_period_end=datetime.utcnow() - timedelta(days=5),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            # Active subscription with upcoming renewal
            Subscription(
                customer_id=customers[2].id,
                pricing_tier_id=professional_tier.id,
                stripe_subscription_id='sub_renewal123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=23),
                current_period_end=datetime.utcnow() + timedelta(days=7),  # Renews in 7 days
                billing_cycle='monthly',
                amount=99.99,
                currency='USD'
            ),
            # Active subscription for upgrade demo
            Subscription(
                customer_id=customers[3].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_upgrade123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            ),
            # Active subscription for cancellation demo
            Subscription(
                customer_id=customers[4].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_cancel123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=20),
                current_period_end=datetime.utcnow() + timedelta(days=10),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            )
        ]
        
        for subscription in subscriptions:
            self.db_session.add(subscription)
        self.db_session.commit()
        
        # Create sample billing history
        billing_records = []
        
        # Failed payment for payment recovery demo
        failed_payment = BillingHistory(
            customer_id=customers[1].id,
            subscription_id=subscriptions[1].id,
            stripe_invoice_id='inv_failed123',
            invoice_number='INV-000001-FAILED',
            amount_due=29.99,
            amount_paid=0,
            currency='USD',
            status='failed',
            paid=False,
            invoice_date=datetime.utcnow() - timedelta(days=5),
            due_date=datetime.utcnow() - timedelta(days=5),
            description='Monthly subscription fee - Mid-Tier',
            invoice_type='recurring',
            retry_count=1
        )
        billing_records.append(failed_payment)
        
        # Successful payments for other subscriptions
        for i, subscription in enumerate(subscriptions[2:], 1):
            successful_payment = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                stripe_invoice_id=f'inv_success{i}',
                invoice_number=f'INV-00000{i}-SUCCESS',
                amount_due=subscription.amount,
                amount_paid=subscription.amount,
                currency=subscription.currency,
                status='succeeded',
                paid=True,
                invoice_date=datetime.utcnow() - timedelta(days=30),
                due_date=datetime.utcnow() - timedelta(days=30),
                paid_date=datetime.utcnow() - timedelta(days=30),
                description=f'Monthly subscription fee - {subscription.pricing_tier.name}',
                invoice_type='recurring'
            )
            billing_records.append(successful_payment)
        
        for record in billing_records:
            self.db_session.add(record)
        self.db_session.commit()
        
        self.sample_customers = customers
        self.sample_subscriptions = subscriptions
        self.sample_billing_records = billing_records
        self.sample_tiers = [budget_tier, mid_tier, professional_tier]
    
    def demonstrate_trial_expiration_workflows(self):
        """Demonstrate trial expiration notifications"""
        print("\n=== Trial Expiration Workflows ===")
        
        trial_subscription = self.sample_subscriptions[0]
        customer = self.sample_customers[0]
        
        print(f"📊 Trial Subscription Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Trial start: {trial_subscription.trial_start.date()}")
        print(f"   Trial end: {trial_subscription.trial_end.date()}")
        print(f"   Days until expiry: {(trial_subscription.trial_end - datetime.utcnow()).days}")
        
        # Process trial expiration workflows
        print(f"\n🔄 Processing Trial Expiration Workflows:")
        trial_result = self.payment_service.process_trial_expiration_workflows()
        
        if trial_result['success']:
            results = trial_result['results']
            print(f"   ✅ Trial workflows processed successfully!")
            print(f"   Notifications sent: {results['notifications_sent']}")
            print(f"   Workflows created: {results['workflows_created']}")
            
            if results['errors']:
                print(f"   Errors encountered: {len(results['errors'])}")
                for error in results['errors'][:3]:
                    print(f"     ❌ {error}")
            
            # Show notification schedule
            print(f"\n📅 Trial Notification Schedule:")
            config = self.workflow_manager.workflow_config['trial_expiration']
            for notification in config['notifications']:
                print(f"   {notification['days_before']} days before expiry: {notification['template']}")
        else:
            print(f"   ❌ Trial workflows failed: {trial_result['error']}")
    
    def demonstrate_payment_recovery_workflows(self):
        """Demonstrate payment failure recovery"""
        print("\n=== Payment Recovery Workflows ===")
        
        failed_payment = self.sample_billing_records[0]
        customer = self.sample_customers[1]
        
        print(f"📊 Failed Payment Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Invoice: {failed_payment.invoice_number}")
        print(f"   Amount: ${failed_payment.amount_due}")
        print(f"   Status: {failed_payment.status}")
        print(f"   Retry count: {failed_payment.retry_count}")
        print(f"   Days since failure: {(datetime.utcnow() - failed_payment.invoice_date).days}")
        
        # Process payment recovery workflows
        print(f"\n🔄 Processing Payment Recovery Workflows:")
        recovery_result = self.payment_service.process_payment_recovery_workflows()
        
        if recovery_result['success']:
            results = recovery_result['results']
            print(f"   ✅ Payment recovery workflows processed successfully!")
            print(f"   Retry attempts: {results['retry_attempts']}")
            print(f"   Recoveries successful: {results['recoveries_successful']}")
            print(f"   Workflows created: {results['workflows_created']}")
            
            if results['errors']:
                print(f"   Errors encountered: {len(results['errors'])}")
                for error in results['errors'][:3]:
                    print(f"     ❌ {error}")
            
            # Show retry schedule
            print(f"\n📅 Payment Retry Schedule:")
            config = self.workflow_manager.workflow_config['payment_recovery']
            print(f"   Max retry attempts: {config['retry_attempts']}")
            print(f"   Retry schedule: {config['retry_schedule']} days after failure")
        else:
            print(f"   ❌ Payment recovery workflows failed: {recovery_result['error']}")
    
    def demonstrate_renewal_confirmation_workflows(self):
        """Demonstrate subscription renewal confirmations"""
        print("\n=== Renewal Confirmation Workflows ===")
        
        renewing_subscription = self.sample_subscriptions[2]
        customer = self.sample_customers[2]
        
        print(f"📊 Renewing Subscription Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Plan: {renewing_subscription.pricing_tier.name}")
        print(f"   Amount: ${renewing_subscription.amount}")
        print(f"   Current period: {renewing_subscription.current_period_start.date()} to {renewing_subscription.current_period_end.date()}")
        print(f"   Days until renewal: {(renewing_subscription.current_period_end - datetime.utcnow()).days}")
        
        # Process renewal confirmation workflows
        print(f"\n🔄 Processing Renewal Confirmation Workflows:")
        renewal_result = self.payment_service.process_renewal_confirmation_workflows()
        
        if renewal_result['success']:
            results = renewal_result['results']
            print(f"   ✅ Renewal confirmation workflows processed successfully!")
            print(f"   Confirmations sent: {results['confirmations_sent']}")
            print(f"   Workflows created: {results['workflows_created']}")
            
            if results['errors']:
                print(f"   Errors encountered: {len(results['errors'])}")
                for error in results['errors'][:3]:
                    print(f"     ❌ {error}")
            
            # Show renewal configuration
            print(f"\n📅 Renewal Configuration:")
            config = self.workflow_manager.workflow_config['renewal_confirmation']
            print(f"   Confirmation sent: {config['days_before']} days before renewal")
            print(f"   Enabled: {config['enabled']}")
        else:
            print(f"   ❌ Renewal confirmation workflows failed: {renewal_result['error']}")
    
    def demonstrate_upgrade_confirmation_workflows(self):
        """Demonstrate upgrade confirmation workflows"""
        print("\n=== Upgrade Confirmation Workflows ===")
        
        upgrade_subscription = self.sample_subscriptions[3]
        customer = self.sample_customers[3]
        new_tier = self.sample_tiers[1]  # Mid-Tier
        
        print(f"📊 Upgrade Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current plan: {upgrade_subscription.pricing_tier.name} (${upgrade_subscription.amount})")
        print(f"   New plan: {new_tier.name} (${new_tier.monthly_price})")
        print(f"   Price difference: ${new_tier.monthly_price - upgrade_subscription.amount}")
        
        # Calculate proration
        remaining_days = (upgrade_subscription.current_period_end - datetime.utcnow()).days
        proration_amount = ((new_tier.monthly_price - upgrade_subscription.amount) * remaining_days) / 30
        
        # Process upgrade confirmation workflow
        print(f"\n🔄 Processing Upgrade Confirmation Workflow:")
        upgrade_result = self.payment_service.process_upgrade_confirmation_workflow(
            subscription_id=upgrade_subscription.id,
            old_tier_name=upgrade_subscription.pricing_tier.name,
            new_tier_name=new_tier.name,
            proration_amount=proration_amount
        )
        
        if upgrade_result['success']:
            print(f"   ✅ Upgrade confirmation workflow processed successfully!")
            print(f"   Confirmation sent: {upgrade_result['confirmation_sent']}")
            
            # Show upgrade configuration
            print(f"\n📅 Upgrade Configuration:")
            config = self.workflow_manager.workflow_config['upgrade_confirmation']
            print(f"   Confirmation required: {config['confirmation_required']}")
            print(f"   Enabled: {config['enabled']}")
        else:
            print(f"   ❌ Upgrade confirmation workflow failed: {upgrade_result['error']}")
    
    def demonstrate_downgrade_confirmation_workflows(self):
        """Demonstrate downgrade confirmation workflows"""
        print("\n=== Downgrade Confirmation Workflows ===")
        
        downgrade_subscription = self.sample_subscriptions[3]  # Use same subscription
        customer = self.sample_customers[3]
        new_tier = self.sample_tiers[0]  # Budget tier
        
        print(f"📊 Downgrade Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current plan: {downgrade_subscription.pricing_tier.name} (${downgrade_subscription.amount})")
        print(f"   New plan: {new_tier.name} (${new_tier.monthly_price})")
        print(f"   Price difference: ${downgrade_subscription.amount - new_tier.monthly_price}")
        
        # Process downgrade confirmation workflow
        print(f"\n🔄 Processing Downgrade Confirmation Workflow:")
        downgrade_result = self.payment_service.process_downgrade_confirmation_workflow(
            subscription_id=downgrade_subscription.id,
            old_tier_name=downgrade_subscription.pricing_tier.name,
            new_tier_name=new_tier.name,
            effective_date='period_end'
        )
        
        if downgrade_result['success']:
            print(f"   ✅ Downgrade confirmation workflow processed successfully!")
            print(f"   Confirmation sent: {downgrade_result['confirmation_sent']}")
            
            # Show downgrade configuration
            print(f"\n📅 Downgrade Configuration:")
            config = self.workflow_manager.workflow_config['downgrade_confirmation']
            print(f"   Confirmation required: {config['confirmation_required']}")
            print(f"   Enabled: {config['enabled']}")
        else:
            print(f"   ❌ Downgrade confirmation workflow failed: {downgrade_result['error']}")
    
    def demonstrate_cancellation_retention_workflows(self):
        """Demonstrate cancellation surveys and retention offers"""
        print("\n=== Cancellation Retention Workflows ===")
        
        cancel_subscription = self.sample_subscriptions[4]
        customer = self.sample_customers[4]
        
        print(f"📊 Cancellation Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current plan: {cancel_subscription.pricing_tier.name}")
        print(f"   Monthly amount: ${cancel_subscription.amount}")
        print(f"   Subscription status: {cancel_subscription.status}")
        
        # Process cancellation retention workflow
        print(f"\n🔄 Processing Cancellation Retention Workflow:")
        retention_result = self.payment_service.process_cancellation_retention_workflow(
            subscription_id=cancel_subscription.id,
            cancellation_reason='Customer requested cancellation'
        )
        
        if retention_result['success']:
            results = retention_result['results']
            print(f"   ✅ Cancellation retention workflow processed successfully!")
            print(f"   Survey sent: {results['survey_sent']}")
            print(f"   Retention offers sent: {results['retention_offers_sent']}")
            print(f"   Workflow completed: {results['workflow_completed']}")
            
            # Show retention offers
            print(f"\n🎁 Retention Offers Available:")
            config = self.workflow_manager.workflow_config['cancellation_retention']
            for offer in config['retention_offers']:
                print(f"   {offer['description']}")
            
            # Show retention configuration
            print(f"\n📅 Retention Configuration:")
            print(f"   Survey enabled: {config['survey_enabled']}")
            print(f"   Retention offers: {len(config['retention_offers'])} available")
            print(f"   Enabled: {config['enabled']}")
        else:
            print(f"   ❌ Cancellation retention workflow failed: {retention_result['error']}")
    
    def demonstrate_workflow_analytics(self):
        """Demonstrate workflow analytics"""
        print("\n=== Workflow Analytics ===")
        
        # Get workflow analytics
        print(f"\n📊 Getting Workflow Analytics:")
        analytics_result = self.payment_service.get_workflow_analytics(
            period='monthly',
            workflow_type=None
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            print(f"   ✅ Workflow analytics retrieved successfully!")
            print(f"   Period: {analytics['period']}")
            print(f"   Total workflows: {analytics['total_workflows']}")
            print(f"   Success rate: {analytics['success_rate']:.1%}")
            
            # Show workflow types
            print(f"\n📈 Workflow Types:")
            for workflow_type, count in analytics['workflow_types'].items():
                print(f"   {workflow_type}: {count} workflows")
            
            # Show recent workflows
            print(f"\n🔄 Recent Workflows:")
            for workflow in analytics['recent_workflows'][:5]:
                print(f"   {workflow['timestamp']}: {workflow['workflow_type']} - {workflow['description']}")
        else:
            print(f"   ❌ Workflow analytics failed: {analytics_result['error']}")
    
    def demonstrate_workflow_configuration(self):
        """Demonstrate workflow configuration"""
        print("\n=== Workflow Configuration ===")
        
        # Configure trial expiration workflow
        print(f"\n⚙️ Configuring Trial Expiration Workflow:")
        trial_config = {
            'enabled': True,
            'notifications': [
                {'days_before': 3, 'template': 'trial_expiring_3_days'},
                {'days_before': 1, 'template': 'trial_expiring_1_day'},
                {'days_before': 0, 'template': 'trial_expired'}
            ]
        }
        
        config_result = self.payment_service.configure_workflow_settings(
            workflow_type='trial_expiration',
            settings=trial_config
        )
        
        if config_result['success']:
            print(f"   ✅ Trial expiration workflow configured successfully!")
            print(f"   Updated settings: {config_result['updated_settings']}")
        else:
            print(f"   ❌ Configuration failed: {config_result['error']}")
        
        # Configure payment recovery workflow
        print(f"\n⚙️ Configuring Payment Recovery Workflow:")
        payment_config = {
            'retry_attempts': 3,
            'retry_schedule': [0, 3, 7],
            'enabled': True
        }
        
        payment_config_result = self.payment_service.configure_workflow_settings(
            workflow_type='payment_recovery',
            settings=payment_config
        )
        
        if payment_config_result['success']:
            print(f"   ✅ Payment recovery workflow configured successfully!")
            print(f"   Updated settings: {payment_config_result['updated_settings']}")
        else:
            print(f"   ❌ Configuration failed: {payment_config_result['error']}")
    
    def demonstrate_complete_workflow_cycle(self):
        """Demonstrate complete automated workflow cycle"""
        print("\n=== Complete Automated Workflow Cycle ===")
        
        print(f"\n🔄 Running All Automated Workflows:")
        cycle_result = self.payment_service.run_all_automated_workflows()
        
        if cycle_result['success']:
            results = cycle_result['results']
            print(f"   ✅ Complete workflow cycle executed successfully!")
            print(f"   Total workflows: {results['total_workflows']}")
            print(f"   Total errors: {results['total_errors']}")
            
            # Show individual workflow results
            print(f"\n📊 Individual Workflow Results:")
            
            if 'trial_expiration' in results:
                trial_results = results['trial_expiration']['results']
                print(f"   Trial Expiration:")
                print(f"     Notifications sent: {trial_results['notifications_sent']}")
                print(f"     Workflows created: {trial_results['workflows_created']}")
            
            if 'payment_recovery' in results:
                payment_results = results['payment_recovery']['results']
                print(f"   Payment Recovery:")
                print(f"     Retry attempts: {payment_results['retry_attempts']}")
                print(f"     Recoveries successful: {payment_results['recoveries_successful']}")
            
            if 'renewal_confirmation' in results:
                renewal_results = results['renewal_confirmation']['results']
                print(f"   Renewal Confirmation:")
                print(f"     Confirmations sent: {renewal_results['confirmations_sent']}")
                print(f"     Workflows created: {renewal_results['workflows_created']}")
        else:
            print(f"   ❌ Complete workflow cycle failed: {cycle_result['error']}")
    
    def run_all_demonstrations(self):
        """Run all automated workflow demonstrations"""
        print("🚀 MINGUS Automated Workflows Demonstration")
        print("=" * 60)
        
        try:
            self.demonstrate_trial_expiration_workflows()
            self.demonstrate_payment_recovery_workflows()
            self.demonstrate_renewal_confirmation_workflows()
            self.demonstrate_upgrade_confirmation_workflows()
            self.demonstrate_downgrade_confirmation_workflows()
            self.demonstrate_cancellation_retention_workflows()
            self.demonstrate_workflow_analytics()
            self.demonstrate_workflow_configuration()
            self.demonstrate_complete_workflow_cycle()
            
            print("\n✅ All automated workflow demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = AutomatedWorkflowsExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 