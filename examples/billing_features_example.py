"""
Billing Features Example for MINGUS
Demonstrates usage of all billing features including automatic invoice generation,
email delivery, dunning management, tax calculation, and currency handling
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.payment_service import PaymentService
from services.billing_features import BillingFeatures
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory

class BillingFeaturesExample:
    """Example demonstrating all billing features"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_billing_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.payment_service = PaymentService(self.db_session, self.config)
        self.billing_features = BillingFeatures(self.db_session, self.config)
        
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
        
        self.db_session.add_all([budget_tier, mid_tier])
        self.db_session.commit()
        
        # Create sample customer
        customer = Customer(
            user_id=1,
            stripe_customer_id='cus_sample123',
            email='john.doe@example.com',
            name='John Doe',
            address={
                'country': 'US',
                'state': 'CA',
                'city': 'San Francisco',
                'postal_code': '94102'
            }
        )
        
        self.db_session.add(customer)
        self.db_session.commit()
        
        # Create sample subscription
        subscription = Subscription(
            customer_id=customer.id,
            pricing_tier_id=mid_tier.id,
            stripe_subscription_id='sub_sample123',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=30),
            current_period_end=datetime.utcnow(),
            billing_cycle='monthly',
            amount=29.99,
            currency='USD'
        )
        
        self.db_session.add(subscription)
        self.db_session.commit()
        
        self.sample_customer = customer
        self.sample_subscription = subscription
    
    def demonstrate_automatic_invoice_generation(self):
        """Demonstrate automatic invoice generation"""
        print("\n=== Automatic Invoice Generation ===")
        
        # Generate automatic invoice
        result = self.payment_service.generate_automatic_invoice(
            subscription_id=self.sample_subscription.id,
            invoice_type='recurring',
            description='Monthly subscription billing'
        )
        
        if result['success']:
            print(f"✅ Invoice generated successfully!")
            print(f"   Invoice ID: {result['invoice_id']}")
            print(f"   Invoice Number: {result['invoice_number']}")
            print(f"   Amount: ${result['amount']:.2f}")
            print(f"   PDF Path: {result['pdf_path']}")
            print(f"   Email Sent: {result['email_sent']}")
        else:
            print(f"❌ Failed to generate invoice: {result['error']}")
    
    def demonstrate_email_delivery(self):
        """Demonstrate email delivery features"""
        print("\n=== Email Delivery ===")
        
        # Get the latest invoice
        invoice = self.db_session.query(BillingHistory).filter(
            BillingHistory.subscription_id == self.sample_subscription.id
        ).order_by(BillingHistory.created_at.desc()).first()
        
        if invoice:
            # Send invoice email
            email_result = self.payment_service.send_invoice_email(invoice.id)
            
            if email_result['success']:
                print(f"✅ Invoice email sent successfully!")
                print(f"   Sent to: {self.sample_customer.email}")
                print(f"   Sent at: {email_result['sent_at']}")
            else:
                print(f"❌ Failed to send invoice email: {email_result['error']}")
            
            # Simulate payment and send receipt
            invoice.paid = True
            invoice.amount_paid = invoice.amount_due
            invoice.paid_date = datetime.utcnow()
            self.db_session.commit()
            
            receipt_result = self.payment_service.send_payment_receipt_email(invoice.id)
            
            if receipt_result['success']:
                print(f"✅ Payment receipt email sent successfully!")
            else:
                print(f"❌ Failed to send receipt email: {receipt_result['error']}")
    
    def demonstrate_dunning_management(self):
        """Demonstrate dunning management"""
        print("\n=== Dunning Management ===")
        
        # Create an overdue invoice for demonstration
        overdue_invoice = BillingHistory(
            customer_id=self.sample_customer.id,
            subscription_id=self.sample_subscription.id,
            stripe_invoice_id='inv_overdue123',
            invoice_number='INV-000001-0002-2024',
            amount_due=29.99,
            amount_paid=0,
            currency='USD',
            status='past_due',
            paid=False,
            invoice_date=datetime.utcnow() - timedelta(days=10),
            due_date=datetime.utcnow() - timedelta(days=3),
            description='Overdue invoice for demonstration'
        )
        
        self.db_session.add(overdue_invoice)
        self.db_session.commit()
        
        # Process dunning management
        dunning_result = self.payment_service.process_dunning_management()
        
        print(f"✅ Dunning management processed!")
        print(f"   Processed: {dunning_result['processed']} invoices")
        print(f"   Dunning emails sent: {dunning_result['dunning_emails_sent']}")
        print(f"   Subscriptions suspended: {dunning_result['subscriptions_suspended']}")
        
        if dunning_result['errors']:
            print(f"   Errors: {len(dunning_result['errors'])}")
    
    def demonstrate_tax_calculation(self):
        """Demonstrate tax calculation"""
        print("\n=== Tax Calculation ===")
        
        # Calculate tax for different scenarios
        scenarios = [
            {'amount': 29.99, 'currency': 'USD', 'tax_exempt': None},
            {'amount': 99.99, 'currency': 'USD', 'tax_exempt': 'exempt'},
            {'amount': 49.99, 'currency': 'EUR', 'tax_exempt': None}
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            tax_result = self.payment_service.calculate_tax(
                customer_id=self.sample_customer.id,
                amount=scenario['amount'],
                currency=scenario['currency'],
                tax_exempt=scenario['tax_exempt']
            )
            
            print(f"Scenario {i}:")
            print(f"   Amount: ${scenario['amount']:.2f} {scenario['currency']}")
            print(f"   Tax Exempt: {scenario['tax_exempt'] or 'No'}")
            print(f"   Tax Amount: ${tax_result['tax_amount']:.2f}")
            print(f"   Tax Rate: {tax_result['tax_rate']:.2%}")
            print(f"   Total: ${scenario['amount'] + tax_result['tax_amount']:.2f}")
            print()
    
    def demonstrate_currency_handling(self):
        """Demonstrate currency handling"""
        print("\n=== Currency Handling ===")
        
        # Convert between currencies
        conversions = [
            {'from': 'USD', 'to': 'EUR', 'amount': 29.99},
            {'from': 'USD', 'to': 'GBP', 'amount': 99.99},
            {'from': 'EUR', 'to': 'USD', 'amount': 25.50},
            {'from': 'GBP', 'to': 'CAD', 'amount': 75.00}
        ]
        
        for conversion in conversions:
            result = self.payment_service.convert_currency(
                amount=conversion['amount'],
                from_currency=conversion['from'],
                to_currency=conversion['to']
            )
            
            if 'error' not in result:
                print(f"✅ {conversion['amount']:.2f} {conversion['from']} = {result['converted_amount']:.2f} {conversion['to']}")
                print(f"   Exchange Rate: {result['exchange_rate']:.4f}")
            else:
                print(f"❌ Currency conversion failed: {result['error']}")
        
        # Format currency amounts
        currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
        amount = 29.99
        
        print(f"\nCurrency formatting for ${amount:.2f}:")
        for currency in currencies:
            formatted = self.payment_service.format_currency(amount, currency)
            print(f"   {currency}: {formatted}")
        
        # Get supported currencies
        supported_currencies = self.payment_service.get_supported_currencies()
        print(f"\nSupported currencies:")
        for currency in supported_currencies:
            print(f"   {currency['code']} - {currency['name']} ({currency['symbol']})")
    
    def demonstrate_automated_billing_cycle(self):
        """Demonstrate complete automated billing cycle"""
        print("\n=== Automated Billing Cycle ===")
        
        # Run automated billing cycle
        cycle_result = self.payment_service.run_automated_billing_cycle()
        
        if cycle_result['success']:
            results = cycle_result['results']
            print(f"✅ Automated billing cycle completed!")
            print(f"   Invoices generated: {results['invoices_generated']}")
            print(f"   Emails sent: {results['emails_sent']}")
            print(f"   Dunning processed: {results['dunning_processed']}")
            
            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")
                for error in results['errors'][:3]:  # Show first 3 errors
                    print(f"     - {error['error']}")
        else:
            print(f"❌ Automated billing cycle failed: {cycle_result['error']}")
    
    def demonstrate_integration_example(self):
        """Demonstrate integration of all features"""
        print("\n=== Complete Integration Example ===")
        
        # Create a new subscription with payment
        subscription_result = self.payment_service.create_subscription_with_payment(
            user_id=2,
            email='jane.smith@example.com',
            name='Jane Smith',
            pricing_tier_id=1,  # Budget tier
            payment_method_id='pm_demo123',
            billing_cycle='monthly',
            trial_days=14
        )
        
        if subscription_result['success']:
            print(f"✅ New subscription created!")
            print(f"   Customer ID: {subscription_result['customer_id']}")
            print(f"   Subscription ID: {subscription_result['subscription_id']}")
            print(f"   Trial End: {subscription_result['trial_end']}")
            
            # Generate invoice with tax calculation
            invoice_result = self.payment_service.generate_automatic_invoice(
                subscription_id=subscription_result['subscription_id'],
                invoice_type='recurring'
            )
            
            if invoice_result['success']:
                print(f"✅ Invoice generated with tax calculation!")
                
                # Send invoice email
                email_result = self.payment_service.send_invoice_email(
                    invoice_result['invoice_id']
                )
                
                if email_result['success']:
                    print(f"✅ Invoice email sent!")
                else:
                    print(f"❌ Email failed: {email_result['error']}")
            else:
                print(f"❌ Invoice generation failed: {invoice_result['error']}")
        else:
            print(f"❌ Subscription creation failed: {subscription_result['error']}")
    
    def run_all_demonstrations(self):
        """Run all demonstrations"""
        print("🚀 MINGUS Billing Features Demonstration")
        print("=" * 50)
        
        try:
            self.demonstrate_automatic_invoice_generation()
            self.demonstrate_email_delivery()
            self.demonstrate_dunning_management()
            self.demonstrate_tax_calculation()
            self.demonstrate_currency_handling()
            self.demonstrate_automated_billing_cycle()
            self.demonstrate_integration_example()
            
            print("\n✅ All demonstrations completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.db_session.close()

def main():
    """Main function to run the demonstration"""
    example = BillingFeaturesExample()
    example.run_all_demonstrations()

if __name__ == "__main__":
    main() 