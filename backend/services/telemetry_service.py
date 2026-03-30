#!/usr/bin/env python3
"""Feature-level usage telemetry into business_intelligence.db (SQLite, separate from SQLAlchemy)."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

from loguru import logger

TRACKED_FEATURES = [
    "wellness_finance_correlation",
    "vehicle_analytics_dashboard",
    "vehicle_analytics_export",
    "housing_intelligence",
    "housing_investment_analysis",
    "financial_dashboard",
    "mood_dashboard",
    "assessment_ai_risk",
    "assessment_income_comparison",
    "assessment_layoff_risk",
    "assessment_cuffing_season",
    "export_pdf",
    "export_excel",
    "fleet_management",
    "tax_optimization",
]


def _bi_db_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "business_intelligence.db")


class TelemetryService:
    @staticmethod
    def log_event(user_id, event_type, feature_name, metadata=None, user_tier=None):
        """
        Insert a feature_events row. Never raises: failures are logged at warning.
        """
        try:
            meta_json = json.dumps(metadata) if metadata is not None else None
            ts = datetime.now(timezone.utc).isoformat()
            uid = str(user_id) if user_id is not None else None
            tier = str(user_tier) if user_tier is not None else None

            path = _bi_db_path()
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feature_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        event_type TEXT,
                        feature_name TEXT,
                        user_tier TEXT,
                        metadata TEXT,
                        session_id TEXT,
                        timestamp TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO feature_events (
                        user_id, event_type, feature_name, user_tier,
                        metadata, session_id, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, NULL, ?)
                    """,
                    (uid, event_type, feature_name, tier, meta_json, ts),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("TelemetryService.log_event failed: {}", exc)
