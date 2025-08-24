"""
Integration modules for connecting job security features with existing Mingus functionality
"""

from .financial_planning_integration import FinancialPlanningIntegration
from .goal_setting_integration import GoalSettingIntegration
from .recommendations_integration import RecommendationsIntegration
from .onboarding_integration import OnboardingIntegration

__all__ = [
    'FinancialPlanningIntegration',
    'GoalSettingIntegration',
    'RecommendationsIntegration',
    'OnboardingIntegration'
] 