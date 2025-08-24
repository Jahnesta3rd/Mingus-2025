#!/usr/bin/env python3
"""
MINGUS Application - Production-Safe Migration Script
====================================================

Safely migrates data to Digital Ocean Managed PostgreSQL with:
- Pre-migration backup
- Transaction-based, zero-downtime migration
- Rollback capabilities
- SSL verification
- Extensive logging and monitoring
- Post-migration validation and performance testing

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import time
import json
import logging
import shutil
import subprocess
import psycopg2
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config.environment import validate_and_load_environment, get_database_url

# Configuration
DIGITALOCEAN_PG_URL = os.environ.get('DATABASE_URL')
SSL_MODE = os.environ.get('DB_SSL_MODE', 'require')
BACKUP_DIR = 'backups/production/'
LOG_FILE = 'logs/production_migration.log'
PERFORMANCE_THRESHOLD_MS = 500

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('ProductionMigration')

@contextmanager
def pg_transaction(engine):
    connection = engine.connect()
    trans = connection.begin()
    try:
        yield connection
        trans.commit()
    except Exception as e:
        trans.rollback()
        raise
    finally:
        connection.close()


def backup_postgres():
    """Perform a full backup of the production PostgreSQL database."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'pg_backup_{timestamp}.sql')
    logger.info(f"Starting PostgreSQL backup to {backup_file}...")
    try:
        # Use pg_dump with SSL
        cmd = [
            'pg_dump', DIGITALOCEAN_PG_URL,
            '--file', backup_file,
            '--format', 'custom',
            '--no-owner',
            '--no-privileges',
            '--compress', '9',
            '--sslmode', SSL_MODE
        ]
        subprocess.check_call(cmd)
        logger.info(f"✅ PostgreSQL backup completed: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"❌ PostgreSQL backup failed: {e}")
        raise


def backup_sqlite(sqlite_paths):
    """Backup all SQLite databases before migration."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_files = []
    for name, path in sqlite_paths.items():
        if not os.path.exists(path):
            continue
        dest = os.path.join(BACKUP_DIR, f'{name}_backup_{timestamp}.db')
        shutil.copy2(path, dest)
        logger.info(f"✅ SQLite backup: {path} -> {dest}")
        backup_files.append(dest)
    return backup_files


def verify_ssl_connection(pg_url):
    logger.info("Verifying SSL connection to PostgreSQL...")
    try:
        conn = psycopg2.connect(pg_url, sslmode=SSL_MODE)
        conn.close()
        logger.info("✅ SSL connection verified.")
        return True
    except Exception as e:
        logger.error(f"❌ SSL connection failed: {e}")
        raise


def monitor_performance(engine, query, params=None):
    start = time.time()
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        rows = result.fetchall() if result.returns_rows else None
    duration = (time.time() - start) * 1000
    logger.info(f"Performance: {query[:40]}... took {duration:.1f}ms")
    if duration > PERFORMANCE_THRESHOLD_MS:
        logger.warning(f"⚠️ Query exceeded performance threshold: {duration:.1f}ms")
    return duration, rows


def validate_data(engine):
    """Post-migration data validation."""
    logger.info("Validating migrated data...")
    checks = []
    # 1. User count
    duration, rows = monitor_performance(engine, "SELECT COUNT(*) FROM users")
    user_count = rows[0][0] if rows else 0
    checks.append(('User count', user_count > 0, user_count))
    # 2. Subscription plans
    duration, rows = monitor_performance(engine, "SELECT COUNT(*) FROM subscription_plans")
    plan_count = rows[0][0] if rows else 0
    checks.append(('Subscription plans', plan_count >= 3, plan_count))
    # 3. Feature access
    duration, rows = monitor_performance(engine, "SELECT COUNT(*) FROM feature_access")
    fa_count = rows[0][0] if rows else 0
    checks.append(('Feature access', fa_count > 0, fa_count))
    # 4. Health checkins
    duration, rows = monitor_performance(engine, "SELECT COUNT(*) FROM user_health_checkins")
    hc_count = rows[0][0] if rows else 0
    checks.append(('Health checkins', hc_count > 0, hc_count))
    # 5. Financial profiles
    duration, rows = monitor_performance(engine, "SELECT COUNT(*) FROM encrypted_financial_profiles")
    fp_count = rows[0][0] if rows else 0
    checks.append(('Financial profiles', fp_count > 0, fp_count))
    # 6. Performance regression
    duration, _ = monitor_performance(engine, "SELECT SUM(monthly_income) FROM encrypted_financial_profiles")
    checks.append(('Performance regression', duration < PERFORMANCE_THRESHOLD_MS, duration))
    # Report
    for name, passed, value in checks:
        status = '✅' if passed else '❌'
        logger.info(f"{status} {name}: {value}")
    if not all(passed for _, passed, _ in checks):
        raise Exception("Post-migration validation failed")
    logger.info("✅ Post-migration validation passed.")


def migrate_data(sqlite_paths, pg_engine):
    """Perform the actual data migration inside a transaction."""
    logger.info("Starting transaction-based migration...")
    with pg_transaction(pg_engine) as conn:
        try:
            # Example: migrate users
            for name, path in sqlite_paths.items():
                if not os.path.exists(path):
                    continue
                sqlite_conn = sqlite3.connect(path)
                sqlite_conn.row_factory = sqlite3.Row
                users = sqlite_conn.execute('SELECT * FROM users').fetchall()
                for user in users:
                    # Upsert user (idempotent)
                    conn.execute(text("""
                        INSERT INTO users (id, email, password_hash, is_active, is_verified, is_admin)
                        VALUES (:id, :email, :password_hash, :is_active, :is_verified, :is_admin)
                        ON CONFLICT (id) DO NOTHING
                    """), dict(user))
                logger.info(f"Migrated {len(users)} users from {name}")
                # Repeat for other tables as needed...
            # Add more migration logic for all tables as needed
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


def rollback_procedure(pg_engine, backup_file):
    logger.warning("Rolling back migration using backup...")
    try:
        # Drop all tables and restore from backup
        cmd = [
            'pg_restore',
            '--clean',
            '--if-exists',
            '--no-owner',
            '--no-privileges',
            '--dbname', DIGITALOCEAN_PG_URL,
            backup_file
        ]
        subprocess.check_call(cmd)
        logger.info("✅ Rollback completed from backup.")
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise


def main():
    logger.info("=== MINGUS PRODUCTION MIGRATION START ===")
    try:
        env_manager = validate_and_load_environment()
        env_manager.print_environment_summary()
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        sys.exit(1)
    # 1. Verify SSL connection
    verify_ssl_connection(DIGITALOCEAN_PG_URL)
    # 2. Pre-migration backup
    backup_file = backup_postgres()
    backup_sqlite({
        'mingus': 'mingus.db',
        'business_intelligence': 'business_intelligence.db',
        'cache': 'cache.db',
        'performance_metrics': 'performance_metrics.db',
        'alerts': 'alerts.db'
    })
    # 3. Zero-downtime migration
    pg_engine = create_engine(DIGITALOCEAN_PG_URL, pool_pre_ping=True)
    try:
        migrate_data({
            'mingus': 'mingus.db',
            'business_intelligence': 'business_intelligence.db',
            'cache': 'cache.db',
            'performance_metrics': 'performance_metrics.db',
            'alerts': 'alerts.db'
        }, pg_engine)
    except Exception as e:
        logger.error(f"❌ Migration failed, starting rollback...")
        rollback_procedure(pg_engine, backup_file)
        sys.exit(1)
    # 4. Post-migration validation
    try:
        validate_data(pg_engine)
    except Exception as e:
        logger.error(f"❌ Post-migration validation failed, starting rollback...")
        rollback_procedure(pg_engine, backup_file)
        sys.exit(1)
    logger.info("=== MINGUS PRODUCTION MIGRATION COMPLETE ===")
    sys.exit(0)

if __name__ == "__main__":
    main() 