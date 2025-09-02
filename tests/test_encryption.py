"""
Encryption System Tests
=======================
Comprehensive test suite for the Mingus Flask application encryption system.
"""

import pytest
import os
import tempfile
import shutil
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import the encryption system components
from backend.security.crypto_config import (
    CryptoConfigManager, EncryptionAlgorithm, KeyType, KeyRotationPolicy, EncryptionConfig
)
from backend.security.key_manager import KeyManager, EncryptionKey, KeyStatus
from backend.security.encryption_service import EncryptionService, EncryptionMode, EncryptedData

# Test configuration
TEST_CONFIG = {
    'algorithm': 'AES_256_GCM',
    'key_size_bits': 256,
    'iv_size_bytes': 16,
    'tag_size_bytes': 16,
    'compression_enabled': False,
    'performance_mode': 'balanced',
    'rotation_policies': [
        {
            'key_type': 'financial_data',
            'rotation_interval_days': 90,
            'max_key_age_days': 365,
            'grace_period_days': 30,
            'auto_rotation': True,
            'batch_size': 100
        },
        {
            'key_type': 'pii',
            'rotation_interval_days': 180,
            'max_key_age_days': 730,
            'grace_period_days': 60,
            'auto_rotation': True,
            'batch_size': 200
        }
    ]
}

class TestCryptoConfig:
    """Test encryption configuration management"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'encryption.json')
        
        # Create test configuration file
        with open(self.config_path, 'w') as f:
            json.dump(TEST_CONFIG, f)
        
        self.config_manager = CryptoConfigManager(self.config_path)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_config_from_file(self):
        """Test loading configuration from file"""
        config = self.config_manager.get_config()
        assert config.algorithm == EncryptionAlgorithm.AES_256_GCM
        assert config.key_size_bits == 256
        assert config.performance_mode == 'balanced'
    
    def test_load_default_config(self):
        """Test loading default configuration when file doesn't exist"""
        # Create config manager with non-existent path
        config_manager = CryptoConfigManager('/non/existent/path')
        config = config_manager.get_config()
        
        assert config.algorithm == EncryptionAlgorithm.AES_256_GCM
        assert config.key_size_bits == 256
    
    def test_rotation_policies(self):
        """Test rotation policy loading and retrieval"""
        financial_policy = self.config_manager.get_rotation_policy(KeyType.FINANCIAL_DATA)
        assert financial_policy.rotation_interval_days == 90
        assert financial_policy.max_key_age_days == 365
        assert financial_policy.auto_rotation is True
        
        pii_policy = self.config_manager.get_rotation_policy(KeyType.PII)
        assert pii_policy.rotation_interval_days == 180
        assert pii_policy.max_key_age_days == 730
    
    def test_update_config(self):
        """Test configuration updates"""
        new_config = EncryptionConfig(
            algorithm=EncryptionAlgorithm.AES_256_CBC,
            key_size_bits=192,
            iv_size_bytes=16,
            tag_size_bytes=0,
            compression_enabled=True,
            performance_mode='security'
        )
        
        self.config_manager.update_config(new_config)
        updated_config = self.config_manager.get_config()
        
        assert updated_config.algorithm == EncryptionAlgorithm.AES_256_CBC
        assert updated_config.key_size_bits == 192
        assert updated_config.compression_enabled is True
        assert updated_config.performance_mode == 'security'
    
    def test_environment_validation(self):
        """Test environment variable validation"""
        # Test with missing required variables
        errors = self.config_manager.validate_environment()
        assert len(errors) > 0
        assert any('ENCRYPTION_MASTER_KEY' in error for error in errors)
        assert any('ENCRYPTION_KEY_ID' in error for error in errors)
        
        # Test with valid environment
        os.environ['ENCRYPTION_MASTER_KEY'] = 'test_key'
        os.environ['ENCRYPTION_KEY_ID'] = 'test_id'
        
        errors = self.config_manager.validate_environment()
        assert len(errors) == 0
        
        # Clean up
        del os.environ['ENCRYPTION_MASTER_KEY']
        del os.environ['ENCRYPTION_KEY_ID']
    
    def test_performance_settings(self):
        """Test performance settings retrieval"""
        # Test balanced mode
        balanced_settings = self.config_manager.get_performance_settings()
        assert balanced_settings['key_derivation_iterations'] == 50000
        assert balanced_settings['memory_cost'] == 32768
        
        # Test security mode
        self.config_manager._config.performance_mode = 'security'
        security_settings = self.config_manager.get_performance_settings()
        assert security_settings['key_derivation_iterations'] == 100000
        assert security_settings['memory_cost'] == 65536

class TestKeyManager:
    """Test encryption key management"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['ENCRYPTION_MASTER_KEY'] = 'test_master_key_for_testing_purposes_only'
        os.environ['ENCRYPTION_KEY_ID'] = 'test_key_id'
        os.environ['ENCRYPTION_KEY_STORAGE_BACKEND'] = 'file'
        os.environ['ENCRYPTION_KEY_STORAGE_PATH'] = self.temp_dir
        
        self.key_manager = KeyManager()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
        del os.environ['ENCRYPTION_MASTER_KEY']
        del os.environ['ENCRYPTION_KEY_ID']
        del os.environ['ENCRYPTION_KEY_STORAGE_BACKEND']
        del os.environ['ENCRYPTION_KEY_STORAGE_PATH']
    
    def test_generate_key(self):
        """Test key generation"""
        key = self.key_manager.generate_key(KeyType.FINANCIAL_DATA)
        
        assert key.key_type == KeyType.FINANCIAL_DATA
        assert key.status == KeyStatus.ACTIVE
        assert key.key_version == 1
        assert key.key_data is not None
        assert len(key.key_data) == 32  # 256 bits = 32 bytes
    
    def test_key_storage_and_retrieval(self):
        """Test key storage and retrieval"""
        # Generate a key
        original_key = self.key_manager.generate_key(KeyType.PII)
        key_id = original_key.key_id
        
        # Retrieve the key
        retrieved_key = self.key_manager.get_key(key_id)
        
        assert retrieved_key is not None
        assert retrieved_key.key_id == key_id
        assert retrieved_key.key_type == KeyType.PII
        assert retrieved_key.key_data == original_key.key_data
    
    def test_get_active_key(self):
        """Test getting active key for a type"""
        # Generate multiple keys for the same type
        key1 = self.key_manager.generate_key(KeyType.FINANCIAL_DATA)
        key2 = self.key_manager.generate_key(KeyType.FINANCIAL_DATA)
        
        # The second key should be active (most recent)
        active_key = self.key_manager.get_active_key(KeyType.FINANCIAL_DATA)
        assert active_key.key_id == key2.key_id
    
    def test_key_rotation(self):
        """Test key rotation"""
        # Generate initial key
        original_key = self.key_manager.generate_key(KeyType.SESSION)
        
        # Rotate the key
        new_key = self.key_manager.rotate_key(KeyType.SESSION, force=True)
        
        assert new_key.key_id != original_key.key_id
        assert new_key.key_type == KeyType.SESSION
        assert new_key.status == KeyStatus.ACTIVE
        
        # Original key should be marked as rotating
        original_key_updated = self.key_manager.get_key(original_key.key_id)
        assert original_key_updated.status == KeyStatus.ROTATING
    
    def test_key_revocation(self):
        """Test key revocation"""
        key = self.key_manager.generate_key(KeyType.API_KEYS)
        key_id = key.key_id
        
        # Revoke the key
        self.key_manager.revoke_key(key_id, "Test revocation")
        
        # Check key status
        revoked_key = self.key_manager.get_key(key_id)
        assert revoked_key.status == KeyStatus.COMPROMISED
        assert revoked_key.metadata['revocation_reason'] == "Test revocation"
    
    def test_cleanup_expired_keys(self):
        """Test expired key cleanup"""
        # Generate a key and manually set it as expired
        key = self.key_manager.generate_key(KeyType.FINANCIAL_DATA)
        key.expires_at = datetime.utcnow() - timedelta(days=1)
        key.status = KeyStatus.ACTIVE
        
        # Clean up expired keys
        cleaned_count = self.key_manager.cleanup_expired_keys()
        
        assert cleaned_count >= 1
        
        # Check that the key is now marked as expired
        expired_key = self.key_manager.get_key(key.key_id)
        assert expired_key.status == KeyStatus.EXPIRED
    
    def test_key_statistics(self):
        """Test key statistics generation"""
        # Generate some keys
        self.key_manager.generate_key(KeyType.FINANCIAL_DATA)
        self.key_manager.generate_key(KeyType.PII)
        self.key_manager.generate_key(KeyType.SESSION)
        
        stats = self.key_manager.get_key_statistics()
        
        assert stats['total_keys'] >= 3
        assert 'financial_data' in stats['by_type']
        assert 'pii' in stats['by_type']
        assert 'session' in stats['by_type']

class TestEncryptionService:
    """Test encryption service functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['ENCRYPTION_MASTER_KEY'] = 'test_master_key_for_testing_purposes_only'
        os.environ['ENCRYPTION_KEY_ID'] = 'test_key_id'
        os.environ['ENCRYPTION_KEY_STORAGE_BACKEND'] = 'file'
        os.environ['ENCRYPTION_KEY_STORAGE_PATH'] = self.temp_dir
        
        self.encryption_service = EncryptionService()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
        del os.environ['ENCRYPTION_MASTER_KEY']
        del os.environ['ENCRYPTION_KEY_ID']
        del os.environ['ENCRYPTION_KEY_STORAGE_BACKEND']
        del os.environ['ENCRYPTION_KEY_STORAGE_PATH']
    
    def test_field_encryption_decryption(self):
        """Test field-level encryption and decryption"""
        # Test numeric value
        original_value = 50000.0
        encrypted_value = self.encryption_service.encrypt_field(
            original_value, KeyType.FINANCIAL_DATA
        )
        
        assert encrypted_value is not None
        assert encrypted_value != str(original_value)
        
        # Decrypt the value
        decrypted_value = self.encryption_service.decrypt_field(
            encrypted_value, KeyType.FINANCIAL_DATA
        )
        
        assert decrypted_value == original_value
    
    def test_string_encryption_decryption(self):
        """Test string value encryption and decryption"""
        original_value = "Monthly salary from ABC Corp"
        encrypted_value = self.encryption_service.encrypt_field(
            original_value, KeyType.FINANCIAL_DATA
        )
        
        assert encrypted_value is not None
        assert encrypted_value != original_value
        
        # Decrypt the value
        decrypted_value = self.encryption_service.decrypt_field(
            encrypted_value, KeyType.FINANCIAL_DATA
        )
        
        assert decrypted_value == original_value
    
    def test_none_value_handling(self):
        """Test handling of None values"""
        encrypted_value = self.encryption_service.encrypt_field(None, KeyType.FINANCIAL_DATA)
        assert encrypted_value is None
        
        decrypted_value = self.encryption_service.decrypt_field(None, KeyType.FINANCIAL_DATA)
        assert decrypted_value is None
    
    def test_bulk_data_encryption(self):
        """Test bulk data encryption and decryption"""
        # Create test data
        test_data = b"This is test bulk data for encryption testing"
        
        # Encrypt bulk data
        encrypted_data = self.encryption_service.encrypt_bulk_data(
            test_data, KeyType.FINANCIAL_DATA
        )
        
        assert encrypted_data.encrypted_data is not None
        assert encrypted_data.key_id is not None
        assert encrypted_data.algorithm is not None
        assert encrypted_data.iv is not None
        assert encrypted_data.tag is not None
        
        # Decrypt bulk data
        decrypted_data = self.encryption_service.decrypt_bulk_data(encrypted_data)
        
        assert decrypted_data == test_data
    
    def test_session_data_encryption(self):
        """Test session data encryption and decryption"""
        session_data = {
            'user_id': 123,
            'session_id': 'test_session_123',
            'permissions': ['read', 'write'],
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Encrypt session data
        encrypted_session = self.encryption_service.encrypt_session_data(session_data)
        
        assert encrypted_session is not None
        assert encrypted_session != json.dumps(session_data)
        
        # Decrypt session data
        decrypted_session = self.encryption_service.decrypt_session_data(encrypted_session)
        
        assert decrypted_session['user_id'] == session_data['user_id']
        assert decrypted_session['session_id'] == session_data['session_id']
        assert decrypted_session['permissions'] == session_data['permissions']
    
    def test_cache_data_encryption(self):
        """Test cache data encryption and decryption"""
        cache_key = "user_profile_123"
        cache_value = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'preferences': {'theme': 'dark', 'notifications': True}
        }
        
        # Encrypt cache data
        encrypted_key, encrypted_value = self.encryption_service.encrypt_cache_data(
            cache_key, cache_value
        )
        
        assert encrypted_key is not None
        assert encrypted_value is not None
        assert encrypted_key != cache_key
        assert encrypted_value != json.dumps(cache_value)
        
        # Decrypt cache data
        decrypted_key, decrypted_value = self.encryption_service.decrypt_cache_data(
            encrypted_key, encrypted_value
        )
        
        assert decrypted_key == cache_key
        assert decrypted_value == cache_value
    
    def test_database_field_encryption(self):
        """Test database field encryption with context"""
        # Test financial field
        income_value = 75000.0
        encrypted_income = self.encryption_service.encrypt_database_field(
            income_value, 'monthly_income', 'users'
        )
        
        assert encrypted_income is not None
        
        # Decrypt the field
        decrypted_income = self.encryption_service.decrypt_database_field(
            encrypted_income, 'monthly_income', 'users'
        )
        
        assert decrypted_income == income_value
        
        # Test PII field
        ssn_value = "123-45-6789"
        encrypted_ssn = self.encryption_service.encrypt_database_field(
            ssn_value, 'ssn', 'users'
        )
        
        assert encrypted_ssn is not None
        
        decrypted_ssn = self.encryption_service.decrypt_database_field(
            encrypted_ssn, 'ssn', 'users'
        )
        
        assert decrypted_ssn == ssn_value
    
    def test_key_type_determination(self):
        """Test automatic key type determination for fields"""
        # Test financial fields
        key_type = self.encryption_service._determine_key_type_for_field('users', 'monthly_income')
        assert key_type == KeyType.FINANCIAL_DATA
        
        key_type = self.encryption_service._determine_key_type_for_field('users', 'current_savings')
        assert key_type == KeyType.FINANCIAL_DATA
        
        # Test PII fields
        key_type = self.encryption_service._determine_key_type_for_field('users', 'ssn')
        assert key_type == KeyType.PII
        
        key_type = self.encryption_service._determine_key_type_for_field('users', 'address')
        assert key_type == KeyType.PII
        
        # Test session fields
        key_type = self.encryption_service._determine_key_type_for_field('sessions', 'session_id')
        assert key_type == KeyType.SESSION
    
    def test_encryption_stats(self):
        """Test encryption service statistics"""
        stats = self.encryption_service.get_encryption_stats()
        
        assert 'encryption_service' in stats
        assert 'algorithm' in stats
        assert 'performance_mode' in stats
        assert 'key_statistics' in stats

class TestKeyRotationTasks:
    """Test key rotation Celery tasks"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['ENCRYPTION_MASTER_KEY'] = 'test_master_key_for_testing_purposes_only'
        os.environ['ENCRYPTION_KEY_ID'] = 'test_key_id'
        os.environ['ENCRYPTION_KEY_STORAGE_BACKEND'] = 'file'
        os.environ['ENCRYPTION_KEY_STORAGE_PATH'] = self.temp_dir
        
        # Mock Celery task
        self.mock_task = Mock()
        self.mock_task.update_state = Mock()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
        del os.environ['ENCRYPTION_MASTER_KEY']
        del os.environ['ENCRYPTION_KEY_ID']
        del os.environ['ENCRYPTION_KEY_STORAGE_BACKEND']
        del os.environ['ENCRYPTION_KEY_STORAGE_PATH']
    
    @patch('backend.tasks.key_rotation.current_task')
    def test_scheduled_key_rotation(self, mock_current_task):
        """Test scheduled key rotation task"""
        mock_current_task.return_value = self.mock_task
        
        from backend.tasks.key_rotation import KeyRotationTasks
        tasks = KeyRotationTasks()
        
        result = tasks.rotate_keys_scheduled()
        
        assert 'rotated_keys' in result
        assert 'failed_rotations' in result
        assert 'total_processed' in result
        assert 'start_time' in result
        assert 'end_time' in result
    
    def test_manual_key_rotation(self):
        """Test manual key rotation task"""
        from backend.tasks.key_rotation import KeyRotationTasks
        tasks = KeyRotationTasks()
        
        result = tasks.rotate_key_manual('financial_data', force=True)
        
        assert result['success'] is True
        assert result['key_type'] == 'financial_data'
        assert result['forced'] is True
        assert 'new_key_id' in result
    
    def test_expired_key_cleanup(self):
        """Test expired key cleanup task"""
        from backend.tasks.key_rotation import KeyRotationTasks
        tasks = KeyRotationTasks()
        
        result = tasks.cleanup_expired_keys()
        
        assert 'keys_cleaned' in result
        assert 'cleanup_time' in result
    
    def test_encryption_status_report(self):
        """Test encryption status report generation"""
        from backend.tasks.key_rotation import KeyRotationTasks
        tasks = KeyRotationTasks()
        
        report = tasks.get_encryption_status_report()
        
        assert 'generated_at' in report
        assert 'key_management' in report
        assert 'encryption_service' in report
        assert 'database_encryption' in report
        assert 'recommendations' in report

class TestPerformance:
    """Test encryption system performance"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['ENCRYPTION_MASTER_KEY'] = 'test_master_key_for_testing_purposes_only'
        os.environ['ENCRYPTION_KEY_ID'] = 'test_key_id'
        os.environ['ENCRYPTION_KEY_STORAGE_BACKEND'] = 'file'
        os.environ['ENCRYPTION_KEY_STORAGE_PATH'] = self.temp_dir
        
        self.encryption_service = EncryptionService()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
        del os.environ['ENCRYPTION_MASTER_KEY']
        del os.environ['ENCRYPTION_KEY_ID']
        del os.environ['ENCRYPTION_KEY_STORAGE_BACKEND']
        del os.environ['ENCRYPTION_KEY_STORAGE_PATH']
    
    def test_field_encryption_performance(self):
        """Test field encryption performance"""
        test_values = [1000.0, 50000.0, 100000.0, 500000.0, 1000000.0]
        
        start_time = time.time()
        
        for value in test_values:
            encrypted = self.encryption_service.encrypt_field(value, KeyType.FINANCIAL_DATA)
            decrypted = self.encryption_service.decrypt_field(encrypted, KeyType.FINANCIAL_DATA)
            assert decrypted == value
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertion: should complete 5 encryptions/decryptions in under 1 second
        assert total_time < 1.0
        print(f"Field encryption performance: {total_time:.4f} seconds for 5 operations")
    
    def test_bulk_data_performance(self):
        """Test bulk data encryption performance"""
        # Test different data sizes
        data_sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB
        
        for size in data_sizes:
            test_data = b"x" * size
            
            start_time = time.time()
            
            encrypted_data = self.encryption_service.encrypt_bulk_data(
                test_data, KeyType.FINANCIAL_DATA
            )
            decrypted_data = self.encryption_service.decrypt_bulk_data(encrypted_data)
            
            end_time = time.time()
            operation_time = end_time - start_time
            
            assert decrypted_data == test_data
            
            # Performance assertion: should complete in reasonable time
            # 100KB should complete in under 0.1 seconds
            max_time = size / 1000000  # 1 second per MB
            assert operation_time < max_time
            
            print(f"Bulk encryption performance ({size} bytes): {operation_time:.4f} seconds")
    
    def test_concurrent_operations(self):
        """Test concurrent encryption operations"""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def encrypt_worker(worker_id, values):
            try:
                for i, value in enumerate(values):
                    encrypted = self.encryption_service.encrypt_field(
                        value, KeyType.FINANCIAL_DATA
                    )
                    decrypted = self.encryption_service.decrypt_field(
                        encrypted, KeyType.FINANCIAL_DATA
                    )
                    assert decrypted == value
                
                results.put(f"Worker {worker_id} completed successfully")
            except Exception as e:
                errors.put(f"Worker {worker_id} failed: {e}")
        
        # Create multiple worker threads
        threads = []
        values_per_worker = [1000.0, 2000.0, 3000.0, 4000.0, 5000.0]
        
        for i in range(4):  # 4 concurrent workers
            thread = threading.Thread(
                target=encrypt_worker,
                args=(i, values_per_worker)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert errors.empty(), f"Errors occurred: {[errors.get() for _ in range(errors.qsize())]}"
        assert results.qsize() == 4, "Not all workers completed"
        
        print("Concurrent operations test completed successfully")

# Test utilities
def create_test_database():
    """Create a test database for integration tests"""
    engine = create_engine('sqlite:///:memory:')
    
    # Create test tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email VARCHAR(255),
                monthly_income DECIMAL(10,2),
                current_savings DECIMAL(12,2),
                current_debt DECIMAL(12,2)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE encrypted_financial_profiles (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER,
                monthly_income TEXT,
                current_savings TEXT,
                current_debt TEXT
            )
        """))
        
        conn.commit()
    
    return engine

# Integration tests
class TestEncryptionIntegration:
    """Integration tests for the complete encryption system"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['ENCRYPTION_MASTER_KEY'] = 'test_master_key_for_testing_purposes_only'
        os.environ['ENCRYPTION_KEY_ID'] = 'test_key_id'
        os.environ['ENCRYPTION_KEY_STORAGE_BACKEND'] = 'file'
        os.environ['ENCRYPTION_KEY_STORAGE_PATH'] = self.temp_dir
        
        self.engine = create_test_database()
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        self.key_manager = KeyManager()
        self.encryption_service = EncryptionService()
    
    def teardown_method(self):
        """Clean up integration test fixtures"""
        shutil.rmtree(self.temp_dir)
        del os.environ['ENCRYPTION_MASTER_KEY']
        del os.environ['ENCRYPTION_KEY_ID']
        del os.environ['ENCRYPTION_KEY_STORAGE_BACKEND']
        del os.environ['ENCRYPTION_KEY_STORAGE_PATH']
    
    def test_end_to_end_encryption_workflow(self):
        """Test complete encryption workflow from key generation to data encryption"""
        # 1. Generate encryption key
        key = self.key_manager.generate_key(KeyType.FINANCIAL_DATA)
        assert key is not None
        
        # 2. Encrypt financial data
        income_data = 75000.0
        encrypted_income = self.encryption_service.encrypt_field(
            income_data, KeyType.FINANCIAL_DATA
        )
        assert encrypted_income is not None
        
        # 3. Store encrypted data in database
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, email, monthly_income)
                VALUES (1, 'test@example.com', :encrypted_income)
            """), {'encrypted_income': encrypted_income})
            conn.commit()
        
        # 4. Retrieve and decrypt data
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT monthly_income FROM users WHERE id = 1
            """)).fetchone()
            
            stored_encrypted = result[0]
            decrypted_income = self.encryption_service.decrypt_field(
                stored_encrypted, KeyType.FINANCIAL_DATA
            )
            
            assert decrypted_income == income_data
    
    def test_key_rotation_with_data_migration(self):
        """Test key rotation with data re-encryption"""
        # 1. Generate initial key and encrypt data
        original_key = self.key_manager.generate_key(KeyType.FINANCIAL_DATA)
        original_income = 50000.0
        encrypted_income = self.encryption_service.encrypt_field(
            original_income, KeyType.FINANCIAL_DATA
        )
        
        # 2. Store encrypted data
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, email, monthly_income)
                VALUES (2, 'test2@example.com', :encrypted_income)
            """), {'encrypted_income': encrypted_income})
            conn.commit()
        
        # 3. Rotate the key
        new_key = self.key_manager.rotate_key(KeyType.FINANCIAL_DATA, force=True)
        assert new_key.key_id != original_key.key_id
        
        # 4. Verify data can still be decrypted with new key
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT monthly_income FROM users WHERE id = 2
            """)).fetchone()
            
            stored_encrypted = result[0]
            decrypted_income = self.encryption_service.decrypt_field(
                stored_encrypted, KeyType.FINANCIAL_DATA
            )
            
            assert decrypted_income == original_income

# Performance benchmarks
def benchmark_encryption_operations():
    """Run encryption performance benchmarks"""
    print("\n" + "="*50)
    print("ENCRYPTION SYSTEM PERFORMANCE BENCHMARKS")
    print("="*50)
    
    # Set up test environment
    temp_dir = tempfile.mkdtemp()
    os.environ['ENCRYPTION_MASTER_KEY'] = 'benchmark_master_key_for_testing_purposes_only'
    os.environ['ENCRYPTION_KEY_ID'] = 'benchmark_key_id'
    os.environ['ENCRYPTION_KEY_STORAGE_BACKEND'] = 'file'
    os.environ['ENCRYPTION_KEY_STORAGE_PATH'] = temp_dir
    
    try:
        encryption_service = EncryptionService()
        
        # Benchmark field encryption
        print("\nField Encryption Performance:")
        print("-" * 30)
        
        test_values = [1000, 50000, 100000, 500000, 1000000]
        for value in test_values:
            start_time = time.time()
            for _ in range(100):  # 100 operations
                encrypted = encryption_service.encrypt_field(value, KeyType.FINANCIAL_DATA)
                decrypted = encryption_service.decrypt_field(encrypted, KeyType.FINANCIAL_DATA)
                assert decrypted == value
            
            end_time = time.time()
            total_time = end_time - start_time
            ops_per_second = 100 / total_time
            
            print(f"Value {value:,}: {total_time:.4f}s for 100 ops ({ops_per_second:.1f} ops/sec)")
        
        # Benchmark bulk data encryption
        print("\nBulk Data Encryption Performance:")
        print("-" * 35)
        
        data_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
        for size in data_sizes:
            test_data = b"x" * size
            
            start_time = time.time()
            for _ in range(10):  # 10 operations
                encrypted_data = encryption_service.encrypt_bulk_data(
                    test_data, KeyType.FINANCIAL_DATA
                )
                decrypted_data = encryption_service.decrypt_bulk_data(encrypted_data)
                assert decrypted_data == test_data
            
            end_time = time.time()
            total_time = end_time - start_time
            ops_per_second = 10 / total_time
            mb_per_second = (size * 10) / (total_time * 1024 * 1024)
            
            print(f"Size {size:,} bytes: {total_time:.4f}s for 10 ops "
                  f"({ops_per_second:.1f} ops/sec, {mb_per_second:.1f} MB/sec)")
        
        print("\nBenchmarks completed successfully!")
        
    finally:
        shutil.rmtree(temp_dir)
        del os.environ['ENCRYPTION_MASTER_KEY']
        del os.environ['ENCRYPTION_KEY_ID']
        del os.environ['ENCRYPTION_KEY_STORAGE_BACKEND']
        del os.environ['ENCRYPTION_KEY_STORAGE_PATH']

if __name__ == "__main__":
    # Run benchmarks if script is executed directly
    benchmark_encryption_operations()
