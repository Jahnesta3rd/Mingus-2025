#!/usr/bin/env python3
"""
Comprehensive Database Connectivity Test Script
Tests PostgreSQL connection, SQLAlchemy configuration, and connection pooling
"""

import os
import sys
import time
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseConnectivityTester:
    """Comprehensive database connectivity tester"""
    
    def __init__(self):
        self.test_results = []
        self.connection_tests = []
        self.pool_tests = []
        
    def log_test(self, test_name, status, details=None, error=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'error': str(error) if error else None,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if status == 'PASS':
            logger.info(f"✅ {test_name}: PASS")
            if details:
                logger.info(f"   Details: {details}")
        else:
            logger.error(f"❌ {test_name}: FAIL")
            if error:
                logger.error(f"   Error: {error}")
            if details:
                logger.info(f"   Details: {details}")
    
    def test_environment_variables(self):
        """Test environment variable configuration"""
        logger.info("🔍 Testing Environment Variables...")
        
        required_vars = [
            'DATABASE_URL',
            'POSTGRES_HOST',
            'POSTGRES_PORT', 
            'POSTGRES_DB',
            'POSTGRES_USER',
            'POSTGRES_PASSWORD'
        ]
        
        optional_vars = [
            'DB_POOL_SIZE',
            'DB_MAX_OVERFLOW',
            'DB_POOL_RECYCLE',
            'REDIS_URL'
        ]
        
        # Check required variables
        missing_required = []
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
            else:
                # Mask sensitive values
                value = os.getenv(var)
                if 'password' in var.lower() or 'secret' in var.lower():
                    masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                else:
                    masked_value = value
                self.log_test(f"ENV_{var}", "PASS", f"Value: {masked_value}")
        
        if missing_required:
            self.log_test("ENV_REQUIRED_VARS", "FAIL", f"Missing: {', '.join(missing_required)}")
        else:
            self.log_test("ENV_REQUIRED_VARS", "PASS", "All required environment variables set")
        
        # Check optional variables
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                self.log_test(f"ENV_{var}", "PASS", f"Value: {value}")
            else:
                self.log_test(f"ENV_{var}", "WARN", f"Not set (using defaults)")
    
    def test_postgresql_connection(self):
        """Test direct PostgreSQL connection"""
        logger.info("🔍 Testing Direct PostgreSQL Connection...")
        
        # Try to parse DATABASE_URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.log_test("POSTGRES_DIRECT_CONNECTION", "FAIL", "DATABASE_URL not set")
            return
        
        try:
            # Test with psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            self.log_test("POSTGRES_DIRECT_CONNECTION", "PASS", f"PostgreSQL version: {version}")
            
            # Test database info
            cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
            db_info = cursor.fetchone()
            self.log_test("POSTGRES_DB_INFO", "PASS", 
                         f"Database: {db_info[0]}, User: {db_info[1]}, Host: {db_info[2]}, Port: {db_info[3]}")
            
            # Test connection parameters
            cursor.execute("SHOW max_connections")
            max_conn = cursor.fetchone()[0]
            cursor.execute("SHOW shared_buffers")
            shared_buffers = cursor.fetchone()[0]
            
            self.log_test("POSTGRES_SERVER_CONFIG", "PASS", 
                         f"Max connections: {max_conn}, Shared buffers: {shared_buffers}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.log_test("POSTGRES_DIRECT_CONNECTION", "FAIL", error=e)
    
    def test_sqlalchemy_connection(self):
        """Test SQLAlchemy connection"""
        logger.info("🔍 Testing SQLAlchemy Connection...")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.log_test("SQLALCHEMY_CONNECTION", "FAIL", "DATABASE_URL not set")
            return
        
        try:
            # Test basic engine creation
            engine = create_engine(database_url)
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                self.log_test("SQLALCHEMY_BASIC_CONNECTION", "PASS", f"Test query result: {test_value}")
            
            # Test connection info
            with engine.connect() as conn:
                result = conn.execute(text("SELECT current_timestamp"))
                timestamp = result.fetchone()[0]
                self.log_test("SQLALCHEMY_TIMESTAMP_QUERY", "PASS", f"Current timestamp: {timestamp}")
            
            engine.dispose()
            
        except Exception as e:
            self.log_test("SQLALCHEMY_CONNECTION", "FAIL", error=e)
    
    def test_connection_pooling(self):
        """Test connection pooling configuration"""
        logger.info("🔍 Testing Connection Pooling...")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.log_test("CONNECTION_POOLING", "FAIL", "DATABASE_URL not set")
            return
        
        try:
            # Test with custom pool settings
            pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
            max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
            pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
            
            engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                pool_recycle=pool_recycle,
                echo=False
            )
            
            # Test pool configuration
            pool = engine.pool
            self.log_test("POOL_CONFIGURATION", "PASS", 
                         f"Pool size: {pool.size()}, Max overflow: {pool._max_overflow}, Recycle: {pool_recycle}")
            
            # Test multiple connections
            connections = []
            try:
                for i in range(min(5, pool_size)):
                    conn = engine.connect()
                    connections.append(conn)
                    self.log_test(f"POOL_CONNECTION_{i+1}", "PASS", f"Connection {i+1} established")
                
                # Test pool status
                self.log_test("POOL_STATUS", "PASS", 
                             f"Checked in: {pool.checkedin()}, Checked out: {pool.checkedout()}")
                
            finally:
                # Close all connections
                for conn in connections:
                    conn.close()
            
            engine.dispose()
            
        except Exception as e:
            self.log_test("CONNECTION_POOLING", "FAIL", error=e)
    
    def test_connection_timeout(self):
        """Test connection timeout handling"""
        logger.info("🔍 Testing Connection Timeout...")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.log_test("CONNECTION_TIMEOUT", "FAIL", "DATABASE_URL not set")
            return
        
        try:
            # Test with timeout settings
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,  # 5 minutes
                connect_args={
                    'connect_timeout': 10,
                    'application_name': 'mingus_connectivity_test'
                }
            )
            
            # Test connection with timeout
            start_time = time.time()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT pg_sleep(1)"))
                result.fetchone()
                connection_time = time.time() - start_time
                
                self.log_test("CONNECTION_TIMEOUT", "PASS", 
                             f"Connection established in {connection_time:.2f}s")
            
            engine.dispose()
            
        except Exception as e:
            self.log_test("CONNECTION_TIMEOUT", "FAIL", error=e)
    
    def test_redis_connection(self):
        """Test Redis connection"""
        logger.info("🔍 Testing Redis Connection...")
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            import redis
            r = redis.from_url(redis_url)
            
            # Test basic operations
            r.set('test_key', 'test_value', ex=60)
            value = r.get('test_key')
            r.delete('test_key')
            
            if value == b'test_value':
                self.log_test("REDIS_CONNECTION", "PASS", "Redis operations successful")
            else:
                self.log_test("REDIS_CONNECTION", "FAIL", "Redis operations failed")
                
        except ImportError:
            self.log_test("REDIS_CONNECTION", "WARN", "Redis Python package not installed")
        except Exception as e:
            self.log_test("REDIS_CONNECTION", "FAIL", error=e)
    
    def test_database_performance(self):
        """Test database performance metrics"""
        logger.info("🔍 Testing Database Performance...")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.log_test("DATABASE_PERFORMANCE", "FAIL", "DATABASE_URL not set")
            return
        
        try:
            engine = create_engine(database_url)
            
            # Test query performance
            start_time = time.time()
            with engine.connect() as conn:
                # Simple query
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                simple_query_time = time.time() - start_time
                
                # Test multiple queries
                start_time = time.time()
                for i in range(10):
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                multiple_query_time = time.time() - start_time
                
                self.log_test("DATABASE_PERFORMANCE", "PASS", 
                             f"Simple query: {simple_query_time*1000:.2f}ms, "
                             f"10 queries: {multiple_query_time*1000:.2f}ms")
            
            engine.dispose()
            
        except Exception as e:
            self.log_test("DATABASE_PERFORMANCE", "FAIL", error=e)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("📊 DATABASE CONNECTIVITY TEST REPORT")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"⚠️  Warnings: {warning_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        # Show failed tests
        if failed_tests > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    logger.error(f"  - {result['test_name']}: {result['error']}")
        
        # Show warnings
        if warning_tests > 0:
            logger.info("\n⚠️  WARNINGS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    logger.warning(f"  - {result['test_name']}: {result['details']}")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        if failed_tests > 0:
            logger.info("  - Check environment variables for database configuration")
            logger.info("  - Verify PostgreSQL service is running")
            logger.info("  - Check network connectivity and firewall settings")
            logger.info("  - Review connection pool settings")
        else:
            logger.info("  - All tests passed! Database connectivity is healthy")
        
        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'warnings': warning_tests,
            'results': self.test_results
        }
    
    def run_all_tests(self):
        """Run all connectivity tests"""
        logger.info("🚀 Starting Database Connectivity Tests...")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        self.test_environment_variables()
        self.test_postgresql_connection()
        self.test_sqlalchemy_connection()
        self.test_connection_pooling()
        self.test_connection_timeout()
        self.test_redis_connection()
        self.test_database_performance()
        
        return self.generate_report()

def main():
    """Main function"""
    tester = DatabaseConnectivityTester()
    
    try:
        results = tester.run_all_tests()
        
        # Exit with error code if any tests failed
        if results['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
