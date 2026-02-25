#!/usr/bin/env python3
"""
Risk Performance Monitor - performance monitoring for risk analytics.

Thin wrapper around PerformanceMonitor with risk-analytics default DB path.
Used by unified_risk_analytics_api and risk_analytics_websocket.
"""

from typing import Optional

from .performance_monitor import PerformanceMonitor


# Default DB path for risk analytics (same dir as other risk analytics DBs)
DEFAULT_RISK_PERFORMANCE_DB = "backend/analytics/risk_analytics.db"


class RiskPerformanceMonitor(PerformanceMonitor):
    """
    Performance monitor for risk analytics. Accepts optional db_path;
    uses risk analytics DB by default.
    """

    def __init__(self, db_path: Optional[str] = None):
        path = db_path if db_path is not None else DEFAULT_RISK_PERFORMANCE_DB
        super().__init__(db_path=path)
