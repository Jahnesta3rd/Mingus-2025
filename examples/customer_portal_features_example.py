"""
Customer Portal Features Example for MINGUS
Demonstrates specific customer portal features:
- Current subscription status and details
- Payment method management
- Billing history and invoice downloads
- Usage tracking and limits display
- Subscription upgrade/downgrade options
- Cancellation with retention offers
- Reactivation for canceled subscriptions
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

class CustomerPortalFeaturesExample:
    """Example demonstrating specific customer portal features"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_portal_features_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.customer_portal = CustomerPortal(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for customer portal features demonstration"""
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
                stripe_customer_id=f'cus_{tier}_features_{i}',
                email=f'{tier}.features.user{i}@example.com',
                name=f'{tier.title()} Features User {i}',
                address={'country': 'US', 'state': 'CA'},
                phone='+1-555-0123',
                created_at=datetime.utcnow() - timedelta(days=400 if i == 0 else 200 if i == 1 else 100)
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions with different statuses
        subscriptions = []
        
        # Budget user with active subscription
        budget_subscription = Subscription(
            customer_id=customers[0].id,
            pricing_tier_id=budget_tier.id,
            stripe_subscription_id='sub_budget_features',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=20),
            current_period_end=datetime.utcnow() + timedelta(days=10),
            billing_cycle='monthly',
            amount=15.00,
            currency='USD'
        )
        subscriptions.append(budget_subscription)
        
        # Mid-tier user with active subscription
        mid_tier_subscription = Subscription(
            customer_id=customers[1].id,
            pricing_tier_id=mid_tier.id,
            stripe_subscription_id='sub_mid_tier_features',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=15),
            billing_cycle='monthly',
            amount=35.00,
            currency='USD'
        )
        subscriptions.append(mid_tier_subscription)
        
        # Professional user with canceled subscription
        professional_subscription = Subscription(
            customer_id=customers[2].id,
            pricing_tier_id=professional_tier.id,
            stripe_subscription_id='sub_professional_features',
            status='canceled',
            current_period_start=datetime.utcnow() - timedelta(days=30),
            current_period_end=datetime.utcnow() + timedelta(days=5),
            billing_cycle='monthly',
            amount=75.00,
            currency='USD',
            canceled_at=datetime.utcnow() - timedelta(days=5)
        )
        subscriptions.append(professional_subscription)
        
        self.db_session.add_all(subscriptions)
        self.db_session.commit()
        
        # Create payment methods
        payment_methods = []
        for i, customer in enumerate(customers):
            payment_method = PaymentMethod(
                customer_id=customer.id,
                stripe_payment_method_id=f'pm_{i}_features',
                payment_type='card',
                last4='4242',
                brand='visa',
                exp_month=12,
                exp_year=2025,
                is_default=True
            )
            payment_methods.append(payment_method)
            
            # Add second payment method for some customers
            if i > 0:
                second_method = PaymentMethod(
                    customer_id=customer.id,
                    stripe_payment_method_id=f'pm_{i}_features_2',
                    payment_type='card',
                    last4='5555',
                    brand='mastercard',
                    exp_month=10,
                    exp_year=2026,
                    is_default=False
                )
                payment_methods.append(second_method)
        
        self.db_session.add_all(payment_methods)
        self.db_session.commit()
        
        # Create billing history
        billing_records = []
        for i, subscription in enumerate(subscriptions):
            # Current month invoice
            current_invoice = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-001',
                amount=subscription.amount,
                currency=subscription.currency,
                status='paid',
                description=f'Monthly subscription - {subscription.pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=5),
                paid_at=datetime.utcnow() - timedelta(days=5),
                stripe_invoice_id=f'in_{subscription.id}_features'
            )
            billing_records.append(current_invoice)
            
            # Previous month invoice
            prev_invoice = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                invoice_number=f'INV-{subscription.id:04d}-002',
                amount=subscription.amount,
                currency=subscription.currency,
                status='paid',
                description=f'Monthly subscription - {subscription.pricing_tier.name}',
                created_at=datetime.utcnow() - timedelta(days=35),
                paid_at=datetime.utcnow() - timedelta(days=35),
                stripe_invoice_id=f'in_{subscription.id}_prev_features'
            )
            billing_records.append(prev_invoice)
            
            # Add unpaid invoice for some customers
            if i == 1:  # Mid-tier user
                unpaid_invoice = BillingHistory(
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    invoice_number=f'INV-{subscription.id:04d}-003',
                    amount=subscription.amount,
                    currency=subscription.currency,
                    status='unpaid',
                    description=f'Monthly subscription - {subscription.pricing_tier.name}',
                    created_at=datetime.utcnow() - timedelta(days=1),
                    due_date=datetime.utcnow() + timedelta(days=14),
                    stripe_invoice_id=f'in_{subscription.id}_unpaid_features'
                )
                billing_records.append(unpaid_invoice)
        
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        # Create feature usage with different usage patterns
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        usage_records = []
        
        # Budget user - near limits
        budget_usage = FeatureUsage(
            subscription_id=budget_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=4,  # At limit
            financial_reports_used=2,  # At limit
            ai_insights_used=0,
            custom_reports_used=0,
            team_members_used=0,
            support_requests_used=1,
            career_risk_management_used=0,
            dedicated_account_manager_used=0
        )
        usage_records.append(budget_usage)
        
        # Mid-tier user - moderate usage
        mid_tier_usage = FeatureUsage(
            subscription_id=mid_tier_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=8,  # 67% of limit
            financial_reports_used=6,  # 60% of limit
            ai_insights_used=35,  # 70% of limit
            custom_reports_used=3,  # 60% of limit
            team_members_used=0,
            support_requests_used=2,
            career_risk_management_used=5,
            dedicated_account_manager_used=0
        )
        usage_records.append(mid_tier_usage)
        
        # Professional user - high usage (before cancellation)
        professional_usage = FeatureUsage(
            subscription_id=professional_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=25,
            financial_reports_used=15,
            ai_insights_used=100,
            custom_reports_used=8,
            team_members_used=5,
            support_requests_used=3,
            career_risk_management_used=12,
            dedicated_account_manager_used=1
        )
        usage_records.append(professional_usage)
        
        self.db_session.add_all(usage_records)
        self.db_session.commit()
        
        self.customers = customers
        self.subscriptions = subscriptions
    
    def demonstrate_subscription_status_and_details(self):
        """Demonstrate current subscription status and details"""
        print("\n=== Current Subscription Status and Details ===")
        
        print(f"\n🔄 Testing Subscription Status:")
        
        # Test for budget user (active, near limits)
        print(f"\n1. Budget User - Active Subscription (Near Limits):")
        status_result = self.customer_portal.get_current_subscription_status(
            customer_id=self.customers[0].id
        )
        
        if status_result['success']:
            status_data = status_result['subscription_status']
            
            print(f"   ✅ Subscription status retrieved")
            print(f"   📋 Subscription Details:")
            print(f"      Status: {status_data['status']}")
            print(f"      Tier: {status_data['tier']['name']} ({status_data['tier']['type']})")
            print(f"      Amount: ${status_data['billing']['amount']:.2f}/{status_data['billing']['cycle']}")
            
            if status_data['billing']['next_billing']:
                next_billing = status_data['billing']['next_billing']
                print(f"      Next Billing: {next_billing['date']} ({next_billing['days_remaining']} days)")
            
            print(f"   📊 Usage Analysis:")
            usage_analysis = status_data['usage']
            for feature, data in usage_analysis.items():
                print(f"      {feature}:")
                print(f"         Used: {data['used']}/{data['limit']} ({data['percentage']:.1f}%)")
                print(f"         Status: {data['status']}")
            
            print(f"   ⚡ Available Actions:")
            for action in status_data['actions_available']:
                print(f"      - {action}")
            
            print(f"   📢 Status Message: {status_data['status_message']}")
        else:
            print(f"   ❌ Failed: {status_result['error']}")
        
        # Test for professional user (canceled)
        print(f"\n2. Professional User - Canceled Subscription:")
        status_result = self.customer_portal.get_current_subscription_status(
            customer_id=self.customers[2].id
        )
        
        if status_result['success']:
            status_data = status_result['subscription_status']
            
            print(f"   ✅ Subscription status retrieved")
            print(f"   📋 Subscription Details:")
            print(f"      Status: {status_data['status']}")
            print(f"      Tier: {status_data['tier']['name']} ({status_data['tier']['type']})")
            print(f"      Canceled: {status_data['canceled_at']}")
            
            print(f"   ⚡ Available Actions:")
            for action in status_data['actions_available']:
                print(f"      - {action}")
            
            print(f"   📢 Status Message: {status_data['status_message']}")
        else:
            print(f"   ❌ Failed: {status_result['error']}")
    
    def demonstrate_payment_method_management(self):
        """Demonstrate payment method management"""
        print("\n=== Payment Method Management ===")
        
        print(f"\n🔄 Testing Payment Method Management:")
        
        # Test listing payment methods
        print(f"\n1. Listing Payment Methods:")
        payment_result = self.customer_portal.manage_payment_methods(
            customer_id=self.customers[1].id,  # Mid-tier user with multiple methods
            action='list'
        )
        
        if payment_result['success']:
            payment_data = payment_result['payment_methods']
            
            print(f"   ✅ Payment methods retrieved")
            print(f"   💳 Payment Methods:")
            for method in payment_data['payment_methods']:
                print(f"      {method['brand'].title()} ending in {method['last4']}")
                print(f"         Expires: {method['exp_month']}/{method['exp_year']}")
                print(f"         Default: {method['is_default']}")
            
            print(f"   📊 Limits:")
            print(f"      Can Add Methods: {payment_data['can_add_methods']}")
            print(f"      Max Methods: {payment_data['max_methods']}")
        else:
            print(f"   ❌ Failed: {payment_result['error']}")
        
        # Test setting default payment method
        print(f"\n2. Setting Default Payment Method:")
        set_default_result = self.customer_portal.manage_payment_methods(
            customer_id=self.customers[1].id,
            action='set_default',
            payment_method_id=3  # Second payment method
        )
        
        if set_default_result['success']:
            print(f"   ✅ Default payment method set successfully")
            print(f"   📢 Message: {set_default_result['message']}")
        else:
            print(f"   ❌ Failed: {set_default_result['error']}")
        
        # Test updating payment method
        print(f"\n3. Updating Payment Method:")
        update_result = self.customer_portal.manage_payment_methods(
            customer_id=self.customers[1].id,
            action='update',
            payment_method_id=2,  # First payment method
            payment_data={'exp_month': 11, 'exp_year': 2026}
        )
        
        if update_result['success']:
            print(f"   ✅ Payment method updated successfully")
            print(f"   📢 Message: {update_result['message']}")
        else:
            print(f"   ❌ Failed: {update_result['error']}")
    
    def demonstrate_billing_history_and_downloads(self):
        """Demonstrate billing history and invoice downloads"""
        print("\n=== Billing History and Invoice Downloads ===")
        
        print(f"\n🔄 Testing Billing History:")
        
        # Test billing history with downloads
        print(f"\n1. Billing History with Download Capabilities:")
        history_result = self.customer_portal.get_billing_history_with_downloads(
            customer_id=self.customers[1].id,  # Mid-tier user with unpaid invoice
            page=1,
            per_page=5
        )
        
        if history_result['success']:
            history_data = history_result['billing_history']
            
            print(f"   ✅ Billing history retrieved")
            
            # Summary
            summary = history_data['summary']
            print(f"   📊 Billing Summary:")
            print(f"      Total Invoices: {summary['total_invoices']}")
            print(f"      Paid Invoices: {summary['paid_invoices']}")
            print(f"      Unpaid Invoices: {summary['unpaid_invoices']}")
            print(f"      Downloadable Invoices: {summary['downloadable_invoices']}")
            
            # Records
            records = history_data['records']
            print(f"   📄 Billing Records:")
            for record in records:
                print(f"      Invoice: {record['invoice_number']}")
                print(f"         Amount: ${record['amount']:.2f} {record['currency']}")
                print(f"         Status: {record['status']}")
                print(f"         Date: {record['created_at']}")
                print(f"         Download Available: {record['download_available']}")
                if record['download_url']:
                    print(f"         Download URL: {record['download_url']}")
            
            # Pagination
            pagination = history_data['pagination']
            print(f"   📑 Pagination:")
            print(f"      Current Page: {pagination['current_page']}")
            print(f"      Total Pages: {pagination['total_pages']}")
            print(f"      Total Records: {pagination['total_count']}")
        else:
            print(f"   ❌ Failed: {history_result['error']}")
        
        # Test invoice download
        print(f"\n2. Invoice Download:")
        download_result = self.customer_portal.download_invoice(
            customer_id=self.customers[1].id,
            invoice_id=3  # Assuming this exists
        )
        
        if download_result['success']:
            invoice_data = download_result['invoice_data']
            print(f"   ✅ Invoice download successful")
            print(f"   📄 Invoice Details:")
            print(f"      Invoice Number: {invoice_data['invoice_number']}")
            print(f"      Amount: ${invoice_data['amount']:.2f} {invoice_data['currency']}")
            print(f"      Status: {invoice_data['status']}")
            print(f"      PDF Available: {invoice_data['pdf_url'] is not None}")
        else:
            print(f"   ❌ Failed: {download_result['error']}")
    
    def demonstrate_usage_tracking_and_limits(self):
        """Demonstrate usage tracking and limits display"""
        print("\n=== Usage Tracking and Limits Display ===")
        
        print(f"\n🔄 Testing Usage Tracking:")
        
        # Test for budget user (near limits)
        print(f"\n1. Budget User - Usage Tracking (Near Limits):")
        usage_result = self.customer_portal.get_usage_tracking_and_limits(
            customer_id=self.customers[0].id
        )
        
        if usage_result['success']:
            usage_data = usage_result['usage_tracking']
            
            print(f"   ✅ Usage tracking retrieved")
            print(f"   📋 Subscription Info:")
            print(f"      Tier: {usage_data['tier']['name']} ({usage_data['tier']['type']})")
            print(f"      Description: {usage_data['tier']['description']}")
            
            print(f"   📊 Current Usage:")
            current_usage = usage_data['current_usage']
            for feature, amount in current_usage.items():
                if amount > 0:
                    print(f"      {feature}: {amount}")
            
            print(f"   🎯 Tier Limits:")
            tier_limits = usage_data['tier_limits']
            for feature, limit in tier_limits.items():
                if limit != 0:
                    limit_text = "Unlimited" if limit == -1 else str(limit)
                    print(f"      {feature}: {limit_text}")
            
            print(f"   📈 Usage Analysis:")
            usage_analysis = usage_data['usage_analysis']
            for feature, analysis in usage_analysis.items():
                if analysis['used'] > 0:
                    print(f"      {feature}:")
                    print(f"         Used: {analysis['used']}")
                    limit_text = "Unlimited" if analysis['limit'] == -1 else str(analysis['limit'])
                    print(f"         Limit: {limit_text}")
                    print(f"         Percentage: {analysis['percentage']:.1f}%")
                    print(f"         Status: {analysis['status']}")
                    if analysis['remaining'] != -1:
                        print(f"         Remaining: {analysis['remaining']}")
            
            print(f"   📊 Usage Trends:")
            trends = usage_data['usage_trends']
            for period, trend_data in trends.items():
                print(f"      {period}:")
                for feature, amount in trend_data.items():
                    if amount > 0:
                        print(f"         {feature}: {amount}")
            
            print(f"   💡 Upgrade Recommendations:")
            recommendations = usage_data['upgrade_recommendations']
            for rec in recommendations:
                print(f"      {rec['type'].title()}: {rec['message']}")
                print(f"         Priority: {rec['priority']}")
        else:
            print(f"   ❌ Failed: {usage_result['error']}")
        
        # Test for professional user (unlimited)
        print(f"\n2. Professional User - Usage Tracking (Unlimited):")
        usage_result = self.customer_portal.get_usage_tracking_and_limits(
            customer_id=self.customers[2].id
        )
        
        if usage_result['success']:
            usage_data = usage_result['usage_tracking']
            
            print(f"   ✅ Usage tracking retrieved")
            print(f"   📋 Subscription Info:")
            print(f"      Tier: {usage_data['tier']['name']} ({usage_data['tier']['type']})")
            
            print(f"   📊 Current Usage:")
            current_usage = usage_data['current_usage']
            for feature, amount in current_usage.items():
                if amount > 0:
                    print(f"      {feature}: {amount}")
            
            print(f"   🎯 Tier Limits:")
            tier_limits = usage_data['tier_limits']
            for feature, limit in tier_limits.items():
                if limit != 0:
                    limit_text = "Unlimited" if limit == -1 else str(limit)
                    print(f"      {feature}: {limit_text}")
        else:
            print(f"   ❌ Failed: {usage_result['error']}")
    
    def demonstrate_upgrade_downgrade_options(self):
        """Demonstrate subscription upgrade/downgrade options"""
        print("\n=== Subscription Upgrade/Downgrade Options ===")
        
        print(f"\n🔄 Testing Upgrade/Downgrade Options:")
        
        # Test for budget user
        print(f"\n1. Budget User - Upgrade/Downgrade Options:")
        options_result = self.customer_portal.get_subscription_upgrade_downgrade_options(
            customer_id=self.customers[0].id
        )
        
        if options_result['success']:
            options_data = options_result['upgrade_downgrade_options']
            
            print(f"   ✅ Upgrade/downgrade options retrieved")
            print(f"   📋 Current Subscription:")
            current_sub = options_data['current_subscription']
            print(f"      Tier: {current_sub['tier_name']} ({current_sub['tier_type']})")
            print(f"      Price: ${current_sub['current_price']:.2f}/{current_sub['billing_cycle']}")
            
            print(f"   🚀 Upgrade Options:")
            upgrade_options = options_data['upgrade_options']
            for option in upgrade_options:
                print(f"      {option['tier_name']} ({option['tier_type']})")
                print(f"         Price: ${option['new_price']:.2f}/month")
                print(f"         Price Difference: {option['price_difference_formatted']}")
                print(f"         Recommended: {option['recommended']}")
                print(f"         Benefits:")
                for benefit in option['benefits']:
                    print(f"            - {benefit}")
                print(f"         Feature Comparison:")
                comparison = option['feature_comparison']
                for feature, comp in comparison.items():
                    if comp['status'] != 'same':
                        status_emoji = "⬆️" if comp['status'] == 'upgrade' else "⬇️"
                        print(f"            {status_emoji} {feature}: {comp['current']} → {comp['new']}")
            
            print(f"   📉 Downgrade Options:")
            downgrade_options = options_data['downgrade_options']
            for option in downgrade_options:
                print(f"      {option['tier_name']} ({option['tier_type']})")
                print(f"         Price: ${option['new_price']:.2f}/month")
                print(f"         Price Difference: {option['price_difference_formatted']}")
                print(f"         Savings: {option['savings_percentage']:.1f}%")
                print(f"         Limitations:")
                for limitation in option['limitations']:
                    print(f"            - {limitation}")
            
            print(f"   💰 Proration Info:")
            proration_info = options_data['proration_info']
            print(f"      Available: {proration_info['proration_available']}")
            print(f"      Method: {proration_info['proration_method']}")
            print(f"      Description: {proration_info['proration_description']}")
        else:
            print(f"   ❌ Failed: {options_result['error']}")
        
        # Test for mid-tier user
        print(f"\n2. Mid-Tier User - Upgrade/Downgrade Options:")
        options_result = self.customer_portal.get_subscription_upgrade_downgrade_options(
            customer_id=self.customers[1].id
        )
        
        if options_result['success']:
            options_data = options_result['upgrade_downgrade_options']
            
            print(f"   ✅ Upgrade/downgrade options retrieved")
            print(f"   📋 Current Subscription:")
            current_sub = options_data['current_subscription']
            print(f"      Tier: {current_sub['tier_name']} ({current_sub['tier_type']})")
            print(f"      Price: ${current_sub['current_price']:.2f}/{current_sub['billing_cycle']}")
            
            print(f"   🚀 Upgrade Options:")
            upgrade_options = options_data['upgrade_options']
            for option in upgrade_options:
                print(f"      {option['tier_name']} ({option['tier_type']})")
                print(f"         Price: ${option['new_price']:.2f}/month")
                print(f"         Price Difference: {option['price_difference_formatted']}")
                print(f"         Recommended: {option['recommended']}")
            
            print(f"   📉 Downgrade Options:")
            downgrade_options = options_data['downgrade_options']
            for option in downgrade_options:
                print(f"      {option['tier_name']} ({option['tier_type']})")
                print(f"         Price: ${option['new_price']:.2f}/month")
                print(f"         Price Difference: {option['price_difference_formatted']}")
                print(f"         Savings: {option['savings_percentage']:.1f}%")
        else:
            print(f"   ❌ Failed: {options_result['error']}")
    
    def demonstrate_cancellation_with_retention_offers(self):
        """Demonstrate cancellation with retention offers"""
        print("\n=== Cancellation with Retention Offers ===")
        
        print(f"\n🔄 Testing Cancellation with Retention Offers:")
        
        # Test cancellation for budget user
        print(f"\n1. Budget User - Cancellation with Retention Offers:")
        cancellation_result = self.customer_portal.cancel_subscription_with_retention_offers(
            customer_id=self.customers[0].id,
            subscription_id=self.subscriptions[0].id,
            cancellation_reason='Too expensive'
        )
        
        if cancellation_result['success']:
            cancellation_data = cancellation_result['cancellation_request']
            
            print(f"   ✅ Cancellation request created")
            print(f"   📋 Cancellation Details:")
            print(f"      Subscription ID: {cancellation_data['subscription_id']}")
            print(f"      Reason: {cancellation_data['reason']}")
            print(f"      Requested At: {cancellation_data['requested_at']}")
            print(f"      Effective Date: {cancellation_data['effective_date']}")
            
            print(f"   🎁 Retention Offers:")
            retention_offers = cancellation_data['retention_offers']
            for offer in retention_offers:
                print(f"      {offer['title']}:")
                print(f"         Type: {offer['type']}")
                print(f"         Description: {offer['description']}")
                if 'discount_percentage' in offer:
                    print(f"         Discount: {offer['discount_percentage']}%")
                if 'duration_months' in offer:
                    print(f"         Duration: {offer['duration_months']} months")
                print(f"         Savings: ${offer['savings']:.2f}")
                print(f"         Offer Code: {offer['offer_code']}")
            
            print(f"   🔗 Action URLs:")
            print(f"      Cancel: {cancellation_data['cancellation_url']}")
            print(f"      Retention: {cancellation_data['retention_url']}")
        else:
            print(f"   ❌ Failed: {cancellation_result['error']}")
        
        # Test cancellation for professional user (high usage)
        print(f"\n2. Professional User - Cancellation with Retention Offers:")
        cancellation_result = self.customer_portal.cancel_subscription_with_retention_offers(
            customer_id=self.customers[2].id,
            subscription_id=self.subscriptions[2].id,
            cancellation_reason='Not using enough features'
        )
        
        if cancellation_result['success']:
            cancellation_data = cancellation_result['cancellation_request']
            
            print(f"   ✅ Cancellation request created")
            print(f"   🎁 Retention Offers:")
            retention_offers = cancellation_data['retention_offers']
            for offer in retention_offers:
                print(f"      {offer['title']}:")
                print(f"         Type: {offer['type']}")
                print(f"         Description: {offer['description']}")
                print(f"         Savings: ${offer['savings']:.2f}")
                print(f"         Offer Code: {offer['offer_code']}")
        else:
            print(f"   ❌ Failed: {cancellation_result['error']}")
    
    def demonstrate_reactivation(self):
        """Demonstrate reactivation for canceled subscriptions"""
        print("\n=== Reactivation for Canceled Subscriptions ===")
        
        print(f"\n🔄 Testing Reactivation:")
        
        # Test reactivation for professional user (canceled subscription)
        print(f"\n1. Professional User - Reactivation:")
        reactivation_result = self.customer_portal.reactivate_canceled_subscription(
            customer_id=self.customers[2].id,
            subscription_id=self.subscriptions[2].id,
            payment_method_id=5  # Assuming this exists
        )
        
        if reactivation_result['success']:
            reactivation_data = reactivation_result['reactivation']
            
            print(f"   ✅ Subscription reactivated successfully")
            print(f"   📋 Reactivation Details:")
            print(f"      Subscription ID: {reactivation_data['subscription_id']}")
            print(f"      Status: {reactivation_data['status']}")
            print(f"      Reactivated At: {reactivation_data['reactivated_at']}")
            print(f"      Next Billing Date: {reactivation_data['next_billing_date']}")
            print(f"      Amount: ${reactivation_data['amount']:.2f} {reactivation_data['currency']}")
            print(f"      Message: {reactivation_data['message']}")
        else:
            print(f"   ❌ Failed: {reactivation_result['error']}")
        
        # Test reactivation for active subscription (should fail)
        print(f"\n2. Budget User - Reactivation (Should Fail):")
        reactivation_result = self.customer_portal.reactivate_canceled_subscription(
            customer_id=self.customers[0].id,
            subscription_id=self.subscriptions[0].id
        )
        
        if not reactivation_result['success']:
            print(f"   ✅ Correctly failed: {reactivation_result['error']}")
        else:
            print(f"   ❌ Unexpectedly succeeded")
    
    def run_all_feature_demonstrations(self):
        """Run all customer portal feature demonstrations"""
        print("🚀 MINGUS Customer Portal Features Demonstration")
        print("=" * 70)
        
        try:
            self.demonstrate_subscription_status_and_details()
            self.demonstrate_payment_method_management()
            self.demonstrate_billing_history_and_downloads()
            self.demonstrate_usage_tracking_and_limits()
            self.demonstrate_upgrade_downgrade_options()
            self.demonstrate_cancellation_with_retention_offers()
            self.demonstrate_reactivation()
            
            print("\n✅ All customer portal feature demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = CustomerPortalFeaturesExample()
    example.run_all_feature_demonstrations()

if __name__ == "__main__":
    main() 