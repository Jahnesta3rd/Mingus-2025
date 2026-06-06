#!/usr/bin/env python3
"""Re-export shim — recommendation logic lives in backend.utils.mingus_job_recommendation_engine."""

from backend.utils.mingus_job_recommendation_engine import (
    MingusJobRecommendationEngine,
    SENIORITY_ORDER,
    TRANSITION_AFFINITY,
    seniority_distance,
)

__all__ = [
    'MingusJobRecommendationEngine',
    'SENIORITY_ORDER',
    'TRANSITION_AFFINITY',
    'seniority_distance',
]
