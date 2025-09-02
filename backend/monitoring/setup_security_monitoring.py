#!/usr/bin/env python3
"""
Security Monitoring Setup Script
Creates necessary database tables and initializes the security monitoring system
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_security_monitoring_tables(engine):
    """Create all necessary tables for security monitoring"""
    
    # Security Performance Metrics Table
    security_metrics_table = """
    CREATE TABLE IF NOT EXISTS security_performance_metrics (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        operation_type VARCHAR(100) NOT NULL,
        duration_ms DECIMAL(10,3) NOT NULL,
        success BOOLEAN NOT NULL DEFAULT true,
        error_message TEXT,
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Encryption Performance Metrics Table
    encryption_metrics_table = """
    CREATE TABLE IF NOT EXISTS encryption_performance_metrics (
        id SERIAL PRIMARY KEY,
        algorithm VARCHAR(50) NOT NULL,
        key_size INTEGER NOT NULL,
        operation VARCHAR(20) NOT NULL CHECK (operation IN ('encrypt', 'decrypt')),
        data_size_bytes BIGINT NOT NULL,
        duration_ms DECIMAL(10,3) NOT NULL,
        success BOOLEAN NOT NULL DEFAULT true,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Audit Log Performance Metrics Table
    audit_log_metrics_table = """
    CREATE TABLE IF NOT EXISTS audit_log_performance_metrics (
        id SERIAL PRIMARY KEY,
        operation_type VARCHAR(100) NOT NULL,
        duration_ms DECIMAL(10,3) NOT NULL,
        log_size_bytes BIGINT NOT NULL,
        success BOOLEAN NOT NULL DEFAULT true,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        batch_size INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Key Rotation Performance Metrics Table
    key_rotation_metrics_table = """
    CREATE TABLE IF NOT EXISTS key_rotation_performance_metrics (
        id SERIAL PRIMARY KEY,
        key_type VARCHAR(50) NOT NULL,
        old_key_id VARCHAR(100) NOT NULL,
        new_key_id VARCHAR(100) NOT NULL,
        duration_ms DECIMAL(10,3) NOT NULL,
        success BOOLEAN NOT NULL DEFAULT true,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        affected_entities INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Security Monitoring Summary Table
    summary_table = """
    CREATE TABLE IF NOT EXISTS security_monitoring_summary (
        id SERIAL PRIMARY KEY,
        metric_type VARCHAR(50) NOT NULL,
        metric_value JSONB NOT NULL,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    tables = [
        ("security_performance_metrics", security_metrics_table),
        ("encryption_performance_metrics", encryption_metrics_table),
        ("audit_log_performance_metrics", audit_log_metrics_table),
        ("key_rotation_performance_metrics", key_rotation_metrics_table),
        ("security_monitoring_summary", summary_table)
    ]
    
    try:
        with engine.connect() as conn:
            for table_name, create_sql in tables:
                logger.info(f"Creating table: {table_name}")
                conn.execute(text(create_sql))
                conn.commit()
                logger.info(f"Successfully created table: {table_name}")
                
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        raise

def create_indexes(engine):
    """Create indexes for better query performance"""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_security_performance_timestamp ON security_performance_metrics(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_security_performance_operation_type ON security_performance_metrics(operation_type);",
        "CREATE INDEX IF NOT EXISTS idx_security_performance_success ON security_performance_metrics(success);",
        
        "CREATE INDEX IF NOT EXISTS idx_encryption_performance_timestamp ON encryption_performance_metrics(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_encryption_performance_algorithm ON encryption_performance_metrics(algorithm);",
        "CREATE INDEX IF NOT EXISTS idx_encryption_performance_operation ON encryption_performance_metrics(operation);",
        
        "CREATE INDEX IF NOT EXISTS idx_audit_log_performance_timestamp ON audit_log_performance_metrics(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_performance_operation_type ON audit_log_performance_metrics(operation_type);",
        
        "CREATE INDEX IF NOT EXISTS idx_key_rotation_performance_timestamp ON key_rotation_performance_metrics(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_key_rotation_performance_key_type ON key_rotation_performance_metrics(key_type);",
        
        "CREATE INDEX IF NOT EXISTS idx_security_monitoring_summary_metric_type ON security_monitoring_summary(metric_type);",
        "CREATE INDEX IF NOT EXISTS idx_security_monitoring_summary_last_updated ON security_monitoring_summary(last_updated);"
    ]
    
    try:
        with engine.connect() as conn:
            for index_sql in indexes:
                logger.info(f"Creating index: {index_sql}")
                conn.execute(text(index_sql))
                conn.commit()
                
    except SQLAlchemyError as e:
        logger.error(f"Error creating indexes: {e}")
        raise

def create_views(engine):
    """Create views for common queries"""
    
    views = {
        "security_performance_summary": """
        CREATE OR REPLACE VIEW security_performance_summary AS
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour_bucket,
            operation_type,
            COUNT(*) as total_operations,
            AVG(duration_ms) as avg_duration_ms,
            MAX(duration_ms) as max_duration_ms,
            MIN(duration_ms) as min_duration_ms,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
            SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations,
            (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100) as success_rate_percent
        FROM security_performance_metrics
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY DATE_TRUNC('hour', timestamp), operation_type
        ORDER BY hour_bucket DESC, operation_type;
        """,
        
        "encryption_performance_summary": """
        CREATE OR REPLACE VIEW encryption_performance_summary AS
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour_bucket,
            algorithm,
            key_size,
            operation,
            COUNT(*) as total_operations,
            AVG(duration_ms) as avg_duration_ms,
            MAX(duration_ms) as max_duration_ms,
            AVG(data_size_bytes) as avg_data_size_bytes,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
            (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100) as success_rate_percent
        FROM encryption_performance_metrics
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY DATE_TRUNC('hour', timestamp), algorithm, key_size, operation
        ORDER BY hour_bucket DESC, algorithm, key_size, operation;
        """,
        
        "audit_log_performance_summary": """
        CREATE OR REPLACE VIEW audit_log_performance_summary AS
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour_bucket,
            operation_type,
            COUNT(*) as total_operations,
            AVG(duration_ms) as avg_duration_ms,
            MAX(duration_ms) as max_duration_ms,
            AVG(log_size_bytes) as avg_log_size_bytes,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
            SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations,
            (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100) as success_rate_percent
        FROM audit_log_performance_metrics
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY DATE_TRUNC('hour', timestamp), operation_type
        ORDER BY hour_bucket DESC, operation_type;
        """
    }
    
    try:
        with engine.connect() as conn:
            for view_name, create_sql in views.items():
                logger.info(f"Creating view: {view_name}")
                conn.execute(text(create_sql))
                conn.commit()
                logger.info(f"Successfully created view: {view_name}")
                
    except SQLAlchemyError as e:
        logger.error(f"Error creating views: {e}")
        raise

def insert_sample_data(engine):
    """Insert sample data for testing"""
    
    sample_data = [
        """
        INSERT INTO security_performance_metrics (timestamp, operation_type, duration_ms, success, metadata) VALUES
        (NOW() - INTERVAL '1 hour', 'user_authentication', 45.2, true, '{"user_id": "test123", "ip": "192.168.1.1"}'),
        (NOW() - INTERVAL '30 minutes', 'password_validation', 12.8, true, '{"user_id": "test123"}'),
        (NOW() - INTERVAL '15 minutes', 'session_creation', 23.1, true, '{"user_id": "test123", "session_id": "sess_abc123"}');
        """,
        
        """
        INSERT INTO encryption_performance_metrics (algorithm, key_size, operation, data_size_bytes, duration_ms, success, timestamp) VALUES
        ('AES-256', 256, 'encrypt', 1024, 15.3, true, NOW() - INTERVAL '1 hour'),
        ('AES-256', 256, 'decrypt', 1024, 12.7, true, NOW() - INTERVAL '1 hour'),
        ('RSA-2048', 2048, 'encrypt', 256, 45.2, true, NOW() - INTERVAL '30 minutes');
        """,
        
        """
        INSERT INTO audit_log_performance_metrics (operation_type, duration_ms, log_size_bytes, success, timestamp, batch_size) VALUES
        ('user_login', 8.5, 512, true, NOW() - INTERVAL '1 hour', 1),
        ('data_access', 12.3, 1024, true, NOW() - INTERVAL '30 minutes', 5),
        ('security_event', 15.7, 2048, true, NOW() - INTERVAL '15 minutes', 1);
        """,
        
        """
        INSERT INTO security_monitoring_summary (metric_type, metric_value) VALUES
        ('system_health_score', '{"score": 100, "status": "healthy"}'),
        ('pci_compliance_status', '{"status": "compliant", "last_check": null}'),
        ('encryption_performance', '{"avg_duration_ms": 0, "success_rate": 100}'),
        ('audit_log_performance', '{"avg_duration_ms": 0, "success_rate": 100}');
        """
    ]
    
    try:
        with engine.connect() as conn:
            for i, insert_sql in enumerate(sample_data):
                logger.info(f"Inserting sample data batch {i+1}")
                conn.execute(text(insert_sql))
                conn.commit()
                logger.info(f"Successfully inserted sample data batch {i+1}")
                
    except SQLAlchemyError as e:
        logger.error(f"Error inserting sample data: {e}")
        # Don't raise here as sample data is optional
        logger.warning("Sample data insertion failed, but this is not critical")

def main():
    """Main setup function"""
    
    # Get database connection string from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Create database engine
        logger.info("Connecting to database...")
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Create tables
        logger.info("Creating security monitoring tables...")
        create_security_monitoring_tables(engine)
        
        # Create indexes
        logger.info("Creating indexes...")
        create_indexes(engine)
        
        # Create views
        logger.info("Creating views...")
        create_views(engine)
        
        # Insert sample data
        logger.info("Inserting sample data...")
        insert_sample_data(engine)
        
        logger.info("Security monitoring setup completed successfully!")
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
