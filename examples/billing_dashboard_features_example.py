"""
Billing Dashboard Features Example for MINGUS
Demonstrates comprehensive billing dashboard features:
- Monthly/annual billing toggle
- Next billing date and amount
- Proration calculations for changes
- Tax information and receipts
- Payment failure notifications and resolution
- Billing dispute and support contact
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from billing.customer_portal import CustomerPortal
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, PaymentMethod, BillingHistory, FeatureUsage

class BillingDashboardFeaturesExample:
    """Example demonstrating comprehensive billing dashboard features"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_billing_dashboard_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.customer_portal = CustomerPortal(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for billing dashboard demonstration"""
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
        for i, tier in enumerate(['budget', 'mid_tier', 'professional']):
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_{tier}_billing_{i}',
                email=f'{tier}.billing.user{i}@example.com',
                name=f'{tier.title()} Billing User {i}',
                address={
                    'country': 'US',
                    'state': 'CA',
                    'city': 'San Francisco',
                    'zip': '94105'
                },
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=400 if i == 0 else 200 if i == 1 else 100)
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with different billing cycles and statuses
        subscriptions = []
        
        # Budget user with monthly billing
        budget_subscription = Subscription(
            customer_id=customers[0].id,
            pricing_tier_id=budget_tier.id,
            stripe_subscription_id='sub_budget_billing',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=20),
            current_period_end=datetime.utcnow() + timedelta(days=10),
            billing_cycle='monthly',
            amount=15.00,
            currency='USD'
        )
        subscriptions.append(budget_subscription)
        
        # Mid-tier user with annual billing
        mid_tier_subscription = Subscription(
            customer_id=customers[1].id,
            pricing_tier_id=mid_tier.id,
            stripe_subscription_id='sub_mid_tier_billing',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=350),
            billing_cycle='annual',
            amount=29.17,  # 350/12
            currency='USD'
        )
        subscriptions.append(mid_tier_subscription)
        
        # Professional user with payment failure
        professional_subscription = Subscription(
            customer_id=customers[2].id,
            pricing_tier_id=professional_tier.id,
            stripe_subscription_id='sub_professional_billing',
            status='past_due',
            current_period_start=datetime.utcnow() - timedelta(days=30),
            current_period_end=datetime.utcnow() + timedelta(days=5),
            billing_cycle='monthly',
            amount=75.00,
            currency='USD'
        )
        subscriptions.append(professional_subscription)
        
        self.db_session.add_all(subscriptions)
        self.db_session.commit()
        
        # Create payment methods
        payment_methods = []
        for i, customer in enumerate(customers):
            payment_method = PaymentMethod(
                customer_id=customer.id,
                stripe_payment_method_id=f'pm_{i}_billing',
                payment_type='card',
                last4='4242',
                brand='visa',
                exp_month=12,
                exp_year=2025,
                is_default=True
            )
            payment_methods.append(payment_method)
        
        self.db_session.add_all(payment_methods)
        self.db_session.commit()
        
        # Create billing history with different scenarios
        billing_records = []
        
        # Budget user - normal billing
        budget_invoice = BillingHistory(
            customer_id=customers[0].id,
            subscription_id=budget_subscription.id,
            invoice_number=f'INV-{budget_subscription.id:04d}-001',
            amount=15.00,
            currency='USD',
            status='paid',
            description=f'Monthly subscription - {budget_subscription.pricing_tier.name}',
            created_at=datetime.utcnow() - timedelta(days=5),
            paid_at=datetime.utcnow() - timedelta(days=5),
            stripe_invoice_id=f'in_{budget_subscription.id}_billing'
        )
        billing_records.append(budget_invoice)
        
        # Mid-tier user - annual billing
        mid_tier_invoice = BillingHistory(
            customer_id=customers[1].id,
            subscription_id=mid_tier_subscription.id,
            invoice_number=f'INV-{mid_tier_subscription.id:04d}-001',
            amount=350.00,
            currency='USD',
            status='paid',
            description=f'Annual subscription - {mid_tier_subscription.pricing_tier.name}',
            created_at=datetime.utcnow() - timedelta(days=15),
            paid_at=datetime.utcnow() - timedelta(days=15),
            stripe_invoice_id=f'in_{mid_tier_subscription.id}_billing'
        )
        billing_records.append(mid_tier_invoice)
        
        # Professional user - failed payment
        professional_failed_invoice = BillingHistory(
            customer_id=customers[2].id,
            subscription_id=professional_subscription.id,
            invoice_number=f'INV-{professional_subscription.id:04d}-001',
            amount=75.00,
            currency='USD',
            status='failed',
            description=f'Monthly subscription - {professional_subscription.pricing_tier.name}',
            created_at=datetime.utcnow() - timedelta(days=1),
            stripe_invoice_id=f'in_{professional_subscription.id}_failed'
        )
        billing_records.append(professional_failed_invoice)
        
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_billing_dashboard(self):
        """Demonstrate comprehensive billing dashboard"""
        print("\n=== Billing Dashboard Demonstration ===")
        
        print(f"\n🔄 Testing Billing Dashboard:")
        
        # Test for budget user (monthly billing)
        print(f"\n1. Budget User - Monthly Billing Dashboard:")
        dashboard_result = self.customer_portal.get_billing_dashboard(
            customer_id=self.customers[0].id
        )
        
        if dashboard_result['success']:
            dashboard = dashboard_result['billing_dashboard']
            
            print(f"   ✅ Billing dashboard retrieved")
            
            # Billing cycle options
            billing_cycle_options = dashboard['billing_cycle_options']
            print(f"   🔄 Billing Cycle Options:")
            print(f"      Current Cycle: {billing_cycle_options['current_cycle']}")
            print(f"      Available Cycles: {', '.join(billing_cycle_options['available_cycles'])}")
            print(f"      Can Change: {billing_cycle_options['can_change']}")
            
            pricing = billing_cycle_options['pricing']
            print(f"      Monthly Price: ${pricing['monthly']['amount']:.2f}")
            print(f"      Annual Price: ${pricing['annual']['amount']:.2f}")
            print(f"      Annual Savings: ${pricing['annual']['savings']:.2f} ({pricing['annual']['savings_percentage']:.1f}%)")
            
            # Next billing info
            next_billing = dashboard['next_billing_info']
            print(f"   📅 Next Billing Information:")
            print(f"      Next Billing Date: {next_billing['next_billing_date']}")
            print(f"      Days Until Billing: {next_billing['days_until_billing']}")
            print(f"      Amount: ${next_billing['amount']:.2f} {next_billing['currency']}")
            print(f"      Billing Cycle: {next_billing['billing_cycle']}")
            print(f"      Status: {next_billing['status']}")
            
            # Tax information
            tax_info = dashboard['tax_information']
            print(f"   🧾 Tax Information:")
            print(f"      Tax Exempt: {tax_info['tax_exempt']}")
            print(f"      Tax Rate: {tax_info['tax_rate']:.1%}")
            print(f"      Tax Location: {tax_info['tax_location']['city']}, {tax_info['tax_location']['state']}")
            print(f"      Tax Documents Available: {tax_info['tax_documents_available']}")
            
            # Payment failure info
            payment_failure = dashboard['payment_failure_info']
            print(f"   ⚠️ Payment Failure Information:")
            print(f"      Has Failures: {payment_failure['has_failures']}")
            if payment_failure['has_failures']:
                print(f"      Status: {payment_failure['status']}")
                print(f"      Failed Payments: {len(payment_failure['failed_payments'])}")
                print(f"      Resolution Actions: {', '.join(payment_failure['resolution_actions'])}")
            
            # Billing dispute info
            dispute_info = dashboard['billing_dispute_info']
            print(f"   ⚖️ Billing Dispute Information:")
            print(f"      Recent Disputes: {dispute_info['dispute_count']}")
            print(f"      Support Contact:")
            print(f"         Email: {dispute_info['support_contact']['email']}")
            print(f"         Phone: {dispute_info['support_contact']['phone']}")
            print(f"         Hours: {dispute_info['support_contact']['hours']}")
            
            # Quick actions
            quick_actions = dashboard['quick_actions']
            print(f"   ⚡ Quick Actions:")
            for action in quick_actions:
                print(f"      - {action['title']}: {action['description']}")
        else:
            print(f"   ❌ Failed: {dashboard_result['error']}")
        
        # Test for mid-tier user (annual billing)
        print(f"\n2. Mid-Tier User - Annual Billing Dashboard:")
        dashboard_result = self.customer_portal.get_billing_dashboard(
            customer_id=self.customers[1].id
        )
        
        if dashboard_result['success']:
            dashboard = dashboard_result['billing_dashboard']
            
            print(f"   ✅ Billing dashboard retrieved")
            
            # Show annual billing differences
            billing_cycle_options = dashboard['billing_cycle_options']
            pricing = billing_cycle_options['pricing']
            print(f"   🔄 Annual Billing Benefits:")
            print(f"      Current Cycle: {billing_cycle_options['current_cycle']}")
            print(f"      Monthly Equivalent: ${pricing['annual']['monthly_equivalent']:.2f}")
            print(f"      Annual Savings: ${pricing['annual']['savings']:.2f}")
            print(f"      Savings Percentage: {pricing['annual']['savings_percentage']:.1f}%")
            
            next_billing = dashboard['next_billing_info']
            print(f"   📅 Next Billing:")
            print(f"      Next Billing Date: {next_billing['next_billing_date']}")
            print(f"      Days Until Billing: {next_billing['days_until_billing']}")
            print(f"      Amount: ${next_billing['amount']:.2f} {next_billing['currency']}")
        else:
            print(f"   ❌ Failed: {dashboard_result['error']}")
    
    def demonstrate_billing_cycle_toggle(self):
        """Demonstrate monthly/annual billing toggle"""
        print("\n=== Billing Cycle Toggle Demonstration ===")
        
        print(f"\n🔄 Testing Billing Cycle Toggle:")
        
        # Test monthly to annual toggle
        print(f"\n1. Budget User - Monthly to Annual Toggle:")
        toggle_result = self.customer_portal.toggle_billing_cycle(
            customer_id=self.customers[0].id,
            subscription_id=self.subscriptions[0].id,
            new_cycle='annual'
        )
        
        if toggle_result['success']:
            change_data = toggle_result['billing_cycle_change']
            
            print(f"   ✅ Billing cycle changed successfully")
            print(f"   📋 Change Details:")
            print(f"      Old Cycle: {change_data['old_cycle']}")
            print(f"      New Cycle: {change_data['new_cycle']}")
            print(f"      Old Amount: ${change_data['old_amount']:.2f}")
            print(f"      New Amount: ${change_data['new_amount']:.2f}")
            print(f"      Next Billing Date: {change_data['next_billing_date']}")
            print(f"      Message: {change_data['message']}")
            
            proration_info = change_data['proration_info']
            print(f"   💰 Proration Information:")
            print(f"      Amount Difference: ${proration_info['amount_difference']:.2f}")
            print(f"      Proration Amount: ${proration_info['proration_amount']:.2f}")
            print(f"      Proration Type: {proration_info['proration_type']}")
            print(f"      Effective Date: {proration_info['effective_date']}")
        else:
            print(f"   ❌ Failed: {toggle_result['error']}")
        
        # Test annual to monthly toggle
        print(f"\n2. Mid-Tier User - Annual to Monthly Toggle:")
        toggle_result = self.customer_portal.toggle_billing_cycle(
            customer_id=self.customers[1].id,
            subscription_id=self.subscriptions[1].id,
            new_cycle='monthly'
        )
        
        if toggle_result['success']:
            change_data = toggle_result['billing_cycle_change']
            
            print(f"   ✅ Billing cycle changed successfully")
            print(f"   📋 Change Details:")
            print(f"      Old Cycle: {change_data['old_cycle']}")
            print(f"      New Cycle: {change_data['new_cycle']}")
            print(f"      Old Amount: ${change_data['old_amount']:.2f}")
            print(f"      New Amount: ${change_data['new_amount']:.2f}")
        else:
            print(f"   ❌ Failed: {toggle_result['error']}")
    
    def demonstrate_next_billing_details(self):
        """Demonstrate next billing details"""
        print("\n=== Next Billing Details Demonstration ===")
        
        print(f"\n🔄 Testing Next Billing Details:")
        
        # Test for budget user
        print(f"\n1. Budget User - Next Billing Details:")
        billing_result = self.customer_portal.get_next_billing_details(
            customer_id=self.customers[0].id,
            subscription_id=self.subscriptions[0].id
        )
        
        if billing_result['success']:
            billing_details = billing_result['next_billing_details']
            
            print(f"   ✅ Next billing details retrieved")
            print(f"   📋 Subscription Details:")
            subscription = billing_details['subscription_details']
            print(f"      ID: {subscription['id']}")
            print(f"      Status: {subscription['status']}")
            print(f"      Tier: {subscription['tier']}")
            print(f"      Billing Cycle: {subscription['billing_cycle']}")
            print(f"      Amount: ${subscription['amount']:.2f} {subscription['currency']}")
            
            next_billing = billing_details['next_billing']
            print(f"   📅 Next Billing:")
            print(f"      Date: {next_billing['next_billing_date']}")
            print(f"      Days Remaining: {next_billing['days_until_billing']}")
            print(f"      Amount: ${next_billing['amount']:.2f} {next_billing['currency']}")
            
            payment_method = billing_details['payment_method']
            if payment_method:
                print(f"   💳 Payment Method:")
                print(f"      Type: {payment_method['type']}")
                print(f"      Brand: {payment_method['brand']}")
                print(f"      Last 4: {payment_method['last4']}")
                print(f"      Expires: {payment_method['exp_month']}/{payment_method['exp_year']}")
            
            tax_info = billing_details['tax_info']
            print(f"   🧾 Tax Information:")
            print(f"      Tax Rate: {tax_info['tax_rate']:.1%}")
            print(f"      Tax Location: {tax_info['tax_location']['city']}, {tax_info['tax_location']['state']}")
            
            invoice_prefs = billing_details['invoice_preferences']
            print(f"   📄 Invoice Preferences:")
            print(f"      Email Invoices: {invoice_prefs['email_invoices']}")
            print(f"      Paper Invoices: {invoice_prefs['paper_invoices']}")
            print(f"      Invoice Frequency: {invoice_prefs['invoice_frequency']}")
        else:
            print(f"   ❌ Failed: {billing_result['error']}")
    
    def demonstrate_proration_calculations(self):
        """Demonstrate proration calculations"""
        print("\n=== Proration Calculations Demonstration ===")
        
        print(f"\n🔄 Testing Proration Calculations:")
        
        # Test proration for budget to mid-tier upgrade
        print(f"\n1. Budget to Mid-Tier Upgrade Proration:")
        mid_tier = self.db_session.query(PricingTier).filter(PricingTier.tier_type == 'mid_tier').first()
        
        proration_result = self.customer_portal.calculate_proration(
            customer_id=self.customers[0].id,
            subscription_id=self.subscriptions[0].id,
            new_tier_id=mid_tier.id,
            effective_date='immediate'
        )
        
        if proration_result['success']:
            proration_data = proration_result['proration_calculation']
            
            print(f"   ✅ Proration calculated successfully")
            print(f"   📋 Current Subscription:")
            current = proration_data['current_subscription']
            print(f"      Tier: {current['tier']}")
            print(f"      Amount: ${current['amount']:.2f}")
            print(f"      Billing Cycle: {current['billing_cycle']}")
            
            print(f"   🚀 New Subscription:")
            new = proration_data['new_subscription']
            print(f"      Tier: {new['tier']}")
            print(f"      Amount: ${new['amount']:.2f}")
            print(f"      Billing Cycle: {new['billing_cycle']}")
            
            print(f"   💰 Proration Details:")
            proration = proration_data['proration_details']
            print(f"      Amount Difference: ${proration['amount_difference']:.2f}")
            print(f"      Proration Amount: ${proration['proration_amount']:.2f}")
            print(f"      Proration Type: {proration['proration_type']}")
            print(f"      Effective Date: {proration['effective_date']}")
            print(f"      Next Billing Date: {proration['next_billing_date']}")
            
            print(f"   💳 Total Charge: ${proration_data['total_charge']:.2f}")
        else:
            print(f"   ❌ Failed: {proration_result['error']}")
        
        # Test proration for mid-tier to professional upgrade
        print(f"\n2. Mid-Tier to Professional Upgrade Proration:")
        professional_tier = self.db_session.query(PricingTier).filter(PricingTier.tier_type == 'professional').first()
        
        proration_result = self.customer_portal.calculate_proration(
            customer_id=self.customers[1].id,
            subscription_id=self.subscriptions[1].id,
            new_tier_id=professional_tier.id,
            effective_date='immediate'
        )
        
        if proration_result['success']:
            proration_data = proration_result['proration_calculation']
            
            print(f"   ✅ Proration calculated successfully")
            print(f"   📋 Current Subscription:")
            current = proration_data['current_subscription']
            print(f"      Tier: {current['tier']}")
            print(f"      Amount: ${current['amount']:.2f}")
            
            print(f"   🚀 New Subscription:")
            new = proration_data['new_subscription']
            print(f"      Tier: {new['tier']}")
            print(f"      Amount: ${new['amount']:.2f}")
            
            print(f"   💰 Proration Details:")
            proration = proration_data['proration_details']
            print(f"      Amount Difference: ${proration['amount_difference']:.2f}")
            print(f"      Proration Amount: ${proration['proration_amount']:.2f}")
            print(f"      Proration Type: {proration['proration_type']}")
        else:
            print(f"   ❌ Failed: {proration_result['error']}")
    
    def demonstrate_tax_information_and_receipts(self):
        """Demonstrate tax information and receipts"""
        print("\n=== Tax Information and Receipts Demonstration ===")
        
        print(f"\n🔄 Testing Tax Information and Receipts:")
        
        # Test for budget user
        print(f"\n1. Budget User - Tax Information and Receipts:")
        tax_result = self.customer_portal.get_tax_information_and_receipts(
            customer_id=self.customers[0].id
        )
        
        if tax_result['success']:
            tax_info = tax_result['tax_information']
            receipts = tax_result['receipts']
            
            print(f"   ✅ Tax information and receipts retrieved")
            print(f"   🧾 Tax Information:")
            print(f"      Tax Exempt: {tax_info['tax_exempt']}")
            print(f"      Tax Rate: {tax_info['tax_rate']:.1%}")
            print(f"      Tax Location: {tax_info['tax_location']['city']}, {tax_info['tax_location']['state']}")
            print(f"      Last Tax Calculation: {tax_info['last_tax_calculation']}")
            print(f"      Tax Documents Available: {tax_info['tax_documents_available']}")
            
            print(f"   📄 Tax Documents:")
            for doc in tax_info['tax_documents']:
                print(f"      {doc['type'].title()} {doc['year']}: {doc['download_url']}")
            
            print(f"   📋 Receipts:")
            for receipt in receipts:
                print(f"      Invoice: {receipt['invoice_number']}")
                print(f"         Amount: ${receipt['amount']:.2f} {receipt['currency']}")
                print(f"         Status: {receipt['status']}")
                print(f"         Date: {receipt['created_at']}")
                if receipt['download_url']:
                    print(f"         Download: {receipt['download_url']}")
        else:
            print(f"   ❌ Failed: {tax_result['error']}")
    
    def demonstrate_payment_failure_handling(self):
        """Demonstrate payment failure handling"""
        print("\n=== Payment Failure Handling Demonstration ===")
        
        print(f"\n🔄 Testing Payment Failure Handling:")
        
        # Test for professional user (has payment failure)
        print(f"\n1. Professional User - Payment Failure Details:")
        failure_result = self.customer_portal.handle_payment_failure(
            customer_id=self.customers[2].id,
            subscription_id=self.subscriptions[2].id,
            action='get_failure_details'
        )
        
        if failure_result['success']:
            failure_details = failure_result['failure_details']
            
            print(f"   ✅ Payment failure details retrieved")
            print(f"   ⚠️ Failure Details:")
            print(f"      Failure Reason: {failure_details['failure_reason']}")
            print(f"      Failure Date: {failure_details['failure_date']}")
            print(f"      Retry Attempts: {failure_details['retry_attempts']}")
            print(f"      Max Retries: {failure_details['max_retries']}")
            print(f"      Next Retry: {failure_details['next_retry']}")
            print(f"      Grace Period End: {failure_details['grace_period_end']}")
        else:
            print(f"   ❌ Failed: {failure_result['error']}")
        
        # Test retry payment
        print(f"\n2. Professional User - Retry Payment:")
        retry_result = self.customer_portal.handle_payment_failure(
            customer_id=self.customers[2].id,
            subscription_id=self.subscriptions[2].id,
            action='retry_payment',
            payment_method_id=3
        )
        
        if retry_result['success']:
            retry_data = retry_result['retry_result']
            
            print(f"   ✅ Payment retry scheduled")
            print(f"   📋 Retry Details:")
            print(f"      Status: {retry_data['status']}")
            print(f"      Retry Date: {retry_data['retry_date']}")
            print(f"      Payment Method ID: {retry_data['payment_method_id']}")
            print(f"      Message: {retry_data['message']}")
        else:
            print(f"   ❌ Failed: {retry_result['error']}")
        
        # Test update payment method
        print(f"\n3. Professional User - Update Payment Method:")
        update_result = self.customer_portal.handle_payment_failure(
            customer_id=self.customers[2].id,
            subscription_id=self.subscriptions[2].id,
            action='update_payment_method',
            payment_method_id=3
        )
        
        if update_result['success']:
            update_data = update_result['update_result']
            
            print(f"   ✅ Payment method updated")
            print(f"   📋 Update Details:")
            print(f"      Status: {update_data['status']}")
            print(f"      Payment Method ID: {update_data['payment_method_id']}")
            print(f"      Retry Scheduled: {update_data['retry_scheduled']}")
            print(f"      Message: {update_data['message']}")
        else:
            print(f"   ❌ Failed: {update_result['error']}")
    
    def demonstrate_billing_dispute_management(self):
        """Demonstrate billing dispute management"""
        print("\n=== Billing Dispute Management Demonstration ===")
        
        print(f"\n🔄 Testing Billing Dispute Management:")
        
        # Test create dispute
        print(f"\n1. Budget User - Create Billing Dispute:")
        dispute_result = self.customer_portal.manage_billing_disputes(
            customer_id=self.customers[0].id,
            action='create_dispute',
            dispute_data={
                'subject': 'Incorrect billing amount',
                'description': 'I was charged $20 instead of $15 for my monthly subscription',
                'priority': 'high'
            }
        )
        
        if dispute_result['success']:
            dispute_data = dispute_result['dispute']
            
            print(f"   ✅ Billing dispute created")
            print(f"   📋 Dispute Details:")
            print(f"      ID: {dispute_data['id']}")
            print(f"      Subject: {dispute_data['subject']}")
            print(f"      Status: {dispute_data['status']}")
            print(f"      Created At: {dispute_data['created_at']}")
            print(f"      Message: {dispute_result['message']}")
        else:
            print(f"   ❌ Failed: {dispute_result['error']}")
        
        # Test get disputes
        print(f"\n2. Budget User - Get Disputes:")
        disputes_result = self.customer_portal.manage_billing_disputes(
            customer_id=self.customers[0].id,
            action='get_disputes'
        )
        
        if disputes_result['success']:
            disputes = disputes_result['disputes']
            
            print(f"   ✅ Disputes retrieved")
            print(f"   📋 Disputes:")
            for dispute in disputes:
                print(f"      ID: {dispute['id']}")
                print(f"         Subject: {dispute['subject']}")
                print(f"         Status: {dispute['status']}")
                print(f"         Priority: {dispute['priority']}")
                print(f"         Created: {dispute['created_at']}")
        else:
            print(f"   ❌ Failed: {disputes_result['error']}")
        
        # Test contact support
        print(f"\n3. Budget User - Contact Billing Support:")
        support_result = self.customer_portal.manage_billing_disputes(
            customer_id=self.customers[0].id,
            action='contact_support',
            dispute_data={
                'subject': 'Billing question',
                'priority': 'medium'
            }
        )
        
        if support_result['success']:
            support_data = support_result['support_ticket']
            
            print(f"   ✅ Support ticket created")
            print(f"   📋 Support Ticket:")
            print(f"      ID: {support_data['id']}")
            print(f"      Customer ID: {support_data['customer_id']}")
            print(f"      Subject: {support_data['subject']}")
            print(f"      Priority: {support_data['priority']}")
            print(f"      Created At: {support_data['created_at']}")
            print(f"      Message: {support_result['message']}")
        else:
            print(f"   ❌ Failed: {support_result['error']}")
    
    def run_all_billing_dashboard_demonstrations(self):
        """Run all billing dashboard feature demonstrations"""
        print("🚀 MINGUS Billing Dashboard Features Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_billing_dashboard()
            self.demonstrate_billing_cycle_toggle()
            self.demonstrate_next_billing_details()
            self.demonstrate_proration_calculations()
            self.demonstrate_tax_information_and_receipts()
            self.demonstrate_payment_failure_handling()
            self.demonstrate_billing_dispute_management()
            
            print("\n✅ All billing dashboard feature demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = BillingDashboardFeaturesExample()
    example.run_all_billing_dashboard_demonstrations()

if __name__ == "__main__":
    main() 