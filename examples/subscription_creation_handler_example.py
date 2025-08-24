"""
Enhanced Subscription Creation Handler Example
Demonstrates the comprehensive customer.subscription.created webhook handler
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

class SubscriptionCreationHandlerExample:
    """Example demonstrating the enhanced subscription creation handler"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///subscription_creation_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.webhook_manager = StripeWebhookManager(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for subscription creation demonstration"""
        print("📊 Creating sample data for subscription creation demonstration...")
        
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
        
        # Create customers
        self.customers = []
        customer_data = [
            {
                'name': 'Subscription Test User 1',
                'email': 'subscription.user1@example.com',
                'stripe_customer_id': 'cus_subscription_001'
            },
            {
                'name': 'Subscription Test User 2',
                'email': 'subscription.user2@example.com',
                'stripe_customer_id': 'cus_subscription_002'
            },
            {
                'name': 'Subscription Test User 3',
                'email': 'subscription.user3@example.com',
                'stripe_customer_id': 'cus_subscription_003'
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
                    'line1': f'{1000 + len(self.customers)} Subscription St',
                    'postal_code': '94105'
                }
            )
            self.db_session.add(customer)
            self.customers.append(customer)
        
        self.db_session.commit()
        print(f"✅ Created {len(self.customers)} customers for subscription testing")
    
    def demonstrate_basic_subscription_creation(self):
        """Demonstrate basic subscription creation"""
        print("\n=== Basic Subscription Creation ===")
        
        # Create a basic subscription webhook event
        subscription_event = self._create_basic_subscription_event()
        
        print(f"\n🔄 Processing Basic Subscription Creation:")
        print(f"   📋 Event Type: customer.subscription.created")
        print(f"   👤 Customer: {self.customers[0].email}")
        print(f"   💰 Amount: $15.00/month")
        print(f"   📅 Billing Cycle: Monthly")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=subscription_event.encode('utf-8'),
            signature=self._generate_test_signature(subscription_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Subscription-Test/1.0",
            request_id="test_subscription_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Subscription created successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_yearly_subscription_creation(self):
        """Demonstrate yearly subscription creation"""
        print("\n=== Yearly Subscription Creation ===")
        
        # Create a yearly subscription webhook event
        subscription_event = self._create_yearly_subscription_event()
        
        print(f"\n🔄 Processing Yearly Subscription Creation:")
        print(f"   📋 Event Type: customer.subscription.created")
        print(f"   👤 Customer: {self.customers[1].email}")
        print(f"   💰 Amount: $350.00/year")
        print(f"   📅 Billing Cycle: Yearly")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=subscription_event.encode('utf-8'),
            signature=self._generate_test_signature(subscription_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Subscription-Test/1.0",
            request_id="test_subscription_002"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Yearly subscription created successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_trial_subscription_creation(self):
        """Demonstrate trial subscription creation"""
        print("\n=== Trial Subscription Creation ===")
        
        # Create a trial subscription webhook event
        subscription_event = self._create_trial_subscription_event()
        
        print(f"\n🔄 Processing Trial Subscription Creation:")
        print(f"   📋 Event Type: customer.subscription.created")
        print(f"   👤 Customer: {self.customers[2].email}")
        print(f"   💰 Amount: $75.00/month")
        print(f"   📅 Billing Cycle: Monthly")
        print(f"   🆓 Trial Period: 14 days")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=subscription_event.encode('utf-8'),
            signature=self._generate_test_signature(subscription_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Subscription-Test/1.0",
            request_id="test_subscription_003"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Trial subscription created successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_custom_pricing_tier_creation(self):
        """Demonstrate custom pricing tier creation"""
        print("\n=== Custom Pricing Tier Creation ===")
        
        # Create a subscription with custom pricing
        subscription_event = self._create_custom_pricing_subscription_event()
        
        print(f"\n🔄 Processing Custom Pricing Subscription Creation:")
        print(f"   📋 Event Type: customer.subscription.created")
        print(f"   👤 Customer: {self.customers[0].email}")
        print(f"   💰 Amount: $25.00/month")
        print(f"   📅 Billing Cycle: Monthly")
        print(f"   🏷️ Custom Pricing Tier: Auto-generated")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=subscription_event.encode('utf-8'),
            signature=self._generate_test_signature(subscription_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Subscription-Test/1.0",
            request_id="test_subscription_004"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Custom pricing subscription created successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_duplicate_subscription_handling(self):
        """Demonstrate duplicate subscription handling"""
        print("\n=== Duplicate Subscription Handling ===")
        
        # Create the same subscription event again
        subscription_event = self._create_basic_subscription_event()
        
        print(f"\n🔄 Processing Duplicate Subscription:")
        print(f"   📋 Event Type: customer.subscription.created")
        print(f"   👤 Customer: {self.customers[0].email}")
        print(f"   ⚠️ This subscription already exists")
        
        # Process the webhook
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=subscription_event.encode('utf-8'),
            signature=self._generate_test_signature(subscription_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Subscription-Test/1.0",
            request_id="test_subscription_005"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.success:
            print(f"   ✅ Duplicate subscription handled gracefully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_error_handling(self):
        """Demonstrate error handling scenarios"""
        print("\n=== Error Handling Scenarios ===")
        
        # Test 1: Invalid customer
        print(f"\n1. Testing Invalid Customer:")
        invalid_customer_event = self._create_invalid_customer_subscription_event()
        
        result = self.webhook_manager.process_webhook(
            payload=invalid_customer_event.encode('utf-8'),
            signature=self._generate_test_signature(invalid_customer_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Subscription-Test/1.0",
            request_id="test_subscription_error_001"
        )
        
        if not result.success:
            print(f"   ❌ Expected error: {result.error}")
        else:
            print(f"   ⚠️ Unexpected success")
        
        # Test 2: Invalid subscription data
        print(f"\n2. Testing Invalid Subscription Data:")
        invalid_data_event = self._create_invalid_subscription_data_event()
        
        result = self.webhook_manager.process_webhook(
            payload=invalid_data_event.encode('utf-8'),
            signature=self._generate_test_signature(invalid_data_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Subscription-Test/1.0",
            request_id="test_subscription_error_002"
        )
        
        if not result.success:
            print(f"   ❌ Expected error: {result.error}")
        else:
            print(f"   ⚠️ Unexpected success")
    
    def _create_basic_subscription_event(self) -> str:
        """Create a basic monthly subscription event"""
        event = {
            'id': f'evt_subscription_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'customer.subscription.created',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'sub_basic_monthly_001',
                    'object': 'subscription',
                    'customer': 'cus_subscription_001',
                    'status': 'active',
                    'current_period_start': int(datetime.utcnow().timestamp()),
                    'current_period_end': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'cancel_at_period_end': False,
                    'collection_method': 'charge_automatically',
                    'items': {
                        'data': [{
                            'id': 'si_basic_001',
                            'object': 'subscription_item',
                            'quantity': 1,
                            'price': {
                                'id': 'price_budget_monthly',
                                'object': 'price',
                                'unit_amount': 1500,
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
                        'test_type': 'basic_subscription'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_yearly_subscription_event(self) -> str:
        """Create a yearly subscription event"""
        event = {
            'id': f'evt_subscription_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'customer.subscription.created',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'sub_yearly_001',
                    'object': 'subscription',
                    'customer': 'cus_subscription_002',
                    'status': 'active',
                    'current_period_start': int(datetime.utcnow().timestamp()),
                    'current_period_end': int((datetime.utcnow() + timedelta(days=365)).timestamp()),
                    'cancel_at_period_end': False,
                    'collection_method': 'charge_automatically',
                    'items': {
                        'data': [{
                            'id': 'si_yearly_001',
                            'object': 'subscription_item',
                            'quantity': 1,
                            'price': {
                                'id': 'price_mid_yearly',
                                'object': 'price',
                                'unit_amount': 35000,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'year',
                                    'interval_count': 1
                                }
                            }
                        }]
                    },
                    'metadata': {
                        'source': 'webhook_test',
                        'test_type': 'yearly_subscription'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_trial_subscription_event(self) -> str:
        """Create a trial subscription event"""
        now = datetime.utcnow()
        trial_end = now + timedelta(days=14)
        
        event = {
            'id': f'evt_subscription_{int(now.timestamp())}',
            'object': 'event',
            'type': 'customer.subscription.created',
            'created': int(now.timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'sub_trial_001',
                    'object': 'subscription',
                    'customer': 'cus_subscription_003',
                    'status': 'trialing',
                    'current_period_start': int(now.timestamp()),
                    'current_period_end': int((now + timedelta(days=30)).timestamp()),
                    'trial_start': int(now.timestamp()),
                    'trial_end': int(trial_end.timestamp()),
                    'cancel_at_period_end': False,
                    'collection_method': 'charge_automatically',
                    'items': {
                        'data': [{
                            'id': 'si_trial_001',
                            'object': 'subscription_item',
                            'quantity': 1,
                            'price': {
                                'id': 'price_pro_monthly',
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
                        'test_type': 'trial_subscription'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_custom_pricing_subscription_event(self) -> str:
        """Create a subscription with custom pricing"""
        event = {
            'id': f'evt_subscription_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'customer.subscription.created',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'sub_custom_001',
                    'object': 'subscription',
                    'customer': 'cus_subscription_001',
                    'status': 'active',
                    'current_period_start': int(datetime.utcnow().timestamp()),
                    'current_period_end': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'cancel_at_period_end': False,
                    'collection_method': 'charge_automatically',
                    'items': {
                        'data': [{
                            'id': 'si_custom_001',
                            'object': 'subscription_item',
                            'quantity': 1,
                            'price': {
                                'id': 'price_custom_monthly',
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
                        'test_type': 'custom_pricing'
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_invalid_customer_subscription_event(self) -> str:
        """Create a subscription event with invalid customer"""
        event = {
            'id': f'evt_subscription_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'customer.subscription.created',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'sub_invalid_customer_001',
                    'object': 'subscription',
                    'customer': 'cus_invalid_customer',
                    'status': 'active',
                    'current_period_start': int(datetime.utcnow().timestamp()),
                    'current_period_end': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    'items': {
                        'data': [{
                            'id': 'si_invalid_001',
                            'object': 'subscription_item',
                            'quantity': 1,
                            'price': {
                                'id': 'price_budget_monthly',
                                'object': 'price',
                                'unit_amount': 1500,
                                'currency': 'usd',
                                'recurring': {
                                    'interval': 'month',
                                    'interval_count': 1
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        return json.dumps(event)
    
    def _create_invalid_subscription_data_event(self) -> str:
        """Create a subscription event with invalid data"""
        event = {
            'id': f'evt_subscription_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': 'customer.subscription.created',
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {
                    'id': 'sub_invalid_data_001',
                    'object': 'subscription',
                    'customer': 'cus_subscription_001',
                    # Missing required fields
                    'items': {
                        'data': []  # Empty items array
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
        """Run all subscription creation demonstrations"""
        print("🚀 Enhanced Subscription Creation Handler Demonstration")
        print("=" * 80)
        
        try:
            self.demonstrate_basic_subscription_creation()
            self.demonstrate_yearly_subscription_creation()
            self.demonstrate_trial_subscription_creation()
            self.demonstrate_custom_pricing_tier_creation()
            self.demonstrate_duplicate_subscription_handling()
            self.demonstrate_error_handling()
            
            print("\n" + "=" * 80)
            print("✅ All subscription creation demonstrations completed successfully!")
            print("\n🎯 Key Features Demonstrated:")
            print("   • Comprehensive subscription data extraction and validation")
            print("   • Automatic pricing tier creation for custom prices")
            print("   • Trial period handling and setup")
            print("   • Billing and payment method configuration")
            print("   • Initial billing history creation")
            print("   • Customer subscription status updates")
            print("   • Multi-channel notification sending")
            print("   • Comprehensive analytics tracking")
            print("   • Detailed audit trail logging")
            print("   • Robust error handling and validation")
            print("   • Duplicate subscription prevention")
            
        except Exception as e:
            print(f"\n❌ Error during demonstration: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    example = SubscriptionCreationHandlerExample()
    example.run_all_demonstrations() 