#!/usr/bin/env python3
"""Append-only SQLite log for business intelligence events (separate from main DB)."""
import os
import sqlite3
from datetime import datetime


def _db_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "business_intelligence.db")


def log_event(event_type: str, **fields):
    """
    Insert a row into business_intelligence.db.

    Stored columns: event_type, timestamp (UTC iso), plus arbitrary string keys in fields.
    """
    path = _db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bi_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                code TEXT,
                batch TEXT,
                timestamp TEXT NOT NULL,
                extra TEXT
            )
            """
        )
        ts = datetime.utcnow().isoformat() + "Z"
        conn.execute(
            """
            INSERT INTO bi_events (event_type, user_id, code, batch, timestamp, extra)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_type,
                fields.get("user_id"),
                fields.get("code"),
                fields.get("batch"),
                ts,
                fields.get("extra"),
            ),
        )
        conn.commit()
    finally:
        conn.close()
