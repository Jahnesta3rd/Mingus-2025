"""
MINGUS Application - Data Migration System
==========================================

Comprehensive data migration system to move data from 5 SQLite databases
to the new unified PostgreSQL database.

Handles:
- SQLite to PostgreSQL data type conversions
- Field mapping for renamed/restructured fields
- Data validation and conflict resolution
- Batch processing for large datasets
- Encrypted financial data migration
- Detailed logging and progress tracking
- Rollback capabilities
- Migration reports

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import json
import uuid
import logging
import sqlite3
from datetime import datetime, timezone, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import hashlib
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import our models
from models import Base, engine, SessionLocal, User, UserProfile, OnboardingProgress
from models import SubscriptionPlan, Subscription, FeatureAccess, BillingHistory
from models import UserHealthCheckin, HealthSpendingCorrelation, HealthGoal
from models import EncryptedFinancialProfile, UserIncomeDueDate, UserExpenseDueDate, FinancialTransaction, IncomeProjection
from models import UserAnalytics, PerformanceMetric, FeatureUsage, UserFeedback
from models import JobSecurityAnalysis, CareerMilestone
from models import SystemAlert, ImportantDate, NotificationPreference


@dataclass
class MigrationConfig:
    """Configuration for database migration."""
    
    # SQLite database paths
    sqlite_databases: Dict[str, str] = None
    
    # PostgreSQL connection
    postgres_url: str = None
    
    # Migration settings
    batch_size: int = 1000
    max_workers: int = 4
    dry_run: bool = False
    validate_only: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "migration.log"
    
    # Backup settings
    create_backup: bool = True
    backup_dir: str = "migration_backups"
    
    # Rollback settings
    enable_rollback: bool = True
    rollback_file: str = "rollback_commands.sql"


@dataclass
class MigrationStats:
    """Statistics for migration progress."""
    
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0
    start_time: datetime = None
    end_time: datetime = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate migration progress percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.processed_records == 0:
            return 0.0
        return (self.successful_records / self.processed_records) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate migration duration in seconds."""
        if not self.start_time or not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()


class DataTypeConverter:
    """Handle data type conversions between SQLite and PostgreSQL."""
    
    @staticmethod
    def convert_uuid(value: Any) -> Optional[str]:
        """Convert value to UUID string."""
        if value is None:
            return None
        
        try:
            # If already a UUID string, return as is
            if isinstance(value, str) and len(value) == 36:
                uuid.UUID(value)  # Validate
                return value
            
            # Generate new UUID for integer IDs
            if isinstance(value, int):
                return str(uuid.uuid4())
            
            # Convert other types to string and generate UUID
            return str(uuid.uuid4())
        except (ValueError, TypeError):
            return str(uuid.uuid4())
    
    @staticmethod
    def convert_datetime(value: Any) -> Optional[datetime]:
        """Convert value to timezone-aware datetime."""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Parse various datetime formats
                for fmt in [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                ]:
                    try:
                        dt = datetime.strptime(value, fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                    except ValueError:
                        continue
                
                # If no format matches, try pandas parsing
                return pd.to_datetime(value, utc=True)
            
            elif isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)
                return value
            
            elif isinstance(value, date):
                return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
            
            else:
                return None
        except Exception:
            return None
    
    @staticmethod
    def convert_date(value: Any) -> Optional[date]:
        """Convert value to date."""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
            elif isinstance(value, datetime):
                return value.date()
            elif isinstance(value, date):
                return value
            else:
                return None
        except Exception:
            return None
    
    @staticmethod
    def convert_decimal(value: Any) -> Optional[float]:
        """Convert value to decimal/float."""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                return float(value)
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def convert_json(value: Any) -> Optional[Dict]:
        """Convert value to JSON dict."""
        if value is None:
            return None
        
        try:
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                return json.loads(value)
            else:
                return None
        except (json.JSONDecodeError, TypeError):
            return None
    
    @staticmethod
    def convert_boolean(value: Any) -> Optional[bool]:
        """Convert value to boolean."""
        if value is None:
            return None
        
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return bool(value)
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        else:
            return None


class FieldMapper:
    """Handle field mapping between SQLite and PostgreSQL tables."""
    
    # Field mapping configurations
    FIELD_MAPPINGS = {
        'users': {
            'id': 'id',
            'email': 'email',
            'password_hash': 'password_hash',
            'is_active': 'is_active',
            'is_verified': 'is_verified',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        },
        'user_profiles': {
            'id': 'id',
            'user_id': 'user_id',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'date_of_birth': 'date_of_birth',
            'gender': 'gender',
            'phone_number': 'phone_number',
            'address_line_1': 'address_line_1',
            'address_line_2': 'address_line_2',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'country': 'country',
            'timezone': 'timezone',
            'dependents': 'dependents',
            'marital_status': 'marital_status',
            'household_size': 'household_size',
            'annual_income': 'annual_income',
            'income_source': 'income_source',
            'employment_status': 'employment_status',
            'education_level': 'education_level',
            'occupation': 'occupation',
            'industry': 'industry',
            'years_of_experience': 'years_of_experience',
            'company_name': 'company_name',
            'company_size': 'company_size',
            'job_title': 'job_title',
            'naics_code': 'naics_code',
            'risk_tolerance': 'risk_tolerance',
            'financial_goals': 'financial_goals',
            'preferences': 'preferences',
            'profile_completion_percentage': 'profile_completion_percentage',
            'onboarding_completed': 'onboarding_completed',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        },
        'onboarding_progress': {
            'id': 'id',
            'user_id': 'user_id',
            'step_name': 'step_name',
            'step_order': 'step_order',
            'is_completed': 'is_completed',
            'completed_at': 'completed_at',
            'step_data': 'step_data',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        },
        'user_health_checkins': {
            'id': 'id',
            'user_id': 'user_id',
            'checkin_date': 'checkin_date',
            'mood_score': 'mood_score',
            'stress_level': 'stress_level',
            'sleep_hours': 'sleep_hours',
            'exercise_minutes': 'exercise_minutes',
            'water_intake_oz': 'water_intake_oz',
            'medication_taken': 'medication_taken',
            'symptoms': 'symptoms',
            'wellness_activities': 'wellness_activities',
            'notes': 'notes',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        },
        'health_spending_correlations': {
            'id': 'id',
            'user_id': 'user_id',
            'correlation_date': 'correlation_date',
            'health_metric': 'health_metric',
            'health_score': 'health_score',
            'spending_amount': 'spending_amount',
            'spending_category': 'spending_category',
            'correlation_strength': 'correlation_strength',
            'confidence_interval_lower': 'confidence_interval_lower',
            'confidence_interval_upper': 'confidence_interval_upper',
            'p_value': 'p_value',
            'is_significant': 'is_significant',
            'analysis_period': 'analysis_period',
            'created_at': 'created_at'
        },
        'encrypted_financial_profiles': {
            'id': 'id',
            'user_id': 'user_id',
            'profile_name': 'profile_name',
            'profile_type': 'profile_type',
            'institution_name': 'institution_name',
            'account_number_encrypted': 'account_number_encrypted',
            'routing_number_encrypted': 'routing_number_encrypted',
            'account_balance': 'account_balance',
            'credit_limit': 'credit_limit',
            'interest_rate': 'interest_rate',
            'last_sync_at': 'last_sync_at',
            'sync_status': 'sync_status',
            'is_active': 'is_active',
            'metadata': 'metadata',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        }
    }
    
    # Default values for missing fields
    DEFAULT_VALUES = {
        'user_profiles': {
            'first_name': 'Unknown',
            'last_name': 'User',
            'zip_code': '00000',
            'dependents': 0,
            'household_size': 1,
            'country': 'USA',
            'timezone': 'America/New_York',
            'risk_tolerance': 'moderate',
            'profile_completion_percentage': 0,
            'onboarding_completed': False
        },
        'users': {
            'is_active': True,
            'is_verified': False,
            'login_attempts': 0
        }
    }
    
    @classmethod
    def get_field_mapping(cls, table_name: str) -> Dict[str, str]:
        """Get field mapping for a specific table."""
        return cls.FIELD_MAPPINGS.get(table_name, {})
    
    @classmethod
    def get_default_values(cls, table_name: str) -> Dict[str, Any]:
        """Get default values for a specific table."""
        return cls.DEFAULT_VALUES.get(table_name, {})
    
    @classmethod
    def map_record(cls, table_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a record from SQLite to PostgreSQL format."""
        mapping = cls.get_field_mapping(table_name)
        defaults = cls.get_default_values(table_name)
        
        mapped_record = {}
        
        # Apply field mapping
        for sqlite_field, pg_field in mapping.items():
            if sqlite_field in record:
                mapped_record[pg_field] = record[sqlite_field]
            elif pg_field in defaults:
                mapped_record[pg_field] = defaults[pg_field]
        
        # Add default values for missing fields
        for field, default_value in defaults.items():
            if field not in mapped_record:
                mapped_record[field] = default_value
        
        return mapped_record


class DatabaseMigrator:
    """Main migration class for moving data from SQLite to PostgreSQL."""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.stats = MigrationStats()
        self.errors = []
        self.rollback_commands = []
        
        # Setup logging
        self.setup_logging()
        
        # Database connections
        self.sqlite_connections = {}
        self.postgres_connection = None
        self.postgres_session = None
        
        # Migration state
        self.migration_id = str(uuid.uuid4())
        self.migration_start_time = datetime.now(timezone.utc)
        
        self.logger.info(f"Initializing DatabaseMigrator with migration ID: {self.migration_id}")
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('DatabaseMigrator')
    
    def connect_databases(self):
        """Establish connections to SQLite and PostgreSQL databases."""
        self.logger.info("Connecting to databases...")
        
        # Connect to SQLite databases
        for db_name, db_path in self.config.sqlite_databases.items():
            try:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    conn.row_factory = sqlite3.Row
                    self.sqlite_connections[db_name] = conn
                    self.logger.info(f"Connected to SQLite database: {db_name} ({db_path})")
                else:
                    self.logger.warning(f"SQLite database not found: {db_path}")
            except Exception as e:
                self.logger.error(f"Failed to connect to SQLite database {db_name}: {e}")
                raise
        
        # Connect to PostgreSQL
        try:
            self.postgres_connection = psycopg2.connect(self.config.postgres_url)
            self.postgres_session = SessionLocal()
            self.logger.info("Connected to PostgreSQL database")
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def disconnect_databases(self):
        """Close all database connections."""
        self.logger.info("Disconnecting from databases...")
        
        # Close SQLite connections
        for db_name, conn in self.sqlite_connections.items():
            try:
                conn.close()
                self.logger.info(f"Closed SQLite connection: {db_name}")
            except Exception as e:
                self.logger.error(f"Error closing SQLite connection {db_name}: {e}")
        
        # Close PostgreSQL connection
        if self.postgres_connection:
            try:
                self.postgres_connection.close()
                self.logger.info("Closed PostgreSQL connection")
            except Exception as e:
                self.logger.error(f"Error closing PostgreSQL connection: {e}")
        
        if self.postgres_session:
            try:
                self.postgres_session.close()
                self.logger.info("Closed PostgreSQL session")
            except Exception as e:
                self.logger.error(f"Error closing PostgreSQL session: {e}")
    
    def get_sqlite_tables(self, db_name: str) -> List[str]:
        """Get list of tables in a SQLite database."""
        try:
            conn = self.sqlite_connections[db_name]
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Exception as e:
            self.logger.error(f"Error getting tables from {db_name}: {e}")
            return []
    
    def get_table_schema(self, db_name: str, table_name: str) -> List[Tuple[str, str]]:
        """Get table schema (column name, type) from SQLite."""
        try:
            conn = self.sqlite_connections[db_name]
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = [(row[1], row[2]) for row in cursor.fetchall()]
            cursor.close()
            return schema
        except Exception as e:
            self.logger.error(f"Error getting schema for {db_name}.{table_name}: {e}")
            return []
    
    def get_record_count(self, db_name: str, table_name: str) -> int:
        """Get record count for a table."""
        try:
            conn = self.sqlite_connections[db_name]
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            self.logger.error(f"Error getting record count for {db_name}.{table_name}: {e}")
            return 0
    
    def fetch_records_batch(self, db_name: str, table_name: str, offset: int, limit: int) -> List[Dict]:
        """Fetch a batch of records from SQLite."""
        try:
            conn = self.sqlite_connections[db_name]
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
            records = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return records
        except Exception as e:
            self.logger.error(f"Error fetching records from {db_name}.{table_name}: {e}")
            return []
    
    def convert_record_data_types(self, table_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data types in a record for PostgreSQL compatibility."""
        converter = DataTypeConverter()
        converted_record = {}
        
        for field, value in record.items():
            try:
                # Handle UUID fields
                if field == 'id' or field.endswith('_id'):
                    converted_record[field] = converter.convert_uuid(value)
                
                # Handle datetime fields
                elif field.endswith('_at') or field in ['created_at', 'updated_at', 'last_login_at']:
                    converted_record[field] = converter.convert_datetime(value)
                
                # Handle date fields
                elif field.endswith('_date') or field in ['date_of_birth', 'checkin_date']:
                    converted_record[field] = converter.convert_date(value)
                
                # Handle decimal/numeric fields
                elif field in ['amount', 'balance', 'income', 'price', 'rate'] or 'amount' in field.lower():
                    converted_record[field] = converter.convert_decimal(value)
                
                # Handle JSON fields
                elif field in ['metadata', 'preferences', 'goals', 'data'] or field.endswith('_data'):
                    converted_record[field] = converter.convert_json(value)
                
                # Handle boolean fields
                elif field.startswith('is_') or field in ['active', 'verified', 'completed']:
                    converted_record[field] = converter.convert_boolean(value)
                
                # Keep other fields as is
                else:
                    converted_record[field] = value
                    
            except Exception as e:
                self.logger.warning(f"Error converting field {field} in {table_name}: {e}")
                converted_record[field] = value
        
        return converted_record
    
    def validate_record(self, table_name: str, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a record before insertion."""
        errors = []
        
        # Check required fields
        required_fields = {
            'users': ['email'],
            'user_profiles': ['user_id', 'first_name', 'last_name', 'zip_code'],
            'onboarding_progress': ['user_id', 'step_name'],
            'user_health_checkins': ['user_id', 'checkin_date'],
            'encrypted_financial_profiles': ['user_id', 'profile_name', 'profile_type']
        }
        
        if table_name in required_fields:
            for field in required_fields[table_name]:
                if field not in record or record[field] is None:
                    errors.append(f"Missing required field: {field}")
        
        # Validate data types
        if 'email' in record and record['email']:
            if '@' not in str(record['email']):
                errors.append("Invalid email format")
        
        if 'zip_code' in record and record['zip_code']:
            zip_code = str(record['zip_code'])
            if len(zip_code) not in [5, 10] or not zip_code.replace('-', '').isdigit():
                errors.append("Invalid ZIP code format")
        
        return len(errors) == 0, errors
    
    def insert_record_postgres(self, table_name: str, record: Dict[str, Any]) -> bool:
        """Insert a record into PostgreSQL."""
        try:
            if self.config.dry_run:
                self.logger.info(f"[DRY RUN] Would insert into {table_name}: {record}")
                return True
            
            # Use SQLAlchemy models for insertion
            model_class = self.get_model_class(table_name)
            if model_class:
                # Create model instance
                model_instance = model_class(**record)
                self.postgres_session.add(model_instance)
                self.postgres_session.commit()
                return True
            else:
                # Fallback to raw SQL
                cursor = self.postgres_connection.cursor()
                fields = list(record.keys())
                values = list(record.values())
                placeholders = ', '.join(['%s'] * len(fields))
                query = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                self.postgres_connection.commit()
                cursor.close()
                return True
                
        except Exception as e:
            self.logger.error(f"Error inserting record into {table_name}: {e}")
            self.postgres_session.rollback()
            return False
    
    def get_model_class(self, table_name: str):
        """Get SQLAlchemy model class for a table."""
        model_mapping = {
            'users': User,
            'user_profiles': UserProfile,
            'onboarding_progress': OnboardingProgress,
            'subscription_plans': SubscriptionPlan,
            'subscriptions': Subscription,
            'feature_access': FeatureAccess,
            'billing_history': BillingHistory,
            'user_health_checkins': UserHealthCheckin,
            'health_spending_correlations': HealthSpendingCorrelation,
            'health_goals': HealthGoal,
            'encrypted_financial_profiles': EncryptedFinancialProfile,
            'user_income_due_dates': UserIncomeDueDate,
            'user_expense_due_dates': UserExpenseDueDate,
            'financial_transactions': FinancialTransaction,
            'income_projections': IncomeProjection,
            'user_analytics': UserAnalytics,
            'performance_metrics': PerformanceMetric,
            'feature_usage': FeatureUsage,
            'user_feedback': UserFeedback,
            'job_security_analysis': JobSecurityAnalysis,
            'career_milestones': CareerMilestone,
            'system_alerts': SystemAlert,
            'important_dates': ImportantDate,
            'notification_preferences': NotificationPreference
        }
        return model_mapping.get(table_name)
    
    def migrate_table(self, db_name: str, table_name: str) -> MigrationStats:
        """Migrate a single table from SQLite to PostgreSQL."""
        self.logger.info(f"Starting migration of table: {db_name}.{table_name}")
        
        table_stats = MigrationStats()
        table_stats.start_time = datetime.now(timezone.utc)
        
        # Get record count
        total_records = self.get_record_count(db_name, table_name)
        table_stats.total_records = total_records
        
        if total_records == 0:
            self.logger.info(f"No records to migrate for {db_name}.{table_name}")
            return table_stats
        
        self.logger.info(f"Migrating {total_records} records from {db_name}.{table_name}")
        
        # Process in batches
        offset = 0
        while offset < total_records:
            batch_records = self.fetch_records_batch(db_name, table_name, offset, self.config.batch_size)
            
            for record in batch_records:
                try:
                    table_stats.processed_records += 1
                    
                    # Convert data types
                    converted_record = self.convert_record_data_types(table_name, record)
                    
                    # Map fields
                    mapped_record = FieldMapper.map_record(table_name, converted_record)
                    
                    # Validate record
                    is_valid, validation_errors = self.validate_record(table_name, mapped_record)
                    
                    if not is_valid:
                        self.logger.warning(f"Validation failed for record in {table_name}: {validation_errors}")
                        table_stats.failed_records += 1
                        continue
                    
                    # Insert into PostgreSQL
                    if self.insert_record_postgres(table_name, mapped_record):
                        table_stats.successful_records += 1
                    else:
                        table_stats.failed_records += 1
                    
                    # Log progress
                    if table_stats.processed_records % 100 == 0:
                        progress = (table_stats.processed_records / total_records) * 100
                        self.logger.info(f"Progress for {table_name}: {progress:.1f}% ({table_stats.processed_records}/{total_records})")
                
                except Exception as e:
                    self.logger.error(f"Error processing record in {table_name}: {e}")
                    table_stats.failed_records += 1
                    self.errors.append({
                        'table': table_name,
                        'error': str(e),
                        'record': record
                    })
            
            offset += self.config.batch_size
        
        table_stats.end_time = datetime.now(timezone.utc)
        
        self.logger.info(f"Completed migration of {table_name}: "
                        f"{table_stats.successful_records} successful, "
                        f"{table_stats.failed_records} failed, "
                        f"{table_stats.skipped_records} skipped")
        
        return table_stats
    
    def create_backup(self):
        """Create backup of SQLite databases."""
        if not self.config.create_backup:
            return
        
        backup_dir = Path(self.config.backup_dir) / self.migration_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Creating backup in: {backup_dir}")
        
        for db_name, db_path in self.config.sqlite_databases.items():
            try:
                backup_path = backup_dir / f"{db_name}.db"
                shutil.copy2(db_path, backup_path)
                self.logger.info(f"Backed up {db_name} to {backup_path}")
            except Exception as e:
                self.logger.error(f"Failed to backup {db_name}: {e}")
    
    def generate_rollback_commands(self):
        """Generate rollback commands for the migration."""
        if not self.config.enable_rollback:
            return
        
        self.logger.info("Generating rollback commands...")
        
        rollback_commands = [
            "-- Rollback commands for migration",
            f"-- Migration ID: {self.migration_id}",
            f"-- Generated: {datetime.now(timezone.utc)}",
            "",
            "BEGIN;",
            ""
        ]
        
        # Add DELETE commands for each table (in reverse order due to foreign keys)
        tables_to_rollback = [
            'notification_preferences', 'important_dates', 'system_alerts',
            'career_milestones', 'job_security_analysis',
            'user_feedback', 'feature_usage', 'performance_metrics', 'user_analytics',
            'income_projections', 'financial_transactions', 'user_expense_due_dates',
            'user_income_due_dates', 'encrypted_financial_profiles',
            'health_goals', 'health_spending_correlations', 'user_health_checkins',
            'billing_history', 'feature_access', 'subscriptions', 'subscription_plans',
            'onboarding_progress', 'user_profiles', 'users'
        ]
        
        for table in tables_to_rollback:
            rollback_commands.append(f"DELETE FROM {table};")
        
        rollback_commands.extend([
            "",
            "COMMIT;",
            "",
            "-- End of rollback commands"
        ])
        
        # Write rollback commands to file
        rollback_file = Path(self.config.rollback_file)
        with open(rollback_file, 'w') as f:
            f.write('\n'.join(rollback_commands))
        
        self.logger.info(f"Rollback commands written to: {rollback_file}")
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate comprehensive migration report."""
        self.logger.info("Generating migration report...")
        
        report = {
            'migration_id': self.migration_id,
            'start_time': self.migration_start_time.isoformat(),
            'end_time': datetime.now(timezone.utc).isoformat(),
            'duration_seconds': (datetime.now(timezone.utc) - self.migration_start_time).total_seconds(),
            'config': asdict(self.config),
            'overall_stats': asdict(self.stats),
            'table_stats': {},
            'errors': self.errors,
            'summary': {
                'total_tables_migrated': len(self.stats.table_stats),
                'total_records_processed': self.stats.processed_records,
                'total_records_successful': self.stats.successful_records,
                'total_records_failed': self.stats.failed_records,
                'success_rate': self.stats.success_rate,
                'error_count': len(self.errors)
            }
        }
        
        return report
    
    def save_migration_report(self, report: Dict[str, Any]):
        """Save migration report to file."""
        report_file = f"migration_report_{self.migration_id}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Migration report saved to: {report_file}")
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        try:
            self.logger.info("Starting database migration process...")
            self.stats.start_time = datetime.now(timezone.utc)
            
            # Create backup
            self.create_backup()
            
            # Connect to databases
            self.connect_databases()
            
            # Generate rollback commands
            self.generate_rollback_commands()
            
            # Migrate each database
            for db_name, db_path in self.config.sqlite_databases.items():
                if not os.path.exists(db_path):
                    self.logger.warning(f"Skipping {db_name} - database file not found: {db_path}")
                    continue
                
                self.logger.info(f"Migrating database: {db_name}")
                
                # Get tables in this database
                tables = self.get_sqlite_tables(db_name)
                
                for table_name in tables:
                    # Skip system tables
                    if table_name.startswith('sqlite_'):
                        continue
                    
                    # Migrate table
                    table_stats = self.migrate_table(db_name, table_name)
                    
                    # Update overall stats
                    self.stats.total_records += table_stats.total_records
                    self.stats.processed_records += table_stats.processed_records
                    self.stats.successful_records += table_stats.successful_records
                    self.stats.failed_records += table_stats.failed_records
                    self.stats.skipped_records += table_stats.skipped_records
            
            # Generate and save report
            report = self.generate_migration_report()
            self.save_migration_report(report)
            
            self.stats.end_time = datetime.now(timezone.utc)
            
            # Log final summary
            self.logger.info("Migration completed!")
            self.logger.info(f"Total records processed: {self.stats.processed_records}")
            self.logger.info(f"Successful: {self.stats.successful_records}")
            self.logger.info(f"Failed: {self.stats.failed_records}")
            self.logger.info(f"Success rate: {self.stats.success_rate:.1f}%")
            self.logger.info(f"Duration: {self.stats.duration:.1f} seconds")
            
            return self.stats.failed_records == 0
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return False
        
        finally:
            # Disconnect from databases
            self.disconnect_databases()


def main():
    """Main function to run the migration."""
    
    # Configuration
    config = MigrationConfig(
        sqlite_databases={
            'mingus': 'mingus.db',
            'business_intelligence': 'business_intelligence.db',
            'cache': 'cache.db',
            'performance_metrics': 'performance_metrics.db',
            'alerts': 'alerts.db'
        },
        postgres_url=os.getenv('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production'),
        batch_size=1000,
        max_workers=4,
        dry_run=False,
        validate_only=False,
        log_level='INFO',
        log_file='migration.log',
        create_backup=True,
        backup_dir='migration_backups',
        enable_rollback=True,
        rollback_file='rollback_commands.sql'
    )
    
    # Create and run migrator
    migrator = DatabaseMigrator(config)
    success = migrator.run_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration completed with errors. Check the log file for details.")
        sys.exit(1)


if __name__ == "__main__":
    main() 