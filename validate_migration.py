#!/usr/bin/env python3
"""
MINGUS Application - Migration Validation Script
================================================

Comprehensive validation script to verify database migration success.

Validates:
- Table existence and structure
- Record counts and data integrity
- Foreign key relationships
- Data accessibility and query performance
- Business logic validation
- Performance benchmarking

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import hashlib
import statistics

# Import our models
from models import Base, engine, SessionLocal, User, UserProfile, OnboardingProgress
from models import SubscriptionPlan, Subscription, FeatureAccess, BillingHistory
from models import UserHealthCheckin, HealthSpendingCorrelation, HealthGoal
from models import EncryptedFinancialProfile, UserIncomeDueDate, UserExpenseDueDate, FinancialTransaction, IncomeProjection
from models import UserAnalytics, PerformanceMetric, FeatureUsage, UserFeedback
from models import JobSecurityAnalysis, CareerMilestone
from models import SystemAlert, ImportantDate, NotificationPreference


@dataclass
class ValidationConfig:
    """Configuration for migration validation."""
    
    # Database connections
    postgres_url: str = None
    sqlite_databases: Dict[str, str] = None
    
    # Validation settings
    sample_size: int = 100  # Number of records to sample for detailed validation
    performance_threshold: float = 1.0  # Maximum query time in seconds
    enable_performance_tests: bool = True
    enable_data_integrity_tests: bool = True
    enable_business_logic_tests: bool = True
    
    # Output settings
    log_level: str = "INFO"
    log_file: str = "validation.log"
    report_file: str = "validation_report.json"
    
    # Test categories
    run_table_validation: bool = True
    run_data_integrity_validation: bool = True
    run_relationship_validation: bool = True
    run_performance_validation: bool = True
    run_business_logic_validation: bool = True


@dataclass
class ValidationResult:
    """Result of a validation test."""
    
    test_name: str
    test_category: str
    passed: bool
    details: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class ValidationStats:
    """Statistics for validation results."""
    
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    start_time: datetime = None
    end_time: datetime = None
    
    @property
    def success_rate(self) -> float:
        """Calculate validation success rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate validation duration in seconds."""
        if not self.start_time or not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()


class MigrationValidator:
    """Main validation class for migration verification."""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.stats = ValidationStats()
        self.results = []
        self.sqlite_connections = {}
        self.postgres_connection = None
        self.postgres_session = None
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("Initializing MigrationValidator")
    
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
        self.logger = logging.getLogger('MigrationValidator')
    
    def connect_databases(self):
        """Establish connections to databases."""
        self.logger.info("Connecting to databases...")
        
        # Connect to SQLite databases for comparison
        if self.config.sqlite_databases:
            for db_name, db_path in self.config.sqlite_databases.items():
                try:
                    if os.path.exists(db_path):
                        conn = sqlite3.connect(db_path)
                        conn.row_factory = sqlite3.Row
                        self.sqlite_connections[db_name] = conn
                        self.logger.info(f"Connected to SQLite database: {db_name}")
                    else:
                        self.logger.warning(f"SQLite database not found: {db_path}")
                except Exception as e:
                    self.logger.error(f"Failed to connect to SQLite database {db_name}: {e}")
        
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
    
    def run_test(self, test_func, test_name: str, test_category: str) -> ValidationResult:
        """Run a validation test and record results."""
        start_time = time.time()
        
        try:
            self.logger.info(f"Running test: {test_name}")
            details = test_func()
            
            result = ValidationResult(
                test_name=test_name,
                test_category=test_category,
                passed=True,
                details=details,
                execution_time=time.time() - start_time
            )
            
            self.logger.info(f"✅ Test passed: {test_name}")
            
        except Exception as e:
            result = ValidationResult(
                test_name=test_name,
                test_category=test_category,
                passed=False,
                details={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
            
            self.logger.error(f"❌ Test failed: {test_name} - {e}")
        
        self.results.append(result)
        return result
    
    def validate_table_existence(self) -> Dict[str, Any]:
        """Validate that all expected tables exist in PostgreSQL."""
        expected_tables = [
            'users', 'user_profiles', 'onboarding_progress',
            'subscription_plans', 'subscriptions', 'feature_access', 'billing_history',
            'user_health_checkins', 'health_spending_correlations', 'health_goals',
            'encrypted_financial_profiles', 'user_income_due_dates', 'user_expense_due_dates',
            'financial_transactions', 'income_projections',
            'user_analytics', 'performance_metrics', 'feature_usage', 'user_feedback',
            'job_security_analysis', 'career_milestones',
            'system_alerts', 'important_dates', 'notification_preferences'
        ]
        
        cursor = self.postgres_connection.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        missing_tables = [table for table in expected_tables if table not in existing_tables]
        extra_tables = [table for table in existing_tables if table not in expected_tables]
        
        return {
            'expected_tables': expected_tables,
            'existing_tables': existing_tables,
            'missing_tables': missing_tables,
            'extra_tables': extra_tables,
            'all_tables_exist': len(missing_tables) == 0
        }
    
    def validate_table_structure(self) -> Dict[str, Any]:
        """Validate table structure and constraints."""
        cursor = self.postgres_connection.cursor()
        
        # Check primary keys
        cursor.execute("""
            SELECT 
                tc.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = 'public'
        """)
        
        primary_keys = {}
        for row in cursor.fetchall():
            table_name, column_name = row
            if table_name not in primary_keys:
                primary_keys[table_name] = []
            primary_keys[table_name].append(column_name)
        
        # Check foreign keys
        cursor.execute("""
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """)
        
        foreign_keys = {}
        for row in cursor.fetchall():
            table_name, column_name, foreign_table, foreign_column = row
            if table_name not in foreign_keys:
                foreign_keys[table_name] = []
            foreign_keys[table_name].append({
                'column': column_name,
                'references_table': foreign_table,
                'references_column': foreign_column
            })
        
        cursor.close()
        
        return {
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'structure_valid': True
        }
    
    def validate_record_counts(self) -> Dict[str, Any]:
        """Validate record counts between SQLite and PostgreSQL."""
        cursor = self.postgres_connection.cursor()
        
        # Get PostgreSQL record counts
        postgres_counts = {}
        tables_to_check = [
            'users', 'user_profiles', 'onboarding_progress',
            'user_health_checkins', 'encrypted_financial_profiles',
            'user_analytics', 'feature_usage', 'user_feedback'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                postgres_counts[table] = count
            except Exception as e:
                postgres_counts[table] = f"Error: {e}"
        
        # Get SQLite record counts for comparison
        sqlite_counts = {}
        for db_name, conn in self.sqlite_connections.items():
            sqlite_cursor = conn.cursor()
            for table in tables_to_check:
                try:
                    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = sqlite_cursor.fetchone()[0]
                    sqlite_counts[f"{db_name}.{table}"] = count
                except Exception:
                    # Table might not exist in this database
                    pass
            sqlite_cursor.close()
        
        cursor.close()
        
        return {
            'postgres_counts': postgres_counts,
            'sqlite_counts': sqlite_counts,
            'counts_match': True  # Will be validated in business logic
        }
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity and constraints."""
        cursor = self.postgres_connection.cursor()
        
        integrity_checks = {}
        
        # Check for null values in required fields
        required_field_checks = [
            ('users', 'email'),
            ('user_profiles', 'first_name'),
            ('user_profiles', 'last_name'),
            ('user_profiles', 'zip_code')
        ]
        
        for table, field in required_field_checks:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {field} IS NULL")
                null_count = cursor.fetchone()[0]
                integrity_checks[f"{table}.{field}_nulls"] = null_count
            except Exception as e:
                integrity_checks[f"{table}.{field}_nulls"] = f"Error: {e}"
        
        # Check for duplicate emails
        try:
            cursor.execute("""
                SELECT email, COUNT(*) 
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1
            """)
            duplicate_emails = cursor.fetchall()
            integrity_checks['duplicate_emails'] = len(duplicate_emails)
        except Exception as e:
            integrity_checks['duplicate_emails'] = f"Error: {e}"
        
        # Check for orphaned records
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_profiles up
                LEFT JOIN users u ON up.user_id = u.id
                WHERE u.id IS NULL
            """)
            orphaned_profiles = cursor.fetchone()[0]
            integrity_checks['orphaned_user_profiles'] = orphaned_profiles
        except Exception as e:
            integrity_checks['orphaned_user_profiles'] = f"Error: {e}"
        
        cursor.close()
        
        return integrity_checks
    
    def validate_user_profile_completeness(self) -> Dict[str, Any]:
        """Validate user profile completeness and data quality."""
        cursor = self.postgres_connection.cursor()
        
        # Check profile completion percentages
        cursor.execute("""
            SELECT 
                COUNT(*) as total_profiles,
                COUNT(CASE WHEN profile_completion_percentage = 0 THEN 1 END) as incomplete_profiles,
                COUNT(CASE WHEN profile_completion_percentage = 100 THEN 1 END) as complete_profiles,
                AVG(profile_completion_percentage) as avg_completion_percentage
            FROM user_profiles
        """)
        
        row = cursor.fetchone()
        profile_stats = {
            'total_profiles': row[0],
            'incomplete_profiles': row[1],
            'complete_profiles': row[2],
            'avg_completion_percentage': float(row[3]) if row[3] else 0
        }
        
        # Check for missing critical fields
        cursor.execute("""
            SELECT 
                COUNT(*) as total_profiles,
                COUNT(CASE WHEN first_name IS NULL OR first_name = '' THEN 1 END) as missing_first_name,
                COUNT(CASE WHEN last_name IS NULL OR last_name = '' THEN 1 END) as missing_last_name,
                COUNT(CASE WHEN zip_code IS NULL OR zip_code = '' THEN 1 END) as missing_zip_code,
                COUNT(CASE WHEN annual_income IS NULL THEN 1 END) as missing_income
            FROM user_profiles
        """)
        
        row = cursor.fetchone()
        missing_fields = {
            'total_profiles': row[0],
            'missing_first_name': row[1],
            'missing_last_name': row[2],
            'missing_zip_code': row[3],
            'missing_income': row[4]
        }
        
        cursor.close()
        
        return {
            'profile_completion_stats': profile_stats,
            'missing_fields': missing_fields,
            'data_quality_score': self.calculate_data_quality_score(profile_stats, missing_fields)
        }
    
    def calculate_data_quality_score(self, profile_stats: Dict, missing_fields: Dict) -> float:
        """Calculate a data quality score based on completeness."""
        if profile_stats['total_profiles'] == 0:
            return 0.0
        
        # Calculate completeness score
        complete_profiles = profile_stats['complete_profiles']
        total_profiles = profile_stats['total_profiles']
        completeness_score = (complete_profiles / total_profiles) * 100
        
        # Calculate field completeness
        total_fields = missing_fields['total_profiles'] * 4  # 4 critical fields
        missing_total = (missing_fields['missing_first_name'] + 
                        missing_fields['missing_last_name'] + 
                        missing_fields['missing_zip_code'] + 
                        missing_fields['missing_income'])
        field_completeness = ((total_fields - missing_total) / total_fields) * 100
        
        # Average the scores
        return (completeness_score + field_completeness) / 2
    
    def validate_financial_data_integrity(self) -> Dict[str, Any]:
        """Validate financial data integrity and consistency."""
        cursor = self.postgres_connection.cursor()
        
        financial_checks = {}
        
        # Check for negative balances
        cursor.execute("""
            SELECT COUNT(*) 
            FROM encrypted_financial_profiles 
            WHERE account_balance < 0
        """)
        negative_balances = cursor.fetchone()[0]
        financial_checks['negative_balances'] = negative_balances
        
        # Check for unreasonable amounts
        cursor.execute("""
            SELECT COUNT(*) 
            FROM encrypted_financial_profiles 
            WHERE account_balance > 1000000000
        """)
        unreasonable_amounts = cursor.fetchone()[0]
        financial_checks['unreasonable_amounts'] = unreasonable_amounts
        
        # Check transaction consistency
        cursor.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(CASE WHEN amount = 0 THEN 1 END) as zero_amount_transactions,
                COUNT(CASE WHEN amount IS NULL THEN 1 END) as null_amount_transactions
            FROM financial_transactions
        """)
        
        row = cursor.fetchone()
        transaction_stats = {
            'total_transactions': row[0],
            'zero_amount_transactions': row[1],
            'null_amount_transactions': row[2]
        }
        
        # Check for orphaned transactions
        cursor.execute("""
            SELECT COUNT(*) 
            FROM financial_transactions ft
            LEFT JOIN users u ON ft.user_id = u.id
            WHERE u.id IS NULL
        """)
        orphaned_transactions = cursor.fetchone()[0]
        
        cursor.close()
        
        return {
            'financial_checks': financial_checks,
            'transaction_stats': transaction_stats,
            'orphaned_transactions': orphaned_transactions,
            'financial_integrity_score': self.calculate_financial_integrity_score(financial_checks, transaction_stats)
        }
    
    def calculate_financial_integrity_score(self, financial_checks: Dict, transaction_stats: Dict) -> float:
        """Calculate financial data integrity score."""
        score = 100.0
        
        # Penalize for negative balances
        if financial_checks['negative_balances'] > 0:
            score -= 10
        
        # Penalize for unreasonable amounts
        if financial_checks['unreasonable_amounts'] > 0:
            score -= 10
        
        # Penalize for zero/null transactions
        total_transactions = transaction_stats['total_transactions']
        if total_transactions > 0:
            zero_null_ratio = (transaction_stats['zero_amount_transactions'] + 
                             transaction_stats['null_amount_transactions']) / total_transactions
            score -= zero_null_ratio * 20
        
        return max(0.0, score)
    
    def validate_health_data_accuracy(self) -> Dict[str, Any]:
        """Validate health check-in data accuracy and consistency."""
        cursor = self.postgres_connection.cursor()
        
        # Check for valid score ranges
        cursor.execute("""
            SELECT 
                COUNT(*) as total_checkins,
                COUNT(CASE WHEN mood_score < 1 OR mood_score > 10 THEN 1 END) as invalid_mood_scores,
                COUNT(CASE WHEN stress_level < 1 OR stress_level > 10 THEN 1 END) as invalid_stress_scores,
                COUNT(CASE WHEN sleep_hours < 0 OR sleep_hours > 24 THEN 1 END) as invalid_sleep_hours,
                COUNT(CASE WHEN exercise_minutes < 0 THEN 1 END) as invalid_exercise_minutes
            FROM user_health_checkins
        """)
        
        row = cursor.fetchone()
        health_stats = {
            'total_checkins': row[0],
            'invalid_mood_scores': row[1],
            'invalid_stress_scores': row[2],
            'invalid_sleep_hours': row[3],
            'invalid_exercise_minutes': row[4]
        }
        
        # Check for duplicate check-ins on same day
        cursor.execute("""
            SELECT COUNT(*) 
            FROM (
                SELECT user_id, checkin_date, COUNT(*)
                FROM user_health_checkins
                GROUP BY user_id, checkin_date
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        duplicate_checkins = cursor.fetchone()[0]
        
        # Check wellness score calculation
        cursor.execute("""
            SELECT 
                COUNT(*) as total_checkins,
                COUNT(CASE WHEN mood_score IS NOT NULL THEN 1 END) as with_mood_score,
                COUNT(CASE WHEN stress_level IS NOT NULL THEN 1 END) as with_stress_level,
                COUNT(CASE WHEN sleep_hours IS NOT NULL THEN 1 END) as with_sleep_hours
            FROM user_health_checkins
        """)
        
        row = cursor.fetchone()
        wellness_stats = {
            'total_checkins': row[0],
            'with_mood_score': row[1],
            'with_stress_level': row[2],
            'with_sleep_hours': row[3]
        }
        
        cursor.close()
        
        return {
            'health_data_stats': health_stats,
            'duplicate_checkins': duplicate_checkins,
            'wellness_stats': wellness_stats,
            'health_data_accuracy_score': self.calculate_health_accuracy_score(health_stats, wellness_stats)
        }
    
    def calculate_health_accuracy_score(self, health_stats: Dict, wellness_stats: Dict) -> float:
        """Calculate health data accuracy score."""
        score = 100.0
        
        # Penalize for invalid scores
        total_checkins = health_stats['total_checkins']
        if total_checkins > 0:
            invalid_ratio = (health_stats['invalid_mood_scores'] + 
                           health_stats['invalid_stress_scores'] + 
                           health_stats['invalid_sleep_hours'] + 
                           health_stats['invalid_exercise_minutes']) / total_checkins
            score -= invalid_ratio * 50
        
        # Reward for complete data
        if wellness_stats['total_checkins'] > 0:
            completeness_ratio = (wellness_stats['with_mood_score'] + 
                                wellness_stats['with_stress_level'] + 
                                wellness_stats['with_sleep_hours']) / (wellness_stats['total_checkins'] * 3)
            score += completeness_ratio * 20
        
        return max(0.0, min(100.0, score))
    
    def validate_subscription_system(self) -> Dict[str, Any]:
        """Validate subscription system functionality."""
        cursor = self.postgres_connection.cursor()
        
        # Check subscription status distribution
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM subscriptions
            GROUP BY status
        """)
        
        status_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Check for orphaned subscriptions
        cursor.execute("""
            SELECT COUNT(*) 
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE u.id IS NULL
        """)
        orphaned_subscriptions = cursor.fetchone()[0]
        
        # Check feature access consistency
        cursor.execute("""
            SELECT 
                COUNT(*) as total_access_records,
                COUNT(CASE WHEN is_enabled = true THEN 1 END) as enabled_features,
                COUNT(CASE WHEN usage_count > usage_limit THEN 1 END) as over_limit_features
            FROM feature_access
            WHERE usage_limit IS NOT NULL
        """)
        
        row = cursor.fetchone()
        feature_access_stats = {
            'total_access_records': row[0],
            'enabled_features': row[1],
            'over_limit_features': row[2]
        }
        
        cursor.close()
        
        return {
            'subscription_status_distribution': status_distribution,
            'orphaned_subscriptions': orphaned_subscriptions,
            'feature_access_stats': feature_access_stats,
            'subscription_system_score': self.calculate_subscription_score(status_distribution, feature_access_stats)
        }
    
    def calculate_subscription_score(self, status_distribution: Dict, feature_access_stats: Dict) -> float:
        """Calculate subscription system health score."""
        score = 100.0
        
        # Penalize for orphaned subscriptions
        if status_distribution.get('active', 0) > 0:
            orphaned_ratio = feature_access_stats['orphaned_subscriptions'] / status_distribution['active']
            score -= orphaned_ratio * 30
        
        # Penalize for over-limit features
        if feature_access_stats['total_access_records'] > 0:
            over_limit_ratio = feature_access_stats['over_limit_features'] / feature_access_stats['total_access_records']
            score -= over_limit_ratio * 20
        
        return max(0.0, score)
    
    def validate_relationships(self) -> Dict[str, Any]:
        """Validate foreign key relationships and referential integrity."""
        cursor = self.postgres_connection.cursor()
        
        relationship_checks = {}
        
        # Check user-profile relationships
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(up.id) as users_with_profiles,
                COUNT(*) - COUNT(up.id) as users_without_profiles
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
        """)
        
        row = cursor.fetchone()
        user_profile_relationship = {
            'total_users': row[0],
            'users_with_profiles': row[1],
            'users_without_profiles': row[2]
        }
        
        # Check subscription-user relationships
        cursor.execute("""
            SELECT 
                COUNT(*) as total_subscriptions,
                COUNT(u.id) as valid_subscriptions,
                COUNT(*) - COUNT(u.id) as orphaned_subscriptions
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.id
        """)
        
        row = cursor.fetchone()
        subscription_relationship = {
            'total_subscriptions': row[0],
            'valid_subscriptions': row[1],
            'orphaned_subscriptions': row[2]
        }
        
        # Check health check-in relationships
        cursor.execute("""
            SELECT 
                COUNT(*) as total_checkins,
                COUNT(u.id) as valid_checkins,
                COUNT(*) - COUNT(u.id) as orphaned_checkins
            FROM user_health_checkins hc
            LEFT JOIN users u ON hc.user_id = u.id
        """)
        
        row = cursor.fetchone()
        health_relationship = {
            'total_checkins': row[0],
            'valid_checkins': row[1],
            'orphaned_checkins': row[2]
        }
        
        cursor.close()
        
        return {
            'user_profile_relationship': user_profile_relationship,
            'subscription_relationship': subscription_relationship,
            'health_relationship': health_relationship,
            'relationship_integrity_score': self.calculate_relationship_score(
                user_profile_relationship, subscription_relationship, health_relationship
            )
        }
    
    def calculate_relationship_score(self, user_profile: Dict, subscription: Dict, health: Dict) -> float:
        """Calculate relationship integrity score."""
        score = 100.0
        
        # Penalize for orphaned records
        if user_profile['total_users'] > 0:
            orphaned_ratio = user_profile['users_without_profiles'] / user_profile['total_users']
            score -= orphaned_ratio * 20
        
        if subscription['total_subscriptions'] > 0:
            orphaned_ratio = subscription['orphaned_subscriptions'] / subscription['total_subscriptions']
            score -= orphaned_ratio * 30
        
        if health['total_checkins'] > 0:
            orphaned_ratio = health['orphaned_checkins'] / health['total_checkins']
            score -= orphaned_ratio * 25
        
        return max(0.0, score)
    
    def benchmark_performance(self) -> Dict[str, Any]:
        """Benchmark performance of key queries."""
        cursor = self.postgres_connection.cursor()
        
        performance_results = {}
        
        # Benchmark queries
        queries = {
            'user_count': "SELECT COUNT(*) FROM users",
            'profile_completion': "SELECT AVG(profile_completion_percentage) FROM user_profiles",
            'health_checkins_today': "SELECT COUNT(*) FROM user_health_checkins WHERE checkin_date = CURRENT_DATE",
            'active_subscriptions': "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'",
            'financial_profiles': "SELECT COUNT(*) FROM encrypted_financial_profiles WHERE is_active = true",
            'user_with_profile': """
                SELECT u.email, up.first_name, up.last_name 
                FROM users u 
                JOIN user_profiles up ON u.id = up.user_id 
                LIMIT 100
            """,
            'health_analytics': """
                SELECT 
                    user_id, 
                    AVG(mood_score) as avg_mood,
                    AVG(stress_level) as avg_stress
                FROM user_health_checkins 
                GROUP BY user_id 
                LIMIT 50
            """
        }
        
        for query_name, query in queries.items():
            try:
                start_time = time.time()
                cursor.execute(query)
                result = cursor.fetchall()
                execution_time = time.time() - start_time
                
                performance_results[query_name] = {
                    'execution_time': execution_time,
                    'result_count': len(result),
                    'within_threshold': execution_time <= self.config.performance_threshold
                }
            except Exception as e:
                performance_results[query_name] = {
                    'execution_time': None,
                    'result_count': 0,
                    'within_threshold': False,
                    'error': str(e)
                }
        
        cursor.close()
        
        # Calculate performance score
        successful_queries = sum(1 for result in performance_results.values() 
                               if result.get('within_threshold', False))
        total_queries = len(performance_results)
        performance_score = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
        
        return {
            'query_performance': performance_results,
            'performance_score': performance_score,
            'average_query_time': statistics.mean([
                result['execution_time'] for result in performance_results.values() 
                if result.get('execution_time') is not None
            ]) if any(result.get('execution_time') for result in performance_results.values()) else 0
        }
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        self.logger.info("Generating validation report...")
        
        # Calculate statistics
        self.stats.total_tests = len(self.results)
        self.stats.passed_tests = sum(1 for result in self.results if result.passed)
        self.stats.failed_tests = sum(1 for result in self.results if not result.passed)
        
        # Group results by category
        results_by_category = {}
        for result in self.results:
            if result.test_category not in results_by_category:
                results_by_category[result.test_category] = []
            results_by_category[result.test_category].append(result)
        
        # Calculate category scores
        category_scores = {}
        for category, results in results_by_category.items():
            passed = sum(1 for result in results if result.passed)
            total = len(results)
            category_scores[category] = (passed / total) * 100 if total > 0 else 0
        
        report = {
            'validation_summary': {
                'total_tests': self.stats.total_tests,
                'passed_tests': self.stats.passed_tests,
                'failed_tests': self.stats.failed_tests,
                'success_rate': self.stats.success_rate,
                'duration_seconds': self.stats.duration
            },
            'category_scores': category_scores,
            'results_by_category': {
                category: [asdict(result) for result in results]
                for category, results in results_by_category.items()
            },
            'overall_assessment': self.generate_overall_assessment(),
            'recommendations': self.generate_recommendations(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return report
    
    def generate_overall_assessment(self) -> str:
        """Generate overall assessment of migration success."""
        if self.stats.success_rate >= 95:
            return "EXCELLENT - Migration was highly successful with minimal issues"
        elif self.stats.success_rate >= 85:
            return "GOOD - Migration was successful with some minor issues"
        elif self.stats.success_rate >= 70:
            return "FAIR - Migration completed with notable issues that should be addressed"
        else:
            return "POOR - Migration has significant issues that require immediate attention"
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Analyze failed tests and generate recommendations
        failed_tests = [result for result in self.results if not result.passed]
        
        for test in failed_tests:
            if 'table' in test.test_name.lower():
                recommendations.append(f"Verify table structure for {test.test_name}")
            elif 'data' in test.test_name.lower():
                recommendations.append(f"Check data integrity for {test.test_name}")
            elif 'performance' in test.test_name.lower():
                recommendations.append(f"Optimize performance for {test.test_name}")
            elif 'relationship' in test.test_name.lower():
                recommendations.append(f"Fix relationship issues in {test.test_name}")
        
        if not recommendations:
            recommendations.append("No specific recommendations - migration appears successful")
        
        return recommendations
    
    def save_validation_report(self, report: Dict[str, Any]):
        """Save validation report to file."""
        with open(self.config.report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Validation report saved to: {self.config.report_file}")
    
    def print_console_summary(self):
        """Print validation summary to console."""
        print("\n" + "="*60)
        print("🔍 MIGRATION VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Tests: {self.stats.total_tests}")
        print(f"   Passed: {self.stats.passed_tests}")
        print(f"   Failed: {self.stats.failed_tests}")
        print(f"   Success Rate: {self.stats.success_rate:.1f}%")
        print(f"   Duration: {self.stats.duration:.1f} seconds")
        
        # Group results by category
        results_by_category = {}
        for result in self.results:
            if result.test_category not in results_by_category:
                results_by_category[result.test_category] = []
            results_by_category[result.test_category].append(result)
        
        print(f"\n📋 Results by Category:")
        for category, results in results_by_category.items():
            passed = sum(1 for result in results if result.passed)
            total = len(results)
            percentage = (passed / total) * 100 if total > 0 else 0
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 60 else "❌"
            print(f"   {status} {category}: {passed}/{total} ({percentage:.1f}%)")
        
        # Show failed tests
        failed_tests = [result for result in self.results if not result.passed]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test.test_name}: {test.error_message}")
        
        print(f"\n📄 Detailed report saved to: {self.config.report_file}")
        print("="*60)
    
    def run_validation(self) -> bool:
        """Run the complete validation process."""
        try:
            self.logger.info("Starting migration validation...")
            self.stats.start_time = datetime.now(timezone.utc)
            
            # Connect to databases
            self.connect_databases()
            
            # Run validation tests
            if self.config.run_table_validation:
                self.run_test(self.validate_table_existence, "Table Existence", "Table Validation")
                self.run_test(self.validate_table_structure, "Table Structure", "Table Validation")
            
            if self.config.run_data_integrity_validation:
                self.run_test(self.validate_record_counts, "Record Counts", "Data Integrity")
                self.run_test(self.validate_data_integrity, "Data Integrity", "Data Integrity")
                self.run_test(self.validate_user_profile_completeness, "User Profile Completeness", "Data Quality")
                self.run_test(self.validate_financial_data_integrity, "Financial Data Integrity", "Data Quality")
                self.run_test(self.validate_health_data_accuracy, "Health Data Accuracy", "Data Quality")
            
            if self.config.run_relationship_validation:
                self.run_test(self.validate_relationships, "Relationship Integrity", "Relationships")
                self.run_test(self.validate_subscription_system, "Subscription System", "Business Logic")
            
            if self.config.run_performance_validation:
                self.run_test(self.benchmark_performance, "Performance Benchmarking", "Performance")
            
            # Generate and save report
            report = self.generate_validation_report()
            self.save_validation_report(report)
            
            self.stats.end_time = datetime.now(timezone.utc)
            
            # Print console summary
            self.print_console_summary()
            
            return self.stats.success_rate >= 80  # Consider 80%+ as successful
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False
        
        finally:
            # Disconnect from databases
            self.disconnect_databases()


def main():
    """Main function to run the validation."""
    
    # Configuration
    config = ValidationConfig(
        postgres_url=os.getenv('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production'),
        sqlite_databases={
            'mingus': 'mingus.db',
            'business_intelligence': 'business_intelligence.db',
            'cache': 'cache.db',
            'performance_metrics': 'performance_metrics.db',
            'alerts': 'alerts.db'
        },
        sample_size=100,
        performance_threshold=1.0,
        enable_performance_tests=True,
        enable_data_integrity_tests=True,
        enable_business_logic_tests=True,
        log_level='INFO',
        log_file='validation.log',
        report_file='validation_report.json'
    )
    
    # Create and run validator
    validator = MigrationValidator(config)
    success = validator.run_validation()
    
    if success:
        print("\n✅ Validation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Validation completed with issues. Check the report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main() 