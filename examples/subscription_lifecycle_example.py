"""
Subscription Lifecycle Management Example for MINGUS
Demonstrates comprehensive subscription lifecycle management including state transitions,
lifecycle operations, automated processing, and analytics
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.subscription_lifecycle import SubscriptionLifecycleManager, SubscriptionState, LifecycleEvent
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory, FeatureUsage

class SubscriptionLifecycleExample:
    """Example demonstrating comprehensive subscription lifecycle management"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_lifecycle_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        self.lifecycle_manager = SubscriptionLifecycleManager(self.db_session, self.config)
        
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
                stripe_customer_id='cus_draft123',
                email='draft.user@example.com',
                name='Draft User',
                address={'country': 'US', 'state': 'CA'}
            ),
            Customer(
                user_id=2,
                stripe_customer_id='cus_trial123',
                email='trial.user@example.com',
                name='Trial User',
                address={'country': 'US', 'state': 'NY'}
            ),
            Customer(
                user_id=3,
                stripe_customer_id='cus_active123',
                email='active.user@example.com',
                name='Active User',
                address={'country': 'US', 'state': 'TX'}
            ),
            Customer(
                user_id=4,
                stripe_customer_id='cus_past_due123',
                email='pastdue.user@example.com',
                name='Past Due User',
                address={'country': 'US', 'state': 'FL'}
            ),
            Customer(
                user_id=5,
                stripe_customer_id='cus_canceling123',
                email='canceling.user@example.com',
                name='Canceling User',
                address={'country': 'US', 'state': 'WA'}
            ),
            Customer(
                user_id=6,
                stripe_customer_id='cus_canceled123',
                email='canceled.user@example.com',
                name='Canceled User',
                address={'country': 'US', 'state': 'OR'}
            )
        ]
        
        for customer in customers:
            self.db_session.add(customer)
        self.db_session.commit()
        
        # Create sample subscriptions in different states
        subscriptions = [
            # Draft subscription
            Subscription(
                customer_id=customers[0].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_draft123',
                status='draft',
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            ),
            # Trial subscription
            Subscription(
                customer_id=customers[1].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_trial123',
                status='trialing',
                trial_start=datetime.utcnow() - timedelta(days=10),
                trial_end=datetime.utcnow() + timedelta(days=4),
                current_period_start=datetime.utcnow() - timedelta(days=10),
                current_period_end=datetime.utcnow() + timedelta(days=4),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            # Active subscription
            Subscription(
                customer_id=customers[2].id,
                pricing_tier_id=professional_tier.id,
                stripe_subscription_id='sub_active123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=99.99,
                currency='USD'
            ),
            # Past due subscription
            Subscription(
                customer_id=customers[3].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_past_due123',
                status='past_due',
                current_period_start=datetime.utcnow() - timedelta(days=45),
                current_period_end=datetime.utcnow() - timedelta(days=15),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            ),
            # Canceling subscription
            Subscription(
                customer_id=customers[4].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_canceling123',
                status='canceling',
                cancel_at_period_end=True,
                current_period_start=datetime.utcnow() - timedelta(days=20),
                current_period_end=datetime.utcnow() + timedelta(days=10),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            # Canceled subscription
            Subscription(
                customer_id=customers[5].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_canceled123',
                status='canceled',
                canceled_at=datetime.utcnow() - timedelta(days=5),
                current_period_start=datetime.utcnow() - timedelta(days=35),
                current_period_end=datetime.utcnow() - timedelta(days=5),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            )
        ]
        
        for subscription in subscriptions:
            self.db_session.add(subscription)
        self.db_session.commit()
        
        self.sample_customers = customers
        self.sample_subscriptions = subscriptions
    
    def demonstrate_subscription_states_and_transitions(self):
        """Demonstrate subscription states and valid transitions"""
        print("\n=== Subscription States and Transitions ===")
        
        # Show all subscription states
        print("📋 All Subscription States:")
        for state in SubscriptionState:
            print(f"   {state.value}: {self._get_state_description(state)}")
        
        # Show current subscription states
        print(f"\n📊 Current Subscription States:")
        for subscription in self.sample_subscriptions:
            customer = next(c for c in self.sample_customers if c.id == subscription.customer_id)
            print(f"   {customer.name}: {subscription.status}")
        
        # Demonstrate state transitions
        print(f"\n🔄 State Transition Examples:")
        
        # Draft -> Pending Activation
        draft_subscription = self.sample_subscriptions[0]
        print(f"\n1. Draft -> Pending Activation:")
        print(f"   Subscription: {draft_subscription.id}")
        print(f"   Current state: {draft_subscription.status}")
        
        transition_result = self.payment_service.process_lifecycle_event(
            subscription_id=draft_subscription.id,
            event='subscription_created',
            metadata={'created_by': 'system'}
        )
        
        if transition_result['success']:
            print(f"   ✅ Transition successful: {transition_result['old_state']} -> {transition_result['new_state']}")
        else:
            print(f"   ❌ Transition failed: {transition_result['error']}")
        
        # Trial -> Active (conversion)
        trial_subscription = self.sample_subscriptions[1]
        print(f"\n2. Trial -> Active (Conversion):")
        print(f"   Subscription: {trial_subscription.id}")
        print(f"   Current state: {trial_subscription.status}")
        
        conversion_result = self.payment_service.convert_trial_to_paid(
            subscription_id=trial_subscription.id,
            payment_method_id='pm_trial_conversion123'
        )
        
        if conversion_result['success']:
            print(f"   ✅ Trial conversion successful: {conversion_result['old_state']} -> {conversion_result['new_state']}")
        else:
            print(f"   ❌ Trial conversion failed: {conversion_result['error']}")
        
        # Active -> Canceling
        active_subscription = self.sample_subscriptions[2]
        print(f"\n3. Active -> Canceling:")
        print(f"   Subscription: {active_subscription.id}")
        print(f"   Current state: {active_subscription.status}")
        
        cancel_result = self.payment_service.request_cancellation(
            subscription_id=active_subscription.id,
            effective_date='period_end',
            reason='User requested cancellation'
        )
        
        if cancel_result['success']:
            print(f"   ✅ Cancellation request successful: {cancel_result['old_state']} -> {cancel_result['new_state']}")
        else:
            print(f"   ❌ Cancellation request failed: {cancel_result['error']}")
    
    def demonstrate_lifecycle_operations(self):
        """Demonstrate lifecycle operations"""
        print("\n=== Lifecycle Operations ===")
        
        # Start trial for draft subscription
        draft_subscription = self.sample_subscriptions[0]
        print(f"\n🎯 Starting Trial:")
        print(f"   Subscription: {draft_subscription.id}")
        print(f"   Current state: {draft_subscription.status}")
        
        trial_result = self.payment_service.start_trial(
            subscription_id=draft_subscription.id,
            trial_days=14
        )
        
        if trial_result['success']:
            print(f"   ✅ Trial started: {trial_result['old_state']} -> {trial_result['new_state']}")
            print(f"   Trial period: {trial_result['metadata']['trial_days']} days")
        else:
            print(f"   ❌ Trial start failed: {trial_result['error']}")
        
        # Request reactivation for canceled subscription
        canceled_subscription = self.sample_subscriptions[5]
        print(f"\n🔄 Requesting Reactivation:")
        print(f"   Subscription: {canceled_subscription.id}")
        print(f"   Current state: {canceled_subscription.status}")
        
        reactivation_result = self.payment_service.request_reactivation(
            subscription_id=canceled_subscription.id,
            payment_method_id='pm_reactivation123'
        )
        
        if reactivation_result['success']:
            print(f"   ✅ Reactivation request successful: {reactivation_result['old_state']} -> {reactivation_result['new_state']}")
        else:
            print(f"   ❌ Reactivation request failed: {reactivation_result['error']}")
    
    def demonstrate_lifecycle_status_queries(self):
        """Demonstrate lifecycle status queries"""
        print("\n=== Lifecycle Status Queries ===")
        
        # Get lifecycle status for a subscription
        active_subscription = self.sample_subscriptions[2]
        print(f"\n📊 Lifecycle Status for Active Subscription:")
        print(f"   Subscription ID: {active_subscription.id}")
        
        status_result = self.payment_service.get_subscription_lifecycle_status(
            subscription_id=active_subscription.id
        )
        
        if status_result['success']:
            status = status_result
            print(f"   Current state: {status['current_state']}")
            print(f"   State info: {status['current_state_info']['status_description']}")
            print(f"   Available transitions: {len(status['available_transitions'])}")
            
            for transition in status['available_transitions'][:3]:  # Show first 3
                print(f"     → {transition['event']} -> {transition['new_state']}")
        else:
            print(f"   ❌ Status query failed: {status_result['error']}")
        
        # Get subscriptions by state
        print(f"\n📋 Subscriptions by State:")
        
        for state in ['active', 'trialing', 'canceled']:
            state_result = self.payment_service.get_subscriptions_by_state(
                state=state,
                include_inactive=False
            )
            
            if state_result['success']:
                print(f"   {state.capitalize()}: {state_result['count']} subscriptions")
                for sub in state_result['subscriptions'][:2]:  # Show first 2
                    print(f"     - ID {sub['subscription_id']}: ${sub['amount']} {sub['currency']}")
            else:
                print(f"   ❌ Query failed for {state}: {state_result['error']}")
    
    def demonstrate_automated_lifecycle_processing(self):
        """Demonstrate automated lifecycle processing"""
        print("\n=== Automated Lifecycle Processing ===")
        
        # Process automated lifecycle events
        print(f"\n🤖 Processing Automated Lifecycle Events:")
        
        automation_result = self.payment_service.process_automated_lifecycle_events()
        
        if automation_result['success']:
            results = automation_result['results']
            print(f"   Events processed: {results['events_processed']}")
            print(f"   Subscriptions updated: {results['subscriptions_updated']}")
            
            if results['errors']:
                print(f"   Errors encountered: {len(results['errors'])}")
                for error in results['errors'][:3]:  # Show first 3 errors
                    print(f"     ❌ {error}")
            else:
                print(f"   ✅ No errors encountered")
        else:
            print(f"   ❌ Automation failed: {automation_result['error']}")
        
        # Show what automated processing does
        print(f"\n📋 Automated Processing Tasks:")
        print(f"   • Trial ending notifications")
        print(f"   • Grace period management")
        print(f"   • Scheduled cancellation processing")
        print(f"   • Subscription expiration handling")
        print(f"   • Payment failure escalations")
    
    def demonstrate_lifecycle_analytics(self):
        """Demonstrate lifecycle analytics"""
        print("\n=== Lifecycle Analytics ===")
        
        # Get lifecycle analytics
        print(f"\n📊 Lifecycle Analytics:")
        
        analytics_result = self.payment_service.get_lifecycle_analytics(
            period='monthly',
            include_transitions=True
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            
            print(f"   Total subscriptions: {analytics['total_subscriptions']}")
            print(f"   Period: {analytics['period']}")
            
            metrics = analytics['metrics']
            print(f"\n📈 Key Metrics:")
            print(f"   Activation rate: {metrics['activation_rate']:.1f}%")
            print(f"   Trial conversion rate: {metrics['trial_conversion_rate']:.1f}%")
            print(f"   Churn rate: {metrics['churn_rate']:.1f}%")
            print(f"   Active subscriptions: {metrics['active_subscriptions']}")
            print(f"   Trial subscriptions: {metrics['trial_subscriptions']}")
            print(f"   Canceled subscriptions: {metrics['canceled_subscriptions']}")
            
            # Show state distribution
            print(f"\n📊 State Distribution:")
            state_dist = analytics['state_distribution']
            for state, count in state_dist.items():
                if count > 0:
                    percentage = (count / analytics['total_subscriptions']) * 100
                    print(f"   {state}: {count} ({percentage:.1f}%)")
            
            # Show transition data
            if 'transitions' in analytics:
                transitions = analytics['transitions']
                print(f"\n🔄 Transition Analysis:")
                print(f"   Total transitions: {transitions['total_transitions']}")
                
                if transitions['transition_types']:
                    print(f"   Common transition types:")
                    for transition_type, count in list(transitions['transition_types'].items())[:5]:
                        print(f"     {transition_type}: {count}")
        else:
            print(f"   ❌ Analytics failed: {analytics_result['error']}")
    
    def demonstrate_lifecycle_workflows(self):
        """Demonstrate complete lifecycle workflows"""
        print("\n=== Lifecycle Workflows ===")
        
        # Complete subscription lifecycle workflow
        print(f"\n🔄 Complete Subscription Lifecycle Workflow:")
        
        # 1. Create subscription (Draft)
        print(f"\n1️⃣ Draft State:")
        draft_sub = self.sample_subscriptions[0]
        print(f"   Created subscription {draft_sub.id} in draft state")
        
        # 2. Start trial
        print(f"\n2️⃣ Trial State:")
        trial_result = self.payment_service.start_trial(
            subscription_id=draft_sub.id,
            trial_days=7
        )
        if trial_result['success']:
            print(f"   ✅ Started trial: {trial_result['old_state']} -> {trial_result['new_state']}")
        
        # 3. Convert to active
        print(f"\n3️⃣ Active State:")
        conversion_result = self.payment_service.convert_trial_to_paid(
            subscription_id=draft_sub.id,
            payment_method_id='pm_conversion123'
        )
        if conversion_result['success']:
            print(f"   ✅ Converted to active: {conversion_result['old_state']} -> {conversion_result['new_state']}")
        
        # 4. Request cancellation
        print(f"\n4️⃣ Canceling State:")
        cancel_result = self.payment_service.request_cancellation(
            subscription_id=draft_sub.id,
            effective_date='period_end',
            reason='Workflow demonstration'
        )
        if cancel_result['success']:
            print(f"   ✅ Requested cancellation: {cancel_result['old_state']} -> {cancel_result['new_state']}")
        
        # 5. Complete cancellation
        print(f"\n5️⃣ Canceled State:")
        complete_result = self.payment_service.process_lifecycle_event(
            subscription_id=draft_sub.id,
            event='cancellation_completed'
        )
        if complete_result['success']:
            print(f"   ✅ Completed cancellation: {complete_result['old_state']} -> {complete_result['new_state']}")
        
        print(f"\n✅ Complete lifecycle workflow demonstrated!")
    
    def run_all_demonstrations(self):
        """Run all subscription lifecycle demonstrations"""
        print("🚀 MINGUS Subscription Lifecycle Management Demonstration")
        print("=" * 60)
        
        try:
            self.demonstrate_subscription_states_and_transitions()
            self.demonstrate_lifecycle_operations()
            self.demonstrate_lifecycle_status_queries()
            self.demonstrate_automated_lifecycle_processing()
            self.demonstrate_lifecycle_analytics()
            self.demonstrate_lifecycle_workflows()
            
            print("\n✅ All subscription lifecycle demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()
    
    def _get_state_description(self, state: SubscriptionState) -> str:
        """Get human-readable description of a state"""
        descriptions = {
            SubscriptionState.DRAFT: "Draft subscription being created",
            SubscriptionState.PENDING_ACTIVATION: "Waiting for activation",
            SubscriptionState.TRIALING: "In free trial period",
            SubscriptionState.ACTIVE: "Active and billing",
            SubscriptionState.PAST_DUE: "Payment failed, in grace period",
            SubscriptionState.UNPAID: "Payment failed, access suspended",
            SubscriptionState.SUSPENDED: "Temporarily suspended",
            SubscriptionState.CANCELING: "Cancellation in progress",
            SubscriptionState.CANCELED: "Subscription canceled",
            SubscriptionState.REACTIVATING: "Reactivation in progress",
            SubscriptionState.ERROR: "System error state",
            SubscriptionState.EXPIRED: "Subscription expired"
        }
        
        return descriptions.get(state, state.value)

def main():
    """Main function to run the demonstration"""
    example = SubscriptionLifecycleExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 