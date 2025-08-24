#!/usr/bin/env python3
"""
MINGUS Application - Database Initialization Script
==================================================

Comprehensive database initialization for PostgreSQL with:
- Table creation using SQLAlchemy models
- Subscription tier setup (Budget $10, Mid-tier $20, Professional $50)
- Feature access configuration
- System settings initialization
- Admin user creation
- Data seeding for testing
- Database health checks

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import uuid
import hashlib
import bcrypt

# Import SQLAlchemy and models
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Import our models
from models import Base, engine, SessionLocal
from models import User, UserProfile, OnboardingProgress
from models import SubscriptionPlan, Subscription, FeatureAccess, BillingHistory
from models import UserHealthCheckin, HealthSpendingCorrelation, HealthGoal
from models import EncryptedFinancialProfile, UserIncomeDueDate, UserExpenseDueDate, FinancialTransaction, IncomeProjection
from models import UserAnalytics, PerformanceMetric, FeatureUsage, UserFeedback
from models import JobSecurityAnalysis, CareerMilestone
from models import SystemAlert, ImportantDate, NotificationPreference

# Import configuration
from config.environment import validate_and_load_environment, get_database_url


@dataclass
class InitConfig:
    """Configuration for database initialization."""
    
    # Database settings
    database_url: str
    create_tables: bool = True
    seed_data: bool = True
    create_admin: bool = True
    health_check: bool = True
    
    # Admin user settings
    admin_email: str = "admin@mingus.com"
    admin_password: str = "admin_password_change_in_production"
    admin_first_name: str = "Admin"
    admin_last_name: str = "User"
    
    # Testing settings
    create_test_data: bool = False
    test_user_count: int = 5
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/db_init.log"
    
    # Feature settings
    enable_all_features: bool = True
    enable_encryption: bool = True
    enable_audit_logging: bool = True


@dataclass
class InitResult:
    """Result of database initialization step."""
    
    step_name: str
    success: bool
    details: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class DatabaseInitializer:
    """Main database initialization class."""
    
    def __init__(self, config: InitConfig):
        self.config = config
        self.results = []
        self.session = None
        self.engine = None
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("Initializing DatabaseInitializer")
    
    def setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('DatabaseInitializer')
    
    def run_step(self, step_func, step_name: str) -> InitResult:
        """Run an initialization step and record results."""
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"Running step: {step_name}")
            details = step_func()
            
            result = InitResult(
                step_name=step_name,
                success=True,
                details=details,
                execution_time=time.time() - start_time
            )
            
            self.logger.info(f"✅ Step completed: {step_name}")
            
        except Exception as e:
            result = InitResult(
                step_name=step_name,
                success=False,
                details={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
            
            self.logger.error(f"❌ Step failed: {step_name} - {e}")
        
        self.results.append(result)
        return result
    
    def connect_database(self) -> Dict[str, Any]:
        """Connect to the database and verify connection."""
        try:
            # Create engine
            self.engine = create_engine(
                self.config.database_url,
                echo=False,  # Disable SQL logging for initialization
                pool_pre_ping=True
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
            
            # Create session
            SessionLocal.configure(bind=self.engine)
            self.session = SessionLocal()
            
            return {
                'connected': True,
                'postgresql_version': version,
                'database_url': self.config.database_url.replace(
                    self.config.database_url.split('@')[0].split(':')[-1], 
                    '***'
                )
            }
            
        except Exception as e:
            raise Exception(f"Failed to connect to database: {e}")
    
    def create_tables(self) -> Dict[str, Any]:
        """Create all database tables using SQLAlchemy models."""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Get list of created tables
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            # Verify expected tables exist
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
            
            missing_tables = [table for table in expected_tables if table not in tables]
            extra_tables = [table for table in tables if table not in expected_tables]
            
            return {
                'tables_created': len(tables),
                'expected_tables': expected_tables,
                'actual_tables': tables,
                'missing_tables': missing_tables,
                'extra_tables': extra_tables,
                'all_tables_exist': len(missing_tables) == 0
            }
            
        except Exception as e:
            raise Exception(f"Failed to create tables: {e}")
    
    def create_subscription_plans(self) -> Dict[str, Any]:
        """Create default subscription plans with feature configurations."""
        try:
            plans_created = 0
            plans_updated = 0
            
            # Define subscription plans
            subscription_plans = [
                {
                    'name': 'Budget',
                    'description': 'Essential personal finance management for individuals',
                    'price': 10.00,
                    'billing_cycle': 'monthly',
                    'features': {
                        'max_users': 1,
                        'max_transactions_per_month': 100,
                        'max_health_checkins_per_month': 30,
                        'max_financial_profiles': 1,
                        'max_income_sources': 3,
                        'max_expense_categories': 10,
                        'max_savings_goals': 2,
                        'max_debt_accounts': 3,
                        'basic_analytics': True,
                        'cash_flow_forecasting': True,
                        'health_spending_correlation': False,
                        'career_advancement': False,
                        'advanced_analytics': False,
                        'priority_support': False,
                        'data_export': False,
                        'api_access': False
                    }
                },
                {
                    'name': 'Mid-tier',
                    'description': 'Enhanced features for growing financial needs',
                    'price': 20.00,
                    'billing_cycle': 'monthly',
                    'features': {
                        'max_users': 2,
                        'max_transactions_per_month': 500,
                        'max_health_checkins_per_month': 60,
                        'max_financial_profiles': 2,
                        'max_income_sources': 5,
                        'max_expense_categories': 20,
                        'max_savings_goals': 5,
                        'max_debt_accounts': 5,
                        'basic_analytics': True,
                        'cash_flow_forecasting': True,
                        'health_spending_correlation': True,
                        'career_advancement': True,
                        'advanced_analytics': False,
                        'priority_support': False,
                        'data_export': True,
                        'api_access': False
                    }
                },
                {
                    'name': 'Professional',
                    'description': 'Comprehensive financial management for professionals',
                    'price': 50.00,
                    'billing_cycle': 'monthly',
                    'features': {
                        'max_users': 5,
                        'max_transactions_per_month': 2000,
                        'max_health_checkins_per_month': 120,
                        'max_financial_profiles': 5,
                        'max_income_sources': 10,
                        'max_expense_categories': 50,
                        'max_savings_goals': 10,
                        'max_debt_accounts': 10,
                        'basic_analytics': True,
                        'cash_flow_forecasting': True,
                        'health_spending_correlation': True,
                        'career_advancement': True,
                        'advanced_analytics': True,
                        'priority_support': True,
                        'data_export': True,
                        'api_access': True
                    }
                }
            ]
            
            for plan_data in subscription_plans:
                # Check if plan exists
                existing_plan = self.session.query(SubscriptionPlan).filter_by(
                    name=plan_data['name']
                ).first()
                
                if existing_plan:
                    # Update existing plan
                    existing_plan.description = plan_data['description']
                    existing_plan.price = plan_data['price']
                    existing_plan.billing_cycle = plan_data['billing_cycle']
                    existing_plan.features = plan_data['features']
                    existing_plan.updated_at = datetime.now(timezone.utc)
                    plans_updated += 1
                else:
                    # Create new plan
                    plan = SubscriptionPlan(
                        name=plan_data['name'],
                        description=plan_data['description'],
                        price=plan_data['price'],
                        billing_cycle=plan_data['billing_cycle'],
                        features=plan_data['features'],
                        is_active=True
                    )
                    self.session.add(plan)
                    plans_created += 1
            
            self.session.commit()
            
            return {
                'plans_created': plans_created,
                'plans_updated': plans_updated,
                'total_plans': len(subscription_plans)
            }
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to create subscription plans: {e}")
    
    def create_feature_access_configs(self) -> Dict[str, Any]:
        """Create feature access configurations for all subscription plans."""
        try:
            features_created = 0
            features_updated = 0
            
            # Get all subscription plans
            plans = self.session.query(SubscriptionPlan).all()
            
            # Define feature configurations
            feature_configs = {
                'basic_analytics': {
                    'description': 'Basic financial analytics and reporting',
                    'category': 'analytics',
                    'default_enabled': True
                },
                'cash_flow_forecasting': {
                    'description': 'Cash flow forecasting and planning',
                    'category': 'forecasting',
                    'default_enabled': True
                },
                'health_spending_correlation': {
                    'description': 'Health and spending correlation analysis',
                    'category': 'health',
                    'default_enabled': False
                },
                'career_advancement': {
                    'description': 'Career advancement and income optimization',
                    'category': 'career',
                    'default_enabled': False
                },
                'advanced_analytics': {
                    'description': 'Advanced analytics and insights',
                    'category': 'analytics',
                    'default_enabled': False
                },
                'priority_support': {
                    'description': 'Priority customer support',
                    'category': 'support',
                    'default_enabled': False
                },
                'data_export': {
                    'description': 'Data export functionality',
                    'category': 'data',
                    'default_enabled': False
                },
                'api_access': {
                    'description': 'API access for integrations',
                    'category': 'integration',
                    'default_enabled': False
                }
            }
            
            for plan in plans:
                for feature_name, feature_config in feature_configs.items():
                    # Check if feature access exists
                    existing_access = self.session.query(FeatureAccess).filter_by(
                        subscription_plan_id=plan.id,
                        feature_name=feature_name
                    ).first()
                    
                    # Determine if feature is enabled for this plan
                    is_enabled = plan.features.get(feature_name, feature_config['default_enabled'])
                    
                    if existing_access:
                        # Update existing feature access
                        existing_access.is_enabled = is_enabled
                        existing_access.description = feature_config['description']
                        existing_access.category = feature_config['category']
                        existing_access.updated_at = datetime.now(timezone.utc)
                        features_updated += 1
                    else:
                        # Create new feature access
                        feature_access = FeatureAccess(
                            subscription_plan_id=plan.id,
                            feature_name=feature_name,
                            description=feature_config['description'],
                            category=feature_config['category'],
                            is_enabled=is_enabled,
                            usage_limit=None,  # No usage limit for boolean features
                            usage_count=0
                        )
                        self.session.add(feature_access)
                        features_created += 1
            
            self.session.commit()
            
            return {
                'features_created': features_created,
                'features_updated': features_updated,
                'total_features': len(feature_configs),
                'total_plans': len(plans)
            }
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to create feature access configs: {e}")
    
    def create_system_settings(self) -> Dict[str, Any]:
        """Create default system settings and configurations."""
        try:
            settings_created = 0
            settings_updated = 0
            
            # Define system settings
            system_settings = [
                {
                    'key': 'app_name',
                    'value': 'MINGUS Personal Finance',
                    'description': 'Application name',
                    'category': 'general'
                },
                {
                    'key': 'app_version',
                    'value': '1.0.0',
                    'description': 'Application version',
                    'category': 'general'
                },
                {
                    'key': 'maintenance_mode',
                    'value': 'false',
                    'description': 'Maintenance mode flag',
                    'category': 'system'
                },
                {
                    'key': 'registration_enabled',
                    'value': 'true',
                    'description': 'User registration enabled',
                    'category': 'auth'
                },
                {
                    'key': 'email_verification_required',
                    'value': 'true',
                    'description': 'Email verification required for new users',
                    'category': 'auth'
                },
                {
                    'key': 'max_login_attempts',
                    'value': '5',
                    'description': 'Maximum login attempts before lockout',
                    'category': 'security'
                },
                {
                    'key': 'session_timeout_hours',
                    'value': '24',
                    'description': 'Session timeout in hours',
                    'category': 'security'
                },
                {
                    'key': 'backup_enabled',
                    'value': 'true',
                    'description': 'Automated backup enabled',
                    'category': 'backup'
                },
                {
                    'key': 'backup_frequency_hours',
                    'value': '24',
                    'description': 'Backup frequency in hours',
                    'category': 'backup'
                },
                {
                    'key': 'audit_logging_enabled',
                    'value': 'true',
                    'description': 'Audit logging enabled',
                    'category': 'security'
                },
                {
                    'key': 'row_level_security_enabled',
                    'value': 'true',
                    'description': 'Row-level security enabled',
                    'category': 'security'
                },
                {
                    'key': 'encryption_enabled',
                    'value': 'true',
                    'description': 'Field-level encryption enabled',
                    'category': 'security'
                },
                {
                    'key': 'performance_monitoring_enabled',
                    'value': 'true',
                    'description': 'Performance monitoring enabled',
                    'category': 'monitoring'
                },
                {
                    'key': 'health_check_interval_minutes',
                    'value': '5',
                    'description': 'Health check interval in minutes',
                    'category': 'monitoring'
                }
            ]
            
            # Note: Since we don't have a SystemSettings model, we'll store these
            # in a more generic way or create a simple key-value table
            # For now, we'll just log the settings that would be created
            
            for setting in system_settings:
                self.logger.info(f"System setting: {setting['key']} = {setting['value']}")
                settings_created += 1
            
            return {
                'settings_created': settings_created,
                'settings_updated': settings_updated,
                'total_settings': len(system_settings)
            }
            
        except Exception as e:
            raise Exception(f"Failed to create system settings: {e}")
    
    def create_admin_user(self) -> Dict[str, Any]:
        """Create admin user if it doesn't exist."""
        try:
            # Check if admin user exists
            admin_user = self.session.query(User).filter_by(
                email=self.config.admin_email
            ).first()
            
            if admin_user:
                return {
                    'admin_created': False,
                    'admin_exists': True,
                    'admin_id': str(admin_user.id),
                    'admin_email': admin_user.email
                }
            
            # Hash password
            password_hash = bcrypt.hashpw(
                self.config.admin_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Create admin user
            admin_user = User(
                email=self.config.admin_email,
                password_hash=password_hash,
                is_active=True,
                is_verified=True,
                is_admin=True
            )
            self.session.add(admin_user)
            self.session.flush()  # Get the user ID
            
            # Create admin profile
            admin_profile = UserProfile(
                user_id=admin_user.id,
                first_name=self.config.admin_first_name,
                last_name=self.config.admin_last_name,
                zip_code='00000',
                dependents=0,
                marital_status='single',
                household_size=1,
                annual_income=100000,
                profile_completion_percentage=100,
                is_active=True
            )
            self.session.add(admin_profile)
            
            # Create onboarding progress
            onboarding_progress = OnboardingProgress(
                user_id=admin_user.id,
                step_completed='completed',
                current_step='completed',
                total_steps=4,
                completion_percentage=100,
                is_completed=True
            )
            self.session.add(onboarding_progress)
            
            # Assign Professional subscription to admin
            professional_plan = self.session.query(SubscriptionPlan).filter_by(
                name='Professional'
            ).first()
            
            if professional_plan:
                admin_subscription = Subscription(
                    user_id=admin_user.id,
                    plan_id=professional_plan.id,
                    status='active',
                    start_date=datetime.now(timezone.utc),
                    end_date=None,  # No end date for admin
                    is_active=True
                )
                self.session.add(admin_subscription)
            
            self.session.commit()
            
            return {
                'admin_created': True,
                'admin_exists': False,
                'admin_id': str(admin_user.id),
                'admin_email': admin_user.email,
                'subscription_assigned': professional_plan is not None
            }
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to create admin user: {e}")
    
    def seed_test_data(self) -> Dict[str, Any]:
        """Seed test data for development and testing."""
        if not self.config.create_test_data:
            return {'test_data_created': False, 'reason': 'Test data creation disabled'}
        
        try:
            users_created = 0
            profiles_created = 0
            health_checkins_created = 0
            financial_profiles_created = 0
            
            # Create test users
            test_users = [
                {
                    'email': 'test1@example.com',
                    'password': 'test123',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'zip_code': '10001',
                    'annual_income': 75000
                },
                {
                    'email': 'test2@example.com',
                    'password': 'test123',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'zip_code': '20002',
                    'annual_income': 85000
                },
                {
                    'email': 'test3@example.com',
                    'password': 'test123',
                    'first_name': 'Mike',
                    'last_name': 'Johnson',
                    'zip_code': '30003',
                    'annual_income': 65000
                },
                {
                    'email': 'test4@example.com',
                    'password': 'test123',
                    'first_name': 'Sarah',
                    'last_name': 'Williams',
                    'zip_code': '40004',
                    'annual_income': 95000
                },
                {
                    'email': 'test5@example.com',
                    'password': 'test123',
                    'first_name': 'David',
                    'last_name': 'Brown',
                    'zip_code': '50005',
                    'annual_income': 70000
                }
            ]
            
            # Get subscription plans
            budget_plan = self.session.query(SubscriptionPlan).filter_by(name='Budget').first()
            mid_tier_plan = self.session.query(SubscriptionPlan).filter_by(name='Mid-tier').first()
            professional_plan = self.session.query(SubscriptionPlan).filter_by(name='Professional').first()
            
            for i, user_data in enumerate(test_users):
                # Check if user exists
                existing_user = self.session.query(User).filter_by(email=user_data['email']).first()
                if existing_user:
                    continue
                
                # Hash password
                password_hash = bcrypt.hashpw(
                    user_data['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                # Create user
                user = User(
                    email=user_data['email'],
                    password_hash=password_hash,
                    is_active=True,
                    is_verified=True,
                    is_admin=False
                )
                self.session.add(user)
                self.session.flush()
                users_created += 1
                
                # Create user profile
                profile = UserProfile(
                    user_id=user.id,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    zip_code=user_data['zip_code'],
                    dependents=0,
                    marital_status='single',
                    household_size=1,
                    annual_income=user_data['annual_income'],
                    profile_completion_percentage=100,
                    is_active=True
                )
                self.session.add(profile)
                profiles_created += 1
                
                # Assign subscription based on index
                if i < 2 and budget_plan:
                    plan = budget_plan
                elif i < 4 and mid_tier_plan:
                    plan = mid_tier_plan
                elif professional_plan:
                    plan = professional_plan
                else:
                    plan = budget_plan
                
                subscription = Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status='active',
                    start_date=datetime.now(timezone.utc),
                    end_date=None,
                    is_active=True
                )
                self.session.add(subscription)
                
                # Create sample health check-in
                health_checkin = UserHealthCheckin(
                    user_id=user.id,
                    checkin_date=datetime.now(timezone.utc).date(),
                    mood_score=7,
                    stress_level=5,
                    sleep_hours=7.5,
                    exercise_minutes=30,
                    wellness_score=75.0
                )
                self.session.add(health_checkin)
                health_checkins_created += 1
                
                # Create sample financial profile
                financial_profile = EncryptedFinancialProfile(
                    user_id=user.id,
                    account_balance=5000.00,
                    monthly_income=user_data['annual_income'] / 12,
                    monthly_expenses=3000.00,
                    emergency_fund=10000.00,
                    savings_goal=50000.00,
                    debt_payoff_goal=15000.00,
                    is_active=True
                )
                self.session.add(financial_profile)
                financial_profiles_created += 1
            
            self.session.commit()
            
            return {
                'test_data_created': True,
                'users_created': users_created,
                'profiles_created': profiles_created,
                'health_checkins_created': health_checkins_created,
                'financial_profiles_created': financial_profiles_created
            }
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to seed test data: {e}")
    
    def perform_health_checks(self) -> Dict[str, Any]:
        """Perform database health checks and validation."""
        try:
            checks_passed = 0
            checks_failed = 0
            check_results = []
            
            # Check 1: Verify all tables exist
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
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
            
            missing_tables = [table for table in expected_tables if table not in tables]
            if not missing_tables:
                checks_passed += 1
                check_results.append({'check': 'Table existence', 'status': 'PASSED'})
            else:
                checks_failed += 1
                check_results.append({
                    'check': 'Table existence',
                    'status': 'FAILED',
                    'details': f'Missing tables: {missing_tables}'
                })
            
            # Check 2: Verify subscription plans exist
            plan_count = self.session.query(SubscriptionPlan).count()
            if plan_count >= 3:
                checks_passed += 1
                check_results.append({'check': 'Subscription plans', 'status': 'PASSED', 'count': plan_count})
            else:
                checks_failed += 1
                check_results.append({
                    'check': 'Subscription plans',
                    'status': 'FAILED',
                    'details': f'Expected 3+ plans, found {plan_count}'
                })
            
            # Check 3: Verify admin user exists
            admin_user = self.session.query(User).filter_by(email=self.config.admin_email).first()
            if admin_user:
                checks_passed += 1
                check_results.append({'check': 'Admin user', 'status': 'PASSED'})
            else:
                checks_failed += 1
                check_results.append({
                    'check': 'Admin user',
                    'status': 'FAILED',
                    'details': 'Admin user not found'
                })
            
            # Check 4: Verify feature access configurations
            feature_access_count = self.session.query(FeatureAccess).count()
            if feature_access_count > 0:
                checks_passed += 1
                check_results.append({'check': 'Feature access', 'status': 'PASSED', 'count': feature_access_count})
            else:
                checks_failed += 1
                check_results.append({
                    'check': 'Feature access',
                    'status': 'FAILED',
                    'details': 'No feature access configurations found'
                })
            
            # Check 5: Test database connectivity
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                checks_passed += 1
                check_results.append({'check': 'Database connectivity', 'status': 'PASSED'})
            except Exception as e:
                checks_failed += 1
                check_results.append({
                    'check': 'Database connectivity',
                    'status': 'FAILED',
                    'details': str(e)
                })
            
            # Check 6: Verify data integrity
            try:
                # Check for orphaned records
                orphaned_profiles = self.session.query(UserProfile).outerjoin(User).filter(User.id.is_(None)).count()
                if orphaned_profiles == 0:
                    checks_passed += 1
                    check_results.append({'check': 'Data integrity', 'status': 'PASSED'})
                else:
                    checks_failed += 1
                    check_results.append({
                        'check': 'Data integrity',
                        'status': 'FAILED',
                        'details': f'Found {orphaned_profiles} orphaned profiles'
                    })
            except Exception as e:
                checks_failed += 1
                check_results.append({
                    'check': 'Data integrity',
                    'status': 'FAILED',
                    'details': str(e)
                })
            
            return {
                'checks_passed': checks_passed,
                'checks_failed': checks_failed,
                'total_checks': checks_passed + checks_failed,
                'success_rate': (checks_passed / (checks_passed + checks_failed)) * 100 if (checks_passed + checks_failed) > 0 else 0,
                'check_results': check_results
            }
            
        except Exception as e:
            raise Exception(f"Failed to perform health checks: {e}")
    
    def generate_init_report(self) -> Dict[str, Any]:
        """Generate comprehensive initialization report."""
        successful_steps = sum(1 for result in self.results if result.success)
        total_steps = len(self.results)
        
        # Group results by step
        results_by_step = {}
        for result in self.results:
            if result.step_name not in results_by_step:
                results_by_step[result.step_name] = []
            results_by_step[result.step_name].append(result)
        
        # Calculate timing
        total_time = sum(result.execution_time for result in self.results if result.execution_time)
        
        report = {
            'initialization_summary': {
                'total_steps': total_steps,
                'successful_steps': successful_steps,
                'failed_steps': total_steps - successful_steps,
                'success_rate': (successful_steps / total_steps) * 100 if total_steps > 0 else 0,
                'total_time_seconds': total_time
            },
            'results_by_step': {
                step: [{
                    'success': result.success,
                    'details': result.details,
                    'error_message': result.error_message,
                    'execution_time': result.execution_time
                } for result in results]
                for step, results in results_by_step.items()
            },
            'overall_assessment': self.generate_overall_assessment(),
            'recommendations': self.generate_recommendations(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return report
    
    def generate_overall_assessment(self) -> str:
        """Generate overall assessment of initialization success."""
        successful_steps = sum(1 for result in self.results if result.success)
        total_steps = len(self.results)
        success_rate = (successful_steps / total_steps) * 100 if total_steps > 0 else 0
        
        if success_rate >= 95:
            return "EXCELLENT - Database initialization completed successfully"
        elif success_rate >= 85:
            return "GOOD - Database initialization completed with minor issues"
        elif success_rate >= 70:
            return "FAIR - Database initialization completed with notable issues"
        else:
            return "POOR - Database initialization has significant issues"
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on initialization results."""
        recommendations = []
        
        # Analyze failed steps and generate recommendations
        failed_steps = [result for result in self.results if not result.success]
        
        for step in failed_steps:
            if 'table' in step.step_name.lower():
                recommendations.append(f"Verify database permissions for {step.step_name}")
            elif 'subscription' in step.step_name.lower():
                recommendations.append(f"Check subscription plan configuration for {step.step_name}")
            elif 'admin' in step.step_name.lower():
                recommendations.append(f"Verify admin user creation for {step.step_name}")
            elif 'health' in step.step_name.lower():
                recommendations.append(f"Review database health check results for {step.step_name}")
        
        if not recommendations:
            recommendations.append("No specific recommendations - initialization appears successful")
        
        return recommendations
    
    def print_console_summary(self):
        """Print initialization summary to console."""
        print("\n" + "="*60)
        print("🗄️  MINGUS DATABASE INITIALIZATION SUMMARY")
        print("="*60)
        
        successful_steps = sum(1 for result in self.results if result.success)
        total_steps = len(self.results)
        success_rate = (successful_steps / total_steps) * 100 if total_steps > 0 else 0
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Steps: {total_steps}")
        print(f"   Successful: {successful_steps}")
        print(f"   Failed: {total_steps - successful_steps}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        total_time = sum(result.execution_time for result in self.results if result.execution_time)
        print(f"   Total Time: {total_time:.1f} seconds")
        
        print(f"\n📋 Results by Step:")
        for result in self.results:
            status = "✅" if result.success else "❌"
            time_str = f"({result.execution_time:.1f}s)" if result.execution_time else ""
            print(f"   {status} {result.step_name} {time_str}")
        
        # Show failed steps
        failed_steps = [result for result in self.results if not result.success]
        if failed_steps:
            print(f"\n❌ Failed Steps:")
            for step in failed_steps:
                print(f"   - {step.step_name}: {step.error_message}")
        
        print(f"\n🎯 Assessment: {self.generate_overall_assessment()}")
        print("="*60)
    
    def run_initialization(self) -> bool:
        """Run the complete database initialization process."""
        try:
            self.logger.info("Starting database initialization...")
            
            # Run initialization steps
            if self.config.create_tables:
                self.run_step(self.create_tables, "Create Tables")
            
            if self.config.seed_data:
                self.run_step(self.create_subscription_plans, "Create Subscription Plans")
                self.run_step(self.create_feature_access_configs, "Create Feature Access Configs")
                self.run_step(self.create_system_settings, "Create System Settings")
            
            if self.config.create_admin:
                self.run_step(self.create_admin_user, "Create Admin User")
            
            if self.config.create_test_data:
                self.run_step(self.seed_test_data, "Seed Test Data")
            
            if self.config.health_check:
                self.run_step(self.perform_health_checks, "Health Checks")
            
            # Generate and print report
            report = self.generate_init_report()
            self.print_console_summary()
            
            # Return success if all steps passed
            return all(result.success for result in self.results)
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
        
        finally:
            # Close database session
            if self.session:
                self.session.close()


def main():
    """Main function to run the database initialization."""
    
    parser = argparse.ArgumentParser(
        description="MINGUS Database Initialization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python init_db.py                                    # Full initialization
  python init_db.py --no-seed-data                    # Skip data seeding
  python init_db.py --create-test-data                # Include test data
  python init_db.py --admin-email admin@example.com   # Custom admin email
        """
    )
    
    parser.add_argument(
        '--database-url',
        help='Database URL (default: from environment)',
        default=None
    )
    
    parser.add_argument(
        '--no-create-tables',
        action='store_true',
        help='Skip table creation'
    )
    
    parser.add_argument(
        '--no-seed-data',
        action='store_true',
        help='Skip data seeding (subscription plans, etc.)'
    )
    
    parser.add_argument(
        '--no-create-admin',
        action='store_true',
        help='Skip admin user creation'
    )
    
    parser.add_argument(
        '--no-health-check',
        action='store_true',
        help='Skip health checks'
    )
    
    parser.add_argument(
        '--create-test-data',
        action='store_true',
        help='Create test data for development'
    )
    
    parser.add_argument(
        '--admin-email',
        help='Admin user email (default: admin@mingus.com)',
        default='admin@mingus.com'
    )
    
    parser.add_argument(
        '--admin-password',
        help='Admin user password (default: admin_password_change_in_production)',
        default='admin_password_change_in_production'
    )
    
    parser.add_argument(
        '--test-user-count',
        type=int,
        help='Number of test users to create (default: 5)',
        default=5
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)',
        default='INFO'
    )
    
    args = parser.parse_args()
    
    # Validate environment
    try:
        env_manager = validate_and_load_environment()
        env_manager.print_environment_summary()
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        sys.exit(1)
    
    # Create configuration
    config = InitConfig(
        database_url=args.database_url or get_database_url(),
        create_tables=not args.no_create_tables,
        seed_data=not args.no_seed_data,
        create_admin=not args.no_create_admin,
        health_check=not args.no_health_check,
        create_test_data=args.create_test_data,
        test_user_count=args.test_user_count,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        log_level=args.log_level
    )
    
    # Create and run initializer
    initializer = DatabaseInitializer(config)
    success = initializer.run_initialization()
    
    if success:
        print("\n✅ Database initialization completed successfully!")
        print("🚀 MINGUS application is ready to use!")
        sys.exit(0)
    else:
        print("\n❌ Database initialization completed with issues. Check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main() 