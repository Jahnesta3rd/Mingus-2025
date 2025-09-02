"""
PostgreSQL Database Backup System
Enterprise-grade backup solution for financial applications with compliance requirements
"""

import os
import sys
import subprocess
import logging
import hashlib
import gzip
import bz2
import lzma
import json
import time
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import boto3
from botocore.exceptions import ClientError
import gnupg
from cryptography.fernet import Fernet
import schedule
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Configuration for database backups"""
    host: str
    port: int
    database: str
    username: str
    password: str
    backup_dir: str
    retention_days: int
    compression_type: str  # gzip, bzip2, lzma
    encryption_enabled: bool
    encryption_key: str
    cross_region_replication: bool
    s3_bucket: str
    s3_region: str
    aws_access_key: str
    aws_secret_key: str
    pg_dump_path: str
    pg_restore_path: str
    backup_verification: bool
    point_in_time_recovery: bool
    wal_archiving: bool
    wal_archive_dir: str

@dataclass
class BackupMetadata:
    """Metadata for backup operations"""
    backup_id: str
    timestamp: datetime.datetime
    backup_type: str  # full, incremental, wal
    size_bytes: int
    checksum: str
    compression_ratio: float
    encryption_method: str
    database_version: str
    tables_count: int
    status: str  # success, failed, in_progress
    error_message: Optional[str]
    verification_status: str
    recovery_time_seconds: Optional[float]

class PostgreSQLBackupManager:
    """Comprehensive PostgreSQL backup management system"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.gpg = None
        self.fernet = None
        self.s3_client = None
        self._setup_encryption()
        self._setup_s3()
        self._setup_backup_directory()
        
    def _setup_encryption(self):
        """Initialize encryption components"""
        if self.config.encryption_enabled:
            try:
                # Setup GPG for asymmetric encryption
                self.gpg = gnupg.GPG()
                
                # Setup Fernet for symmetric encryption
                if self.config.encryption_key:
                    self.fernet = Fernet(self.config.encryption_key.encode())
                    
                logger.info("Encryption components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize encryption: {e}")
                raise
                
    def _setup_s3(self):
        """Initialize S3 client for cross-region replication"""
        if self.config.cross_region_replication:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.config.aws_access_key,
                    aws_secret_access_key=self.config.aws_secret_key,
                    region_name=self.config.s3_region
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                raise
                
    def _setup_backup_directory(self):
        """Create backup directory structure"""
        backup_path = Path(self.config.backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (backup_path / "full").mkdir(exist_ok=True)
        (backup_path / "incremental").mkdir(exist_ok=True)
        (backup_path / "wal").mkdir(exist_ok=True)
        (backup_path / "metadata").mkdir(exist_ok=True)
        (backup_path / "temp").mkdir(exist_ok=True)
        
    def _generate_backup_id(self) -> str:
        """Generate unique backup identifier"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"backup_{timestamp}_{random_suffix}"
        
    def _get_compression_command(self, compression_type: str) -> Tuple[str, str]:
        """Get compression command and file extension"""
        if compression_type == "gzip":
            return "gzip", ".gz"
        elif compression_type == "bzip2":
            return "bzip2", ".bz2"
        elif compression_type == "lzma":
            return "xz", ".xz"
        else:
            return "gzip", ".gz"
            
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
        
    def _compress_file(self, input_path: str, compression_type: str) -> Tuple[str, float]:
        """Compress file and return output path and compression ratio"""
        comp_cmd, ext = self._get_compression_command(compression_type)
        output_path = input_path + ext
        
        try:
            # Get original file size
            original_size = os.path.getsize(input_path)
            
            # Compress file
            if comp_cmd == "gzip":
                with open(input_path, 'rb') as f_in:
                    with gzip.open(output_path, 'wb') as f_out:
                        f_out.writelines(f_in)
            elif comp_cmd == "bzip2":
                with open(input_path, 'rb') as f_in:
                    with bz2.open(output_path, 'wb') as f_out:
                        f_out.writelines(f_in)
            elif comp_cmd == "xz":
                with open(input_path, 'rb') as f_in:
                    with lzma.open(output_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                        
            # Calculate compression ratio
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            # Remove original file
            os.remove(input_path)
            
            return output_path, compression_ratio
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise
            
    def _encrypt_file(self, file_path: str) -> str:
        """Encrypt file using configured encryption method"""
        if not self.config.encryption_enabled:
            return file_path
            
        try:
            if self.fernet:
                # Symmetric encryption with Fernet
                with open(file_path, 'rb') as f:
                    data = f.read()
                encrypted_data = self.fernet.encrypt(data)
                
                encrypted_path = file_path + ".enc"
                with open(encrypted_path, 'wb') as f:
                    f.write(encrypted_data)
                    
                os.remove(file_path)
                return encrypted_path
                
            elif self.gpg:
                # Asymmetric encryption with GPG
                encrypted_path = file_path + ".gpg"
                with open(file_path, 'rb') as f:
                    self.gpg.encrypt_file(
                        f,
                        recipients=[self.config.encryption_key],
                        output=encrypted_path
                    )
                    
                os.remove(file_path)
                return encrypted_path
                
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
            
        return file_path
        
    def _test_database_connection(self) -> bool:
        """Test database connectivity"""
        try:
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password
            )
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
            
    def _get_database_info(self) -> Dict[str, str]:
        """Get database version and table count"""
        try:
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password
            )
            
            cursor = conn.cursor()
            
            # Get PostgreSQL version
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                "version": version,
                "tables_count": str(tables_count)
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"version": "unknown", "tables_count": "0"}
            
    def create_full_backup(self) -> BackupMetadata:
        """Create full database backup"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="full",
            size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            database_version="",
            tables_count=0,
            status="in_progress",
            error_message=None,
            verification_status="pending",
            recovery_time_seconds=None
        )
        
        try:
            # Test database connection
            if not self._test_database_connection():
                raise Exception("Database connection failed")
                
            # Get database info
            db_info = self._get_database_info()
            metadata.database_version = db_info["version"]
            metadata.tables_count = int(db_info["tables_count"])
            
            # Create backup filename
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"full_backup_{backup_id}_{timestamp_str}.sql"
            backup_path = Path(self.config.backup_dir) / "full" / backup_filename
            
            # Execute pg_dump
            cmd = [
                self.config.pg_dump_path,
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--username={self.config.username}",
                f"--dbname={self.config.database}",
                "--verbose",
                "--no-password",
                "--format=custom",
                f"--file={backup_path}"
            ]
            
            # Set environment variable for password
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.password
            
            logger.info(f"Starting full backup: {backup_id}")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
                
            # Calculate file size and checksum
            metadata.size_bytes = os.path.getsize(backup_path)
            metadata.checksum = self._calculate_checksum(str(backup_path))
            
            # Compress backup
            compressed_path, compression_ratio = self._compress_file(
                str(backup_path), 
                self.config.compression_type
            )
            metadata.compression_ratio = compression_ratio
            
            # Encrypt backup
            if self.config.encryption_enabled:
                encrypted_path = self._encrypt_file(compressed_path)
                metadata.encryption_method = self.config.encryption_type
                final_path = encrypted_path
            else:
                final_path = compressed_path
                
            # Update metadata
            metadata.status = "success"
            metadata.size_bytes = os.path.getsize(final_path)
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(final_path, backup_id)
                
            # Verify backup integrity
            if self.config.backup_verification:
                self._verify_backup_integrity(final_path, metadata)
                
            logger.info(f"Full backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Full backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate recovery time
            recovery_time = time.time() - start_time
            metadata.recovery_time_seconds = recovery_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def create_incremental_backup(self) -> BackupMetadata:
        """Create incremental backup using WAL archiving"""
        if not self.config.wal_archiving:
            raise Exception("WAL archiving not enabled for incremental backups")
            
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="incremental",
            size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            database_version="",
            tables_count=0,
            status="in_progress",
            error_message=None,
            verification_status="pending",
            recovery_time_seconds=None
        )
        
        try:
            # Get database info
            db_info = self._get_database_info()
            metadata.database_version = db_info["version"]
            metadata.tables_count = int(db_info["tables_count"])
            
            # Create WAL backup
            wal_dir = Path(self.config.wal_archive_dir)
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            wal_backup_filename = f"wal_backup_{backup_id}_{timestamp_str}.tar"
            wal_backup_path = Path(self.config.backup_dir) / "incremental" / wal_backup_filename
            
            # Create tar archive of WAL files
            cmd = [
                "tar",
                "-czf",
                str(wal_backup_path),
                "-C",
                str(wal_dir.parent),
                wal_dir.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"WAL backup creation failed: {result.stderr}")
                
            # Calculate file size and checksum
            metadata.size_bytes = os.path.getsize(wal_backup_path)
            metadata.checksum = self._calculate_checksum(str(wal_backup_path))
            
            # Encrypt backup
            if self.config.encryption_enabled:
                encrypted_path = self._encrypt_file(str(wal_backup_path))
                metadata.encryption_method = self.config.encryption_type
                final_path = encrypted_path
            else:
                final_path = str(wal_backup_path)
                
            # Update metadata
            metadata.status = "success"
            metadata.size_bytes = os.path.getsize(final_path)
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(final_path, backup_id)
                
            logger.info(f"Incremental backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Incremental backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate recovery time
            recovery_time = time.time() - start_time
            metadata.recovery_time_seconds = recovery_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to file"""
        metadata_path = Path(self.config.backup_dir) / "metadata" / f"{metadata.backup_id}.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, default=str, indent=2)
            
    def _upload_to_s3(self, file_path: str, backup_id: str):
        """Upload backup file to S3 for cross-region replication"""
        try:
            file_name = os.path.basename(file_path)
            s3_key = f"backups/{backup_id}/{file_name}"
            
            self.s3_client.upload_file(
                file_path,
                self.config.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            logger.info(f"Backup uploaded to S3: {s3_key}")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
            
    def _verify_backup_integrity(self, backup_path: str, metadata: BackupMetadata):
        """Verify backup file integrity"""
        try:
            # Verify file size
            actual_size = os.path.getsize(backup_path)
            if actual_size != metadata.size_bytes:
                raise Exception(f"File size mismatch: expected {metadata.size_bytes}, got {actual_size}")
                
            # Verify checksum
            actual_checksum = self._calculate_checksum(backup_path)
            if actual_checksum != metadata.checksum:
                raise Exception(f"Checksum mismatch: expected {metadata.checksum}, got {actual_checksum}")
                
            # Test restore to temporary location
            if metadata.backup_type == "full":
                self._test_backup_restore(backup_path)
                
            metadata.verification_status = "verified"
            logger.info(f"Backup integrity verified: {metadata.backup_id}")
            
        except Exception as e:
            metadata.verification_status = "verification_failed"
            logger.error(f"Backup integrity verification failed: {metadata.backup_id} - {e}")
            raise
            
    def _test_backup_restore(self, backup_path: str):
        """Test backup restore to temporary location"""
        try:
            # Create temporary database for testing
            temp_db_name = f"test_restore_{int(time.time())}"
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database="postgres",
                user=self.config.username,
                password=self.config.password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Create temporary database
            cursor.execute(f"CREATE DATABASE {temp_db_name}")
            cursor.close()
            conn.close()
            
            # Restore backup to temporary database
            restore_cmd = [
                self.config.pg_restore_path,
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--username={self.config.username}",
                f"--dbname={temp_db_name}",
                "--verbose",
                "--no-password",
                "--clean",
                "--if-exists",
                backup_path
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.password
            
            result = subprocess.run(
                restore_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Test restore failed: {result.stderr}")
                
            # Clean up temporary database
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database="postgres",
                user=self.config.username,
                password=self.config.password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE {temp_db_name}")
            cursor.close()
            conn.close()
            
            logger.info("Backup restore test completed successfully")
            
        except Exception as e:
            logger.error(f"Backup restore test failed: {e}")
            raise
            
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        try:
            backup_dir = Path(self.config.backup_dir)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config.retention_days)
            
            for backup_type in ["full", "incremental", "wal"]:
                type_dir = backup_dir / backup_type
                if type_dir.exists():
                    for backup_file in type_dir.iterdir():
                        if backup_file.is_file():
                            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                            if file_time < cutoff_date:
                                backup_file.unlink()
                                logger.info(f"Removed old backup: {backup_file}")
                                
            # Clean up metadata files
            metadata_dir = backup_dir / "metadata"
            if metadata_dir.exists():
                for metadata_file in metadata_dir.iterdir():
                    if metadata_file.is_file():
                        file_time = datetime.datetime.fromtimestamp(metadata_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            metadata_file.unlink()
                            logger.info(f"Removed old metadata: {metadata_file}")
                            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            
    def get_backup_status(self) -> List[BackupMetadata]:
        """Get status of all backups"""
        metadata_dir = Path(self.config.backup_dir) / "metadata"
        backups = []
        
        if metadata_dir.exists():
            for metadata_file in metadata_dir.iterdir():
                if metadata_file.is_file() and metadata_file.suffix == ".json":
                    try:
                        with open(metadata_file, 'r') as f:
                            data = json.load(f)
                            backup = BackupMetadata(**data)
                            backups.append(backup)
                    except Exception as e:
                        logger.error(f"Failed to load metadata {metadata_file}: {e}")
                        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)
        
    def schedule_backups(self):
        """Schedule automated backups"""
        # Daily full backup at 2 AM
        schedule.every().day.at("02:00").do(self.create_full_backup)
        
        # Hourly incremental backups during business hours (9 AM - 6 PM)
        for hour in range(9, 18):
            schedule.every().hour.at(f"{hour:02d}:00").do(self.create_incremental_backup)
            
        # Cleanup old backups daily at 3 AM
        schedule.every().day.at("03:00").do(self.cleanup_old_backups)
        
        logger.info("Backup schedule configured")
        
        # Run scheduler in separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Backup scheduler started")


def create_backup_config_from_env() -> BackupConfig:
    """Create backup configuration from environment variables"""
    return BackupConfig(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        database=os.getenv('POSTGRES_DB', 'mingus'),
        username=os.getenv('POSTGRES_USER', 'mingus'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        backup_dir=os.getenv('BACKUP_DIR', '/var/backups/postgresql'),
        retention_days=int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
        compression_type=os.getenv('BACKUP_COMPRESSION', 'gzip'),
        encryption_enabled=os.getenv('BACKUP_ENCRYPTION', 'true').lower() == 'true',
        encryption_key=os.getenv('BACKUP_ENCRYPTION_KEY', ''),
        cross_region_replication=os.getenv('BACKUP_CROSS_REGION', 'false').lower() == 'true',
        s3_bucket=os.getenv('BACKUP_S3_BUCKET', ''),
        s3_region=os.getenv('BACKUP_S3_REGION', 'us-east-1'),
        aws_access_key=os.getenv('AWS_ACCESS_KEY_ID', ''),
        aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY', ''),
        pg_dump_path=os.getenv('PG_DUMP_PATH', 'pg_dump'),
        pg_restore_path=os.getenv('PG_RESTORE_PATH', 'pg_restore'),
        backup_verification=os.getenv('BACKUP_VERIFICATION', 'true').lower() == 'true',
        point_in_time_recovery=os.getenv('BACKUP_PITR', 'true').lower() == 'true',
        wal_archiving=os.getenv('BACKUP_WAL_ARCHIVING', 'true').lower() == 'true',
        wal_archive_dir=os.getenv('BACKUP_WAL_ARCHIVE_DIR', '/var/lib/postgresql/wal_archive')
    )


if __name__ == "__main__":
    # Example usage
    config = create_backup_config_from_env()
    backup_manager = PostgreSQLBackupManager(config)
    
    # Create immediate backup
    metadata = backup_manager.create_full_backup()
    print(f"Backup completed: {metadata.backup_id}")
    
    # Schedule automated backups
    backup_manager.schedule_backups()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Backup manager stopped")
