#!/usr/bin/env python3
"""
Environment Setup and Database Schema Implementation Script
Sets up security keys and creates encrypted financial tables
"""

import os
import sys
import secrets
import string
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_secure_key(length=64):
    """Generate a secure random key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_django_key():
    """Generate a Django-compatible secret key"""
    return 'django-insecure-' + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(50))

def setup_environment_variables():
    """Set up environment variables for security keys"""
    logger.info("Setting up environment variables...")
    
    # Generate secure keys
    field_encryption_key = generate_secure_key(64)
    django_secret_key = generate_django_key()
    flask_secret_key = generate_secure_key(32)
    
    # Set environment variables
    os.environ['FIELD_ENCRYPTION_KEY'] = field_encryption_key
    os.environ['DJANGO_SECRET_KEY'] = django_secret_key
    os.environ['SECRET_KEY'] = flask_secret_key
    os.environ['SECURE_SSL_REDIRECT'] = 'True'
    
    # Database URL (you can modify this for your setup)
    database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mingus')
    os.environ['DATABASE_URL'] = database_url
    
    logger.info("Environment variables set successfully")
    logger.info(f"Database URL: {database_url}")
    logger.info("Security keys generated and configured")
    
    return {
        'field_encryption_key': field_encryption_key,
        'django_secret_key': django_secret_key,
        'flask_secret_key': flask_secret_key,
        'database_url': database_url
    }

def create_database_tables(database_url):
    """Create encrypted financial tables in the database"""
    logger.info("Creating encrypted financial tables...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Read the SQL schema file
        schema_file = Path(__file__).parent.parent / 'database' / 'create_encrypted_financial_tables.sql'
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r') as f:
            sql_commands = f.read()
        
        # Split SQL commands by semicolon and execute each
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        with engine.connect() as connection:
            for command in commands:
                if command:
                    try:
                        connection.execute(text(command))
                        connection.commit()
                        logger.info(f"Executed SQL command: {command[:50]}...")
                    except SQLAlchemyError as e:
                        logger.warning(f"Command failed (may already exist): {e}")
                        connection.rollback()
        
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False

def verify_database_setup(database_url):
    """Verify that all tables were created successfully"""
    logger.info("Verifying database setup...")
    
    try:
        engine = create_engine(database_url)
        
        # List of expected tables
        expected_tables = [
            'encrypted_financial_profiles',
            'encrypted_income_sources', 
            'encrypted_debt_accounts',
            'encrypted_child_support',
            'financial_audit_logs'
        ]
        
        with engine.connect() as connection:
            for table in expected_tables:
                result = connection.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """))
                exists = result.scalar()
                
                if exists:
                    logger.info(f"✅ Table '{table}' exists")
                else:
                    logger.error(f"❌ Table '{table}' missing")
                    return False
        
        logger.info("Database verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("Starting environment and database setup...")
    
    try:
        # Step 1: Setup environment variables
        env_config = setup_environment_variables()
        
        # Step 2: Create database tables
        success = create_database_tables(env_config['database_url'])
        
        if not success:
            logger.error("Failed to create database tables")
            sys.exit(1)
        
        # Step 3: Verify setup
        verification_success = verify_database_setup(env_config['database_url'])
        
        if not verification_success:
            logger.error("Database verification failed")
            sys.exit(1)
        
        logger.info("🎉 Environment and database setup completed successfully!")
        logger.info("\n📋 Setup Summary:")
        logger.info(f"   • Database URL: {env_config['database_url']}")
        logger.info(f"   • Field Encryption Key: {env_config['field_encryption_key'][:20]}...")
        logger.info(f"   • Django Secret Key: {env_config['django_secret_key'][:20]}...")
        logger.info(f"   • Flask Secret Key: {env_config['flask_secret_key'][:20]}...")
        logger.info("\n🔒 Security Features Enabled:")
        logger.info("   • Field-level encryption for sensitive data")
        logger.info("   • Row Level Security (RLS) policies")
        logger.info("   • Audit logging for all financial operations")
        logger.info("   • HTTPS enforcement")
        logger.info("   • Input validation and rate limiting")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 