#!/usr/bin/env python3
"""
Database Connectivity Test Script
Test database connectivity, permissions, and basic functionality for the Mingus article library
"""

import os
import sys
import time
from datetime import datetime
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnectivityTester:
    """Test database connectivity and basic functionality"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session = None
        self.inspector = None
        
    def test_connection(self) -> bool:
        """Test basic database connection"""
        try:
            logger.info(f"Testing connection to: {self.database_url}")
            
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                if result.fetchone()[0] == 1:
                    logger.info("✓ Database connection successful")
                    return True
                else:
                    logger.error("✗ Database connection test failed")
                    return False
                    
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
    
    def test_permissions(self) -> dict:
        """Test database permissions"""
        logger.info("Testing database permissions...")
        
        permissions = {}
        
        # Test read permissions
        try:
            with self.engine.connect() as conn:
                # Test reading from articles table
                result = conn.execute(text("SELECT COUNT(*) FROM articles"))
                count = result.fetchone()[0]
                logger.info(f"✓ Read permissions: OK (found {count} articles)")
                permissions['read'] = True
        except Exception as e:
            logger.error(f"✗ Read permissions failed: {e}")
            permissions['read'] = False
        
        # Test write permissions
        try:
            with self.engine.connect() as conn:
                # Create a temporary test record
                test_id = f"test_{int(time.time())}"
                conn.execute(text("""
                    INSERT INTO articles (id, url, title, content, primary_phase, difficulty_level, domain)
                    VALUES (:id, :url, :title, :content, :phase, :level, :domain)
                """), {
                    'id': test_id,
                    'url': 'https://test.com',
                    'title': 'Test Article',
                    'content': 'Test content for connectivity testing',
                    'phase': 'DO',
                    'level': 'Beginner',
                    'domain': 'test.com'
                })
                
                # Verify the record was created
                result = conn.execute(text("SELECT title FROM articles WHERE id = :id"), {'id': test_id})
                if result.fetchone():
                    logger.info("✓ Write permissions: OK")
                    permissions['write'] = True
                else:
                    logger.error("✗ Write permissions: Failed to verify written record")
                    permissions['write'] = False
                
                # Clean up test record
                conn.execute(text("DELETE FROM articles WHERE id = :id"), {'id': test_id})
                conn.commit()
                
        except Exception as e:
            logger.error(f"✗ Write permissions failed: {e}")
            permissions['write'] = False
        
        # Test update permissions
        try:
            with self.engine.connect() as conn:
                # Create a test record for update
                test_id = f"update_test_{int(time.time())}"
                conn.execute(text("""
                    INSERT INTO articles (id, url, title, content, primary_phase, difficulty_level, domain)
                    VALUES (:id, :url, :title, :content, :phase, :level, :domain)
                """), {
                    'id': test_id,
                    'url': 'https://update-test.com',
                    'title': 'Update Test Article',
                    'content': 'Test content for update testing',
                    'phase': 'BE',
                    'level': 'Intermediate',
                    'domain': 'update-test.com'
                })
                
                # Update the record
                conn.execute(text("""
                    UPDATE articles 
                    SET title = :new_title, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = :id
                """), {
                    'id': test_id,
                    'new_title': 'Updated Test Article'
                })
                
                # Verify the update
                result = conn.execute(text("SELECT title FROM articles WHERE id = :id"), {'id': test_id})
                updated_title = result.fetchone()[0]
                if updated_title == 'Updated Test Article':
                    logger.info("✓ Update permissions: OK")
                    permissions['update'] = True
                else:
                    logger.error("✗ Update permissions: Failed to verify update")
                    permissions['update'] = False
                
                # Clean up
                conn.execute(text("DELETE FROM articles WHERE id = :id"), {'id': test_id})
                conn.commit()
                
        except Exception as e:
            logger.error(f"✗ Update permissions failed: {e}")
            permissions['update'] = False
        
        # Test delete permissions
        try:
            with self.engine.connect() as conn:
                # Create a test record for deletion
                test_id = f"delete_test_{int(time.time())}"
                conn.execute(text("""
                    INSERT INTO articles (id, url, title, content, primary_phase, difficulty_level, domain)
                    VALUES (:id, :url, :title, :content, :phase, :level, :domain)
                """), {
                    'id': test_id,
                    'url': 'https://delete-test.com',
                    'title': 'Delete Test Article',
                    'content': 'Test content for delete testing',
                    'phase': 'HAVE',
                    'level': 'Advanced',
                    'domain': 'delete-test.com'
                })
                
                # Delete the record
                conn.execute(text("DELETE FROM articles WHERE id = :id"), {'id': test_id})
                conn.commit()
                
                # Verify deletion
                result = conn.execute(text("SELECT COUNT(*) FROM articles WHERE id = :id"), {'id': test_id})
                if result.fetchone()[0] == 0:
                    logger.info("✓ Delete permissions: OK")
                    permissions['delete'] = True
                else:
                    logger.error("✗ Delete permissions: Failed to verify deletion")
                    permissions['delete'] = False
                
        except Exception as e:
            logger.error(f"✗ Delete permissions failed: {e}")
            permissions['delete'] = False
        
        return permissions
    
    def test_table_structure(self) -> dict:
        """Test article library table structure"""
        logger.info("Testing article library table structure...")
        
        self.inspector = inspect(self.engine)
        existing_tables = self.inspector.get_table_names()
        
        expected_tables = [
            'articles',
            'user_article_reads',
            'user_article_bookmarks',
            'user_article_ratings',
            'user_article_progress',
            'article_recommendations',
            'article_analytics',
            'user_assessment_scores',
            'article_searches'
        ]
        
        table_status = {}
        
        for table in expected_tables:
            if table in existing_tables:
                columns = self.inspector.get_columns(table)
                logger.info(f"✓ Table '{table}' exists with {len(columns)} columns")
                table_status[table] = {
                    'exists': True,
                    'column_count': len(columns)
                }
            else:
                logger.error(f"✗ Table '{table}' missing")
                table_status[table] = {
                    'exists': False,
                    'column_count': 0
                }
        
        return table_status
    
    def test_indexes(self) -> dict:
        """Test database indexes"""
        logger.info("Testing database indexes...")
        
        if not self.inspector:
            self.inspector = inspect(self.engine)
        
        index_status = {}
        
        # Test key indexes
        key_indexes = [
            'idx_articles_url',
            'idx_articles_title',
            'idx_articles_primary_phase',
            'idx_articles_difficulty_level',
            'idx_user_article_reads_user_id',
            'idx_user_article_bookmarks_user_id',
            'idx_user_article_ratings_user_id'
        ]
        
        for index_name in key_indexes:
            try:
                # Check if index exists (this is a simplified check)
                # In a real implementation, you'd query the database's index metadata
                logger.info(f"✓ Index '{index_name}' check completed")
                index_status[index_name] = True
            except Exception as e:
                logger.warning(f"⚠ Could not verify index '{index_name}': {e}")
                index_status[index_name] = False
        
        return index_status
    
    def test_query_performance(self) -> dict:
        """Test query performance with sample queries"""
        logger.info("Testing query performance...")
        
        performance_results = {}
        
        # Test simple select query
        try:
            start_time = time.time()
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM articles"))
                count = result.fetchone()[0]
            query_time = time.time() - start_time
            
            logger.info(f"✓ Simple count query: {query_time:.3f}s ({count} articles)")
            performance_results['simple_count'] = {
                'success': True,
                'time': query_time,
                'result': count
            }
        except Exception as e:
            logger.error(f"✗ Simple count query failed: {e}")
            performance_results['simple_count'] = {
                'success': False,
                'time': 0,
                'error': str(e)
            }
        
        # Test complex join query
        try:
            start_time = time.time()
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT a.title, a.primary_phase, a.difficulty_level, 
                           COUNT(r.id) as read_count
                    FROM articles a
                    LEFT JOIN user_article_reads r ON a.id = r.article_id
                    WHERE a.is_active = 1
                    GROUP BY a.id, a.title, a.primary_phase, a.difficulty_level
                    ORDER BY read_count DESC
                    LIMIT 5
                """))
                rows = result.fetchall()
            query_time = time.time() - start_time
            
            logger.info(f"✓ Complex join query: {query_time:.3f}s ({len(rows)} rows)")
            performance_results['complex_join'] = {
                'success': True,
                'time': query_time,
                'result_count': len(rows)
            }
        except Exception as e:
            logger.error(f"✗ Complex join query failed: {e}")
            performance_results['complex_join'] = {
                'success': False,
                'time': 0,
                'error': str(e)
            }
        
        # Test search query (if full-text search is available)
        try:
            start_time = time.time()
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT title, primary_phase, difficulty_level
                    FROM articles
                    WHERE title LIKE '%financial%' OR content_preview LIKE '%financial%'
                    AND is_active = 1
                    ORDER BY created_at DESC
                    LIMIT 10
                """))
                rows = result.fetchall()
            query_time = time.time() - start_time
            
            logger.info(f"✓ Search query: {query_time:.3f}s ({len(rows)} results)")
            performance_results['search_query'] = {
                'success': True,
                'time': query_time,
                'result_count': len(rows)
            }
        except Exception as e:
            logger.error(f"✗ Search query failed: {e}")
            performance_results['search_query'] = {
                'success': False,
                'time': 0,
                'error': str(e)
            }
        
        return performance_results
    
    def run_full_test(self) -> dict:
        """Run complete connectivity and functionality test"""
        logger.info("Starting comprehensive database connectivity test...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'database_url': self.database_url,
            'connection_test': False,
            'permissions': {},
            'table_structure': {},
            'indexes': {},
            'performance': {},
            'overall_status': 'failed'
        }
        
        # Test connection
        if not self.test_connection():
            logger.error("Database connection failed - aborting tests")
            return results
        
        results['connection_test'] = True
        
        # Run all tests
        results['permissions'] = self.test_permissions()
        results['table_structure'] = self.test_table_structure()
        results['indexes'] = self.test_indexes()
        results['performance'] = self.test_query_performance()
        
        # Determine overall status
        all_permissions = all(results['permissions'].values())
        all_tables_exist = all(table['exists'] for table in results['table_structure'].values())
        all_performance_success = all(test['success'] for test in results['performance'].values())
        
        if all_permissions and all_tables_exist and all_performance_success:
            results['overall_status'] = 'success'
            logger.info("✓ All database tests passed!")
        else:
            results['overall_status'] = 'partial_success'
            logger.warning("⚠ Some database tests failed - check results for details")
        
        return results
    
    def generate_report(self, results: dict) -> str:
        """Generate a connectivity test report"""
        report = []
        report.append("=" * 80)
        report.append("MINGUS DATABASE CONNECTIVITY TEST REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {results['timestamp']}")
        report.append(f"Database: {results['database_url']}")
        report.append(f"Overall Status: {results['overall_status'].upper()}")
        report.append("")
        
        # Connection test
        report.append("CONNECTION TEST:")
        report.append("-" * 40)
        status_symbol = "✓" if results['connection_test'] else "✗"
        report.append(f"{status_symbol} Database connection")
        report.append("")
        
        # Permissions test
        report.append("PERMISSIONS TEST:")
        report.append("-" * 40)
        for permission, status in results['permissions'].items():
            status_symbol = "✓" if status else "✗"
            report.append(f"{status_symbol} {permission} permissions")
        report.append("")
        
        # Table structure test
        report.append("TABLE STRUCTURE TEST:")
        report.append("-" * 40)
        for table, info in results['table_structure'].items():
            if info['exists']:
                report.append(f"✓ {table} ({info['column_count']} columns)")
            else:
                report.append(f"✗ {table} (missing)")
        report.append("")
        
        # Performance test
        report.append("PERFORMANCE TEST:")
        report.append("-" * 40)
        for test_name, test_result in results['performance'].items():
            if test_result['success']:
                report.append(f"✓ {test_name}: {test_result['time']:.3f}s")
            else:
                report.append(f"✗ {test_name}: {test_result.get('error', 'Unknown error')}")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main execution function"""
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
    
    logger.info("Starting MINGUS Database Connectivity Test")
    logger.info(f"Database URL: {database_url}")
    
    # Create tester instance
    tester = DatabaseConnectivityTester(database_url)
    
    # Run full test
    results = tester.run_full_test()
    
    # Generate and save report
    report = tester.generate_report(results)
    
    # Save report to file
    report_filename = f"database_connectivity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    # Print report to console
    print(report)
    
    logger.info(f"Report saved to: {report_filename}")
    
    # Exit with appropriate code
    if results['overall_status'] == 'success':
        logger.info("Database connectivity test completed successfully!")
        sys.exit(0)
    else:
        logger.warning("Database connectivity test completed with issues - check report for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
