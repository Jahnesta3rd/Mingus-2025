#!/usr/bin/env python3
"""
Security Monitoring Example Script
Demonstrates how to use the security performance monitoring system
"""

import time
import random
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from monitoring.security_monitor import SecurityPerformanceMonitor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

def simulate_encryption_operation(algorithm, key_size, data_size):
    """Simulate encryption/decryption operation with realistic timing"""
    # Simulate different performance characteristics for different algorithms
    if algorithm == 'AES-256':
        base_time = 10  # 10ms base time
        size_factor = data_size / 1024  # Linear scaling with data size
        random_factor = random.uniform(0.8, 1.2)  # 20% random variation
        return base_time * size_factor * random_factor
    elif algorithm == 'RSA-2048':
        base_time = 40  # 40ms base time (RSA is slower)
        size_factor = (data_size / 256) ** 0.5  # Sub-linear scaling
        random_factor = random.uniform(0.7, 1.3)  # 30% random variation
        return base_time * size_factor * random_factor
    else:
        return random.uniform(5, 50)  # Generic random timing

def simulate_audit_logging(operation_type, log_size, batch_size=None):
    """Simulate audit logging operation"""
    # Simulate different performance for different operation types
    base_times = {
        'user_login': 5,
        'data_access': 8,
        'security_event': 12,
        'admin_action': 15,
        'system_event': 6
    }
    
    base_time = base_times.get(operation_type, 10)
    
    # Batch processing is more efficient
    if batch_size and batch_size > 1:
        base_time = base_time / (batch_size ** 0.5)  # Square root scaling
    
    # Add some random variation
    random_factor = random.uniform(0.8, 1.2)
    return base_time * random_factor

def simulate_key_rotation(key_type):
    """Simulate key rotation operation"""
    # Different key types have different rotation times
    rotation_times = {
        'encryption_key': 2000,  # 2 seconds
        'signing_key': 1500,     # 1.5 seconds
        'session_key': 500,      # 0.5 seconds
        'master_key': 5000       # 5 seconds
    }
    
    base_time = rotation_times.get(key_type, 1000)
    random_factor = random.uniform(0.9, 1.1)  # 10% random variation
    return base_time * random_factor

def run_security_monitoring_demo():
    """Run a comprehensive demo of the security monitoring system"""
    
    # Database connection (you'll need to set DATABASE_URL environment variable)
    database_url = "postgresql://localhost/mingus_db"  # Update with your actual DB URL
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.info("Running in demo mode without database...")
        db_session = None
    
    # Initialize security monitor
    if db_session:
        monitor = SecurityPerformanceMonitor(db_session)
        logger.info("Security monitor initialized with database")
    else:
        logger.info("Running without database - metrics will not be stored")
        monitor = None
    
    logger.info("Starting Security Monitoring Demo...")
    logger.info("=" * 50)
    
    # Demo 1: Security Operations Monitoring
    logger.info("\n🔒 Demo 1: Security Operations Monitoring")
    logger.info("-" * 40)
    
    security_operations = [
        ('user_authentication', {'user_id': 'user123', 'ip': '192.168.1.100'}),
        ('password_validation', {'user_id': 'user123', 'strength': 'strong'}),
        ('session_creation', {'user_id': 'user123', 'session_id': 'sess_abc123'}),
        ('permission_check', {'user_id': 'user123', 'resource': '/api/data'}),
        ('rate_limit_check', {'user_id': 'user123', 'endpoint': '/api/login'})
    ]
    
    for operation_type, metadata in security_operations:
        if monitor:
            with monitor.measure_security_operation(operation_type, metadata):
                # Simulate operation time
                operation_time = random.uniform(10, 100)
                time.sleep(operation_time / 1000)  # Convert to seconds
                logger.info(f"✅ {operation_type}: {operation_time:.2f}ms")
        else:
            operation_time = random.uniform(10, 100)
            time.sleep(operation_time / 1000)
            logger.info(f"✅ {operation_type}: {operation_time:.2f}ms (demo mode)")
    
    # Demo 2: Encryption Operations Monitoring
    logger.info("\n🔐 Demo 2: Encryption Operations Monitoring")
    logger.info("-" * 40)
    
    encryption_scenarios = [
        ('AES-256', 256, 'encrypt', 1024),
        ('AES-256', 256, 'decrypt', 1024),
        ('RSA-2048', 2048, 'encrypt', 256),
        ('RSA-2048', 2048, 'decrypt', 256),
        ('AES-128', 128, 'encrypt', 2048),
        ('AES-128', 128, 'decrypt', 2048)
    ]
    
    for algorithm, key_size, operation, data_size in encryption_scenarios:
        if monitor:
            with monitor.measure_encryption_operation(algorithm, key_size, operation, data_size):
                # Simulate encryption time
                encryption_time = simulate_encryption_operation(algorithm, key_size, data_size)
                time.sleep(encryption_time / 1000)
                logger.info(f"✅ {algorithm} {key_size}bit {operation}: {encryption_time:.2f}ms")
        else:
            encryption_time = simulate_encryption_operation(algorithm, key_size, data_size)
            time.sleep(encryption_time / 1000)
            logger.info(f"✅ {algorithm} {key_size}bit {operation}: {encryption_time:.2f}ms (demo mode)")
    
    # Demo 3: Audit Logging Performance
    logger.info("\n📊 Demo 3: Audit Logging Performance")
    logger.info("-" * 40)
    
    audit_scenarios = [
        ('user_login', 512, 1),
        ('data_access', 1024, 5),
        ('security_event', 2048, 1),
        ('admin_action', 1536, 3),
        ('system_event', 768, 10)
    ]
    
    for operation_type, log_size, batch_size in audit_scenarios:
        if monitor:
            with monitor.measure_audit_logging(operation_type, log_size, batch_size):
                # Simulate audit logging time
                logging_time = simulate_audit_logging(operation_type, log_size, batch_size)
                time.sleep(logging_time / 1000)
                logger.info(f"✅ {operation_type} (batch: {batch_size}): {logging_time:.2f}ms")
        else:
            logging_time = simulate_audit_logging(operation_type, log_size, batch_size)
            time.sleep(logging_time / 1000)
            logger.info(f"✅ {operation_type} (batch: {batch_size}): {logging_time:.2f}ms (demo mode)")
    
    # Demo 4: Key Rotation Performance
    logger.info("\n🔑 Demo 4: Key Rotation Performance")
    logger.info("-" * 40)
    
    key_rotation_scenarios = [
        ('encryption_key', 'key_old_001', 'key_new_001'),
        ('signing_key', 'key_old_002', 'key_new_002'),
        ('session_key', 'key_old_003', 'key_new_003'),
        ('master_key', 'key_old_004', 'key_new_004')
    ]
    
    for key_type, old_key_id, new_key_id in key_rotation_scenarios:
        if monitor:
            with monitor.measure_key_rotation(key_type, old_key_id, new_key_id):
                # Simulate key rotation time
                rotation_time = simulate_key_rotation(key_type)
                time.sleep(rotation_time / 1000)
                logger.info(f"✅ {key_type} rotation: {rotation_time:.2f}ms")
        else:
            rotation_time = simulate_key_rotation(key_type)
            time.sleep(rotation_time / 1000)
            logger.info(f"✅ {key_type} rotation: {rotation_time:.2f}ms (demo mode)")
    
    # Demo 5: Performance Analysis
    if monitor:
        logger.info("\n📈 Demo 5: Performance Analysis")
        logger.info("-" * 40)
        
        # Get performance summary
        summary = monitor.get_performance_summary(hours=1)
        logger.info(f"📊 Performance Summary (last hour):")
        logger.info(f"   - Total operations: {len(summary.get('overall_performance', []))}")
        logger.info(f"   - Encryption operations: {len(summary.get('encryption_performance', []))}")
        logger.info(f"   - Audit operations: {len(summary.get('audit_log_performance', []))}")
        
        # Get real-time metrics
        realtime = monitor.get_real_time_metrics()
        logger.info(f"🔄 Real-time Metrics:")
        logger.info(f"   - Health Score: {realtime.get('current_health_score', 'N/A')}")
        logger.info(f"   - Active Alerts: {realtime.get('active_alerts', 'N/A')}")
        logger.info(f"   - Buffer Size: {realtime.get('buffer_size', 'N/A')}")
    
    logger.info("\n" + "=" * 50)
    logger.info("🎉 Security Monitoring Demo Completed!")
    
    if monitor:
        logger.info("💡 Check your database for stored metrics")
        logger.info("💡 Monitor Prometheus metrics for real-time data")
        logger.info("💡 Use /health/security endpoint for health checks")
    
    logger.info("💡 Run with DATABASE_URL environment variable for full functionality")

def run_health_check_demo():
    """Demo the health check endpoints"""
    logger.info("\n🏥 Health Check Demo")
    logger.info("=" * 30)
    
    logger.info("Available health check endpoints:")
    logger.info("  GET /health - Basic health check")
    logger.info("  GET /health/detailed - Comprehensive health check")
    logger.info("  GET /health/security - Security-specific health check")
    logger.info("  GET /health/readiness - Kubernetes readiness probe")
    logger.info("  GET /health/liveness - Kubernetes liveness probe")
    logger.info("  GET /health/startup - Kubernetes startup probe")
    
    logger.info("\nTo test these endpoints:")
    logger.info("1. Start your Flask application")
    logger.info("2. Make requests to the health endpoints")
    logger.info("3. Check the response for security metrics")

if __name__ == "__main__":
    # Configure logging
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    try:
        # Run the main demo
        run_security_monitoring_demo()
        
        # Run health check demo
        run_health_check_demo()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed with error: {e}")
        logger.info("💡 Make sure your database is running and accessible")
        logger.info("💡 Check that DATABASE_URL environment variable is set correctly")
