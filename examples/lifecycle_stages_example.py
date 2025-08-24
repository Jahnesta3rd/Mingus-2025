"""
Lifecycle Stages Example for MINGUS
Demonstrates specific subscription lifecycle stages including active subscription,
upgrade/downgrade with proration, pause functionality, cancellation, and reactivation
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

class LifecycleStagesExample:
    """Example demonstrating specific subscription lifecycle stages"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_lifecycle_stages_example.db')
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
                stripe_customer_id='cus_active123',
                email='active.user@example.com',
                name='Active User',
                address={'country': 'US', 'state': 'CA'}
            ),
            Customer(
                user_id=2,
                stripe_customer_id='cus_upgrade123',
                email='upgrade.user@example.com',
                name='Upgrade User',
                address={'country': 'US', 'state': 'NY'}
            ),
            Customer(
                user_id=3,
                stripe_customer_id='cus_downgrade123',
                email='downgrade.user@example.com',
                name='Downgrade User',
                address={'country': 'US', 'state': 'TX'}
            ),
            Customer(
                user_id=4,
                stripe_customer_id='cus_pause123',
                email='pause.user@example.com',
                name='Pause User',
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
            # Active subscription (Budget tier)
            Subscription(
                customer_id=customers[0].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_active123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=15),
                current_period_end=datetime.utcnow() + timedelta(days=15),
                billing_cycle='monthly',
                amount=9.99,
                currency='USD'
            ),
            # Active subscription (Mid-tier) - for upgrade demo
            Subscription(
                customer_id=customers[1].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_upgrade123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=10),
                current_period_end=datetime.utcnow() + timedelta(days=20),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            # Active subscription (Professional) - for downgrade demo
            Subscription(
                customer_id=customers[2].id,
                pricing_tier_id=professional_tier.id,
                stripe_subscription_id='sub_downgrade123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=5),
                current_period_end=datetime.utcnow() + timedelta(days=25),
                billing_cycle='monthly',
                amount=99.99,
                currency='USD'
            ),
            # Active subscription - for pause demo
            Subscription(
                customer_id=customers[3].id,
                pricing_tier_id=mid_tier.id,
                stripe_subscription_id='sub_pause123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=12),
                current_period_end=datetime.utcnow() + timedelta(days=18),
                billing_cycle='monthly',
                amount=29.99,
                currency='USD'
            ),
            # Active subscription - for cancellation demo
            Subscription(
                customer_id=customers[4].id,
                pricing_tier_id=budget_tier.id,
                stripe_subscription_id='sub_cancel123',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=8),
                current_period_end=datetime.utcnow() + timedelta(days=22),
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
        self.sample_tiers = [budget_tier, mid_tier, professional_tier]
    
    def demonstrate_active_subscription(self):
        """Demonstrate active subscription management"""
        print("\n=== Active Subscription Management ===")
        
        active_subscription = self.sample_subscriptions[0]
        customer = self.sample_customers[0]
        
        print(f"📊 Active Subscription Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Subscription ID: {active_subscription.id}")
        print(f"   Current tier: {active_subscription.pricing_tier.name}")
        print(f"   Monthly amount: ${active_subscription.amount}")
        print(f"   Billing cycle: {active_subscription.billing_cycle}")
        print(f"   Period: {active_subscription.current_period_start.date()} to {active_subscription.current_period_end.date()}")
        
        # Get access status
        access_result = self.payment_service.get_subscription_access_status(
            subscription_id=active_subscription.id
        )
        
        if access_result['success']:
            access_status = access_result['access_status']
            print(f"\n🔐 Access Status:")
            print(f"   Has access: {access_status['has_access']}")
            print(f"   Access level: {access_status['access_level']}")
            print(f"   Access until: {access_status['access_until']}")
            
            if access_status['restrictions']:
                print(f"   Restrictions: {', '.join(access_status['restrictions'])}")
        
        # Get lifecycle status
        lifecycle_result = self.payment_service.get_subscription_lifecycle_status(
            subscription_id=active_subscription.id
        )
        
        if lifecycle_result['success']:
            lifecycle = lifecycle_result
            print(f"\n🔄 Lifecycle Status:")
            print(f"   Current state: {lifecycle['current_state']}")
            print(f"   Available transitions: {len(lifecycle['available_transitions'])}")
            
            for transition in lifecycle['available_transitions']:
                print(f"     → {transition['event']} -> {transition['new_state']}")
    
    def demonstrate_subscription_upgrade(self):
        """Demonstrate subscription upgrade with proration"""
        print("\n=== Subscription Upgrade with Proration ===")
        
        upgrade_subscription = self.sample_subscriptions[1]
        customer = self.sample_customers[1]
        new_tier = self.sample_tiers[2]  # Professional tier
        
        print(f"📈 Upgrade Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current tier: {upgrade_subscription.pricing_tier.name} (${upgrade_subscription.amount}/month)")
        print(f"   New tier: {new_tier.name} (${new_tier.monthly_price}/month)")
        print(f"   Price difference: ${new_tier.monthly_price - upgrade_subscription.amount}")
        
        # Calculate remaining days for proration
        remaining_days = (upgrade_subscription.current_period_end - datetime.utcnow()).days
        print(f"   Remaining days in period: {remaining_days}")
        
        # Perform upgrade
        print(f"\n🔄 Performing Upgrade:")
        upgrade_result = self.payment_service.upgrade_subscription(
            subscription_id=upgrade_subscription.id,
            new_tier_id=new_tier.id,
            proration_behavior='create_prorations'
        )
        
        if upgrade_result['success']:
            print(f"   ✅ Upgrade successful!")
            print(f"   Old state: {upgrade_result['old_state']}")
            print(f"   New state: {upgrade_result['new_state']}")
            
            metadata = upgrade_result['metadata']
            print(f"   Proration amount: ${metadata['proration_amount']}")
            print(f"   Proration behavior: {metadata['proration_behavior']}")
            print(f"   Upgrade date: {metadata['upgrade_date']}")
            
            # Show updated subscription details
            self.db_session.refresh(upgrade_subscription)
            print(f"\n📊 Updated Subscription:")
            print(f"   New amount: ${upgrade_subscription.amount}")
            print(f"   New tier: {upgrade_subscription.pricing_tier.name}")
        else:
            print(f"   ❌ Upgrade failed: {upgrade_result['error']}")
    
    def demonstrate_subscription_downgrade(self):
        """Demonstrate subscription downgrade with proration"""
        print("\n=== Subscription Downgrade with Proration ===")
        
        downgrade_subscription = self.sample_subscriptions[2]
        customer = self.sample_customers[2]
        new_tier = self.sample_tiers[0]  # Budget tier
        
        print(f"📉 Downgrade Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current tier: {downgrade_subscription.pricing_tier.name} (${downgrade_subscription.amount}/month)")
        print(f"   New tier: {new_tier.name} (${new_tier.monthly_price}/month)")
        print(f"   Price difference: ${downgrade_subscription.amount - new_tier.monthly_price}")
        
        # Calculate remaining days for proration
        remaining_days = (downgrade_subscription.current_period_end - datetime.utcnow()).days
        print(f"   Remaining days in period: {remaining_days}")
        
        # Perform immediate downgrade
        print(f"\n🔄 Performing Immediate Downgrade:")
        downgrade_result = self.payment_service.downgrade_subscription(
            subscription_id=downgrade_subscription.id,
            new_tier_id=new_tier.id,
            effective_date='immediate',
            proration_behavior='create_prorations'
        )
        
        if downgrade_result['success']:
            print(f"   ✅ Downgrade successful!")
            print(f"   Old state: {downgrade_result['old_state']}")
            print(f"   New state: {downgrade_result['new_state']}")
            
            metadata = downgrade_result['metadata']
            print(f"   Proration amount: ${metadata['proration_amount']}")
            print(f"   Proration behavior: {metadata['proration_behavior']}")
            print(f"   Effective date: {metadata['effective_date']}")
            print(f"   Downgrade date: {metadata['downgrade_date']}")
            
            # Show updated subscription details
            self.db_session.refresh(downgrade_subscription)
            print(f"\n📊 Updated Subscription:")
            print(f"   New amount: ${downgrade_subscription.amount}")
            print(f"   New tier: {downgrade_subscription.pricing_tier.name}")
        else:
            print(f"   ❌ Downgrade failed: {downgrade_result['error']}")
        
        # Demonstrate scheduled downgrade
        print(f"\n📅 Scheduling Downgrade for Period End:")
        schedule_result = self.payment_service.downgrade_subscription(
            subscription_id=downgrade_subscription.id,
            new_tier_id=new_tier.id,
            effective_date='period_end',
            proration_behavior='none'
        )
        
        if schedule_result['success']:
            print(f"   ✅ Downgrade scheduled!")
            metadata = schedule_result['metadata']
            print(f"   Effective date: {metadata['effective_date']}")
            print(f"   Scheduled date: {metadata['scheduled_date']}")
        else:
            print(f"   ❌ Schedule failed: {schedule_result['error']}")
    
    def demonstrate_subscription_pause(self):
        """Demonstrate subscription pause functionality"""
        print("\n=== Subscription Pause Functionality ===")
        
        pause_subscription = self.sample_subscriptions[3]
        customer = self.sample_customers[3]
        
        print(f"⏸️ Pause Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current tier: {pause_subscription.pricing_tier.name}")
        print(f"   Current status: {pause_subscription.status}")
        
        # Pause subscription
        print(f"\n🔄 Pausing Subscription:")
        pause_result = self.payment_service.pause_subscription(
            subscription_id=pause_subscription.id,
            pause_reason='Customer requested temporary pause',
            pause_duration_days=30
        )
        
        if pause_result['success']:
            print(f"   ✅ Pause successful!")
            print(f"   Old state: {pause_result['old_state']}")
            print(f"   New state: {pause_result['new_state']}")
            
            metadata = pause_result['metadata']
            print(f"   Pause reason: {metadata['pause_reason']}")
            print(f"   Pause duration: {metadata['pause_duration_days']} days")
            print(f"   Pause until: {metadata['pause_until']}")
            print(f"   Paused at: {metadata['paused_at']}")
            
            # Check access status after pause
            access_result = self.payment_service.get_subscription_access_status(
                subscription_id=pause_subscription.id
            )
            
            if access_result['success']:
                access_status = access_result['access_status']
                print(f"\n🔐 Access Status After Pause:")
                print(f"   Has access: {access_status['has_access']}")
                print(f"   Access level: {access_status['access_level']}")
                print(f"   Restrictions: {', '.join(access_status['restrictions'])}")
        else:
            print(f"   ❌ Pause failed: {pause_result['error']}")
        
        # Unpause subscription
        print(f"\n▶️ Unpausing Subscription:")
        unpause_result = self.payment_service.unpause_subscription(
            subscription_id=pause_subscription.id
        )
        
        if unpause_result['success']:
            print(f"   ✅ Unpause successful!")
            print(f"   Old state: {unpause_result['old_state']}")
            print(f"   New state: {unpause_result['new_state']}")
            
            metadata = unpause_result['metadata']
            print(f"   Pause duration: {metadata['pause_duration_days']} days")
            print(f"   Unpaused at: {metadata['unpaused_at']}")
            
            # Check access status after unpause
            access_result = self.payment_service.get_subscription_access_status(
                subscription_id=pause_subscription.id
            )
            
            if access_result['success']:
                access_status = access_result['access_status']
                print(f"\n🔐 Access Status After Unpause:")
                print(f"   Has access: {access_status['has_access']}")
                print(f"   Access level: {access_status['access_level']}")
        else:
            print(f"   ❌ Unpause failed: {unpause_result['error']}")
    
    def demonstrate_subscription_cancellation(self):
        """Demonstrate subscription cancellation with access until period end"""
        print("\n=== Subscription Cancellation ===")
        
        cancel_subscription = self.sample_subscriptions[4]
        customer = self.sample_customers[4]
        
        print(f"❌ Cancellation Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current tier: {cancel_subscription.pricing_tier.name}")
        print(f"   Current status: {cancel_subscription.status}")
        print(f"   Period end: {cancel_subscription.current_period_end.date()}")
        
        # Cancel at period end (maintain access)
        print(f"\n🔄 Canceling at Period End:")
        cancel_result = self.payment_service.cancel_subscription(
            subscription_id=cancel_subscription.id,
            effective_date='period_end',
            reason='Customer requested cancellation'
        )
        
        if cancel_result['success']:
            print(f"   ✅ Cancellation scheduled!")
            print(f"   Old state: {cancel_result['old_state']}")
            print(f"   New state: {cancel_result['new_state']}")
            
            metadata = cancel_result['metadata']
            print(f"   Effective date: {metadata['effective_date']}")
            print(f"   Reason: {metadata['reason']}")
            print(f"   Access until: {metadata['access_until']}")
            print(f"   Cancel requested at: {metadata['cancel_requested_at']}")
            
            # Check access status after cancellation request
            access_result = self.payment_service.get_subscription_access_status(
                subscription_id=cancel_subscription.id
            )
            
            if access_result['success']:
                access_status = access_result['access_status']
                print(f"\n🔐 Access Status After Cancellation Request:")
                print(f"   Has access: {access_status['has_access']}")
                print(f"   Access level: {access_status['access_level']}")
                print(f"   Access until: {access_status['access_until']}")
        else:
            print(f"   ❌ Cancellation failed: {cancel_result['error']}")
        
        # Demonstrate immediate cancellation
        print(f"\n⚡ Immediate Cancellation:")
        immediate_result = self.payment_service.cancel_subscription(
            subscription_id=cancel_subscription.id,
            effective_date='immediate',
            reason='Customer requested immediate cancellation',
            refund_amount=5.00
        )
        
        if immediate_result['success']:
            print(f"   ✅ Immediate cancellation successful!")
            metadata = immediate_result['metadata']
            print(f"   Effective date: {metadata['effective_date']}")
            print(f"   Refund amount: ${metadata['refund_amount']}")
            print(f"   Canceled at: {metadata['canceled_at']}")
        else:
            print(f"   ❌ Immediate cancellation failed: {immediate_result['error']}")
    
    def demonstrate_subscription_reactivation(self):
        """Demonstrate subscription reactivation"""
        print("\n=== Subscription Reactivation ===")
        
        # Use the canceled subscription from previous demo
        reactivate_subscription = self.sample_subscriptions[4]
        customer = self.sample_customers[4]
        
        print(f"🔄 Reactivation Details:")
        print(f"   Customer: {customer.name} ({customer.email})")
        print(f"   Current status: {reactivate_subscription.status}")
        
        # Check if subscription can be reactivated
        print(f"\n🔍 Checking Reactivation Eligibility:")
        lifecycle_result = self.payment_service.get_subscription_lifecycle_status(
            subscription_id=reactivate_subscription.id
        )
        
        if lifecycle_result['success']:
            lifecycle = lifecycle_result
            print(f"   Current state: {lifecycle['current_state']}")
            print(f"   Available transitions: {len(lifecycle['available_transitions'])}")
            
            for transition in lifecycle['available_transitions']:
                print(f"     → {transition['event']} -> {transition['new_state']}")
        
        # Reactivate subscription
        print(f"\n🔄 Reactivating Subscription:")
        reactivate_result = self.payment_service.reactivate_subscription(
            subscription_id=reactivate_subscription.id,
            payment_method_id='pm_reactivation123',
            restore_features=True
        )
        
        if reactivate_result['success']:
            print(f"   ✅ Reactivation successful!")
            print(f"   Old state: {reactivate_result['old_state']}")
            print(f"   New state: {reactivate_result['new_state']}")
            
            metadata = reactivate_result['metadata']
            print(f"   Payment method: {metadata['payment_method_id']}")
            print(f"   Restore features: {metadata['restore_features']}")
            print(f"   Reactivation date: {metadata['reactivation_date']}")
            print(f"   New billing period: {metadata['new_billing_period_start']} to {metadata['new_billing_period_end']}")
            
            # Check access status after reactivation
            access_result = self.payment_service.get_subscription_access_status(
                subscription_id=reactivate_subscription.id
            )
            
            if access_result['success']:
                access_status = access_result['access_status']
                print(f"\n🔐 Access Status After Reactivation:")
                print(f"   Has access: {access_status['has_access']}")
                print(f"   Access level: {access_status['access_level']}")
                print(f"   Access until: {access_status['access_until']}")
        else:
            print(f"   ❌ Reactivation failed: {reactivate_result['error']}")
    
    def demonstrate_complete_lifecycle_journey(self):
        """Demonstrate a complete subscription lifecycle journey"""
        print("\n=== Complete Subscription Lifecycle Journey ===")
        
        # Create a new subscription for the journey
        journey_customer = Customer(
            user_id=999,
            stripe_customer_id='cus_journey123',
            email='journey.user@example.com',
            name='Journey User',
            address={'country': 'US', 'state': 'CA'}
        )
        self.db_session.add(journey_customer)
        self.db_session.commit()
        
        journey_subscription = Subscription(
            customer_id=journey_customer.id,
            pricing_tier_id=self.sample_tiers[0].id,  # Start with Budget
            stripe_subscription_id='sub_journey123',
            status='draft',
            billing_cycle='monthly',
            amount=self.sample_tiers[0].monthly_price,
            currency='USD'
        )
        self.db_session.add(journey_subscription)
        self.db_session.commit()
        
        print(f"🚀 Starting Lifecycle Journey for {journey_customer.name}")
        print(f"   Initial state: {journey_subscription.status}")
        
        # 1. Activate subscription
        print(f"\n1️⃣ Activating Subscription:")
        activate_result = self.payment_service.activate_subscription(
            subscription_id=journey_subscription.id
        )
        if activate_result['success']:
            print(f"   ✅ Activated: {activate_result['old_state']} -> {activate_result['new_state']}")
        
        # 2. Upgrade subscription
        print(f"\n2️⃣ Upgrading to Mid-Tier:")
        upgrade_result = self.payment_service.upgrade_subscription(
            subscription_id=journey_subscription.id,
            new_tier_id=self.sample_tiers[1].id
        )
        if upgrade_result['success']:
            print(f"   ✅ Upgraded: {upgrade_result['old_state']} -> {upgrade_result['new_state']}")
            print(f"   Proration: ${upgrade_result['metadata']['proration_amount']}")
        
        # 3. Pause subscription
        print(f"\n3️⃣ Pausing Subscription:")
        pause_result = self.payment_service.pause_subscription(
            subscription_id=journey_subscription.id,
            pause_reason='Temporary pause for demonstration',
            pause_duration_days=7
        )
        if pause_result['success']:
            print(f"   ✅ Paused: {pause_result['old_state']} -> {pause_result['new_state']}")
        
        # 4. Unpause subscription
        print(f"\n4️⃣ Unpausing Subscription:")
        unpause_result = self.payment_service.unpause_subscription(
            subscription_id=journey_subscription.id
        )
        if unpause_result['success']:
            print(f"   ✅ Unpaused: {unpause_result['old_state']} -> {unpause_result['new_state']}")
        
        # 5. Downgrade subscription
        print(f"\n5️⃣ Downgrading to Budget:")
        downgrade_result = self.payment_service.downgrade_subscription(
            subscription_id=journey_subscription.id,
            new_tier_id=self.sample_tiers[0].id,
            effective_date='immediate'
        )
        if downgrade_result['success']:
            print(f"   ✅ Downgraded: {downgrade_result['old_state']} -> {downgrade_result['new_state']}")
            print(f"   Proration: ${downgrade_result['metadata']['proration_amount']}")
        
        # 6. Cancel subscription
        print(f"\n6️⃣ Canceling Subscription:")
        cancel_result = self.payment_service.cancel_subscription(
            subscription_id=journey_subscription.id,
            effective_date='period_end',
            reason='End of lifecycle journey'
        )
        if cancel_result['success']:
            print(f"   ✅ Canceled: {cancel_result['old_state']} -> {cancel_result['new_state']}")
        
        # 7. Reactivate subscription
        print(f"\n7️⃣ Reactivating Subscription:")
        reactivate_result = self.payment_service.reactivate_subscription(
            subscription_id=journey_subscription.id
        )
        if reactivate_result['success']:
            print(f"   ✅ Reactivated: {reactivate_result['old_state']} -> {reactivate_result['new_state']}")
        
        print(f"\n🎉 Complete lifecycle journey finished!")
        
        # Show final status
        final_status = self.payment_service.get_subscription_lifecycle_status(
            subscription_id=journey_subscription.id
        )
        if final_status['success']:
            print(f"   Final state: {final_status['current_state']}")
    
    def run_all_demonstrations(self):
        """Run all lifecycle stage demonstrations"""
        print("🚀 MINGUS Subscription Lifecycle Stages Demonstration")
        print("=" * 60)
        
        try:
            self.demonstrate_active_subscription()
            self.demonstrate_subscription_upgrade()
            self.demonstrate_subscription_downgrade()
            self.demonstrate_subscription_pause()
            self.demonstrate_subscription_cancellation()
            self.demonstrate_subscription_reactivation()
            self.demonstrate_complete_lifecycle_journey()
            
            print("\n✅ All lifecycle stage demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = LifecycleStagesExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 