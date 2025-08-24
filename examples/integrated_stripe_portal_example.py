"""
Integrated Stripe Customer Portal Example for MINGUS
Demonstrates seamless Stripe Customer Portal integration within the main PaymentService
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

class IntegratedStripePortalExample:
    """Example demonstrating integrated Stripe Customer Portal functionality"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_integrated_portal_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for integrated portal demonstration"""
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
        for i in range(30):  # Create 30 customers for integrated demonstration
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_integrated_{i:04d}',  # Simulated Stripe customer ID
                email=f'integrated.user{i}@example.com',
                name=f'Integrated Portal User {i}',
                address={
                    'country': 'US' if i < 20 else 'CA' if i < 25 else 'UK',
                    'state': 'CA' if i < 10 else 'NY' if i < 20 else 'ON' if i < 25 else 'London',
                    'city': 'San Francisco' if i < 10 else 'New York' if i < 20 else 'Toronto' if i < 25 else 'London',
                    'zip': '94105' if i < 10 else '10001' if i < 20 else 'M5V' if i < 25 else 'SW1A'
                },
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=365 - (i * 7))
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions for integrated customers
        subscriptions = []
        billing_records = []
        
        for i, customer in enumerate(customers):
            # Assign different tiers
            if i < 10:
                tier = budget_tier
                amount = 15.00
            elif i < 20:
                tier = mid_tier
                amount = 35.00
            else:
                tier = professional_tier
                amount = 75.00
            
            subscription = Subscription(
                customer_id=customer.id,
                pricing_tier_id=tier.id,
                stripe_subscription_id=f'sub_integrated_{i:04d}',
                status='active',
                current_period_start=datetime.utcnow() - timedelta(days=30),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                billing_cycle='monthly' if i < 20 else 'annual',
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
                stripe_invoice_id=f'in_integrated_{i:04d}_001'
            )
            billing_records.append(billing_record)
        
        self.db_session.add_all(subscriptions)
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_integrated_portal_session_creation(self):
        """Demonstrate integrated portal session creation through PaymentService"""
        print("\n=== Integrated Stripe Customer Portal Session Creation ===")
        
        print(f"\n🔗 Testing Integrated Portal Session Creation:")
        
        # Test basic portal session creation through PaymentService
        print(f"\n1. Create Basic Portal Session via PaymentService:")
        customer = self.customers[0]
        session_result = self.payment_service.create_stripe_portal_session(
            customer_id=customer.id,
            return_url="https://mingus.com/dashboard/billing"
        )
        
        if session_result['success']:
            portal_session = session_result['portal_session']
            print(f"   ✅ Integrated portal session created successfully")
            print(f"   🆔 Session ID: {portal_session['id']}")
            print(f"   🔗 Portal URL: {portal_session['url']}")
            print(f"   👤 Customer: {portal_session['customer']}")
            print(f"   📅 Created: {datetime.fromtimestamp(portal_session['created'])}")
            print(f"   ⏰ Expires: {datetime.fromtimestamp(portal_session['expires_at'])}")
            print(f"   🔙 Return URL: {portal_session['return_url']}")
        else:
            print(f"   ❌ Failed: {session_result['error']}")
        
        # Test limited portal session creation
        print(f"\n2. Create Limited Portal Session via PaymentService:")
        customer = self.customers[1]
        limited_session_result = self.payment_service.create_limited_portal_session(
            customer_id=customer.id,
            allowed_features=['payment_method_update', 'invoice_history'],
            return_url="https://mingus.com/dashboard/billing/limited"
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
    
    def demonstrate_portal_access_management(self):
        """Demonstrate portal access management through PaymentService"""
        print("\n=== Integrated Portal Access Management ===")
        
        print(f"\n🔐 Testing Integrated Portal Access Management:")
        
        # Test full portal access
        print(f"\n1. Full Portal Access via PaymentService:")
        customer = self.customers[2]
        access_result = self.payment_service.get_customer_portal_access(
            customer_id=customer.id,
            access_type='full'
        )
        
        if access_result['success']:
            portal_access = access_result['portal_access']
            print(f"   ✅ Full portal access retrieved successfully")
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
        print(f"\n2. Limited Portal Access via PaymentService:")
        customer = self.customers[3]
        access_result = self.payment_service.get_customer_portal_access(
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
    
    def demonstrate_portal_configuration_management(self):
        """Demonstrate portal configuration management through PaymentService"""
        print("\n=== Integrated Portal Configuration Management ===")
        
        print(f"\n⚙️ Testing Integrated Portal Configuration Management:")
        
        # Test creating portal configuration
        print(f"\n1. Create Custom Portal Configuration via PaymentService:")
        config_result = self.payment_service.create_portal_configuration(
            configuration_name="MINGUS Integrated Portal",
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
            print(f"   ✅ Integrated portal configuration created successfully")
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
        print(f"\n2. Get All Portal Configurations via PaymentService:")
        configs_result = self.payment_service.get_portal_configurations()
        
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
    
    def demonstrate_portal_integration_workflows(self):
        """Demonstrate portal integration workflows through PaymentService"""
        print("\n=== Integrated Portal Integration Workflows ===")
        
        print(f"\n🔄 Testing Integrated Portal Integration Workflows:")
        
        # Test payment update workflow
        print(f"\n1. Payment Update Workflow:")
        customer = self.customers[4]
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='payment_update',
            return_url="https://mingus.com/dashboard/billing/payment-updated"
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Payment update workflow created successfully")
            print(f"   🔄 Workflow Type: {workflow['type']}")
            print(f"   📝 Description: {workflow['description']}")
            print(f"   🔒 Allowed Features: {', '.join(workflow['allowed_features'])}")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
            print(f"   🔙 Return URL: {workflow['return_url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
        
        # Test billing review workflow
        print(f"\n2. Billing Review Workflow:")
        customer = self.customers[5]
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='billing_review'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Billing review workflow created successfully")
            print(f"   🔄 Workflow Type: {workflow['type']}")
            print(f"   📝 Description: {workflow['description']}")
            print(f"   🔒 Allowed Features: {', '.join(workflow['allowed_features'])}")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
        
        # Test subscription management workflow
        print(f"\n3. Subscription Management Workflow:")
        customer = self.customers[6]
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='subscription_management'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Subscription management workflow created successfully")
            print(f"   🔄 Workflow Type: {workflow['type']}")
            print(f"   📝 Description: {workflow['description']}")
            print(f"   🔒 Allowed Features: {', '.join(workflow['allowed_features'])}")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
        
        # Test cancellation process workflow
        print(f"\n4. Cancellation Process Workflow:")
        customer = self.customers[7]
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='cancellation_process'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Cancellation process workflow created successfully")
            print(f"   🔄 Workflow Type: {workflow['type']}")
            print(f"   📝 Description: {workflow['description']}")
            print(f"   🔒 Allowed Features: {', '.join(workflow['allowed_features'])}")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
        
        # Test profile update workflow
        print(f"\n5. Profile Update Workflow:")
        customer = self.customers[8]
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='profile_update'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Profile update workflow created successfully")
            print(f"   🔄 Workflow Type: {workflow['type']}")
            print(f"   📝 Description: {workflow['description']}")
            print(f"   🔒 Allowed Features: {', '.join(workflow['allowed_features'])}")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
    
    def demonstrate_portal_analytics_and_insights(self):
        """Demonstrate portal analytics and insights through PaymentService"""
        print("\n=== Integrated Portal Analytics and Insights ===")
        
        print(f"\n📊 Testing Integrated Portal Analytics and Insights:")
        
        # Test portal analytics
        print(f"\n1. Portal Analytics via PaymentService:")
        analytics_result = self.payment_service.get_portal_analytics(
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
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
        
        # Test comprehensive portal insights
        print(f"\n2. Comprehensive Portal Insights via PaymentService:")
        customer = self.customers[9]
        insights_result = self.payment_service.get_comprehensive_portal_insights(
            customer_id=customer.id,
            date_range='30d'
        )
        
        if insights_result['success']:
            insights = insights_result['portal_insights']
            print(f"   ✅ Comprehensive portal insights retrieved successfully")
            
            # Portal analytics
            if insights['portal_analytics']['success']:
                analytics = insights['portal_analytics']['analytics']
                print(f"   📊 Portal Analytics:")
                print(f"      Total Sessions: {analytics['total_sessions']}")
                print(f"      Unique Customers: {analytics['unique_customers']}")
                print(f"      Average Session Duration: {analytics['session_duration']:.1f} minutes")
            
            # Portal configurations
            if insights['portal_configurations']['success']:
                configs = insights['portal_configurations']['configurations']
                print(f"   ⚙️ Portal Configurations: {len(configs)} available")
            
            # Customer portal access
            if 'customer_portal_access' in insights:
                access = insights['customer_portal_access']['portal_access']
                print(f"   🔐 Customer Portal Access:")
                print(f"      Access Type: {access['access_type']}")
                print(f"      Has Active Subscription: {access['has_active_subscription']}")
                print(f"      Subscription Status: {access['subscription_status']}")
            
            # Recommendations
            recommendations = insights['recommendations']
            print(f"   💡 Portal Optimization Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].upper()}: {rec['title']}")
                print(f"         Description: {rec['description']}")
                print(f"         Action: {rec['action']}")
        else:
            print(f"   ❌ Failed: {insights_result['error']}")
    
    def demonstrate_webhook_integration(self):
        """Demonstrate webhook integration through PaymentService"""
        print("\n=== Integrated Portal Webhook Handling ===")
        
        print(f"\n🔄 Testing Integrated Portal Webhook Handling:")
        
        # Test customer.updated webhook
        print(f"\n1. Handle Customer Updated Webhook via PaymentService:")
        customer_updated_event = {
            'type': 'customer.updated',
            'data': {
                'object': {
                    'id': 'cus_integrated_0001',
                    'email': 'updated.integrated.user1@example.com',
                    'name': 'Updated Integrated Portal User 1',
                    'address': {
                        'country': 'US',
                        'state': 'CA',
                        'city': 'San Francisco',
                        'line1': '123 Updated Integrated St',
                        'postal_code': '94105'
                    }
                }
            }
        }
        
        webhook_result = self.payment_service.handle_portal_webhook(customer_updated_event)
        if webhook_result['success']:
            print(f"   ✅ Customer updated webhook handled successfully via PaymentService")
            print(f"   📝 Message: {webhook_result['message']}")
        else:
            print(f"   ❌ Failed: {webhook_result['error']}")
        
        # Test invoice.payment_succeeded webhook
        print(f"\n2. Handle Invoice Payment Succeeded Webhook via PaymentService:")
        payment_succeeded_event = {
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_integrated_0001_001',
                    'customer': 'cus_integrated_0001',
                    'subscription': 'sub_integrated_0001',
                    'amount_paid': 1500,
                    'currency': 'usd',
                    'status': 'paid'
                }
            }
        }
        
        webhook_result = self.payment_service.handle_portal_webhook(payment_succeeded_event)
        if webhook_result['success']:
            print(f"   ✅ Payment succeeded webhook handled successfully via PaymentService")
            print(f"   📝 Message: {webhook_result['message']}")
        else:
            print(f"   ❌ Failed: {webhook_result['error']}")
        
        # Test subscription.updated webhook
        print(f"\n3. Handle Subscription Updated Webhook via PaymentService:")
        subscription_updated_event = {
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_integrated_0001',
                    'customer': 'cus_integrated_0001',
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
        
        webhook_result = self.payment_service.handle_portal_webhook(subscription_updated_event)
        if webhook_result['success']:
            print(f"   ✅ Subscription updated webhook handled successfully via PaymentService")
            print(f"   📝 Message: {webhook_result['message']}")
        else:
            print(f"   ❌ Failed: {webhook_result['error']}")
    
    def demonstrate_real_world_integration_scenarios(self):
        """Demonstrate real-world integration scenarios through PaymentService"""
        print("\n=== Real-World Integration Scenarios ===")
        
        print(f"\n🌐 Testing Real-World Integration Scenarios via PaymentService:")
        
        # Scenario 1: Customer needs to update payment method
        print(f"\n1. Scenario: Customer Payment Method Update")
        customer = self.customers[10]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   💳 Need: Update payment method")
        print(f"   🔄 Solution: Use integrated payment update workflow")
        
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='payment_update'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Workflow created successfully")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
            print(f"   🔒 Limited to: {', '.join(workflow['allowed_features'])}")
            print(f"   🔙 Return URL: {workflow['return_url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
        
        # Scenario 2: Customer wants to review billing and update profile
        print(f"\n2. Scenario: Customer Billing Review and Profile Update")
        customer = self.customers[11]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   📋 Need: Review billing history and update profile")
        print(f"   🔄 Solution: Use integrated billing review workflow")
        
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='billing_review'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Workflow created successfully")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
            print(f"   🔒 Limited to: {', '.join(workflow['allowed_features'])}")
            print(f"   🔙 Return URL: {workflow['return_url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
        
        # Scenario 3: Customer wants to manage subscription
        print(f"\n3. Scenario: Customer Subscription Management")
        customer = self.customers[12]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   🔄 Need: Update subscription plan and payment method")
        print(f"   🔄 Solution: Use integrated subscription management workflow")
        
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='subscription_management'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Workflow created successfully")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
            print(f"   🔒 Limited to: {', '.join(workflow['allowed_features'])}")
            print(f"   🔙 Return URL: {workflow['return_url']}")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
        
        # Scenario 4: Customer wants to cancel subscription
        print(f"\n4. Scenario: Customer Subscription Cancellation")
        customer = self.customers[13]
        print(f"   👤 Customer: {customer.name} ({customer.email})")
        print(f"   ❌ Need: Cancel subscription with reason")
        print(f"   🔄 Solution: Use integrated cancellation process workflow")
        
        workflow_result = self.payment_service.create_portal_integration_workflow(
            customer_id=customer.id,
            workflow_type='cancellation_process'
        )
        
        if workflow_result['success']:
            workflow = workflow_result['workflow']
            print(f"   ✅ Workflow created successfully")
            print(f"   🔗 Portal URL: {workflow['portal_session']['url']}")
            print(f"   🔒 Limited to: {', '.join(workflow['allowed_features'])}")
            print(f"   🔙 Return URL: {workflow['return_url']}")
            print(f"   📝 Note: Customer will be redirected to cancellation survey after portal")
        else:
            print(f"   ❌ Failed: {workflow_result['error']}")
    
    def run_all_integrated_portal_demonstrations(self):
        """Run all integrated Stripe Customer Portal demonstrations"""
        print("🚀 MINGUS Integrated Stripe Customer Portal Demonstration")
        print("=" * 65)
        
        try:
            self.demonstrate_integrated_portal_session_creation()
            self.demonstrate_portal_access_management()
            self.demonstrate_portal_configuration_management()
            self.demonstrate_portal_integration_workflows()
            self.demonstrate_portal_analytics_and_insights()
            self.demonstrate_webhook_integration()
            self.demonstrate_real_world_integration_scenarios()
            
            print("\n✅ All integrated Stripe Customer Portal demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = IntegratedStripePortalExample()
    example.run_all_integrated_portal_demonstrations()

if __name__ == "__main__":
    main() 