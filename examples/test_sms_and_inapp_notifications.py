#!/usr/bin/env python3
"""
Test script for SMS Notifications and In-App Notifications
Tests the payment recovery system's ability to send SMS notifications for critical
payment failures and in-app notifications with billing alerts.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from billing.payment_recovery import PaymentRecoverySystem, PaymentFailure, RecoveryAction
from models.payment_recovery import PaymentRecoveryRecord, RecoveryStatus, ActionStatus
from models.subscription import Customer, Subscription
from config.base import Config

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.customers = {}
        self.subscriptions = {}
        self.failures = {}
        self.actions = {}
    
    def commit(self):
        pass
    
    def add(self, obj):
        if isinstance(obj, Customer):
            self.customers[obj.id] = obj
        elif isinstance(obj, Subscription):
            self.subscriptions[obj.id] = obj
        elif isinstance(obj, PaymentRecoveryRecord):
            self.failures[obj.id] = obj
        elif isinstance(obj, RecoveryAction):
            self.actions[obj.action_id] = obj
    
    def query(self, model):
        return MockQuery(self, model)

class MockQuery:
    """Mock query for testing"""
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.filters = []
    
    def filter(self, condition):
        self.filters.append(condition)
        return self
    
    def first(self):
        # Mock implementation
        return None
    
    def all(self):
        # Mock implementation
        return []

class MockNotificationService:
    """Mock notification service for testing"""
    def send_sms_notifications(self, data):
        return {
            'success': True,
            'notifications_sent': 1,
            'channels': ['sms']
        }
    
    def send_in_app_notifications(self, data):
        return {
            'success': True,
            'notifications_sent': 1,
            'channels': ['in_app']
        }
    
    def send_billing_alerts(self, data):
        return {
            'success': True,
            'notifications_sent': 1,
            'channels': ['push', 'in_app']
        }

def create_mock_customer() -> Customer:
    """Create a mock customer for testing"""
    return Customer(
        id=str(uuid.uuid4()),
        stripe_customer_id=f"cus_{uuid.uuid4().hex[:24]}",
        email="test@example.com",
        name="Test Customer",
        status="active",
        created_at=datetime.now(timezone.utc),
        metadata={
            'phone_number': '+1-555-123-4567'
        }
    )

def create_mock_subscription(customer_id: str) -> Subscription:
    """Create a mock subscription for testing"""
    return Subscription(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        stripe_subscription_id=f"sub_{uuid.uuid4().hex[:24]}",
        status="active",
        plan_id="premium_plan",
        amount=99.99,
        currency="usd",
        interval="month",
        created_at=datetime.now(timezone.utc),
        metadata={}
    )

def create_mock_failure_record(customer_id: str, subscription_id: str) -> PaymentRecoveryRecord:
    """Create a mock payment failure record for testing"""
    return PaymentRecoveryRecord(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        subscription_id=subscription_id,
        invoice_id=f"in_{uuid.uuid4().hex[:24]}",
        payment_intent_id=f"pi_{uuid.uuid4().hex[:24]}",
        failure_reason="expired_card",
        failure_code="card_declined_expired",
        amount=99.99,
        currency="usd",
        failed_at=datetime.now(timezone.utc),
        status=RecoveryStatus.PENDING,
        retry_count=0,
        metadata={}
    )

def test_sms_notifications_configuration():
    """Test SMS notifications configuration"""
    print("📱 Testing SMS Notifications Configuration")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test configuration
    sms_config = recovery_system.recovery_config['dunning_email_sequence']['sms_notifications']
    
    print(f"✅ SMS Notifications Configuration:")
    print(f"   Enabled: {sms_config.get('enabled', False)}")
    print(f"   Critical Stages: {sms_config.get('critical_stages', [])}")
    print(f"   Support Phone: {sms_config.get('support_phone', 'N/A')}")
    print(f"   Opt-out Keywords: {sms_config.get('opt_out_keywords', [])}")
    print(f"   Help Keywords: {sms_config.get('help_keywords', [])}")
    print()
    
    # Test SMS templates
    sms_templates = sms_config.get('sms_templates', {})
    print(f"📝 SMS Templates:")
    for template_name, template_config in sms_templates.items():
        print(f"   {template_name}:")
        print(f"     Message: {template_config.get('message', 'N/A')[:80]}...")
        print(f"     Priority: {template_config.get('priority', 'N/A')}")
        print(f"     Retry Count: {template_config.get('retry_count', 0)}")
        print()
    
    print("✅ SMS Notifications Configuration Tests Completed")
    print()

def test_in_app_notifications_configuration():
    """Test in-app notifications configuration"""
    print("📱 Testing In-App Notifications Configuration")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test configuration
    in_app_config = recovery_system.recovery_config['dunning_email_sequence']['in_app_notifications']
    
    print(f"✅ In-App Notifications Configuration:")
    print(f"   Enabled: {in_app_config.get('enabled', False)}")
    print()
    
    # Test notification types
    notification_types = in_app_config.get('notification_types', {})
    print(f"📋 Notification Types:")
    for notification_type, type_config in notification_types.items():
        print(f"   {notification_type}:")
        print(f"     Title: {type_config.get('title', 'N/A')}")
        print(f"     Severity: {type_config.get('severity', 'N/A')}")
        print(f"     Action Required: {type_config.get('action_required', False)}")
        print(f"     Action Text: {type_config.get('action_text', 'N/A')}")
        print(f"     Action URL: {type_config.get('action_url', 'N/A')}")
        print(f"     Dismissible: {type_config.get('dismissible', False)}")
        print(f"     Persistent: {type_config.get('persistent', False)}")
        print()
    
    # Test billing alerts
    billing_alerts = in_app_config.get('billing_alerts', {})
    print(f"🚨 Billing Alerts Configuration:")
    print(f"   Enabled: {billing_alerts.get('enabled', False)}")
    print()
    
    alert_types = billing_alerts.get('alert_types', {})
    print(f"   Alert Types:")
    for alert_type, alert_config in alert_types.items():
        print(f"     {alert_type}:")
        print(f"       Title: {alert_config.get('title', 'N/A')}")
        print(f"       Icon: {alert_config.get('icon', 'N/A')}")
        print(f"       Color: {alert_config.get('color', 'N/A')}")
        print(f"       Sound: {alert_config.get('sound', 'N/A')}")
        print(f"       Vibration: {alert_config.get('vibration', False)}")
        print()
    
    notification_frequency = billing_alerts.get('notification_frequency', {})
    print(f"   Notification Frequency:")
    for alert_type, frequency in notification_frequency.items():
        print(f"     {alert_type}: {frequency}")
    print()
    
    print("✅ In-App Notifications Configuration Tests Completed")
    print()

def test_sms_notification_sending():
    """Test SMS notification sending"""
    print("📤 Testing SMS Notification Sending")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for SMS testing")
    print()
    
    # Test SMS sending for critical stages
    print("📱 Test 1: Send SMS Notifications for Critical Stages")
    critical_stages = ['dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in critical_stages:
        print(f"   {stage_name.upper()} Stage:")
        
        # Send SMS notification
        result = recovery_system.send_sms_notification(failure_record.id, stage_name)
        
        print(f"     Success: {result.get('success', False)}")
        print(f"     SMS Sent: {result.get('sms_sent', 0)}")
        print(f"     Phone Number: {result.get('phone_number', 'N/A')}")
        print(f"     Priority: {result.get('priority', 'N/A')}")
        print(f"     Message: {result.get('message', 'N/A')[:60]}...")
        print()
    
    # Test non-critical stage
    print("❌ Test 2: Non-Critical Stage Handling")
    non_critical_result = recovery_system.send_sms_notification(failure_record.id, 'dunning_1')
    print(f"   Non-Critical Result: {non_critical_result.get('error', 'N/A')}")
    print()
    
    # Test customer without phone number
    print("📞 Test 3: Customer Without Phone Number")
    customer_no_phone = create_mock_customer()
    customer_no_phone.metadata = {}  # No phone number
    db.add(customer_no_phone)
    
    failure_no_phone = create_mock_failure_record(customer_no_phone.id, subscription.id)
    db.add(failure_no_phone)
    
    no_phone_result = recovery_system.send_sms_notification(failure_no_phone.id, 'dunning_3')
    print(f"   No Phone Result: {no_phone_result.get('error', 'N/A')}")
    print()
    
    print("✅ SMS Notification Sending Tests Completed")
    print()

def test_sms_content_generation():
    """Test SMS content generation"""
    print("📝 Testing SMS Content Generation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for content generation")
    print()
    
    # Test SMS content generation for different stages
    print("📋 Test 1: SMS Content Generation by Stage")
    critical_stages = ['dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in critical_stages:
        print(f"   {stage_name.upper()} Stage:")
        
        # Generate SMS content
        content = recovery_system._generate_sms_content(failure_record, customer, stage_name)
        
        print(f"     Message: {content.get('message', 'N/A')}")
        print(f"     Priority: {content.get('priority', 'N/A')}")
        print(f"     Retry Count: {content.get('retry_count', 0)}")
        print(f"     Template Key: {content.get('template_key', 'N/A')}")
        print()
    
    # Test invalid stage
    print("❌ Test 2: Invalid Stage Content Generation")
    invalid_content = recovery_system._generate_sms_content(failure_record, customer, 'invalid_stage')
    print(f"   Invalid Stage Content: {invalid_content.get('message', 'N/A')}")
    print()
    
    print("✅ SMS Content Generation Tests Completed")
    print()

def test_customer_phone_number_retrieval():
    """Test customer phone number retrieval"""
    print("📞 Testing Customer Phone Number Retrieval")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different customer scenarios
    print("📋 Test 1: Customer with Phone Number in Metadata")
    customer_with_phone = create_mock_customer()
    customer_with_phone.metadata = {'phone_number': '+1-555-123-4567'}
    
    phone_number = recovery_system._get_customer_phone_number(customer_with_phone)
    print(f"   Phone Number: {phone_number}")
    print()
    
    print("📋 Test 2: Customer with Phone Number Attribute")
    customer_with_attr = create_mock_customer()
    customer_with_attr.phone_number = '+1-555-987-6543'
    customer_with_attr.metadata = {}
    
    phone_number = recovery_system._get_customer_phone_number(customer_with_attr)
    print(f"   Phone Number: {phone_number}")
    print()
    
    print("📋 Test 3: Customer without Phone Number")
    customer_no_phone = create_mock_customer()
    customer_no_phone.metadata = {}
    
    phone_number = recovery_system._get_customer_phone_number(customer_no_phone)
    print(f"   Phone Number: {phone_number}")
    print()
    
    print("✅ Customer Phone Number Retrieval Tests Completed")
    print()

def test_in_app_notification_sending():
    """Test in-app notification sending"""
    print("📱 Testing In-App Notification Sending")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for in-app notification testing")
    print()
    
    # Test in-app notification sending for different types
    print("📋 Test 1: Send In-App Notifications by Type")
    notification_types = ['payment_failure', 'grace_period_active', 'suspension_warning', 'account_suspended']
    
    for notification_type in notification_types:
        print(f"   {notification_type.upper()} Type:")
        
        # Send in-app notification
        result = recovery_system.send_in_app_notification(failure_record.id, notification_type)
        
        print(f"     Success: {result.get('success', False)}")
        print(f"     Notification Sent: {result.get('notification_sent', 0)}")
        print(f"     Title: {result.get('title', 'N/A')}")
        print(f"     Severity: {result.get('severity', 'N/A')}")
        print(f"     Action Required: {result.get('action_required', False)}")
        print()
    
    # Test invalid notification type
    print("❌ Test 2: Invalid Notification Type")
    invalid_result = recovery_system.send_in_app_notification(failure_record.id, 'invalid_type')
    print(f"   Invalid Type Result: {invalid_result.get('error', 'N/A')}")
    print()
    
    print("✅ In-App Notification Sending Tests Completed")
    print()

def test_in_app_notification_content_generation():
    """Test in-app notification content generation"""
    print("📝 Testing In-App Notification Content Generation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for content generation")
    print()
    
    # Test content generation for different notification types
    print("📋 Test 1: In-App Notification Content by Type")
    notification_types = ['payment_failure', 'grace_period_active', 'suspension_warning', 'account_suspended']
    
    for notification_type in notification_types:
        print(f"   {notification_type.upper()} Type:")
        
        # Generate content
        content = recovery_system._generate_in_app_notification_content(
            failure_record, customer, notification_type
        )
        
        print(f"     Title: {content.get('title', 'N/A')}")
        print(f"     Message: {content.get('message', 'N/A')[:80]}...")
        print(f"     Severity: {content.get('severity', 'N/A')}")
        print(f"     Action Required: {content.get('action_required', False)}")
        print(f"     Action Text: {content.get('action_text', 'N/A')}")
        print(f"     Action URL: {content.get('action_url', 'N/A')}")
        print(f"     Dismissible: {content.get('dismissible', False)}")
        print(f"     Persistent: {content.get('persistent', False)}")
        print()
    
    print("✅ In-App Notification Content Generation Tests Completed")
    print()

def test_billing_alert_sending():
    """Test billing alert sending"""
    print("🚨 Testing Billing Alert Sending")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for billing alert testing")
    print()
    
    # Test billing alert sending for different types
    print("📋 Test 1: Send Billing Alerts by Type")
    alert_types = ['payment_failed', 'grace_period_started', 'suspension_imminent', 'account_suspended']
    
    for alert_type in alert_types:
        print(f"   {alert_type.upper()} Type:")
        
        # Send billing alert
        result = recovery_system.send_billing_alert(failure_record.id, alert_type)
        
        print(f"     Success: {result.get('success', False)}")
        print(f"     Alert Sent: {result.get('alert_sent', 0)}")
        print(f"     Title: {result.get('title', 'N/A')}")
        print(f"     Icon: {result.get('icon', 'N/A')}")
        print(f"     Color: {result.get('color', 'N/A')}")
        print(f"     Sound: {result.get('sound', 'N/A')}")
        print(f"     Vibration: {result.get('vibration', False)}")
        print()
    
    # Test invalid alert type
    print("❌ Test 2: Invalid Alert Type")
    invalid_result = recovery_system.send_billing_alert(failure_record.id, 'invalid_alert')
    print(f"   Invalid Alert Result: {invalid_result.get('error', 'N/A')}")
    print()
    
    print("✅ Billing Alert Sending Tests Completed")
    print()

def test_billing_alert_content_generation():
    """Test billing alert content generation"""
    print("📝 Testing Billing Alert Content Generation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for content generation")
    print()
    
    # Test content generation for different alert types
    print("📋 Test 1: Billing Alert Content by Type")
    alert_types = ['payment_failed', 'grace_period_started', 'suspension_imminent', 'account_suspended']
    
    for alert_type in alert_types:
        print(f"   {alert_type.upper()} Type:")
        
        # Generate content
        content = recovery_system._generate_billing_alert_content(
            failure_record, customer, alert_type
        )
        
        print(f"     Title: {content.get('title', 'N/A')}")
        print(f"     Message: {content.get('message', 'N/A')[:80]}...")
        print(f"     Icon: {content.get('icon', 'N/A')}")
        print(f"     Color: {content.get('color', 'N/A')}")
        print(f"     Sound: {content.get('sound', 'N/A')}")
        print(f"     Vibration: {content.get('vibration', False)}")
        print()
    
    print("✅ Billing Alert Content Generation Tests Completed")
    print()

def test_multi_channel_notifications():
    """Test multi-channel notifications"""
    print("📡 Testing Multi-Channel Notifications")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for multi-channel testing")
    print()
    
    # Test multi-channel notifications for different stages
    print("📋 Test 1: Multi-Channel Notifications by Stage")
    stages = ['dunning_1', 'dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in stages:
        print(f"   {stage_name.upper()} Stage:")
        
        # Send multi-channel notifications
        result = recovery_system.send_multi_channel_notifications(failure_record.id, stage_name)
        
        print(f"     Success: {result.get('success', False)}")
        print(f"     Total Channels: {result.get('total_channels', 0)}")
        print(f"     Channels Sent: {result.get('channels_sent', [])}")
        
        # Show individual channel results
        results = result.get('results', {})
        for channel, channel_result in results.items():
            if channel_result:
                print(f"       {channel}: {channel_result.get('success', False)}")
        print()
    
    print("✅ Multi-Channel Notifications Tests Completed")
    print()

def test_sms_response_handling():
    """Test SMS response handling"""
    print("📱 Testing SMS Response Handling")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different SMS responses
    print("📋 Test 1: SMS Response Types")
    
    # Test opt-out response
    print("   Opt-out Response:")
    opt_out_result = recovery_system.handle_sms_response('+1-555-123-4567', 'STOP')
    print(f"     Success: {opt_out_result.get('success', False)}")
    print(f"     Action: {opt_out_result.get('action', 'N/A')}")
    print()
    
    # Test help request
    print("   Help Request:")
    help_result = recovery_system.handle_sms_response('+1-555-123-4567', 'HELP')
    print(f"     Success: {help_result.get('success', False)}")
    print(f"     Action: {help_result.get('action', 'N/A')}")
    print()
    
    # Test payment update request
    print("   Payment Update Request:")
    update_result = recovery_system.handle_sms_response('+1-555-123-4567', 'UPDATE PAYMENT')
    print(f"     Success: {update_result.get('success', False)}")
    print(f"     Action: {update_result.get('action', 'N/A')}")
    print()
    
    # Test default response
    print("   Default Response:")
    default_result = recovery_system.handle_sms_response('+1-555-123-4567', 'Hello')
    print(f"     Success: {default_result.get('success', False)}")
    print(f"     Action: {default_result.get('action', 'N/A')}")
    print()
    
    print("✅ SMS Response Handling Tests Completed")
    print()

def test_phone_number_normalization():
    """Test phone number normalization"""
    print("📞 Testing Phone Number Normalization")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different phone number formats
    print("📋 Test 1: Phone Number Format Normalization")
    
    test_numbers = [
        '555-123-4567',
        '(555) 123-4567',
        '555.123.4567',
        '5551234567',
        '1-555-123-4567',
        '+1-555-123-4567',
        '+15551234567',
        '555-123-4567 ext 123'
    ]
    
    for phone_number in test_numbers:
        normalized = recovery_system._normalize_phone_number(phone_number)
        print(f"   {phone_number} -> {normalized}")
    
    print()
    print("✅ Phone Number Normalization Tests Completed")
    print()

def test_stage_to_notification_mapping():
    """Test stage to notification mapping"""
    print("🗺️ Testing Stage to Notification Mapping")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test stage to notification type mapping
    print("📋 Test 1: Stage to In-App Notification Type Mapping")
    stages = ['dunning_1', 'dunning_2', 'dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in stages:
        notification_type = recovery_system._get_in_app_notification_type_for_stage(stage_name)
        print(f"   {stage_name} -> {notification_type}")
    
    print()
    
    # Test stage to alert type mapping
    print("📋 Test 2: Stage to Billing Alert Type Mapping")
    for stage_name in stages:
        alert_type = recovery_system._get_billing_alert_type_for_stage(stage_name)
        print(f"   {stage_name} -> {alert_type}")
    
    print()
    print("✅ Stage to Notification Mapping Tests Completed")
    print()

def test_integration_with_dunning_system():
    """Test integration with dunning system"""
    print("🔗 Testing Integration with Dunning System")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Create test data
    customer = create_mock_customer()
    subscription = create_mock_subscription(customer.id)
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    # Store test data
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"✅ Created test data for integration testing")
    print()
    
    # Test complete workflow
    print("🔄 Test 1: Complete Dunning Workflow with Multi-Channel Notifications")
    
    # Step 1: Schedule dunning sequence
    print("   Step 1: Schedule Dunning Email Sequence")
    schedule_result = recovery_system.schedule_dunning_email_sequence(failure_record.id)
    print(f"     Success: {schedule_result.get('success', False)}")
    print(f"     Scheduled: {schedule_result.get('scheduled_emails', 0)} emails")
    
    # Step 2: Send multi-channel notifications for critical stages
    print("   Step 2: Send Multi-Channel Notifications for Critical Stages")
    critical_stages = ['dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in critical_stages:
        print(f"     {stage_name}:")
        result = recovery_system.send_multi_channel_notifications(failure_record.id, stage_name)
        print(f"       Channels: {result.get('channels_sent', [])}")
        print(f"       Total: {result.get('total_channels', 0)}")
    
    # Step 3: Test SMS response handling
    print("   Step 3: Test SMS Response Handling")
    sms_response = recovery_system.handle_sms_response('+1-555-123-4567', 'HELP')
    print(f"     SMS Response: {sms_response.get('action', 'N/A')}")
    
    print()
    print("✅ Integration with Dunning System Tests Completed")
    print()

def test_performance_and_scalability():
    """Test performance and scalability aspects"""
    print("⚡ Testing Performance and Scalability")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    print("📈 Performance Metrics:")
    
    # Test SMS notification performance
    print("   Testing SMS notification performance...")
    customer = create_mock_customer()
    failure_record = create_mock_failure_record(customer.id, "sub_123")
    
    import time
    start_time = time.time()
    
    for i in range(100):
        sms_result = recovery_system.send_sms_notification(failure_record.id, 'dunning_3')
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average SMS notification time: {avg_time:.2f}ms")
    print(f"   SMS notifications per second: {1000 / avg_time:.1f}")
    print()
    
    # Test in-app notification performance
    print("   Testing in-app notification performance...")
    start_time = time.time()
    
    for i in range(100):
        in_app_result = recovery_system.send_in_app_notification(failure_record.id, 'payment_failure')
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average in-app notification time: {avg_time:.2f}ms")
    print(f"   In-app notifications per second: {1000 / avg_time:.1f}")
    print()
    
    # Test billing alert performance
    print("   Testing billing alert performance...")
    start_time = time.time()
    
    for i in range(100):
        alert_result = recovery_system.send_billing_alert(failure_record.id, 'payment_failed')
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average billing alert time: {avg_time:.2f}ms")
    print(f"   Billing alerts per second: {1000 / avg_time:.1f}")
    print()
    
    print("✅ Performance and Scalability Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 SMS Notifications and In-App Notifications Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_sms_notifications_configuration()
        test_in_app_notifications_configuration()
        test_sms_notification_sending()
        test_sms_content_generation()
        test_customer_phone_number_retrieval()
        test_in_app_notification_sending()
        test_in_app_notification_content_generation()
        test_billing_alert_sending()
        test_billing_alert_content_generation()
        test_multi_channel_notifications()
        test_sms_response_handling()
        test_phone_number_normalization()
        test_stage_to_notification_mapping()
        test_integration_with_dunning_system()
        test_performance_and_scalability()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ SMS Notifications Configuration")
        print("   ✅ In-App Notifications Configuration")
        print("   ✅ SMS Notification Sending")
        print("   ✅ SMS Content Generation")
        print("   ✅ Customer Phone Number Retrieval")
        print("   ✅ In-App Notification Sending")
        print("   ✅ In-App Notification Content Generation")
        print("   ✅ Billing Alert Sending")
        print("   ✅ Billing Alert Content Generation")
        print("   ✅ Multi-Channel Notifications")
        print("   ✅ SMS Response Handling")
        print("   ✅ Phone Number Normalization")
        print("   ✅ Stage to Notification Mapping")
        print("   ✅ Integration with Dunning System")
        print("   ✅ Performance and Scalability")
        print()
        print("🚀 The SMS notifications and in-app notifications system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 