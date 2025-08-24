"""
Comprehensive Webhook Management System Example for MINGUS
Demonstrates complete webhook handling, monitoring, validation, and testing
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webhooks.stripe_webhooks import StripeWebhookManager, WebhookEvent
from webhooks.webhook_config import WebhookConfig, WebhookEnvironment
from webhooks.webhook_monitor import WebhookMonitor
from webhooks.webhook_validator import WebhookValidator
from config.billing_config import BillingConfig
from models.subscription import Customer, Subscription, PricingTier, BillingHistory

class ComprehensiveWebhookManagementExample:
    """Example demonstrating comprehensive webhook management system"""
    
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine('sqlite:///mingus_webhook_management_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.config = BillingConfig()
        self.webhook_config = WebhookConfig(WebhookEnvironment.DEVELOPMENT)
        self.webhook_manager = StripeWebhookManager(self.db_session, self.config)
        self.webhook_monitor = WebhookMonitor(self.db_session, self.config)
        self.webhook_validator = WebhookValidator(self.db_session, self.config)
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for webhook management demonstration"""
        print("📊 Creating sample data for webhook management demonstration...")
        
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
                'name': 'Webhook Test User 1',
                'email': 'webhook.user1@example.com',
                'stripe_customer_id': 'cus_webhook_0001'
            },
            {
                'name': 'Webhook Test User 2',
                'email': 'webhook.user2@example.com',
                'stripe_customer_id': 'cus_webhook_0002'
            },
            {
                'name': 'Webhook Test User 3',
                'email': 'webhook.user3@example.com',
                'stripe_customer_id': 'cus_webhook_0003'
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
                    'line1': f'{1000 + len(self.customers)} Webhook St',
                    'postal_code': '94105'
                }
            )
            self.db_session.add(customer)
            self.customers.append(customer)
        
        self.db_session.commit()
        print(f"✅ Created {len(self.customers)} customers for webhook testing")
    
    def demonstrate_webhook_processing(self):
        """Demonstrate webhook event processing"""
        print("\n=== Webhook Event Processing ===")
        
        print(f"\n🔄 Testing Webhook Event Processing:")
        
        # Test 1: Customer Created Webhook
        print(f"\n1. Process Customer Created Webhook:")
        customer_created_event = self._create_test_webhook_event(
            event_type="customer.created",
            customer_data={
                'id': 'cus_webhook_new_001',
                'email': 'new.webhook.user@example.com',
                'name': 'New Webhook User',
                'phone': '+1234567890',
                'address': {
                    'country': 'US',
                    'state': 'NY',
                    'city': 'New York',
                    'line1': '123 Webhook Ave',
                    'postal_code': '10001'
                }
            }
        )
        
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=customer_created_event.encode('utf-8'),
            signature=self._generate_test_signature(customer_created_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Webhook-Test/1.0",
            request_id="test_request_001"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Track the event for monitoring
        self.webhook_monitor.track_webhook_event(
            event_type="customer.created",
            processing_time=processing_time,
            success=result.success,
            error=result.error
        )
        
        if result.success:
            print(f"   ✅ Customer created webhook processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
        
        # Test 2: Subscription Created Webhook
        print(f"\n2. Process Subscription Created Webhook:")
        subscription_created_event = self._create_test_webhook_event(
            event_type="customer.subscription.created",
            subscription_data={
                'id': 'sub_webhook_001',
                'customer': 'cus_webhook_0001',
                'status': 'active',
                'current_period_start': int(datetime.utcnow().timestamp()),
                'current_period_end': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                'items': {
                    'data': [{
                        'price': {
                            'id': 'price_budget_monthly',
                            'unit_amount': 1500
                        }
                    }]
                }
            }
        )
        
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=subscription_created_event.encode('utf-8'),
            signature=self._generate_test_signature(subscription_created_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Webhook-Test/1.0",
            request_id="test_request_002"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Track the event for monitoring
        self.webhook_monitor.track_webhook_event(
            event_type="customer.subscription.created",
            processing_time=processing_time,
            success=result.success,
            error=result.error
        )
        
        if result.success:
            print(f"   ✅ Subscription created webhook processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
        
        # Test 3: Payment Succeeded Webhook
        print(f"\n3. Process Payment Succeeded Webhook:")
        payment_succeeded_event = self._create_test_webhook_event(
            event_type="invoice.payment_succeeded",
            invoice_data={
                'id': 'in_webhook_001',
                'customer': 'cus_webhook_0001',
                'subscription': 'sub_webhook_001',
                'amount_paid': 1500,
                'currency': 'usd',
                'status': 'paid',
                'hosted_invoice_url': 'https://invoice.stripe.com/i/test',
                'invoice_pdf': 'https://pay.stripe.com/invoice/test/pdf'
            }
        )
        
        start_time = datetime.utcnow()
        result = self.webhook_manager.process_webhook(
            payload=payment_succeeded_event.encode('utf-8'),
            signature=self._generate_test_signature(payment_succeeded_event),
            source_ip="127.0.0.1",
            user_agent="MINGUS-Webhook-Test/1.0",
            request_id="test_request_003"
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Track the event for monitoring
        self.webhook_monitor.track_webhook_event(
            event_type="invoice.payment_succeeded",
            processing_time=processing_time,
            success=result.success,
            error=result.error
        )
        
        if result.success:
            print(f"   ✅ Payment succeeded webhook processed successfully")
            print(f"   📝 Message: {result.message}")
            print(f"   ⏱️ Processing Time: {processing_time:.3f}s")
            print(f"   📊 Changes: {len(result.changes)} changes")
            for change in result.changes:
                print(f"      - {change}")
            print(f"   📧 Notifications Sent: {result.notifications_sent}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def demonstrate_webhook_monitoring(self):
        """Demonstrate webhook monitoring and analytics"""
        print("\n=== Webhook Monitoring and Analytics ===")
        
        print(f"\n📊 Testing Webhook Monitoring:")
        
        # Test 1: Get Webhook Metrics
        print(f"\n1. Get Webhook Metrics:")
        metrics = self.webhook_monitor.get_webhook_metrics(time_range="1h")
        
        print(f"   📈 Total Events: {metrics.total_events}")
        print(f"   ✅ Successful Events: {metrics.successful_events}")
        print(f"   ❌ Failed Events: {metrics.failed_events}")
        print(f"   📊 Success Rate: {metrics.success_rate:.2%}")
        print(f"   ⏱️ Average Processing Time: {metrics.average_processing_time:.3f}s")
        print(f"   🚀 Events per Minute: {metrics.events_per_minute:.2f}")
        print(f"   🕐 Last Event Time: {metrics.last_event_time}")
        
        if metrics.error_distribution:
            print(f"   🚨 Error Distribution:")
            for error, count in metrics.error_distribution.items():
                print(f"      - {error}: {count}")
        
        # Test 2: Get Webhook Health
        print(f"\n2. Get Webhook Health:")
        health = self.webhook_monitor.get_webhook_health()
        
        print(f"   🏥 Health Status: {health.status}")
        print(f"   ✅ Is Healthy: {health.is_healthy}")
        
        if health.issues:
            print(f"   🚨 Issues:")
            for issue in health.issues:
                print(f"      - {issue}")
        
        if health.recommendations:
            print(f"   💡 Recommendations:")
            for recommendation in health.recommendations:
                print(f"      - {recommendation}")
        
        # Test 3: Get Event Type Analytics
        print(f"\n3. Get Event Type Analytics:")
        analytics = self.webhook_monitor.get_event_type_analytics(time_range="1h")
        
        if analytics.get('event_type_counts'):
            print(f"   📊 Event Type Counts:")
            for event_type, count in analytics['event_type_counts'].items():
                print(f"      - {event_type}: {count}")
        
        if analytics.get('processing_times_by_type'):
            print(f"   ⏱️ Processing Times by Type:")
            for event_type, data in analytics['processing_times_by_type'].items():
                print(f"      - {event_type}: {data['avg_processing_time']:.3f}s (Success: {data['success_rate']:.2%})")
        
        # Test 4: Get Performance Trends
        print(f"\n4. Get Performance Trends:")
        trends = self.webhook_monitor.get_performance_trends(hours=1)
        
        if trends.get('success_rate_trend'):
            print(f"   📈 Success Rate Trend:")
            for point in trends['success_rate_trend'][-5:]:  # Last 5 points
                print(f"      - {point['timestamp']}: {point['value']:.2%}")
        
        if trends.get('processing_time_trend'):
            print(f"   ⏱️ Processing Time Trend:")
            for point in trends['processing_time_trend'][-5:]:  # Last 5 points
                print(f"      - {point['timestamp']}: {point['value']:.3f}s")
    
    def demonstrate_webhook_validation(self):
        """Demonstrate webhook validation and testing"""
        print("\n=== Webhook Validation and Testing ===")
        
        print(f"\n🔍 Testing Webhook Validation:")
        
        # Test 1: Validate Webhook Configuration
        print(f"\n1. Validate Webhook Configuration:")
        validation_result = self.webhook_validator.validate_webhook_configuration()
        
        print(f"   ✅ Configuration Valid: {validation_result.is_valid}")
        
        if validation_result.issues:
            print(f"   🚨 Issues:")
            for issue in validation_result.issues:
                print(f"      - {issue}")
        
        if validation_result.warnings:
            print(f"   ⚠️ Warnings:")
            for warning in validation_result.warnings:
                print(f"      - {warning}")
        
        if validation_result.recommendations:
            print(f"   💡 Recommendations:")
            for recommendation in validation_result.recommendations:
                print(f"      - {recommendation}")
        
        # Test 2: Test Endpoint Connectivity
        print(f"\n2. Test Endpoint Connectivity:")
        for endpoint_name, endpoint in self.webhook_config.endpoints.items():
            if endpoint.enabled:
                test_result = self.webhook_validator.test_endpoint(endpoint.url)
                print(f"   🔗 {endpoint_name}:")
                print(f"      - Success: {test_result.success}")
                print(f"      - Response Time: {test_result.response_time:.3f}s")
                print(f"      - Status Code: {test_result.status_code}")
                if test_result.error:
                    print(f"      - Error: {test_result.error}")
        
        # Test 3: Test Signature Verification
        print(f"\n3. Test Signature Verification:")
        signature_test = self.webhook_validator.test_webhook_signature_verification()
        
        if signature_test.get('success', False):
            print(f"   ✅ Signature verification test successful")
            print(f"   🔐 Signature Valid: {signature_test.get('signature_valid', False)}")
        else:
            print(f"   ❌ Signature verification test failed: {signature_test.get('error', 'Unknown error')}")
        
        # Test 4: Run Comprehensive Tests
        print(f"\n4. Run Comprehensive Webhook Tests:")
        comprehensive_tests = self.webhook_validator.run_comprehensive_webhook_tests()
        
        print(f"   🎯 Overall Success: {comprehensive_tests.get('overall_success', False)}")
        print(f"   📊 Test Summary:")
        summary = comprehensive_tests.get('summary', {})
        print(f"      - Total Tests: {summary.get('total_tests', 0)}")
        print(f"      - Passed Tests: {summary.get('passed_tests', 0)}")
        print(f"      - Failed Tests: {summary.get('failed_tests', 0)}")
        
        # Test 5: Generate Test Report
        print(f"\n5. Generate Webhook Test Report:")
        test_report = self.webhook_validator.generate_webhook_test_report()
        
        print(f"   📋 Report Generated: {test_report.get('generated_at')}")
        print(f"   🎯 Overall Status: {test_report.get('overall_status', 'UNKNOWN')}")
        
        if test_report.get('recommendations'):
            print(f"   💡 Recommendations:")
            for recommendation in test_report['recommendations']:
                print(f"      - {recommendation}")
    
    def demonstrate_webhook_reporting(self):
        """Demonstrate webhook reporting and insights"""
        print("\n=== Webhook Reporting and Insights ===")
        
        print(f"\n📊 Testing Webhook Reporting:")
        
        # Test 1: Generate Webhook Report
        print(f"\n1. Generate Comprehensive Webhook Report:")
        webhook_report = self.webhook_monitor.generate_webhook_report(time_range="1h")
        
        print(f"   📋 Report Generated: {webhook_report.get('report_generated_at')}")
        print(f"   ⏰ Time Range: {webhook_report.get('time_range')}")
        
        summary = webhook_report.get('summary', {})
        print(f"   📊 Summary:")
        print(f"      - Total Events: {summary.get('total_events', 0)}")
        print(f"      - Success Rate: {summary.get('success_rate', 0):.2%}")
        print(f"      - Avg Processing Time: {summary.get('avg_processing_time', 0):.3f}s")
        print(f"      - Events per Minute: {summary.get('events_per_minute', 0):.2f}")
        print(f"      - Is Healthy: {summary.get('is_healthy', False)}")
        print(f"      - Status: {summary.get('status', 'Unknown')}")
        
        health = webhook_report.get('health', {})
        print(f"   🏥 Health:")
        print(f"      - Is Healthy: {health.get('is_healthy', False)}")
        print(f"      - Status: {health.get('status', 'Unknown')}")
        
        if health.get('issues'):
            print(f"      - Issues: {len(health['issues'])}")
            for issue in health['issues']:
                print(f"        * {issue}")
        
        if health.get('recommendations'):
            print(f"      - Recommendations: {len(health['recommendations'])}")
            for recommendation in health['recommendations']:
                print(f"        * {recommendation}")
        
        # Test 2: Get Error Analytics
        print(f"\n2. Get Error Analytics:")
        error_analytics = self.webhook_monitor.get_error_analytics(time_range="1h")
        
        print(f"   🚨 Total Errors: {error_analytics.get('total_errors', 0)}")
        print(f"   📊 Error Rate: {error_analytics.get('error_rate', 0):.2%}")
        
        if error_analytics.get('most_common_errors'):
            print(f"   🔥 Most Common Errors:")
            for error, count in error_analytics['most_common_errors'][:5]:
                print(f"      - {error}: {count}")
        
        # Test 3: Get Performance Trends
        print(f"\n3. Get Performance Trends:")
        trends = self.webhook_monitor.get_performance_trends(hours=1)
        
        if trends.get('success_rate_trend'):
            print(f"   📈 Success Rate Trend (Last 5 points):")
            for point in trends['success_rate_trend'][-5:]:
                print(f"      - {point['timestamp']}: {point['value']:.2%}")
        
        if trends.get('processing_time_trend'):
            print(f"   ⏱️ Processing Time Trend (Last 5 points):")
            for point in trends['processing_time_trend'][-5:]:
                print(f"      - {point['timestamp']}: {point['value']:.3f}s")
    
    def _create_test_webhook_event(self, event_type: str, **data) -> str:
        """Create a test webhook event JSON string"""
        import json
        
        event = {
            'id': f'evt_test_{int(datetime.utcnow().timestamp())}',
            'object': 'event',
            'type': event_type,
            'created': int(datetime.utcnow().timestamp()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': data.get('customer_data', data.get('subscription_data', data.get('invoice_data', {})))
            }
        }
        
        return json.dumps(event)
    
    def _generate_test_signature(self, payload: str) -> str:
        """Generate a test webhook signature"""
        import hmac
        import hashlib
        
        webhook_secret = self.webhook_config.get_webhook_secret() or "whsec_test_secret"
        timestamp = int(datetime.utcnow().timestamp())
        
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"t={timestamp},v1={signature}"
    
    def run_all_demonstrations(self):
        """Run all webhook management demonstrations"""
        print("🚀 MINGUS Comprehensive Webhook Management System Demonstration")
        print("=" * 80)
        
        try:
            self.demonstrate_webhook_processing()
            self.demonstrate_webhook_monitoring()
            self.demonstrate_webhook_validation()
            self.demonstrate_webhook_reporting()
            
            print("\n" + "=" * 80)
            print("✅ All webhook management demonstrations completed successfully!")
            print("\n🎯 Key Features Demonstrated:")
            print("   • Real-time webhook event processing")
            print("   • Comprehensive webhook monitoring and analytics")
            print("   • Webhook configuration validation and testing")
            print("   • Performance tracking and health monitoring")
            print("   • Error analysis and reporting")
            print("   • Signature verification and security")
            print("   • Endpoint connectivity testing")
            print("   • Comprehensive reporting and insights")
            
        except Exception as e:
            print(f"\n❌ Error during demonstration: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    example = ComprehensiveWebhookManagementExample()
    example.run_all_demonstrations() 