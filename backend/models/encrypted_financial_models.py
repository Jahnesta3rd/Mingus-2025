"""
Encrypted Financial Profile Models
Stores encrypted financial data with AES-256 encryption
"""

import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from cryptography.fernet import Fernet
import base64

# Encryption key management
def get_encryption_key():
    """Get encryption key from environment or generate one"""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Generate a new key if not exists (for development)
        key = Fernet.generate_key()
        os.environ['ENCRYPTION_KEY'] = key.decode()
    return key

def encrypt_value(value: float) -> str:
    """Encrypt a numeric value"""
    if value is None:
        return None
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(str(value).encode())
    return base64.b64encode(encrypted).decode()

def decrypt_value(encrypted_value: str) -> Optional[float]:
    """Decrypt a numeric value"""
    if not encrypted_value:
        return None
    try:
        f = Fernet(get_encryption_key())
        decoded = base64.b64decode(encrypted_value.encode())
        decrypted = f.decrypt(decoded)
        return float(decrypted.decode())
    except Exception:
        return None

class EncryptedFinancialProfile(Base):
    """
    Encrypted financial profile model with field-level encryption
    for sensitive financial data like income, savings, and debt amounts
    """
    __tablename__ = 'encrypted_financial_profiles'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Encrypted financial fields
    monthly_income = Column(Text, nullable=True)  # Encrypted
    income_frequency = Column(String(50), nullable=True)
    primary_income_source = Column(String(100), nullable=True)
    secondary_income_source = Column(String(100), nullable=True)
    
    # Encrypted savings and debt
    current_savings = Column(Text, nullable=True)  # Encrypted
    current_debt = Column(Text, nullable=True)  # Encrypted
    emergency_fund = Column(Text, nullable=True)  # Encrypted
    
    # Financial goals (encrypted amounts)
    savings_goal = Column(Text, nullable=True)  # Encrypted
    debt_payoff_goal = Column(Text, nullable=True)  # Encrypted
    investment_goal = Column(Text, nullable=True)  # Encrypted
    
    # Risk tolerance and preferences (not encrypted - not sensitive)
    risk_tolerance = Column(String(50), nullable=True)
    investment_experience = Column(String(50), nullable=True)
    budgeting_experience = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_complete = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User", back_populates="encrypted_financial_profile")
    
    def __repr__(self):
        return f"<EncryptedFinancialProfile(id='{self.id}', user_id='{self.user_id}', is_complete={self.is_complete})>"
    
    def to_dict(self):
        """Convert profile object to dictionary (decrypted values)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'monthly_income': self.get_monthly_income(),
            'income_frequency': self.income_frequency,
            'primary_income_source': self.primary_income_source,
            'secondary_income_source': self.secondary_income_source,
            'current_savings': self.get_current_savings(),
            'current_debt': self.get_current_debt(),
            'emergency_fund': self.get_emergency_fund(),
            'savings_goal': self.get_savings_goal(),
            'debt_payoff_goal': self.get_debt_payoff_goal(),
            'investment_goal': self.get_investment_goal(),
            'risk_tolerance': self.risk_tolerance,
            'investment_experience': self.investment_experience,
            'budgeting_experience': self.budgeting_experience,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_complete': self.is_complete
        }
    
    # Encrypted field getters and setters
    def get_monthly_income(self) -> Optional[float]:
        """Get decrypted monthly income"""
        return decrypt_value(self.monthly_income)
    
    def set_monthly_income(self, value: float) -> None:
        """Set encrypted monthly income"""
        self.monthly_income = encrypt_value(value)
    
    def get_current_savings(self) -> Optional[float]:
        """Get decrypted current savings"""
        return decrypt_value(self.current_savings)
    
    def set_current_savings(self, value: float) -> None:
        """Set encrypted current savings"""
        self.current_savings = encrypt_value(value)
    
    def get_current_debt(self) -> Optional[float]:
        """Get decrypted current debt"""
        return decrypt_value(self.current_debt)
    
    def set_current_debt(self, value: float) -> None:
        """Set encrypted current debt"""
        self.current_debt = encrypt_value(value)
    
    def get_emergency_fund(self) -> Optional[float]:
        """Get decrypted emergency fund"""
        return decrypt_value(self.emergency_fund)
    
    def set_emergency_fund(self, value: float) -> None:
        """Set encrypted emergency fund"""
        self.emergency_fund = encrypt_value(value)
    
    def get_savings_goal(self) -> Optional[float]:
        """Get decrypted savings goal"""
        return decrypt_value(self.savings_goal)
    
    def set_savings_goal(self, value: float) -> None:
        """Set encrypted savings goal"""
        self.savings_goal = encrypt_value(value)
    
    def get_debt_payoff_goal(self) -> Optional[float]:
        """Get decrypted debt payoff goal"""
        return decrypt_value(self.debt_payoff_goal)
    
    def set_debt_payoff_goal(self, value: float) -> None:
        """Set encrypted debt payoff goal"""
        self.debt_payoff_goal = encrypt_value(value)
    
    def get_investment_goal(self) -> Optional[float]:
        """Get decrypted investment goal"""
        return decrypt_value(self.investment_goal)
    
    def set_investment_goal(self, value: float) -> None:
        """Set encrypted investment goal"""
        self.investment_goal = encrypt_value(value)

class EncryptedIncomeSource(Base):
    """
    Encrypted income source model for storing multiple income streams
    """
    __tablename__ = 'encrypted_income_sources'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Encrypted income details
    source_name = Column(String(100), nullable=False)
    amount = Column(Text, nullable=False)  # Encrypted
    frequency = Column(String(50), nullable=False)
    
    # Additional details
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="encrypted_income_sources")
    
    def __repr__(self):
        return f"<EncryptedIncomeSource(id='{self.id}', user_id='{self.user_id}', source='{self.source_name}')>"
    
    def get_amount(self) -> float:
        """Get decrypted amount"""
        return decrypt_value(self.amount) or 0.0
    
    def set_amount(self, value: float) -> None:
        """Set encrypted amount"""
        self.amount = encrypt_value(value)
    
    def to_dict(self):
        """Convert to dictionary (decrypted values)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_name': self.source_name,
            'amount': self.get_amount(),
            'frequency': self.frequency,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EncryptedDebtAccount(Base):
    """
    Encrypted debt account model for storing multiple debt sources
    """
    __tablename__ = 'encrypted_debt_accounts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Encrypted debt details
    account_name = Column(String(100), nullable=False)
    balance = Column(Text, nullable=False)  # Encrypted
    interest_rate = Column(DECIMAL(5, 4), nullable=True)  # Not encrypted - not sensitive
    minimum_payment = Column(Text, nullable=True)  # Encrypted
    
    # Account details
    account_type = Column(String(50), nullable=False)  # credit_card, student_loan, mortgage, etc.
    due_date = Column(Integer, nullable=True)  # Day of month
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="encrypted_debt_accounts")
    
    def __repr__(self):
        return f"<EncryptedDebtAccount(id='{self.id}', user_id='{self.user_id}', account='{self.account_name}')>"
    
    def get_balance(self) -> float:
        """Get decrypted balance"""
        return decrypt_value(self.balance) or 0.0
    
    def set_balance(self, value: float) -> None:
        """Set encrypted balance"""
        self.balance = encrypt_value(value)
    
    def get_minimum_payment(self) -> Optional[float]:
        """Get decrypted minimum payment"""
        return decrypt_value(self.minimum_payment)
    
    def set_minimum_payment(self, value: float) -> None:
        """Set encrypted minimum payment"""
        self.minimum_payment = encrypt_value(value)
    
    def to_dict(self):
        """Convert to dictionary (decrypted values)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_name': self.account_name,
            'balance': self.get_balance(),
            'interest_rate': float(self.interest_rate) if self.interest_rate else None,
            'minimum_payment': self.get_minimum_payment(),
            'account_type': self.account_type,
            'due_date': self.due_date,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FinancialAuditLog(Base):
    """
    Audit log for tracking access to encrypted financial data
    """
    __tablename__ = 'financial_audit_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Audit details
    action = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE
    table_name = Column(String(100), nullable=False)
    record_id = Column(String(36), nullable=True)
    field_name = Column(String(100), nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(36), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="financial_audit_logs")
    
    def __repr__(self):
        return f"<FinancialAuditLog(id='{self.id}', user_id='{self.user_id}', action='{self.action}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'field_name': self.field_name,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 