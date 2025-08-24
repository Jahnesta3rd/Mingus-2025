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

# Article library models
from .articles import (
    Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
    UserArticleProgress, ArticleRecommendation, ArticleAnalytics, UserAssessmentScores
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
    # Article library models
    'Article',
    'UserArticleRead',
    'UserArticleBookmark', 
    'UserArticleRating',
    'UserArticleProgress',
    'ArticleRecommendation',
    'ArticleAnalytics',
    'UserAssessmentScores',
    'db_session',
    'SessionLocal'
] 