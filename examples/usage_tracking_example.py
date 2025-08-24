"""
Usage Tracking Example for MINGUS
Demonstrates comprehensive usage tracking including feature monitoring, overage billing,
limit enforcement, and real-time updates
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.usage_tracker import UsageTracker
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, FeatureUsage

class UsageTrackingExample:
    """Example demonstrating comprehensive usage tracking"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_usage_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        self.usage_tracker = UsageTracker(self.db_session, self.config)
        
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
            )
        ]
        
        for subscription in subscriptions:
            self.db_session.add(subscription)
        self.db_session.commit()
        
        self.sample_customers = customers
        self.sample_subscriptions = subscriptions
    
    def demonstrate_feature_usage_monitoring(self):
        """Demonstrate feature usage monitoring"""
        print("\n=== Feature Usage Monitoring ===")
        
        # Track various feature usage for different customers
        usage_scenarios = [
            {'customer_id': 1, 'feature': 'health_checkins', 'quantity': 2, 'description': 'Budget user health check-ins'},
            {'customer_id': 1, 'feature': 'financial_reports', 'quantity': 1, 'description': 'Budget user financial report'},
            {'customer_id': 2, 'feature': 'health_checkins', 'quantity': 5, 'description': 'Mid-tier user health check-ins'},
            {'customer_id': 2, 'feature': 'ai_insights', 'quantity': 10, 'description': 'Mid-tier user AI insights'},
            {'customer_id': 3, 'feature': 'health_checkins', 'quantity': 20, 'description': 'Professional user health check-ins'},
            {'customer_id': 3, 'feature': 'ai_insights', 'quantity': 100, 'description': 'Professional user AI insights'}
        ]
        
        for scenario in usage_scenarios:
            customer = self.sample_customers[scenario['customer_id'] - 1]
            
            result = self.payment_service.track_feature_usage(
                customer_id=customer.id,
                feature_name=scenario['feature'],
                quantity=scenario['quantity'],
                metadata={'description': scenario['description']}
            )
            
            if result['success']:
                print(f"✅ {scenario['description']}: {result['current_usage']} used")
                if result.get('limit_warning'):
                    print(f"   ⚠️  Warning: {result['limit_warning']['severity']} - {result['limit_warning']['percentage_used']:.1f}% used")
            else:
                print(f"❌ {scenario['description']}: {result.get('error', 'Unknown error')}")
        
        # Try to exceed limits
        print("\n--- Testing Limit Enforcement ---")
        
        # Budget user trying to exceed health check-ins limit
        budget_customer = self.sample_customers[0]
        limit_test = self.payment_service.track_feature_usage(
            customer_id=budget_customer.id,
            feature_name='health_checkins',
            quantity=5  # This should exceed the 4 limit
        )
        
        if not limit_test['allowed']:
            print(f"✅ Limit enforcement working: Budget user blocked from exceeding health check-ins limit")
            print(f"   Current usage: {limit_test['limit_info']['current_usage']}")
            print(f"   Limit: {limit_test['limit_info']['limit']}")
            print(f"   Remaining: {limit_test['limit_info']['remaining']}")
    
    def demonstrate_usage_queries(self):
        """Demonstrate usage queries and reporting"""
        print("\n=== Usage Queries and Reporting ===")
        
        for i, customer in enumerate(self.sample_customers, 1):
            print(f"\nCustomer {i} ({customer.name} - {customer.email}):")
            
            # Get current usage
            usage_result = self.payment_service.get_feature_usage(customer.id)
            
            if usage_result['success']:
                usage_data = usage_result['usage']
                for feature, data in usage_data.items():
                    if data['limit'] > 0:  # Skip unlimited features
                        percentage = data['percentage_used']
                        status = "🟢" if percentage < 80 else "🟡" if percentage < 100 else "🔴"
                        print(f"   {status} {feature}: {data['current_usage']}/{data['limit']} ({percentage:.1f}%)")
                    elif data['limit'] == -1:
                        print(f"   ∞ {feature}: {data['current_usage']} (unlimited)")
            
            # Get specific feature usage
            health_usage = self.payment_service.get_feature_usage(
                customer.id, 
                feature_name='health_checkins'
            )
            
            if health_usage['success']:
                print(f"   Health check-ins: {health_usage['current_usage']}/{health_usage['limit']} ({health_usage['percentage_used']:.1f}%)")
    
    def demonstrate_overage_billing(self):
        """Demonstrate overage billing preparation"""
        print("\n=== Overage Billing Preparation ===")
        
        # Simulate high usage for mid-tier customer
        mid_customer = self.sample_customers[1]
        
        # Add more usage to trigger overage
        for _ in range(15):  # Add 15 more health check-ins (total 20, limit is 12)
            self.payment_service.track_feature_usage(
                customer_id=mid_customer.id,
                feature_name='health_checkins',
                quantity=1
            )
        
        for _ in range(15):  # Add 15 more AI insights (total 25, limit is 50)
            self.payment_service.track_feature_usage(
                customer_id=mid_customer.id,
                feature_name='ai_insights',
                quantity=1
            )
        
        # Calculate overage
        overage_result = self.payment_service.calculate_usage_overage(mid_customer.id)
        
        if overage_result['success']:
            print(f"✅ Overage calculation for {mid_customer.name}:")
            
            if overage_result['has_overage']:
                print(f"   Total overage amount: ${overage_result['total_overage_amount']:.2f}")
                
                for feature, overage_data in overage_result['overage_charges'].items():
                    print(f"   {feature}: {overage_data['overage_quantity']} over limit = ${overage_data['total_charge']:.2f}")
                
                # Generate overage invoice
                invoice_result = self.payment_service.generate_usage_overage_invoice(mid_customer.id)
                
                if invoice_result['success']:
                    print(f"   ✅ Overage invoice generated: {invoice_result['invoice_number']}")
                    print(f"   Amount: ${invoice_result['overage_amount']:.2f}")
            else:
                print("   No overage charges")
    
    def demonstrate_limit_enforcement(self):
        """Demonstrate usage limit enforcement"""
        print("\n=== Usage Limit Enforcement ===")
        
        # Test limit enforcement for different scenarios
        enforcement_tests = [
            {'customer_id': 1, 'feature': 'health_checkins', 'quantity': 1, 'expected': False},
            {'customer_id': 1, 'feature': 'ai_insights', 'quantity': 1, 'expected': False},
            {'customer_id': 2, 'feature': 'health_checkins', 'quantity': 1, 'expected': True},
            {'customer_id': 3, 'feature': 'health_checkins', 'quantity': 100, 'expected': True},  # Unlimited
        ]
        
        for test in enforcement_tests:
            customer = self.sample_customers[test['customer_id'] - 1]
            
            result = self.payment_service.enforce_usage_limits(
                customer_id=customer.id,
                feature_name=test['feature'],
                quantity=test['quantity']
            )
            
            status = "✅" if result['allowed'] == test['expected'] else "❌"
            print(f"{status} {customer.name} - {test['feature']}: {'Allowed' if result['allowed'] else 'Blocked'} (Expected: {'Allowed' if test['expected'] else 'Blocked'})")
            
            if not result['allowed']:
                print(f"   Reason: {result.get('reason', 'Unknown')}")
    
    def demonstrate_usage_alerts(self):
        """Demonstrate usage alerts"""
        print("\n=== Usage Alerts ===")
        
        for customer in self.sample_customers:
            alerts_result = self.payment_service.get_usage_alerts(
                customer_id=customer.id,
                threshold_percentage=80.0
            )
            
            if alerts_result['success']:
                print(f"\n{customer.name} alerts:")
                
                if alerts_result['alert_count'] > 0:
                    for alert in alerts_result['alerts']:
                        icon = "🔴" if alert['severity'] == 'critical' else "🟡"
                        print(f"   {icon} {alert['feature']}: {alert['percentage_used']:.1f}% used ({alert['remaining']} remaining)")
                else:
                    print("   🟢 No alerts - usage within limits")
    
    def demonstrate_real_time_updates(self):
        """Demonstrate real-time usage updates"""
        print("\n=== Real-Time Usage Updates ===")
        
        # Get real-time usage for each customer
        for customer in self.sample_customers:
            real_time_result = self.payment_service.get_real_time_usage(customer.id)
            
            if real_time_result['success']:
                data = real_time_result['data']
                print(f"\n{customer.name} - Real-time usage:")
                print(f"   Tier: {data['tier_name']} ({data['tier']})")
                print(f"   Last updated: {data['last_updated']}")
                
                for feature, usage_data in data['features'].items():
                    if usage_data['limit'] > 0:  # Skip unlimited features
                        status_icon = {
                            'within_limit': '🟢',
                            'approaching_limit': '🟡',
                            'limit_reached': '🔴',
                            'unlimited': '∞',
                            'not_available': '❌'
                        }.get(usage_data['status'], '❓')
                        
                        print(f"   {status_icon} {feature}: {usage_data['current_usage']}/{usage_data['limit']} ({usage_data['percentage_used']:.1f}%)")
        
        # Demonstrate real-time update
        print("\n--- Real-time Update Example ---")
        test_customer = self.sample_customers[1]
        
        # Update usage in real-time
        update_result = self.payment_service.update_usage_in_real_time(
            customer_id=test_customer.id,
            feature_name='api_calls',
            quantity=50,
            metadata={'source': 'example_demo', 'user_agent': 'demo_client'}
        )
        
        if update_result['success']:
            print(f"✅ Real-time update successful for {test_customer.name}")
            print(f"   API calls updated: +50")
            
            # Show updated real-time data
            if update_result['real_time_data']:
                api_calls_data = update_result['real_time_data']['features']['api_calls']
                print(f"   Current API calls: {api_calls_data['current_usage']}")
                print(f"   Status: {api_calls_data['status']}")
    
    def demonstrate_usage_dashboard(self):
        """Demonstrate comprehensive usage dashboard"""
        print("\n=== Usage Dashboard ===")
        
        for customer in self.sample_customers:
            dashboard_result = self.payment_service.get_usage_dashboard_data(customer.id)
            
            if dashboard_result['success']:
                data = dashboard_result['dashboard_data']
                print(f"\n📊 {customer.name} - Usage Dashboard:")
                print(f"   Last updated: {data['last_updated']}")
                
                # Show alerts
                if data['alerts']:
                    print(f"   ⚠️  Alerts ({len(data['alerts'])}):")
                    for alert in data['alerts']:
                        icon = "🔴" if alert['severity'] == 'critical' else "🟡"
                        print(f"     {icon} {alert['feature']}: {alert['percentage_used']:.1f}%")
                else:
                    print("   🟢 No alerts")
                
                # Show overage
                if data['overage']:
                    print(f"   💰 Overage charges: ${data['total_overage']:.2f}")
                    for feature, overage_data in data['overage'].items():
                        print(f"     {feature}: ${overage_data['total_charge']:.2f}")
                else:
                    print("   💚 No overage charges")
                
                # Show usage history
                if data['usage_history']:
                    print(f"   📈 Usage history ({len(data['usage_history'])} periods)")
                    latest = data['usage_history'][0]
                    print(f"     Latest: {latest['period']} - {latest['created_at']}")
    
    def demonstrate_usage_reset(self):
        """Demonstrate monthly usage reset"""
        print("\n=== Monthly Usage Reset ===")
        
        for subscription in self.sample_subscriptions:
            reset_result = self.payment_service.reset_monthly_usage(subscription.id)
            
            if reset_result['success']:
                if 'reset_date' in reset_result:
                    print(f"✅ Usage reset for subscription {subscription.id}")
                    print(f"   Reset date: {reset_result['reset_date']}")
                    print(f"   Period: {reset_result['month']}/{reset_result['year']}")
                else:
                    print(f"ℹ️  Subscription {subscription.id}: {reset_result['message']}")
            else:
                print(f"❌ Failed to reset usage for subscription {subscription.id}: {reset_result['error']}")
    
    def demonstrate_usage_history(self):
        """Demonstrate usage history tracking"""
        print("\n=== Usage History Tracking ===")
        
        for customer in self.sample_customers:
            history_result = self.payment_service.get_usage_history(
                customer_id=customer.id,
                days=30
            )
            
            if history_result['success']:
                print(f"\n📚 {customer.name} - Usage History:")
                print(f"   History periods: {len(history_result['history'])}")
                
                if history_result['history']:
                    latest = history_result['history'][0]
                    print(f"   Latest period: {latest['period']}")
                    print(f"   Last usage: {latest['last_usage_date']}")
                    
                    if 'usage' in latest and isinstance(latest['usage'], dict):
                        for feature, usage_count in latest['usage'].items():
                            if usage_count > 0:
                                print(f"     {feature}: {usage_count}")
    
    def run_all_demonstrations(self):
        """Run all usage tracking demonstrations"""
        print("🚀 MINGUS Usage Tracking Demonstration")
        print("=" * 50)
        
        try:
            self.demonstrate_feature_usage_monitoring()
            self.demonstrate_usage_queries()
            self.demonstrate_overage_billing()
            self.demonstrate_limit_enforcement()
            self.demonstrate_usage_alerts()
            self.demonstrate_real_time_updates()
            self.demonstrate_usage_dashboard()
            self.demonstrate_usage_reset()
            self.demonstrate_usage_history()
            
            print("\n✅ All usage tracking demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = UsageTrackingExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 