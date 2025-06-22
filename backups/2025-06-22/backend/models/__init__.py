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

# Export everything needed
__all__ = [
    'Base',  # Shared Base for all models
    'User',
    'UserProfile', 
    'OnboardingProgress',
    'UserHealthCheckin',
    'HealthSpendingCorrelation'
] 