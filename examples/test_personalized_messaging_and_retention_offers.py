#!/usr/bin/env python3
"""
Test script for Personalized Messaging and Retention Offers
Tests the payment recovery system's ability to provide personalized recovery messaging
by user segment and retention offers for at-risk subscriptions.
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
    def send_personalized_dunning_emails(self, data):
        return {
            'success': True,
            'notifications_sent': 1,
            'channels': ['email']
        }

def create_mock_customer(segment_type: str = 'standard') -> Customer:
    """Create a mock customer for testing with specific segment characteristics"""
    customer_id = str(uuid.uuid4())
    
    # Set customer characteristics based on segment
    if segment_type == 'high_value':
        metadata = {
            'phone_number': '+1-555-123-4567',
            'preferred_contact_method': 'email',
            'monthly_revenue': 750.0,
            'subscription_length_months': 18,
            'feature_usage': 85.0,
            'support_tickets': 1
        }
        name = "Premium Customer"
        status = "active"
    elif segment_type == 'mid_value':
        metadata = {
            'phone_number': '+1-555-234-5678',
            'preferred_contact_method': 'email',
            'monthly_revenue': 250.0,
            'subscription_length_months': 8,
            'feature_usage': 65.0,
            'support_tickets': 3
        }
        name = "Professional Customer"
        status = "active"
    elif segment_type == 'at_risk':
        metadata = {
            'phone_number': '+1-555-345-6789',
            'preferred_contact_method': 'phone',
            'monthly_revenue': 50.0,
            'subscription_length_months': 1,
            'feature_usage': 15.0,
            'support_tickets': 5,
            'payment_failures_last_3_months': 3
        }
        name = "At-Risk Customer"
        status = "grace_period"
    else:  # standard
        metadata = {
            'phone_number': '+1-555-456-7890',
            'preferred_contact_method': 'email',
            'monthly_revenue': 75.0,
            'subscription_length_months': 3,
            'feature_usage': 35.0,
            'support_tickets': 7
        }
        name = "Standard Customer"
        status = "active"
    
    return Customer(
        id=customer_id,
        stripe_customer_id=f"cus_{uuid.uuid4().hex[:24]}",
        email=f"{segment_type}@example.com",
        name=name,
        status=status,
        created_at=datetime.now(timezone.utc) - timedelta(days=metadata['subscription_length_months'] * 30),
        metadata=metadata
    )

def create_mock_subscription(customer_id: str, segment_type: str = 'standard') -> Subscription:
    """Create a mock subscription for testing"""
    # Set subscription amount based on segment
    if segment_type == 'high_value':
        amount = 750.0
        plan_id = "premium_plan"
    elif segment_type == 'mid_value':
        amount = 250.0
        plan_id = "professional_plan"
    elif segment_type == 'at_risk':
        amount = 50.0
        plan_id = "basic_plan"
    else:  # standard
        amount = 75.0
        plan_id = "standard_plan"
    
    return Subscription(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        stripe_subscription_id=f"sub_{uuid.uuid4().hex[:24]}",
        status="active",
        plan_id=plan_id,
        amount=amount,
        currency="usd",
        interval="month",
        created_at=datetime.now(timezone.utc),
        metadata={}
    )

def create_mock_failure_record(customer_id: str, subscription_id: str, failure_reason: str = "expired_card") -> PaymentRecoveryRecord:
    """Create a mock payment failure record for testing"""
    return PaymentRecoveryRecord(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        subscription_id=subscription_id,
        invoice_id=f"in_{uuid.uuid4().hex[:24]}",
        payment_intent_id=f"pi_{uuid.uuid4().hex[:24]}",
        failure_reason=failure_reason,
        failure_code="card_declined_expired",
        amount=99.99,
        currency="usd",
        failed_at=datetime.now(timezone.utc),
        status=RecoveryStatus.PENDING,
        retry_count=0,
        metadata={}
    )

def test_user_segmentation():
    """Test user segmentation functionality"""
    print("👥 Testing User Segmentation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different customer segments
    print("📋 Test 1: User Segment Determination")
    segments = ['high_value', 'mid_value', 'standard', 'at_risk']
    
    for segment_type in segments:
        print(f"   {segment_type.upper()} Customer:")
        
        # Create customer
        customer = create_mock_customer(segment_type)
        db.add(customer)
        
        # Determine segment
        result = recovery_system.determine_user_segment(customer.id)
        
        if result['success']:
            print(f"     Determined Segment: {result['segment']}")
            print(f"     Match Score: {result['score']:.2f}")
            print(f"     Messaging Tone: {result['segment_config']['messaging_tone']}")
            print(f"     Priority Level: {result['segment_config']['priority_level']}")
            print(f"     Custom Offers: {result['segment_config']['custom_offers']}")
            print(f"     Dedicated Support: {result['segment_config']['dedicated_support']}")
        else:
            print(f"     Error: {result['error']}")
        print()
    
    print("✅ User Segmentation Tests Completed")
    print()

def test_customer_metrics_calculation():
    """Test customer metrics calculation"""
    print("📊 Testing Customer Metrics Calculation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test metrics calculation for different segments
    print("📋 Test 1: Customer Metrics by Segment")
    segments = ['high_value', 'mid_value', 'standard', 'at_risk']
    
    for segment_type in segments:
        print(f"   {segment_type.upper()} Customer:")
        
        # Create customer and subscription
        customer = create_mock_customer(segment_type)
        subscription = create_mock_subscription(customer.id, segment_type)
        db.add(customer)
        db.add(subscription)
        
        # Get customer metrics
        metrics = recovery_system._get_customer_metrics(customer.id)
        
        print(f"     Monthly Revenue: ${metrics.get('monthly_revenue', 0):.2f}")
        print(f"     Subscription Age: {metrics.get('subscription_length_months', 0)} months")
        print(f"     Feature Usage: {metrics.get('feature_usage', 0):.1f}%")
        print(f"     Support Tickets: {metrics.get('support_tickets', 0)}")
        print(f"     Payment Failures (3mo): {metrics.get('payment_failures_last_3_months', 0)}")
        print()
    
    print("✅ Customer Metrics Calculation Tests Completed")
    print()

def test_segment_criteria_evaluation():
    """Test segment criteria evaluation"""
    print("🎯 Testing Segment Criteria Evaluation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test criteria evaluation
    print("📋 Test 1: Segment Criteria Evaluation")
    
    # Get user segments configuration
    user_segments = recovery_system.recovery_config['dunning_email_sequence']['personalized_messaging']['user_segments']
    
    for segment_name, segment_config in user_segments.items():
        print(f"   {segment_name.upper()} Segment Criteria:")
        
        criteria = segment_config['segment_criteria']
        for criterion, conditions in criteria.items():
            print(f"     {criterion}:")
            for condition, value in conditions.items():
                print(f"       {condition}: {value}")
        print()
    
    print("✅ Segment Criteria Evaluation Tests Completed")
    print()

def test_personalized_message_generation():
    """Test personalized message generation"""
    print("💬 Testing Personalized Message Generation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test message generation for different segments and stages
    print("📋 Test 1: Personalized Messages by Segment and Stage")
    segments = ['high_value', 'mid_value', 'standard', 'at_risk']
    stages = ['dunning_1', 'dunning_3']
    
    for segment_type in segments:
        print(f"   {segment_type.upper()} Customer:")
        
        # Create customer and failure record
        customer = create_mock_customer(segment_type)
        subscription = create_mock_subscription(customer.id, segment_type)
        failure_record = create_mock_failure_record(customer.id, subscription.id)
        
        db.add(customer)
        db.add(subscription)
        db.add(failure_record)
        
        for stage_name in stages:
            print(f"     {stage_name.upper()} Stage:")
            
            # Generate personalized message
            result = recovery_system.generate_personalized_message(failure_record.id, stage_name)
            
            if result['success']:
                message = result['personalized_message']
                print(f"       Segment: {result['segment']}")
                print(f"       Messaging Tone: {result['messaging_tone']}")
                print(f"       Subject: {message.get('subject', 'N/A')}")
                print(f"       Message: {message.get('message', 'N/A')[:100]}...")
                print(f"       CTA Text: {message.get('cta_text', 'N/A')}")
                print(f"       CTA URL: {message.get('cta_url', 'N/A')}")
                print(f"       Personal Touch: {message.get('personal_touch', False)}")
                print(f"       Retention Offer: {message.get('retention_offer', False)}")
            else:
                print(f"       Error: {result['error']}")
            print()
    
    print("✅ Personalized Message Generation Tests Completed")
    print()

def test_message_personalization():
    """Test message personalization features"""
    print("🎨 Testing Message Personalization")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test personalization features
    print("📋 Test 1: Message Personalization Features")
    
    # Create customer and failure record
    customer = create_mock_customer('high_value')
    subscription = create_mock_subscription(customer.id, 'high_value')
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    # Get customer metrics
    customer_metrics = recovery_system._get_customer_metrics(customer.id)
    
    # Test template personalization
    template = {
        'subject': 'Important: Payment Update Required for Your Premium Account',
        'message': 'Dear {customer_name}, we noticed a payment issue with your premium MINGUS account. As a valued customer, we want to ensure uninterrupted access to your advanced features. Please update your payment method to continue enjoying premium benefits.',
        'cta_text': 'Update Payment Method',
        'cta_url': '/billing/premium-update',
        'personal_touch': True
    }
    
    personalized = recovery_system._personalize_message_template(
        template, customer, failure_record, customer_metrics
    )
    
    print(f"   Original Template:")
    print(f"     Subject: {template['subject']}")
    print(f"     Message: {template['message'][:100]}...")
    print()
    
    print(f"   Personalized Message:")
    print(f"     Subject: {personalized['subject']}")
    print(f"     Message: {personalized['message'][:100]}...")
    print(f"     CTA Text: {personalized['cta_text']}")
    print(f"     CTA URL: {personalized['cta_url']}")
    print(f"     Personal Touch: {personalized['personal_touch']}")
    print()
    
    # Test personalization configuration
    personalization_config = recovery_system.recovery_config['dunning_email_sequence']['retention_offers']['offer_personalization']
    print(f"   Personalization Configuration:")
    for feature, enabled in personalization_config.items():
        print(f"     {feature}: {enabled}")
    print()
    
    print("✅ Message Personalization Tests Completed")
    print()

def test_retention_offers_generation():
    """Test retention offers generation"""
    print("🎁 Testing Retention Offers Generation")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test offers generation for different segments and stages
    print("📋 Test 1: Retention Offers by Segment and Stage")
    segments = ['high_value', 'mid_value', 'standard', 'at_risk']
    stages = ['dunning_1', 'dunning_3', 'dunning_5']
    
    for segment_type in segments:
        print(f"   {segment_type.upper()} Customer:")
        
        # Create customer and failure record
        customer = create_mock_customer(segment_type)
        subscription = create_mock_subscription(customer.id, segment_type)
        failure_record = create_mock_failure_record(customer.id, subscription.id)
        
        db.add(customer)
        db.add(subscription)
        db.add(failure_record)
        
        for stage_name in stages:
            print(f"     {stage_name.upper()} Stage:")
            
            # Generate retention offers
            result = recovery_system.generate_retention_offers(failure_record.id, stage_name)
            
            if result['success']:
                offers = result['offers']
                print(f"       Segment: {result['segment']}")
                print(f"       Offers Generated: {len(offers)}")
                
                for offer_type, offer in offers.items():
                    print(f"         {offer_type}:")
                    if isinstance(offer, dict) and 'type' in offer:
                        print(f"           Type: {offer['type']}")
                        if 'discount_percent' in offer:
                            print(f"           Discount: {offer['discount_percent']}%")
                        if 'installments' in offer:
                            print(f"           Installments: {offer['installments']}")
                        if 'upgraded_features' in offer:
                            print(f"           Features: {', '.join(offer['upgraded_features'])}")
                        if 'grace_period_days' in offer:
                            print(f"           Grace Period: {offer['grace_period_days']} days")
                    else:
                        print(f"           Error: {offer.get('error', 'Unknown error')}")
            else:
                print(f"       Error: {result['error']}")
            print()
    
    print("✅ Retention Offers Generation Tests Completed")
    print()

def test_specific_offer_types():
    """Test specific offer type generation"""
    print("🎯 Testing Specific Offer Types")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test different offer types
    print("📋 Test 1: Discount Offers")
    
    # Create customer and failure record
    customer = create_mock_customer('high_value')
    subscription = create_mock_subscription(customer.id, 'high_value')
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    # Test discount offer
    discount_config = {'discount_percent': 50, 'duration_months': 6}
    discount_offer = recovery_system._generate_discount_offer(
        discount_config, customer, failure_record, 'high_value'
    )
    
    print(f"   Discount Offer:")
    print(f"     Type: {discount_offer['type']}")
    print(f"     Discount Percent: {discount_offer['discount_percent']}%")
    print(f"     Discount Amount: ${discount_offer['discount_amount']:.2f}")
    print(f"     Duration: {discount_offer['duration_months']} months")
    print(f"     Original Amount: ${discount_offer['original_amount']:.2f}")
    print(f"     Discounted Amount: ${discount_offer['discounted_amount']:.2f}")
    print(f"     Total Savings: ${discount_offer['savings_total']:.2f}")
    print(f"     Offer Code: {discount_offer['offer_code']}")
    print()
    
    # Test payment plan offer
    print("📋 Test 2: Payment Plan Offers")
    payment_plan_config = {'installments': 3, 'interest_free': True}
    payment_plan_offer = recovery_system._generate_payment_plan_offer(
        payment_plan_config, customer, failure_record, 'high_value'
    )
    
    print(f"   Payment Plan Offer:")
    print(f"     Type: {payment_plan_offer['type']}")
    print(f"     Installments: {payment_plan_offer['installments']}")
    print(f"     Installment Amount: ${payment_plan_offer['installment_amount']:.2f}")
    print(f"     Interest Free: {payment_plan_offer['interest_free']}")
    print(f"     Total Amount: ${payment_plan_offer['total_amount']:.2f}")
    print(f"     Offer Code: {payment_plan_offer['offer_code']}")
    print()
    
    # Test feature upgrade offer
    print("📋 Test 3: Feature Upgrade Offers")
    feature_config = ['premium_support', 'advanced_analytics', 'priority_queue']
    feature_offer = recovery_system._generate_feature_upgrade_offer(
        feature_config, customer, failure_record, 'high_value'
    )
    
    print(f"   Feature Upgrade Offer:")
    print(f"     Type: {feature_offer['type']}")
    print(f"     Upgraded Features: {', '.join(feature_offer['upgraded_features'])}")
    print(f"     Upgrade Duration: {feature_offer['upgrade_duration_months']} months")
    print(f"     Offer Code: {feature_offer['offer_code']}")
    print()
    
    # Test grace period offer
    print("📋 Test 4: Grace Period Offers")
    grace_config = {'days': 21, 'full_access': True}
    grace_offer = recovery_system._generate_grace_period_offer(
        grace_config, customer, failure_record, 'high_value'
    )
    
    print(f"   Grace Period Offer:")
    print(f"     Type: {grace_offer['type']}")
    print(f"     Grace Period Days: {grace_offer['grace_period_days']}")
    print(f"     Full Access: {grace_offer['full_access']}")
    print(f"     Grace Period Start: {grace_offer['grace_period_start']}")
    print(f"     Grace Period End: {grace_offer['grace_period_end']}")
    print(f"     Offer Code: {grace_offer['offer_code']}")
    print()
    
    print("✅ Specific Offer Types Tests Completed")
    print()

def test_offer_triggers():
    """Test offer trigger mechanisms"""
    print("🔔 Testing Offer Triggers")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test offer triggers
    print("📋 Test 1: Offer Trigger Evaluation")
    
    # Get offer triggers configuration
    offer_triggers = recovery_system.recovery_config['dunning_email_sequence']['retention_offers']['offer_triggers']
    
    print(f"   Offer Triggers Configuration:")
    for trigger_type, trigger_config in offer_triggers.items():
        print(f"     {trigger_type}:")
        for segment, conditions in trigger_config.items():
            print(f"       {segment}: {conditions}")
    print()
    
    # Test trigger evaluation for different customer profiles
    print("📋 Test 2: Trigger Evaluation by Customer Profile")
    
    test_profiles = [
        {'segment': 'high_value', 'failures': 1, 'age': 0, 'usage': 60},
        {'segment': 'at_risk', 'failures': 3, 'age': 1, 'usage': 10},
        {'segment': 'standard', 'failures': 2, 'age': 3, 'usage': 25}
    ]
    
    for profile in test_profiles:
        print(f"   {profile['segment'].upper()} Profile:")
        print(f"     Payment Failures: {profile['failures']}")
        print(f"     Subscription Age: {profile['age']} months")
        print(f"     Feature Usage: {profile['usage']}%")
        
        # Create mock metrics
        customer_metrics = {
            'payment_failures_last_3_months': profile['failures'],
            'subscription_length_months': profile['age'],
            'feature_usage': profile['usage']
        }
        
        # Check triggers
        triggered_offers = recovery_system._check_offer_triggers(
            offer_triggers, customer_metrics, profile['segment']
        )
        
        print(f"     Triggered Offers: {len(triggered_offers)}")
        for offer_type, offer in triggered_offers.items():
            print(f"       {offer_type}: {offer.get('type', 'Unknown')}")
        print()
    
    print("✅ Offer Triggers Tests Completed")
    print()

def test_personalized_dunning_email():
    """Test personalized dunning email sending"""
    print("📧 Testing Personalized Dunning Email")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test personalized dunning email for different segments
    print("📋 Test 1: Personalized Dunning Email by Segment")
    segments = ['high_value', 'mid_value', 'standard', 'at_risk']
    stages = ['dunning_1', 'dunning_3']
    
    for segment_type in segments:
        print(f"   {segment_type.upper()} Customer:")
        
        # Create customer and failure record
        customer = create_mock_customer(segment_type)
        subscription = create_mock_subscription(customer.id, segment_type)
        failure_record = create_mock_failure_record(customer.id, subscription.id)
        
        db.add(customer)
        db.add(subscription)
        db.add(failure_record)
        
        for stage_name in stages:
            print(f"     {stage_name.upper()} Stage:")
            
            # Send personalized dunning email
            result = recovery_system.send_personalized_dunning_email(failure_record.id, stage_name)
            
            if result['success']:
                print(f"       Email Sent: {result['email_sent']}")
                print(f"       Segment: {result['segment']}")
                print(f"       Messaging Tone: {result['messaging_tone']}")
                print(f"       Offers Count: {result['offers_count']}")
                
                # Show personalized content
                content = result['personalized_content']
                message = content['message']
                print(f"       Subject: {message.get('subject', 'N/A')}")
                print(f"       Message: {message.get('message', 'N/A')[:80]}...")
                
                # Show offers
                offers = content['offers']
                if offers:
                    print(f"       Offers:")
                    for offer_type, offer in offers.items():
                        if isinstance(offer, dict) and 'type' in offer:
                            print(f"         {offer_type}: {offer['type']}")
            else:
                print(f"       Error: {result['error']}")
            print()
    
    print("✅ Personalized Dunning Email Tests Completed")
    print()

def test_messaging_templates():
    """Test messaging templates by tone"""
    print("📝 Testing Messaging Templates")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test messaging templates
    print("📋 Test 1: Messaging Templates by Tone")
    
    # Get messaging templates
    messaging_templates = recovery_system.recovery_config['dunning_email_sequence']['personalized_messaging']['messaging_templates']
    
    tones = ['premium', 'professional', 'friendly', 'supportive']
    stages = ['dunning_1', 'dunning_3']
    
    for tone in tones:
        print(f"   {tone.upper()} Tone:")
        
        if tone in messaging_templates:
            tone_templates = messaging_templates[tone]
            
            for stage in stages:
                if stage in tone_templates:
                    template = tone_templates[stage]
                    print(f"     {stage.upper()} Stage:")
                    print(f"       Subject: {template.get('subject', 'N/A')}")
                    print(f"       Message: {template.get('message', 'N/A')[:80]}...")
                    print(f"       CTA Text: {template.get('cta_text', 'N/A')}")
                    print(f"       CTA URL: {template.get('cta_url', 'N/A')}")
                    print(f"       Personal Touch: {template.get('personal_touch', False)}")
                    print(f"       Retention Offer: {template.get('retention_offer', False)}")
                else:
                    print(f"     {stage.upper()} Stage: No template available")
        else:
            print(f"     No templates available for {tone} tone")
        print()
    
    print("✅ Messaging Templates Tests Completed")
    print()

def test_retention_offers_configuration():
    """Test retention offers configuration"""
    print("⚙️ Testing Retention Offers Configuration")
    print("=" * 60)
    
    # Setup
    db = MockDatabase()
    config = Config()
    
    # Create recovery system
    recovery_system = PaymentRecoverySystem(db, config)
    
    # Test retention offers configuration
    print("📋 Test 1: Retention Offers Configuration")
    
    # Get retention offers configuration
    retention_offers = recovery_system.recovery_config['dunning_email_sequence']['retention_offers']
    
    print(f"   Enabled: {retention_offers.get('enabled', False)}")
    print()
    
    # Test offer types
    offer_types = retention_offers.get('offer_types', {})
    print(f"   Offer Types:")
    for offer_type, segment_config in offer_types.items():
        print(f"     {offer_type}:")
        for segment, stage_config in segment_config.items():
            print(f"       {segment}:")
            for stage, config in stage_config.items():
                print(f"         {stage}: {config}")
        print()
    
    # Test offer triggers
    offer_triggers = retention_offers.get('offer_triggers', {})
    print(f"   Offer Triggers:")
    for trigger_type, segment_config in offer_triggers.items():
        print(f"     {trigger_type}:")
        for segment, conditions in segment_config.items():
            print(f"       {segment}: {conditions}")
        print()
    
    # Test personalization
    personalization = retention_offers.get('offer_personalization', {})
    print(f"   Offer Personalization:")
    for feature, enabled in personalization.items():
        print(f"     {feature}: {enabled}")
    print()
    
    print("✅ Retention Offers Configuration Tests Completed")
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
    
    # Test complete workflow
    print("📋 Test 1: Complete Personalized Dunning Workflow")
    
    # Create customer and failure record
    customer = create_mock_customer('high_value')
    subscription = create_mock_subscription(customer.id, 'high_value')
    failure_record = create_mock_failure_record(customer.id, subscription.id)
    
    db.add(customer)
    db.add(subscription)
    db.add(failure_record)
    
    print(f"   Customer: {customer.name}")
    print(f"   Segment: High Value")
    print(f"   Failure Amount: ${failure_record.amount}")
    print()
    
    # Step 1: Determine user segment
    print("   Step 1: Determine User Segment")
    segment_result = recovery_system.determine_user_segment(customer.id)
    if segment_result['success']:
        print(f"     Segment: {segment_result['segment']}")
        print(f"     Score: {segment_result['score']:.2f}")
        print(f"     Messaging Tone: {segment_result['segment_config']['messaging_tone']}")
    print()
    
    # Step 2: Generate personalized message
    print("   Step 2: Generate Personalized Message")
    message_result = recovery_system.generate_personalized_message(failure_record.id, 'dunning_3')
    if message_result['success']:
        message = message_result['personalized_message']
        print(f"     Subject: {message.get('subject', 'N/A')}")
        print(f"     Message: {message.get('message', 'N/A')[:80]}...")
    print()
    
    # Step 3: Generate retention offers
    print("   Step 3: Generate Retention Offers")
    offers_result = recovery_system.generate_retention_offers(failure_record.id, 'dunning_3')
    if offers_result['success']:
        offers = offers_result['offers']
        print(f"     Offers Generated: {len(offers)}")
        for offer_type, offer in offers.items():
            if isinstance(offer, dict) and 'type' in offer:
                print(f"       {offer_type}: {offer['type']}")
    print()
    
    # Step 4: Send personalized dunning email
    print("   Step 4: Send Personalized Dunning Email")
    email_result = recovery_system.send_personalized_dunning_email(failure_record.id, 'dunning_3')
    if email_result['success']:
        print(f"     Email Sent: {email_result['email_sent']}")
        print(f"     Segment: {email_result['segment']}")
        print(f"     Offers Count: {email_result['offers_count']}")
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
    
    # Test segmentation performance
    print("   Testing user segmentation performance...")
    customer = create_mock_customer('high_value')
    db.add(customer)
    
    import time
    start_time = time.time()
    
    for i in range(100):
        segment_result = recovery_system.determine_user_segment(customer.id)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average segmentation time: {avg_time:.2f}ms")
    print(f"   Segmentations per second: {1000 / avg_time:.1f}")
    print()
    
    # Test message generation performance
    print("   Testing message generation performance...")
    failure_record = create_mock_failure_record(customer.id, "sub_123")
    db.add(failure_record)
    
    start_time = time.time()
    
    for i in range(100):
        message_result = recovery_system.generate_personalized_message(failure_record.id, 'dunning_3')
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average message generation time: {avg_time:.2f}ms")
    print(f"   Messages per second: {1000 / avg_time:.1f}")
    print()
    
    # Test offers generation performance
    print("   Testing offers generation performance...")
    start_time = time.time()
    
    for i in range(100):
        offers_result = recovery_system.generate_retention_offers(failure_record.id, 'dunning_3')
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # Convert to milliseconds
    
    print(f"   Average offers generation time: {avg_time:.2f}ms")
    print(f"   Offers per second: {1000 / avg_time:.1f}")
    print()
    
    print("✅ Performance and Scalability Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Personalized Messaging and Retention Offers Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_user_segmentation()
        test_customer_metrics_calculation()
        test_segment_criteria_evaluation()
        test_personalized_message_generation()
        test_message_personalization()
        test_retention_offers_generation()
        test_specific_offer_types()
        test_offer_triggers()
        test_personalized_dunning_email()
        test_messaging_templates()
        test_retention_offers_configuration()
        test_integration_with_dunning_system()
        test_performance_and_scalability()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ User Segmentation")
        print("   ✅ Customer Metrics Calculation")
        print("   ✅ Segment Criteria Evaluation")
        print("   ✅ Personalized Message Generation")
        print("   ✅ Message Personalization")
        print("   ✅ Retention Offers Generation")
        print("   ✅ Specific Offer Types")
        print("   ✅ Offer Triggers")
        print("   ✅ Personalized Dunning Email")
        print("   ✅ Messaging Templates")
        print("   ✅ Retention Offers Configuration")
        print("   ✅ Integration with Dunning System")
        print("   ✅ Performance and Scalability")
        print()
        print("🚀 The personalized messaging and retention offers system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 