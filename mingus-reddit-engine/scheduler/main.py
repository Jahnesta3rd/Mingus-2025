"""Mingus Reddit Engine — main scheduler entry point."""

import argparse
import logging
import os
import sys
import traceback
import zoneinfo
from pathlib import Path
from urllib.parse import urlparse, unquote

ET = zoneinfo.ZoneInfo("America/New_York")

# ---------------------------------------------------------------------------
# Module-level env bootstrap — must run before any storage.db import so the
# connection pool in db.py sees the correct PG* vars at initialisation time.
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv("/var/www/mingus/.env")
except ImportError:
    pass

_database_url = os.getenv("DATABASE_URL", "")
if _database_url:
    _p = urlparse(_database_url)
    os.environ["PGHOST"] = _p.hostname or ""
    os.environ["PGPORT"] = str(_p.port or 5432)
    os.environ["PGUSER"] = unquote(_p.username or "")
    os.environ["PGPASSWORD"] = unquote(_p.password or "")
    os.environ["PGDATABASE"] = _p.path.lstrip("/")
    os.environ["PGSSLMODE"] = "require"


# ---------------------------------------------------------------------------
# Logging — must configure before any module import that uses logging
# ---------------------------------------------------------------------------

def _configure_logging():
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(logs_dir / "engine.log"),
        ],
    )


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Environment bootstrap
# ---------------------------------------------------------------------------

def _load_env():
    """Re-run dotenv + DATABASE_URL expansion inside main() for safety."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        load_dotenv("/var/www/mingus/.env")
    except ImportError:
        pass

    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        p = urlparse(database_url)
        os.environ["PGHOST"] = p.hostname or ""
        os.environ["PGPORT"] = str(p.port or 5432)
        os.environ["PGUSER"] = unquote(p.username or "")
        os.environ["PGPASSWORD"] = unquote(p.password or "")
        os.environ["PGDATABASE"] = p.path.lstrip("/")
        os.environ["PGSSLMODE"] = "require"


# ---------------------------------------------------------------------------
# Lazy pipeline imports (avoids DB pool creation at import time)
# ---------------------------------------------------------------------------

def _imports():
    from storage import db
    from intelligence import heat_map
    from listeners import reddit_listener
    from pipeline import matcher, scorer, reply_crafter, notifier
    from pipeline import ads_brief as ads_brief_mod
    from reporting import weekly_report as weekly_report_mod
    return db, heat_map, reddit_listener, matcher, scorer, reply_crafter, notifier, ads_brief_mod, weekly_report_mod


# ---------------------------------------------------------------------------
# Core pipeline step — matcher → scorer → store
# ---------------------------------------------------------------------------

def _process_items(items, db, matcher, scorer, reply_crafter, notifier, dry_run=False):
    leads_scored = 0
    leads_stored = 0
    hot_leads = 0

    for item in items:
        match = matcher.keyword_match(item)
        if match is None:
            continue

        lead = scorer.semantic_score(match)
        if lead is None:
            continue

        leads_scored += 1

        if dry_run:
            print(
                f"  [DRY RUN] would store: "
                f"r/{item.get('subreddit')} | "
                f"score={lead.get('composite_score')} | "
                f"domain={lead.get('domain_id')}"
            )
            continue

        db.insert_lead(lead)
        leads_stored += 1
        reply_crafter.process_lead(lead)

        if lead.get("is_hot_lead"):
            hot_leads += 1
            notifier.send_hot_lead_sms(lead)

    return leads_scored, leads_stored, hot_leads


# ---------------------------------------------------------------------------
# Scheduled job functions
# ---------------------------------------------------------------------------

def run_pipeline(dry_run=False):
    """Full 6-hour pipeline: heat check → listen → match/score → store."""
    try:
        db, heat_map, reddit_listener, matcher, scorer, reply_crafter, notifier, _, _ = _imports()

        # 1. Heat check
        heat_map.run_heat_check()
        communities = db.get_communities()
        logger.info("Heat check complete: %d communities refreshed", len(communities))

        # 2. Listener
        result = reddit_listener.run_listener()
        logger.info(
            "Listener complete: %d fetched, %d new",
            result["total_items"],
            result["new_items"],
        )

        # 3. Match / score / store
        leads_scored, leads_stored, hot_leads = _process_items(
            result["items"], db, matcher, scorer, reply_crafter, notifier, dry_run=dry_run
        )

        # 4. Summary
        logger.info(
            "PIPELINE COMPLETE | leads scored: %d | leads stored: %d | hot leads: %d",
            leads_scored,
            leads_stored,
            hot_leads,
        )

    except Exception:
        logger.error("Unhandled exception in run_pipeline:\n%s", traceback.format_exc())


def run_peak_scan():
    """High-traffic window scan — high-tier communities only."""
    try:
        db, heat_map, reddit_listener, matcher, scorer, reply_crafter, notifier, _, _ = _imports()

        high_communities = heat_map.get_ranked_communities(min_tier="high")
        if not high_communities:
            logger.info("No high-tier communities — skipping peak scan")
            return

        # Run listener scoped to high-tier by temporarily patching get_ranked_communities
        import listeners.reddit_listener as _rl_module
        import intelligence.heat_map as _hm_module

        _orig = _hm_module.get_ranked_communities

        def _high_only(min_tier=None):
            return _orig(min_tier="high")

        _rl_module.get_ranked_communities = _high_only  # type: ignore[attr-defined]
        # also patch inside the module's own namespace
        try:
            result = _rl_module.run_listener()
        finally:
            _rl_module.get_ranked_communities = _orig  # type: ignore[attr-defined]

        logger.info(
            "Peak scan complete: %d fetched from %d high-tier communities",
            result["total_items"],
            result["communities_scanned"],
        )

        leads_scored, leads_stored, hot_leads = _process_items(
            result["items"], db, matcher, scorer, reply_crafter, notifier
        )
        logger.info(
            "Peak scan pipeline | scored: %d | stored: %d | hot: %d",
            leads_scored, leads_stored, hot_leads,
        )

    except Exception:
        logger.error("Unhandled exception in run_peak_scan:\n%s", traceback.format_exc())


def run_daily_digest():
    """Send (or print) the daily lead digest."""
    try:
        _, _, _, _, _, _, notifier, _, _ = _imports()
        success = notifier.send_daily_digest()
        logger.info("Daily digest %s", "sent" if success else "FAILED")
    except Exception:
        logger.error("Unhandled exception in run_daily_digest:\n%s", traceback.format_exc())


def run_weekly_brief():
    """Generate and email the weekly Reddit Ads brief."""
    try:
        _, _, _, _, _, _, notifier, ads_brief_mod, _ = _imports()
        brief = ads_brief_mod.generate_brief()
        success = notifier.send_weekly_ads_brief(brief)
        logger.info("Weekly brief %s", "sent" if success else "FAILED")
    except Exception:
        logger.error("Unhandled exception in run_weekly_brief:\n%s", traceback.format_exc())


def run_weekly_report():
    """Generate the weekly performance report."""
    try:
        _, _, _, _, _, _, _, _, weekly_report_mod = _imports()
        report = weekly_report_mod.generate_report()
        logger.info("Weekly report saved: %s", report.get("output_file", "unknown"))
    except Exception:
        logger.error("Unhandled exception in run_weekly_report:\n%s", traceback.format_exc())


# cluster_expander.run_expansion() — 1st of month, 05:00 ET
# Activate when PRAW_AVAILABLE = True


# ---------------------------------------------------------------------------
# --status helper
# ---------------------------------------------------------------------------

def _print_status():
    from psycopg2.extras import RealDictCursor
    db, _, _, _, _, _, _, _, _ = _imports()

    conn = db.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS total FROM leads")
            total_leads = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS total FROM communities WHERE active = TRUE")
            total_communities = cur.fetchone()["total"]

            cur.execute(
                "SELECT generated_at, status FROM ad_briefs "
                "ORDER BY generated_at DESC LIMIT 1"
            )
            latest_brief = cur.fetchone()
    finally:
        db.release_connection(conn)

    print("=== Mingus Reddit Engine Status ===")
    print(f"Total leads (all time): {total_leads}")
    print(f"Active communities:     {total_communities}")
    if latest_brief:
        print(
            f"Last ads brief:         {latest_brief['generated_at'].date()} "
            f"[{latest_brief['status']}]"
        )
    else:
        print("Last ads brief:         none yet")


# ---------------------------------------------------------------------------
# Scheduler builder
# ---------------------------------------------------------------------------

def _build_scheduler():
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BlockingScheduler(timezone=ET)

    # Full pipeline — every 6 hours
    scheduler.add_job(
        run_pipeline,
        CronTrigger(hour="0,6,12,18", minute=0, timezone=ET),
        id="pipeline",
        name="Full pipeline",
        max_instances=1,
        coalesce=True,
    )

    # Peak scan — 12:00 and 20:00 ET daily
    for hour in (12, 20):
        scheduler.add_job(
            run_peak_scan,
            CronTrigger(hour=hour, minute=0, timezone=ET),
            id=f"peak_scan_{hour}",
            name=f"Peak scan {hour}:00 ET",
            max_instances=1,
            coalesce=True,
        )

    # Daily digest — 08:00 ET
    scheduler.add_job(
        run_daily_digest,
        CronTrigger(hour=8, minute=0, timezone=ET),
        id="daily_digest",
        name="Daily digest",
        max_instances=1,
        coalesce=True,
    )

    # Weekly ads brief — Sunday 06:00 ET
    scheduler.add_job(
        run_weekly_brief,
        CronTrigger(day_of_week="sun", hour=6, minute=0, timezone=ET),
        id="weekly_brief",
        name="Weekly ads brief",
        max_instances=1,
        coalesce=True,
    )

    # Weekly report — Monday 07:00 ET
    scheduler.add_job(
        run_weekly_report,
        CronTrigger(day_of_week="mon", hour=7, minute=0, timezone=ET),
        id="weekly_report",
        name="Weekly report",
        max_instances=1,
        coalesce=True,
    )

    return scheduler


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Mingus Reddit Engine scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline once without storing leads or sending notifications",
    )
    parser.add_argument(
        "--test-community",
        metavar="NAME",
        help="Run listener + pipeline for one community only (no storage)",
    )
    parser.add_argument(
        "--generate-brief",
        action="store_true",
        help="Generate and send the weekly ads brief now, then exit",
    )
    parser.add_argument(
        "--heat-check",
        action="store_true",
        help="Run a heat check now and exit",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate the weekly performance report now and exit",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialise (or re-initialise) the database schema and exit",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current system status and exit",
    )
    return parser.parse_args()


def main():
    _configure_logging()
    # Re-run env bootstrap inside main() so PG* vars are guaranteed to be set
    # before any code path that triggers _imports() / storage.db import.
    _load_env()

    args = _parse_args()

    # --- One-shot flags (all exit after completing) ---

    if args.init_db:
        from storage import db
        db.init_db()
        print("Database initialised.")
        return

    if args.status:
        _print_status()
        return

    if args.heat_check:
        from intelligence import heat_map
        from storage import db
        heat_map.run_heat_check()
        communities = db.get_communities()
        print(f"Heat check complete: {len(communities)} communities active")
        return

    if args.generate_brief:
        run_weekly_brief()
        return

    if args.report:
        run_weekly_report()
        return

    if args.test_community:
        name = args.test_community
        db, _, _, matcher, scorer, _, _, _, _ = _imports()
        from listeners.reddit_listener import fetch_community_content
        from intelligence.heat_map import get_ranked_communities

        community_row = next(
            (c for c in get_ranked_communities(min_tier="low") if c["name"].lower() == name.lower()),
            None,
        )
        if not community_row:
            print(f"Community '{name}' not found in DB. Run --heat-check first.")
            sys.exit(1)

        items = fetch_community_content(community_row)
        print(f"Fetched {len(items)} items from r/{name}")
        leads_scored, _, _ = _process_items(
            items, db, matcher, scorer,
            reply_crafter=type("_NR", (), {"process_lead": staticmethod(lambda l: None)})(),
            notifier=type("_NR", (), {"send_hot_lead_sms": staticmethod(lambda l: None)})(),
            dry_run=True,
        )
        print(f"Leads that would be scored: {leads_scored}")
        return

    if args.dry_run:
        print("DRY RUN — pipeline will run once without storing or notifying")
        run_pipeline(dry_run=True)
        return

    # --- Full scheduled mode ---
    from storage import db
    from intelligence import heat_map

    db.init_db()
    heat_map.seed_communities()

    active = db.get_communities()
    logger.info("Mingus Reddit Engine started")
    logger.info("Communities: %d active", len(active))
    logger.info("Schedule: pipeline every 6h, digest daily 8am ET")

    scheduler = _build_scheduler()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
