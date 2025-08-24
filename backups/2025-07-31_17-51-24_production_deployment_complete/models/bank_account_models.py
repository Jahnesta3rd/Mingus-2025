"""
Bank Account Data Models for MINGUS

This module provides comprehensive data models for bank account management:
- BankAccount: Account details and institution information
- PlaidConnection: Connection status and token management
- TransactionSync: Sync history and last update tracking
- AccountBalance: Current balances and historical data
- BankingPreferences: User settings and notification preferences
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, JSON,
    Numeric, SmallInteger, BigInteger
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.plaid_models import PlaidConnection as BasePlaidConnection

logger = logging.getLogger(__name__)

class AccountType(Enum):
    """Bank account type enumeration"""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    MORTGAGE = "mortgage"
    BUSINESS = "business"
    MONEY_MARKET = "money_market"
    CERTIFICATE_OF_DEPOSIT = "certificate_of_deposit"
    PREPAID = "prepaid"
    OTHER = "other"

class AccountStatus(Enum):
    """Account status enumeration"""
    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    DISCONNECTED = "disconnected"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    ARCHIVED = "archived"
    CLOSED = "closed"

class SyncStatus(Enum):
    """Synchronization status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"

class BalanceType(Enum):
    """Balance type enumeration"""
    CURRENT = "current"
    AVAILABLE = "available"
    PENDING = "pending"
    OVERDRAFT = "overdraft"
    CREDIT_LIMIT = "credit_limit"
    PAYMENT_DUE = "payment_due"
    LAST_PAYMENT = "last_payment"

class NotificationFrequency(Enum):
    """Notification frequency enumeration"""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"

class BankAccount(Base):
    """Bank account model for storing account details and institution information"""
    
    __tablename__ = 'bank_accounts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    plaid_connection_id = Column(UUID(as_uuid=True), ForeignKey('plaid_connections.id'), nullable=False)
    
    # Account identification
    account_id = Column(String(255), nullable=False)  # Plaid account ID
    name = Column(String(255), nullable=False)
    mask = Column(String(10), nullable=True)
    
    # Account type and classification
    type = Column(String(50), nullable=False)
    subtype = Column(String(50), nullable=True)
    account_type = Column(String(50), nullable=False)  # Our classification
    
    # Account status
    status = Column(String(50), nullable=False, default=AccountStatus.ACTIVE.value)
    verification_status = Column(String(50), nullable=False, default='pending')
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Financial information
    current_balance = Column(Numeric(15, 2), nullable=True)
    available_balance = Column(Numeric(15, 2), nullable=True)
    credit_limit = Column(Numeric(15, 2), nullable=True)
    payment_due = Column(Numeric(15, 2), nullable=True)
    last_payment_amount = Column(Numeric(15, 2), nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    
    # Currency and limits
    iso_currency_code = Column(String(3), nullable=False, default='USD')
    unofficial_currency_code = Column(String(10), nullable=True)
    
    # Account details
    interest_rate = Column(Float, nullable=True)
    apr = Column(Float, nullable=True)
    minimum_balance = Column(Numeric(15, 2), nullable=True)
    monthly_fee = Column(Numeric(15, 2), nullable=True)
    
    # Account metadata
    account_number = Column(String(50), nullable=True)  # Masked for security
    routing_number = Column(String(20), nullable=True)  # Masked for security
    account_holder_name = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    last_sync_at = Column(DateTime, nullable=True)
    last_balance_update = Column(DateTime, nullable=True)
    
    # Additional data
    metadata = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)  # User-defined tags
    notes = Column(Text, nullable=True)  # User notes
    
    # Relationships
    plaid_connection = relationship("PlaidConnection", back_populates="bank_accounts")
    user = relationship("User", back_populates="bank_accounts")
    balances = relationship("AccountBalance", back_populates="bank_account", cascade="all, delete-orphan")
    transaction_syncs = relationship("TransactionSync", back_populates="bank_account", cascade="all, delete-orphan")
    preferences = relationship("BankingPreferences", back_populates="bank_account", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_bank_accounts_user_id', 'user_id'),
        Index('idx_bank_accounts_plaid_connection_id', 'plaid_connection_id'),
        Index('idx_bank_accounts_account_id', 'account_id'),
        Index('idx_bank_accounts_status', 'status'),
        Index('idx_bank_accounts_type', 'type'),
        Index('idx_bank_accounts_is_active', 'is_active'),
        Index('idx_bank_accounts_last_sync_at', 'last_sync_at'),
        UniqueConstraint('plaid_connection_id', 'account_id', name='uq_bank_account_connection'),
    )
    
    @validates('type')
    def validate_type(self, key, value):
        """Validate account type"""
        valid_types = ['depository', 'credit', 'loan', 'investment', 'other']
        if value not in valid_types:
            raise ValueError(f"Invalid account type: {value}")
        return value
    
    @validates('status')
    def validate_status(self, key, value):
        """Validate account status"""
        valid_statuses = [status.value for status in AccountStatus]
        if value not in valid_statuses:
            raise ValueError(f"Invalid account status: {value}")
        return value
    
    @validates('iso_currency_code')
    def validate_currency(self, key, value):
        """Validate currency code"""
        if value and len(value) != 3:
            raise ValueError("Currency code must be 3 characters")
        return value.upper() if value else 'USD'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'plaid_connection_id': str(self.plaid_connection_id),
            'account_id': self.account_id,
            'name': self.name,
            'mask': self.mask,
            'type': self.type,
            'subtype': self.subtype,
            'account_type': self.account_type,
            'status': self.status,
            'verification_status': self.verification_status,
            'is_active': self.is_active,
            'current_balance': float(self.current_balance) if self.current_balance else None,
            'available_balance': float(self.available_balance) if self.available_balance else None,
            'credit_limit': float(self.credit_limit) if self.credit_limit else None,
            'payment_due': float(self.payment_due) if self.payment_due else None,
            'iso_currency_code': self.iso_currency_code,
            'interest_rate': self.interest_rate,
            'apr': self.apr,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'metadata': self.metadata,
            'tags': self.tags,
            'notes': self.notes
        }
    
    def update_balance(self, balance_type: str, amount: Decimal, currency: str = None):
        """Update account balance"""
        if balance_type == 'current':
            self.current_balance = amount
        elif balance_type == 'available':
            self.available_balance = amount
        elif balance_type == 'credit_limit':
            self.credit_limit = amount
        
        if currency:
            self.iso_currency_code = currency
        
        self.last_balance_update = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_overdrawn(self) -> bool:
        """Check if account is overdrawn"""
        if self.current_balance is not None and self.current_balance < 0:
            return True
        return False
    
    def get_available_credit(self) -> Optional[Decimal]:
        """Get available credit for credit accounts"""
        if self.type == 'credit' and self.credit_limit and self.current_balance:
            return self.credit_limit + self.current_balance
        return None

class PlaidConnection(Base):
    """Enhanced Plaid connection model with additional functionality"""
    
    __tablename__ = 'plaid_connections'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Plaid identifiers
    access_token = Column(Text, nullable=False)  # Encrypted
    item_id = Column(String(255), nullable=False)
    institution_id = Column(String(255), nullable=False)
    
    # Connection information
    institution_name = Column(String(255), nullable=False)
    institution_logo = Column(String(500), nullable=True)
    institution_primary_color = Column(String(7), nullable=True)  # Hex color
    institution_url = Column(String(500), nullable=True)
    
    # Connection status
    is_active = Column(Boolean, nullable=False, default=True)
    requires_reauth = Column(Boolean, nullable=False, default=False)
    last_error = Column(String(255), nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    error_count = Column(Integer, nullable=False, default=0)
    
    # Maintenance and sync
    maintenance_until = Column(DateTime, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)
    sync_frequency = Column(String(50), nullable=False, default='daily')
    
    # Connection metadata
    link_token = Column(String(255), nullable=True)
    link_token_expires_at = Column(DateTime, nullable=True)
    reconnection_attempted_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Additional data
    metadata = Column(JSONB, nullable=True)
    settings = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="plaid_connections")
    bank_accounts = relationship("BankAccount", back_populates="plaid_connection", cascade="all, delete-orphan")
    transaction_syncs = relationship("TransactionSync", back_populates="plaid_connection", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_plaid_connections_user_id', 'user_id'),
        Index('idx_plaid_connections_item_id', 'item_id'),
        Index('idx_plaid_connections_institution_id', 'institution_id'),
        Index('idx_plaid_connections_is_active', 'is_active'),
        Index('idx_plaid_connections_last_sync_at', 'last_sync_at'),
        Index('idx_plaid_connections_requires_reauth', 'requires_reauth'),
        UniqueConstraint('item_id', name='uq_plaid_connection_item'),
    )
    
    @validates('sync_frequency')
    def validate_sync_frequency(self, key, value):
        """Validate sync frequency"""
        valid_frequencies = ['real_time', 'hourly', 'daily', 'weekly', 'manual']
        if value not in valid_frequencies:
            raise ValueError(f"Invalid sync frequency: {value}")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'item_id': self.item_id,
            'institution_id': self.institution_id,
            'institution_name': self.institution_name,
            'institution_logo': self.institution_logo,
            'institution_primary_color': self.institution_primary_color,
            'is_active': self.is_active,
            'requires_reauth': self.requires_reauth,
            'last_error': self.last_error,
            'last_error_at': self.last_error_at.isoformat() if self.last_error_at else None,
            'error_count': self.error_count,
            'maintenance_until': self.maintenance_until.isoformat() if self.maintenance_until else None,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'next_sync_at': self.next_sync_at.isoformat() if self.next_sync_at else None,
            'sync_frequency': self.sync_frequency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'settings': self.settings
        }
    
    def update_sync_status(self, success: bool, error_message: str = None):
        """Update sync status"""
        self.last_sync_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if success:
            self.last_error = None
            self.last_error_at = None
            self.error_count = 0
        else:
            self.last_error = error_message
            self.last_error_at = datetime.utcnow()
            self.error_count += 1
    
    def calculate_next_sync(self):
        """Calculate next sync time based on frequency"""
        if not self.last_sync_at:
            self.next_sync_at = datetime.utcnow()
            return
        
        if self.sync_frequency == 'real_time':
            self.next_sync_at = datetime.utcnow()
        elif self.sync_frequency == 'hourly':
            self.next_sync_at = self.last_sync_at + timedelta(hours=1)
        elif self.sync_frequency == 'daily':
            self.next_sync_at = self.last_sync_at + timedelta(days=1)
        elif self.sync_frequency == 'weekly':
            self.next_sync_at = self.last_sync_at + timedelta(weeks=1)
        else:  # manual
            self.next_sync_at = None

class TransactionSync(Base):
    """Transaction synchronization model for tracking sync history and last updates"""
    
    __tablename__ = 'transaction_syncs'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey('bank_accounts.id'), nullable=False)
    plaid_connection_id = Column(UUID(as_uuid=True), ForeignKey('plaid_connections.id'), nullable=False)
    
    # Sync information
    sync_type = Column(String(50), nullable=False)  # initial, incremental, full, manual
    status = Column(String(50), nullable=False, default=SyncStatus.PENDING.value)
    
    # Timing information
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Sync results
    records_processed = Column(Integer, nullable=False, default=0)
    records_failed = Column(Integer, nullable=False, default=0)
    records_added = Column(Integer, nullable=False, default=0)
    records_updated = Column(Integer, nullable=False, default=0)
    records_deleted = Column(Integer, nullable=False, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    retry_after = Column(DateTime, nullable=True)
    
    # Sync context
    context = Column(JSONB, nullable=True)  # Additional sync context
    metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bank_account = relationship("BankAccount", back_populates="transaction_syncs")
    plaid_connection = relationship("PlaidConnection", back_populates="transaction_syncs")
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_syncs_bank_account_id', 'bank_account_id'),
        Index('idx_transaction_syncs_plaid_connection_id', 'plaid_connection_id'),
        Index('idx_transaction_syncs_status', 'status'),
        Index('idx_transaction_syncs_started_at', 'started_at'),
        Index('idx_transaction_syncs_completed_at', 'completed_at'),
        Index('idx_transaction_syncs_sync_type', 'sync_type'),
    )
    
    @validates('status')
    def validate_status(self, key, value):
        """Validate sync status"""
        valid_statuses = [status.value for status in SyncStatus]
        if value not in valid_statuses:
            raise ValueError(f"Invalid sync status: {value}")
        return value
    
    @validates('sync_type')
    def validate_sync_type(self, key, value):
        """Validate sync type"""
        valid_types = ['initial', 'incremental', 'full', 'manual', 'scheduled']
        if value not in valid_types:
            raise ValueError(f"Invalid sync type: {value}")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'bank_account_id': str(self.bank_account_id),
            'plaid_connection_id': str(self.plaid_connection_id),
            'sync_type': self.sync_type,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'records_processed': self.records_processed,
            'records_failed': self.records_failed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'records_deleted': self.records_deleted,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'retry_count': self.retry_count,
            'retry_after': self.retry_after.isoformat() if self.retry_after else None,
            'context': self.context,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def mark_completed(self, success: bool, duration: float = None, error_message: str = None):
        """Mark sync as completed"""
        self.completed_at = datetime.utcnow()
        self.duration = duration
        self.updated_at = datetime.utcnow()
        
        if success:
            self.status = SyncStatus.SUCCESS.value
            self.error_message = None
            self.error_code = None
        else:
            self.status = SyncStatus.FAILED.value
            self.error_message = error_message
    
    def increment_retry(self, retry_after: datetime = None):
        """Increment retry count"""
        self.retry_count += 1
        self.retry_after = retry_after
        self.updated_at = datetime.utcnow()

class AccountBalance(Base):
    """Account balance model for storing current balances and historical data"""
    
    __tablename__ = 'account_balances'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey('bank_accounts.id'), nullable=False)
    
    # Balance information
    balance_type = Column(String(50), nullable=False)  # current, available, pending, etc.
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # Balance metadata
    as_of_date = Column(DateTime, nullable=False, server_default=func.now())
    is_current = Column(Boolean, nullable=False, default=True)
    source = Column(String(50), nullable=False, default='plaid')  # plaid, manual, calculated
    
    # Historical tracking
    previous_amount = Column(Numeric(15, 2), nullable=True)
    change_amount = Column(Numeric(15, 2), nullable=True)
    change_percentage = Column(Float, nullable=True)
    
    # Additional data
    metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bank_account = relationship("BankAccount", back_populates="balances")
    
    # Indexes
    __table_args__ = (
        Index('idx_account_balances_bank_account_id', 'bank_account_id'),
        Index('idx_account_balances_balance_type', 'balance_type'),
        Index('idx_account_balances_as_of_date', 'as_of_date'),
        Index('idx_account_balances_is_current', 'is_current'),
        Index('idx_account_balances_source', 'source'),
    )
    
    @validates('balance_type')
    def validate_balance_type(self, key, value):
        """Validate balance type"""
        valid_types = [balance_type.value for balance_type in BalanceType]
        if value not in valid_types:
            raise ValueError(f"Invalid balance type: {value}")
        return value
    
    @validates('currency')
    def validate_currency(self, key, value):
        """Validate currency code"""
        if value and len(value) != 3:
            raise ValueError("Currency code must be 3 characters")
        return value.upper() if value else 'USD'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'bank_account_id': str(self.bank_account_id),
            'balance_type': self.balance_type,
            'amount': float(self.amount),
            'currency': self.currency,
            'as_of_date': self.as_of_date.isoformat(),
            'is_current': self.is_current,
            'source': self.source,
            'previous_amount': float(self.previous_amount) if self.previous_amount else None,
            'change_amount': float(self.change_amount) if self.change_amount else None,
            'change_percentage': self.change_percentage,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_change(self, previous_balance: 'AccountBalance'):
        """Calculate change from previous balance"""
        if previous_balance and previous_balance.amount:
            self.previous_amount = previous_balance.amount
            self.change_amount = self.amount - previous_balance.amount
            
            if previous_balance.amount != 0:
                self.change_percentage = (self.change_amount / previous_balance.amount) * 100
            else:
                self.change_percentage = 100.0 if self.amount > 0 else 0.0

class BankingPreferences(Base):
    """Banking preferences model for user settings and notification preferences"""
    
    __tablename__ = 'banking_preferences'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey('bank_accounts.id'), nullable=True)  # Null for global preferences
    
    # Sync preferences
    sync_frequency = Column(String(50), nullable=False, default='daily')
    auto_sync = Column(Boolean, nullable=False, default=True)
    sync_on_login = Column(Boolean, nullable=False, default=True)
    
    # Notification preferences
    balance_alerts = Column(Boolean, nullable=False, default=True)
    balance_threshold = Column(Numeric(15, 2), nullable=True)
    low_balance_alert = Column(Boolean, nullable=False, default=True)
    low_balance_threshold = Column(Numeric(15, 2), nullable=True)
    
    # Transaction notifications
    transaction_notifications = Column(Boolean, nullable=False, default=True)
    large_transaction_threshold = Column(Numeric(15, 2), nullable=True)
    unusual_activity_alerts = Column(Boolean, nullable=False, default=True)
    
    # Notification channels
    email_notifications = Column(Boolean, nullable=False, default=True)
    push_notifications = Column(Boolean, nullable=False, default=True)
    sms_notifications = Column(Boolean, nullable=False, default=False)
    in_app_notifications = Column(Boolean, nullable=False, default=True)
    
    # Notification frequency
    notification_frequency = Column(String(50), nullable=False, default=NotificationFrequency.DAILY.value)
    
    # Privacy and security
    share_analytics = Column(Boolean, nullable=False, default=True)
    share_aggregated_data = Column(Boolean, nullable=False, default=True)
    allow_marketing_emails = Column(Boolean, nullable=False, default=False)
    
    # Display preferences
    default_currency = Column(String(3), nullable=False, default='USD')
    date_format = Column(String(20), nullable=False, default='MM/DD/YYYY')
    time_format = Column(String(10), nullable=False, default='12h')
    show_balances = Column(Boolean, nullable=False, default=True)
    show_transaction_details = Column(Boolean, nullable=False, default=True)
    
    # Account-specific settings
    account_alias = Column(String(100), nullable=True)
    account_color = Column(String(7), nullable=True)  # Hex color
    account_icon = Column(String(50), nullable=True)
    hide_account = Column(Boolean, nullable=False, default=False)
    
    # Additional preferences
    metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="banking_preferences")
    bank_account = relationship("BankAccount", back_populates="preferences")
    
    # Indexes
    __table_args__ = (
        Index('idx_banking_preferences_user_id', 'user_id'),
        Index('idx_banking_preferences_bank_account_id', 'bank_account_id'),
        Index('idx_banking_preferences_sync_frequency', 'sync_frequency'),
        Index('idx_banking_preferences_notification_frequency', 'notification_frequency'),
        UniqueConstraint('user_id', 'bank_account_id', name='uq_banking_preferences_user_account'),
    )
    
    @validates('sync_frequency')
    def validate_sync_frequency(self, key, value):
        """Validate sync frequency"""
        valid_frequencies = ['real_time', 'hourly', 'daily', 'weekly', 'manual']
        if value not in valid_frequencies:
            raise ValueError(f"Invalid sync frequency: {value}")
        return value
    
    @validates('notification_frequency')
    def validate_notification_frequency(self, key, value):
        """Validate notification frequency"""
        valid_frequencies = [freq.value for freq in NotificationFrequency]
        if value not in valid_frequencies:
            raise ValueError(f"Invalid notification frequency: {value}")
        return value
    
    @validates('default_currency')
    def validate_currency(self, key, value):
        """Validate currency code"""
        if value and len(value) != 3:
            raise ValueError("Currency code must be 3 characters")
        return value.upper() if value else 'USD'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'bank_account_id': str(self.bank_account_id) if self.bank_account_id else None,
            'sync_frequency': self.sync_frequency,
            'auto_sync': self.auto_sync,
            'sync_on_login': self.sync_on_login,
            'balance_alerts': self.balance_alerts,
            'balance_threshold': float(self.balance_threshold) if self.balance_threshold else None,
            'low_balance_alert': self.low_balance_alert,
            'low_balance_threshold': float(self.low_balance_threshold) if self.low_balance_threshold else None,
            'transaction_notifications': self.transaction_notifications,
            'large_transaction_threshold': float(self.large_transaction_threshold) if self.large_transaction_threshold else None,
            'unusual_activity_alerts': self.unusual_activity_alerts,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'sms_notifications': self.sms_notifications,
            'in_app_notifications': self.in_app_notifications,
            'notification_frequency': self.notification_frequency,
            'share_analytics': self.share_analytics,
            'share_aggregated_data': self.share_aggregated_data,
            'allow_marketing_emails': self.allow_marketing_emails,
            'default_currency': self.default_currency,
            'date_format': self.date_format,
            'time_format': self.time_format,
            'show_balances': self.show_balances,
            'show_transaction_details': self.show_transaction_details,
            'account_alias': self.account_alias,
            'account_color': self.account_color,
            'account_icon': self.account_icon,
            'hide_account': self.hide_account,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def should_notify_balance_change(self, new_balance: Decimal, old_balance: Decimal = None) -> bool:
        """Check if balance change should trigger notification"""
        if not self.balance_alerts:
            return False
        
        if self.balance_threshold and abs(new_balance) >= self.balance_threshold:
            return True
        
        if self.low_balance_alert and self.low_balance_threshold and new_balance <= self.low_balance_threshold:
            return True
        
        if old_balance and self.large_transaction_threshold:
            change = abs(new_balance - old_balance)
            if change >= self.large_transaction_threshold:
                return True
        
        return False
    
    def get_notification_channels(self) -> List[str]:
        """Get enabled notification channels"""
        channels = []
        if self.email_notifications:
            channels.append('email')
        if self.push_notifications:
            channels.append('push')
        if self.sms_notifications:
            channels.append('sms')
        if self.in_app_notifications:
            channels.append('in_app')
        return channels 