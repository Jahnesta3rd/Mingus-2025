"""
Plaid Database Models for MINGUS

This module defines the database models for Plaid integration:
- Plaid connections and access tokens
- Bank accounts and balances
- Transactions and categories
- Institution information
- Identity verification data
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from backend.models.base import Base

class PlaidConnection(Base):
    """Plaid connection model for storing access tokens and item information"""
    
    __tablename__ = 'plaid_connections'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Plaid identifiers
    item_id = Column(String(255), nullable=False, unique=True, index=True)
    access_token = Column(Text, nullable=False)  # Encrypted in production
    institution_id = Column(String(255), nullable=False, index=True)
    
    # Connection metadata
    institution_name = Column(String(255), nullable=False)
    products = Column(JSON, nullable=False, default=list)  # List of enabled products
    webhook_url = Column(String(500), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="plaid_connections")
    accounts = relationship("PlaidAccount", back_populates="connection", cascade="all, delete-orphan")
    transactions = relationship("PlaidTransaction", back_populates="connection", cascade="all, delete-orphan")
    identity = relationship("PlaidIdentity", back_populates="connection", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_plaid_connections_user_active', 'user_id', 'is_active'),
        Index('idx_plaid_connections_institution', 'institution_id'),
        Index('idx_plaid_connections_last_sync', 'last_sync_at'),
    )
    
    @validates('access_token')
    def validate_access_token(self, key, value):
        """Validate access token format"""
        if not value or len(value) < 10:
            raise ValueError("Access token must be at least 10 characters")
        return value
    
    @validates('products')
    def validate_products(self, key, value):
        """Validate products list"""
        if not isinstance(value, list):
            raise ValueError("Products must be a list")
        return value
    
    def __repr__(self):
        return f'<PlaidConnection {self.institution_name} for user {self.user_id}>'

class PlaidAccount(Base):
    """Plaid account model for storing bank account information"""
    
    __tablename__ = 'plaid_accounts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    connection_id = Column(UUID(as_uuid=True), ForeignKey('plaid_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Plaid identifiers
    plaid_account_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Account information
    name = Column(String(255), nullable=False)
    mask = Column(String(10), nullable=True)
    official_name = Column(String(255), nullable=True)
    type = Column(String(50), nullable=False)  # depository, credit, loan, investment, etc.
    subtype = Column(String(50), nullable=True)  # checking, savings, credit card, etc.
    
    # Balance information
    current_balance = Column(Float, nullable=True)
    available_balance = Column(Float, nullable=True)
    iso_currency_code = Column(String(3), nullable=True)
    unofficial_currency_code = Column(String(10), nullable=True)
    limit = Column(Float, nullable=True)
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    last_balance_update = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    connection = relationship("PlaidConnection", back_populates="accounts")
    user = relationship("User", back_populates="plaid_accounts")
    transactions = relationship("PlaidTransaction", back_populates="account", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_plaid_accounts_connection_active', 'connection_id', 'is_active'),
        Index('idx_plaid_accounts_user_active', 'user_id', 'is_active'),
        Index('idx_plaid_accounts_type', 'type'),
        Index('idx_plaid_accounts_balance_update', 'last_balance_update'),
    )
    
    @validates('type')
    def validate_type(self, key, value):
        """Validate account type"""
        valid_types = ['depository', 'credit', 'loan', 'investment', 'brokerage', 'other']
        if value not in valid_types:
            raise ValueError(f"Invalid account type: {value}")
        return value
    
    def __repr__(self):
        return f'<PlaidAccount {self.name} ({self.type}) for user {self.user_id}>'

class PlaidTransaction(Base):
    """Plaid transaction model for storing transaction data"""
    
    __tablename__ = 'plaid_transactions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    connection_id = Column(UUID(as_uuid=True), ForeignKey('plaid_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey('plaid_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Plaid identifiers
    plaid_transaction_id = Column(String(255), nullable=False, unique=True, index=True)
    pending_transaction_id = Column(String(255), nullable=True, index=True)
    
    # Transaction information
    name = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    datetime = Column(String(30), nullable=True)  # ISO 8601 format
    authorized_date = Column(String(10), nullable=True)
    authorized_datetime = Column(String(30), nullable=True)
    
    # Merchant information
    merchant_name = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Categorization
    category = Column(JSON, nullable=False, default=list)  # List of category strings
    category_id = Column(String(50), nullable=False)
    personal_finance_category = Column(JSON, nullable=True)  # Plaid's personal finance category
    
    # Transaction details
    pending = Column(Boolean, default=False, nullable=False)
    payment_channel = Column(String(50), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    transaction_code = Column(String(50), nullable=True)
    
    # Location and payment metadata
    location = Column(JSON, nullable=True)  # Address, coordinates, etc.
    payment_meta = Column(JSON, nullable=True)  # Payment method, reference number, etc.
    
    # Currency information
    iso_currency_code = Column(String(3), nullable=True)
    unofficial_currency_code = Column(String(10), nullable=True)
    
    # Additional information
    account_owner = Column(String(255), nullable=True)
    check_number = Column(String(50), nullable=True)
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    connection = relationship("PlaidConnection", back_populates="transactions")
    account = relationship("PlaidAccount", back_populates="transactions")
    user = relationship("User", back_populates="plaid_transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_plaid_transactions_connection', 'connection_id'),
        Index('idx_plaid_transactions_account', 'account_id'),
        Index('idx_plaid_transactions_user', 'user_id'),
        Index('idx_plaid_transactions_date', 'date'),
        Index('idx_plaid_transactions_amount', 'amount'),
        Index('idx_plaid_transactions_category', 'category_id'),
        Index('idx_plaid_transactions_pending', 'pending'),
        Index('idx_plaid_transactions_active', 'is_active'),
    )
    
    @validates('amount')
    def validate_amount(self, key, value):
        """Validate transaction amount"""
        if not isinstance(value, (int, float)):
            raise ValueError("Amount must be a number")
        return float(value)
    
    @validates('date')
    def validate_date(self, key, value):
        """Validate date format"""
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return value
    
    def __repr__(self):
        return f'<PlaidTransaction {self.name} ({self.amount}) for account {self.account_id}>'

class PlaidInstitution(Base):
    """Plaid institution model for storing financial institution information"""
    
    __tablename__ = 'plaid_institutions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Plaid identifiers
    plaid_institution_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Institution information
    name = Column(String(255), nullable=False)
    logo = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color code
    url = Column(String(500), nullable=True)
    
    # Products and features
    products = Column(JSON, nullable=False, default=list)  # List of available products
    routing_numbers = Column(JSON, nullable=True)  # List of routing numbers
    oauth = Column(Boolean, default=False, nullable=False)
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_plaid_institutions_active', 'is_active'),
        Index('idx_plaid_institutions_name', 'name'),
    )
    
    def __repr__(self):
        return f'<PlaidInstitution {self.name}>'

class PlaidSyncLog(Base):
    """Plaid sync log model for tracking synchronization activities"""
    
    __tablename__ = 'plaid_sync_logs'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    connection_id = Column(UUID(as_uuid=True), ForeignKey('plaid_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Sync information
    sync_type = Column(String(50), nullable=False)  # transactions, accounts, identity, etc.
    status = Column(String(20), nullable=False)  # in_progress, success, error
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Sync results
    items_processed = Column(Integer, default=0, nullable=False)
    items_added = Column(Integer, default=0, nullable=False)
    items_updated = Column(Integer, default=0, nullable=False)
    items_failed = Column(Integer, default=0, nullable=False)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional sync information
    
    # Indexes
    __table_args__ = (
        Index('idx_plaid_sync_logs_connection', 'connection_id'),
        Index('idx_plaid_sync_logs_user', 'user_id'),
        Index('idx_plaid_sync_logs_status', 'status'),
        Index('idx_plaid_sync_logs_started', 'started_at'),
        Index('idx_plaid_sync_logs_type', 'sync_type'),
    )
    
    def calculate_duration(self):
        """Calculate sync duration in seconds"""
        if self.started_at and self.completed_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def __repr__(self):
        return f'<PlaidSyncLog {self.sync_type} ({self.status}) for connection {self.connection_id}>'

class PlaidIdentity(Base):
    """Plaid identity model for storing account holder identity information"""
    
    __tablename__ = 'plaid_identities'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    connection_id = Column(UUID(as_uuid=True), ForeignKey('plaid_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Identity information
    names = Column(JSON, nullable=False, default=list)  # List of names
    phone_numbers = Column(JSON, nullable=False, default=list)  # List of phone numbers with metadata
    emails = Column(JSON, nullable=False, default=list)  # List of emails with metadata
    addresses = Column(JSON, nullable=False, default=list)  # List of addresses with metadata
    
    # Account associations
    account_ids = Column(JSON, nullable=False, default=list)  # List of account IDs this identity is associated with
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    connection = relationship("PlaidConnection", back_populates="identity")
    user = relationship("User", back_populates="plaid_identities")
    
    # Indexes
    __table_args__ = (
        Index('idx_plaid_identities_connection', 'connection_id'),
        Index('idx_plaid_identities_user', 'user_id'),
        Index('idx_plaid_identities_active', 'is_active'),
    )
    
    @validates('names')
    def validate_names(self, key, value):
        """Validate names list"""
        if not isinstance(value, list):
            raise ValueError("Names must be a list")
        return value
    
    @validates('phone_numbers')
    def validate_phone_numbers(self, key, value):
        """Validate phone numbers list"""
        if not isinstance(value, list):
            raise ValueError("Phone numbers must be a list")
        return value
    
    @validates('emails')
    def validate_emails(self, key, value):
        """Validate emails list"""
        if not isinstance(value, list):
            raise ValueError("Emails must be a list")
        return value
    
    @validates('addresses')
    def validate_addresses(self, key, value):
        """Validate addresses list"""
        if not isinstance(value, list):
            raise ValueError("Addresses must be a list")
        return value
    
    @validates('account_ids')
    def validate_account_ids(self, key, value):
        """Validate account IDs list"""
        if not isinstance(value, list):
            raise ValueError("Account IDs must be a list")
        return value
    
    def __repr__(self):
        return f'<PlaidIdentity for connection {self.connection_id}>' 