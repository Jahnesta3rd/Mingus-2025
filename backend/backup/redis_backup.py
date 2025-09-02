"""
Redis Backup and Persistence System
Comprehensive Redis backup solution with RDB, AOF, and session data management
"""

import os
import sys
import subprocess
import logging
import json
import time
import datetime
import shutil
import hashlib
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import redis
import boto3
from botocore.exceptions import ClientError
import schedule
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RedisBackupConfig:
    """Configuration for Redis backups"""
    host: str
    port: int
    password: str
    backup_dir: str
    retention_days: int
    rdb_backup_enabled: bool
    aof_backup_enabled: bool
    session_backup_enabled: bool
    compression_enabled: bool
    encryption_enabled: bool
    encryption_key: str
    cross_region_replication: bool
    s3_bucket: str
    s3_region: str
    aws_access_key: str
    aws_secret_key: str
    redis_cli_path: str
    backup_verification: bool
    auto_backup_interval: int  # minutes
    max_memory_policy: str
    save_configuration: List[str]

@dataclass
class RedisBackupMetadata:
    """Metadata for Redis backup operations"""
    backup_id: str
    timestamp: datetime.datetime
    backup_type: str  # rdb, aof, session, config
    size_bytes: int
    checksum: str
    compression_ratio: float
    encryption_method: str
    redis_version: str
    keys_count: int
    memory_usage: int
    status: str  # success, failed, in_progress
    error_message: Optional[str]
    verification_status: str
    backup_time_seconds: Optional[float]

class RedisBackupManager:
    """Comprehensive Redis backup management system"""
    
    def __init__(self, config: RedisBackupConfig):
        self.config = config
        self.redis_client = None
        self.s3_client = None
        self._setup_redis_connection()
        self._setup_s3()
        self._setup_backup_directory()
        self._configure_redis_persistence()
        
    def _setup_redis_connection(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                decode_responses=False,
                socket_connect_timeout=10,
                socket_timeout=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to establish Redis connection: {e}")
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
        (backup_path / "rdb").mkdir(exist_ok=True)
        (backup_path / "aof").mkdir(exist_ok=True)
        (backup_path / "session").mkdir(exist_ok=True)
        (backup_path / "config").mkdir(exist_ok=True)
        (backup_path / "metadata").mkdir(exist_ok=True)
        (backup_path / "temp").mkdir(exist_ok=True)
        
    def _configure_redis_persistence(self):
        """Configure Redis persistence settings"""
        try:
            # Configure RDB persistence
            if self.config.rdb_backup_enabled:
                self._configure_rdb_persistence()
                
            # Configure AOF persistence
            if self.config.aof_backup_enabled:
                self._configure_aof_persistence()
                
            # Set memory policy
            if self.config.max_memory_policy:
                self.redis_client.config_set('maxmemory-policy', self.config.max_memory_policy)
                
            logger.info("Redis persistence configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure Redis persistence: {e}")
            raise
            
    def _configure_rdb_persistence(self):
        """Configure RDB snapshot persistence"""
        try:
            # Set save configuration
            for save_config in self.config.save_configuration:
                self.redis_client.config_set('save', save_config)
                
            # Enable RDB persistence
            self.redis_client.config_set('stop-writes-on-bgsave-error', 'yes')
            self.redis_client.config_set('rdbcompression', 'yes')
            self.redis_client.config_set('rdbchecksum', 'yes')
            
            logger.info("RDB persistence configured")
            
        except Exception as e:
            logger.error(f"Failed to configure RDB persistence: {e}")
            raise
            
    def _configure_aof_persistence(self):
        """Configure AOF persistence"""
        try:
            # Enable AOF
            self.redis_client.config_set('appendonly', 'yes')
            self.redis_client.config_set('appendfsync', 'everysec')
            self.redis_client.config_set('no-appendfsync-on-rewrite', 'no')
            self.redis_client.config_set('auto-aof-rewrite-percentage', '100')
            self.redis_client.config_set('auto-aof-rewrite-min-size', '64mb')
            
            logger.info("AOF persistence configured")
            
        except Exception as e:
            logger.error(f"Failed to configure AOF persistence: {e}")
            raise
            
    def _generate_backup_id(self) -> str:
        """Generate unique backup identifier"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"redis_backup_{timestamp}_{random_suffix}"
        
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
        
    def _compress_file(self, input_path: str) -> Tuple[str, float]:
        """Compress file and return output path and compression ratio"""
        if not self.config.compression_enabled:
            return input_path, 0.0
            
        output_path = input_path + ".gz"
        
        try:
            # Get original file size
            original_size = os.path.getsize(input_path)
            
            # Compress file
            with open(input_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb') as f_out:
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
            
    def _get_redis_info(self) -> Dict[str, str]:
        """Get Redis server information"""
        try:
            info = self.redis_client.info()
            return {
                "version": info.get(b'redis_version', b'unknown').decode('utf-8'),
                "keys_count": str(info.get(b'db0', {}).get(b'keys', 0)),
                "memory_usage": str(info.get(b'used_memory', 0)),
                "uptime": str(info.get(b'uptime_in_seconds', 0))
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {"version": "unknown", "keys_count": "0", "memory_usage": "0", "uptime": "0"}
            
    def create_rdb_backup(self) -> RedisBackupMetadata:
        """Create RDB snapshot backup"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = RedisBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="rdb",
            size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            redis_version="",
            keys_count=0,
            memory_usage=0,
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            # Get Redis info
            redis_info = self._get_redis_info()
            metadata.redis_version = redis_info["version"]
            metadata.keys_count = int(redis_info["keys_count"])
            metadata.memory_usage = int(redis_info["memory_usage"])
            
            # Trigger RDB save
            logger.info(f"Starting RDB backup: {backup_id}")
            self.redis_client.bgsave()
            
            # Wait for save to complete
            while True:
                save_status = self.redis_client.info('persistence')
                if save_status.get(b'rdb_bgsave_in_progress', 0) == 0:
                    break
                time.sleep(1)
                
            # Get RDB file path
            rdb_path = self.redis_client.config_get('dir')[b'dir'].decode('utf-8')
            rdb_file = os.path.join(rdb_path, 'dump.rdb')
            
            if not os.path.exists(rdb_file):
                raise Exception("RDB file not found after save operation")
                
            # Create backup filename
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"rdb_backup_{backup_id}_{timestamp_str}.rdb"
            backup_path = Path(self.config.backup_dir) / "rdb" / backup_filename
            
            # Copy RDB file to backup location
            shutil.copy2(rdb_file, backup_path)
            
            # Calculate file size and checksum
            metadata.size_bytes = os.path.getsize(backup_path)
            metadata.checksum = self._calculate_checksum(str(backup_path))
            
            # Compress backup
            if self.config.compression_enabled:
                compressed_path, compression_ratio = self._compress_file(str(backup_path))
                metadata.compression_ratio = compression_ratio
                final_path = compressed_path
            else:
                final_path = str(backup_path)
                
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
                
            logger.info(f"RDB backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"RDB backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def create_aof_backup(self) -> RedisBackupMetadata:
        """Create AOF file backup"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = RedisBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="aof",
            size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            redis_version="",
            keys_count=0,
            memory_usage=0,
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            # Get Redis info
            redis_info = self._get_redis_info()
            metadata.redis_version = redis_info["version"]
            metadata.keys_count = int(redis_info["keys_count"])
            metadata.memory_usage = int(redis_info["memory_usage"])
            
            # Get AOF file path
            aof_path = self.redis_client.config_get('dir')[b'dir'].decode('utf-8')
            aof_file = os.path.join(aof_path, 'appendonly.aof')
            
            if not os.path.exists(aof_file):
                raise Exception("AOF file not found")
                
            # Create backup filename
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"aof_backup_{backup_id}_{timestamp_str}.aof"
            backup_path = Path(self.config.backup_dir) / "aof" / backup_filename
            
            # Copy AOF file to backup location
            shutil.copy2(aof_file, backup_path)
            
            # Calculate file size and checksum
            metadata.size_bytes = os.path.getsize(backup_path)
            metadata.checksum = self._calculate_checksum(str(backup_path))
            
            # Compress backup
            if self.config.compression_enabled:
                compressed_path, compression_ratio = self._compress_file(str(backup_path))
                metadata.compression_ratio = compression_ratio
                final_path = compressed_path
            else:
                final_path = str(backup_path)
                
            # Update metadata
            metadata.status = "success"
            metadata.size_bytes = os.path.getsize(final_path)
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(final_path, backup_id)
                
            logger.info(f"AOF backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"AOF backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def create_session_backup(self) -> RedisBackupMetadata:
        """Create session data backup"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = RedisBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="session",
            size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            redis_version="",
            keys_count=0,
            memory_usage=0,
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            # Get Redis info
            redis_info = self._get_redis_info()
            metadata.redis_version = redis_info["version"]
            metadata.keys_count = int(redis_info["keys_count"])
            metadata.memory_usage = int(redis_info["memory_usage"])
            
            # Create backup filename
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"session_backup_{backup_id}_{timestamp_str}.json"
            backup_path = Path(self.config.backup_dir) / "session" / backup_filename
            temp_path = Path(self.config.backup_dir) / "temp" / backup_filename
            
            # Export session data
            session_data = {}
            
            # Get all keys
            all_keys = self.redis_client.keys('*')
            for key in all_keys:
                try:
                    key_str = key.decode('utf-8')
                    key_type = self.redis_client.type(key)
                    
                    if key_type == b'string':
                        value = self.redis_client.get(key)
                        session_data[key_str] = {
                            'type': 'string',
                            'value': value.decode('utf-8') if value else None,
                            'ttl': self.redis_client.ttl(key)
                        }
                    elif key_type == b'hash':
                        value = self.redis_client.hgetall(key)
                        session_data[key_str] = {
                            'type': 'hash',
                            'value': {k.decode('utf-8'): v.decode('utf-8') for k, v in value.items()},
                            'ttl': self.redis_client.ttl(key)
                        }
                    elif key_type == b'set':
                        value = self.redis_client.smembers(key)
                        session_data[key_str] = {
                            'type': 'set',
                            'value': [v.decode('utf-8') for v in value],
                            'ttl': self.redis_client.ttl(key)
                        }
                    elif key_type == b'list':
                        value = self.redis_client.lrange(key, 0, -1)
                        session_data[key_str] = {
                            'type': 'list',
                            'value': [v.decode('utf-8') for v in value],
                            'ttl': self.redis_client.ttl(key)
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to export key {key}: {e}")
                    continue
                    
            # Save session data to file
            with open(temp_path, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            # Move to final location
            shutil.move(str(temp_path), str(backup_path))
            
            # Calculate file size and checksum
            metadata.size_bytes = os.path.getsize(backup_path)
            metadata.checksum = self._calculate_checksum(str(backup_path))
            
            # Compress backup
            if self.config.compression_enabled:
                compressed_path, compression_ratio = self._compress_file(str(backup_path))
                metadata.compression_ratio = compression_ratio
                final_path = compressed_path
            else:
                final_path = str(backup_path)
                
            # Update metadata
            metadata.status = "success"
            metadata.size_bytes = os.path.getsize(final_path)
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(final_path, backup_id)
                
            logger.info(f"Session backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Session backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def create_config_backup(self) -> RedisBackupMetadata:
        """Create Redis configuration backup"""
        backup_id = self._generate_backup_id()
        start_time = time.time()
        
        metadata = RedisBackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type="config",
            size_bytes=0,
            checksum="",
            compression_ratio=0.0,
            encryption_method="none",
            redis_version="",
            keys_count=0,
            memory_usage=0,
            status="in_progress",
            error_message=None,
            verification_status="pending",
            backup_time_seconds=None
        )
        
        try:
            # Get Redis info
            redis_info = self._get_redis_info()
            metadata.redis_version = redis_info["version"]
            metadata.keys_count = int(redis_info["keys_count"])
            metadata.memory_usage = int(redis_info["memory_usage"])
            
            # Create backup filename
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{backup_id}_{timestamp_str}.conf"
            backup_path = Path(self.config.backup_dir) / "config" / backup_filename
            temp_path = Path(self.config.backup_dir) / "temp" / backup_filename
            
            # Export configuration
            config_data = {}
            
            # Get all configuration parameters
            config_keys = [
                'maxmemory', 'maxmemory-policy', 'save', 'appendonly', 'appendfsync',
                'dir', 'dbfilename', 'requirepass', 'port', 'bind', 'timeout',
                'tcp-keepalive', 'loglevel', 'logfile', 'databases', 'rdbcompression',
                'rdbchecksum', 'stop-writes-on-bgsave-error'
            ]
            
            for key in config_keys:
                try:
                    value = self.redis_client.config_get(key)
                    if value:
                        config_data[key] = value.get(key.decode('utf-8'), '').decode('utf-8')
                except Exception as e:
                    logger.warning(f"Failed to get config {key}: {e}")
                    continue
                    
            # Save configuration to file
            with open(temp_path, 'w') as f:
                for key, value in config_data.items():
                    f.write(f"{key} {value}\n")
                    
            # Move to final location
            shutil.move(str(temp_path), str(backup_path))
            
            # Calculate file size and checksum
            metadata.size_bytes = os.path.getsize(backup_path)
            metadata.checksum = self._calculate_checksum(str(backup_path))
            
            # Compress backup
            if self.config.compression_enabled:
                compressed_path, compression_ratio = self._compress_file(str(backup_path))
                metadata.compression_ratio = compression_ratio
                final_path = compressed_path
            else:
                final_path = str(backup_path)
                
            # Update metadata
            metadata.status = "success"
            metadata.size_bytes = os.path.getsize(final_path)
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to S3 if cross-region replication enabled
            if self.config.cross_region_replication:
                self._upload_to_s3(final_path, backup_id)
                
            logger.info(f"Config backup completed successfully: {backup_id}")
            
        except Exception as e:
            metadata.status = "failed"
            metadata.error_message = str(e)
            logger.error(f"Config backup failed: {backup_id} - {e}")
            
        finally:
            # Calculate backup time
            backup_time = time.time() - start_time
            metadata.backup_time_seconds = backup_time
            
            # Update metadata
            self._save_backup_metadata(metadata)
            
        return metadata
        
    def _save_backup_metadata(self, metadata: RedisBackupMetadata):
        """Save backup metadata to file"""
        metadata_path = Path(self.config.backup_dir) / "metadata" / f"{metadata.backup_id}.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, default=str, indent=2)
            
    def _upload_to_s3(self, file_path: str, backup_id: str):
        """Upload backup file to S3 for cross-region replication"""
        try:
            file_name = os.path.basename(file_path)
            s3_key = f"redis_backups/{backup_id}/{file_name}"
            
            self.s3_client.upload_file(
                file_path,
                self.config.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            logger.info(f"Redis backup uploaded to S3: {s3_key}")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
            
    def _verify_backup_integrity(self, backup_path: str, metadata: RedisBackupMetadata):
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
                
            metadata.verification_status = "verified"
            logger.info(f"Redis backup integrity verified: {metadata.backup_id}")
            
        except Exception as e:
            metadata.verification_status = "verification_failed"
            logger.error(f"Redis backup integrity verification failed: {metadata.backup_id} - {e}")
            raise
            
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        try:
            backup_dir = Path(self.config.backup_dir)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config.retention_days)
            
            for backup_type in ["rdb", "aof", "session", "config"]:
                type_dir = backup_dir / backup_type
                if type_dir.exists():
                    for backup_file in type_dir.iterdir():
                        if backup_file.is_file():
                            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                            if file_time < cutoff_date:
                                backup_file.unlink()
                                logger.info(f"Removed old Redis backup: {backup_file}")
                                
            # Clean up metadata files
            metadata_dir = backup_dir / "metadata"
            if metadata_dir.exists():
                for metadata_file in metadata_dir.iterdir():
                    if metadata_file.is_file():
                        file_time = datetime.datetime.fromtimestamp(metadata_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            metadata_file.unlink()
                            logger.info(f"Removed old Redis metadata: {metadata_file}")
                            
        except Exception as e:
            logger.error(f"Redis backup cleanup failed: {e}")
            
    def get_backup_status(self) -> List[RedisBackupMetadata]:
        """Get status of all Redis backups"""
        metadata_dir = Path(self.config.backup_dir) / "metadata"
        backups = []
        
        if metadata_dir.exists():
            for metadata_file in metadata_dir.iterdir():
                if metadata_file.is_file() and metadata_file.suffix == ".json":
                    try:
                        with open(metadata_file, 'r') as f:
                            data = json.load(f)
                            backup = RedisBackupMetadata(**data)
                            backups.append(backup)
                    except Exception as e:
                        logger.error(f"Failed to load Redis metadata {metadata_file}: {e}")
                        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)
        
    def schedule_backups(self):
        """Schedule automated Redis backups"""
        # RDB backup every 6 hours
        schedule.every(6).hours.do(self.create_rdb_backup)
        
        # AOF backup every hour
        schedule.every().hour.do(self.create_aof_backup)
        
        # Session backup every 30 minutes
        schedule.every(30).minutes.do(self.create_session_backup)
        
        # Config backup daily at 1 AM
        schedule.every().day.at("01:00").do(self.create_config_backup)
        
        # Cleanup old backups daily at 4 AM
        schedule.every().day.at("04:00").do(self.cleanup_old_backups)
        
        logger.info("Redis backup schedule configured")
        
        # Run scheduler in separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Redis backup scheduler started")


def create_redis_backup_config_from_env() -> RedisBackupConfig:
    """Create Redis backup configuration from environment variables"""
    return RedisBackupConfig(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        password=os.getenv('REDIS_PASSWORD', ''),
        backup_dir=os.getenv('REDIS_BACKUP_DIR', '/var/backups/redis'),
        retention_days=int(os.getenv('REDIS_BACKUP_RETENTION_DAYS', '30')),
        rdb_backup_enabled=os.getenv('REDIS_RDB_BACKUP', 'true').lower() == 'true',
        aof_backup_enabled=os.getenv('REDIS_AOF_BACKUP', 'true').lower() == 'true',
        session_backup_enabled=os.getenv('REDIS_SESSION_BACKUP', 'true').lower() == 'true',
        compression_enabled=os.getenv('REDIS_BACKUP_COMPRESSION', 'true').lower() == 'true',
        encryption_enabled=os.getenv('REDIS_BACKUP_ENCRYPTION', 'false').lower() == 'true',
        encryption_key=os.getenv('REDIS_BACKUP_ENCRYPTION_KEY', ''),
        cross_region_replication=os.getenv('REDIS_BACKUP_CROSS_REGION', 'false').lower() == 'true',
        s3_bucket=os.getenv('REDIS_BACKUP_S3_BUCKET', ''),
        s3_region=os.getenv('REDIS_BACKUP_S3_REGION', 'us-east-1'),
        aws_access_key=os.getenv('AWS_ACCESS_KEY_ID', ''),
        aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY', ''),
        redis_cli_path=os.getenv('REDIS_CLI_PATH', 'redis-cli'),
        backup_verification=os.getenv('REDIS_BACKUP_VERIFICATION', 'true').lower() == 'true',
        auto_backup_interval=int(os.getenv('REDIS_AUTO_BACKUP_INTERVAL', '30')),
        max_memory_policy=os.getenv('REDIS_MAX_MEMORY_POLICY', 'allkeys-lru'),
        save_configuration=os.getenv('REDIS_SAVE_CONFIG', '900 1 300 10 60 10000').split()
    )


if __name__ == "__main__":
    # Example usage
    config = create_redis_backup_config_from_env()
    backup_manager = RedisBackupManager(config)
    
    # Create immediate backups
    rdb_metadata = backup_manager.create_rdb_backup()
    aof_metadata = backup_manager.create_aof_backup()
    session_metadata = backup_manager.create_session_backup()
    config_metadata = backup_manager.create_config_backup()
    
    print(f"RDB backup completed: {rdb_metadata.backup_id}")
    print(f"AOF backup completed: {aof_metadata.backup_id}")
    print(f"Session backup completed: {session_metadata.backup_id}")
    print(f"Config backup completed: {config_metadata.backup_id}")
    
    # Schedule automated backups
    backup_manager.schedule_backups()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Redis backup manager stopped")
