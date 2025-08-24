"""
Customer Portal Example for MINGUS
Demonstrates comprehensive billing dashboard and self-service capabilities
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

class CustomerPortalExample:
    """Example demonstrating comprehensive customer portal functionality"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_customer_portal_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.customer_portal = CustomerPortal(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for customer portal demonstration"""
        # Create pricing tiers
        budget_tier = PricingTier(
            tier_type='budget',
            name='Budget',
            description='Basic features for individual users',
            monthly_price=15.00,
            yearly_price=150.00,
            max_health_checkins_per_month=4,
            max_financial_reports_per_month=2,
            max_ai_insights_per_month=0
        )
        
        mid_tier = PricingTier(
            tier_type='mid_tier',
            name='Mid-Tier',
            description='Enhanced features for serious users',
            monthly_price=35.00,
            yearly_price=350.00,
            max_health_checkins_per_month=12,
            max_financial_reports_per_month=10,
            max_ai_insights_per_month=50
        )
        
        professional_tier = PricingTier(
            tier_type='professional',
            name='Professional',
            description='Complete solution for professionals',
            monthly_price=75.00,
            yearly_price=750.00,
            max_health_checkins_per_month=-1,
            max_financial_reports_per_month=-1,
            max_ai_insights_per_month=-1
        )
        
        self.db_session.add_all([budget_tier, mid_tier, professional_tier])
        self.db_session.commit()
        
        # Create sample customers
        customers = []
        for i, tier in enumerate(['budget', 'mid_tier', 'professional']):
            customer = Customer(
                user_id=i + 1,
                stripe_customer_id=f'cus_{tier}_portal_demo_{i}',
                email=f'{tier}.portal.user{i}@example.com',
                name=f'{tier.title()} Portal User {i}',
                address={'country': 'US', 'state': 'CA'},
                phone='+1-555-0123'
            )
            customers.append(customer)
        
        self.db_session.add_all(customers)
        self.db_session.commit()
        
        # Create subscriptions
        subscriptions = []
        
        # Budget user with active subscription
        budget_subscription = Subscription(
            customer_id=customers[0].id,
            pricing_tier_id=budget_tier.id,
            stripe_subscription_id='sub_budget_portal',
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
            stripe_subscription_id='sub_mid_tier_portal',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=15),
            billing_cycle='monthly',
            amount=35.00,
            currency='USD'
        )
        subscriptions.append(mid_tier_subscription)
        
        # Professional user with active subscription
        professional_subscription = Subscription(
            customer_id=customers[2].id,
            pricing_tier_id=professional_tier.id,
            stripe_subscription_id='sub_professional_portal',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=10),
            current_period_end=datetime.utcnow() + timedelta(days=20),
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
                stripe_payment_method_id=f'pm_{i}_demo',
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
                stripe_invoice_id=f'in_{subscription.id}_demo'
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
                stripe_invoice_id=f'in_{subscription.id}_prev_demo'
            )
            billing_records.append(prev_invoice)
        
        self.db_session.add_all(billing_records)
        self.db_session.commit()
        
        # Create feature usage
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        usage_records = []
        
        # Budget user usage
        budget_usage = FeatureUsage(
            subscription_id=budget_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=3,
            financial_reports_used=1,
            ai_insights_used=0,
            custom_reports_used=0,
            team_members_used=0,
            support_requests_used=1,
            career_risk_management_used=0,
            dedicated_account_manager_used=0
        )
        usage_records.append(budget_usage)
        
        # Mid-tier user usage
        mid_tier_usage = FeatureUsage(
            subscription_id=mid_tier_subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=8,
            financial_reports_used=6,
            ai_insights_used=35,
            custom_reports_used=3,
            team_members_used=0,
            support_requests_used=2,
            career_risk_management_used=5,
            dedicated_account_manager_used=0
        )
        usage_records.append(mid_tier_usage)
        
        # Professional user usage
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
    
    def demonstrate_customer_dashboard(self):
        """Demonstrate comprehensive customer dashboard"""
        print("\n=== Customer Dashboard Demonstration ===")
        
        print(f"\n🔄 Testing Customer Dashboard:")
        
        # Test dashboard for budget user
        print(f"\n1. Budget User Dashboard:")
        dashboard_result = self.customer_portal.get_customer_dashboard(
            customer_id=self.customers[0].id
        )
        
        if dashboard_result['success']:
            dashboard = dashboard_result['dashboard']
            
            print(f"   ✅ Dashboard generated successfully")
            
            # Customer info
            customer_info = dashboard['customer_info']
            print(f"   👤 Customer Info:")
            print(f"      Name: {customer_info['name']}")
            print(f"      Email: {customer_info['email']}")
            print(f"      Status: {customer_info['status']}")
            
            # Subscription info
            subscription = dashboard['subscription']
            if subscription:
                print(f"   📋 Subscription:")
                print(f"      Tier: {subscription['tier']['name']} ({subscription['tier']['type']})")
                print(f"      Status: {subscription['status']}")
                print(f"      Amount: ${subscription['billing']['amount']}/{subscription['billing']['cycle']}")
                print(f"      Next Billing: {subscription['billing']['next_billing']}")
            
            # Billing summary
            billing_summary = dashboard['billing_summary']
            print(f"   💰 Billing Summary:")
            print(f"      Total Billed: ${billing_summary['total_billed']:.2f}")
            print(f"      Total Paid: ${billing_summary['total_paid']:.2f}")
            print(f"      Outstanding: ${billing_summary['outstanding_balance']:.2f}")
            
            # Usage summary
            usage_summary = dashboard['usage_summary']
            print(f"   📊 Usage Summary:")
            for feature, usage in usage_summary.items():
                if usage > 0:
                    print(f"      {feature}: {usage}")
            
            # Quick actions
            quick_actions = dashboard['quick_actions']
            print(f"   ⚡ Quick Actions:")
            for action in quick_actions:
                print(f"      - {action['title']}: {action['description']}")
        else:
            print(f"   ❌ Failed: {dashboard_result['error']}")
        
        # Test dashboard for professional user
        print(f"\n2. Professional User Dashboard:")
        dashboard_result = self.customer_portal.get_customer_dashboard(
            customer_id=self.customers[2].id
        )
        
        if dashboard_result['success']:
            dashboard = dashboard_result['dashboard']
            print(f"   ✅ Dashboard generated successfully")
            
            # Show different features for professional user
            subscription = dashboard['subscription']
            if subscription:
                print(f"   📋 Professional Subscription:")
                print(f"      Tier: {subscription['tier']['name']} ({subscription['tier']['type']})")
                print(f"      Amount: ${subscription['billing']['amount']}/{subscription['billing']['cycle']}")
            
            # Show more usage data
            usage_summary = dashboard['usage_summary']
            print(f"   📊 Professional Usage:")
            for feature, usage in usage_summary.items():
                if usage > 0:
                    print(f"      {feature}: {usage}")
        else:
            print(f"   ❌ Failed: {dashboard_result['error']}")
    
    def demonstrate_subscription_management(self):
        """Demonstrate subscription management interface"""
        print("\n=== Subscription Management Demonstration ===")
        
        print(f"\n🔄 Testing Subscription Management:")
        
        # Test subscription management for budget user
        print(f"\n1. Budget User Subscription Management:")
        management_result = self.customer_portal.get_subscription_management(
            customer_id=self.customers[0].id
        )
        
        if management_result['success']:
            management = management_result['subscription_management']
            
            print(f"   ✅ Subscription management generated")
            
            # Current subscription
            current_sub = management['current_subscription']
            if current_sub:
                print(f"   📋 Current Subscription:")
                print(f"      Tier: {current_sub['tier']['name']}")
                print(f"      Status: {current_sub['status']}")
                print(f"      Amount: ${current_sub['billing']['amount']}/{current_sub['billing']['cycle']}")
            
            # Upgrade options
            upgrade_options = management['upgrade_options']
            print(f"   🚀 Upgrade Options:")
            for option in upgrade_options:
                print(f"      {option['name']} ({option['price']})")
                print(f"         Price Difference: {option['price_difference']}")
                print(f"         Benefits:")
                for benefit in option['benefits']:
                    print(f"            - {benefit}")
            
            # Downgrade options
            downgrade_options = management['downgrade_options']
            print(f"   📉 Downgrade Options:")
            for option in downgrade_options:
                print(f"      {option['name']} ({option['price']})")
                print(f"         Price Difference: {option['price_difference']}")
                print(f"         Limitations:")
                for limitation in option['limitations']:
                    print(f"            - {limitation}")
            
            # Cancellation options
            cancellation_options = management['cancellation_options']
            print(f"   ❌ Cancellation Options:")
            print(f"      Can Cancel: {cancellation_options['can_cancel']}")
            print(f"      Cancel at Period End: {cancellation_options['cancel_at_period_end']}")
            print(f"      Refund Policy: {cancellation_options['refund_policy']}")
            print(f"      Data Retention: {cancellation_options['data_retention']}")
        else:
            print(f"   ❌ Failed: {management_result['error']}")
    
    def demonstrate_billing_history(self):
        """Demonstrate billing history with pagination"""
        print("\n=== Billing History Demonstration ===")
        
        print(f"\n🔄 Testing Billing History:")
        
        # Test billing history for budget user
        print(f"\n1. Budget User Billing History:")
        history_result = self.customer_portal.get_billing_history(
            customer_id=self.customers[0].id,
            page=1,
            per_page=5
        )
        
        if history_result['success']:
            history = history_result['billing_history']
            
            print(f"   ✅ Billing history retrieved")
            
            # Summary
            summary = history['summary']
            print(f"   📊 Billing Summary:")
            print(f"      Total Billed: ${summary['total_billed']:.2f}")
            print(f"      Total Paid: ${summary['total_paid']:.2f}")
            print(f"      Outstanding: ${summary['outstanding']:.2f}")
            
            # Records
            records = history['records']
            print(f"   📄 Billing Records:")
            for record in records:
                print(f"      Invoice: {record['invoice_number']}")
                print(f"         Amount: ${record['amount']:.2f} {record['currency']}")
                print(f"         Status: {record['status']}")
                print(f"         Date: {record['created_at']}")
                if record['download_url']:
                    print(f"         Download: Available")
            
            # Pagination
            pagination = history['pagination']
            print(f"   📑 Pagination:")
            print(f"      Current Page: {pagination['current_page']}")
            print(f"      Total Pages: {pagination['total_pages']}")
            print(f"      Total Records: {pagination['total_count']}")
            print(f"      Has Next: {pagination['has_next']}")
            print(f"      Has Prev: {pagination['has_prev']}")
        else:
            print(f"   ❌ Failed: {history_result['error']}")
    
    def demonstrate_payment_methods(self):
        """Demonstrate payment method management"""
        print("\n=== Payment Methods Demonstration ===")
        
        print(f"\n🔄 Testing Payment Methods:")
        
        # Test payment methods for budget user
        print(f"\n1. Budget User Payment Methods:")
        payment_result = self.customer_portal.get_payment_methods(
            customer_id=self.customers[0].id
        )
        
        if payment_result['success']:
            payment_data = payment_result['payment_methods']
            
            print(f"   ✅ Payment methods retrieved")
            
            # Payment methods
            payment_methods = payment_data['payment_methods']
            print(f"   💳 Payment Methods:")
            for method in payment_methods:
                print(f"      {method['brand'].title()} ending in {method['last4']}")
                print(f"         Expires: {method['exp_month']}/{method['exp_year']}")
                print(f"         Default: {method['is_default']}")
            
            # Limits
            print(f"   📊 Limits:")
            print(f"      Can Add Methods: {payment_data['can_add_methods']}")
            print(f"      Max Methods: {payment_data['max_methods']}")
        else:
            print(f"   ❌ Failed: {payment_result['error']}")
    
    def demonstrate_usage_analytics(self):
        """Demonstrate usage analytics"""
        print("\n=== Usage Analytics Demonstration ===")
        
        print(f"\n🔄 Testing Usage Analytics:")
        
        # Test usage analytics for mid-tier user
        print(f"\n1. Mid-Tier User Usage Analytics:")
        analytics_result = self.customer_portal.get_usage_analytics(
            customer_id=self.customers[1].id,
            date_range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow())
        )
        
        if analytics_result['success']:
            analytics = analytics_result['usage_analytics']
            
            print(f"   ✅ Usage analytics generated")
            
            # Subscriptions
            subscriptions = analytics['subscriptions']
            print(f"   📊 Subscription Usage:")
            for sub_data in subscriptions:
                print(f"      Tier: {sub_data['tier']}")
                usage = sub_data['usage']
                for feature, amount in usage.items():
                    if amount > 0:
                        print(f"         {feature}: {amount}")
            
            # Usage summary
            usage_summary = analytics['usage_summary']
            print(f"   📈 Usage Summary:")
            for feature, amount in usage_summary.items():
                if amount > 0:
                    print(f"      {feature}: {amount}")
            
            # Trends
            trends = analytics['trends']
            print(f"   📊 Usage Trends:")
            print(f"      Trend: {trends['trend']}")
            print(f"      Growth Rate: {trends['growth_rate']}%")
            print(f"      Peak Usage Month: {trends['peak_usage_month']}")
            print(f"      Usage Pattern: {trends['usage_pattern']}")
            
            # Recommendations
            recommendations = analytics['recommendations']
            print(f"   💡 Recommendations:")
            for rec in recommendations:
                print(f"      {rec['type'].title()}: {rec['title']}")
                print(f"         {rec['message']}")
                print(f"         Priority: {rec['priority']}")
        else:
            print(f"   ❌ Failed: {analytics_result['error']}")
    
    def demonstrate_payment_method_operations(self):
        """Demonstrate payment method operations"""
        print("\n=== Payment Method Operations Demonstration ===")
        
        print(f"\n🔄 Testing Payment Method Operations:")
        
        # Test setting default payment method
        print(f"\n1. Setting Default Payment Method:")
        set_default_result = self.customer_portal.set_default_payment_method(
            customer_id=self.customers[0].id,
            payment_method_id=1  # Assuming this exists
        )
        
        if set_default_result['success']:
            print(f"   ✅ Default payment method set successfully")
            print(f"   📢 Message: {set_default_result['message']}")
        else:
            print(f"   ❌ Failed: {set_default_result['error']}")
        
        # Test updating payment method
        print(f"\n2. Updating Payment Method:")
        update_result = self.customer_portal.update_payment_method(
            customer_id=self.customers[0].id,
            payment_method_id=1,
            updates={'exp_month': 11, 'exp_year': 2026}
        )
        
        if update_result['success']:
            print(f"   ✅ Payment method updated successfully")
            print(f"   📢 Message: {update_result['message']}")
        else:
            print(f"   ❌ Failed: {update_result['error']}")
    
    def demonstrate_support_requests(self):
        """Demonstrate support request functionality"""
        print("\n=== Support Requests Demonstration ===")
        
        print(f"\n🔄 Testing Support Requests:")
        
        # Test creating support request
        print(f"\n1. Creating Support Request:")
        support_result = self.customer_portal.create_support_request(
            customer_id=self.customers[0].id,
            request_data={
                'subject': 'Billing Question',
                'description': 'I have a question about my recent invoice.',
                'priority': 'medium'
            }
        )
        
        if support_result['success']:
            support_request = support_result['support_request']
            print(f"   ✅ Support request created successfully")
            print(f"   📋 Request Details:")
            print(f"      ID: {support_request['id']}")
            print(f"      Subject: {support_request['subject']}")
            print(f"      Status: {support_request['status']}")
            print(f"      Priority: {support_request['priority']}")
            print(f"      Created: {support_request['created_at']}")
        else:
            print(f"   ❌ Failed: {support_result['error']}")
    
    def demonstrate_account_settings(self):
        """Demonstrate account settings management"""
        print("\n=== Account Settings Demonstration ===")
        
        print(f"\n🔄 Testing Account Settings:")
        
        # Test getting account settings
        print(f"\n1. Getting Account Settings:")
        settings_result = self.customer_portal.get_account_settings(
            customer_id=self.customers[0].id
        )
        
        if settings_result['success']:
            settings = settings_result['account_settings']
            
            print(f"   ✅ Account settings retrieved")
            
            # Customer info
            customer_info = settings['customer_info']
            print(f"   👤 Customer Information:")
            print(f"      Name: {customer_info['name']}")
            print(f"      Email: {customer_info['email']}")
            print(f"      Phone: {customer_info['phone']}")
            
            # Billing preferences
            billing_prefs = settings['billing_preferences']
            print(f"   💰 Billing Preferences:")
            print(f"      Billing Cycle: {billing_prefs['billing_cycle']}")
            print(f"      Invoice Delivery: {billing_prefs['invoice_delivery']}")
            print(f"      Payment Reminders: {billing_prefs['payment_reminders']}")
            print(f"      Usage Alerts: {billing_prefs['usage_alerts']}")
            
            # Notification settings
            notification_settings = settings['notification_settings']
            print(f"   🔔 Notification Settings:")
            print(f"      Email Notifications: {notification_settings['email_notifications']}")
            print(f"      Billing Alerts: {notification_settings['billing_alerts']}")
            print(f"      Usage Alerts: {notification_settings['usage_alerts']}")
            print(f"      Security Alerts: {notification_settings['security_alerts']}")
            
            # Security settings
            security_settings = settings['security_settings']
            print(f"   🔒 Security Settings:")
            print(f"      Two Factor Enabled: {security_settings['two_factor_enabled']}")
            print(f"      Session Timeout: {security_settings['session_timeout']} minutes")
        else:
            print(f"   ❌ Failed: {settings_result['error']}")
        
        # Test updating account settings
        print(f"\n2. Updating Account Settings:")
        update_result = self.customer_portal.update_account_settings(
            customer_id=self.customers[0].id,
            updates={
                'customer_info': {
                    'name': 'Updated Portal User',
                    'email': 'updated.portal.user@example.com'
                }
            }
        )
        
        if update_result['success']:
            print(f"   ✅ Account settings updated successfully")
            print(f"   📢 Message: {update_result['message']}")
        else:
            print(f"   ❌ Failed: {update_result['error']}")
    
    def demonstrate_invoice_download(self):
        """Demonstrate invoice download functionality"""
        print("\n=== Invoice Download Demonstration ===")
        
        print(f"\n🔄 Testing Invoice Download:")
        
        # Test downloading invoice
        print(f"\n1. Downloading Invoice:")
        download_result = self.customer_portal.download_invoice(
            customer_id=self.customers[0].id,
            invoice_id=1  # Assuming this exists
        )
        
        if download_result['success']:
            invoice_data = download_result['invoice_data']
            print(f"   ✅ Invoice download successful")
            print(f"   📄 Invoice Details:")
            print(f"      Invoice Number: {invoice_data['invoice_number']}")
            print(f"      Amount: ${invoice_data['amount']:.2f} {invoice_data['currency']}")
            print(f"      Status: {invoice_data['status']}")
            print(f"      Created: {invoice_data['created_at']}")
            print(f"      PDF Available: {invoice_data['pdf_url'] is not None}")
        else:
            print(f"   ❌ Failed: {download_result['error']}")
    
    def run_all_demonstrations(self):
        """Run all customer portal demonstrations"""
        print("🚀 MINGUS Customer Portal Demonstration")
        print("=" * 65)
        
        try:
            self.demonstrate_customer_dashboard()
            self.demonstrate_subscription_management()
            self.demonstrate_billing_history()
            self.demonstrate_payment_methods()
            self.demonstrate_usage_analytics()
            self.demonstrate_payment_method_operations()
            self.demonstrate_support_requests()
            self.demonstrate_account_settings()
            self.demonstrate_invoice_download()
            
            print("\n✅ All customer portal demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = CustomerPortalExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 