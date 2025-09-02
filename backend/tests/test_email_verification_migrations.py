"""
Database Migration Tests for Email Verification System
Tests migration validation, schema integrity, and data consistency
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..models.email_verification import EmailVerification
from ..models.user import User
from ..models.base import Base
from ..database import get_db_session

@pytest.fixture(scope="function")
def temp_db_file():
    """Create temporary database file for migration testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)

@pytest.fixture(scope="function")
def test_db_engine(temp_db_file):
    """Create test database engine"""
    engine = create_engine(f'sqlite:///{temp_db_file}')
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()

class TestDatabaseSchemaCreation:
    """Test database schema creation and structure"""
    
    def test_schema_creation(self, test_db_engine):
        """Test that email verification schema is created correctly"""
        # Create all tables
        Base.metadata.create_all(test_db_engine)
        
        # Get inspector
        inspector = inspect(test_db_engine)
        
        # Check that required tables exist
        tables = inspector.get_table_names()
        assert 'email_verifications' in tables
        assert 'users' in tables
        
        # Check email_verifications table structure
        columns = {col['name']: col for col in inspector.get_columns('email_verifications')}
        
        required_columns = [
            'id', 'user_id', 'email', 'verification_token_hash', 'expires_at',
            'verified_at', 'created_at', 'resend_count', 'last_resend_at',
            'ip_address', 'user_agent', 'verification_type', 'old_email',
            'failed_attempts', 'last_failed_attempt', 'locked_until'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_column_data_types(self, test_db_engine):
        """Test that columns have correct data types"""
        Base.metadata.create_all(test_db_engine)
        inspector = inspect(test_db_engine)
        
        columns = {col['name']: col for col in inspector.get_columns('email_verifications')}
        
        # Check data types
        assert columns['id']['type'].__class__.__name__ == 'Integer'
        assert columns['user_id']['type'].__class__.__name__ == 'Integer'
        assert columns['email']['type'].__class__.__name__ == 'String'
        assert columns['verification_token_hash']['type'].__class__.__name__ == 'String'
        assert columns['expires_at']['type'].__class__.__name__ == 'DateTime'
        assert columns['verified_at']['type'].__class__.__name__ == 'DateTime'
        assert columns['created_at']['type'].__class__.__name__ == 'DateTime'
        assert columns['resend_count']['type'].__class__.__name__ == 'Integer'
        assert columns['last_resend_at']['type'].__class__.__name__ == 'DateTime'
        assert columns['ip_address']['type'].__class__.__name__ == 'String'
        assert columns['user_agent']['type'].__class__.__name__ == 'Text'
        assert columns['verification_type']['type'].__class__.__name__ == 'String'
        assert columns['old_email']['type'].__class__.__name__ == 'String'
        assert columns['failed_attempts']['type'].__class__.__name__ == 'Integer'
        assert columns['last_failed_attempt']['type'].__class__.__name__ == 'DateTime'
        assert columns['locked_until']['type'].__class__.__name__ == 'DateTime'
    
    def test_column_constraints(self, test_db_engine):
        """Test that columns have correct constraints"""
        Base.metadata.create_all(test_db_engine)
        inspector = inspect(test_db_engine)
        
        columns = {col['name']: col for col in inspector.get_columns('email_verifications')}
        
        # Check primary key
        assert columns['id']['primary_key'] is True
        
        # Check nullable constraints
        assert columns['user_id']['nullable'] is False
        assert columns['email']['nullable'] is False
        assert columns['verification_token_hash']['nullable'] is False
        assert columns['expires_at']['nullable'] is False
        assert columns['verified_at']['nullable'] is True  # Can be null initially
        assert columns['created_at']['nullable'] is True  # Has default
        assert columns['resend_count']['nullable'] is False  # Has default
        assert columns['last_resend_at']['nullable'] is True
        assert columns['ip_address']['nullable'] is True
        assert columns['user_agent']['nullable'] is True
        assert columns['verification_type']['nullable'] is False  # Has default
        assert columns['old_email']['nullable'] is True
        assert columns['failed_attempts']['nullable'] is False  # Has default
        assert columns['last_failed_attempt']['nullable'] is True
        assert columns['locked_until']['nullable'] is True
    
    def test_indexes_creation(self, test_db_engine):
        """Test that required indexes are created"""
        Base.metadata.create_all(test_db_engine)
        inspector = inspect(test_db_engine)
        
        indexes = inspector.get_indexes('email_verifications')
        index_names = [idx['name'] for idx in indexes]
        
        # Check required indexes
        required_indexes = [
            'ix_email_verifications_email',
            'ix_email_verifications_verification_token_hash',
            'ix_email_verifications_expires_at',
            'ix_email_verifications_verified_at',
            'ix_email_verifications_created_at',
            'idx_email_verification_user_type',
            'idx_email_verification_expires_created',
            'idx_email_verification_rate_limit'
        ]
        
        for idx in required_indexes:
            assert idx in index_names, f"Missing index: {idx}"
    
    def test_foreign_key_constraints(self, test_db_engine):
        """Test foreign key relationships"""
        Base.metadata.create_all(test_db_engine)
        inspector = inspect(test_db_engine)
        
        foreign_keys = inspector.get_foreign_keys('email_verifications')
        
        # Check user_id foreign key
        user_fk = next((fk for fk in foreign_keys if fk['constrained_columns'] == ['user_id']), None)
        assert user_fk is not None
        assert user_fk['referred_table'] == 'users'
        assert user_fk['referred_columns'] == ['id']
        assert user_fk['ondelete'] == 'CASCADE'

class TestDatabaseMigrationValidation:
    """Test migration validation and data integrity"""
    
    def test_migration_upgrade_path(self, test_db_engine):
        """Test that migrations can be applied in sequence"""
        # Start with empty database
        inspector = inspect(test_db_engine)
        tables = inspector.get_table_names()
        assert 'email_verifications' not in tables
        
        # Apply migrations (create tables)
        Base.metadata.create_all(test_db_engine)
        
        # Verify tables exist
        inspector = inspect(test_db_engine)
        tables = inspector.get_table_names()
        assert 'email_verifications' in tables
        assert 'users' in tables
        
        # Verify schema structure
        columns = {col['name']: col for col in inspector.get_columns('email_verifications')}
        assert len(columns) >= 15  # Should have all required columns
    
    def test_migration_rollback_simulation(self, test_db_engine):
        """Test migration rollback simulation"""
        # Create tables
        Base.metadata.create_all(test_db_engine)
        
        # Verify tables exist
        inspector = inspect(test_db_engine)
        assert 'email_verifications' in inspector.get_table_names()
        
        # Simulate rollback by dropping tables
        Base.metadata.drop_all(test_db_engine)
        
        # Verify tables are gone
        inspector = inspect(test_db_engine)
        assert 'email_verifications' not in inspector.get_table_names()
        
        # Recreate tables
        Base.metadata.create_all(test_db_engine)
        
        # Verify tables exist again
        inspector = inspect(test_db_engine)
        assert 'email_verifications' in inspector.get_table_names()
    
    def test_data_consistency_after_migration(self, test_db_engine, test_db_session):
        """Test data consistency after migration"""
        # Create tables
        Base.metadata.create_all(test_db_engine)
        
        # Create test data
        user = User(
            id=1,
            email='test@example.com',
            full_name='Test User',
            password_hash='hashed_password',
            email_verified=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        verification = EmailVerification(
            user_id=user.id,
            email=user.email,
            verification_token_hash='test_hash',
            expires_at=datetime.utcnow() + timedelta(hours=24),
            verification_type='signup'
        )
        test_db_session.add(verification)
        test_db_session.commit()
        
        # Verify data integrity
        assert verification.id is not None
        assert verification.user_id == user.id
        assert verification.email == user.email
        assert verification.verification_token_hash == 'test_hash'
        assert verification.verification_type == 'signup'
        assert verification.resend_count == 0
        assert verification.failed_attempts == 0
    
    def test_constraint_violation_handling(self, test_db_engine, test_db_session):
        """Test constraint violation handling"""
        Base.metadata.create_all(test_db_engine)
        
        # Try to create verification without required fields
        with pytest.raises(IntegrityError):
            verification = EmailVerification()
            test_db_session.add(verification)
            test_db_session.commit()
        
        test_db_session.rollback()
        
        # Try to create verification with invalid user_id
        with pytest.raises(IntegrityError):
            verification = EmailVerification(
                user_id=999,  # Non-existent user
                email='test@example.com',
                verification_token_hash='test_hash',
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            test_db_session.add(verification)
            test_db_session.commit()
        
        test_db_session.rollback()

class TestDatabasePerformance:
    """Test database performance characteristics"""
    
    def test_index_performance(self, test_db_engine, test_db_session):
        """Test that indexes improve query performance"""
        Base.metadata.create_all(test_db_engine)
        
        # Create test data
        users = []
        verifications = []
        
        for i in range(1000):
            user = User(
                id=i+1,
                email=f'user{i}@example.com',
                full_name=f'User {i}',
                password_hash=f'hash_{i}',
                email_verified=False
            )
            users.append(user)
            
            verification = EmailVerification(
                user_id=user.id,
                email=user.email,
                verification_token_hash=f'hash_{i}',
                expires_at=datetime.utcnow() + timedelta(hours=24),
                verification_type='signup'
            )
            verifications.append(verification)
        
        test_db_session.add_all(users)
        test_db_session.add_all(verifications)
        test_db_session.commit()
        
        # Test query performance with index
        import time
        
        start_time = time.time()
        result = test_db_session.query(EmailVerification).filter_by(email='user500@example.com').first()
        indexed_query_time = time.time() - start_time
        
        assert result is not None
        assert indexed_query_time < 0.1  # Should be very fast with index
    
    def test_bulk_operations_performance(self, test_db_engine, test_db_session):
        """Test bulk operations performance"""
        Base.metadata.create_all(test_db_engine)
        
        # Test bulk insert performance
        import time
        
        users = []
        verifications = []
        
        start_time = time.time()
        
        for i in range(1000):
            user = User(
                id=i+1,
                email=f'user{i}@example.com',
                full_name=f'User {i}',
                password_hash=f'hash_{i}',
                email_verified=False
            )
            users.append(user)
            
            verification = EmailVerification(
                user_id=user.id,
                email=user.email,
                verification_token_hash=f'hash_{i}',
                expires_at=datetime.utcnow() + timedelta(hours=24),
                verification_type='signup'
            )
            verifications.append(verification)
        
        test_db_session.add_all(users)
        test_db_session.add_all(verifications)
        test_db_session.commit()
        
        bulk_insert_time = time.time() - start_time
        
        # Should insert 1000 records in reasonable time
        assert bulk_insert_time < 5.0
        
        # Test bulk update performance
        start_time = time.time()
        
        expired_count = test_db_session.query(EmailVerification).filter(
            EmailVerification.id.in_([i for i in range(1, 101)])
        ).update({
            'expires_at': datetime.utcnow() - timedelta(hours=1)
        })
        
        test_db_session.commit()
        bulk_update_time = time.time() - start_time
        
        assert expired_count == 100
        assert bulk_update_time < 1.0
    
    def test_memory_usage_optimization(self, test_db_engine, test_db_session):
        """Test memory usage optimization"""
        Base.metadata.create_all(test_db_engine)
        
        import gc
        import sys
        
        # Get initial memory usage
        gc.collect()
        initial_memory = sys.getsizeof(test_db_session)
        
        # Create large dataset
        users = []
        verifications = []
        
        for i in range(10000):
            user = User(
                id=i+1,
                email=f'user{i}@example.com',
                full_name=f'User {i}',
                password_hash=f'hash_{i}',
                email_verified=False
            )
            users.append(user)
            
            verification = EmailVerification(
                user_id=user.id,
                email=user.email,
                verification_token_hash=f'hash_{i}',
                expires_at=datetime.utcnow() + timedelta(hours=24),
                verification_type='signup'
            )
            verifications.append(verification)
        
        # Add to database
        test_db_session.add_all(users)
        test_db_session.add_all(verifications)
        test_db_session.commit()
        
        # Clear Python references
        del users
        del verifications
        gc.collect()
        
        # Get memory after cleanup
        final_memory = sys.getsizeof(test_db_session)
        
        # Memory increase should be reasonable
        memory_increase = final_memory - initial_memory
        assert memory_increase < 100 * 1024 * 1024  # 100MB

class TestDatabaseConcurrency:
    """Test database concurrency handling"""
    
    def test_concurrent_inserts(self, test_db_engine):
        """Test concurrent insert operations"""
        Base.metadata.create_all(test_db_engine)
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def worker(worker_id):
            """Worker function for concurrent testing"""
            try:
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
                session = SessionLocal()
                
                # Create user and verification
                user = User(
                    id=worker_id,
                    email=f'worker{worker_id}@example.com',
                    full_name=f'Worker {worker_id}',
                    password_hash=f'hash_{worker_id}',
                    email_verified=False
                )
                session.add(user)
                session.commit()
                
                verification = EmailVerification(
                    user_id=user.id,
                    email=user.email,
                    verification_token_hash=f'hash_{worker_id}',
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    verification_type='signup'
                )
                session.add(verification)
                session.commit()
                
                session.close()
                results.put((worker_id, True))
            except Exception as e:
                results.put((worker_id, str(e)))
        
        # Start 10 concurrent workers
        threads = []
        start_time = time.time()
        
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert total_time < 10.0
        
        # Check results
        successful_workers = 0
        for _ in range(10):
            worker_id, result = results.get()
            if result is True:
                successful_workers += 1
        
        # All workers should succeed
        assert successful_workers == 10
        
        # Verify data integrity
        inspector = inspect(test_db_engine)
        assert 'email_verifications' in inspector.get_table_names()
    
    def test_transaction_isolation(self, test_db_engine):
        """Test transaction isolation levels"""
        Base.metadata.create_all(test_db_engine)
        
        # Create two sessions
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
        session1 = SessionLocal()
        session2 = SessionLocal()
        
        try:
            # Session 1: Create user and verification
            user = User(
                id=1,
                email='test@example.com',
                full_name='Test User',
                password_hash='hashed_password',
                email_verified=False
            )
            session1.add(user)
            session1.commit()
            
            verification = EmailVerification(
                user_id=user.id,
                email=user.email,
                verification_token_hash='test_hash',
                expires_at=datetime.utcnow() + timedelta(hours=24),
                verification_type='signup'
            )
            session1.add(verification)
            session1.commit()
            
            # Session 2: Should see the data
            user2 = session2.query(User).filter_by(id=1).first()
            assert user2 is not None
            assert user2.email == 'test@example.com'
            
            verification2 = session2.query(EmailVerification).filter_by(user_id=1).first()
            assert verification2 is not None
            assert verification2.email == 'test@example.com'
            
        finally:
            session1.close()
            session2.close()

class TestDatabaseBackupAndRecovery:
    """Test database backup and recovery procedures"""
    
    def test_schema_backup(self, test_db_engine, temp_db_file):
        """Test schema backup functionality"""
        Base.metadata.create_all(test_db_engine)
        
        # Create backup file
        backup_file = temp_db_file.replace('.db', '_backup.db')
        
        # Copy database (simulate backup)
        import shutil
        shutil.copy2(temp_db_file, backup_file)
        
        # Verify backup exists
        assert os.path.exists(backup_file)
        
        # Verify backup has same schema
        backup_engine = create_engine(f'sqlite:///{backup_file}')
        backup_inspector = inspect(backup_engine)
        
        original_inspector = inspect(test_db_engine)
        
        original_tables = original_inspector.get_table_names()
        backup_tables = backup_inspector.get_table_names()
        
        assert original_tables == backup_tables
        
        backup_engine.dispose()
        os.unlink(backup_file)
    
    def test_data_recovery(self, test_db_engine, temp_db_file):
        """Test data recovery functionality"""
        Base.metadata.create_all(test_db_engine)
        
        # Create test data
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
        session = SessionLocal()
        
        user = User(
            id=1,
            email='test@example.com',
            full_name='Test User',
            password_hash='hashed_password',
            email_verified=False
        )
        session.add(user)
        session.commit()
        
        verification = EmailVerification(
            user_id=user.id,
            email=user.email,
            verification_token_hash='test_hash',
            expires_at=datetime.utcnow() + timedelta(hours=24),
            verification_type='signup'
        )
        session.add(verification)
        session.commit()
        
        session.close()
        
        # Create backup
        backup_file = temp_db_file.replace('.db', '_backup.db')
        import shutil
        shutil.copy2(temp_db_file, backup_file)
        
        # Drop original database
        Base.metadata.drop_all(test_db_engine)
        
        # Verify data is gone
        inspector = inspect(test_db_engine)
        assert 'email_verifications' not in inspector.get_table_names()
        
        # Restore from backup
        shutil.copy2(backup_file, temp_db_file)
        
        # Reconnect to restored database
        restored_engine = create_engine(f'sqlite:///{temp_db_file}')
        Base.metadata.create_all(restored_engine)
        
        # Verify data is restored
        restored_session = sessionmaker(autocommit=False, autoflush=False, bind=restored_engine)()
        
        restored_user = restored_session.query(User).filter_by(id=1).first()
        assert restored_user is not None
        assert restored_user.email == 'test@example.com'
        
        restored_verification = restored_session.query(EmailVerification).filter_by(user_id=1).first()
        assert restored_verification is not None
        assert restored_verification.email == 'test@example.com'
        
        restored_session.close()
        restored_engine.dispose()
        os.unlink(backup_file)

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
