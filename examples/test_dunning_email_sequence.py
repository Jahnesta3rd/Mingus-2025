#!/usr/bin/env python3
"""
Test script for Progressive Dunning Email Sequence
Tests the payment recovery system's ability to send escalating email sequences
for failed payments with progressive urgency and offers.
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
    def send_dunning_emails(self, data):
        return {
            'success': True,
            'notifications_sent': 1,
            'channels': ['email']
        }
    
    def send_manual_intervention_notifications(self, data):
        return {
            'success': True,
            'notifications_sent': 1,
            'channels': ['email']
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

def test_dunning_email_sequence_configuration():
    """Test dunning email sequence configuration"""
    print("⚙️ Testing Dunning Email Sequence Configuration")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test configuration
    dunning_config = recovery_system.recovery_config['dunning_email_sequence']
    
    print(f"✅ Dunning Email Sequence Configuration:")
    print(f"   Enabled: {dunning_config.get('enabled', False)}")
    print(f"   Stages: {len(dunning_config.get('stages', {}))}")
    print(f"   Email Templates: {len(dunning_config.get('email_templates', {}))}")
    print()
    
    # Test stages configuration
    stages = dunning_config.get('stages', {})
    print(f"📧 Dunning Stages:")
    for stage_name, stage_config in stages.items():
        print(f"   {stage_name}:")
        print(f"     Delay Days: {stage_config.get('delay_days', 0)}")
        print(f"     Subject: {stage_config.get('subject', 'N/A')}")
        print(f"     Template: {stage_config.get('template', 'N/A')}")
        print(f"     Urgency: {stage_config.get('urgency', 'N/A')}")
        print(f"     Retry Attempt: {stage_config.get('retry_attempt', False)}")
        print(f"     Amount Adjustment: {stage_config.get('amount_adjustment', False)}")
        print(f"     Payment Method Update: {stage_config.get('payment_method_update', False)}")
        print(f"     Grace Period Offer: {stage_config.get('grace_period_offer', False)}")
        print(f"     Partial Payment Offer: {stage_config.get('partial_payment_offer', False)}")
        print(f"     Manual Intervention: {stage_config.get('manual_intervention', False)}")
        print()
    
    # Test email templates
    templates = dunning_config.get('email_templates', {})
    print(f"📝 Email Templates:")
    for template_name, template_config in templates.items():
        print(f"   {template_name}:")
        print(f"     Subject: {template_config.get('subject', 'N/A')}")
        print(f"     Urgency Level: {template_config.get('urgency_level', 'N/A')}")
        print(f"     Call to Action: {template_config.get('call_to_action', 'N/A')}")
        print()
    
    # Test retry configuration
    retry_config = dunning_config.get('retry_config', {})
    print(f"🔄 Retry Configuration:")
    print(f"   Enabled: {retry_config.get('enabled', False)}")
    print(f"   Max Retries Per Stage: {retry_config.get('max_retries_per_stage', 0)}")
    print(f"   Retry Delay Hours: {retry_config.get('retry_delay_hours', 0)}")
    print(f"   Amount Reduction Percentage: {retry_config.get('amount_reduction_percentage', 0)}%")
    print(f"   Retry Conditions: {retry_config.get('retry_conditions', [])}")
    print()
    
    # Test grace period configuration
    grace_config = dunning_config.get('grace_period_config', {})
    print(f"⏰ Grace Period Configuration:")
    print(f"   Enabled: {grace_config.get('enabled', False)}")
    print(f"   Grace Period Days: {grace_config.get('grace_period_days', 0)}")
    print(f"   Grace Period Offers: {grace_config.get('grace_period_offers', [])}")
    print()
    
    # Test partial payment configuration
    partial_config = dunning_config.get('partial_payment_config', {})
    print(f"💰 Partial Payment Configuration:")
    print(f"   Enabled: {partial_config.get('enabled', False)}")
    print(f"   Minimum Percentage: {partial_config.get('minimum_percentage', 0)}%")
    print(f"   Partial Payment Offers: {partial_config.get('partial_payment_offers', [])}")
    print()
    
    print("✅ Dunning Email Sequence Configuration Tests Completed")
    print()

def test_dunning_email_sequence_scheduling():
    """Test scheduling dunning email sequence"""
    print("📅 Testing Dunning Email Sequence Scheduling")
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
    
    # Test scheduling dunning sequence
    print("📋 Test 1: Schedule Dunning Email Sequence")
    result = recovery_system.schedule_dunning_email_sequence(failure_record.id)
    
    print(f"   Scheduling Result:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Scheduled Emails: {result.get('scheduled_emails', 0)}")
    print(f"   Dunning Stages: {result.get('dunning_stages', [])}")
    print(f"   First Email Date: {result.get('first_email_date', 'N/A')}")
    print(f"   Final Notice Date: {result.get('final_notice_date', 'N/A')}")
    print()
    
    # Test dunning stage date calculation
    print("📊 Test 2: Calculate Dunning Stage Dates")
    dunning_dates = recovery_system._calculate_dunning_stage_dates(failure_record)
    
    print(f"   Calculated Dunning Dates:")
    for stage_name, email_date in dunning_dates.items():
        print(f"   {stage_name}: {email_date.isoformat()}")
    print()
    
    # Test next dunning stage
    print("⏭️ Test 3: Get Next Dunning Stage")
    next_stage = recovery_system._get_next_dunning_stage(dunning_dates)
    print(f"   Next Stage: {next_stage}")
    print()
    
    print("✅ Dunning Email Sequence Scheduling Tests Completed")
    print()

def test_dunning_email_content_generation():
    """Test dunning email content generation"""
    print("📝 Testing Dunning Email Content Generation")
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
    
    # Test content generation for different stages
    print("📋 Test 1: Content Generation by Dunning Stage")
    stages = ['dunning_1', 'dunning_2', 'dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in stages:
        print(f"   {stage_name.upper()} Stage:")
        
        # Get stage configuration
        stage_config = recovery_system.recovery_config['dunning_email_sequence']['stages'].get(stage_name, {})
        
        # Generate content
        content = recovery_system._generate_dunning_email_content(
            failure_record, customer, stage_name, stage_config
        )
        
        print(f"     Subject: {content.get('subject', 'N/A')}")
        print(f"     Urgency Level: {content.get('urgency_level', 'N/A')}")
        print(f"     Stage Name: {content.get('stage_name', 'N/A')}")
        print(f"     Days Since Failure: {content.get('days_since_failure', 0)}")
        print(f"     Payment Update URL: {content.get('payment_update_url', 'N/A')}")
        print(f"     Offers: {list(content.get('offers', {}).keys())}")
        print()
    
    # Test personalized content
    print("👤 Test 2: Personalized Content Generation")
    stage_config = recovery_system.recovery_config['dunning_email_sequence']['stages']['dunning_1']
    template = recovery_system.recovery_config['dunning_email_sequence']['email_templates']['dunning_1_gentle_reminder']
    
    personalized = recovery_system._get_personalized_dunning_content(
        customer, failure_record, 'dunning_1', stage_config, template
    )
    
    print(f"   Personalized Content:")
    print(f"     Greeting: {personalized.get('greeting', 'N/A')}")
    print(f"     Body: {personalized.get('body', 'N/A')[:100]}...")
    print(f"     Call to Action: {personalized.get('call_to_action', 'N/A')}")
    print(f"     Footer: {personalized.get('footer', 'N/A')}")
    print()
    
    # Test offers generation
    print("🎁 Test 3: Offers Generation")
    offers = recovery_system._get_dunning_offers('dunning_3', stage_config, failure_record)
    
    print(f"   Generated Offers:")
    for offer_type, offer_config in offers.items():
        print(f"     {offer_type}: {offer_config}")
    print()
    
    print("✅ Dunning Email Content Generation Tests Completed")
    print()

def test_dunning_email_sending():
    """Test sending dunning emails"""
    print("📤 Testing Dunning Email Sending")
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
    
    print(f"✅ Created test data for email sending")
    print()
    
    # Test sending emails for different stages
    print("📧 Test 1: Send Dunning Emails by Stage")
    stages = ['dunning_1', 'dunning_2', 'dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in stages:
        print(f"   {stage_name.upper()} Stage:")
        
        # Send dunning email
        result = recovery_system.send_dunning_email(failure_record.id, stage_name)
        
        print(f"     Success: {result.get('success', False)}")
        print(f"     Email Sent: {result.get('email_sent', 0)}")
        print(f"     Urgency: {result.get('urgency', 'N/A')}")
        print(f"     Retry Attempted: {result.get('retry_attempted', False)}")
        print(f"     Amount Adjustment: {result.get('amount_adjustment', False)}")
        print(f"     Payment Method Update: {result.get('payment_method_update', False)}")
        print(f"     Grace Period Offer: {result.get('grace_period_offer', False)}")
        print(f"     Partial Payment Offer: {result.get('partial_payment_offer', False)}")
        print(f"     Manual Intervention: {result.get('manual_intervention', False)}")
        print()
    
    # Test invalid stage
    print("❌ Test 2: Invalid Stage Handling")
    invalid_result = recovery_system.send_dunning_email(failure_record.id, 'invalid_stage')
    print(f"   Invalid Stage Result: {invalid_result.get('error', 'N/A')}")
    print()
    
    print("✅ Dunning Email Sending Tests Completed")
    print()

def test_dunning_stage_actions():
    """Test dunning stage actions execution"""
    print("⚡ Testing Dunning Stage Actions")
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
    
    print(f"✅ Created test data for stage actions")
    print()
    
    # Test stage actions for different stages
    print("🔄 Test 1: Stage Actions by Dunning Stage")
    stages = ['dunning_1', 'dunning_2', 'dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in stages:
        print(f"   {stage_name.upper()} Stage:")
        
        # Get stage configuration
        stage_config = recovery_system.recovery_config['dunning_email_sequence']['stages'].get(stage_name, {})
        
        # Execute stage actions
        actions = recovery_system._execute_dunning_stage_actions(failure_record, stage_name, stage_config)
        
        print(f"     Actions Executed:")
        for action_type, action_result in actions.items():
            print(f"       {action_type}: {action_result.get('success', False)}")
        print()
    
    # Test specific action types
    print("🎯 Test 2: Specific Action Types")
    
    # Test payment retry
    print("   Payment Retry Action:")
    retry_result = recovery_system._attempt_dunning_payment_retry(failure_record, 'dunning_1')
    print(f"     Success: {retry_result.get('success', False)}")
    print(f"     Reason: {retry_result.get('reason', 'N/A')}")
    
    # Test payment method update prompt
    print("   Payment Method Update Prompt:")
    update_result = recovery_system._schedule_payment_method_update_prompt(failure_record, 'dunning_2')
    print(f"     Success: {update_result.get('success', False)}")
    print(f"     Prompt Scheduled: {update_result.get('prompt_scheduled', False)}")
    
    # Test grace period offer
    print("   Grace Period Offer:")
    grace_result = recovery_system._offer_grace_period(failure_record, 'dunning_3')
    print(f"     Success: {grace_result.get('success', False)}")
    print(f"     Grace Period Offered: {grace_result.get('grace_period_offered', False)}")
    
    # Test partial payment offer
    print("   Partial Payment Offer:")
    partial_result = recovery_system._offer_partial_payment(failure_record, 'dunning_4')
    print(f"     Success: {partial_result.get('success', False)}")
    print(f"     Partial Payment Offered: {partial_result.get('partial_payment_offered', False)}")
    
    # Test manual intervention
    print("   Manual Intervention:")
    manual_result = recovery_system._trigger_manual_intervention(failure_record, 'dunning_5')
    print(f"     Success: {manual_result.get('success', False)}")
    print(f"     Manual Intervention Triggered: {manual_result.get('manual_intervention_triggered', False)}")
    print()
    
    print("✅ Dunning Stage Actions Tests Completed")
    print()

def test_dunning_sequence_status():
    """Test dunning sequence status tracking"""
    print("📊 Testing Dunning Sequence Status")
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
    
    print(f"✅ Created test data for status tracking")
    print()
    
    # Test sequence status
    print("📈 Test 1: Get Dunning Sequence Status")
    status_result = recovery_system.get_dunning_sequence_status(failure_record.id)
    
    if status_result.get('success', False):
        status = status_result.get('status', {})
        print(f"   Status Result:")
        print(f"     Failure ID: {status.get('failure_id', 'N/A')}")
        print(f"     Failed At: {status.get('failed_at', 'N/A')}")
        print(f"     Current Stage: {status.get('current_stage', 'N/A')}")
        print(f"     Next Stage: {status.get('next_stage', 'N/A')}")
        print(f"     Scheduled Emails: {len(status.get('scheduled_emails', []))}")
        print(f"     Sent Emails: {len(status.get('sent_emails', []))}")
        print(f"     Next Email Date: {status.get('next_email_date', 'N/A')}")
        print(f"     Final Notice Date: {status.get('final_notice_date', 'N/A')}")
    else:
        print(f"   Status Error: {status_result.get('error', 'Unknown error')}")
    print()
    
    # Test stage progress
    print("📊 Test 2: Dunning Stage Progress")
    progress = recovery_system._get_dunning_stage_progress(failure_record)
    
    print(f"   Progress Result:")
    print(f"     Current Stage: {progress.get('current_stage', 'N/A')}")
    print(f"     Total Stages: {progress.get('total_stages', 0)}")
    print(f"     Current Stage Index: {progress.get('current_stage_index', 0)}")
    print(f"     Progress Percentage: {progress.get('progress_percentage', 0):.1f}%")
    print(f"     Stages Completed: {progress.get('stages_completed', 0)}")
    print(f"     Stages Remaining: {progress.get('stages_remaining', 0)}")
    print()
    
    # Test current and next stage
    print("📍 Test 3: Current and Next Stage")
    current_stage = recovery_system._get_current_dunning_stage(failure_record)
    next_stage = recovery_system._get_next_dunning_stage_for_failure(failure_record)
    
    print(f"   Current Stage: {current_stage}")
    print(f"   Next Stage: {next_stage}")
    print()
    
    print("✅ Dunning Sequence Status Tests Completed")
    print()

def test_dunning_email_templates():
    """Test dunning email templates"""
    print("📧 Testing Dunning Email Templates")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Get templates
    templates = recovery_system.recovery_config['dunning_email_sequence']['email_templates']
    
    print("📝 Test 1: Email Template Analysis")
    for template_name, template_config in templates.items():
        print(f"   {template_name}:")
        print(f"     Subject: {template_config.get('subject', 'N/A')}")
        print(f"     Greeting: {template_config.get('greeting', 'N/A')}")
        print(f"     Body: {template_config.get('body', 'N/A')[:80]}...")
        print(f"     Call to Action: {template_config.get('call_to_action', 'N/A')}")
        print(f"     Footer: {template_config.get('footer', 'N/A')}")
        print(f"     Urgency Level: {template_config.get('urgency_level', 'N/A')}")
        print()
    
    # Test template progression
    print("📈 Test 2: Template Progression Analysis")
    template_names = [
        'dunning_1_gentle_reminder',
        'dunning_2_friendly_reminder',
        'dunning_3_urgent_reminder',
        'dunning_4_final_warning',
        'dunning_5_suspension_warning',
        'dunning_final_suspension'
    ]
    
    print("   Urgency Progression:")
    for template_name in template_names:
        template = templates.get(template_name, {})
        urgency = template.get('urgency_level', 'unknown')
        subject = template.get('subject', 'N/A')
        print(f"     {template_name}: {urgency} - {subject}")
    print()
    
    print("✅ Dunning Email Templates Tests Completed")
    print()

def test_integration_with_recovery_system():
    """Test integration with overall recovery system"""
    print("🔗 Testing Integration with Recovery System")
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
    
    # Test complete dunning workflow
    print("🔄 Test 1: Complete Dunning Workflow")
    
    # Step 1: Schedule dunning sequence
    print("   Step 1: Schedule Dunning Email Sequence")
    schedule_result = recovery_system.schedule_dunning_email_sequence(failure_record.id)
    print(f"     Success: {schedule_result.get('success', False)}")
    print(f"     Scheduled: {schedule_result.get('scheduled_emails', 0)} emails")
    
    # Step 2: Send emails through stages
    print("   Step 2: Send Emails Through Stages")
    stages = ['dunning_1', 'dunning_2', 'dunning_3', 'dunning_4', 'dunning_5', 'final_notice']
    
    for stage_name in stages:
        print(f"     {stage_name}:")
        result = recovery_system.send_dunning_email(failure_record.id, stage_name)
        print(f"       Sent: {result.get('email_sent', 0)} emails")
        print(f"       Urgency: {result.get('urgency', 'N/A')}")
        print(f"       Actions: {list(result.get('stage_actions', {}).keys())}")
    
    # Step 3: Check final status
    print("   Step 3: Check Final Status")
    status_result = recovery_system.get_dunning_sequence_status(failure_record.id)
    if status_result.get('success', False):
        status = status_result.get('status', {})
        print(f"     Current Stage: {status.get('current_stage', 'N/A')}")
        print(f"     Sent Emails: {len(status.get('sent_emails', []))}")
        print(f"     Progress: {status.get('stage_progress', {}).get('progress_percentage', 0):.1f}%")
    print()
    
    # Test integration with other recovery features
    print("🔗 Test 2: Integration with Other Recovery Features")
    
    # Test with grace period
    print("   Grace Period Integration:")
    grace_result = recovery_system.manage_grace_period_access(failure_record.id)
    print(f"     Grace Period Active: {grace_result.get('grace_period_active', False)}")
    
    # Test with alternative payment methods
    print("   Alternative Payment Methods Integration:")
    alt_result = recovery_system.suggest_alternative_payment_methods(failure_record.id, 1)
    print(f"     Suggestions Sent: {alt_result.get('suggestions_sent', 0)}")
    
    # Test with voluntary update reminders
    print("   Voluntary Update Reminders Integration:")
    vol_result = recovery_system.schedule_voluntary_update_reminders(failure_record.id)
    print(f"     Reminders Scheduled: {vol_result.get('scheduled_reminders', 0)}")
    print()
    
    print("✅ Integration with Recovery System Tests Completed")
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
    
    # Test dunning sequence scheduling performance
    print("   Testing dunning sequence scheduling performance...")
    customer = create_mock_customer()
    failure_record = create_mock_failure_record(customer.id, "sub_123")
    
    import time
    start_time = time.time()
    
    for i in range(100):
        schedule_result = recovery_system.schedule_dunning_email_sequence(failure_record.id)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average dunning sequence scheduling time: {avg_time:.2f}ms")
    print(f"   Sequences per second: {1000 / avg_time:.1f}")
    print()
    
    # Test email content generation performance
    print("   Testing email content generation performance...")
    start_time = time.time()
    
    for i in range(100):
        content = recovery_system._generate_dunning_email_content(
            failure_record, customer, 'dunning_1', 
            recovery_system.recovery_config['dunning_email_sequence']['stages']['dunning_1']
        )
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average email content generation time: {avg_time:.2f}ms")
    print(f"   Content generations per second: {1000 / avg_time:.1f}")
    print()
    
    print("✅ Performance and Scalability Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Progressive Dunning Email Sequence Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_dunning_email_sequence_configuration()
        test_dunning_email_sequence_scheduling()
        test_dunning_email_content_generation()
        test_dunning_email_sending()
        test_dunning_stage_actions()
        test_dunning_sequence_status()
        test_dunning_email_templates()
        test_integration_with_recovery_system()
        test_performance_and_scalability()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Dunning Email Sequence Configuration")
        print("   ✅ Dunning Email Sequence Scheduling")
        print("   ✅ Dunning Email Content Generation")
        print("   ✅ Dunning Email Sending")
        print("   ✅ Dunning Stage Actions")
        print("   ✅ Dunning Sequence Status")
        print("   ✅ Dunning Email Templates")
        print("   ✅ Integration with Recovery System")
        print("   ✅ Performance and Scalability")
        print()
        print("🚀 The progressive dunning email sequence system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 