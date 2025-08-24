"""
MINGUS Application - Subscription Models Tests
============================================

Tests for the comprehensive subscription data models and service.

Author: MINGUS Development Team
Date: January 2025
"""

import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.models.subscription_models import (
    MINGUSSubscription, MINGUSInvoice, MINGUSPaymentMethod, MINGUSUsageRecord,
    MINGUSSubscriptionTier, MINGUSBillingEvent, BillingCycle, SubscriptionStatus,
    PaymentStatus, UsageType
)
from backend.payment.stripe_integration import SubscriptionTier
from backend.services.subscription_service import SubscriptionService


class TestSubscriptionModels:
    """Test cases for subscription models."""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        engine = create_engine('sqlite:///:memory:')
        from backend.models.base import Base
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid.uuid4()
    
    @pytest.fixture
    def sample_subscription_tier(self):
        """Sample subscription tier for testing."""
        return MINGUSSubscriptionTier(
            id=uuid.uuid4(),
            tier=SubscriptionTier.BUDGET,
            name="Budget Tier",
            description="Test budget tier",
            monthly_price=Decimal('15.00'),
            yearly_price=Decimal('144.00'),
            currency='usd',
            features={
                'basic_analytics': True,
                'goal_setting': True,
                'email_support': True
            },
            limits={
                'analytics_reports': 5,
                'goals': 3,
                'support_requests': 3
            },
            is_active=True,
            sort_order=1
        )
    
    @pytest.fixture
    def sample_subscription(self, sample_user_id):
        """Sample subscription for testing."""
        return MINGUSSubscription(
            id=uuid.uuid4(),
            user_id=sample_user_id,
            stripe_subscription_id='sub_test123',
            stripe_customer_id='cus_test123',
            stripe_price_id='price_test123',
            tier=SubscriptionTier.BUDGET,
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            amount=Decimal('15.00'),
            currency='usd',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            usage_limits={
                'analytics_reports': 5,
                'goals': 3,
                'support_requests': 3
            },
            current_usage={
                'analytics_reports': 2,
                'goals': 1,
                'support_requests': 0
            }
        )
    
    def test_subscription_tier_creation(self, db_session, sample_subscription_tier):
        """Test subscription tier creation."""
        db_session.add(sample_subscription_tier)
        db_session.commit()
        
        # Retrieve from database
        tier = db_session.query(MINGUSSubscriptionTier).filter_by(
            id=sample_subscription_tier.id
        ).first()
        
        assert tier is not None
        assert tier.tier == SubscriptionTier.BUDGET
        assert tier.name == "Budget Tier"
        assert tier.monthly_price == Decimal('15.00')
        assert tier.yearly_price == Decimal('144.00')
        assert tier.is_active is True
    
    def test_subscription_tier_price_validation(self, db_session):
        """Test subscription tier price validation."""
        # Test negative price
        with pytest.raises(ValueError):
            tier = MINGUSSubscriptionTier(
                tier=SubscriptionTier.BUDGET,
                name="Test Tier",
                monthly_price=Decimal('-10.00'),
                yearly_price=Decimal('100.00')
            )
            db_session.add(tier)
            db_session.commit()
    
    def test_subscription_tier_get_price(self, sample_subscription_tier):
        """Test getting price for different billing cycles."""
        monthly_price = sample_subscription_tier.get_price(BillingCycle.MONTHLY)
        yearly_price = sample_subscription_tier.get_price(BillingCycle.YEARLY)
        
        assert monthly_price == 15.0
        assert yearly_price == 144.0
    
    def test_subscription_tier_yearly_discount(self, sample_subscription_tier):
        """Test yearly discount calculation."""
        discount = sample_subscription_tier.get_yearly_discount_percentage()
        
        # Monthly cost: 15 * 12 = 180
        # Yearly cost: 144
        # Discount: (180 - 144) / 180 * 100 = 20%
        assert discount == 20.0
    
    def test_subscription_creation(self, db_session, sample_subscription):
        """Test subscription creation."""
        db_session.add(sample_subscription)
        db_session.commit()
        
        # Retrieve from database
        subscription = db_session.query(MINGUSSubscription).filter_by(
            id=sample_subscription.id
        ).first()
        
        assert subscription is not None
        assert subscription.user_id == sample_subscription.user_id
        assert subscription.stripe_subscription_id == 'sub_test123'
        assert subscription.tier == SubscriptionTier.BUDGET
        assert subscription.status == SubscriptionStatus.ACTIVE
    
    def test_subscription_amount_validation(self, db_session, sample_user_id):
        """Test subscription amount validation."""
        # Test negative amount
        with pytest.raises(ValueError):
            subscription = MINGUSSubscription(
                user_id=sample_user_id,
                stripe_subscription_id='sub_test123',
                stripe_customer_id='cus_test123',
                stripe_price_id='price_test123',
                tier=SubscriptionTier.BUDGET,
                billing_cycle=BillingCycle.MONTHLY,
                amount=Decimal('-10.00'),
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            db_session.add(subscription)
            db_session.commit()
    
    def test_subscription_is_active(self, sample_subscription):
        """Test subscription active status."""
        # Active subscription
        assert sample_subscription.is_active() is True
        
        # Canceled subscription
        sample_subscription.status = SubscriptionStatus.CANCELED
        assert sample_subscription.is_active() is False
    
    def test_subscription_is_trial(self, sample_subscription):
        """Test subscription trial status."""
        # No trial
        assert sample_subscription.is_trial() is False
        
        # With trial
        sample_subscription.trial_end = datetime.utcnow() + timedelta(days=7)
        assert sample_subscription.is_trial() is True
        
        # Expired trial
        sample_subscription.trial_end = datetime.utcnow() - timedelta(days=1)
        assert sample_subscription.is_trial() is False
    
    def test_subscription_days_until_renewal(self, sample_subscription):
        """Test days until renewal calculation."""
        days = sample_subscription.days_until_renewal()
        assert days >= 0
        assert days <= 30
    
    def test_subscription_usage_percentage(self, sample_subscription):
        """Test usage percentage calculation."""
        # Analytics reports: 2 used out of 5 limit = 40%
        percentage = sample_subscription.get_usage_percentage(UsageType.ANALYTICS_REPORTS)
        assert percentage == 40.0
        
        # Support requests: 0 used out of 3 limit = 0%
        percentage = sample_subscription.get_usage_percentage(UsageType.SUPPORT_REQUESTS)
        assert percentage == 0.0
    
    def test_subscription_can_use_feature(self, sample_subscription):
        """Test feature usage allowance."""
        # Can use analytics (2 + 1 = 3 <= 5)
        assert sample_subscription.can_use_feature(UsageType.ANALYTICS_REPORTS, 1) is True
        
        # Cannot use analytics (2 + 4 = 6 > 5)
        assert sample_subscription.can_use_feature(UsageType.ANALYTICS_REPORTS, 4) is False
    
    def test_subscription_to_dict(self, sample_subscription):
        """Test subscription to dictionary conversion."""
        data = sample_subscription.to_dict()
        
        assert data['id'] == str(sample_subscription.id)
        assert data['user_id'] == str(sample_subscription.user_id)
        assert data['tier'] == 'budget'
        assert data['status'] == 'active'
        assert data['amount'] == 15.0
        assert data['is_active'] is True
        assert 'usage_limits' in data
        assert 'current_usage' in data
    
    def test_invoice_creation(self, db_session, sample_subscription):
        """Test invoice creation."""
        db_session.add(sample_subscription)
        db_session.commit()
        
        invoice = MINGUSInvoice(
            subscription_id=sample_subscription.id,
            stripe_invoice_id='in_test123',
            invoice_number='INV-001',
            status=PaymentStatus.PENDING,
            subtotal=Decimal('15.00'),
            tax=Decimal('0.00'),
            discount=Decimal('0.00'),
            total=Decimal('15.00'),
            amount_paid=Decimal('0.00'),
            amount_remaining=Decimal('15.00'),
            currency='usd',
            items=[]
        )
        
        db_session.add(invoice)
        db_session.commit()
        
        # Retrieve from database
        retrieved_invoice = db_session.query(MINGUSInvoice).filter_by(
            id=invoice.id
        ).first()
        
        assert retrieved_invoice is not None
        assert retrieved_invoice.stripe_invoice_id == 'in_test123'
        assert retrieved_invoice.status == PaymentStatus.PENDING
    
    def test_invoice_is_paid(self):
        """Test invoice paid status."""
        invoice = MINGUSInvoice(
            subscription_id=uuid.uuid4(),
            stripe_invoice_id='in_test123',
            invoice_number='INV-001',
            status=PaymentStatus.PENDING,
            subtotal=Decimal('15.00'),
            total=Decimal('15.00'),
            amount_paid=Decimal('0.00'),
            amount_remaining=Decimal('15.00'),
            currency='usd',
            items=[]
        )
        
        # Not paid
        assert invoice.is_paid() is False
        
        # Paid
        invoice.status = PaymentStatus.SUCCEEDED
        assert invoice.is_paid() is True
    
    def test_invoice_payment_percentage(self):
        """Test invoice payment percentage calculation."""
        invoice = MINGUSInvoice(
            subscription_id=uuid.uuid4(),
            stripe_invoice_id='in_test123',
            invoice_number='INV-001',
            status=PaymentStatus.PENDING,
            subtotal=Decimal('15.00'),
            total=Decimal('15.00'),
            amount_paid=Decimal('7.50'),
            amount_remaining=Decimal('7.50'),
            currency='usd',
            items=[]
        )
        
        percentage = invoice.get_payment_percentage()
        assert percentage == 50.0
    
    def test_payment_method_creation(self, db_session, sample_subscription):
        """Test payment method creation."""
        db_session.add(sample_subscription)
        db_session.commit()
        
        payment_method = MINGUSPaymentMethod(
            subscription_id=sample_subscription.id,
            stripe_payment_method_id='pm_test123',
            type='card',
            brand='visa',
            last4='4242',
            exp_month=12,
            exp_year=2025,
            country='US',
            is_default=True,
            is_active=True
        )
        
        db_session.add(payment_method)
        db_session.commit()
        
        # Retrieve from database
        retrieved_pm = db_session.query(MINGUSPaymentMethod).filter_by(
            id=payment_method.id
        ).first()
        
        assert retrieved_pm is not None
        assert retrieved_pm.stripe_payment_method_id == 'pm_test123'
        assert retrieved_pm.type == 'card'
        assert retrieved_pm.is_default is True
    
    def test_payment_method_is_expired(self):
        """Test payment method expiration."""
        # Not expired
        payment_method = MINGUSPaymentMethod(
            subscription_id=uuid.uuid4(),
            stripe_payment_method_id='pm_test123',
            type='card',
            exp_month=12,
            exp_year=datetime.utcnow().year + 1,
            is_default=True,
            is_active=True
        )
        assert payment_method.is_expired() is False
        
        # Expired
        payment_method.exp_year = datetime.utcnow().year - 1
        assert payment_method.is_expired() is True
    
    def test_payment_method_display_name(self):
        """Test payment method display name."""
        payment_method = MINGUSPaymentMethod(
            subscription_id=uuid.uuid4(),
            stripe_payment_method_id='pm_test123',
            type='card',
            brand='visa',
            last4='4242',
            is_default=True,
            is_active=True
        )
        
        display_name = payment_method.get_display_name()
        assert display_name == "Visa •••• 4242"
    
    def test_usage_record_creation(self, db_session, sample_subscription):
        """Test usage record creation."""
        db_session.add(sample_subscription)
        db_session.commit()
        
        usage_record = MINGUSUsageRecord(
            subscription_id=sample_subscription.id,
            usage_type=UsageType.ANALYTICS_REPORTS,
            quantity=1,
            description='Generated analytics report',
            metadata={'report_type': 'monthly_summary'}
        )
        
        db_session.add(usage_record)
        db_session.commit()
        
        # Retrieve from database
        retrieved_record = db_session.query(MINGUSUsageRecord).filter_by(
            id=usage_record.id
        ).first()
        
        assert retrieved_record is not None
        assert retrieved_record.usage_type == UsageType.ANALYTICS_REPORTS
        assert retrieved_record.quantity == 1
        assert retrieved_record.description == 'Generated analytics report'
    
    def test_usage_record_quantity_validation(self, db_session, sample_subscription):
        """Test usage record quantity validation."""
        db_session.add(sample_subscription)
        db_session.commit()
        
        # Test negative quantity
        with pytest.raises(ValueError):
            usage_record = MINGUSUsageRecord(
                subscription_id=sample_subscription.id,
                usage_type=UsageType.ANALYTICS_REPORTS,
                quantity=-1
            )
            db_session.add(usage_record)
            db_session.commit()
    
    def test_billing_event_creation(self, db_session, sample_subscription):
        """Test billing event creation."""
        db_session.add(sample_subscription)
        db_session.commit()
        
        billing_event = MINGUSBillingEvent(
            subscription_id=sample_subscription.id,
            user_id=sample_subscription.user_id,
            event_type='subscription.created',
            event_source='stripe',
            event_data={
                'stripe_subscription_id': 'sub_test123',
                'amount': 15.00
            },
            stripe_event_id='evt_test123'
        )
        
        db_session.add(billing_event)
        db_session.commit()
        
        # Retrieve from database
        retrieved_event = db_session.query(MINGUSBillingEvent).filter_by(
            id=billing_event.id
        ).first()
        
        assert retrieved_event is not None
        assert retrieved_event.event_type == 'subscription.created'
        assert retrieved_event.event_source == 'stripe'
        assert retrieved_event.stripe_event_id == 'evt_test123'


class TestSubscriptionService:
    """Test cases for subscription service."""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        engine = create_engine('sqlite:///:memory:')
        from backend.models.base import Base
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def mock_stripe_service(self):
        """Mock Stripe service."""
        return Mock()
    
    @pytest.fixture
    def subscription_service(self, db_session, mock_stripe_service):
        """Create subscription service instance."""
        return SubscriptionService(db_session, mock_stripe_service)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid.uuid4()
    
    def test_get_all_tiers(self, subscription_service, db_session):
        """Test getting all active tiers."""
        # Create test tiers
        tier1 = MINGUSSubscriptionTier(
            tier=SubscriptionTier.BUDGET,
            name="Budget Tier",
            monthly_price=Decimal('15.00'),
            yearly_price=Decimal('144.00'),
            is_active=True,
            sort_order=1
        )
        
        tier2 = MINGUSSubscriptionTier(
            tier=SubscriptionTier.MID_TIER,
            name="Mid Tier",
            monthly_price=Decimal('35.00'),
            yearly_price=Decimal('336.00'),
            is_active=True,
            sort_order=2
        )
        
        tier3 = MINGUSSubscriptionTier(
            tier=SubscriptionTier.PROFESSIONAL,
            name="Professional Tier",
            monthly_price=Decimal('75.00'),
            yearly_price=Decimal('720.00'),
            is_active=False,  # Inactive
            sort_order=3
        )
        
        db_session.add_all([tier1, tier2, tier3])
        db_session.commit()
        
        # Get active tiers
        active_tiers = subscription_service.get_all_tiers()
        
        assert len(active_tiers) == 2
        assert active_tiers[0].tier == SubscriptionTier.BUDGET
        assert active_tiers[1].tier == SubscriptionTier.MID_TIER
    
    def test_get_tier_by_id(self, subscription_service, db_session):
        """Test getting tier by ID."""
        tier = MINGUSSubscriptionTier(
            tier=SubscriptionTier.BUDGET,
            name="Budget Tier",
            monthly_price=Decimal('15.00'),
            yearly_price=Decimal('144.00'),
            is_active=True
        )
        
        db_session.add(tier)
        db_session.commit()
        
        retrieved_tier = subscription_service.get_tier_by_id(tier.id)
        assert retrieved_tier is not None
        assert retrieved_tier.tier == SubscriptionTier.BUDGET
    
    def test_get_tier_by_stripe_price_id(self, subscription_service, db_session):
        """Test getting tier by Stripe price ID."""
        tier = MINGUSSubscriptionTier(
            tier=SubscriptionTier.BUDGET,
            name="Budget Tier",
            monthly_price=Decimal('15.00'),
            yearly_price=Decimal('144.00'),
            stripe_monthly_price_id='price_monthly_123',
            stripe_yearly_price_id='price_yearly_123',
            is_active=True
        )
        
        db_session.add(tier)
        db_session.commit()
        
        # Test monthly price ID
        retrieved_tier = subscription_service.get_tier_by_stripe_price_id('price_monthly_123')
        assert retrieved_tier is not None
        assert retrieved_tier.tier == SubscriptionTier.BUDGET
        
        # Test yearly price ID
        retrieved_tier = subscription_service.get_tier_by_stripe_price_id('price_yearly_123')
        assert retrieved_tier is not None
        assert retrieved_tier.tier == SubscriptionTier.BUDGET
    
    def test_create_subscription_from_stripe(self, subscription_service, db_session, sample_user_id):
        """Test creating subscription from Stripe."""
        # Mock Stripe subscription
        mock_stripe_subscription = Mock()
        mock_stripe_subscription.id = 'sub_test123'
        mock_stripe_subscription.customer_id = 'cus_test123'
        mock_stripe_subscription.price_id = 'price_test123'
        mock_stripe_subscription.status = 'active'
        mock_stripe_subscription.amount = Decimal('15.00')
        mock_stripe_subscription.currency = 'usd'
        mock_stripe_subscription.current_period_start = datetime.utcnow()
        mock_stripe_subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
        mock_stripe_subscription.trial_start = None
        mock_stripe_subscription.trial_end = None
        mock_stripe_subscription.metadata = {}
        
        # Mock tier configuration
        mock_tier_config = Mock()
        mock_tier_config.limits = {
            'analytics_reports': 5,
            'goals': 3,
            'support_requests': 3
        }
        subscription_service.stripe_service.get_subscription_tier_info.return_value = mock_tier_config
        
        # Create subscription
        subscription = subscription_service.create_subscription_from_stripe(
            sample_user_id,
            mock_stripe_subscription,
            SubscriptionTier.BUDGET,
            BillingCycle.MONTHLY
        )
        
        assert subscription is not None
        assert subscription.user_id == sample_user_id
        assert subscription.stripe_subscription_id == 'sub_test123'
        assert subscription.tier == SubscriptionTier.BUDGET
        assert subscription.status == SubscriptionStatus.ACTIVE
    
    def test_get_user_subscriptions(self, subscription_service, db_session, sample_user_id):
        """Test getting user subscriptions."""
        # Create test subscriptions
        sub1 = MINGUSSubscription(
            user_id=sample_user_id,
            stripe_subscription_id='sub_test1',
            stripe_customer_id='cus_test1',
            stripe_price_id='price_test1',
            tier=SubscriptionTier.BUDGET,
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            amount=Decimal('15.00'),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        sub2 = MINGUSSubscription(
            user_id=sample_user_id,
            stripe_subscription_id='sub_test2',
            stripe_customer_id='cus_test2',
            stripe_price_id='price_test2',
            tier=SubscriptionTier.MID_TIER,
            billing_cycle=BillingCycle.YEARLY,
            status=SubscriptionStatus.CANCELED,
            amount=Decimal('35.00'),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=365)
        )
        
        db_session.add_all([sub1, sub2])
        db_session.commit()
        
        # Get user subscriptions
        subscriptions = subscription_service.get_user_subscriptions(sample_user_id)
        
        assert len(subscriptions) == 2
        assert subscriptions[0].stripe_subscription_id == 'sub_test2'  # Most recent first
        assert subscriptions[1].stripe_subscription_id == 'sub_test1'
    
    def test_get_active_subscription(self, subscription_service, db_session, sample_user_id):
        """Test getting active subscription."""
        # Create test subscriptions
        active_sub = MINGUSSubscription(
            user_id=sample_user_id,
            stripe_subscription_id='sub_active',
            stripe_customer_id='cus_test',
            stripe_price_id='price_test',
            tier=SubscriptionTier.BUDGET,
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            amount=Decimal('15.00'),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        canceled_sub = MINGUSSubscription(
            user_id=sample_user_id,
            stripe_subscription_id='sub_canceled',
            stripe_customer_id='cus_test',
            stripe_price_id='price_test',
            tier=SubscriptionTier.BUDGET,
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.CANCELED,
            amount=Decimal('15.00'),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        db_session.add_all([active_sub, canceled_sub])
        db_session.commit()
        
        # Get active subscription
        active_subscription = subscription_service.get_active_subscription(sample_user_id)
        
        assert active_subscription is not None
        assert active_subscription.stripe_subscription_id == 'sub_active'
        assert active_subscription.status == SubscriptionStatus.ACTIVE
    
    def test_track_usage(self, subscription_service, db_session, sample_user_id):
        """Test usage tracking."""
        # Create subscription with usage limits
        subscription = MINGUSSubscription(
            user_id=sample_user_id,
            stripe_subscription_id='sub_test',
            stripe_customer_id='cus_test',
            stripe_price_id='price_test',
            tier=SubscriptionTier.BUDGET,
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            amount=Decimal('15.00'),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            usage_limits={
                'analytics_reports': 5,
                'goals': 3,
                'support_requests': 3
            },
            current_usage={
                'analytics_reports': 2,
                'goals': 1,
                'support_requests': 0
            }
        )
        
        db_session.add(subscription)
        db_session.commit()
        
        # Track usage
        success = subscription_service.track_usage(
            subscription.id,
            UsageType.ANALYTICS_REPORTS,
            1,
            'Generated monthly report'
        )
        
        assert success is True
        
        # Check updated usage
        updated_subscription = db_session.query(MINGUSSubscription).filter_by(
            id=subscription.id
        ).first()
        
        assert updated_subscription.current_usage['analytics_reports'] == 3
        
        # Check usage record was created
        usage_records = db_session.query(MINGUSUsageRecord).filter_by(
            subscription_id=subscription.id
        ).all()
        
        assert len(usage_records) == 1
        assert usage_records[0].usage_type == UsageType.ANALYTICS_REPORTS
        assert usage_records[0].quantity == 1
    
    def test_track_usage_limit_exceeded(self, subscription_service, db_session, sample_user_id):
        """Test usage tracking when limit is exceeded."""
        # Create subscription with usage limits
        subscription = MINGUSSubscription(
            user_id=sample_user_id,
            stripe_subscription_id='sub_test',
            stripe_customer_id='cus_test',
            stripe_price_id='price_test',
            tier=SubscriptionTier.BUDGET,
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            amount=Decimal('15.00'),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            usage_limits={
                'analytics_reports': 5,
                'goals': 3,
                'support_requests': 3
            },
            current_usage={
                'analytics_reports': 5,  # Already at limit
                'goals': 1,
                'support_requests': 0
            }
        )
        
        db_session.add(subscription)
        db_session.commit()
        
        # Try to track usage beyond limit
        success = subscription_service.track_usage(
            subscription.id,
            UsageType.ANALYTICS_REPORTS,
            1,
            'Generated report'
        )
        
        assert success is False  # Should fail due to limit
    
    def test_get_usage_summary(self, subscription_service, db_session, sample_user_id):
        """Test getting usage summary."""
        # Create subscription
        subscription = MINGUSSubscription(
            user_id=sample_user_id,
            stripe_subscription_id='sub_test',
            stripe_customer_id='cus_test',
            stripe_price_id='price_test',
            tier=SubscriptionTier.BUDGET,
            billing_cycle=BillingCycle.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            amount=Decimal('15.00'),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            usage_limits={
                'analytics_reports': 5,
                'goals': 3,
                'support_requests': 3
            },
            current_usage={
                'analytics_reports': 2,
                'goals': 1,
                'support_requests': 0
            }
        )
        
        db_session.add(subscription)
        db_session.commit()
        
        # Create usage records
        usage_record1 = MINGUSUsageRecord(
            subscription_id=subscription.id,
            usage_type=UsageType.ANALYTICS_REPORTS,
            quantity=1,
            description='Report 1'
        )
        
        usage_record2 = MINGUSUsageRecord(
            subscription_id=subscription.id,
            usage_type=UsageType.ANALYTICS_REPORTS,
            quantity=1,
            description='Report 2'
        )
        
        usage_record3 = MINGUSUsageRecord(
            subscription_id=subscription.id,
            usage_type=UsageType.GOALS,
            quantity=1,
            description='Goal 1'
        )
        
        db_session.add_all([usage_record1, usage_record2, usage_record3])
        db_session.commit()
        
        # Get usage summary
        summary = subscription_service.get_usage_summary(subscription.id, days=30)
        
        assert summary['subscription_id'] == str(subscription.id)
        assert summary['period_days'] == 30
        assert summary['total_usage_records'] == 3
        
        # Check analytics reports usage
        analytics_usage = summary['usage_by_type']['analytics_reports']
        assert analytics_usage['total_quantity'] == 2
        assert analytics_usage['total_records'] == 2
        assert analytics_usage['limit'] == 5
        assert analytics_usage['current'] == 2
        assert analytics_usage['percentage'] == 40.0
        assert analytics_usage['can_use'] is True


if __name__ == '__main__':
    pytest.main([__file__]) 