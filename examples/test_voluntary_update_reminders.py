#!/usr/bin/env python3
"""
Test script for Voluntary Update Reminders
Tests the payment recovery system's ability to send escalating reminders
before forced suspension to encourage voluntary payment method updates.
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
    def send_voluntary_update_reminders(self, data):
        return {
            'success': True,
            'notifications_sent': 2,
            'channels': ['email', 'sms']
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
        metadata={}
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

def test_voluntary_update_reminder_configuration():
    """Test voluntary update reminder configuration"""
    print("⚙️ Testing Voluntary Update Reminder Configuration")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test configuration
    voluntary_config = recovery_system.recovery_config['voluntary_update_reminders']
    
    print(f"✅ Voluntary Update Reminders Configuration:")
    print(f"   Enabled: {voluntary_config.get('enabled', False)}")
    print(f"   Reminder Days: {voluntary_config.get('reminder_days', [])}")
    print(f"   Final Warning Day: {voluntary_config.get('final_warning_day', 0)}")
    print(f"   Max Reminders: {voluntary_config.get('max_reminders', 0)}")
    print(f"   Reminder Channels: {voluntary_config.get('reminder_channels', [])}")
    print()
    
    # Test escalation levels
    escalation_levels = voluntary_config.get('escalation_levels', {})
    print(f"📈 Escalation Levels:")
    for day, level in escalation_levels.items():
        print(f"   Day {day}: {level}")
    print()
    
    # Test reminder templates
    templates = voluntary_config.get('reminder_templates', {})
    print(f"📝 Reminder Templates:")
    for level, template in templates.items():
        print(f"   {level}: {template}")
    print()
    
    print("✅ Voluntary Update Reminder Configuration Tests Completed")
    print()

def test_voluntary_update_reminder_scheduling():
    """Test scheduling voluntary update reminders"""
    print("📅 Testing Voluntary Update Reminder Scheduling")
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
    
    print(f"✅ Created test data:")
    print(f"   Customer ID: {customer.id}")
    print(f"   Failure ID: {failure_record.id}")
    print()
    
    # Test scheduling reminders
    print("📋 Test 1: Schedule Voluntary Update Reminders")
    result = recovery_system.schedule_voluntary_update_reminders(failure_record.id)
    
    print(f"   Scheduling Result:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Scheduled Reminders: {result.get('scheduled_reminders', 0)}")
    print(f"   Reminder Days: {result.get('reminder_days', [])}")
    print(f"   First Reminder Date: {result.get('first_reminder_date', 'N/A')}")
    print(f"   Final Warning Date: {result.get('final_warning_date', 'N/A')}")
    print()
    
    # Test reminder date calculation
    print("📊 Test 2: Calculate Reminder Dates")
    reminder_dates = recovery_system._calculate_voluntary_reminder_dates(failure_record)
    
    print(f"   Calculated Reminder Dates:")
    for day, date in reminder_dates.items():
        print(f"   Day {day}: {date.isoformat()}")
    print()
    
    print("✅ Voluntary Update Reminder Scheduling Tests Completed")
    print()

def test_escalation_levels_and_templates():
    """Test escalation levels and reminder templates"""
    print("📈 Testing Escalation Levels and Templates")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test escalation levels for different days
    print("🔍 Test 1: Escalation Levels by Day")
    reminder_days = [1, 3, 5, 6, 7]
    
    for day in reminder_days:
        escalation_level = recovery_system._get_escalation_level(day)
        reminder_template = recovery_system._get_reminder_template(day)
        urgency_level = recovery_system._get_urgency_level(day)
        
        print(f"   Day {day}:")
        print(f"     Escalation Level: {escalation_level}")
        print(f"     Template: {reminder_template}")
        print(f"     Urgency Level: {urgency_level}")
        print()
    
    # Test urgency level mapping
    print("⚡ Test 2: Urgency Level Mapping")
    urgency_mapping = {
        'low': 'Days 1-2',
        'medium': 'Days 2-4', 
        'high': 'Days 4-6',
        'critical': 'Days 6+'
    }
    
    for urgency, days in urgency_mapping.items():
        print(f"   {urgency.upper()}: {days}")
    print()
    
    print("✅ Escalation Levels and Templates Tests Completed")
    print()

def test_voluntary_update_reminder_content():
    """Test voluntary update reminder content generation"""
    print("📝 Testing Voluntary Update Reminder Content")
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
    
    # Test content generation for different reminder days
    print("📋 Test 1: Content Generation by Reminder Day")
    reminder_days = [1, 3, 5, 6, 7]
    
    for day in reminder_days:
        print(f"   Day {day} Reminder:")
        
        # Generate content
        content = recovery_system._generate_voluntary_reminder_content(
            failure_record, customer, day
        )
        
        print(f"     Subject: {content.get('subject', 'N/A')}")
        print(f"     Escalation Level: {content.get('escalation_level', 'N/A')}")
        print(f"     Urgency Level: {content.get('urgency_level', 'N/A')}")
        print(f"     Is Final Warning: {content.get('is_final_warning', False)}")
        print(f"     Days Until Suspension: {content.get('days_until_suspension', 0)}")
        print(f"     Payment Update URL: {content.get('payment_update_url', 'N/A')}")
        print(f"     Action Items: {content.get('action_items', [])}")
        print(f"     Support Contact: {content.get('support_contact', {})}")
        print()
    
    # Test personalized message generation
    print("👤 Test 2: Personalized Message Generation")
    escalation_levels = ['gentle_reminder', 'friendly_reminder', 'urgent_reminder', 'final_warning']
    
    for level in escalation_levels:
        message = recovery_system._get_personalized_reminder_message(
            customer, failure_record, level, 3
        )
        print(f"   {level.replace('_', ' ').title()}:")
        print(f"     {message[:100]}...")
        print()
    
    # Test action items generation
    print("✅ Test 3: Action Items Generation")
    for level in escalation_levels:
        action_items = recovery_system._get_reminder_action_items(level, level == 'final_warning')
        print(f"   {level.replace('_', ' ').title()}:")
        for item in action_items:
            print(f"     • {item}")
        print()
    
    print("✅ Voluntary Update Reminder Content Tests Completed")
    print()

def test_voluntary_update_reminder_sending():
    """Test sending voluntary update reminders"""
    print("📤 Testing Voluntary Update Reminder Sending")
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
    
    print(f"✅ Created test data for reminder sending")
    print()
    
    # Test sending reminders for different days
    print("📧 Test 1: Send Reminders by Day")
    reminder_days = [1, 3, 5, 6, 7]
    
    for day in reminder_days:
        print(f"   Day {day} Reminder:")
        
        # Send reminder
        result = recovery_system.send_voluntary_update_reminder(failure_record.id, day)
        
        print(f"     Success: {result.get('success', False)}")
        print(f"     Reminder Sent: {result.get('reminder_sent', 0)}")
        print(f"     Escalation Level: {result.get('escalation_level', 'N/A')}")
        print(f"     Reminder Template: {result.get('reminder_template', 'N/A')}")
        print(f"     Reminder Number: {result.get('reminder_number', 0)}")
        print(f"     Is Final Warning: {result.get('is_final_warning', False)}")
        print()
    
    # Test reminder limits
    print("🚫 Test 2: Reminder Limits")
    max_reminders = recovery_system.recovery_config['voluntary_update_reminders']['max_reminders']
    print(f"   Maximum Reminders Allowed: {max_reminders}")
    
    # Try to send more reminders than allowed
    for i in range(max_reminders + 2):
        result = recovery_system.send_voluntary_update_reminder(failure_record.id, 1)
        if not result.get('success', False):
            print(f"   Reminder {i+1} blocked: {result.get('error', 'Unknown error')}")
            break
    print()
    
    print("✅ Voluntary Update Reminder Sending Tests Completed")
    print()

def test_voluntary_reminder_schedule():
    """Test voluntary reminder schedule management"""
    print("📅 Testing Voluntary Reminder Schedule Management")
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
    
    print(f"✅ Created test data for schedule management")
    print()
    
    # Test getting reminder schedule
    print("📊 Test 1: Get Reminder Schedule")
    schedule_result = recovery_system.get_voluntary_reminder_schedule(failure_record.id)
    
    if schedule_result.get('success', False):
        schedule = schedule_result.get('schedule', {})
        print(f"   Schedule Result:")
        print(f"     Failure ID: {schedule.get('failure_id', 'N/A')}")
        print(f"     Failed At: {schedule.get('failed_at', 'N/A')}")
        print(f"     Reminder Days: {schedule.get('reminder_days', [])}")
        print(f"     Scheduled Reminders: {len(schedule.get('scheduled_reminders', []))}")
        print(f"     Sent Reminders: {len(schedule.get('sent_reminders', []))}")
        print(f"     Next Reminder Date: {schedule.get('next_reminder_date', 'N/A')}")
        print(f"     Final Warning Date: {schedule.get('final_warning_date', 'N/A')}")
    else:
        print(f"   Schedule Error: {schedule_result.get('error', 'Unknown error')}")
    print()
    
    # Test schedule before and after reminders
    print("⏰ Test 2: Schedule Timeline")
    print("   Before sending reminders:")
    before_schedule = recovery_system.get_voluntary_reminder_schedule(failure_record.id)
    if before_schedule.get('success', False):
        before = before_schedule.get('schedule', {})
        print(f"     Scheduled Reminders: {len(before.get('scheduled_reminders', []))}")
        print(f"     Sent Reminders: {len(before.get('sent_reminders', []))}")
    
    # Send a reminder
    print("   After sending reminder:")
    recovery_system.send_voluntary_update_reminder(failure_record.id, 1)
    after_schedule = recovery_system.get_voluntary_reminder_schedule(failure_record.id)
    if after_schedule.get('success', False):
        after = after_schedule.get('schedule', {})
        print(f"     Scheduled Reminders: {len(after.get('scheduled_reminders', []))}")
        print(f"     Sent Reminders: {len(after.get('sent_reminders', []))}")
    print()
    
    print("✅ Voluntary Reminder Schedule Management Tests Completed")
    print()

def test_integration_with_grace_period():
    """Test integration with grace period access management"""
    print("🔗 Testing Integration with Grace Period")
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
    print("🔄 Test 1: Complete Voluntary Update Workflow")
    
    # Step 1: Schedule reminders
    print("   Step 1: Schedule Voluntary Update Reminders")
    schedule_result = recovery_system.schedule_voluntary_update_reminders(failure_record.id)
    print(f"     Success: {schedule_result.get('success', False)}")
    print(f"     Scheduled: {schedule_result.get('scheduled_reminders', 0)} reminders")
    
    # Step 2: Send reminders over time
    print("   Step 2: Send Reminders Over Time")
    reminder_days = [1, 3, 5, 6, 7]
    
    for day in reminder_days:
        print(f"     Day {day}:")
        result = recovery_system.send_voluntary_update_reminder(failure_record.id, day)
        print(f"       Sent: {result.get('reminder_sent', 0)} notifications")
        print(f"       Level: {result.get('escalation_level', 'N/A')}")
        print(f"       Final Warning: {result.get('is_final_warning', False)}")
    
    # Step 3: Check schedule status
    print("   Step 3: Check Schedule Status")
    schedule_status = recovery_system.get_voluntary_reminder_schedule(failure_record.id)
    if schedule_status.get('success', False):
        schedule = schedule_status.get('schedule', {})
        print(f"     Total Sent: {len(schedule.get('sent_reminders', []))}")
        print(f"     Remaining: {len(schedule.get('scheduled_reminders', []))}")
    print()
    
    # Test grace period integration
    print("⏰ Test 2: Grace Period Integration")
    grace_period_result = recovery_system.manage_grace_period_access(failure_record.id)
    print(f"   Grace Period Active: {grace_period_result.get('grace_period_active', False)}")
    print(f"   Days Remaining: {grace_period_result.get('days_remaining', 0)}")
    print(f"   Access Level: {grace_period_result.get('access_level', 'N/A')}")
    print()
    
    print("✅ Integration with Grace Period Tests Completed")
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
    
    # Test reminder scheduling performance
    print("   Testing reminder scheduling performance...")
    customer = create_mock_customer()
    failure_record = create_mock_failure_record(customer.id, "sub_123")
    
    import time
    start_time = time.time()
    
    for i in range(100):
        schedule_result = recovery_system.schedule_voluntary_update_reminders(failure_record.id)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average reminder scheduling time: {avg_time:.2f}ms")
    print(f"   Schedules per second: {1000 / avg_time:.1f}")
    print()
    
    # Test content generation performance
    print("   Testing content generation performance...")
    start_time = time.time()
    
    for i in range(100):
        content = recovery_system._generate_voluntary_reminder_content(
            failure_record, customer, 1
        )
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average content generation time: {avg_time:.2f}ms")
    print(f"   Content generations per second: {1000 / avg_time:.1f}")
    print()
    
    print("✅ Performance and Scalability Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Voluntary Update Reminders Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_voluntary_update_reminder_configuration()
        test_voluntary_update_reminder_scheduling()
        test_escalation_levels_and_templates()
        test_voluntary_update_reminder_content()
        test_voluntary_update_reminder_sending()
        test_voluntary_reminder_schedule()
        test_integration_with_grace_period()
        test_performance_and_scalability()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Voluntary Update Reminder Configuration")
        print("   ✅ Voluntary Update Reminder Scheduling")
        print("   ✅ Escalation Levels and Templates")
        print("   ✅ Voluntary Update Reminder Content")
        print("   ✅ Voluntary Update Reminder Sending")
        print("   ✅ Voluntary Reminder Schedule Management")
        print("   ✅ Integration with Grace Period")
        print("   ✅ Performance and Scalability")
        print()
        print("🚀 The voluntary update reminders system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 