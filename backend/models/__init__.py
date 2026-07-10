#!/usr/bin/env python3
"""
Mingus Application - Database Models Package
SQLAlchemy models for the Mingus financial application
"""

from .database import db
from .user_models import User
from .user_profile import UserProfile
from .beta_code import BetaCode
from .beta_invite_log import BetaInviteLog
from .lead_magnet_email_log import LeadMagnetEmailLog
from .vehicle_models import Vehicle, MaintenancePrediction, CommuteScenario, MSAGasPrice
from .housing_models import HousingSearch, HousingScenario, UserHousingPreferences, CommuteRouteCache, HousingType
from .daily_outlook import DailyOutlook, UserRelationshipStatus, DailyOutlookTemplate, RelationshipStatus, TemplateTier, TemplateCategory
from .notification_models import (
    UserNotificationPreferences,
    PushSubscription,
    NotificationDelivery,
    NotificationInteraction,
    NotificationTemplate,
    NotificationChannel,
    NotificationType,
    DeliveryStatus,
    InteractionType
)
from .wellness import (
    WeeklyCheckin,
    WellnessScore,
    WellnessFinanceCorrelation,
    WellnessCheckinStreak,
    UserSpendingBaseline,
    UserAchievement,
    CheckinQuestionLog,
)
from .financial_setup import RecurringExpense, UserIncome
from .feedback import FeatureRating, NPSSurvey
from .vibe_checkups import (
    VibeCheckupsSession,
    VibeCheckupsLead,
    VibeCheckupsFunnelEvent,
)
from .life_ledger import (
    LifeLedgerProfile,
    LifeLedgerModuleAnswer,
    LifeLedgerInsight,
)
from .vibe_tracker import (
    VibeTrackedPerson,
    VibePersonAssessment,
    VibePersonTrend,
    LlmNarrativeCredit,
)
from .connection_trend import ConnectionTrendAssessment
from .alerts import UserAlert
from .life_correlation import LifeScoreSnapshot
from .spirit_checkin import (
    SpiritCheckin,
    SpiritCheckinStreak,
    SpiritFinanceCorrelation,
)
from .spirit_prefs import SpiritNotificationPrefs, DEFAULT_REMINDER_DAYS
from .in_app_notification import InAppNotification
from .transaction_schedule import IncomeStream, ScheduledExpense
from .favorite_verse import FavoriteVerse
from .bug_report import BugReport
from .onboarding_progress import OnboardingProgress
from .housing_profile import HousingProfile
from .career_profile import CareerProfile
from .career_commitment_profile import CareerCommitmentProfile
from .llm_usage import LlmUsage
from .agreement_acceptance import AgreementAcceptance
from .job_posting import JobPosting
from .transaction import Transaction
from .market_conditions_models import OesWageData, MarketDataCache
from .employer import Employer, EmployerHealthSnapshot, LayoffEvent
from .company_screen import CompanyScreen, CompanyScreenQuestion, CompanyJargonCache
from .hprs_score import HprsScore
from .hprs_plan import HprsPlan
from .hprs_score_history import HprsScoreHistory
from .hprs_latent_candidate import HprsLatentCandidate
from .debt_profile import DebtProfile
from .gap_analysis import GapAnalysisResult
from .health_insurance_plan import HealthInsurancePlan
from .health_insurance_recommendation import HealthInsuranceRecommendation
from .assessment_token import AssessmentToken
from .assessment_event import AssessmentEvent
from .quick_spend import QuickSpendEntry
from .product import Product
from .bts import BackToSchoolSession, BackToSchoolPurchasePlan, BackToSchoolRecommendation
from .order import Order
from .job_commitment import JobCommitment

__all__ = [
    'db',
    'User',
    'UserProfile',
    'BetaCode',
    'BetaInviteLog',
    'LeadMagnetEmailLog',
    'Vehicle',
    'MaintenancePrediction',
    'CommuteScenario',
    'MSAGasPrice',
    'HousingSearch',
    'HousingScenario',
    'UserHousingPreferences',
    'CommuteRouteCache',
    'HousingType',
    'DailyOutlook',
    'UserRelationshipStatus',
    'DailyOutlookTemplate',
    'RelationshipStatus',
    'TemplateTier',
    'TemplateCategory',
    'UserNotificationPreferences',
    'PushSubscription',
    'NotificationDelivery',
    'NotificationInteraction',
    'NotificationTemplate',
    'NotificationChannel',
    'NotificationType',
    'DeliveryStatus',
    'InteractionType',
    'WeeklyCheckin',
    'WellnessScore',
    'WellnessFinanceCorrelation',
    'WellnessCheckinStreak',
    'UserSpendingBaseline',
    'UserAchievement',
    'CheckinQuestionLog',
    'RecurringExpense',
    'UserIncome',
    'FeatureRating',
    'NPSSurvey',
    'VibeCheckupsSession',
    'VibeCheckupsLead',
    'VibeCheckupsFunnelEvent',
    'LifeLedgerProfile',
    'LifeLedgerModuleAnswer',
    'LifeLedgerInsight',
    'VibeTrackedPerson',
    'VibePersonAssessment',
    'VibePersonTrend',
    'LlmNarrativeCredit',
    'ConnectionTrendAssessment',
    'UserAlert',
    'LifeScoreSnapshot',
    'SpiritCheckin',
    'SpiritCheckinStreak',
    'SpiritFinanceCorrelation',
    'SpiritNotificationPrefs',
    'DEFAULT_REMINDER_DAYS',
    'InAppNotification',
    'IncomeStream',
    'ScheduledExpense',
    'FavoriteVerse',
    'BugReport',
    'OnboardingProgress',
    'HousingProfile',
    'CareerProfile',
    'CareerCommitmentProfile',
    'LlmUsage',
    'AgreementAcceptance',
    'JobPosting',
    'Transaction',
    'OesWageData',
    'MarketDataCache',
    'Employer',
    'EmployerHealthSnapshot',
    'LayoffEvent',
    'CompanyScreen',
    'CompanyScreenQuestion',
    'CompanyJargonCache',
    'HprsScore',
    'HprsPlan',
    'HprsScoreHistory',
    'HprsLatentCandidate',
    'DebtProfile',
    'GapAnalysisResult',
    'HealthInsurancePlan',
    'HealthInsuranceRecommendation',
    'QuickSpendEntry',
    'AssessmentToken',
    'AssessmentEvent',
    'Product',
    'BackToSchoolSession',
    'BackToSchoolPurchasePlan',
    'BackToSchoolRecommendation',
    'Order',
    'JobCommitment',
]
