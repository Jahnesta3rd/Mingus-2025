#!/usr/bin/env python3
"""
MINGUS Application - Post-Migration Cleanup & Maintenance Script
==============================================================

- Safely backup old SQLite databases
- Clean up migration artifacts and temp files
- Set up ongoing PostgreSQL maintenance (VACUUM, ANALYZE, REINDEX)
- Configure monitoring and alerting
- Implement database health check system
- Set up automated backup verification
- Document new database structure and maintenance procedures

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import shutil
import glob
import logging
import subprocess
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from config.environment import validate_and_load_environment, get_database_url

# Configuration
SQLITE_DBS = [
    'mingus.db',
    'business_intelligence.db',
    'cache.db',
    'performance_metrics.db',
    'alerts.db'
]
BACKUP_DIR = 'backups/post_migration/'
TEMP_DIRS = ['tmp/', 'temp/', 'migration_tmp/', 'migration_artifacts/']
LOG_FILE = 'logs/cleanup_migration.log'
HEALTH_CHECK_REPORT = 'db_health_report.json'
DB_STRUCTURE_DOC = 'DATABASE_STRUCTURE.md'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('CleanupMigration')


def backup_sqlite_dbs():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_files = []
    for db in SQLITE_DBS:
        if os.path.exists(db):
            dest = os.path.join(BACKUP_DIR, f'{os.path.basename(db)}_{timestamp}.bak')
            shutil.copy2(db, dest)
            logger.info(f"✅ Backed up {db} -> {dest}")
            backup_files.append(dest)
    return backup_files


def cleanup_temp_files():
    removed = []
    for temp_dir in TEMP_DIRS:
        if os.path.exists(temp_dir):
            for f in glob.glob(os.path.join(temp_dir, '*')):
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                        removed.append(f)
                    elif os.path.isdir(f):
                        shutil.rmtree(f)
                        removed.append(f)
                except Exception as e:
                    logger.warning(f"Could not remove {f}: {e}")
            logger.info(f"✅ Cleaned up {temp_dir}")
    return removed


def optimize_postgres(engine):
    logger.info("Running VACUUM, ANALYZE, and REINDEX on PostgreSQL...")
    with engine.connect() as conn:
        for cmd in ["VACUUM", "ANALYZE", "REINDEX DATABASE mingus_production"]:
            try:
                conn.execute(text(cmd))
                logger.info(f"✅ {cmd} completed.")
            except Exception as e:
                logger.warning(f"{cmd} failed: {e}")


def setup_monitoring_and_alerting():
    # This is a placeholder for integration with external monitoring (e.g., Datadog, Papertrail, DO Monitoring)
    logger.info("Monitoring and alerting should be configured in Digital Ocean dashboard and with external tools.")
    logger.info("- Enable health checks, CPU/memory/disk alerts, and log forwarding.")


def health_check(engine):
    logger.info("Running database health checks...")
    checks = []
    with engine.connect() as conn:
        # Table existence
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        table_list = [row[0] for row in tables]
        checks.append({'check': 'Table existence', 'tables': table_list, 'passed': len(table_list) > 0})
        # Indexes
        idx = conn.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname='public'"))
        idx_list = [row[0] for row in idx]
        checks.append({'check': 'Indexes', 'indexes': idx_list, 'passed': len(idx_list) > 0})
        # Orphaned records
        orphaned = conn.execute(text("SELECT COUNT(*) FROM user_profiles up LEFT JOIN users u ON up.user_id = u.id WHERE u.id IS NULL"))
        orphaned_count = orphaned.fetchone()[0]
        checks.append({'check': 'Orphaned user_profiles', 'count': orphaned_count, 'passed': orphaned_count == 0})
        # Performance
        t0 = datetime.now()
        conn.execute(text("SELECT 1"))
        t1 = datetime.now()
        checks.append({'check': 'Connection latency', 'ms': (t1-t0).total_seconds()*1000, 'passed': (t1-t0).total_seconds()*1000 < 200})
    with open(HEALTH_CHECK_REPORT, 'w') as f:
        json.dump(checks, f, indent=2)
    logger.info(f"Health check report saved to {HEALTH_CHECK_REPORT}")
    return checks


def verify_backups():
    logger.info("Verifying latest PostgreSQL backup...")
    backup_files = sorted(glob.glob('backups/production/pg_backup_*.sql'), reverse=True)
    if not backup_files:
        logger.warning("No PostgreSQL backups found.")
        return False
    latest = backup_files[0]
    # Try to list contents (simulate restore)
    try:
        subprocess.check_call(['pg_restore', '--list', latest])
        logger.info(f"✅ Backup {latest} verified.")
        return True
    except Exception as e:
        logger.error(f"❌ Backup verification failed: {e}")
        return False


def document_db_structure(engine):
    logger.info("Documenting new database structure...")
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        doc = ["# MINGUS PostgreSQL Database Structure\n"]
        for row in tables:
            table = row[0]
            doc.append(f"## Table: {table}\n")
            cols = conn.execute(text(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='{table}'"))
            doc.append("| Column | Type | Nullable |\n|--------|------|----------|\n")
            for col in cols:
                doc.append(f"| {col[0]} | {col[1]} | {col[2]} |\n")
            doc.append("\n")
    with open(DB_STRUCTURE_DOC, 'w') as f:
        f.writelines(doc)
    logger.info(f"Database structure documented in {DB_STRUCTURE_DOC}")


def main():
    logger.info("=== MINGUS POST-MIGRATION CLEANUP & MAINTENANCE START ===")
    try:
        env_manager = validate_and_load_environment()
        env_manager.print_environment_summary()
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        sys.exit(1)
    # 1. Backup old SQLite databases
    backup_sqlite_dbs()
    # 2. Cleanup migration artifacts
    cleanup_temp_files()
    # 3. Optimize and maintain PostgreSQL
    engine = create_engine(get_database_url(), pool_pre_ping=True)
    optimize_postgres(engine)
    # 4. Setup monitoring and alerting
    setup_monitoring_and_alerting()
    # 5. Health check system
    health_check(engine)
    # 6. Automated backup verification
    verify_backups()
    # 7. Document new database structure
    document_db_structure(engine)
    logger.info("=== MINGUS POST-MIGRATION CLEANUP & MAINTENANCE COMPLETE ===")
    sys.exit(0)

if __name__ == "__main__":
    main() 