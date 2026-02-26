#!/usr/bin/env python3
"""
Seed sample memes for testing: one meme per day of the week with a distinct theme.

Run from repo root. Uses mingus_memes.db (or MINGUS_MEME_DB_PATH).
Ensures migrations 001 and 004 are applied, then inserts/updates 7 memes (Mon=0 .. Sun=6).

Idempotent: removes any existing day-themed memes, then inserts the 7 sample memes.
"""

import os
import sqlite3
import sys
from pathlib import Path

# Repo root (parent of scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

DB_PATH = os.environ.get("MINGUS_MEME_DB_PATH", str(REPO_ROOT / "mingus_memes.db"))

# Day -> theme and category: aligned with meme_selector.py DAY_CATEGORY_MAP (Python weekday 0=Mon .. 6=Sun)
DAY_THEMES = [
    (0, "Monday Motivation", "work_life", "Monday: When the coffee budget exceeds the food budget ☕💸", "Monday motivation meme about coffee and budget"),
    (1, "Tuesday Health", "health", "Tuesday: Health and hustle. Your body and your budget both need a plan. 💪📊", "Tuesday health meme"),
    (2, "Wednesday Housing", "housing", "Wednesday: Dream home or smart rent? How’s your vibe? How’s your budget? 🧘‍♀️📊", "Wednesday housing meme"),
    (3, "Thursday Transportation", "transportation", "Thursday: Gas, car note, or transit? One more day to plan the commute. 🚗💵", "Thursday transportation meme"),
    (4, "Friday Relationships", "relationships", "Friday: Date night or stay in? Either way, the budget's part of the relationship. 💕👛", "Friday relationships meme"),
    (5, "Saturday Family", "family", "Saturday: Kids want everything. Your budget wants to survive the month. Who wins? 👨‍👩‍👧‍👦💸", "Saturday family meme"),
    (6, "Sunday Faith", "faith", "Sunday: Reset your mind and your spending. New week, new plan. 🌅📋", "Sunday faith meme"),
]

# Placeholder image: same reliable placeholder per day (you can replace with real URLs)
def image_url_for_day(day: int) -> str:
    # Use picsum.photos for varied placeholder images (seed by day for consistency)
    return f"https://picsum.photos/seed/mingus{day}/400/400"


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure memes table exists and has day_of_week, theme columns."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memes'")
    if not cursor.fetchone():
        # Run initial schema if present
        schema_path = REPO_ROOT / "migrations" / "001_initial_meme_schema.sql"
        if schema_path.exists():
            conn.executescript(schema_path.read_text())
        else:
            raise SystemExit("memes table missing and 001_initial_meme_schema.sql not found")
    # Add day_of_week / theme if missing (004)
    cursor.execute("PRAGMA table_info(memes)")
    cols = [row[1] for row in cursor.fetchall()]
    if "day_of_week" not in cols:
        cursor.execute("ALTER TABLE memes ADD COLUMN day_of_week INTEGER")
    if "theme" not in cols:
        cursor.execute("ALTER TABLE memes ADD COLUMN theme TEXT")
    conn.commit()


def seed_memes_by_day(conn: sqlite3.Connection) -> int:
    """Remove existing day-themed memes and insert 7 (one per day). Returns count inserted."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memes WHERE day_of_week IS NOT NULL")
    deleted = cursor.rowcount

    for day_of_week, theme, category, caption, alt_text in DAY_THEMES:
        cursor.execute(
            """
            INSERT INTO memes (image_url, category, caption, alt_text, is_active, day_of_week, theme, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, datetime('now'), datetime('now'))
            """,
            (image_url_for_day(day_of_week), category, caption, alt_text, day_of_week, theme),
        )
    conn.commit()
    return len(DAY_THEMES)


def main() -> None:
    if not Path(DB_PATH).parent.exists():
        print(f"Parent directory of DB does not exist: {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    print(f"Using database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_schema(conn)
        n = seed_memes_by_day(conn)
        print(f"Seeded {n} day-themed sample memes (Mon=0 .. Sun=6).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
