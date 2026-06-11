"""Signal library manager — apply keyword additions/removals and auto-parse reports."""

import json
import logging
import re
import sys
from pathlib import Path

from storage import db

logger = logging.getLogger(__name__)

_SIGNALS_PATH = Path(__file__).parent.parent / "config" / "domain_signals.json"
_PENDING_PATH = Path(__file__).parent.parent / "config" / "signal_updates_pending.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_signals() -> dict:
    return json.loads(_SIGNALS_PATH.read_text())


def _save_signals(data: dict) -> None:
    _SIGNALS_PATH.write_text(json.dumps(data, indent=2))


def _load_pending() -> dict:
    if _PENDING_PATH.exists():
        try:
            return json.loads(_PENDING_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"pending_additions": [], "pending_removals": []}


def _save_pending(data: dict) -> None:
    _PENDING_PATH.write_text(json.dumps(data, indent=2))


def _available_domain_ids() -> list:
    signals = _load_signals()
    return [d["domain_id"] for d in signals.get("domains", [])]


# ---------------------------------------------------------------------------
# Public keyword management
# ---------------------------------------------------------------------------

def apply_keyword_addition(
    keyword: str,
    domain_id: str,
    reason: str,
    source: str = "manual",
) -> bool:
    """Add keyword to domain_signals.json and log the update."""
    signals = _load_signals()
    for domain in signals.get("domains", []):
        if domain["domain_id"] == domain_id:
            if keyword not in domain["keywords"]:
                domain["keywords"].append(keyword)
                _save_signals(signals)
                try:
                    db.log_signal_update(
                        domain_id=domain_id,
                        added=keyword,
                        removed=None,
                        reason=reason,
                        source=source,
                    )
                except Exception as exc:
                    logger.warning("DB log_signal_update failed: %s", exc)
                logger.info("Added keyword '%s' to %s", keyword, domain_id)
                return True
            else:
                logger.info("Keyword '%s' already present in %s", keyword, domain_id)
                return True
    logger.warning("Domain '%s' not found in domain_signals.json", domain_id)
    return False


def apply_keyword_removal(
    keyword: str,
    domain_id: str,
    reason: str,
    source: str = "manual",
) -> bool:
    """Remove keyword from domain_signals.json and log the update."""
    signals = _load_signals()
    for domain in signals.get("domains", []):
        if domain["domain_id"] == domain_id:
            if keyword in domain["keywords"]:
                domain["keywords"].remove(keyword)
                _save_signals(signals)
                try:
                    db.log_signal_update(
                        domain_id=domain_id,
                        added=None,
                        removed=keyword,
                        reason=reason,
                        source=source,
                    )
                except Exception as exc:
                    logger.warning("DB log_signal_update failed: %s", exc)
                logger.info("Removed keyword '%s' from %s", keyword, domain_id)
                return True
            else:
                logger.info("Keyword '%s' not found in %s — nothing removed", keyword, domain_id)
                return True
    logger.warning("Domain '%s' not found in domain_signals.json", domain_id)
    return False


# ---------------------------------------------------------------------------
# Auto-parse from weekly report
# ---------------------------------------------------------------------------

def auto_update_from_report(report_dict: dict) -> None:
    """
    Parse the signal_library markdown section from a weekly report dict.
    Writes quoted phrases from section 3 (candidates) and section 4 (false
    positives) to config/signal_updates_pending.json without modifying
    domain_signals.json directly — a human assigns domain_ids during --review.
    """
    signal_text = report_dict.get("sections", {}).get("signal_library", "")
    if not signal_text or "No leads this week" in signal_text or "unavailable" in signal_text:
        logger.info("auto_update_from_report: no usable signal library text")
        return

    # Split into numbered sections by looking for lines starting with "1." .. "5."
    section_texts = {i: "" for i in range(1, 6)}
    current_section = None
    for line in signal_text.splitlines():
        match = re.match(r"^#{0,3}\s*(\d)\.", line)
        if match:
            current_section = int(match.group(1))
        if current_section is not None:
            section_texts[current_section] += line + "\n"

    # Section 3 → keyword candidates (additions)
    additions_raw = re.findall(r'"([^"]{3,80})"', section_texts.get(3, ""))
    # Section 4 → false positives (removals)
    removals_raw = re.findall(r'"([^"]{3,80})"', section_texts.get(4, ""))

    pending = _load_pending()
    existing_add_kws = {item["keyword"] for item in pending["pending_additions"]}
    existing_rem_kws = {item["keyword"] for item in pending["pending_removals"]}

    added_count = 0
    for kw in additions_raw:
        kw = kw.strip().lower()
        if kw and kw not in existing_add_kws:
            pending["pending_additions"].append(
                {"keyword": kw, "domain_id": None, "reason": "weekly_report"}
            )
            existing_add_kws.add(kw)
            added_count += 1

    removed_count = 0
    for kw in removals_raw:
        kw = kw.strip().lower()
        if kw and kw not in existing_rem_kws:
            pending["pending_removals"].append(
                {"keyword": kw, "domain_id": None, "reason": "false_positive"}
            )
            existing_rem_kws.add(kw)
            removed_count += 1

    _save_pending(pending)
    logger.info(
        "auto_update_from_report: %d addition(s) and %d removal(s) queued",
        added_count,
        removed_count,
    )


# ---------------------------------------------------------------------------
# CLI review loop
# ---------------------------------------------------------------------------

def _prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def review_candidates() -> None:
    """Interactive CLI to process pending signal updates."""
    pending = _load_pending()
    domain_ids = _available_domain_ids()
    domain_list = ", ".join(domain_ids)
    remaining_additions = []
    remaining_removals = []

    additions = pending.get("pending_additions", [])
    removals = pending.get("pending_removals", [])

    if not additions and not removals:
        print("No pending signal updates.")
        return

    # --- Additions ---
    if additions:
        print(f"\n=== PENDING ADDITIONS ({len(additions)}) ===")
        print(f"Available domains: {domain_list}\n")
        for item in additions:
            kw = item["keyword"]
            reason = item.get("reason", "")
            print(f"Add '{kw}'  [{reason}]")
            choice = _prompt(f"Domain (or 'skip'): ").lower()
            if choice == "skip" or not choice:
                remaining_additions.append(item)
            elif choice in domain_ids:
                apply_keyword_addition(kw, choice, reason=reason, source="review")
            else:
                print(f"  Unknown domain '{choice}' — skipping")
                remaining_additions.append(item)
            print()

    # --- Removals ---
    if removals:
        print(f"\n=== PENDING REMOVALS ({len(removals)}) ===")
        print(f"Available domains: {domain_list}\n")
        for item in removals:
            kw = item["keyword"]
            reason = item.get("reason", "")
            print(f"Remove '{kw}'  [{reason}]")
            choice = _prompt(f"Domain (or 'skip'): ").lower()
            if choice == "skip" or not choice:
                remaining_removals.append(item)
            elif choice in domain_ids:
                apply_keyword_removal(kw, choice, reason=reason, source="review")
            else:
                print(f"  Unknown domain '{choice}' — skipping")
                remaining_removals.append(item)
            print()

    pending["pending_additions"] = remaining_additions
    pending["pending_removals"] = remaining_removals
    _save_pending(pending)
    print(
        f"Review complete. "
        f"{len(remaining_additions)} addition(s) and "
        f"{len(remaining_removals)} removal(s) still pending."
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    if "--review" in sys.argv:
        review_candidates()
    else:
        pending = _load_pending()
        n_add = len(pending.get("pending_additions", []))
        n_rem = len(pending.get("pending_removals", []))
        print(f"Pending additions: {n_add} | Pending removals: {n_rem}")
        if n_add or n_rem:
            print("Run with --review to process them.")
        else:
            print("Signal library is up to date.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
