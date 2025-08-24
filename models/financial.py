"""
MINGUS Application - Financial Models
=====================================

SQLAlchemy models for financial data and transactions.

Models:
- EncryptedFinancialProfile: Encrypted financial account information
- UserIncomeDueDate: Income tracking and due date management
- UserExpenseDueDate: Expense tracking and due date management
- FinancialTransaction: Complete transaction history
- IncomeProjection: Career income projection analysis

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from . import Base


class EncryptedFinancialProfile(Base):
    """Encrypted financial account information."""
    
    __tablename__ = 'encrypted_financial_profiles'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Profile information
    profile_name = Column(String(100), nullable=False)
    profile_type = Column(String(50), nullable=False)  # checking, savings, credit, investment
    
    # Institution information
    institution_name = Column(String(255))
    account_number_encrypted = Column(Text)  # encrypted with pgcrypto
    routing_number_encrypted = Column(Text)  # encrypted with pgcrypto
    
    # Account details
    account_balance = Column(Numeric(15, 2))
    credit_limit = Column(Numeric(15, 2))
    interest_rate = Column(Numeric(5, 4))
    
    # Sync information
    last_sync_at = Column(DateTime(timezone=True))
    sync_status = Column(String(50), default='pending')  # pending, success, failed
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Additional data
    metadata = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="financial_profiles")
    transactions = relationship("FinancialTransaction", back_populates="financial_profile", cascade="all, delete-orphan")
    
    # Validation
    @validates('profile_type')
    def validate_profile_type(self, key, profile_type):
        """Validate profile type."""
        valid_types = ['checking', 'savings', 'credit', 'investment', 'loan', 'mortgage']
        if profile_type not in valid_types:
            raise ValueError(f"Profile type must be one of: {valid_types}")
        return profile_type
    
    @validates('sync_status')
    def validate_sync_status(self, key, status):
        """Validate sync status."""
        valid_statuses = ['pending', 'success', 'failed', 'in_progress']
        if status not in valid_statuses:
            raise ValueError(f"Sync status must be one of: {valid_statuses}")
        return status
    
    @validates('interest_rate')
    def validate_interest_rate(self, key, rate):
        """Validate interest rate."""
        if rate is not None and (rate < 0 or rate > 1):
            raise ValueError("Interest rate must be between 0 and 1")
        return rate
    
    # Properties
    @property
    def is_credit_account(self):
        """Check if this is a credit account."""
        return self.profile_type in ['credit', 'loan', 'mortgage']
    
    @property
    def available_credit(self):
        """Calculate available credit for credit accounts."""
        if not self.is_credit_account or not self.credit_limit:
            return None
        if not self.account_balance:
            return self.credit_limit
        return max(0, self.credit_limit - self.account_balance)
    
    @property
    def credit_utilization(self):
        """Calculate credit utilization percentage."""
        if not self.is_credit_account or not self.credit_limit:
            return None
        if not self.account_balance:
            return 0
        return (self.account_balance / self.credit_limit) * 100
    
    @property
    def sync_age_days(self):
        """Calculate days since last sync."""
        if not self.last_sync_at:
            return None
        delta = datetime.now(timezone.utc) - self.last_sync_at
        return delta.days
    
    # Methods
    def update_balance(self, new_balance):
        """Update account balance."""
        self.account_balance = new_balance
        self.last_sync_at = datetime.now(timezone.utc)
        self.sync_status = 'success'
    
    def mark_sync_failed(self):
        """Mark sync as failed."""
        self.sync_status = 'failed'
    
    def to_dict(self):
        """Convert financial profile to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'profile_name': self.profile_name,
            'profile_type': self.profile_type,
            'institution_name': self.institution_name,
            'account_balance': float(self.account_balance) if self.account_balance else None,
            'credit_limit': float(self.credit_limit) if self.credit_limit else None,
            'interest_rate': float(self.interest_rate) if self.interest_rate else None,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'is_active': self.is_active,
            'metadata': self.metadata,
            'is_credit_account': self.is_credit_account,
            'available_credit': float(self.available_credit) if self.available_credit else None,
            'credit_utilization': float(self.credit_utilization) if self.credit_utilization else None,
            'sync_age_days': self.sync_age_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<EncryptedFinancialProfile(id={self.id}, user_id={self.user_id}, name='{self.profile_name}', type='{self.profile_type}')>"


class UserIncomeDueDate(Base):
    """Income tracking and due date management."""
    
    __tablename__ = 'user_income_due_dates'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Income information
    income_source = Column(String(100), nullable=False)
    expected_amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    frequency = Column(String(20), nullable=False)  # weekly, biweekly, monthly, quarterly, yearly
    
    # Status tracking
    is_recurring = Column(Boolean, default=True)
    last_received_date = Column(Date)
    last_received_amount = Column(Numeric(12, 2))
    status = Column(String(50), default='pending')  # pending, received, overdue
    
    # Additional information
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('expected_amount')
    def validate_expected_amount(self, key, amount):
        """Validate expected amount."""
        if amount <= 0:
            raise ValueError("Expected amount must be positive")
        return amount
    
    @validates('frequency')
    def validate_frequency(self, key, frequency):
        """Validate income frequency."""
        valid_frequencies = ['weekly', 'biweekly', 'monthly', 'quarterly', 'yearly']
        if frequency not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        return frequency
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status."""
        valid_statuses = ['pending', 'received', 'overdue', 'partial']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    # Properties
    @property
    def is_overdue(self):
        """Check if income is overdue."""
        if self.status == 'received':
            return False
        return date.today() > self.due_date
    
    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @property
    def days_until_due(self):
        """Calculate days until due."""
        if self.status == 'received':
            return None
        delta = self.due_date - date.today()
        return max(0, delta.days)
    
    @property
    def next_due_date(self):
        """Calculate next due date for recurring income."""
        if not self.is_recurring or not self.due_date:
            return None
        
        today = date.today()
        next_date = self.due_date
        
        while next_date <= today:
            if self.frequency == 'weekly':
                next_date = next_date.replace(day=next_date.day + 7)
            elif self.frequency == 'biweekly':
                next_date = next_date.replace(day=next_date.day + 14)
            elif self.frequency == 'monthly':
                next_date = next_date.replace(month=next_date.month + 1)
            elif self.frequency == 'quarterly':
                next_date = next_date.replace(month=next_date.month + 3)
            elif self.frequency == 'yearly':
                next_date = next_date.replace(year=next_date.year + 1)
        
        return next_date
    
    # Methods
    def mark_received(self, received_amount=None, received_date=None):
        """Mark income as received."""
        self.status = 'received'
        self.last_received_date = received_date or date.today()
        self.last_received_amount = received_amount or self.expected_amount
    
    def mark_partial(self, received_amount, received_date=None):
        """Mark income as partially received."""
        self.status = 'partial'
        self.last_received_date = received_date or date.today()
        self.last_received_amount = received_amount
    
    def to_dict(self):
        """Convert income due date to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'income_source': self.income_source,
            'expected_amount': float(self.expected_amount) if self.expected_amount else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'frequency': self.frequency,
            'is_recurring': self.is_recurring,
            'last_received_date': self.last_received_date.isoformat() if self.last_received_date else None,
            'last_received_amount': float(self.last_received_amount) if self.last_received_amount else None,
            'status': self.status,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'days_until_due': self.days_until_due,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<UserIncomeDueDate(id={self.id}, user_id={self.user_id}, source='{self.income_source}', amount={self.expected_amount})>"


class UserExpenseDueDate(Base):
    """Expense tracking and due date management."""
    
    __tablename__ = 'user_expense_due_dates'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Expense information
    expense_name = Column(String(255), nullable=False)
    expense_category = Column(String(100))
    expected_amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    frequency = Column(String(20), nullable=False)  # weekly, biweekly, monthly, quarterly, yearly
    
    # Status tracking
    is_recurring = Column(Boolean, default=True)
    is_essential = Column(Boolean, default=True)
    last_paid_date = Column(Date)
    last_paid_amount = Column(Numeric(12, 2))
    status = Column(String(50), default='pending')  # pending, paid, overdue
    
    # Payment settings
    auto_pay_enabled = Column(Boolean, default=False)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('expected_amount')
    def validate_expected_amount(self, key, amount):
        """Validate expected amount."""
        if amount <= 0:
            raise ValueError("Expected amount must be positive")
        return amount
    
    @validates('frequency')
    def validate_frequency(self, key, frequency):
        """Validate expense frequency."""
        valid_frequencies = ['weekly', 'biweekly', 'monthly', 'quarterly', 'yearly']
        if frequency not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        return frequency
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status."""
        valid_statuses = ['pending', 'paid', 'overdue', 'partial']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    # Properties
    @property
    def is_overdue(self):
        """Check if expense is overdue."""
        if self.status == 'paid':
            return False
        return date.today() > self.due_date
    
    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @property
    def days_until_due(self):
        """Calculate days until due."""
        if self.status == 'paid':
            return None
        delta = self.due_date - date.today()
        return max(0, delta.days)
    
    @property
    def next_due_date(self):
        """Calculate next due date for recurring expenses."""
        if not self.is_recurring or not self.due_date:
            return None
        
        today = date.today()
        next_date = self.due_date
        
        while next_date <= today:
            if self.frequency == 'weekly':
                next_date = next_date.replace(day=next_date.day + 7)
            elif self.frequency == 'biweekly':
                next_date = next_date.replace(day=next_date.day + 14)
            elif self.frequency == 'monthly':
                next_date = next_date.replace(month=next_date.month + 1)
            elif self.frequency == 'quarterly':
                next_date = next_date.replace(month=next_date.month + 3)
            elif self.frequency == 'yearly':
                next_date = next_date.replace(year=next_date.year + 1)
        
        return next_date
    
    # Methods
    def mark_paid(self, paid_amount=None, paid_date=None):
        """Mark expense as paid."""
        self.status = 'paid'
        self.last_paid_date = paid_date or date.today()
        self.last_paid_amount = paid_amount or self.expected_amount
    
    def mark_partial(self, paid_amount, paid_date=None):
        """Mark expense as partially paid."""
        self.status = 'partial'
        self.last_paid_date = paid_date or date.today()
        self.last_paid_amount = paid_amount
    
    def to_dict(self):
        """Convert expense due date to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'expense_name': self.expense_name,
            'expense_category': self.expense_category,
            'expected_amount': float(self.expected_amount) if self.expected_amount else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'frequency': self.frequency,
            'is_recurring': self.is_recurring,
            'is_essential': self.is_essential,
            'last_paid_date': self.last_paid_date.isoformat() if self.last_paid_date else None,
            'last_paid_amount': float(self.last_paid_amount) if self.last_paid_amount else None,
            'status': self.status,
            'auto_pay_enabled': self.auto_pay_enabled,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'days_until_due': self.days_until_due,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<UserExpenseDueDate(id={self.id}, user_id={self.user_id}, name='{self.expense_name}', amount={self.expected_amount})>"


class FinancialTransaction(Base):
    """Complete transaction history."""
    
    __tablename__ = 'financial_transactions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    financial_profile_id = Column(UUID(as_uuid=True), ForeignKey('encrypted_financial_profiles.id'))
    
    # Transaction information
    transaction_type = Column(String(50), nullable=False)  # income, expense, transfer
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    merchant_name = Column(String(255))
    
    # Dates
    transaction_date = Column(Date, nullable=False)
    posted_date = Column(Date)
    
    # Additional information
    reference_number = Column(String(255))
    status = Column(String(50), default='pending')  # pending, completed, failed, disputed
    metadata = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    financial_profile = relationship("EncryptedFinancialProfile", back_populates="transactions")
    
    # Validation
    @validates('amount')
    def validate_amount(self, key, amount):
        """Validate transaction amount."""
        if amount == 0:
            raise ValueError("Transaction amount cannot be zero")
        return amount
    
    @validates('transaction_type')
    def validate_transaction_type(self, key, transaction_type):
        """Validate transaction type."""
        valid_types = ['income', 'expense', 'transfer', 'refund', 'fee']
        if transaction_type not in valid_types:
            raise ValueError(f"Transaction type must be one of: {valid_types}")
        return transaction_type
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate transaction status."""
        valid_statuses = ['pending', 'completed', 'failed', 'disputed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    # Properties
    @property
    def is_income(self):
        """Check if transaction is income."""
        return self.transaction_type == 'income'
    
    @property
    def is_expense(self):
        """Check if transaction is expense."""
        return self.transaction_type == 'expense'
    
    @property
    def absolute_amount(self):
        """Get absolute amount value."""
        return abs(self.amount)
    
    @property
    def is_completed(self):
        """Check if transaction is completed."""
        return self.status == 'completed'
    
    # Methods
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'financial_profile_id': str(self.financial_profile_id) if self.financial_profile_id else None,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount) if self.amount else None,
            'description': self.description,
            'category': self.category,
            'merchant_name': self.merchant_name,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'reference_number': self.reference_number,
            'status': self.status,
            'metadata': self.metadata,
            'is_income': self.is_income,
            'is_expense': self.is_expense,
            'absolute_amount': float(self.absolute_amount) if self.absolute_amount else None,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<FinancialTransaction(id={self.id}, user_id={self.user_id}, type='{self.transaction_type}', amount={self.amount})>"


class IncomeProjection(Base):
    """Career income projection analysis."""
    
    __tablename__ = 'income_projections'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Projection information
    projection_date = Column(Date, nullable=False)
    current_income = Column(Numeric(12, 2), nullable=False)
    projected_income_1_year = Column(Numeric(12, 2))
    projected_income_3_years = Column(Numeric(12, 2))
    projected_income_5_years = Column(Numeric(12, 2))
    
    # Growth analysis
    growth_rate = Column(Numeric(5, 2))  # percentage
    factors = Column(JSONB)  # factors affecting projection
    confidence_level = Column(Numeric(3, 2))  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('current_income')
    def validate_current_income(self, key, income):
        """Validate current income."""
        if income <= 0:
            raise ValueError("Current income must be positive")
        return income
    
    @validates('growth_rate')
    def validate_growth_rate(self, key, rate):
        """Validate growth rate."""
        if rate is not None and (rate < -100 or rate > 1000):
            raise ValueError("Growth rate must be between -100% and 1000%")
        return rate
    
    @validates('confidence_level')
    def validate_confidence_level(self, key, level):
        """Validate confidence level."""
        if level is not None and (level < 0 or level > 1):
            raise ValueError("Confidence level must be between 0 and 1")
        return level
    
    # Properties
    @property
    def annual_growth_rate(self):
        """Calculate annual growth rate."""
        if not self.projected_income_1_year or not self.current_income:
            return None
        return ((self.projected_income_1_year - self.current_income) / self.current_income) * 100
    
    @property
    def projected_growth_3_years(self):
        """Calculate 3-year growth percentage."""
        if not self.projected_income_3_years or not self.current_income:
            return None
        return ((self.projected_income_3_years - self.current_income) / self.current_income) * 100
    
    @property
    def projected_growth_5_years(self):
        """Calculate 5-year growth percentage."""
        if not self.projected_income_5_years or not self.current_income:
            return None
        return ((self.projected_income_5_years - self.current_income) / self.current_income) * 100
    
    # Methods
    def to_dict(self):
        """Convert income projection to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'projection_date': self.projection_date.isoformat() if self.projection_date else None,
            'current_income': float(self.current_income) if self.current_income else None,
            'projected_income_1_year': float(self.projected_income_1_year) if self.projected_income_1_year else None,
            'projected_income_3_years': float(self.projected_income_3_years) if self.projected_income_3_years else None,
            'projected_income_5_years': float(self.projected_income_5_years) if self.projected_income_5_years else None,
            'growth_rate': float(self.growth_rate) if self.growth_rate else None,
            'factors': self.factors,
            'confidence_level': float(self.confidence_level) if self.confidence_level else None,
            'annual_growth_rate': float(self.annual_growth_rate) if self.annual_growth_rate else None,
            'projected_growth_3_years': float(self.projected_growth_3_years) if self.projected_growth_3_years else None,
            'projected_growth_5_years': float(self.projected_growth_5_years) if self.projected_growth_5_years else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<IncomeProjection(id={self.id}, user_id={self.user_id}, current_income={self.current_income}, growth_rate={self.growth_rate}%)>" 