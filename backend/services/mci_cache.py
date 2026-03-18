#!/usr/bin/env python3
"""
File-based cache for the Mingus Conditions Index (MCI) snapshot.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import sys

# Ensure `services.*` imports work.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from services.mci_service import build_mci_snapshot

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Cache config
# -----------------------------------------------------------------------------

CACHE_PATH = "backend/cache/mci_snapshot.json"

_TTL_DAYS = 7

HISTORY_PATH = "backend/cache/mci_history.json"
MAX_HISTORY_WEEKS = 12


def append_to_history(snapshot: Dict[str, Any]) -> None:
    """
    Append a snapshot into the weekly history array and persist it.

    The history file stores a JSON array of snapshots (not wrapped in an object),
    truncated to MAX_HISTORY_WEEKS most recent entries.
    """
    try:
        history_dir = os.path.dirname(HISTORY_PATH)
        os.makedirs(history_dir, exist_ok=True)

        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except FileNotFoundError:
            existing = []
        except Exception:
            existing = []

        if not isinstance(existing, list):
            existing = []

        existing.append(snapshot)
        history = existing[-MAX_HISTORY_WEEKS :]

        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False)
    except Exception as e:
        # History should never prevent snapshot creation.
        logger.warning("MCI history append failed: %s", e)


def get_history() -> list[dict]:
    """
    Return the MCI weekly history array, or [] if not found/bad.
    """
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)

        if isinstance(existing, list):
            return existing
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning("MCI history read failed: %s", e)
    return []


def get_cached_mci() -> Optional[Dict[str, Any]]:
    """
    Return cached snapshot dict, or None if the cache is missing/expired/bad.
    """
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        cached_at = payload.get("cached_at")
        snapshot = payload.get("snapshot")
        if not isinstance(snapshot, dict):
            return None

        # TTL is driven by the cached_at timestamp in JSON to make unit tests
        # deterministic without relying on filesystem mtime.
        if not cached_at or not isinstance(cached_at, str):
            return None

        cached_dt = datetime.fromisoformat(cached_at)
        if datetime.utcnow() - cached_dt > timedelta(days=_TTL_DAYS):
            return None

        return snapshot
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.warning("MCI cache read failed: %s", e)
        return None


def save_mci_cache(data: Dict[str, Any]) -> None:
    """
    Save a snapshot to the cache file with `cached_at` timestamp.
    """
    try:
        cache_dir = os.path.dirname(CACHE_PATH)
        os.makedirs(cache_dir, exist_ok=True)

        payload = {
            "cached_at": datetime.utcnow().isoformat(),
            "snapshot": data,
        }
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception as e:
        logger.warning("MCI cache write failed: %s", e)


def get_or_fetch_mci() -> Dict[str, Any]:
    """
    Return cached snapshot if available; otherwise build and cache it.
    """
    cached = get_cached_mci()
    if cached is not None:
        return cached

    snapshot = build_mci_snapshot()

    # Persist weekly history only when we build a fresh snapshot.
    append_to_history(snapshot)

    save_mci_cache(snapshot)
    return snapshot

