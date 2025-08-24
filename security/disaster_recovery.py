"""
Disaster Recovery and Backup Security
Comprehensive backup and recovery system with security focus
"""

import os
import sys
import json
import time
import hashlib
import tarfile
import zipfile
import shutil
import subprocess
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import boto3
import paramiko
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from loguru import logger
import schedule
import asyncio
import aiofiles
import aiohttp

class BackupType(Enum):
    """Types of backups"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    LOGS = "logs"

class BackupStatus(Enum):
    """Backup status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"

class StorageType(Enum):
    """Storage types"""
    LOCAL = "local"
    S3 = "s3"
    SFTP = "sftp"
    AZURE = "azure"
    GCP = "gcp"

class RecoveryType(Enum):
    """Recovery types"""
    FULL_RESTORE = "full_restore"
    PARTIAL_RESTORE = "partial_restore"
    DATABASE_RESTORE = "database_restore"
    CONFIGURATION_RESTORE = "configuration_restore"
    DISASTER_RECOVERY = "disaster_recovery"

@dataclass
class BackupConfig:
    """Backup configuration"""
    backup_id: str
    backup_type: BackupType
    source_paths: List[str]
    destination_path: str
    storage_type: StorageType
    encryption_enabled: bool = True
    compression_enabled: bool = True
    retention_days: int = 30
    schedule: str = "0 2 * * *"  # Daily at 2 AM
    max_backup_size_gb: int = 10
    verify_backup: bool = True
    access_controls: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BackupMetadata:
    """Backup metadata"""
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    size_bytes: int
    checksum: str
    encryption_key_id: str
    compression_ratio: float
    source_paths: List[str]
    destination_path: str
    storage_type: StorageType
    status: BackupStatus
    error_message: Optional[str] = None
    verification_status: Optional[str] = None

@dataclass
class RecoveryConfig:
    """Recovery configuration"""
    recovery_id: str
    recovery_type: RecoveryType
    backup_id: str
    target_paths: List[str]
    verification_enabled: bool = True
    rollback_enabled: bool = True
    access_controls: Dict[str, Any] = field(default_factory=dict)

class DisasterRecoveryManager:
    """Disaster recovery and backup security manager"""
    
    def __init__(self, base_path: str = "/var/lib/mingus/backups"):
        self.base_path = base_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.backup_lock = threading.Lock()
        self.recovery_lock = threading.Lock()
        
        # Initialize backup database
        self._init_backup_database()
        
        # Load backup configurations
        self.backup_configs = self._load_backup_configs()
        
        # Initialize storage providers
        self.storage_providers = self._init_storage_providers()
        
        # Initialize access controls
        self.access_manager = BackupAccessManager(base_path)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for backups"""
        key_file = os.path.join(self.base_path, "backup_encryption.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _init_backup_database(self):
        """Initialize backup database"""
        try:
            os.makedirs(self.base_path, exist_ok=True)
            
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                # Backup metadata table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backup_metadata (
                        backup_id TEXT PRIMARY KEY,
                        backup_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        checksum TEXT NOT NULL,
                        encryption_key_id TEXT NOT NULL,
                        compression_ratio REAL,
                        source_paths TEXT NOT NULL,
                        destination_path TEXT NOT NULL,
                        storage_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        verification_status TEXT
                    )
                """)
                
                # Recovery metadata table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS recovery_metadata (
                        recovery_id TEXT PRIMARY KEY,
                        recovery_type TEXT NOT NULL,
                        backup_id TEXT NOT NULL,
                        target_paths TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        verification_status TEXT,
                        FOREIGN KEY (backup_id) REFERENCES backup_metadata (backup_id)
                    )
                """)
                
                # Access control table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backup_access_controls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backup_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        permission TEXT NOT NULL,
                        granted_at TEXT NOT NULL,
                        expires_at TEXT,
                        granted_by TEXT NOT NULL,
                        FOREIGN KEY (backup_id) REFERENCES backup_metadata (backup_id)
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_backup_timestamp ON backup_metadata(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_backup_type ON backup_metadata(backup_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_backup_status ON backup_metadata(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_recovery_timestamp ON recovery_metadata(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_access_backup ON backup_access_controls(backup_id)")
                
        except Exception as e:
            logger.error(f"Error initializing backup database: {e}")
    
    def _load_backup_configs(self) -> Dict[str, BackupConfig]:
        """Load backup configurations"""
        configs = {}
        
        # Full system backup
        configs["full_system"] = BackupConfig(
            backup_id="full_system",
            backup_type=BackupType.FULL,
            source_paths=[
                "/var/lib/mingus",
                "/etc/mingus",
                "/opt/mingus"
            ],
            destination_path="/backups/full_system",
            storage_type=StorageType.S3,
            encryption_enabled=True,
            compression_enabled=True,
            retention_days=30,
            schedule="0 2 * * 0",  # Weekly on Sunday
            max_backup_size_gb=50,
            verify_backup=True,
            access_controls={
                "admin_only": True,
                "require_mfa": True,
                "audit_logging": True
            }
        )
        
        # Database backup
        configs["database"] = BackupConfig(
            backup_id="database",
            backup_type=BackupType.DATABASE,
            source_paths=["/var/lib/mingus/database"],
            destination_path="/backups/database",
            storage_type=StorageType.S3,
            encryption_enabled=True,
            compression_enabled=True,
            retention_days=90,
            schedule="0 1 * * *",  # Daily at 1 AM
            max_backup_size_gb=10,
            verify_backup=True,
            access_controls={
                "admin_only": True,
                "require_mfa": True,
                "audit_logging": True
            }
        )
        
        # Configuration backup
        configs["configuration"] = BackupConfig(
            backup_id="configuration",
            backup_type=BackupType.CONFIGURATION,
            source_paths=[
                "/etc/mingus",
                "/var/lib/mingus/config"
            ],
            destination_path="/backups/configuration",
            storage_type=StorageType.S3,
            encryption_enabled=True,
            compression_enabled=True,
            retention_days=365,
            schedule="0 3 * * *",  # Daily at 3 AM
            max_backup_size_gb=5,
            verify_backup=True,
            access_controls={
                "admin_only": True,
                "require_mfa": True,
                "audit_logging": True
            }
        )
        
        # Logs backup
        configs["logs"] = BackupConfig(
            backup_id="logs",
            backup_type=BackupType.LOGS,
            source_paths=["/var/log/mingus"],
            destination_path="/backups/logs",
            storage_type=StorageType.S3,
            encryption_enabled=True,
            compression_enabled=True,
            retention_days=30,
            schedule="0 4 * * *",  # Daily at 4 AM
            max_backup_size_gb=20,
            verify_backup=True,
            access_controls={
                "admin_only": False,
                "require_mfa": False,
                "audit_logging": True
            }
        )
        
        return configs
    
    def _init_storage_providers(self) -> Dict[StorageType, Any]:
        """Initialize storage providers"""
        providers = {}
        
        # Local storage provider
        providers[StorageType.LOCAL] = LocalStorageProvider(self.base_path)
        
        # S3 storage provider
        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            providers[StorageType.S3] = S3StorageProvider(
                bucket_name=os.getenv("S3_BACKUP_BUCKET", "mingus-backups"),
                region=os.getenv("AWS_REGION", "us-east-1")
            )
        
        # SFTP storage provider
        if os.getenv("SFTP_HOST") and os.getenv("SFTP_USERNAME"):
            providers[StorageType.SFTP] = SFTPStorageProvider(
                host=os.getenv("SFTP_HOST"),
                username=os.getenv("SFTP_USERNAME"),
                password=os.getenv("SFTP_PASSWORD"),
                key_file=os.getenv("SFTP_KEY_FILE")
            )
        
        return providers
    
    def create_backup(self, backup_config_id: str, user_id: str = "system") -> str:
        """Create backup"""
        if backup_config_id not in self.backup_configs:
            raise ValueError(f"Backup configuration {backup_config_id} not found")
        
        config = self.backup_configs[backup_config_id]
        
        # Check access permissions
        if not self.access_manager.check_backup_permission(user_id, config.backup_id, "create"):
            raise PermissionError(f"User {user_id} does not have permission to create backup {config.backup_id}")
        
        backup_id = f"{config.backup_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with self.backup_lock:
                # Update status to in progress
                self._update_backup_status(backup_id, BackupStatus.IN_PROGRESS)
                
                # Create backup
                metadata = self._perform_backup(backup_id, config)
                
                # Verify backup if enabled
                if config.verify_backup:
                    self._verify_backup(metadata)
                
                # Update status to completed
                self._update_backup_status(backup_id, BackupStatus.COMPLETED)
                
                # Log access
                self.access_manager.log_backup_access(user_id, backup_id, "create")
                
                logger.info(f"Backup {backup_id} created successfully")
                return backup_id
                
        except Exception as e:
            self._update_backup_status(backup_id, BackupStatus.FAILED, str(e))
            logger.error(f"Backup {backup_id} failed: {e}")
            raise
    
    def _perform_backup(self, backup_id: str, config: BackupConfig) -> BackupMetadata:
        """Perform actual backup operation"""
        start_time = time.time()
        
        # Create temporary backup directory
        temp_dir = os.path.join(self.base_path, "temp", backup_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Collect files to backup
            files_to_backup = []
            for source_path in config.source_paths:
                if os.path.exists(source_path):
                    if os.path.isfile(source_path):
                        files_to_backup.append(source_path)
                    else:
                        for root, dirs, files in os.walk(source_path):
                            for file in files:
                                files_to_backup.append(os.path.join(root, file))
            
            # Create backup archive
            backup_file = os.path.join(temp_dir, f"{backup_id}.tar.gz")
            
            with tarfile.open(backup_file, "w:gz") as tar:
                for file_path in files_to_backup:
                    try:
                        tar.add(file_path, arcname=os.path.relpath(file_path, "/"))
                    except Exception as e:
                        logger.warning(f"Could not add file {file_path} to backup: {e}")
            
            # Get backup size
            backup_size = os.path.getsize(backup_file)
            
            # Check size limit
            if backup_size > config.max_backup_size_gb * 1024 * 1024 * 1024:
                raise ValueError(f"Backup size {backup_size} exceeds limit {config.max_backup_size_gb}GB")
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_file)
            
            # Encrypt backup if enabled
            if config.encryption_enabled:
                backup_file = self._encrypt_backup(backup_file)
            
            # Upload to storage
            storage_provider = self.storage_providers.get(config.storage_type)
            if not storage_provider:
                raise ValueError(f"Storage provider {config.storage_type} not available")
            
            destination_path = f"{config.destination_path}/{backup_id}.tar.gz"
            storage_provider.upload(backup_file, destination_path)
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=config.backup_type,
                timestamp=datetime.utcnow(),
                size_bytes=backup_size,
                checksum=checksum,
                encryption_key_id=self._get_encryption_key_id(),
                compression_ratio=backup_size / os.path.getsize(backup_file) if config.compression_enabled else 1.0,
                source_paths=config.source_paths,
                destination_path=destination_path,
                storage_type=config.storage_type,
                status=BackupStatus.COMPLETED
            )
            
            # Store metadata
            self._store_backup_metadata(metadata)
            
            return metadata
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _encrypt_backup(self, backup_file: str) -> str:
        """Encrypt backup file"""
        encrypted_file = backup_file + ".encrypted"
        
        with open(backup_file, 'rb') as f_in:
            data = f_in.read()
        
        encrypted_data = self.cipher_suite.encrypt(data)
        
        with open(encrypted_file, 'wb') as f_out:
            f_out.write(encrypted_data)
        
        return encrypted_file
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _get_encryption_key_id(self) -> str:
        """Get encryption key ID"""
        return hashlib.sha256(self.encryption_key).hexdigest()[:16]
    
    def _verify_backup(self, metadata: BackupMetadata):
        """Verify backup integrity"""
        try:
            # Download backup from storage
            storage_provider = self.storage_providers.get(metadata.storage_type)
            temp_file = os.path.join(self.base_path, "temp", f"verify_{metadata.backup_id}")
            
            storage_provider.download(metadata.destination_path, temp_file)
            
            # Verify checksum
            calculated_checksum = self._calculate_checksum(temp_file)
            if calculated_checksum != metadata.checksum:
                raise ValueError("Backup checksum verification failed")
            
            # Test extraction
            if metadata.backup_type in [BackupType.FULL, BackupType.INCREMENTAL, BackupType.DIFFERENTIAL]:
                with tarfile.open(temp_file, "r:gz") as tar:
                    tar.getmembers()  # Test archive integrity
            
            # Update verification status
            self._update_backup_verification(metadata.backup_id, "verified")
            
            # Clean up
            os.remove(temp_file)
            
        except Exception as e:
            self._update_backup_verification(metadata.backup_id, f"failed: {e}")
            raise
    
    def restore_backup(self, backup_id: str, target_paths: List[str], user_id: str = "system") -> str:
        """Restore backup"""
        # Get backup metadata
        metadata = self._get_backup_metadata(backup_id)
        if not metadata:
            raise ValueError(f"Backup {backup_id} not found")
        
        # Check access permissions
        if not self.access_manager.check_backup_permission(user_id, backup_id, "restore"):
            raise PermissionError(f"User {user_id} does not have permission to restore backup {backup_id}")
        
        recovery_id = f"recovery_{backup_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with self.recovery_lock:
                # Create recovery configuration
                recovery_config = RecoveryConfig(
                    recovery_id=recovery_id,
                    recovery_type=RecoveryType.FULL_RESTORE,
                    backup_id=backup_id,
                    target_paths=target_paths,
                    verification_enabled=True,
                    rollback_enabled=True,
                    access_controls={
                        "admin_only": True,
                        "require_mfa": True,
                        "audit_logging": True
                    }
                )
                
                # Perform recovery
                self._perform_recovery(recovery_config, metadata)
                
                # Log access
                self.access_manager.log_backup_access(user_id, backup_id, "restore")
                
                logger.info(f"Recovery {recovery_id} completed successfully")
                return recovery_id
                
        except Exception as e:
            logger.error(f"Recovery {recovery_id} failed: {e}")
            raise
    
    def _perform_recovery(self, recovery_config: RecoveryConfig, metadata: BackupMetadata):
        """Perform actual recovery operation"""
        # Download backup from storage
        storage_provider = self.storage_providers.get(metadata.storage_type)
        temp_file = os.path.join(self.base_path, "temp", f"recovery_{recovery_config.recovery_id}")
        
        try:
            storage_provider.download(metadata.destination_path, temp_file)
            
            # Decrypt if necessary
            if metadata.encryption_key_id:
                temp_file = self._decrypt_backup(temp_file)
            
            # Create backup of current state if rollback enabled
            if recovery_config.rollback_enabled:
                self._create_rollback_backup(recovery_config.target_paths)
            
            # Extract backup
            with tarfile.open(temp_file, "r:gz") as tar:
                tar.extractall(path="/")
            
            # Verify recovery if enabled
            if recovery_config.verification_enabled:
                self._verify_recovery(recovery_config, metadata)
            
            # Store recovery metadata
            self._store_recovery_metadata(recovery_config, "completed")
            
        finally:
            # Clean up
            os.remove(temp_file)
    
    def _decrypt_backup(self, encrypted_file: str) -> str:
        """Decrypt backup file"""
        decrypted_file = encrypted_file.replace(".encrypted", "")
        
        with open(encrypted_file, 'rb') as f_in:
            encrypted_data = f_in.read()
        
        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        
        with open(decrypted_file, 'wb') as f_out:
            f_out.write(decrypted_data)
        
        return decrypted_file
    
    def _create_rollback_backup(self, target_paths: List[str]):
        """Create rollback backup of current state"""
        rollback_id = f"rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create quick backup of target paths
        rollback_file = os.path.join(self.base_path, "rollback", f"{rollback_id}.tar.gz")
        os.makedirs(os.path.dirname(rollback_file), exist_ok=True)
        
        with tarfile.open(rollback_file, "w:gz") as tar:
            for target_path in target_paths:
                if os.path.exists(target_path):
                    tar.add(target_path, arcname=os.path.basename(target_path))
    
    def _verify_recovery(self, recovery_config: RecoveryConfig, metadata: BackupMetadata):
        """Verify recovery integrity"""
        # Check if restored files exist and are accessible
        for target_path in recovery_config.target_paths:
            if not os.path.exists(target_path):
                raise ValueError(f"Recovery verification failed: {target_path} not found")
            
            # Check file permissions
            if os.path.isfile(target_path):
                if not os.access(target_path, os.R_OK):
                    raise ValueError(f"Recovery verification failed: {target_path} not readable")
    
    def list_backups(self, backup_type: Optional[BackupType] = None, limit: int = 100) -> List[BackupMetadata]:
        """List available backups"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                query = """
                    SELECT backup_id, backup_type, timestamp, size_bytes, checksum,
                           encryption_key_id, compression_ratio, source_paths,
                           destination_path, storage_type, status, error_message, verification_status
                    FROM backup_metadata
                """
                params = []
                
                if backup_type:
                    query += " WHERE backup_type = ?"
                    params.append(backup_type.value)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                backups = []
                for row in cursor.fetchall():
                    backup = BackupMetadata(
                        backup_id=row[0],
                        backup_type=BackupType(row[1]),
                        timestamp=datetime.fromisoformat(row[2]),
                        size_bytes=row[3],
                        checksum=row[4],
                        encryption_key_id=row[5],
                        compression_ratio=row[6],
                        source_paths=json.loads(row[7]),
                        destination_path=row[8],
                        storage_type=StorageType(row[9]),
                        status=BackupStatus(row[10]),
                        error_message=row[11],
                        verification_status=row[12]
                    )
                    backups.append(backup)
                
                return backups
                
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def delete_backup(self, backup_id: str, user_id: str = "system") -> bool:
        """Delete backup"""
        # Check access permissions
        if not self.access_manager.check_backup_permission(user_id, backup_id, "delete"):
            raise PermissionError(f"User {user_id} does not have permission to delete backup {backup_id}")
        
        try:
            # Get backup metadata
            metadata = self._get_backup_metadata(backup_id)
            if not metadata:
                return False
            
            # Delete from storage
            storage_provider = self.storage_providers.get(metadata.storage_type)
            storage_provider.delete(metadata.destination_path)
            
            # Delete metadata from database
            self._delete_backup_metadata(backup_id)
            
            # Log access
            self.access_manager.log_backup_access(user_id, backup_id, "delete")
            
            logger.info(f"Backup {backup_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Clean up old backups"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Get old backups
            old_backups = []
            for backup_config in self.backup_configs.values():
                backups = self.list_backups(backup_config.backup_type)
                for backup in backups:
                    if backup.timestamp < cutoff_date:
                        old_backups.append(backup.backup_id)
            
            # Delete old backups
            deleted_count = 0
            for backup_id in old_backups:
                if self.delete_backup(backup_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0
    
    def _update_backup_status(self, backup_id: str, status: BackupStatus, error_message: str = None):
        """Update backup status"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    UPDATE backup_metadata 
                    SET status = ?, error_message = ?
                    WHERE backup_id = ?
                """, (status.value, error_message, backup_id))
        except Exception as e:
            logger.error(f"Error updating backup status: {e}")
    
    def _update_backup_verification(self, backup_id: str, verification_status: str):
        """Update backup verification status"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    UPDATE backup_metadata 
                    SET verification_status = ?
                    WHERE backup_id = ?
                """, (verification_status, backup_id))
        except Exception as e:
            logger.error(f"Error updating backup verification: {e}")
    
    def _store_backup_metadata(self, metadata: BackupMetadata):
        """Store backup metadata"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backup_metadata 
                    (backup_id, backup_type, timestamp, size_bytes, checksum,
                     encryption_key_id, compression_ratio, source_paths,
                     destination_path, storage_type, status, error_message, verification_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.backup_id,
                    metadata.backup_type.value,
                    metadata.timestamp.isoformat(),
                    metadata.size_bytes,
                    metadata.checksum,
                    metadata.encryption_key_id,
                    metadata.compression_ratio,
                    json.dumps(metadata.source_paths),
                    metadata.destination_path,
                    metadata.storage_type.value,
                    metadata.status.value,
                    metadata.error_message,
                    metadata.verification_status
                ))
        except Exception as e:
            logger.error(f"Error storing backup metadata: {e}")
    
    def _store_recovery_metadata(self, recovery_config: RecoveryConfig, status: str):
        """Store recovery metadata"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO recovery_metadata 
                    (recovery_id, recovery_type, backup_id, target_paths, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    recovery_config.recovery_id,
                    recovery_config.recovery_type.value,
                    recovery_config.backup_id,
                    json.dumps(recovery_config.target_paths),
                    datetime.utcnow().isoformat(),
                    status
                ))
        except Exception as e:
            logger.error(f"Error storing recovery metadata: {e}")
    
    def _get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get backup metadata"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("""
                    SELECT backup_id, backup_type, timestamp, size_bytes, checksum,
                           encryption_key_id, compression_ratio, source_paths,
                           destination_path, storage_type, status, error_message, verification_status
                    FROM backup_metadata 
                    WHERE backup_id = ?
                """, (backup_id,))
                
                row = cursor.fetchone()
                if row:
                    return BackupMetadata(
                        backup_id=row[0],
                        backup_type=BackupType(row[1]),
                        timestamp=datetime.fromisoformat(row[2]),
                        size_bytes=row[3],
                        checksum=row[4],
                        encryption_key_id=row[5],
                        compression_ratio=row[6],
                        source_paths=json.loads(row[7]),
                        destination_path=row[8],
                        storage_type=StorageType(row[9]),
                        status=BackupStatus(row[10]),
                        error_message=row[11],
                        verification_status=row[12]
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting backup metadata: {e}")
            return None
    
    def _delete_backup_metadata(self, backup_id: str):
        """Delete backup metadata"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("DELETE FROM backup_metadata WHERE backup_id = ?", (backup_id,))
                conn.execute("DELETE FROM backup_access_controls WHERE backup_id = ?", (backup_id,))
        except Exception as e:
            logger.error(f"Error deleting backup metadata: {e}")

class BackupAccessManager:
    """Backup access control manager"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    def check_backup_permission(self, user_id: str, backup_id: str, permission: str) -> bool:
        """Check if user has permission for backup operation"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("""
                    SELECT permission, expires_at
                    FROM backup_access_controls 
                    WHERE user_id = ? AND backup_id = ? AND permission = ?
                """, (user_id, backup_id, permission))
                
                row = cursor.fetchone()
                if row:
                    permission_granted, expires_at = row
                    
                    # Check if permission has expired
                    if expires_at:
                        expiry_date = datetime.fromisoformat(expires_at)
                        if datetime.utcnow() > expiry_date:
                            return False
                    
                    return True
                
                # Check for admin permissions
                if self._is_admin_user(user_id):
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking backup permission: {e}")
            return False
    
    def grant_backup_permission(self, user_id: str, backup_id: str, permission: str, 
                               granted_by: str, expires_at: Optional[datetime] = None):
        """Grant backup permission to user"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backup_access_controls 
                    (user_id, backup_id, permission, granted_at, expires_at, granted_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    backup_id,
                    permission,
                    datetime.utcnow().isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    granted_by
                ))
            
            logger.info(f"Granted {permission} permission for backup {backup_id} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error granting backup permission: {e}")
    
    def revoke_backup_permission(self, user_id: str, backup_id: str, permission: str):
        """Revoke backup permission from user"""
        try:
            db_path = os.path.join(self.base_path, "backup_recovery.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    DELETE FROM backup_access_controls 
                    WHERE user_id = ? AND backup_id = ? AND permission = ?
                """, (user_id, backup_id, permission))
            
            logger.info(f"Revoked {permission} permission for backup {backup_id} from user {user_id}")
            
        except Exception as e:
            logger.error(f"Error revoking backup permission: {e}")
    
    def log_backup_access(self, user_id: str, backup_id: str, action: str):
        """Log backup access for audit"""
        try:
            # This would integrate with your audit logging system
            logger.info(f"Backup access: user={user_id}, backup={backup_id}, action={action}")
        except Exception as e:
            logger.error(f"Error logging backup access: {e}")
    
    def _is_admin_user(self, user_id: str) -> bool:
        """Check if user is admin"""
        # This would integrate with your user management system
        admin_users = ["admin", "root", "system"]
        return user_id in admin_users

class LocalStorageProvider:
    """Local storage provider"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    def upload(self, local_path: str, destination_path: str):
        """Upload file to local storage"""
        full_destination = os.path.join(self.base_path, destination_path)
        os.makedirs(os.path.dirname(full_destination), exist_ok=True)
        shutil.copy2(local_path, full_destination)
    
    def download(self, source_path: str, local_path: str):
        """Download file from local storage"""
        full_source = os.path.join(self.base_path, source_path)
        shutil.copy2(full_source, local_path)
    
    def delete(self, file_path: str):
        """Delete file from local storage"""
        full_path = os.path.join(self.base_path, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)

class S3StorageProvider:
    """S3 storage provider"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)
    
    def upload(self, local_path: str, destination_path: str):
        """Upload file to S3"""
        self.s3_client.upload_file(local_path, self.bucket_name, destination_path)
    
    def download(self, source_path: str, local_path: str):
        """Download file from S3"""
        self.s3_client.download_file(self.bucket_name, source_path, local_path)
    
    def delete(self, file_path: str):
        """Delete file from S3"""
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)

class SFTPStorageProvider:
    """SFTP storage provider"""
    
    def __init__(self, host: str, username: str, password: str = None, key_file: str = None):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
    
    def upload(self, local_path: str, destination_path: str):
        """Upload file via SFTP"""
        transport = paramiko.Transport((self.host, 22))
        
        if self.key_file:
            private_key = paramiko.RSAKey.from_private_key_file(self.key_file)
            transport.connect(username=self.username, pkey=private_key)
        else:
            transport.connect(username=self.username, password=self.password)
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(local_path, destination_path)
        sftp.close()
        transport.close()
    
    def download(self, source_path: str, local_path: str):
        """Download file via SFTP"""
        transport = paramiko.Transport((self.host, 22))
        
        if self.key_file:
            private_key = paramiko.RSAKey.from_private_key_file(self.key_file)
            transport.connect(username=self.username, pkey=private_key)
        else:
            transport.connect(username=self.username, password=self.password)
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get(source_path, local_path)
        sftp.close()
        transport.close()
    
    def delete(self, file_path: str):
        """Delete file via SFTP"""
        transport = paramiko.Transport((self.host, 22))
        
        if self.key_file:
            private_key = paramiko.RSAKey.from_private_key_file(self.key_file)
            transport.connect(username=self.username, pkey=private_key)
        else:
            transport.connect(username=self.username, password=self.password)
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.remove(file_path)
        sftp.close()
        transport.close()

# Global disaster recovery manager instance
_disaster_recovery_manager = None

def get_disaster_recovery_manager(base_path: str = "/var/lib/mingus/backups") -> DisasterRecoveryManager:
    """Get global disaster recovery manager instance"""
    global _disaster_recovery_manager
    
    if _disaster_recovery_manager is None:
        _disaster_recovery_manager = DisasterRecoveryManager(base_path)
    
    return _disaster_recovery_manager

def create_backup(backup_config_id: str, user_id: str = "system", base_path: str = "/var/lib/mingus/backups") -> str:
    """Create backup"""
    manager = get_disaster_recovery_manager(base_path)
    return manager.create_backup(backup_config_id, user_id)

def restore_backup(backup_id: str, target_paths: List[str], user_id: str = "system", base_path: str = "/var/lib/mingus/backups") -> str:
    """Restore backup"""
    manager = get_disaster_recovery_manager(base_path)
    return manager.restore_backup(backup_id, target_paths, user_id)

def list_backups(backup_type: Optional[BackupType] = None, limit: int = 100, base_path: str = "/var/lib/mingus/backups") -> List[BackupMetadata]:
    """List available backups"""
    manager = get_disaster_recovery_manager(base_path)
    return manager.list_backups(backup_type, limit) 