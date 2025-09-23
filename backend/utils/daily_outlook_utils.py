#!/usr/bin/env python3
"""
Mingus Application - Daily Outlook Utility Functions
Utility functions for daily outlook operations
"""

import logging
from datetime import date
from typing import Optional

from ..models.daily_outlook import DailyOutlook, UserRelationshipStatus, RelationshipStatus
from ..models.user_models import User
from ..models.database import db
from ..services.daily_outlook_service import DailyOutlookService
from ..services.feature_flag_service import FeatureFlagService, FeatureTier

logger = logging.getLogger(__name__)

# Initialize services
daily_outlook_service = DailyOutlookService()
feature_flag_service = FeatureFlagService()

def calculate_streak_count(user_id: int, target_date: date) -> int:
    """
    Calculate streak count for a user up to a target date
    
    Args:
        user_id: User ID to calculate streak for
        target_date: Date to calculate streak up to
        
    Returns:
        Number of consecutive days with daily outlooks
    """
    return daily_outlook_service.calculate_streak_count(user_id, target_date)

def update_user_relationship_status(user_id: int, status: str, 
                                  satisfaction_score: int, financial_impact_score: int) -> bool:
    """
    Update user's relationship status
    
    Args:
        user_id: User ID to update
        status: Relationship status string
        satisfaction_score: Satisfaction score (1-10)
        financial_impact_score: Financial impact score (1-10)
        
    Returns:
        True if successful, False otherwise
    """
    return daily_outlook_service.update_user_relationship_status(
        user_id, status, satisfaction_score, financial_impact_score
    )

def check_user_tier_access(user_id: int, required_tier: FeatureTier) -> bool:
    """
    Check if a user has access to a specific tier feature
    
    Args:
        user_id: User ID to check
        required_tier: Required tier level
        
    Returns:
        True if user has access, False otherwise
    """
    return feature_flag_service.check_user_tier_access(user_id, required_tier)
