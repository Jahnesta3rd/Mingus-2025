#!/usr/bin/env python3
"""
Script to apply user profile migrations using SQLite for development
This will set up the database with all required user profile fields
"""

import os
import sqlite3
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sqlite_database():
    """Create SQLite database with user profile tables"""
    try:
        # Create database directory if it doesn't exist
        os.makedirs('instance', exist_ok=True)
        
        # Connect to SQLite database
        db_path = 'instance/mingus.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info(f"Creating SQLite database at {db_path}")
        
        # Create users table with comprehensive profile fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Personal Information
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                date_of_birth DATE,
                gender VARCHAR(20),
                phone_number VARCHAR(20),
                
                -- Address Information
                zip_code VARCHAR(10),
                city VARCHAR(100),
                state VARCHAR(50),
                country VARCHAR(100) DEFAULT 'USA',
                timezone VARCHAR(50) DEFAULT 'America/New_York',
                
                -- Family Information
                dependents INTEGER DEFAULT 0,
                marital_status VARCHAR(20),
                household_size INTEGER DEFAULT 1,
                
                -- Financial Information
                monthly_income DECIMAL(10,2),
                income_frequency VARCHAR(20),
                primary_income_source VARCHAR(100),
                current_savings_balance DECIMAL(10,2),
                total_debt_amount DECIMAL(10,2),
                credit_score_range VARCHAR(20),
                employment_status VARCHAR(50),
                
                -- Employment Information
                education_level VARCHAR(100),
                occupation VARCHAR(100),
                industry VARCHAR(100),
                years_of_experience INTEGER,
                company_name VARCHAR(255),
                company_size VARCHAR(50),
                job_title VARCHAR(100),
                naics_code VARCHAR(10),
                
                -- Goals and Preferences
                primary_financial_goal VARCHAR(100),
                risk_tolerance_level VARCHAR(20),
                financial_knowledge_level VARCHAR(20),
                preferred_contact_method VARCHAR(50),
                notification_preferences TEXT,
                
                -- Health and Wellness
                health_checkin_frequency VARCHAR(20),
                stress_level_baseline INTEGER,
                wellness_goals TEXT,
                
                -- Compliance and Preferences
                gdpr_consent_status BOOLEAN DEFAULT FALSE,
                data_sharing_preferences VARCHAR(100),
                profile_completion_percentage DECIMAL(5,2) DEFAULT 0.00,
                onboarding_step INTEGER DEFAULT 1,
                
                -- Verification
                email_verification_status BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Create user_profiles table (for additional profile data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                date_of_birth DATE,
                gender VARCHAR(20),
                phone_number VARCHAR(20),
                address_line_1 VARCHAR(255),
                address_line_2 VARCHAR(255),
                city VARCHAR(100),
                state VARCHAR(50),
                zip_code VARCHAR(10) NOT NULL,
                country VARCHAR(100) DEFAULT 'USA',
                timezone VARCHAR(50) DEFAULT 'America/New_York',
                dependents INTEGER DEFAULT 0,
                marital_status VARCHAR(20),
                household_size INTEGER DEFAULT 1,
                annual_income DECIMAL(12,2),
                income_source VARCHAR(100),
                employment_status VARCHAR(50),
                education_level VARCHAR(50),
                occupation VARCHAR(100),
                industry VARCHAR(100),
                years_of_experience INTEGER,
                company_name VARCHAR(255),
                company_size VARCHAR(50),
                job_title VARCHAR(100),
                naics_code VARCHAR(10),
                risk_tolerance VARCHAR(20) DEFAULT 'moderate',
                financial_goals TEXT,
                preferences TEXT,
                profile_completion_percentage INTEGER DEFAULT 0,
                onboarding_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Create onboarding progress tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS onboarding_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                step_name VARCHAR(100) NOT NULL,
                step_order INTEGER NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                step_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, step_name)
            )
        ''')
        
        # Create subscription plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                billing_cycle VARCHAR(20) NOT NULL,
                features TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL,
                current_period_start TIMESTAMP NOT NULL,
                current_period_end TIMESTAMP NOT NULL,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                cancelled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
            )
        ''')
        
        # Create feature usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER NOT NULL,
                feature_name VARCHAR(100) NOT NULL,
                usage_count INTEGER DEFAULT 0,
                usage_month INTEGER NOT NULL,
                usage_year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE,
                UNIQUE(subscription_id, feature_name, usage_month, usage_year)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_zip_code ON users(zip_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_industry ON users(industry)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_profile_completion ON users(profile_completion_percentage)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_onboarding_progress_user_id ON onboarding_progress(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_usage_subscription_id ON feature_usage(subscription_id)')
        
        # Insert default subscription plans
        cursor.execute('''
            INSERT OR IGNORE INTO subscription_plans (id, name, description, price, billing_cycle, features) VALUES
            (1, 'Budget', 'Essential financial planning for individuals', 10.00, 'monthly', '["basic_health_checkins", "financial_reports", "email_support"]'),
            (2, 'Mid-Tier', 'Advanced features for growing professionals', 20.00, 'monthly', '["unlimited_health_checkins", "ai_insights", "career_risk_management", "priority_support"]'),
            (3, 'Professional', 'Comprehensive solution for executives', 50.00, 'monthly', '["team_management", "dedicated_account_manager", "api_access", "custom_reports"]')
        ''')
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info("✅ Database created successfully with all user profile tables!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False

def create_sample_user():
    """Create a sample user for testing"""
    try:
        conn = sqlite3.connect('instance/mingus.db')
        cursor = conn.cursor()
        
        # Check if sample user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', ('test@mingus.com',))
        if cursor.fetchone():
            logger.info("Sample user already exists")
            conn.close()
            return True
        
        # Create sample user with complete profile
        cursor.execute('''
            INSERT INTO users (
                email, first_name, last_name, zip_code, dependents, 
                marital_status, industry, job_title, naics_code,
                monthly_income, employment_status, profile_completion_percentage,
                onboarding_step, email_verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'test@mingus.com',
            'John',
            'Doe',
            '30301',
            2,
            'married',
            'Technology',
            'Software Engineer',
            '511210',
            7500.00,
            'employed',
            85.0,
            5,
            True
        ))
        
        user_id = cursor.lastrowid
        
        # Create corresponding user profile
        cursor.execute('''
            INSERT INTO user_profiles (
                user_id, first_name, last_name, zip_code, dependents,
                marital_status, industry, job_title, naics_code,
                annual_income, employment_status, profile_completion_percentage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            'John',
            'Doe',
            '30301',
            2,
            'married',
            'Technology',
            'Software Engineer',
            '511210',
            90000.00,
            'employed',
            85
        ))
        
        # Create subscription for sample user
        cursor.execute('''
            INSERT INTO subscriptions (
                user_id, plan_id, status, current_period_start, current_period_end
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            2,  # Mid-Tier plan
            'active',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Sample user created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create sample user: {e}")
        return False

def verify_database_setup():
    """Verify that all tables and sample data are properly set up"""
    try:
        conn = sqlite3.connect('instance/mingus.db')
        cursor = conn.cursor()
        
        # Check tables exist
        tables = ['users', 'user_profiles', 'onboarding_progress', 'subscription_plans', 'subscriptions', 'feature_usage']
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                logger.error(f"❌ Table {table} not found!")
                return False
            else:
                logger.info(f"✅ Table {table} exists")
        
        # Check sample user
        cursor.execute('SELECT id, email, first_name, last_name, profile_completion_percentage FROM users WHERE email = ?', ('test@mingus.com',))
        user = cursor.fetchone()
        if user:
            logger.info(f"✅ Sample user found: {user[2]} {user[3]} (ID: {user[0]}, Completion: {user[4]}%)")
        else:
            logger.warning("⚠️ Sample user not found")
        
        # Check subscription plans
        cursor.execute('SELECT name, price, billing_cycle FROM subscription_plans')
        plans = cursor.fetchall()
        logger.info(f"✅ Found {len(plans)} subscription plans:")
        for plan in plans:
            logger.info(f"   - {plan[0]}: ${plan[1]} ({plan[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main function to set up the database"""
    logger.info("🚀 Starting user profile database setup...")
    
    # Step 1: Create database and tables
    if not create_sqlite_database():
        logger.error("Failed to create database")
        return
    
    # Step 2: Create sample user
    if not create_sample_user():
        logger.error("Failed to create sample user")
        return
    
    # Step 3: Verify setup
    if not verify_database_setup():
        logger.error("Database verification failed")
        return
    
    logger.info("🎉 User profile database setup completed successfully!")
    logger.info("📊 Database location: instance/mingus.db")
    logger.info("👤 Sample user: test@mingus.com")
    logger.info("💳 Subscription plans: Budget ($10), Mid-Tier ($20), Professional ($50)")
    logger.info("🔧 Next step: Test the user profile API endpoints")

if __name__ == "__main__":
    main() 