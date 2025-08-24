"""
Enhanced Payment Processing Handlers Example
Demonstrates comprehensive payment success and failure handling
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webhooks.stripe_webhooks import StripeWebhookManager, WebhookEvent
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory

class PaymentProcessingHandlersExample:
    """Example demonstrating enhanced payment processing handlers"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///payment_processing_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.webhook_manager = StripeWebhookManager(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for payment processing demonstration"""
        print("📊 Creating sample data for payment processing testing...")
        
        # Create pricing tiers
        tiers = [
            PricingTier(
                name="Basic Tier",
                monthly_price=10.00,
                yearly_price=100.00,
                stripe_price_id_monthly="price_basic_monthly",
                stripe_price_id_yearly="price_basic_yearly",
                features=["basic_features", "email_support"]
            ),
            PricingTier(
                name="Pro Tier",
                monthly_price=25.00,
                yearly_price=250.00,
                stripe_price_id_monthly="price_pro_monthly",
                stripe_price_id_yearly="price_pro_yearly",
                features=["advanced_features", "priority_support", "analytics"]
            ),
            PricingTier(
                name="Enterprise Tier",
                monthly_price=75.00,
                yearly_price=750.00,
                stripe_price_id_monthly="price_enterprise_monthly",
                stripe_price_id_yearly="price_enterprise_yearly",
                features=["enterprise_features", "dedicated_support", "custom_integrations"]
            )
        ]
        
        for tier in tiers:
            self.db_session.add(tier)
        self.db_session.commit()
        
        # Create customers
        self.customers = []
        customer_data = [
            {
                'name': 'Payment Success User 1',
                'email': 'payment.success1@example.com',
                'stripe_customer_id': 'cus_payment_success_001'
            },
            {
                'name': 'Payment Success User 2',
                'email': 'payment.success2@example.com',
                'stripe_customer_id': 'cus_payment_success_002'
            },
            {
                'name': 'Payment Failure User 1',
                'email': 'payment.failure1@example.com',
                'stripe_customer_id': 'cus_payment_failure_001'
            },
            {
                'name': 'Payment Failure User 2',
                'email': 'payment.failure2@example.com',
                'stripe_customer_id': 'cus_payment_failure_002'
            }
        ]
        
        for data in customer_data:
            customer = Customer(
                name=data['name'],
                email=data['email'],
                stripe_customer_id=data['stripe_customer_id'],
                phone=f"+1-555-{1000 + len(self.customers):04d}",
                address={
                    'country': 'US',
                    'state': 'CA',
                    'city': 'San Francisco',
                    'line1': f'{1000 + len(self.customers)} Test St',
                    'postal_code': '94105'
                }
            )
            self.db_session.add(customer)
            self.customers.append(customer)
        
        self.db_session.commit()
        print(f"✅ Created {len(self.customers)} customers for testing")
    
    def demonstrate_successful_subscription_payment(self):
        """Demonstrate successful subscription payment"""
        print("\n=== Successful Subscription Payment ===")
        
        # Create a successful subscription payment webhook event
        success_event = self._create_successful_subscription_payment_event()
        
        print(f"\n🔄 Processing Successful Subscription Payment:")
        print(f"   📋 Event Type: invoice.payment_succeeded")
        print(f"   👤 Customer: {self.customers[0].email}")
        print(f"   💰 Amount: $25.00")
        print(f"   📅 Billing Period: Monthly")
        print(f"   💳 Payment Method: card_1234567890")
        print(f"   📊 Subscription: Active")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=success_event.encode('utf-8'),
            signature=self._generate_test_signature(success_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_payment_success_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Payment processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_successful_one_time_payment(self):
        """Demonstrate successful one-time payment"""
        print("\n=== Successful One-Time Payment ===")
        
        # Create a successful one-time payment webhook event
        one_time_event = self._create_successful_one_time_payment_event()
        
        print(f"\n🔄 Processing Successful One-Time Payment:")
        print(f"   📋 Event Type: invoice.payment_succeeded")
        print(f"   👤 Customer: {self.customers[1].email}")
        print(f"   💰 Amount: $50.00")
        print(f"   📅 Payment Type: One-time")
        print(f"   💳 Payment Method: card_0987654321")
        print(f"   🎯 Purpose: Feature upgrade")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=one_time_event.encode('utf-8'),
            signature=self._generate_test_signature(one_time_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_one_time_payment_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ One-time payment processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_successful_payment_with_discount(self):
        """Demonstrate successful payment with discount"""
        print("\n=== Successful Payment with Discount ===")
        
        # Create a successful payment with discount webhook event
        discount_event = self._create_successful_payment_with_discount_event()
        
        print(f"\n🔄 Processing Successful Payment with Discount:")
        print(f"   📋 Event Type: invoice.payment_succeeded")
        print(f"   👤 Customer: {self.customers[0].email}")
        print(f"   💰 Original Amount: $75.00")
        print(f"   🎫 Discount: $15.00 (20% off)")
        print(f"   💰 Final Amount: $60.00")
        print(f"   💳 Payment Method: card_1111111111")
        print(f"   🏷️ Coupon: WELCOME20")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=discount_event.encode('utf-8'),
            signature=self._generate_test_signature(discount_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_discount_payment_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Discounted payment processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_first_payment_success(self):
        """Demonstrate first payment success"""
        print("\n=== First Payment Success ===")
        
        # Create a first payment success webhook event
        first_payment_event = self._create_first_payment_success_event()
        
        print(f"\n🔄 Processing First Payment Success:")
        print(f"   📋 Event Type: invoice.payment_succeeded")
        print(f"   👤 Customer: {self.customers[1].email}")
        print(f"   💰 Amount: $10.00")
        print(f"   🎯 First Payment: Yes")
        print(f"   💳 Payment Method: card_2222222222")
        print(f"   📊 Customer Status: New")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=first_payment_event.encode('utf-8'),
            signature=self._generate_test_signature(first_payment_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_first_payment_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ First payment processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_payment_failure_first_attempt(self):
        """Demonstrate payment failure on first attempt"""
        print("\n=== Payment Failure (First Attempt) ===")
        
        # Create a payment failure webhook event
        failure_event = self._create_payment_failure_first_attempt_event()
        
        print(f"\n🔄 Processing Payment Failure (First Attempt):")
        print(f"   📋 Event Type: invoice.payment_failed")
        print(f"   👤 Customer: {self.customers[2].email}")
        print(f"   💰 Amount: $25.00")
        print(f"   ❌ Failure Reason: card_declined")
        print(f"   🔄 Attempt: 1 of 3")
        print(f"   📅 Next Retry: Tomorrow")
        print(f"   💳 Payment Method: card_3333333333")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=failure_event.encode('utf-8'),
            signature=self._generate_test_signature(failure_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_payment_failure_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Payment failure processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_payment_failure_multiple_attempts(self):
        """Demonstrate payment failure after multiple attempts"""
        print("\n=== Payment Failure (Multiple Attempts) ===")
        
        # Create a payment failure after multiple attempts webhook event
        multiple_failure_event = self._create_payment_failure_multiple_attempts_event()
        
        print(f"\n🔄 Processing Payment Failure (Multiple Attempts):")
        print(f"   📋 Event Type: invoice.payment_failed")
        print(f"   👤 Customer: {self.customers[3].email}")
        print(f"   💰 Amount: $75.00")
        print(f"   ❌ Failure Reason: insufficient_funds")
        print(f"   🔄 Attempt: 3 of 3")
        print(f"   ⚠️ Status: Maximum attempts reached")
        print(f"   🚫 Action: Account suspension initiated")
        print(f"   💳 Payment Method: card_4444444444")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=multiple_failure_event.encode('utf-8'),
            signature=self._generate_test_signature(multiple_failure_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_multiple_failure_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Multiple payment failure processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_payment_failure_expired_card(self):
        """Demonstrate payment failure due to expired card"""
        print("\n=== Payment Failure (Expired Card) ===")
        
        # Create a payment failure due to expired card webhook event
        expired_card_event = self._create_payment_failure_expired_card_event()
        
        print(f"\n🔄 Processing Payment Failure (Expired Card):")
        print(f"   📋 Event Type: invoice.payment_failed")
        print(f"   👤 Customer: {self.customers[2].email}")
        print(f"   💰 Amount: $25.00")
        print(f"   ❌ Failure Reason: expired_card")
        print(f"   🔄 Attempt: 1 of 3")
        print(f"   📅 Next Retry: Tomorrow")
        print(f"   💳 Payment Method: card_5555555555")
        print(f"   📧 Action: Payment method update request sent")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=expired_card_event.encode('utf-8'),
            signature=self._generate_test_signature(expired_card_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_expired_card_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Expired card failure processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_subscription_reactivation_payment(self):
        """Demonstrate subscription reactivation payment"""
        print("\n=== Subscription Reactivation Payment ===")
        
        # Create a subscription reactivation payment webhook event
        reactivation_event = self._create_subscription_reactivation_payment_event()
        
        print(f"\n🔄 Processing Subscription Reactivation Payment:")
        print(f"   📋 Event Type: invoice.payment_succeeded")
        print(f"   👤 Customer: {self.customers[0].email}")
        print(f"   💰 Amount: $25.00")
        print(f"   🔄 Subscription Status: past_due → active")
        print(f"   💳 Payment Method: card_6666666666")
        print(f"   📊 Action: Subscription reactivated")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=reactivation_event.encode('utf-8'),
            signature=self._generate_test_signature(reactivation_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Payment-Test/1.0",
            request_id="test_reactivation_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Subscription reactivation payment processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def _create_successful_subscription_payment_event(self) -> str:
        """Create a successful subscription payment event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_succeeded',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_success_subscription_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_success_001',
                    'subscription': 'sub_success_001',
                    'status': 'paid',
                    'amount_due': 2500,
                    'amount_paid': 2500,
                    'amount_remaining': 0,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'period_start': int((datetime.utcnow() - timedelta(days=30)).timestamp()),
                    'period_end': int(datetime.utcnow().timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_success_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_success_001/pdf',
                    'receipt_url': 'https://pay.stripe.com/receipts/test_success_001',
                    'collection_method': 'charge_automatically',
                    'auto_advance': True,
                    'attempt_count': 1,
                    'payment_intent': 'pi_success_001',
                    'charge': 'ch_success_001',
                    'payment_method': 'pm_success_001',
                    'payment_method_types': ['card'],
                    'lines': {
                        'data': [{
                            'id': 'il_success_001',
                            'object': 'line_item',
                            'amount': 2500,
                            'currency': 'usd',
                            'description': 'Pro Tier - Monthly',
                            'quantity': 1,
                            'price': {
                                'id': 'price_pro_monthly',
                                'object': 'price',
                                'unit_amount': 2500,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'successful_subscription_payment',
                        'payment_method': 'card_1234567890'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_successful_one_time_payment_event(self) -> str:
        """Create a successful one-time payment event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_succeeded',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_success_one_time_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_success_002',
                    'subscription': None,
                    'status': 'paid',
                    'amount_due': 5000,
                    'amount_paid': 5000,
                    'amount_remaining': 0,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_one_time_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_one_time_001/pdf',
                    'receipt_url': 'https://pay.stripe.com/receipts/test_one_time_001',
                    'collection_method': 'charge_automatically',
                    'auto_advance': False,
                    'attempt_count': 1,
                    'payment_intent': 'pi_one_time_001',
                    'charge': 'ch_one_time_001',
                    'payment_method': 'pm_one_time_001',
                    'payment_method_types': ['card'],
                    'lines': {
                        'data': [{
                            'id': 'il_one_time_001',
                            'object': 'line_item',
                            'amount': 5000,
                            'currency': 'usd',
                            'description': 'Feature Upgrade Package',
                            'quantity': 1
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'successful_one_time_payment',
                        'payment_method': 'card_0987654321',
                        'purpose': 'feature_upgrade'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_successful_payment_with_discount_event(self) -> str:
        """Create a successful payment with discount event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_succeeded',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_success_discount_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_success_001',
                    'subscription': 'sub_discount_001',
                    'status': 'paid',
                    'amount_due': 6000,
                    'amount_paid': 6000,
                    'amount_remaining': 0,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'period_start': int((datetime.utcnow() - timedelta(days=30)).timestamp()),
                    'period_end': int(datetime.utcnow().timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_discount_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_discount_001/pdf',
                    'receipt_url': 'https://pay.stripe.com/receipts/test_discount_001',
                    'collection_method': 'charge_automatically',
                    'auto_advance': True,
                    'attempt_count': 1,
                    'payment_intent': 'pi_discount_001',
                    'charge': 'ch_discount_001',
                    'payment_method': 'pm_discount_001',
                    'payment_method_types': ['card'],
                    'discount': {
                        'id': 'di_discount_001',
                        'object': 'discount',
                        'amount_off': 1500,
                        'currency': 'usd',
                        'type': 'coupon',
                        'coupon': {
                            'id': 'WELCOME20',
                            'object': 'coupon',
                            'percent_off': 20,
                            'duration': 'once'
                        }
                    },
                    'lines': {
                        'data': [{
                            'id': 'il_discount_001',
                            'object': 'line_item',
                            'amount': 7500,
                            'currency': 'usd',
                            'description': 'Enterprise Tier - Monthly',
                            'quantity': 1,
                            'price': {
                                'id': 'price_enterprise_monthly',
                                'object': 'price',
                                'unit_amount': 7500,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'successful_payment_with_discount',
                        'payment_method': 'card_1111111111',
                        'coupon_used': 'WELCOME20'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_first_payment_success_event(self) -> str:
        """Create a first payment success event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_succeeded',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_first_payment_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_success_002',
                    'subscription': 'sub_first_001',
                    'status': 'paid',
                    'amount_due': 1000,
                    'amount_paid': 1000,
                    'amount_remaining': 0,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'period_start': int(datetime.utcnow().timestamp()),
                    'period_end': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_first_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_first_001/pdf',
                    'receipt_url': 'https://pay.stripe.com/receipts/test_first_001',
                    'collection_method': 'charge_automatically',
                    'auto_advance': True,
                    'attempt_count': 1,
                    'payment_intent': 'pi_first_001',
                    'charge': 'ch_first_001',
                    'payment_method': 'pm_first_001',
                    'payment_method_types': ['card'],
                    'lines': {
                        'data': [{
                            'id': 'il_first_001',
                            'object': 'line_item',
                            'amount': 1000,
                            'currency': 'usd',
                            'description': 'Basic Tier - Monthly',
                            'quantity': 1,
                            'price': {
                                'id': 'price_basic_monthly',
                                'object': 'price',
                                'unit_amount': 1000,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'first_payment_success',
                        'payment_method': 'card_2222222222',
                        'first_payment': 'true'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_payment_failure_first_attempt_event(self) -> str:
        """Create a payment failure first attempt event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_failed',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_failure_first_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_failure_001',
                    'subscription': 'sub_failure_001',
                    'status': 'open',
                    'amount_due': 2500,
                    'amount_paid': 0,
                    'amount_remaining': 2500,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'period_start': int((datetime.utcnow() - timedelta(days=30)).timestamp()),
                    'period_end': int(datetime.utcnow().timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_failure_first_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_failure_first_001/pdf',
                    'collection_method': 'charge_automatically',
                    'auto_advance': True,
                    'attempt_count': 1,
                    'next_payment_attempt': int((datetime.utcnow() + timedelta(days=1)).timestamp()),
                    'last_payment_error': {
                        'type': 'card_error',
                        'code': 'card_declined',
                        'message': 'Your card was declined.'
                    },
                    'lines': {
                        'data': [{
                            'id': 'il_failure_first_001',
                            'object': 'line_item',
                            'amount': 2500,
                            'currency': 'usd',
                            'description': 'Pro Tier - Monthly',
                            'quantity': 1,
                            'price': {
                                'id': 'price_pro_monthly',
                                'object': 'price',
                                'unit_amount': 2500,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'payment_failure_first_attempt',
                        'payment_method': 'card_3333333333',
                        'failure_reason': 'card_declined'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_payment_failure_multiple_attempts_event(self) -> str:
        """Create a payment failure after multiple attempts event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_failed',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_failure_multiple_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_failure_002',
                    'subscription': 'sub_failure_multiple_001',
                    'status': 'open',
                    'amount_due': 7500,
                    'amount_paid': 0,
                    'amount_remaining': 7500,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'period_start': int((datetime.utcnow() - timedelta(days=30)).timestamp()),
                    'period_end': int(datetime.utcnow().timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_failure_multiple_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_failure_multiple_001/pdf',
                    'collection_method': 'charge_automatically',
                    'auto_advance': True,
                    'attempt_count': 3,
                    'next_payment_attempt': None,
                    'last_payment_error': {
                        'type': 'card_error',
                        'code': 'insufficient_funds',
                        'message': 'Your card has insufficient funds.'
                    },
                    'lines': {
                        'data': [{
                            'id': 'il_failure_multiple_001',
                            'object': 'line_item',
                            'amount': 7500,
                            'currency': 'usd',
                            'description': 'Enterprise Tier - Monthly',
                            'quantity': 1,
                            'price': {
                                'id': 'price_enterprise_monthly',
                                'object': 'price',
                                'unit_amount': 7500,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'payment_failure_multiple_attempts',
                        'payment_method': 'card_4444444444',
                        'failure_reason': 'insufficient_funds',
                        'max_attempts_reached': 'true'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_payment_failure_expired_card_event(self) -> str:
        """Create a payment failure due to expired card event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_failed',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_failure_expired_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_failure_001',
                    'subscription': 'sub_failure_expired_001',
                    'status': 'open',
                    'amount_due': 2500,
                    'amount_paid': 0,
                    'amount_remaining': 2500,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'period_start': int((datetime.utcnow() - timedelta(days=30)).timestamp()),
                    'period_end': int(datetime.utcnow().timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_failure_expired_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_failure_expired_001/pdf',
                    'collection_method': 'charge_automatically',
                    'auto_advance': True,
                    'attempt_count': 1,
                    'next_payment_attempt': int((datetime.utcnow() + timedelta(days=1)).timestamp()),
                    'last_payment_error': {
                        'type': 'card_error',
                        'code': 'expired_card',
                        'message': 'Your card has expired.'
                    },
                    'lines': {
                        'data': [{
                            'id': 'il_failure_expired_001',
                            'object': 'line_item',
                            'amount': 2500,
                            'currency': 'usd',
                            'description': 'Pro Tier - Monthly',
                            'quantity': 1,
                            'price': {
                                'id': 'price_pro_monthly',
                                'object': 'price',
                                'unit_amount': 2500,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'payment_failure_expired_card',
                        'payment_method': 'card_5555555555',
                        'failure_reason': 'expired_card'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_subscription_reactivation_payment_event(self) -> str:
        """Create a subscription reactivation payment event"""
        event = {
            'id': f'evt_payment_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'invoice.payment_succeeded',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'in_reactivation_001',
                    'object': 'invoice',
                    'customer': 'cus_payment_success_001',
                    'subscription': 'sub_reactivation_001',
                    'status': 'paid',
                    'amount_due': 2500,
                    'amount_paid': 2500,
                    'amount_remaining': 0,
                    'currency': 'usd',
                    'created': int(datetime.utcnow().timestamp()),
                    'due_date': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'period_start': int((datetime.utcnow() - timedelta(days=30)).timestamp()),
                    'period_end': int(datetime.utcnow().timestamp()),
                    'hosted_invoice_url': 'https://invoice.stripe.com/i/test_reactivation_001',
                    'invoice_pdf': 'https://pay.stripe.com/invoice/test_reactivation_001/pdf',
                    'receipt_url': 'https://pay.stripe.com/receipts/test_reactivation_001',
                    'collection_method': 'charge_automatically',
                    'auto_advance': True,
                    'attempt_count': 1,
                    'payment_intent': 'pi_reactivation_001',
                    'charge': 'ch_reactivation_001',
                    'payment_method': 'pm_reactivation_001',
                    'payment_method_types': ['card'],
                    'lines': {
                        'data': [{
                            'id': 'il_reactivation_001',
                            'object': 'line_item',
                            'amount': 2500,
                            'currency': 'usd',
                            'description': 'Pro Tier - Monthly',
                            'quantity': 1,
                            'price': {
                                'id': 'price_pro_monthly',
                                'object': 'price',
                                'unit_amount': 2500,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'subscription_reactivation_payment',
                        'payment_method': 'card_6666666666',
                        'reactivation': 'true',
                        'previous_status': 'past_due'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _generate_test_signature(self, payload: str) -> str:
        """Generate a test webhook signature"""
        import hmac
        import hashlib
        
        webhook_secret = "whsec_test_secret"
        timestamp = int(datetime.utcnow().timestamp())
        
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"t={timestamp},v1={signature}"
    
    def run_all_demonstrations(self):
        """Run all payment processing demonstrations"""
        print("🚀 Enhanced Payment Processing Handlers Demonstration")
        print("=" * 80)
        
        try:
            self.demonstrate_successful_subscription_payment()
            self.demonstrate_successful_one_time_payment()
            self.demonstrate_successful_payment_with_discount()
            self.demonstrate_first_payment_success()
            self.demonstrate_payment_failure_first_attempt()
            self.demonstrate_payment_failure_multiple_attempts()
            self.demonstrate_payment_failure_expired_card()
            self.demonstrate_subscription_reactivation_payment()
            
            print("\n" + "=" * 80)
            print("✅ All payment processing demonstrations completed successfully!")
            print("\n🎯 Key Features Demonstrated:")
            print("   • Comprehensive payment success processing")
            print("   • Subscription and one-time payment handling")
            print("   • Discount and coupon processing")
            print("   • First payment special handling")
            print("   • Payment failure with retry logic")
            print("   • Multiple failure attempt handling")
            print("   • Expired card and payment method issues")
            print("   • Subscription reactivation processing")
            print("   • Tax calculation and handling")
            print("   • Multi-channel notification sending")
            print("   • Comprehensive analytics tracking")
            print("   • Detailed audit trail logging")
            print("   • Dunning management and escalation")
            print("   • Payment method failure tracking")
            print("   • Customer lifetime value tracking")
            
        except Exception as e:
            print(f"\n❌ Error during demonstration: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    example = PaymentProcessingHandlersExample()
    example.run_all_demonstrations() 