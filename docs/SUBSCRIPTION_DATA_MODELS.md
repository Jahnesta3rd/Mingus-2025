# MINGUS Subscription Data Models Documentation

## Overview

This document details the comprehensive subscription data models for the MINGUS application, including SQLAlchemy models, database schema, relationships, and integration with Stripe for complete subscription management.

## 📊 **Database Schema**

### **Core Tables**

#### 1. **mingus_subscription_tiers**
Configuration table for subscription tiers and pricing.

```sql
CREATE TABLE mingus_subscription_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier subscription_tier NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Pricing
    monthly_price DECIMAL(10,2) NOT NULL CHECK (monthly_price >= 0),
    yearly_price DECIMAL(10,2) NOT NULL CHECK (yearly_price >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    
    -- Stripe integration
    stripe_monthly_price_id VARCHAR(255),
    stripe_yearly_price_id VARCHAR(255),
    
    -- Features and limits
    features JSONB NOT NULL DEFAULT '{}',
    limits JSONB NOT NULL DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_featured BOOLEAN NOT NULL DEFAULT false,
    sort_order INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### 2. **mingus_subscriptions**
Main subscription table integrating with Stripe subscriptions.

```sql
CREATE TABLE mingus_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User relationship
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Stripe integration
    stripe_subscription_id VARCHAR(255) NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(255) NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    
    -- Subscription details
    tier subscription_tier NOT NULL,
    billing_cycle billing_cycle NOT NULL,
    status subscription_status NOT NULL DEFAULT 'incomplete',
    
    -- Pricing information
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    discount_amount DECIMAL(10,2) CHECK (discount_amount >= 0),
    discount_percentage INTEGER CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
    
    -- Billing dates
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage limits and tracking
    usage_limits JSONB NOT NULL DEFAULT '{}',
    current_usage JSONB NOT NULL DEFAULT '{}',
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### 3. **mingus_invoices**
Invoice records integrating with Stripe invoices.

```sql
CREATE TABLE mingus_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    subscription_id UUID NOT NULL REFERENCES mingus_subscriptions(id) ON DELETE CASCADE,
    
    -- Stripe integration
    stripe_invoice_id VARCHAR(255) NOT NULL UNIQUE,
    stripe_payment_intent_id VARCHAR(255),
    
    -- Invoice details
    invoice_number VARCHAR(255) NOT NULL UNIQUE,
    status payment_status NOT NULL DEFAULT 'pending',
    
    -- Amounts
    subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0),
    tax DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (tax >= 0),
    discount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
    total DECIMAL(10,2) NOT NULL CHECK (total >= 0),
    amount_paid DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
    amount_remaining DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (amount_remaining >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    
    -- Billing dates
    due_date TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    
    -- Invoice items
    items JSONB NOT NULL DEFAULT '[]',
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### 4. **mingus_payment_methods**
Payment method records integrating with Stripe payment methods.

```sql
CREATE TABLE mingus_payment_methods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    subscription_id UUID NOT NULL REFERENCES mingus_subscriptions(id) ON DELETE CASCADE,
    
    -- Stripe integration
    stripe_payment_method_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- Payment method details
    type VARCHAR(50) NOT NULL,
    brand VARCHAR(50),
    last4 VARCHAR(4),
    exp_month INTEGER CHECK (exp_month >= 1 AND exp_month <= 12),
    exp_year INTEGER CHECK (exp_year >= 2000),
    country VARCHAR(2),
    
    -- Billing details
    billing_details JSONB,
    
    -- Status
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### 5. **mingus_usage_records**
Usage tracking for subscription features and limits.

```sql
CREATE TABLE mingus_usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    subscription_id UUID NOT NULL REFERENCES mingus_subscriptions(id) ON DELETE CASCADE,
    
    -- Usage details
    usage_type usage_type NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    description TEXT,
    
    -- Usage period
    usage_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### 6. **mingus_billing_events**
Audit log for all billing-related events.

```sql
CREATE TABLE mingus_billing_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationships
    subscription_id UUID REFERENCES mingus_subscriptions(id) ON DELETE SET NULL,
    invoice_id UUID REFERENCES mingus_invoices(id) ON DELETE SET NULL,
    
    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(50) NOT NULL DEFAULT 'stripe',
    
    -- Event data
    event_data JSONB NOT NULL DEFAULT '{}',
    previous_state JSONB,
    new_state JSONB,
    
    -- User context
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Stripe integration
    stripe_event_id VARCHAR(255),
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

## 🔗 **Database Relationships**

### **Entity Relationship Diagram**

```
users (1) ←→ (N) mingus_subscriptions
mingus_subscriptions (1) ←→ (N) mingus_invoices
mingus_subscriptions (1) ←→ (N) mingus_payment_methods
mingus_subscriptions (1) ←→ (N) mingus_usage_records
mingus_subscriptions (1) ←→ (N) mingus_billing_events
mingus_invoices (1) ←→ (N) mingus_billing_events
```

### **Key Relationships**

1. **User → Subscriptions**: One user can have multiple subscriptions (historical tracking)
2. **Subscription → Invoices**: One subscription can have multiple invoices
3. **Subscription → Payment Methods**: One subscription can have multiple payment methods
4. **Subscription → Usage Records**: One subscription can have multiple usage records
5. **Subscription → Billing Events**: One subscription can have multiple billing events

## 📋 **Data Types and Enums**

### **Billing Cycles**
```python
class BillingCycle(PyEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"
    DAILY = "daily"
```

### **Subscription Statuses**
```python
class SubscriptionStatus(PyEnum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIAL = "trial"
    EXPIRED = "expired"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"
```

### **Payment Statuses**
```python
class PaymentStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"
```

### **Usage Types**
```python
class UsageType(PyEnum):
    ANALYTICS_REPORTS = "analytics_reports"
    DATA_EXPORTS = "data_exports"
    SUPPORT_REQUESTS = "support_requests"
    AI_INSIGHTS = "ai_insights"
    API_REQUESTS = "api_requests"
    GOALS = "goals"
    INVESTMENT_ACCOUNTS = "investment_accounts"
    CUSTOM_CATEGORIES = "custom_categories"
    TEAM_MEMBERS = "team_members"
```

## 🏗️ **SQLAlchemy Models**

### **MINGUSSubscription Model**

```python
class MINGUSSubscription(Base):
    """MINGUS subscription model that integrates with Stripe."""
    
    __tablename__ = 'mingus_subscriptions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    user = relationship("User", back_populates="subscriptions")
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=False)
    
    # Subscription details
    tier = Column(Enum(SubscriptionTier), nullable=False)
    billing_cycle = Column(Enum(BillingCycle), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.INCOMPLETE)
    
    # Pricing information
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='usd')
    discount_amount = Column(Numeric(10, 2), nullable=True)
    discount_percentage = Column(Integer, nullable=True)
    
    # Billing dates
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage limits and tracking
    usage_limits = Column(JSON, nullable=False, default=dict)
    current_usage = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    invoices = relationship("MINGUSInvoice", back_populates="subscription", cascade="all, delete-orphan")
    usage_records = relationship("MINGUSUsageRecord", back_populates="subscription", cascade="all, delete-orphan")
    payment_methods = relationship("MINGUSPaymentMethod", back_populates="subscription", cascade="all, delete-orphan")
```

### **Key Methods**

```python
def is_active(self) -> bool:
    """Check if subscription is active."""
    return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]

def is_trial(self) -> bool:
    """Check if subscription is in trial period."""
    if not self.trial_end:
        return False
    return datetime.utcnow() < self.trial_end

def days_until_renewal(self) -> int:
    """Calculate days until next renewal."""
    if not self.current_period_end:
        return 0
    delta = self.current_period_end - datetime.utcnow()
    return max(0, delta.days)

def get_usage_percentage(self, usage_type: UsageType) -> float:
    """Get usage percentage for a specific type."""
    limit = self.usage_limits.get(usage_type.value, 0)
    current = self.current_usage.get(usage_type.value, 0)
    
    if limit == 0:
        return 0.0
    if limit == -1:  # Unlimited
        return 0.0
    
    return min(100.0, (current / limit) * 100)

def can_use_feature(self, usage_type: UsageType, amount: int = 1) -> bool:
    """Check if user can use a feature based on limits."""
    limit = self.usage_limits.get(usage_type.value, 0)
    current = self.current_usage.get(usage_type.value, 0)
    
    if limit == -1:  # Unlimited
        return True
    
    return current + amount <= limit
```

## 🔧 **Database Indexes**

### **Performance Indexes**

```sql
-- Subscription indexes
CREATE INDEX idx_subscriptions_user_id ON mingus_subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON mingus_subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_stripe_customer_id ON mingus_subscriptions(stripe_customer_id);
CREATE INDEX idx_subscriptions_user_status ON mingus_subscriptions(user_id, status);
CREATE INDEX idx_subscriptions_tier_billing ON mingus_subscriptions(tier, billing_cycle);
CREATE INDEX idx_subscriptions_period_end ON mingus_subscriptions(current_period_end);
CREATE INDEX idx_subscriptions_status ON mingus_subscriptions(status);
CREATE INDEX idx_subscriptions_trial_end ON mingus_subscriptions(trial_end);

-- Invoice indexes
CREATE INDEX idx_invoices_subscription_id ON mingus_invoices(subscription_id);
CREATE INDEX idx_invoices_stripe_invoice_id ON mingus_invoices(stripe_invoice_id);
CREATE INDEX idx_invoices_stripe_payment_intent_id ON mingus_invoices(stripe_payment_intent_id);
CREATE INDEX idx_invoices_subscription_status ON mingus_invoices(subscription_id, status);
CREATE INDEX idx_invoices_status ON mingus_invoices(status);
CREATE INDEX idx_invoices_due_date ON mingus_invoices(due_date);
CREATE INDEX idx_invoices_paid_at ON mingus_invoices(paid_at);

-- Payment method indexes
CREATE INDEX idx_payment_methods_subscription_id ON mingus_payment_methods(subscription_id);
CREATE INDEX idx_payment_methods_stripe_payment_method_id ON mingus_payment_methods(stripe_payment_method_id);
CREATE INDEX idx_payment_methods_subscription_default ON mingus_payment_methods(subscription_id, is_default);
CREATE INDEX idx_payment_methods_type ON mingus_payment_methods(type);
CREATE INDEX idx_payment_methods_active ON mingus_payment_methods(is_active);

-- Usage record indexes
CREATE INDEX idx_usage_records_subscription_id ON mingus_usage_records(subscription_id);
CREATE INDEX idx_usage_records_subscription_type ON mingus_usage_records(subscription_id, usage_type);
CREATE INDEX idx_usage_records_usage_date ON mingus_usage_records(usage_date);
CREATE INDEX idx_usage_records_type_date ON mingus_usage_records(usage_type, usage_date);
CREATE INDEX idx_usage_records_created_at ON mingus_usage_records(created_at);

-- Billing event indexes
CREATE INDEX idx_billing_events_subscription_id ON mingus_billing_events(subscription_id);
CREATE INDEX idx_billing_events_invoice_id ON mingus_billing_events(invoice_id);
CREATE INDEX idx_billing_events_user_id ON mingus_billing_events(user_id);
CREATE INDEX idx_billing_events_event_type ON mingus_billing_events(event_type);
CREATE INDEX idx_billing_events_event_timestamp ON mingus_billing_events(event_timestamp);
CREATE INDEX idx_billing_events_user_timestamp ON mingus_billing_events(user_id, event_timestamp);
CREATE INDEX idx_billing_events_stripe_event_id ON mingus_billing_events(stripe_event_id);
```

## 🚀 **Subscription Service**

### **Core Service Methods**

```python
class SubscriptionService:
    """Comprehensive subscription service for MINGUS."""
    
    def get_all_tiers(self) -> List[MINGUSSubscriptionTier]:
        """Get all active subscription tiers."""
    
    def get_active_subscription(self, user_id: UUID) -> Optional[MINGUSSubscription]:
        """Get active subscription for a user."""
    
    def create_subscription_from_stripe(
        self, 
        user_id: UUID, 
        stripe_subscription: Subscription,
        tier: SubscriptionTier,
        billing_cycle: BillingCycle
    ) -> Optional[MINGUSSubscription]:
        """Create MINGUS subscription from Stripe subscription."""
    
    def update_subscription_from_stripe(self, stripe_subscription: Subscription) -> bool:
        """Update MINGUS subscription from Stripe subscription."""
    
    def cancel_subscription(self, subscription_id: UUID, at_period_end: bool = True) -> bool:
        """Cancel subscription."""
    
    def track_usage(
        self, 
        subscription_id: UUID, 
        usage_type: UsageType, 
        quantity: int = 1,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track usage for a subscription feature."""
    
    def get_usage_summary(self, subscription_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for a subscription."""
```

### **Usage Tracking Example**

```python
# Track usage for analytics reports
success = subscription_service.track_usage(
    subscription_id=subscription.id,
    usage_type=UsageType.ANALYTICS_REPORTS,
    quantity=1,
    description='Generated monthly analytics report',
    metadata={'report_type': 'monthly_summary'}
)

if success:
    print("Usage tracked successfully")
else:
    print("Usage limit exceeded")
```

### **Usage Summary Example**

```python
# Get usage summary for last 30 days
summary = subscription_service.get_usage_summary(subscription.id, days=30)

print(f"Analytics Reports: {summary['usage_by_type']['analytics_reports']['current']}/{summary['usage_by_type']['analytics_reports']['limit']}")
print(f"Usage Percentage: {summary['usage_by_type']['analytics_reports']['percentage']}%")
print(f"Can Use Feature: {summary['usage_by_type']['analytics_reports']['can_use']}")
```

## 📊 **Database Views**

### **Active Subscriptions View**

```sql
CREATE VIEW active_subscriptions_view AS
SELECT 
    s.id,
    s.user_id,
    s.stripe_subscription_id,
    s.tier,
    s.billing_cycle,
    s.status,
    s.amount,
    s.currency,
    s.current_period_start,
    s.current_period_end,
    s.trial_end,
    s.usage_limits,
    s.current_usage,
    u.email as user_email,
    u.first_name,
    u.last_name,
    CASE 
        WHEN s.trial_end IS NOT NULL AND s.trial_end > NOW() THEN true
        ELSE false
    END as is_trial,
    CASE 
        WHEN s.current_period_end > NOW() THEN 
            EXTRACT(DAY FROM (s.current_period_end - NOW()))
        ELSE 0
    END as days_until_renewal
FROM mingus_subscriptions s
JOIN users u ON s.user_id = u.id
WHERE s.status IN ('active', 'trial');
```

### **Usage Analytics View**

```sql
CREATE VIEW subscription_usage_analytics AS
SELECT 
    s.id as subscription_id,
    s.user_id,
    s.tier,
    s.billing_cycle,
    s.usage_limits,
    s.current_usage,
    ur.usage_type,
    COUNT(ur.id) as total_usage_records,
    SUM(ur.quantity) as total_quantity,
    MAX(ur.usage_date) as last_usage_date
FROM mingus_subscriptions s
LEFT JOIN mingus_usage_records ur ON s.id = ur.subscription_id
GROUP BY s.id, s.user_id, s.tier, s.billing_cycle, s.usage_limits, s.current_usage, ur.usage_type;
```

## 🔄 **Database Triggers**

### **Updated At Trigger**

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_mingus_subscriptions_updated_at 
    BEFORE UPDATE ON mingus_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### **Single Default Payment Method Trigger**

```sql
CREATE OR REPLACE FUNCTION ensure_single_default_payment_method()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = true THEN
        -- Set all other payment methods for this subscription to not default
        UPDATE mingus_payment_methods 
        SET is_default = false 
        WHERE subscription_id = NEW.subscription_id 
        AND id != NEW.id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER ensure_single_default_payment_method_trigger
    BEFORE INSERT OR UPDATE ON mingus_payment_methods
    FOR EACH ROW EXECUTE FUNCTION ensure_single_default_payment_method();
```

## 🧪 **Testing**

### **Model Testing**

```python
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

def test_subscription_usage_tracking(self, subscription_service, db_session, sample_user_id):
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
```

## 📈 **Performance Considerations**

### **Query Optimization**

1. **Use Indexes**: All foreign keys and frequently queried columns are indexed
2. **Composite Indexes**: Multi-column indexes for common query patterns
3. **Partial Indexes**: Indexes on active records only where appropriate
4. **JSONB Indexes**: For efficient querying of JSON data in PostgreSQL

### **Data Archiving**

1. **Old Usage Records**: Archive usage records older than 2 years
2. **Billing Events**: Archive billing events older than 5 years
3. **Canceled Subscriptions**: Archive canceled subscriptions after 1 year

### **Caching Strategy**

1. **Subscription Data**: Cache active subscription data for 5 minutes
2. **Usage Limits**: Cache usage limits for 1 hour
3. **Tier Configuration**: Cache tier configuration for 24 hours

## 🔒 **Security Considerations**

### **Data Protection**

1. **Encryption**: Sensitive data encrypted at rest
2. **Access Control**: Row-level security for user data
3. **Audit Logging**: All billing events logged for compliance
4. **Data Masking**: Sensitive data masked in logs

### **Validation**

1. **Input Validation**: All model inputs validated
2. **Business Rules**: Usage limits enforced at database level
3. **Referential Integrity**: Foreign key constraints enforced
4. **Data Consistency**: Triggers ensure data consistency

## 🎯 **Best Practices**

### **Model Design**

1. **Single Responsibility**: Each model has a clear, single purpose
2. **Normalization**: Data normalized to prevent redundancy
3. **Extensibility**: Models designed for future feature additions
4. **Performance**: Optimized for common query patterns

### **Data Management**

1. **Consistency**: Use transactions for multi-table operations
2. **Validation**: Validate data at both application and database levels
3. **Auditing**: Track all changes for compliance and debugging
4. **Backup**: Regular backups of subscription data

### **Integration**

1. **Stripe Sync**: Keep local data in sync with Stripe
2. **Error Handling**: Graceful handling of Stripe API failures
3. **Retry Logic**: Implement retry logic for failed operations
4. **Monitoring**: Monitor subscription health and usage patterns

This comprehensive subscription data model provides a robust foundation for managing subscriptions, tracking usage, and integrating with Stripe while maintaining excellent performance and security standards. 