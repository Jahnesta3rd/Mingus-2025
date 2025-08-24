"""
Enhanced Stripe Customer Portal Integration Example for MINGUS
Demonstrates comprehensive portal integration with:
- Return handling from Stripe portal
- Synchronized data between portals
- Custom branding and messaging
- Workflow-based portal sessions
- Analytics and insights
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory

class EnhancedStripePortalIntegrationExample:
    """Example demonstrating enhanced Stripe Customer Portal integration"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_enhanced_portal_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for enhanced portal demonstration"""
        print("📊 Creating sample data for enhanced portal demonstration...")
        
        # Create pricing tiers
        tiers = [
            PricingTier(
                name="Budget Tier",
                monthly_price=15.00,
                yearly_price=150.00,
                stripe_price_id_monthly="price_budget_monthly",
                stripe_price_id_yearly="price_budget_yearly",
                features=["basic_budgeting", "expense_tracking", "financial_goals"]
            ),
            PricingTier(
                name="Mid-Tier",
                monthly_price=35.00,
                yearly_price=350.00,
                stripe_price_id_monthly="price_mid_monthly",
                stripe_price_id_yearly="price_mid_yearly",
                features=["advanced_budgeting", "investment_tracking", "tax_planning", "debt_management"]
            ),
            PricingTier(
                name="Professional Tier",
                monthly_price=75.00,
                yearly_price=720.00,
                stripe_price_id_monthly="price_pro_monthly",
                stripe_price_id_yearly="price_pro_yearly",
                features=["comprehensive_financial_planning", "estate_planning", "business_finances", "wealth_management"]
            )
        ]
        
        for tier in tiers:
            self.db_session.add(tier)
        self.db_session.commit()
        
        # Create customers with different scenarios
        self.customers = []
        customer_scenarios = [
            {
                'name': 'Enhanced Portal User 1',
                'email': 'enhanced.user1@example.com',
                'stripe_customer_id': 'cus_enhanced_0001',
                'scenario': 'payment_update_needed'
            },
            {
                'name': 'Enhanced Portal User 2',
                'email': 'enhanced.user2@example.com',
                'stripe_customer_id': 'cus_enhanced_0002',
                'scenario': 'subscription_management'
            },
            {
                'name': 'Enhanced Portal User 3',
                'email': 'enhanced.user3@example.com',
                'stripe_customer_id': 'cus_enhanced_0003',
                'scenario': 'billing_review'
            },
            {
                'name': 'Enhanced Portal User 4',
                'email': 'enhanced.user4@example.com',
                'stripe_customer_id': 'cus_enhanced_0004',
                'scenario': 'cancellation_process'
            },
            {
                'name': 'Enhanced Portal User 5',
                'email': 'enhanced.user5@example.com',
                'stripe_customer_id': 'cus_enhanced_0005',
                'scenario': 'profile_update'
            }
        ]
        
        for i, scenario in enumerate(customer_scenarios):
            customer = Customer(
                name=scenario['name'],
                email=scenario['email'],
                stripe_customer_id=scenario['stripe_customer_id'],
                phone=f"+1-555-{1000+i:04d}",
                address={
                    'country': 'US',
                    'state': 'CA',
                    'city': 'San Francisco',
                    'line1': f'{1000+i} Enhanced St',
                    'postal_code': '94105'
                }
            )
            self.db_session.add(customer)
            self.customers.append(customer)
        
        self.db_session.commit()
        print(f"✅ Created {len(self.customers)} customers with different portal scenarios")
    
    def demonstrate_enhanced_portal_session_creation(self):
        """Demonstrate enhanced portal session creation with custom branding"""
        print("\n=== Enhanced Portal Session Creation ===")
        
        print(f"\n🔗 Testing Enhanced Portal Session Creation:")
        
        # Test 1: Payment Update Workflow with Custom Branding
        print(f"\n1. Create Payment Update Workflow with Custom Branding:")
        customer = self.customers[0]
        
        session_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='payment_update',
            return_url="https://mingus.com/dashboard/billing/payment-updated"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Payment update workflow created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🔄 Workflow Type: {session_result['workflow_type']}")
            print(f"   📝 Description: {session_result['description']}")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
        
        # Test 2: Subscription Management with Custom Configuration
        print(f"\n2. Create Subscription Management with Custom Configuration:")
        customer = self.customers[1]
        
        custom_config_result = self.payment_service.create_portal_configuration(
            configuration_name="MINGUS Enhanced Subscription Management",
            features={
                'subscription_update': {
                    'enabled': True,
                    'default_allowed_updates': ['price', 'quantity', 'promotion_code'],
                    'proration_behavior': 'create_prorations'
                },
                'subscription_cancel': {
                    'enabled': True,
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
                    }
                },
                'invoice_history': {
                    'enabled': True
                },
                'payment_method_update': {
                    'enabled': True
                }
            }
        )
        
        if custom_config_result['success']:
            config_id = custom_config_result['configuration']['id']
            
            session_result = self.payment_service.create_stripe_portal_session(
                customer_id=customer.id,
                return_url="https://mingus.com/dashboard/billing/subscription-updated",
                configuration_id=config_id
            )
            
            if session_result['success']:
                portal_session = session_result['portal_session']
                print(f"   ✅ Custom subscription management portal created")
                print(f"   🆔 Session ID: {portal_session['id']}")
                print(f"   🔗 Portal URL: {portal_session['url']}")
                print(f"   ⚙️ Configuration ID: {config_id}")
                print(f"   🔙 Return URL: {portal_session['return_url']}")
            else:
                print(f"   ❌ Failed: {session_result['error']}")
        else:
            print(f"   ❌ Failed to create custom configuration: {custom_config_result['error']}")
        
        # Test 3: Billing Review Workflow
        print(f"\n3. Create Billing Review Workflow:")
        customer = self.customers[2]
        
        session_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='billing_review',
            return_url="https://mingus.com/dashboard/billing/history"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Billing review workflow created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🔄 Workflow Type: {session_result['workflow_type']}")
            print(f"   📝 Description: {session_result['description']}")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
    
    def demonstrate_portal_return_handling(self):
        """Demonstrate portal return handling with data synchronization"""
        print("\n=== Portal Return Handling ===")
        
        print(f"\n🔄 Testing Portal Return Handling:")
        
        # Test 1: Payment Method Updated Return
        print(f"\n1. Handle Payment Method Updated Return:")
        customer = self.customers[0]
        
        sync_result = self.payment_service.synchronize_portal_data(
            customer_id=customer.stripe_customer_id,
            session_id="bps_payment_update_001",
            action="payment_updated"
        )
        
        if sync_result['success']:
            synchronized_data = sync_result['synchronized_data']
            print(f"   ✅ Payment method update return handled successfully")
            print(f"   📊 Synchronized Data:")
            print(f"      • Customer Updated: {synchronized_data['customer_updated']}")
            print(f"      • Subscription Changed: {synchronized_data['subscription_changed']}")
            print(f"      • Payment Method Updated: {synchronized_data['payment_method_updated']}")
            print(f"   📝 Changes: {len(synchronized_data['changes'])} changes detected")
            for change in synchronized_data['changes']:
                print(f"      - {change}")
            print(f"   🔗 Redirect URL: {sync_result['redirect_url']}")
        else:
            print(f"   ❌ Failed: {sync_result['error']}")
        
        # Test 2: Subscription Changed Return
        print(f"\n2. Handle Subscription Changed Return:")
        customer = self.customers[1]
        
        sync_result = self.payment_service.synchronize_portal_data(
            customer_id=customer.stripe_customer_id,
            session_id="bps_subscription_001",
            action="subscription_changed"
        )
        
        if sync_result['success']:
            synchronized_data = sync_result['synchronized_data']
            print(f"   ✅ Subscription change return handled successfully")
            print(f"   📊 Synchronized Data:")
            print(f"      • Customer Updated: {synchronized_data['customer_updated']}")
            print(f"      • Subscription Changed: {synchronized_data['subscription_changed']}")
            print(f"      • Payment Method Updated: {synchronized_data['payment_method_updated']}")
            print(f"   📝 Changes: {len(synchronized_data['changes'])} changes detected")
            for change in synchronized_data['changes']:
                print(f"      - {change}")
            print(f"   🔗 Redirect URL: {sync_result['redirect_url']}")
        else:
            print(f"   ❌ Failed: {sync_result['error']}")
        
        # Test 3: Profile Updated Return
        print(f"\n3. Handle Profile Updated Return:")
        customer = self.customers[4]
        
        sync_result = self.payment_service.synchronize_portal_data(
            customer_id=customer.stripe_customer_id,
            session_id="bps_profile_001",
            action="profile_updated"
        )
        
        if sync_result['success']:
            synchronized_data = sync_result['synchronized_data']
            print(f"   ✅ Profile update return handled successfully")
            print(f"   📊 Synchronized Data:")
            print(f"      • Customer Updated: {synchronized_data['customer_updated']}")
            print(f"      • Subscription Changed: {synchronized_data['subscription_changed']}")
            print(f"      • Payment Method Updated: {synchronized_data['payment_method_updated']}")
            print(f"   📝 Changes: {len(synchronized_data['changes'])} changes detected")
            for change in synchronized_data['changes']:
                print(f"      - {change}")
            print(f"   🔗 Redirect URL: {sync_result['redirect_url']}")
        else:
            print(f"   ❌ Failed: {sync_result['error']}")
    
    def demonstrate_custom_branding(self):
        """Demonstrate custom branding and messaging"""
        print("\n=== Custom Branding and Messaging ===")
        
        print(f"\n🎨 Testing Custom Branding:")
        
        # Test 1: Apply Custom Branding to Portal Configuration
        print(f"\n1. Apply Custom Branding to Portal Configuration:")
        
        custom_branding = {
            'company_name': 'MINGUS Financial Excellence',
            'logo_url': 'https://mingus.com/assets/logo-enhanced.png',
            'primary_color': '#1e40af',
            'secondary_color': '#3b82f6',
            'privacy_policy_url': 'https://mingus.com/privacy-enhanced',
            'terms_of_service_url': 'https://mingus.com/terms-enhanced',
            'support_url': 'https://mingus.com/support-enhanced'
        }
        
        # Create a new configuration with custom branding
        config_result = self.payment_service.create_portal_configuration(
            configuration_name="MINGUS Branded Portal",
            features={
                'customer_update': {
                    'enabled': True,
                    'allowed_updates': ['address', 'shipping', 'tax_id', 'phone']
                },
                'subscription_update': {
                    'enabled': True,
                    'default_allowed_updates': ['price', 'quantity']
                },
                'invoice_history': {
                    'enabled': True
                }
            }
        )
        
        if config_result['success']:
            config_id = config_result['configuration']['id']
            
            # Apply custom branding
            branding_result = self.payment_service.apply_custom_portal_branding(
                session_or_config_id=config_id,
                branding=custom_branding
            )
            
            if branding_result['success']:
                print(f"   ✅ Custom branding applied successfully")
                print(f"   🎨 Company Name: {custom_branding['company_name']}")
                print(f"   🖼️ Logo URL: {custom_branding['logo_url']}")
                print(f"   🎨 Primary Color: {custom_branding['primary_color']}")
                print(f"   🎨 Secondary Color: {custom_branding['secondary_color']}")
                print(f"   📄 Privacy Policy: {custom_branding['privacy_policy_url']}")
                print(f"   📄 Terms of Service: {custom_branding['terms_of_service_url']}")
                print(f"   🆘 Support URL: {custom_branding['support_url']}")
            else:
                print(f"   ❌ Failed to apply branding: {branding_result['error']}")
        else:
            print(f"   ❌ Failed to create configuration: {config_result['error']}")
        
        # Test 2: Create Portal Session with Custom Branding
        print(f"\n2. Create Portal Session with Custom Branding:")
        customer = self.customers[2]
        
        session_result = self.payment_service.create_stripe_portal_session(
            customer_id=customer.id,
            return_url="https://mingus.com/dashboard/billing/branded",
            configuration_id=config_id if config_result['success'] else None
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Branded portal session created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   🎨 Custom Branding: Applied")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
    
    def demonstrate_portal_analytics(self):
        """Demonstrate portal analytics and insights"""
        print("\n=== Portal Analytics and Insights ===")
        
        print(f"\n📊 Testing Portal Analytics:")
        
        # Test 1: Get Portal Analytics
        print(f"\n1. Get Portal Analytics:")
        
        analytics_result = self.payment_service.get_portal_analytics(
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )
        
        if analytics_result['success']:
            analytics = analytics_result['analytics']
            print(f"   ✅ Portal analytics retrieved successfully")
            print(f"   📈 Total Sessions: {analytics['total_sessions']}")
            print(f"   👥 Unique Customers: {analytics['unique_customers']}")
            print(f"   📊 Return Rate: {analytics['return_rate']:.2%}")
            print(f"   ⏱️ Average Session Duration: {analytics['session_duration_stats']['average_duration_minutes']} minutes")
            print(f"   📅 Period: {analytics['period']['start_date']} to {analytics['period']['end_date']}")
            
            if analytics['most_used_features']:
                print(f"   🔥 Most Used Features:")
                for feature, count in analytics['most_used_features']:
                    print(f"      • {feature}: {count} uses")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
        
        # Test 2: Get Customer-Specific Analytics
        print(f"\n2. Get Customer-Specific Analytics:")
        customer = self.customers[0]
        
        customer_analytics_result = self.payment_service.get_portal_analytics(
            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            customer_id=customer.stripe_customer_id
        )
        
        if customer_analytics_result['success']:
            analytics = customer_analytics_result['analytics']
            print(f"   ✅ Customer analytics retrieved successfully")
            print(f"   👤 Customer: {customer.name}")
            print(f"   📈 Total Sessions: {analytics['total_sessions']}")
            print(f"   📊 Return Rate: {analytics['return_rate']:.2%}")
            print(f"   📅 Period: {analytics['period']['start_date']} to {analytics['period']['end_date']}")
        else:
            print(f"   ❌ Failed: {customer_analytics_result['error']}")
    
    def demonstrate_workflow_scenarios(self):
        """Demonstrate different workflow scenarios"""
        print("\n=== Workflow Scenarios ===")
        
        print(f"\n🔄 Testing Different Workflow Scenarios:")
        
        workflows = [
            {
                'name': 'Payment Update Workflow',
                'type': 'payment_update',
                'customer': self.customers[0],
                'description': 'Customer needs to update payment method'
            },
            {
                'name': 'Billing Review Workflow',
                'type': 'billing_review',
                'customer': self.customers[2],
                'description': 'Customer wants to review billing history'
            },
            {
                'name': 'Subscription Management Workflow',
                'type': 'subscription_management',
                'customer': self.customers[1],
                'description': 'Customer wants to manage subscription'
            },
            {
                'name': 'Cancellation Process Workflow',
                'type': 'cancellation_process',
                'customer': self.customers[3],
                'description': 'Customer wants to cancel subscription'
            },
            {
                'name': 'Profile Update Workflow',
                'type': 'profile_update',
                'customer': self.customers[4],
                'description': 'Customer wants to update profile'
            }
        ]
        
        for i, workflow in enumerate(workflows, 1):
            print(f"\n{i}. {workflow['name']}:")
            print(f"   📝 Description: {workflow['description']}")
            
            session_result = self.payment_service.create_portal_integration_workflow(
                customer_id=workflow['customer'].id,
                workflow_type=workflow['type'],
                return_url=f"https://mingus.com/dashboard/billing/{workflow['type']}-completed"
            )
            
            if session_result['success']:
                portal_session = session_result['portal_session']
                print(f"   ✅ Workflow created successfully")
                print(f"   🆔 Session ID: {portal_session['id']}")
                print(f"   🔗 Portal URL: {portal_session['url']}")
                print(f"   🔄 Workflow Type: {session_result['workflow_type']}")
                print(f"   🔙 Return URL: {portal_session['return_url']}")
            else:
                print(f"   ❌ Failed: {session_result['error']}")
    
    def run_all_demonstrations(self):
        """Run all enhanced portal integration demonstrations"""
        print("🚀 MINGUS Enhanced Stripe Customer Portal Integration Demonstration")
        print("=" * 80)
        
        try:
            self.demonstrate_enhanced_portal_session_creation()
            self.demonstrate_portal_return_handling()
            self.demonstrate_custom_branding()
            self.demonstrate_portal_analytics()
            self.demonstrate_workflow_scenarios()
            
            print("\n" + "=" * 80)
            print("✅ All enhanced portal integration demonstrations completed successfully!")
            print("\n🎯 Key Features Demonstrated:")
            print("   • Enhanced portal session creation with custom branding")
            print("   • Return handling with data synchronization")
            print("   • Custom branding and messaging")
            print("   • Portal analytics and insights")
            print("   • Workflow-based portal sessions")
            print("   • Comprehensive data synchronization")
            
        except Exception as e:
            print(f"\n❌ Error during demonstration: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    example = EnhancedStripePortalIntegrationExample()
    example.run_all_demonstrations() 