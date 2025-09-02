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

# Two-factor authentication models
from .two_factor_auth import (
    TwoFactorAuth, 
    TwoFactorBackupCode, 
    TwoFactorVerificationAttempt,
    TwoFactorRecoveryRequest
)

# Authentication models
from .auth_tokens import AuthToken

# Assessment models
from .assessment_models import Assessment, UserAssessment, AssessmentResult, Lead, EmailSequence, EmailLog
from .assessment_analytics_models import AssessmentAnalyticsEvent, AssessmentSession, ConversionFunnel

# AI Job Assessment models
from .ai_job_models import AIJobAssessment, AIJobRiskData, AICalculatorConversion
from .ai_user_profile_extension import AIUserProfileExtension, AIOnboardingProgress

# Article library models
from .articles import (
    Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
    UserArticleProgress, ArticleRecommendation, ArticleAnalytics, UserAssessmentScores
)

# Meme models
from .meme_models import Meme, UserMemeHistory, UserMemePreferences

# Email verification model
from .email_verification import EmailVerification

# Export everything needed
__all__ = [
    'Base',  # Shared Base for all models
    'User',
    'UserProfile', 
    'OnboardingProgress',
    'UserHealthCheckin',
    'HealthSpendingCorrelation',
    'UserGoals',
    # Two-factor authentication models
    'TwoFactorAuth',
    'TwoFactorBackupCode',
    'TwoFactorVerificationAttempt',
    'TwoFactorRecoveryRequest',
    # Authentication models
    'AuthToken',
    # Assessment models
    'Assessment',
    'UserAssessment',
    'AssessmentResult',
    'Lead',
    'EmailSequence',
    'EmailLog',
    'AssessmentAnalyticsEvent',
    'AssessmentSession',
    'ConversionFunnel',
    # AI Job Assessment models
    'AIJobAssessment',
    'AIJobRiskData', 
    'AICalculatorConversion',
    'AIUserProfileExtension',
    'AIOnboardingProgress',
    # Article library models
    'Article',
    'UserArticleRead',
    'UserArticleBookmark', 
    'UserArticleRating',
    'UserArticleProgress',
    'ArticleRecommendation',
    'ArticleAnalytics',
    'UserAssessmentScores',
    # Meme models
    'Meme',
    'UserMemeHistory',
    'UserMemePreferences',
    # Email verification model
    'EmailVerification'
] 