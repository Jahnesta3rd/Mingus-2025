"""
File System Backup System
Comprehensive file backup solution for user documents, configs, and application code
"""

import os
import sys
import shutil
import logging
import json
import time
import datetime
import hashlib
import gzip
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError
import schedule
import threading
from cryptography.fernet import Fernet
import fnmatch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileBackupConfig:
    """Configuration for file system backups"""
    backup_dir: str
    retention_days: int
    compression_enabled: bool
    compression_type: str  # gzip, bzip2, lzma, tar
    encryption_enabled: bool
    encryption_key: str
    cross_region_replication: bool
    s3_bucket: str
    s3_region: str
    aws_access_key: str
    aws_secret_key: str
    backup_verification: bool
    exclude_patterns: List[str]
    include_patterns: List[str]
    max_file_size: int  # bytes
    preserve_permissions: bool
    preserve_timestamps: bool
    backup_schedule: str  # daily, hourly, custom

@dataclass
class FileBackupMetadata:
    """Metadata for file backup operations"""
    backup_id: str
    timestamp: datetime.datetime
    backup_type: str  # full, incremental, selective
    total_files: int
    total_size_bytes: int
    checksum: str
    compression_ratio: float
    encryption_method: str
    backup_path: str
    excluded_files: List[str]
    error_files: List[str]
    status: str  # success, failed, in_progress
    error_message: Optional[str]
    verification_status: str
    backup_time_seconds: Optional[float]

@dataclass
class FileBackupItem:
    """Individual file backup item"""
    file_path: str
    relative_path: str
    size_bytes: int
    checksum: str
    permissions: str
    modified_time: datetime.datetime
    backup_status: str
    error_message: Optional[str]

class FileBackupManager:
    """Comprehensive file system backup management system"""
    
    def __init__(self, config: FileBackupConfig):
        self.config = config
        self.s3_client = None
        self.fernet = None
        self._setup_encryption()
        self._setup_s3()
        self._setup_backup_directory()
        
    def _setup_encryption(self):
        """Initialize encryption components"""
        if self.config.encryption_enabled:
            try:
                if self.config.encryption_key:
                    self.fernet = Fernet(self.config.encryption_key.encode())
                logger.info("File encryption initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize file encryption: {e}")
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
        (backup_path / "documents").mkdir(exist_ok=True)
        (backup_path / "configs").mkdir(exist_ok=True)
        (backup_path / "code").mkdir(exist_ok=True)
        (backup_path / "incremental").mkdir(exist_ok=True)
        (backup_path / "metadata").mkdir(exist_ok=True)
        (backup_path / "temp").mkdir(exist_ok=True)
        
    def _generate_backup_id(self) -> str:
        """Generate unique backup identifier"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"file_backup_{timestamp}_{random_suffix}"
        
    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included in backup based on patterns"""
        file_path_str = str(file_path)
        
        # Check include patterns first
        if self.config.include_patterns:
            included = False
            for pattern in self.config.include_patterns:
                if fnmatch.fnmatch(file_path_str, pattern):
                    included = True
                    break
            if not included:
                return False
                
        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(file_path_str, pattern):
                return False
                
        return True
        
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
            
    def _get_file_info(self, file_path: str) -> Optional[FileBackupItem]:
        """Get file information for backup"""
        try:
            stat = os.stat(file_path)
            
            # Check file size limit
            if stat.st_size > self.config.max_file_size:
                logger.warning(f"File {file_path} exceeds size limit: {stat.st_size} bytes")
                return None
                
            # Check if file should be included
            if not self._should_include_file(file_path):
                return None
                
            # Calculate relative path
            relative_path = os.path.relpath(file_path, start=os.getcwd())
            
            # Get file permissions
            permissions = oct(stat.st_mode)[-3:]
            
            # Get modified time
            modified_time = datetime.datetime.fromtimestamp(stat.st_mtime)
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(file_path)
            
            return FileBackupItem(
                file_path=file_path,
                relative_path=relative_path,
                size_bytes=stat.st_size,
                checksum=checksum,
                permissions=permissions,
                modified_time=modified_time,
                backup_status="pending",
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
            
    def _scan_directory(self, directory_path: str) -> List[FileBackupItem]:
        """Scan directory for files to backup"""
        files_to_backup = []
        excluded_files = []
        error_files = []
        
        try:
            for root, dirs, files in os.walk(directory_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if self._should_include_file(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_info = self._get_file_info(file_path)
                    
                    if file_info:
                        files_to_backup.append(file_info)
                    else:
                        excluded_files.append(file_path)
                        
        except Exception as e:
            logger.error(f"Failed to scan directory {directory_path}: {e}")
            error_files.append(f"Directory scan error: {e}")
            
        return files_to_backup, excluded_files, error_files
        
    def _compress_files(self, files: List[FileBackupItem], backup_id: str) -> Tuple[str, float]:
        """Compress files into archive"""
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.config.compression_type == "tar":
            archive_path = Path(self.config.backup_dir) / "temp" / f"{backup_id}_{timestamp_str}.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                for file_item in files:
                    try:
                        tar.add(file_item.file_path, arcname=file_item.relative_path)
                    except Exception as e:
                        logger.error(f"Failed to add {file_item.file_path} to tar: {e}")
                        file_item.backup_status = "failed"
                        file_item.error_message = str(e)
                        
        elif self.config.compression_type == "zip":
            archive_path = Path(self.config.backup_dir) / "temp" / f"{backup_id}_{timestamp_str}.zip"
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_item in files:
                    try:
                        zipf.write(file_item.file_path, arcname=file_item.relative_path)
                    except Exception as e:
                        logger.error(f"Failed to add {file_item.file_path} to zip: {e}")
                        file_item.backup_status = "failed"
                        file_item.error_message = str(e)
                        
        else:
            # Individual file compression
            archive_path = Path(self.config.backup_dir) / "temp" / backup_id
            archive_path.mkdir(exist_ok=True)
            
            for file_item in files:
                try:
                    compressed_path = archive_path / f"{file_item.relative_path}.gz"
                    compressed_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(file_item.file_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            f_out.writelines(f_in)
                            
                    file_item.backup_status = "success"
                    
                except Exception as e:
                    logger.error(f"Failed to compress {file_item.file_path}: {e}")
                    file_item.backup_status = "failed"
                    file_item.error_message = str(e)
                    
        # Calculate compression ratio
        total_original_size = sum(f.size_bytes for f in files if f.backup_status == "success")
        archive_size = sum(os.path.getsize(f) for f in archive_path.rglob('*') if f.is_file())
        compression_ratio = (1 - archive_size / total_original_size) * 100 if total_original_size > 0 else 0
        
        return str(archive_path), compression_ratio
        
    def _encrypt_backup(self, backup_path: str) -> str:
        """Encrypt backup file"""
        if not self.config.encryption_enabled or not self.fernet:
            return backup_path
            
        try:
            with open(backup_path, 'rb') as f:
                data = f.read()
                
            encrypted_data = self.fernet.encrypt(data)
            encrypted_path = backup_path + ".enc"
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
                
            # Remove original file
            os.remove(backup_path)
            
            return encrypted_path
            
        except Exception as e:
            logger.error(f"Failed to encrypt backup: {e}")
            raise
            
    def create_documents_backup(self, documents_dir: str) -> FileBackupMetadata:
        """Create backup of user documents"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = FileBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="documents",
            total_files=0,
            total_size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            backup_path="",
            excluded_files=[],
            error_files=[],
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            logger.info(f"Starting documents backup: {backup_id}")
            
            # Scan documents directory
            files_to_backup, excluded_files, error_files = self._scan_directory(documents_dir)
            metadata.excluded_files = excluded_files
            metadata.error_files = error_files
            metadata.total_files = len(files_to_backup)
            metadata.total_size_bytes = sum(f.size_bytes for f in files_to_backup)
            
            if not files_to_backup:
                raise Exception("No files found to backup")
                
            # Compress files
            backup_path, compression_ratio = self._compress_files(files_to_backup, backup_id)
            metadata.compression_ratio = compression_ratio
            
            # Encrypt backup
            if self.config.encryption_enabled:
                encrypted_path = self._encrypt_backup(backup_path)
                metadata.encryption_method = "fernet"
                final_path = encrypted_path
            else:
                final_path = backup_path
                
            # Move to final location
            final_backup_path = Path(self.config.backup_dir) / "documents" / f"{backup_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            shutil.move(final_path, final_backup_path)
            
            # Calculate final checksum
            metadata.checksum = self._calculate_file_checksum(str(final_backup_path))
            metadata.backup_path = str(final_backup_path)
            metadata.status = "success"
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(str(final_backup_path), backup_id)
                
            # Verify backup integrity
            if self.config.backup_verification:
                self._verify_backup_integrity(str(final_backup_path), metadata)
                
            logger.info(f"Documents backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Documents backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def create_configs_backup(self, configs_dir: str) -> FileBackupMetadata:
        """Create backup of configuration files"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = FileBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="configs",
            total_files=0,
            total_size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            backup_path="",
            excluded_files=[],
            error_files=[],
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            logger.info(f"Starting configs backup: {backup_id}")
            
            # Scan configs directory
            files_to_backup, excluded_files, error_files = self._scan_directory(configs_dir)
            metadata.excluded_files = excluded_files
            metadata.error_files = error_files
            metadata.total_files = len(files_to_backup)
            metadata.total_size_bytes = sum(f.size_bytes for f in files_to_backup)
            
            if not files_to_backup:
                raise Exception("No configuration files found to backup")
                
            # Compress files
            backup_path, compression_ratio = self._compress_files(files_to_backup, backup_id)
            metadata.compression_ratio = compression_ratio
            
            # Encrypt backup
            if self.config.encryption_enabled:
                encrypted_path = self._encrypt_backup(backup_path)
                metadata.encryption_method = "fernet"
                final_path = encrypted_path
            else:
                final_path = backup_path
                
            # Move to final location
            final_backup_path = Path(self.config.backup_dir) / "configs" / f"{backup_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            shutil.move(final_path, final_backup_path)
            
            # Calculate final checksum
            metadata.checksum = self._calculate_file_checksum(str(final_backup_path))
            metadata.backup_path = str(final_backup_path)
            metadata.status = "success"
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(str(final_backup_path), backup_id)
                
            logger.info(f"Configs backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Configs backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def create_code_backup(self, code_dir: str) -> FileBackupMetadata:
        """Create backup of application code"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = FileBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="code",
            total_files=0,
            total_size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            backup_path="",
            excluded_files=[],
            error_files=[],
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            logger.info(f"Starting code backup: {backup_id}")
            
            # Add common code exclusions
            code_exclusions = [
                '*.pyc', '*.pyo', '__pycache__', '*.so', '*.dll', '*.dylib',
                'node_modules', '.git', '.svn', '.hg', '*.log', '*.tmp',
                '*.cache', '.pytest_cache', 'coverage', 'htmlcov', 'dist',
                'build', '*.egg-info', '.env', '.venv', 'venv'
            ]
            
            # Temporarily add code-specific exclusions
            original_exclusions = self.config.exclude_patterns.copy()
            self.config.exclude_patterns.extend(code_exclusions)
            
            try:
                # Scan code directory
                files_to_backup, excluded_files, error_files = self._scan_directory(code_dir)
                metadata.excluded_files = excluded_files
                metadata.error_files = error_files
                metadata.total_files = len(files_to_backup)
                metadata.total_size_bytes = sum(f.size_bytes for f in files_to_backup)
                
                if not files_to_backup:
                    raise Exception("No code files found to backup")
                    
                # Compress files
                backup_path, compression_ratio = self._compress_files(files_to_backup, backup_id)
                metadata.compression_ratio = compression_ratio
                
                # Encrypt backup
                if self.config.encryption_enabled:
                    encrypted_path = self._encrypt_backup(backup_path)
                    metadata.encryption_method = "fernet"
                    final_path = encrypted_path
                else:
                    final_path = backup_path
                    
                # Move to final location
                final_backup_path = Path(self.config.backup_dir) / "code" / f"{backup_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
                shutil.move(final_path, final_backup_path)
                
                # Calculate final checksum
                metadata.checksum = self._calculate_file_checksum(str(final_backup_path))
                metadata.backup_path = str(final_backup_path)
                metadata.status = "success"
                
                # Save metadata
                self._save_backup_metadata(metadata)
                
                # Upload to S3 if cross-region replication enabled
                if self.config.cross_region_replication:
                    self._upload_to_s3(str(final_backup_path), backup_id)
                    
                logger.info(f"Code backup completed successfully: {backup_id}")
                
            finally:
                # Restore original exclusions
                self.config.exclude_patterns = original_exclusions
                
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Code backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def create_incremental_backup(self, base_dir: str, last_backup_time: datetime.datetime) -> FileBackupMetadata:
        """Create incremental backup of changed files"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = FileBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="incremental",
            total_files=0,
            total_size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            backup_path="",
            excluded_files=[],
            error_files=[],
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            logger.info(f"Starting incremental backup: {backup_id}")
            
            # Find changed files since last backup
            changed_files = []
            excluded_files = []
            error_files = []
            
            for root, dirs, files in os.walk(base_dir):
                dirs[:] = [d for d in dirs if self._should_include_file(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        stat = os.stat(file_path)
                        file_modified = datetime.datetime.fromtimestamp(stat.st_mtime)
                        
                        if file_modified > last_backup_time:
                            file_info = self._get_file_info(file_path)
                            if file_info:
                                changed_files.append(file_info)
                            else:
                                excluded_files.append(file_path)
                                
                    except Exception as e:
                        logger.error(f"Failed to check file {file_path}: {e}")
                        error_files.append(f"{file_path}: {e}")
                        
            metadata.excluded_files = excluded_files
            metadata.error_files = error_files
            metadata.total_files = len(changed_files)
            metadata.total_size_bytes = sum(f.size_bytes for f in changed_files)
            
            if not changed_files:
                logger.info("No files changed since last backup")
                metadata.status = "success"
                metadata.backup_path = "no_changes"
                return metadata
                
            # Compress changed files
            backup_path, compression_ratio = self._compress_files(changed_files, backup_id)
            metadata.compression_ratio = compression_ratio
            
            # Encrypt backup
            if self.config.encryption_enabled:
                encrypted_path = self._encrypt_backup(backup_path)
                metadata.encryption_method = "fernet"
                final_path = encrypted_path
            else:
                final_path = backup_path
                
            # Move to final location
            final_backup_path = Path(self.config.backup_dir) / "incremental" / f"{backup_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            shutil.move(final_path, final_backup_path)
            
            # Calculate final checksum
            metadata.checksum = self._calculate_file_checksum(str(final_backup_path))
            metadata.backup_path = str(final_backup_path)
            metadata.status = "success"
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(str(final_backup_path), backup_id)
                
            logger.info(f"Incremental backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Incremental backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def _save_backup_metadata(self, metadata: FileBackupMetadata):
        """Save backup metadata to file"""
        metadata_path = Path(self.config.backup_dir) / "metadata" / f"{metadata.backup_id}.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, default=str, indent=2)
            
    def _upload_to_s3(self, file_path: str, backup_id: str):
        """Upload backup file to S3 for cross-region replication"""
        try:
            file_name = os.path.basename(file_path)
            s3_key = f"file_backups/{backup_id}/{file_name}"
            
            self.s3_client.upload_file(
                file_path,
                self.config.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            logger.info(f"File backup uploaded to S3: {s3_key}")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
            
    def _verify_backup_integrity(self, backup_path: str, metadata: FileBackupMetadata):
        """Verify backup file integrity"""
        try:
            # Verify file exists
            if not os.path.exists(backup_path):
                raise Exception("Backup file not found")
                
            # Verify checksum
            actual_checksum = self._calculate_file_checksum(backup_path)
            if actual_checksum != metadata.checksum:
                raise Exception(f"Checksum mismatch: expected {metadata.checksum}, got {actual_checksum}")
                
            metadata.verification_status = "verified"
            logger.info(f"File backup integrity verified: {metadata.backup_id}")
            
        except Exception as e:
            metadata.verification_status = "verification_failed"
            logger.error(f"File backup integrity verification failed: {metadata.backup_id} - {e}")
            raise
            
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        try:
            backup_dir = Path(self.config.backup_dir)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config.retention_days)
            
            for backup_type in ["documents", "configs", "code", "incremental"]:
                type_dir = backup_dir / backup_type
                if type_dir.exists():
                    for backup_file in type_dir.iterdir():
                        if backup_file.is_file():
                            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                            if file_time < cutoff_date:
                                backup_file.unlink()
                                logger.info(f"Removed old file backup: {backup_file}")
                                
            # Clean up metadata files
            metadata_dir = backup_dir / "metadata"
            if metadata_dir.exists():
                for metadata_file in metadata_dir.iterdir():
                    if metadata_file.is_file():
                        file_time = datetime.datetime.fromtimestamp(metadata_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            metadata_file.unlink()
                            logger.info(f"Removed old file metadata: {metadata_file}")
                            
        except Exception as e:
            logger.error(f"File backup cleanup failed: {e}")
            
    def get_backup_status(self) -> List[FileBackupMetadata]:
        """Get status of all file backups"""
        metadata_dir = Path(self.config.backup_dir) / "metadata"
        backups = []
        
        if metadata_dir.exists():
            for metadata_file in metadata_dir.iterdir():
                if metadata_file.is_file() and metadata_file.suffix == ".json":
                    try:
                        with open(metadata_file, 'r') as f:
                            data = json.load(f)
                            backup = FileBackupMetadata(**data)
                            backups.append(backup)
                    except Exception as e:
                        logger.error(f"Failed to load file metadata {metadata_file}: {e}")
                        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)
        
    def schedule_backups(self, documents_dir: str, configs_dir: str, code_dir: str):
        """Schedule automated file backups"""
        # Daily full backups at 1 AM
        schedule.every().day.at("01:00").do(self.create_documents_backup, documents_dir)
        schedule.every().day.at("01:30").do(self.create_configs_backup, configs_dir)
        schedule.every().day.at("02:00").do(self.create_code_backup, code_dir)
        
        # Hourly incremental backups during business hours
        for hour in range(9, 18):
            schedule.every().hour.at(f"{hour:02d}:00").do(
                self.create_incremental_backup, 
                documents_dir, 
                datetime.datetime.now() - datetime.timedelta(hours=1)
            )
            
        # Cleanup old backups daily at 3 AM
        schedule.every().day.at("03:00").do(self.cleanup_old_backups)
        
        logger.info("File backup schedule configured")
        
        # Run scheduler in separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("File backup scheduler started")


def create_file_backup_config_from_env() -> FileBackupConfig:
    """Create file backup configuration from environment variables"""
    return FileBackupConfig(
        backup_dir=os.getenv('FILE_BACKUP_DIR', '/var/backups/files'),
        retention_days=int(os.getenv('FILE_BACKUP_RETENTION_DAYS', '30')),
        compression_enabled=os.getenv('FILE_BACKUP_COMPRESSION', 'true').lower() == 'true',
        compression_type=os.getenv('FILE_BACKUP_COMPRESSION_TYPE', 'tar'),
        encryption_enabled=os.getenv('FILE_BACKUP_ENCRYPTION', 'true').lower() == 'true',
        encryption_key=os.getenv('FILE_BACKUP_ENCRYPTION_KEY', ''),
        cross_region_replication=os.getenv('FILE_BACKUP_CROSS_REGION', 'false').lower() == 'true',
        s3_bucket=os.getenv('FILE_BACKUP_S3_BUCKET', ''),
        s3_region=os.getenv('FILE_BACKUP_S3_REGION', 'us-east-1'),
        aws_access_key=os.getenv('AWS_ACCESS_KEY_ID', ''),
        aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY', ''),
        backup_verification=os.getenv('FILE_BACKUP_VERIFICATION', 'true').lower() == 'true',
        exclude_patterns=os.getenv('FILE_BACKUP_EXCLUDE_PATTERNS', '*.tmp,*.log,*.cache,.git').split(','),
        include_patterns=os.getenv('FILE_BACKUP_INCLUDE_PATTERNS', '').split(','),
        max_file_size=int(os.getenv('FILE_BACKUP_MAX_FILE_SIZE', '1073741824')),  # 1GB
        preserve_permissions=os.getenv('FILE_BACKUP_PRESERVE_PERMISSIONS', 'true').lower() == 'true',
        preserve_timestamps=os.getenv('FILE_BACKUP_PRESERVE_TIMESTAMPS', 'true').lower() == 'true',
        backup_schedule=os.getenv('FILE_BACKUP_SCHEDULE', 'daily')
    )


if __name__ == "__main__":
    # Example usage
    config = create_file_backup_config_from_env()
    backup_manager = FileBackupManager(config)
    
    # Create immediate backups
    documents_metadata = backup_manager.create_documents_backup("./documents")
    configs_metadata = backup_manager.create_configs_backup("./config")
    code_metadata = backup_manager.create_code_backup("./backend")
    
    print(f"Documents backup completed: {documents_metadata.backup_id}")
    print(f"Configs backup completed: {configs_metadata.backup_id}")
    print(f"Code backup completed: {code_metadata.backup_id}")
    
    # Schedule automated backups
    backup_manager.schedule_backups("./documents", "./config", "./backend")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("File backup manager stopped")
