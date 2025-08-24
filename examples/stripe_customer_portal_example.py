"""
Stripe Customer Portal Integration Example for MINGUS
Demonstrates seamless handoff to Stripe for complex billing management
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.stripe_customer_portal import StripeCustomerPortal
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory

class StripeCustomerPortalExample:
    """Example demonstrating Stripe Customer Portal integration"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_stripe_portal_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.stripe_portal = StripeCustomerPortal(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for Stripe Customer Portal demonstration"""
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
        
        # Create sample customers with Stripe customer IDs
        customers = []
        for i in range(50):  # Create 50 customers for portal demonstration
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_portal_{i:04d}',  # Simulated Stripe customer ID
                email=f'portal.user{i}@example.com',
                name=f'Portal User {i}',
                address={
                    'country': 'US' if i < 30 else 'CA' if i < 40 else 'UK',
                    'state': 'CA' if i < 15 else 'NY' if i < 30 else 'ON' if i < 40 else 'London',
                    'city': 'San Francisco' if i < 15 else 'New York' if i < 30 else 'Toronto' if i < 40 else 'London',
                    'zip': '94105' if i < 15 else '10001' if i < 30 else 'M5V' if i < 40 else 'SW1A'
                },
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=365 - (i * 7))
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions for portal customers
        subscriptions = []
        billing_records = []
        
        for i, customer in enumerate(customers):
            # Assign different tiers
            if i < 20:
                tier = budget_tier
                amount = 15.00
            elif i < 35:
                tier = mid_tier
                amount = 35.00
            else:
                tier = professional_tier
                amount = 75.00
            
            subscription = Subscription(
                customer_id=customer.id,
                pricing_tier_id=tier.id,
                stripe_subscription_id=f'sub_portal_{i:04d}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 35 else 'annual',
                amount=amount,
                currency='USD'
            )
            subscriptions.append(subscription)
            
            # Create billing history
            billing_record = BillingHistory(
                customer_id=customer.id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-001',
                amount=amount,
                currency='USD',
                status='paid',
                description=f'Monthly payment - {tier.name}',
                created_at=datetime.utcnow() - timedelta(days=25),
                paid_at=datetime.utcnow() - timedelta(days=25),
                stripe_invoice_id=f'in_portal_{i:04d}_001'
            )
            billing_records.append(billing_record)
        
        self.db_session.add_all(subscriptions)
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_portal_session_creation(self):
        """Demonstrate creating Stripe Customer Portal sessions"""
        print("\n=== Stripe Customer Portal Session Creation ===")
        
        print(f"\n🔗 Testing Portal Session Creation:")
        
        # Test basic portal session creation
        print(f"\n1. Create Basic Portal Session:")
        customer = self.customers[0]
        session_result = self.stripe_portal.create_customer_portal_session(
            customer_id=customer.id,
            return_url="https://mingus.com/dashboard/billing"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Portal session created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   👤 Customer: {portal_session['customer']}")
            print(f"   📅 Created: {datetime.fromtimestamp(portal_session['created'])}")
            print(f"   ⏰ Expires: {datetime.fromtimestamp(portal_session['expires_at'])}")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
        
        # Test portal session with custom configuration
        print(f"\n2. Create Portal Session with Custom Configuration:")
        customer = self.customers[1]
        session_result = self.stripe_portal.create_customer_portal_session(
            customer_id=customer.id,
            return_url="https://mingus.com/dashboard/billing",
            configuration_id="bpc_1234567890"  # Example configuration ID
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Custom portal session created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   ⚙️ Configuration: {portal_session.get('configuration', 'default')}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
    
    def demonstrate_portal_configuration_management(self):
        """Demonstrate portal configuration management"""
        print("\n=== Portal Configuration Management ===")
        
        print(f"\n⚙️ Testing Portal Configuration Management:")
        
        # Test creating portal configuration
        print(f"\n1. Create Custom Portal Configuration:")
        config_result = self.stripe_portal.create_portal_configuration(
            configuration_name="MINGUS Enhanced Portal",
            features={
                'customer_update': {
                    'allowed_updates': ['address', 'shipping', 'tax_id'],
                    'enabled': True
                },
                'invoice_history': {
                    'enabled': True
                },
                'payment_method_update': {
                    'enabled': True
                },
                'subscription_cancel': {
                    'cancellation_reason': {
                        'enabled': True,
                        'options': [
                            'too_expensive',
                            'missing_features',
                            'switched_service',
                            'unused',
                            'customer_service',
                            'too_complex',
                            'low_quality',
                            'other'
                        ]
                    },
                    'enabled': True,
                    'mode': 'at_period_end',
                    'proration_behavior': 'create_prorations'
                },
                'subscription_pause': {
                    'enabled': True
                },
                'subscription_update': {
                    'default_allowed_updates': ['price', 'quantity', 'promotion_code'],
                    'enabled': True,
                    'proration_behavior': 'create_prorations'
                }
            }
        )
        
        if config_result['success']:
            configuration = config_result['configuration']
            print(f"   ✅ Portal configuration created successfully")
            print(f"   🆔 Configuration ID: {configuration['id']}")
            print(f"   📝 Name: {configuration['name']}")
            print(f"   📅 Created: {datetime.fromtimestamp(configuration['created'])}")
            print(f"   🏢 Business Profile:")
            print(f"      Headline: {configuration['business_profile']['headline']}")
            print(f"      Privacy Policy: {configuration['business_profile']['privacy_policy_url']}")
            print(f"      Terms of Service: {configuration['business_profile']['terms_of_service_url']}")
            print(f"      Support URL: {configuration['business_profile']['support_url']}")
            
            # Store configuration ID for later use
            self.configuration_id = configuration['id']
        else:
            print(f"   ❌ Failed: {config_result['error']}")
        
        # Test getting portal configurations
        print(f"\n2. Get All Portal Configurations:")
        configs_result = self.stripe_portal.get_portal_configurations()
        
        if configs_result['success']:
            configurations = configs_result['configurations']
            print(f"   ✅ Retrieved {configs_result['total_count']} portal configurations")
            for config in configurations[:3]:  # Show first 3 configurations
                print(f"   📋 Configuration: {config['name']}")
                print(f"      ID: {config['id']}")
                print(f"      Default: {config['is_default']}")
                print(f"      Created: {datetime.fromtimestamp(config['created'])}")
        else:
            print(f"   ❌ Failed: {configs_result['error']}")
        
        # Test updating portal configuration
        if hasattr(self, 'configuration_id'):
            print(f"\n3. Update Portal Configuration:")
            update_result = self.stripe_portal.update_portal_configuration(
                configuration_id=self.configuration_id,
                updates={
                    'business_profile': {
                        'headline': 'MINGUS - Advanced Financial Health Platform',
                        'privacy_policy_url': 'https://mingus.com/privacy/v2',
                        'terms_of_service_url': 'https://mingus.com/terms/v2',
                        'support_url': 'https://mingus.com/support/portal'
                    }
                }
            )
            
            if update_result['success']:
                configuration = update_result['configuration']
                print(f"   ✅ Portal configuration updated successfully")
                print(f"   📝 Updated Name: {configuration['name']}")
                print(f"   🏢 Updated Business Profile:")
                print(f"      Headline: {configuration['business_profile']['headline']}")
                print(f"      Privacy Policy: {configuration['business_profile']['privacy_policy_url']}")
            else:
                print(f"   ❌ Failed: {update_result['error']}")
    
    def demonstrate_limited_portal_access(self):
        """Demonstrate limited portal access for specific use cases"""
        print("\n=== Limited Portal Access ===")
        
        print(f"\n🔒 Testing Limited Portal Access:")
        
        # Test limited portal session for read-only access
        print(f"\n1. Create Read-Only Portal Session:")
        customer = self.customers[2]
        limited_session_result = self.stripe_portal.create_limited_portal_session(
            customer_id=customer.id,
            allowed_features=['invoice_history', 'customer_update'],
            return_url="https://mingus.com/dashboard/billing/readonly"
        )
        
        if limited_session_result['success']:
            portal_session = limited_session_result['portal_session']
            print(f"   ✅ Limited portal session created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🔒 Allowed Features: {', '.join(portal_session['allowed_features'])}")
            print(f"   📅 Expires: {datetime.fromtimestamp(portal_session['expires_at'])}")
        else:
            print(f"   ❌ Failed: {limited_session_result['error']}")
        
        # Test limited portal session for payment method updates only
        print(f"\n2. Create Payment Method Update Portal Session:")
        customer = self.customers[3]
        payment_session_result = self.stripe_portal.create_limited_portal_session(
            customer_id=customer.id,
            allowed_features=['payment_method_update'],
            return_url="https://mingus.com/dashboard/billing/payment"
        )
        
        if payment_session_result['success']:
            portal_session = payment_session_result['portal_session']
            print(f"   ✅ Payment portal session created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   💳 Allowed Features: {', '.join(portal_session['allowed_features'])}")
        else:
            print(f"   ❌ Failed: {payment_session_result['error']}")
    
    def demonstrate_portal_access_management(self):
        """Demonstrate portal access management and permissions"""
        print("\n=== Portal Access Management ===")
        
        print(f"\n🔐 Testing Portal Access Management:")
        
        # Test full portal access
        print(f"\n1. Full Portal Access:")
        customer = self.customers[4]
        access_result = self.stripe_portal.get_customer_portal_access(
            customer_id=customer.id,
            access_type='full'
        )
        
        if access_result['success']:
            portal_access = access_result['portal_access']
            print(f"   ✅ Portal access retrieved successfully")
            print(f"   👤 Customer ID: {portal_access['customer_id']}")
            print(f"   🆔 Stripe Customer ID: {portal_access['stripe_customer_id']}")
            print(f"   📊 Has Active Subscription: {portal_access['has_active_subscription']}")
            print(f"   📋 Subscription Status: {portal_access['subscription_status']}")
            print(f"   🔐 Access Type: {portal_access['access_type']}")
            print(f"   🔑 Permissions:")
            for permission, allowed in portal_access['permissions'].items():
                status = "✅" if allowed else "❌"
                print(f"      {status} {permission}: {allowed}")
        else:
            print(f"   ❌ Failed: {access_result['error']}")
        
        # Test limited portal access
        print(f"\n2. Limited Portal Access:")
        customer = self.customers[5]
        access_result = self.stripe_portal.get_customer_portal_access(
            customer_id=customer.id,
            access_type='limited'
        )
        
        if access_result['success']:
            portal_access = access_result['portal_access']
            print(f"   ✅ Limited portal access retrieved successfully")
            print(f"   🔐 Access Type: {portal_access['access_type']}")
            print(f"   🔑 Limited Permissions:")
            for permission, allowed in portal_access['permissions'].items():
                status = "✅" if allowed else "❌"
                print(f"      {status} {permission}: {allowed}")
        else:
            print(f"   ❌ Failed: {access_result['error']}")
    
    def demonstrate_webhook_handling(self):
        """Demonstrate webhook handling for portal events"""
        print("\n=== Portal Webhook Handling ===")
        
        print(f"\n🔄 Testing Portal Webhook Handling:")
        
        # Test customer.updated webhook
        print(f"\n1. Handle Customer Updated Webhook:")
        customer_updated_event = {
            'type': 'customer.updated',
            'data': {
                'object': {
                    'id': 'cus_portal_0001',
                    'email': 'updated.user1@example.com',
                    'name': 'Updated Portal User 1',
                    'address': {
                        'country': 'US',
                        'state': 'CA',
                        'city': 'San Francisco',
                        'line1': '123 Updated St',
                        'postal_code': '94105'
                    }
                }
            }
        }
        
        webhook_result = self.stripe_portal.handle_portal_webhook(customer_updated_event)
        if webhook_result['success']:
            print(f"   ✅ Customer updated webhook handled successfully")
            print(f"   📝 Message: {webhook_result['message']}")
        else:
            print(f"   ❌ Failed: {webhook_result['error']}")
        
        # Test invoice.payment_succeeded webhook
        print(f"\n2. Handle Invoice Payment Succeeded Webhook:")
        payment_succeeded_event = {
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_portal_0001_001',
                    'customer': 'cus_portal_0001',
                    'subscription': 'sub_portal_0001',
                    'amount_paid': 1500,
                    'currency': 'usd',
                    'status': 'paid'
                }
            }
        }
        
        webhook_result = self.stripe_portal.handle_portal_webhook(payment_succeeded_event)
        if webhook_result['success']:
            print(f"   ✅ Payment succeeded webhook handled successfully")
            print(f"   📝 Message: {webhook_result['message']}")
        else:
            print(f"   ❌ Failed: {webhook_result['error']}")
        
        # Test subscription.updated webhook
        print(f"\n3. Handle Subscription Updated Webhook:")
        subscription_updated_event = {
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_portal_0001',
                    'customer': 'cus_portal_0001',
                    'status': 'active',
                    'current_period_start': int(datetime.utcnow().timestamp()),
                    'current_period_end': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'items': {
                        'data': [{
                            'price': {
                                'unit_amount': 1500
                            }
                        }]
                    }
                }
            }
        }
        
        webhook_result = self.stripe_portal.handle_portal_webhook(subscription_updated_event)
        if webhook_result['success']:
            print(f"   ✅ Subscription updated webhook handled successfully")
            print(f"   📝 Message: {webhook_result['message']}")
        else:
            print(f"   ❌ Failed: {webhook_result['error']}")
    
    def demonstrate_portal_analytics(self):
        """Demonstrate portal analytics and usage insights"""
        print("\n=== Portal Analytics ===")
        
        print(f"\n📊 Testing Portal Analytics:")
        
        # Test portal analytics
        print(f"\n1. Portal Usage Analytics (30 days):")
        analytics_result = self.stripe_portal.get_portal_analytics(
            date_range='30d'
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            date_range = analytics_result['date_range']
            
            print(f"   ✅ Portal analytics retrieved successfully")
            print(f"   📅 Date Range: {date_range['start_date']} to {date_range['end_date']}")
            print(f"   📊 Analytics Summary:")
            print(f"      Total Sessions: {analytics['total_sessions']}")
            print(f"      Unique Customers: {analytics['unique_customers']}")
            print(f"      Average Session Duration: {analytics['session_duration']:.1f} minutes")
            
            # Feature usage
            feature_usage = analytics['feature_usage']
            print(f"   🔧 Feature Usage:")
            for feature, count in feature_usage.items():
                print(f"      {feature}: {count} uses")
            
            # Customer satisfaction
            satisfaction = analytics['customer_satisfaction']
            print(f"   😊 Customer Satisfaction:")
            for metric, score in satisfaction.items():
                print(f"      {metric}: {score}/5")
            
            # Common actions
            common_actions = analytics['common_actions']
            print(f"   🎯 Common Portal Actions:")
            for action in common_actions:
                print(f"      {action['action']}: {action['count']} times ({action['percentage']:.1f}%)")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
        
        # Test different date ranges
        print(f"\n2. Portal Analytics - Different Date Ranges:")
        date_ranges = ['7d', '30d', '90d', '1y']
        
        for date_range in date_ranges:
            analytics_result = self.stripe_portal.get_portal_analytics(
                date_range=date_range
            )
            
            if analytics_result['success']:
                analytics = analytics_result['analytics']
                print(f"   📊 {date_range}: {analytics['total_sessions']} sessions, {analytics['unique_customers']} unique customers")
            else:
                print(f"   ❌ {date_range}: Failed - {analytics_result['error']}")
    
    def demonstrate_integration_scenarios(self):
        """Demonstrate real-world integration scenarios"""
        print("\n=== Integration Scenarios ===")
        
        print(f"\n🌐 Testing Real-World Integration Scenarios:")
        
        # Scenario 1: Customer wants to update payment method
        print(f"\n1. Scenario: Customer Payment Method Update")
        customer = self.customers[6]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   💳 Need: Update payment method")
        
        # Create limited portal session for payment method update
        session_result = self.stripe_portal.create_limited_portal_session(
            customer_id=customer.id,
            allowed_features=['payment_method_update'],
            return_url="https://mingus.com/dashboard/billing/payment-updated"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Solution: Created payment method update portal session")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🔒 Limited to: Payment method updates only")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
        
        # Scenario 2: Customer wants to view billing history
        print(f"\n2. Scenario: Customer Billing History Review")
        customer = self.customers[7]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   📋 Need: View billing history and invoices")
        
        # Create limited portal session for billing history
        session_result = self.stripe_portal.create_limited_portal_session(
            customer_id=customer.id,
            allowed_features=['invoice_history', 'customer_update'],
            return_url="https://mingus.com/dashboard/billing/history"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Solution: Created billing history portal session")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🔒 Limited to: Invoice history and profile updates")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
        
        # Scenario 3: Customer wants to manage subscription
        print(f"\n3. Scenario: Customer Subscription Management")
        customer = self.customers[8]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   🔄 Need: Update subscription plan and payment method")
        
        # Create full portal session for subscription management
        session_result = self.stripe_portal.create_customer_portal_session(
            customer_id=customer.id,
            return_url="https://mingus.com/dashboard/billing/subscription-updated"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Solution: Created full subscription management portal session")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🔓 Full Access: All subscription and billing features")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
        
        # Scenario 4: Customer wants to cancel subscription
        print(f"\n4. Scenario: Customer Subscription Cancellation")
        customer = self.customers[9]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   ❌ Need: Cancel subscription with reason")
        
        # Create portal session with cancellation features
        session_result = self.stripe_portal.create_limited_portal_session(
            customer_id=customer.id,
            allowed_features=['subscription_cancel', 'invoice_history'],
            return_url="https://mingus.com/dashboard/billing/cancellation-survey"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Solution: Created cancellation portal session")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🔒 Limited to: Subscription cancellation and invoice history")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
            print(f"   📝 Note: Customer will be redirected to cancellation survey after portal")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
    
    def run_all_stripe_portal_demonstrations(self):
        """Run all Stripe Customer Portal demonstrations"""
        print("🚀 MINGUS Stripe Customer Portal Integration Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_portal_session_creation()
            self.demonstrate_portal_configuration_management()
            self.demonstrate_limited_portal_access()
            self.demonstrate_portal_access_management()
            self.demonstrate_webhook_handling()
            self.demonstrate_portal_analytics()
            self.demonstrate_integration_scenarios()
            
            print("\n✅ All Stripe Customer Portal demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = StripeCustomerPortalExample()
    example.run_all_stripe_portal_demonstrations()

if __name__ == "__main__":
    main() 