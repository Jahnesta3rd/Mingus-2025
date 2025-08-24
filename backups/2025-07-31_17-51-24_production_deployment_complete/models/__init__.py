"""
Models package - SQLAlchemy database models with shared Base
Import order is important for relationship resolution
"""

# Import shared Base first
from .base import Base

# Import all models in dependency order (User first, then related models)
from .user import User
from .user_profile import UserProfile
from .onboarding_progress import OnboardingProgress
from .user_health_checkin import UserHealthCheckin
from .health_spending_correlation import HealthSpendingCorrelation
from .user_goals import UserGoals
from .communication_preferences import (
    CommunicationPreferences, ConsentRecord, AlertTypePreference, 
    DeliveryLog, OptOutHistory, UserEngagementMetrics, CommunicationPolicy,
    CommunicationChannel, AlertType, FrequencyType, ConsentStatus, SMSConsent
)
from .communication_analytics import (
    CommunicationMetrics, UserEngagementMetrics, FinancialImpactMetrics,
    ChannelEffectiveness, CostTracking, ABTestResults, CommunicationQueueStatus, 
    AnalyticsAlert, AnalyticsReport, UserSegmentPerformance, 
    MetricType, ChannelType, UserSegment, FinancialOutcome
)
from .behavioral_triggers import (
    BehavioralTrigger, TriggerEvent, TriggerEffectiveness, UserBehaviorPattern,
    MLModel, TriggerTemplate, TriggerSchedule, TriggerType, TriggerCategory,
    TriggerStatus, TriggerPriority
)
from .subscription import (
    Customer, PricingTier, Subscription, PaymentMethod, BillingHistory, SubscriptionUsage,
    FeatureUsage, TaxCalculation, Refund, Credit, ProrationCalculation,
    AuditLog, ComplianceRecord, SecurityEvent, BillingDispute, DisputeComment
)

# Database session configuration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engine and session factory
engine = create_engine('sqlite:///instance/mingus.db', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = SessionLocal()

# Export everything needed
__all__ = [
    'Base',  # Shared Base for all models
    'User',
    'UserProfile', 
    'OnboardingProgress',
    'UserHealthCheckin',
    'HealthSpendingCorrelation',
    'UserGoals',
    'CommunicationPreferences',
    'ConsentRecord',
    'AlertTypePreference',
    'DeliveryLog',
    'OptOutHistory',
    'UserEngagementMetrics',
    'CommunicationPolicy',
    'CommunicationChannel',
    'AlertType',
    'FrequencyType',
    'ConsentStatus',
    'SMSConsent',
    'CommunicationMetrics',
    'FinancialImpactMetrics',
    'ChannelEffectiveness',
    'CostTracking',
    'ABTestResults',
    'CommunicationQueueStatus',
    'AnalyticsAlert',
    'AnalyticsReport',
    'UserSegmentPerformance',
    'MetricType',
    'ChannelType',
    'UserSegment',
    'FinancialOutcome',
    'BehavioralTrigger',
    'TriggerEvent',
    'TriggerEffectiveness',
    'UserBehaviorPattern',
    'MLModel',
    'TriggerTemplate',
    'TriggerSchedule',
    'TriggerType',
    'TriggerCategory',
    'TriggerStatus',
    'TriggerPriority',
    'Customer',
    'PricingTier',
    'Subscription',
    'PaymentMethod',
    'BillingHistory',
    'SubscriptionUsage',
    'FeatureUsage',
    'TaxCalculation',
    'Refund',
    'Credit',
    'ProrationCalculation',
    'AuditLog',
    'ComplianceRecord',
    'SecurityEvent',
    'BillingDispute',
    'DisputeComment',
    'db_session',
    'SessionLocal'
]
