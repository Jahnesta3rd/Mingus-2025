#!/usr/bin/env python3
"""
Article Library Database Verification and Optimization Script
Comprehensive verification and optimization of the Mingus article library database

This script will:
1. Verify all article library tables are created correctly
2. Set up database indexes for optimal search performance
3. Configure PostgreSQL full-text search extensions
4. Test database connectivity and permissions
5. Generate performance recommendations
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseVerifier:
    """Comprehensive database verification and optimization class"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session = None
        self.inspector = None
        self.is_postgresql = 'postgresql' in database_url.lower()
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            logger.info(f"Connecting to database: {self.database_url}")
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.session = sessionmaker(bind=self.engine)()
            self.inspector = inspect(self.engine)
            
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def verify_article_library_tables(self) -> Dict[str, bool]:
        """Verify all article library tables exist and have correct structure"""
        logger.info("Verifying article library tables...")
        
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
        
        existing_tables = self.inspector.get_table_names()
        verification_results = {}
        
        for table in expected_tables:
            if table in existing_tables:
                logger.info(f"✓ Table '{table}' exists")
                verification_results[table] = True
                
                # Verify table structure
                columns = self.inspector.get_columns(table)
                logger.info(f"  - {table}: {len(columns)} columns")
                
                # Check for critical columns
                critical_columns = self._get_critical_columns(table)
                missing_columns = []
                for col in critical_columns:
                    if not any(c['name'] == col for c in columns):
                        missing_columns.append(col)
                
                if missing_columns:
                    logger.warning(f"  - Missing critical columns in {table}: {missing_columns}")
                    verification_results[table] = False
                else:
                    logger.info(f"  - All critical columns present in {table}")
            else:
                logger.error(f"✗ Table '{table}' missing")
                verification_results[table] = False
        
        return verification_results
    
    def _get_critical_columns(self, table: str) -> List[str]:
        """Get critical columns for each table"""
        critical_columns = {
            'articles': ['id', 'url', 'title', 'content', 'primary_phase', 'difficulty_level', 'domain'],
            'user_article_reads': ['id', 'user_id', 'article_id', 'started_at'],
            'user_article_bookmarks': ['id', 'user_id', 'article_id', 'folder_name'],
            'user_article_ratings': ['id', 'user_id', 'article_id', 'overall_rating'],
            'user_article_progress': ['id', 'user_id', 'article_id', 'current_phase'],
            'article_recommendations': ['id', 'user_id', 'article_id', 'recommendation_score'],
            'article_analytics': ['id', 'article_id', 'total_views', 'total_reads'],
            'user_assessment_scores': ['id', 'user_id', 'be_score', 'do_score', 'have_score'],
            'article_searches': ['id', 'user_id', 'search_query', 'created_at']
        }
        return critical_columns.get(table, [])
    
    def setup_database_indexes(self) -> Dict[str, bool]:
        """Set up database indexes for optimal search performance"""
        logger.info("Setting up database indexes...")
        
        index_definitions = self._get_index_definitions()
        index_results = {}
        
        for index_name, index_sql in index_definitions.items():
            try:
                with self.engine.connect() as conn:
                    # Check if index already exists
                    if self.is_postgresql:
                        check_sql = """
                            SELECT 1 FROM pg_indexes 
                            WHERE indexname = :index_name
                        """
                    else:
                        check_sql = """
                            SELECT 1 FROM sqlite_master 
                            WHERE type = 'index' AND name = :index_name
                        """
                    
                    result = conn.execute(text(check_sql), {'index_name': index_name})
                    if result.fetchone():
                        logger.info(f"✓ Index '{index_name}' already exists")
                        index_results[index_name] = True
                        continue
                    
                    # Create index
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info(f"✓ Created index '{index_name}'")
                    index_results[index_name] = True
                    
            except Exception as e:
                logger.error(f"✗ Failed to create index '{index_name}': {e}")
                index_results[index_name] = False
        
        return index_results
    
    def _get_index_definitions(self) -> Dict[str, str]:
        """Get index definitions for optimal performance"""
        indexes = {}
        
        # Articles table indexes
        indexes['idx_articles_url'] = "CREATE INDEX idx_articles_url ON articles(url)"
        indexes['idx_articles_title'] = "CREATE INDEX idx_articles_title ON articles(title)"
        indexes['idx_articles_primary_phase'] = "CREATE INDEX idx_articles_primary_phase ON articles(primary_phase)"
        indexes['idx_articles_difficulty_level'] = "CREATE INDEX idx_articles_difficulty_level ON articles(difficulty_level)"
        indexes['idx_articles_demographic_relevance'] = "CREATE INDEX idx_articles_demographic_relevance ON articles(demographic_relevance)"
        indexes['idx_articles_domain'] = "CREATE INDEX idx_articles_domain ON articles(domain)"
        indexes['idx_articles_is_active'] = "CREATE INDEX idx_articles_is_active ON articles(is_active)"
        indexes['idx_articles_is_featured'] = "CREATE INDEX idx_articles_is_featured ON articles(is_featured)"
        indexes['idx_articles_created_at'] = "CREATE INDEX idx_articles_created_at ON articles(created_at)"
        indexes['idx_articles_publish_date'] = "CREATE INDEX idx_articles_publish_date ON articles(publish_date)"
        
        # Composite indexes for common queries
        indexes['idx_articles_phase_difficulty'] = "CREATE INDEX idx_articles_phase_difficulty ON articles(primary_phase, difficulty_level)"
        indexes['idx_articles_domain_active'] = "CREATE INDEX idx_articles_domain_active ON articles(domain, is_active)"
        
        # User article reads indexes
        indexes['idx_user_article_reads_user_id'] = "CREATE INDEX idx_user_article_reads_user_id ON user_article_reads(user_id)"
        indexes['idx_user_article_reads_article_id'] = "CREATE INDEX idx_user_article_reads_article_id ON user_article_reads(article_id)"
        indexes['idx_user_article_reads_created_at'] = "CREATE INDEX idx_user_article_reads_created_at ON user_article_reads(created_at)"
        indexes['idx_user_article_reads_completed_at'] = "CREATE INDEX idx_user_article_reads_completed_at ON user_article_reads(completed_at)"
        
        # User article bookmarks indexes
        indexes['idx_user_article_bookmarks_user_id'] = "CREATE INDEX idx_user_article_bookmarks_user_id ON user_article_bookmarks(user_id)"
        indexes['idx_user_article_bookmarks_article_id'] = "CREATE INDEX idx_user_article_bookmarks_article_id ON user_article_bookmarks(article_id)"
        indexes['idx_user_article_bookmarks_folder_name'] = "CREATE INDEX idx_user_article_bookmarks_folder_name ON user_article_bookmarks(folder_name)"
        
        # User article ratings indexes
        indexes['idx_user_article_ratings_user_id'] = "CREATE INDEX idx_user_article_ratings_user_id ON user_article_ratings(user_id)"
        indexes['idx_user_article_ratings_article_id'] = "CREATE INDEX idx_user_article_ratings_article_id ON user_article_ratings(article_id)"
        indexes['idx_user_article_ratings_overall_rating'] = "CREATE INDEX idx_user_article_ratings_overall_rating ON user_article_ratings(overall_rating)"
        indexes['idx_user_article_ratings_is_approved'] = "CREATE INDEX idx_user_article_ratings_is_approved ON user_article_ratings(is_approved)"
        
        # User article progress indexes
        indexes['idx_user_article_progress_user_id'] = "CREATE INDEX idx_user_article_progress_user_id ON user_article_progress(user_id)"
        indexes['idx_user_article_progress_article_id'] = "CREATE INDEX idx_user_article_progress_article_id ON user_article_progress(article_id)"
        indexes['idx_user_article_progress_current_phase'] = "CREATE INDEX idx_user_article_progress_current_phase ON user_article_progress(current_phase)"
        
        # Article recommendations indexes
        indexes['idx_article_recommendations_user_id'] = "CREATE INDEX idx_article_recommendations_user_id ON article_recommendations(user_id)"
        indexes['idx_article_recommendations_article_id'] = "CREATE INDEX idx_article_recommendations_article_id ON article_recommendations(article_id)"
        indexes['idx_article_recommendations_score'] = "CREATE INDEX idx_article_recommendations_score ON article_recommendations(recommendation_score)"
        indexes['idx_article_recommendations_recommended_at'] = "CREATE INDEX idx_article_recommendations_recommended_at ON article_recommendations(recommended_at)"
        
        # Article analytics indexes
        indexes['idx_article_analytics_article_id'] = "CREATE INDEX idx_article_analytics_article_id ON article_analytics(article_id)"
        indexes['idx_article_analytics_total_views'] = "CREATE INDEX idx_article_analytics_total_views ON article_analytics(total_views)"
        indexes['idx_article_analytics_total_reads'] = "CREATE INDEX idx_article_analytics_total_reads ON article_analytics(total_reads)"
        indexes['idx_article_analytics_average_rating'] = "CREATE INDEX idx_article_analytics_average_rating ON article_analytics(average_rating)"
        
        # User assessment scores indexes
        indexes['idx_user_assessment_scores_user_id'] = "CREATE INDEX idx_user_assessment_scores_user_id ON user_assessment_scores(user_id)"
        indexes['idx_user_assessment_scores_assessment_date'] = "CREATE INDEX idx_user_assessment_scores_assessment_date ON user_assessment_scores(assessment_date)"
        
        # Article searches indexes
        indexes['idx_article_searches_user_id'] = "CREATE INDEX idx_article_searches_user_id ON article_searches(user_id)"
        indexes['idx_article_searches_created_at'] = "CREATE INDEX idx_article_searches_created_at ON article_searches(created_at)"
        indexes['idx_article_searches_query'] = "CREATE INDEX idx_article_searches_query ON article_searches(search_query)"
        
        return indexes
    
    def configure_postgresql_fulltext_search(self) -> Dict[str, bool]:
        """Configure PostgreSQL full-text search extensions and functions"""
        if not self.is_postgresql:
            logger.info("Skipping PostgreSQL full-text search configuration (not using PostgreSQL)")
            return {'postgresql_fulltext': False}
        
        logger.info("Configuring PostgreSQL full-text search...")
        results = {}
        
        try:
            with self.engine.connect() as conn:
                # Enable required extensions
                extensions = ['pg_trgm', 'unaccent']
                for ext in extensions:
                    try:
                        conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
                        logger.info(f"✓ Extension '{ext}' enabled")
                        results[f'extension_{ext}'] = True
                    except Exception as e:
                        logger.error(f"✗ Failed to enable extension '{ext}': {e}")
                        results[f'extension_{ext}'] = False
                
                # Create full-text search function
                fulltext_function = """
                CREATE OR REPLACE FUNCTION update_article_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.search_vector := 
                        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('english', COALESCE(NEW.content_preview, '')), 'B') ||
                        setweight(to_tsvector('english', COALESCE(NEW.meta_description, '')), 'C') ||
                        setweight(to_tsvector('english', COALESCE(NEW.key_topics::text, '')), 'B');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
                
                try:
                    conn.execute(text(fulltext_function))
                    logger.info("✓ Full-text search function created")
                    results['fulltext_function'] = True
                except Exception as e:
                    logger.error(f"✗ Failed to create full-text search function: {e}")
                    results['fulltext_function'] = False
                
                # Create trigger for automatic search vector updates
                trigger_sql = """
                DROP TRIGGER IF EXISTS update_article_search_vector_trigger ON articles;
                CREATE TRIGGER update_article_search_vector_trigger
                    BEFORE INSERT OR UPDATE ON articles
                    FOR EACH ROW EXECUTE FUNCTION update_article_search_vector();
                """
                
                try:
                    conn.execute(text(trigger_sql))
                    logger.info("✓ Full-text search trigger created")
                    results['fulltext_trigger'] = True
                except Exception as e:
                    logger.error(f"✗ Failed to create full-text search trigger: {e}")
                    results['fulltext_trigger'] = False
                
                # Create GIN index for full-text search
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_search_vector ON articles USING GIN(search_vector)"))
                    logger.info("✓ Full-text search GIN index created")
                    results['fulltext_gin_index'] = True
                except Exception as e:
                    logger.error(f"✗ Failed to create full-text search GIN index: {e}")
                    results['fulltext_gin_index'] = False
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to configure PostgreSQL full-text search: {e}")
            results['postgresql_fulltext'] = False
        
        return results
    
    def test_database_connectivity(self) -> Dict[str, bool]:
        """Test database connectivity and permissions"""
        logger.info("Testing database connectivity and permissions...")
        
        tests = {}
        
        # Test basic connectivity
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                if result.fetchone()[0] == 1:
                    logger.info("✓ Basic connectivity test passed")
                    tests['basic_connectivity'] = True
                else:
                    logger.error("✗ Basic connectivity test failed")
                    tests['basic_connectivity'] = False
        except Exception as e:
            logger.error(f"✗ Basic connectivity test failed: {e}")
            tests['basic_connectivity'] = False
        
        # Test read permissions
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM articles"))
                count = result.fetchone()[0]
                logger.info(f"✓ Read permissions test passed (found {count} articles)")
                tests['read_permissions'] = True
        except Exception as e:
            logger.error(f"✗ Read permissions test failed: {e}")
            tests['read_permissions'] = False
        
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
                    'content': 'Test content',
                    'phase': 'DO',
                    'level': 'Beginner',
                    'domain': 'test.com'
                })
                
                # Clean up test record
                conn.execute(text("DELETE FROM articles WHERE id = :id"), {'id': test_id})
                conn.commit()
                
                logger.info("✓ Write permissions test passed")
                tests['write_permissions'] = True
        except Exception as e:
            logger.error(f"✗ Write permissions test failed: {e}")
            tests['write_permissions'] = False
        
        # Test performance with sample queries
        try:
            with self.engine.connect() as conn:
                start_time = time.time()
                
                # Test complex query performance
                result = conn.execute(text("""
                    SELECT a.title, a.primary_phase, a.difficulty_level, 
                           COUNT(r.id) as read_count, AVG(ar.overall_rating) as avg_rating
                    FROM articles a
                    LEFT JOIN user_article_reads r ON a.id = r.article_id
                    LEFT JOIN user_article_ratings ar ON a.id = ar.article_id
                    WHERE a.is_active = 1
                    GROUP BY a.id, a.title, a.primary_phase, a.difficulty_level
                    ORDER BY read_count DESC
                    LIMIT 10
                """))
                
                query_time = time.time() - start_time
                rows = result.fetchall()
                
                logger.info(f"✓ Performance test passed ({len(rows)} rows in {query_time:.3f}s)")
                tests['performance_test'] = True
                tests['query_time'] = query_time
                
        except Exception as e:
            logger.error(f"✗ Performance test failed: {e}")
            tests['performance_test'] = False
        
        return tests
    
    def generate_performance_recommendations(self) -> List[str]:
        """Generate performance recommendations based on current state"""
        logger.info("Generating performance recommendations...")
        
        recommendations = []
        
        # Check table sizes
        try:
            with self.engine.connect() as conn:
                for table in ['articles', 'user_article_reads', 'user_article_ratings']:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    
                    if count > 10000:
                        recommendations.append(f"Consider partitioning {table} table (current size: {count:,} rows)")
                    elif count > 1000:
                        recommendations.append(f"Monitor {table} table growth (current size: {count:,} rows)")
        except Exception as e:
            logger.warning(f"Could not check table sizes: {e}")
        
        # Check for missing indexes
        if self.is_postgresql:
            try:
                with self.engine.connect() as conn:
                    # Check for slow queries
                    result = conn.execute(text("""
                        SELECT schemaname, tablename, attname, n_distinct, correlation
                        FROM pg_stats 
                        WHERE schemaname = 'public' 
                        AND tablename IN ('articles', 'user_article_reads', 'user_article_ratings')
                        ORDER BY n_distinct DESC
                    """))
                    
                    stats = result.fetchall()
                    for stat in stats:
                        if stat[3] < 10:  # Low distinct values
                            recommendations.append(f"Consider index on {stat[1]}.{stat[2]} (low distinct values: {stat[3]})")
            except Exception as e:
                logger.warning(f"Could not analyze table statistics: {e}")
        
        # General recommendations
        recommendations.extend([
            "Consider implementing database connection pooling for production",
            "Set up regular database maintenance (VACUUM, ANALYZE for PostgreSQL)",
            "Monitor query performance and add indexes as needed",
            "Consider implementing read replicas for high-traffic scenarios",
            "Set up database backup and recovery procedures"
        ])
        
        return recommendations
    
    def run_full_verification(self) -> Dict[str, any]:
        """Run complete database verification and optimization"""
        logger.info("Starting comprehensive database verification...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'database_url': self.database_url,
            'is_postgresql': self.is_postgresql
        }
        
        # Connect to database
        if not self.connect():
            results['status'] = 'failed'
            results['error'] = 'Could not connect to database'
            return results
        
        # Run all verification steps
        results['table_verification'] = self.verify_article_library_tables()
        results['index_setup'] = self.setup_database_indexes()
        results['fulltext_search'] = self.configure_postgresql_fulltext_search()
        results['connectivity_tests'] = self.test_database_connectivity()
        results['recommendations'] = self.generate_performance_recommendations()
        
        # Determine overall status
        all_tests = []
        all_tests.extend(results['table_verification'].values())
        all_tests.extend(results['index_setup'].values())
        all_tests.extend(results['fulltext_search'].values())
        all_tests.extend(results['connectivity_tests'].values())
        
        if all(all_tests):
            results['status'] = 'success'
            logger.info("✓ All database verification tests passed!")
        else:
            results['status'] = 'partial_success'
            failed_count = len([t for t in all_tests if not t])
            logger.warning(f"⚠ {failed_count} tests failed - check logs for details")
        
        return results
    
    def generate_report(self, results: Dict[str, any]) -> str:
        """Generate a comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("MINGUS ARTICLE LIBRARY DATABASE VERIFICATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {results['timestamp']}")
        report.append(f"Database: {results['database_url']}")
        report.append(f"PostgreSQL: {results['is_postgresql']}")
        report.append(f"Status: {results['status'].upper()}")
        report.append("")
        
        # Table verification results
        report.append("TABLE VERIFICATION:")
        report.append("-" * 40)
        for table, status in results['table_verification'].items():
            status_symbol = "✓" if status else "✗"
            report.append(f"{status_symbol} {table}")
        report.append("")
        
        # Index setup results
        report.append("INDEX SETUP:")
        report.append("-" * 40)
        success_count = sum(1 for status in results['index_setup'].values() if status)
        total_count = len(results['index_setup'])
        report.append(f"Indexes created: {success_count}/{total_count}")
        report.append("")
        
        # Full-text search results
        if results['is_postgresql']:
            report.append("POSTGRESQL FULL-TEXT SEARCH:")
            report.append("-" * 40)
            for component, status in results['fulltext_search'].items():
                status_symbol = "✓" if status else "✗"
                report.append(f"{status_symbol} {component}")
            report.append("")
        
        # Connectivity test results
        report.append("CONNECTIVITY TESTS:")
        report.append("-" * 40)
        for test, status in results['connectivity_tests'].items():
            if test != 'query_time':
                status_symbol = "✓" if status else "✗"
                report.append(f"{status_symbol} {test}")
        if 'query_time' in results['connectivity_tests']:
            report.append(f"Query performance: {results['connectivity_tests']['query_time']:.3f}s")
        report.append("")
        
        # Recommendations
        report.append("PERFORMANCE RECOMMENDATIONS:")
        report.append("-" * 40)
        for i, rec in enumerate(results['recommendations'], 1):
            report.append(f"{i}. {rec}")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main execution function"""
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
    
    logger.info("Starting MINGUS Article Library Database Verification")
    logger.info(f"Database URL: {database_url}")
    
    # Create verifier instance
    verifier = DatabaseVerifier(database_url)
    
    # Run full verification
    results = verifier.run_full_verification()
    
    # Generate and save report
    report = verifier.generate_report(results)
    
    # Save report to file
    report_filename = f"database_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    # Print report to console
    print(report)
    
    logger.info(f"Report saved to: {report_filename}")
    
    # Exit with appropriate code
    if results['status'] == 'success':
        logger.info("Database verification completed successfully!")
        sys.exit(0)
    else:
        logger.warning("Database verification completed with issues - check report for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
