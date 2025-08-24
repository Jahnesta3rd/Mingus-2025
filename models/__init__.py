"""
MINGUS Application - SQLAlchemy Models Package
==============================================

This package contains all SQLAlchemy models for the MINGUS personal finance
application, corresponding to the unified PostgreSQL schema.

Models are organized by functionality:
- user.py: User management and profiles
- subscription.py: Subscription and billing system
- health.py: Health tracking and correlations
- financial.py: Financial data and transactions
- analytics.py: Analytics and performance metrics

Author: MINGUS Development Team
Date: January 2025
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production')

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv('SQLALCHEMY_ECHO', 'false').lower() == 'true'
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
db_session = scoped_session(SessionLocal)

# Import all models to ensure they are registered with the Base
from .user import User, UserProfile, OnboardingProgress
from .subscription import SubscriptionPlan, Subscription, FeatureAccess, BillingHistory
from .health import UserHealthCheckin, HealthSpendingCorrelation, HealthGoal
from .financial import EncryptedFinancialProfile, UserIncomeDueDate, UserExpenseDueDate, FinancialTransaction, IncomeProjection
from .analytics import UserAnalytics, PerformanceMetric, FeatureUsage, UserFeedback
from .career import JobSecurityAnalysis, CareerMilestone
from .system import SystemAlert, ImportantDate, NotificationPreference

# Create all tables
def create_all_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

# Drop all tables (use with caution)
def drop_all_tables():
    """Drop all database tables."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        raise

# Database session management
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Model registry for easy access
__all__ = [
    # Base
    'Base',
    'engine',
    'SessionLocal',
    'db_session',
    'create_all_tables',
    'drop_all_tables',
    'get_db',
    
    # User models
    'User',
    'UserProfile',
    'OnboardingProgress',
    
    # Subscription models
    'SubscriptionPlan',
    'Subscription',
    'FeatureAccess',
    'BillingHistory',
    
    # Health models
    'UserHealthCheckin',
    'HealthSpendingCorrelation',
    'HealthGoal',
    
    # Financial models
    'EncryptedFinancialProfile',
    'UserIncomeDueDate',
    'UserExpenseDueDate',
    'FinancialTransaction',
    'IncomeProjection',
    
    # Analytics models
    'UserAnalytics',
    'PerformanceMetric',
    'FeatureUsage',
    'UserFeedback',
    
    # Career models
    'JobSecurityAnalysis',
    'CareerMilestone',
    
    # System models
    'SystemAlert',
    'ImportantDate',
    'NotificationPreference',
] 