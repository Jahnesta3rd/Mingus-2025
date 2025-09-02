#!/usr/bin/env python3
"""
Database Connectivity Fix Script
Automatically fixes common PostgreSQL and SQLAlchemy connection issues
"""

import os
import sys
import subprocess
import psycopg2
from sqlalchemy import create_engine, text
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseConnectivityFixer:
    """Automated database connectivity issue fixer"""
    
    def __init__(self):
        self.fixes_applied = []
        self.errors_encountered = []
        
    def log_fix(self, fix_name, description, success=True, error=None):
        """Log applied fixes"""
        if success:
            logger.info(f"✅ {fix_name}: {description}")
            self.fixes_applied.append(fix_name)
        else:
            logger.error(f"❌ {fix_name}: {description}")
            if error:
                logger.error(f"   Error: {error}")
            self.errors_encountered.append(fix_name)
    
    def check_postgresql_service(self):
        """Check and fix PostgreSQL service status"""
        logger.info("🔍 Checking PostgreSQL service status...")
        
        try:
            # Check if PostgreSQL is running
            result = subprocess.run(['brew', 'services', 'list'], 
                                  capture_output=True, text=True, check=True)
            
            if 'postgresql' in result.stdout:
                if 'started' in result.stdout:
                    self.log_fix("POSTGRESQL_SERVICE", "PostgreSQL service is running")
                    return True
                elif 'error' in result.stdout:
                    logger.warning("⚠️  PostgreSQL service has errors, attempting to restart...")
                    
                    # Try to restart PostgreSQL
                    subprocess.run(['brew', 'services', 'restart', 'postgresql@14'], 
                                 capture_output=True, check=True)
                    
                    # Wait a moment for restart
                    import time
                    time.sleep(5)
                    
                    # Check status again
                    result = subprocess.run(['brew', 'services', 'list'], 
                                          capture_output=True, text=True, check=True)
                    
                    if 'started' in result.stdout:
                        self.log_fix("POSTGRESQL_SERVICE_RESTART", "PostgreSQL service restarted successfully")
                        return True
                    else:
                        self.log_fix("POSTGRESQL_SERVICE_RESTART", "Failed to restart PostgreSQL service", False)
                        return False
                else:
                    # Try to start PostgreSQL
                    logger.info("🚀 Starting PostgreSQL service...")
                    subprocess.run(['brew', 'services', 'start', 'postgresql@14'], 
                                 capture_output=True, check=True)
                    
                    # Wait for startup
                    import time
                    time.sleep(10)
                    
                    self.log_fix("POSTGRESQL_SERVICE_START", "PostgreSQL service started")
                    return True
            else:
                self.log_fix("POSTGRESQL_SERVICE", "PostgreSQL not found in brew services", False)
                return False
                
        except subprocess.CalledProcessError as e:
            self.log_fix("POSTGRESQL_SERVICE_CHECK", f"Failed to check PostgreSQL service: {e}", False, e)
            return False
        except Exception as e:
            self.log_fix("POSTGRESQL_SERVICE_CHECK", f"Unexpected error: {e}", False, e)
            return False
    
    def create_database_and_user(self):
        """Create database and user if they don't exist"""
        logger.info("🔍 Checking database and user existence...")
        
        try:
            # Connect to PostgreSQL as superuser
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres'
            )
            
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'mingus_db'")
            if not cursor.fetchone():
                cursor.execute("CREATE DATABASE mingus_db")
                self.log_fix("DATABASE_CREATION", "Created mingus_db database")
            else:
                self.log_fix("DATABASE_EXISTS", "mingus_db database already exists")
            
            # Check if user exists
            cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'mingus_user'")
            if not cursor.fetchone():
                cursor.execute("CREATE USER mingus_user WITH PASSWORD 'mingus_password'")
                cursor.execute("GRANT ALL PRIVILEGES ON DATABASE mingus_db TO mingus_user")
                self.log_fix("USER_CREATION", "Created mingus_user with privileges")
            else:
                self.log_fix("USER_EXISTS", "mingus_user already exists")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except psycopg2.OperationalError as e:
            if "authentication failed" in str(e).lower():
                logger.warning("⚠️  Cannot connect as postgres user. You may need to:")
                logger.warning("   1. Set a password for postgres user: ALTER USER postgres PASSWORD 'password'")
                logger.warning("   2. Or use your system username instead")
                return False
            else:
                self.log_fix("DATABASE_SETUP", f"Database setup failed: {e}", False, e)
                return False
        except Exception as e:
            self.log_fix("DATABASE_SETUP", f"Unexpected error: {e}", False, e)
            return False
    
    def test_database_connection(self):
        """Test database connection with created credentials"""
        logger.info("🔍 Testing database connection...")
        
        try:
            # Test connection with the new database
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='mingus_db',
                user='mingus_user',
                password='mingus_password'
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.log_fix("DATABASE_CONNECTION", f"Successfully connected to mingus_db: {version}")
            return True
            
        except Exception as e:
            self.log_fix("DATABASE_CONNECTION", f"Connection test failed: {e}", False, e)
            return False
    
    def create_environment_file(self):
        """Create .env file with proper database configuration"""
        logger.info("🔍 Creating environment configuration file...")
        
        env_content = """# Database Configuration
DATABASE_URL=postgresql://mingus_user:mingus_password@localhost:5432/mingus_db

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Flask Settings
FLASK_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-key-change-this-in-production

# Security Settings
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mingus.log

# Performance
ENABLE_PERFORMANCE_MONITORING=true
CREATE_TABLES=true
"""
        
        try:
            env_file = Path('.env')
            if env_file.exists():
                # Backup existing .env file
                backup_file = Path('.env.backup')
                env_file.rename(backup_file)
                self.log_fix("ENV_BACKUP", f"Backed up existing .env to {backup_file}")
            
            # Create new .env file
            with open('.env', 'w') as f:
                f.write(env_content)
            
            self.log_fix("ENV_CREATION", "Created .env file with database configuration")
            return True
            
        except Exception as e:
            self.log_fix("ENV_CREATION", f"Failed to create .env file: {e}", False, e)
            return False
    
    def install_required_packages(self):
        """Install required Python packages"""
        logger.info("🔍 Installing required Python packages...")
        
        required_packages = [
            'psycopg2-binary>=2.9.7',
            'SQLAlchemy>=2.0.0',
            'Flask-SQLAlchemy>=3.0.5',
            'redis>=4.6.0',
            'python-dotenv>=1.0.0'
        ]
        
        try:
            for package in required_packages:
                logger.info(f"Installing {package}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             capture_output=True, check=True)
                self.log_fix(f"PACKAGE_INSTALL_{package.split('>')[0]}", f"Installed {package}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_fix("PACKAGE_INSTALL", f"Failed to install packages: {e}", False, e)
            return False
        except Exception as e:
            self.log_fix("PACKAGE_INSTALL", f"Unexpected error: {e}", False, e)
            return False
    
    def optimize_postgresql_settings(self):
        """Optimize PostgreSQL settings for better performance"""
        logger.info("🔍 Optimizing PostgreSQL settings...")
        
        try:
            # Connect to database
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='mingus_db',
                user='mingus_user',
                password='mingus_password'
            )
            
            cursor = conn.cursor()
            
            # Set optimized connection settings
            optimizations = [
                ("SET max_connections = 200", "Increased max connections"),
                ("SET shared_buffers = '256MB'", "Set shared buffers"),
                ("SET effective_cache_size = '1GB'", "Set effective cache size"),
                ("SET maintenance_work_mem = '64MB'", "Set maintenance work memory"),
                ("SET checkpoint_completion_target = 0.9", "Optimized checkpoint completion"),
                ("SET wal_buffers = '16MB'", "Set WAL buffers"),
                ("SET default_statistics_target = 100", "Set default statistics target")
            ]
            
            for sql, description in optimizations:
                try:
                    cursor.execute(sql)
                    self.log_fix("POSTGRESQL_OPTIMIZATION", description)
                except Exception as e:
                    logger.warning(f"⚠️  Could not apply optimization '{description}': {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.log_fix("POSTGRESQL_OPTIMIZATION", f"Failed to optimize settings: {e}", False, e)
            return False
    
    def test_sqlalchemy_integration(self):
        """Test SQLAlchemy integration with the database"""
        logger.info("🔍 Testing SQLAlchemy integration...")
        
        try:
            # Test SQLAlchemy engine creation
            engine = create_engine(
                'postgresql://mingus_user:mingus_password@localhost:5432/mingus_db',
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                
                if test_value == 1:
                    self.log_fix("SQLALCHEMY_INTEGRATION", "SQLAlchemy integration successful")
                else:
                    self.log_fix("SQLALCHEMY_INTEGRATION", "SQLAlchemy test query failed", False)
                    return False
            
            engine.dispose()
            return True
            
        except Exception as e:
            self.log_fix("SQLALCHEMY_INTEGRATION", f"SQLAlchemy integration failed: {e}", False, e)
            return False
    
    def generate_summary_report(self):
        """Generate summary report of all fixes applied"""
        logger.info("\n" + "="*60)
        logger.info("📊 DATABASE CONNECTIVITY FIX SUMMARY")
        logger.info("="*60)
        
        logger.info(f"✅ Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            logger.info(f"   - {fix}")
        
        if self.errors_encountered:
            logger.info(f"\n❌ Errors Encountered: {len(self.errors_encountered)}")
            for error in self.errors_encountered:
                logger.info(f"   - {error}")
        
        logger.info(f"\n💡 Next Steps:")
        if not self.errors_encountered:
            logger.info("   1. Your database connectivity should now be working!")
            logger.info("   2. Test your Flask application")
            logger.info("   3. Monitor connection pool usage")
            logger.info("   4. Consider adjusting pool settings based on your load")
        else:
            logger.info("   1. Review the errors above")
            logger.info("   2. Check PostgreSQL service status manually")
            logger.info("   3. Verify database credentials")
            logger.info("   4. Check firewall and network settings")
        
        return {
            'fixes_applied': self.fixes_applied,
            'errors_encountered': self.errors_encountered,
            'success': len(self.errors_encountered) == 0
        }
    
    def run_all_fixes(self):
        """Run all database connectivity fixes"""
        logger.info("🚀 Starting Database Connectivity Fixes...")
        
        # Check and fix PostgreSQL service
        if not self.check_postgresql_service():
            logger.error("❌ Cannot proceed without PostgreSQL service")
            return False
        
        # Install required packages
        self.install_required_packages()
        
        # Create database and user
        self.create_database_and_user()
        
        # Test connection
        if not self.test_database_connection():
            logger.error("❌ Cannot proceed without database connection")
            return False
        
        # Optimize PostgreSQL settings
        self.optimize_postgresql_settings()
        
        # Test SQLAlchemy integration
        self.test_sqlalchemy_integration()
        
        # Create environment file
        self.create_environment_file()
        
        return True

def main():
    """Main function"""
    fixer = DatabaseConnectivityFixer()
    
    try:
        success = fixer.run_all_fixes()
        
        # Generate summary report
        report = fixer.generate_summary_report()
        
        if report['success']:
            logger.info("\n🎉 Database connectivity issues have been resolved!")
            sys.exit(0)
        else:
            logger.error("\n⚠️  Some issues could not be resolved automatically.")
            logger.error("Please review the errors above and fix them manually.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Fix process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Unexpected error during fix process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
