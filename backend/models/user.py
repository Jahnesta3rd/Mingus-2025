"""
User model for authentication and user management
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Any, Dict
from .base import Base  # Use shared Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone_number = Column(String(50))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Encrypted financial fields (new columns)
    encrypted_monthly_income = Column(Text, nullable=True)
    encrypted_income_frequency = Column(Text, nullable=True)
    encrypted_primary_income_source = Column(Text, nullable=True)
    encrypted_secondary_income_source = Column(Text, nullable=True)
    encrypted_current_savings = Column(Text, nullable=True)
    encrypted_current_debt = Column(Text, nullable=True)
    encrypted_emergency_fund = Column(Text, nullable=True)
    encrypted_savings_goal = Column(Text, nullable=True)
    encrypted_debt_payoff_goal = Column(Text, nullable=True)
    encrypted_investment_goal = Column(Text, nullable=True)
    
    # Encrypted PII fields
    encrypted_ssn = Column(Text, nullable=True)
    encrypted_tax_id = Column(Text, nullable=True)
    encrypted_passport_number = Column(Text, nullable=True)
    encrypted_drivers_license = Column(Text, nullable=True)
    encrypted_address = Column(Text, nullable=True)
    encrypted_birth_date = Column(Text, nullable=True)
    
    # Non-encrypted financial fields (for backwards compatibility)
    monthly_income = Column(DECIMAL(10, 2), nullable=True)
    income_frequency = Column(String(50), nullable=True)
    primary_income_source = Column(String(100), nullable=True)
    secondary_income_source = Column(String(100), nullable=True)
    current_savings = Column(DECIMAL(12, 2), nullable=True)
    current_debt = Column(DECIMAL(12, 2), nullable=True)
    emergency_fund = Column(DECIMAL(12, 2), nullable=True)
    savings_goal = Column(DECIMAL(12, 2), nullable=True)
    debt_payoff_goal = Column(DECIMAL(12, 2), nullable=True)
    investment_goal = Column(DECIMAL(12, 2), nullable=True)
    
    # Risk tolerance and preferences (not encrypted - not sensitive)
    risk_tolerance = Column(String(50), nullable=True)
    investment_experience = Column(String(50), nullable=True)
    budgeting_experience = Column(String(50), nullable=True)
    
    # Encryption metadata
    encryption_version = Column(String(10), nullable=True, default='1.0')
    last_encryption_update = Column(DateTime, nullable=True)
    
    # Relationships - using back_populates for bidirectional relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    onboarding_progress = relationship("OnboardingProgress", back_populates="user")
    health_checkins = relationship("UserHealthCheckin", back_populates="user")
    health_correlations = relationship("HealthSpendingCorrelation", back_populates="user")
    
    # Article library relationships
    article_reads = relationship("UserArticleRead", back_populates="user")
    article_bookmarks = relationship("UserArticleBookmark", back_populates="user")
    article_ratings = relationship("UserArticleRating", back_populates="user")
    article_progress = relationship("UserArticleProgress", back_populates="user")
    article_recommendations = relationship("ArticleRecommendation", back_populates="user")
    assessment_scores = relationship("UserAssessmentScores", back_populates="user", uselist=False)
    
    # Meme splash page relationships
    meme_history = relationship("UserMemeHistory", back_populates="user")
    meme_preferences = relationship("UserMemePreferences", back_populates="user", uselist=False)
    
    # Assessment system relationships
    assessments = relationship("UserAssessment", back_populates="user")
    leads = relationship("Lead", back_populates="user")
    
    # AI Job Assessment relationships
    ai_job_assessments = relationship("AIJobAssessment", back_populates="user", foreign_keys="AIJobAssessment.user_id")
    ai_profile_extension = relationship("AIUserProfileExtension", back_populates="user", uselist=False)
    ai_onboarding_progress = relationship("AIOnboardingProgress", back_populates="user", uselist=False)
    
    # Authentication relationships
    auth_tokens = relationship("AuthToken", back_populates="user")
    email_verification = relationship("EmailVerification", back_populates="user", uselist=False)
    two_factor_auth = relationship("TwoFactorAuth", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary with decrypted values"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Financial data (decrypted)
            'monthly_income': self.monthly_income_encrypted,
            'income_frequency': self.income_frequency_encrypted,
            'primary_income_source': self.primary_income_source_encrypted,
            'secondary_income_source': self.secondary_income_source_encrypted,
            'current_savings': self.current_savings_encrypted,
            'current_debt': self.current_debt_encrypted,
            'emergency_fund': self.emergency_fund_encrypted,
            'savings_goal': self.savings_goal_encrypted,
            'debt_payoff_goal': self.debt_payoff_goal_encrypted,
            'investment_goal': self.investment_goal_encrypted,
            # PII data (decrypted)
            'ssn': self.ssn_encrypted,
            'tax_id': self.tax_id_encrypted,
            'passport_number': self.passport_number_encrypted,
            'drivers_license': self.drivers_license_encrypted,
            'address': self.address_encrypted,
            'birth_date': self.birth_date_encrypted,
            # Non-sensitive data
            'risk_tolerance': self.risk_tolerance,
            'investment_experience': self.investment_experience,
            'budgeting_experience': self.budgeting_experience,
            # Encryption metadata
            'encryption_version': self.encryption_version,
            'last_encryption_update': self.last_encryption_update.isoformat() if self.last_encryption_update else None
        }
    
    # ===== ENCRYPTED PROPERTY DECORATORS =====
    
    @property
    def monthly_income_encrypted(self) -> Optional[float]:
        """Get decrypted monthly income"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if self.encrypted_monthly_income:
                return encryption_service.decrypt_field(
                    self.encrypted_monthly_income, 
                    'financial_data'
                )
            elif self.monthly_income:
                # Fallback to legacy unencrypted field
                return float(self.monthly_income)
            return None
        except Exception:
            # Fallback to legacy field if decryption fails
            return float(self.monthly_income) if self.monthly_income else None
    
    @monthly_income_encrypted.setter
    def monthly_income_encrypted(self, value: Optional[float]):
        """Set encrypted monthly income"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if value is not None:
                self.encrypted_monthly_income = encryption_service.encrypt_field(
                    value, 
                    'financial_data'
                )
                # Keep legacy field for backwards compatibility
                self.monthly_income = value
                self._update_encryption_metadata()
            else:
                self.encrypted_monthly_income = None
                self.monthly_income = None
        except Exception as e:
            # Fallback to legacy field if encryption fails
            self.monthly_income = value
            self.encrypted_monthly_income = None
    
    @property
    def income_frequency_encrypted(self) -> Optional[str]:
        """Get decrypted income frequency"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if self.encrypted_income_frequency:
                return encryption_service.decrypt_field(
                    self.encrypted_income_frequency, 
                    'financial_data'
                )
            elif self.income_frequency:
                return self.income_frequency
            return None
        except Exception:
            return self.income_frequency
    
    @income_frequency_encrypted.setter
    def income_frequency_encrypted(self, value: Optional[str]):
        """Set encrypted income frequency"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if value:
                self.encrypted_income_frequency = encryption_service.encrypt_field(
                    value, 
                    'financial_data'
                )
                self.income_frequency = value
                self._update_encryption_metadata()
            else:
                self.encrypted_income_frequency = None
                self.income_frequency = None
        except Exception:
            self.income_frequency = value
            self.encrypted_income_frequency = None
    
    @property
    def current_savings_encrypted(self) -> Optional[float]:
        """Get decrypted current savings"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if self.encrypted_current_savings:
                return encryption_service.decrypt_field(
                    self.encrypted_current_savings, 
                    'financial_data'
                )
            elif self.current_savings:
                return float(self.current_savings)
            return None
        except Exception:
            return float(self.current_savings) if self.current_savings else None
    
    @current_savings_encrypted.setter
    def current_savings_encrypted(self, value: Optional[float]):
        """Set encrypted current savings"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if value is not None:
                self.encrypted_current_savings = encryption_service.encrypt_field(
                    value, 
                    'financial_data'
                )
                self.current_savings = value
                self._update_encryption_metadata()
            else:
                self.encrypted_current_savings = None
                self.current_savings = None
        except Exception:
            self.current_savings = value
            self.encrypted_current_savings = None
    
    @property
    def current_debt_encrypted(self) -> Optional[float]:
        """Get decrypted current debt"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if self.encrypted_current_debt:
                return encryption_service.decrypt_field(
                    self.encrypted_current_debt, 
                    'financial_data'
                )
            elif self.current_debt:
                return float(self.current_debt)
            return None
        except Exception:
            return float(self.current_debt) if self.current_debt else None
    
    @current_debt_encrypted.setter
    def current_debt_encrypted(self, value: Optional[float]):
        """Set encrypted current debt"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if value is not None:
                self.encrypted_current_debt = encryption_service.encrypt_field(
                    value, 
                    'financial_data'
                )
                self.current_debt = value
                self._update_encryption_metadata()
            else:
                self.encrypted_current_debt = None
                self.current_debt = None
        except Exception:
            self.current_debt = value
            self.encrypted_current_debt = None
    
    # PII Properties
    @property
    def ssn_encrypted(self) -> Optional[str]:
        """Get decrypted SSN"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if self.encrypted_ssn:
                return encryption_service.decrypt_field(
                    self.encrypted_ssn, 
                    'pii'
                )
            return None
        except Exception:
            return None
    
    @ssn_encrypted.setter
    def ssn_encrypted(self, value: Optional[str]):
        """Set encrypted SSN"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if value:
                self.encrypted_ssn = encryption_service.encrypt_field(
                    value, 
                    'pii'
                )
                self._update_encryption_metadata()
            else:
                self.encrypted_ssn = None
        except Exception:
            # Don't store unencrypted SSN
            self.encrypted_ssn = None
    
    @property
    def address_encrypted(self) -> Optional[str]:
        """Get decrypted address"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if self.encrypted_address:
                return encryption_service.decrypt_field(
                    self.encrypted_address, 
                    'pii'
                )
            return None
        except Exception:
            return None
    
    @address_encrypted.setter
    def address_encrypted(self, value: Optional[str]):
        """Set encrypted address"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if value:
                self.encrypted_address = encryption_service.encrypt_field(
                    value, 
                    'pii'
                )
                self._update_encryption_metadata()
            else:
                self.encrypted_address = None
        except Exception:
            self.encrypted_address = None
    
    # ===== HELPER METHODS =====
    
    def _update_encryption_metadata(self):
        """Update encryption metadata when fields are encrypted"""
        self.last_encryption_update = datetime.utcnow()
        if not self.encryption_version:
            self.encryption_version = '1.0'
    
    def migrate_to_encryption(self):
        """Migrate existing unencrypted data to encrypted fields"""
        try:
            from backend.security.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            # Migrate financial data
            if self.monthly_income and not self.encrypted_monthly_income:
                self.monthly_income_encrypted = float(self.monthly_income)
            
            if self.income_frequency and not self.encrypted_income_frequency:
                self.income_frequency_encrypted = self.income_frequency
            
            if self.current_savings and not self.encrypted_current_savings:
                self.current_savings_encrypted = float(self.current_savings)
            
            if self.current_debt and not self.encrypted_current_debt:
                self.current_debt_encrypted = float(self.current_debt)
            
            self._update_encryption_metadata()
            
        except Exception as e:
            # Log error but don't fail migration
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to migrate user {self.id} to encryption: {e}")
    
    def is_fully_encrypted(self) -> bool:
        """Check if all sensitive fields are encrypted"""
        return (
            self.encrypted_monthly_income is not None or
            self.encrypted_current_savings is not None or
            self.encrypted_current_debt is not None or
            self.encrypted_ssn is not None or
            self.encrypted_address is not None
        )
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Get encryption status for this user"""
        return {
            'user_id': self.id,
            'encryption_version': self.encryption_version,
            'last_encryption_update': self.last_encryption_update.isoformat() if self.last_encryption_update else None,
            'fully_encrypted': self.is_fully_encrypted(),
            'financial_fields_encrypted': bool(self.encrypted_monthly_income or self.encrypted_current_savings or self.encrypted_current_debt),
            'pii_fields_encrypted': bool(self.encrypted_ssn or self.encrypted_address),
            'legacy_fields_present': bool(self.monthly_income or self.current_savings or self.current_debt)
        } 