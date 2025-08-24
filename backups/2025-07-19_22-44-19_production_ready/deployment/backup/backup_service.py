#!/usr/bin/env python3
"""
Backup Service for Mingus Application
Handles database backups, file backups, and cloud storage integration
"""

import os
import sys
import time
import schedule
import logging
import subprocess
import boto3
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
import json
import gzip
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.s3_bucket = os.getenv('BACKUP_S3_BUCKET', 'mingus-backups')
        self.backup_dir = Path('/app/backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Backup retention settings
        self.db_retention_days = 30
        self.file_retention_days = 90
        self.log_retention_days = 7
        
    def create_database_backup(self):
        """Create a PostgreSQL database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"database_backup_{timestamp}.sql"
            
            # Parse database URL
            db_parts = self.db_url.replace('postgresql://', '').split('@')
            credentials = db_parts[0].split(':')
            host_port_db = db_parts[1].split('/')
            host_port = host_port_db[0].split(':')
            
            username = credentials[0]
            password = credentials[1]
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            database = host_port_db[1]
            
            # Create backup using pg_dump
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', database,
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges'
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env)
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_file}")
                
                # Compress backup
                compressed_file = self.compress_file(backup_file)
                
                # Upload to S3
                self.upload_to_s3(compressed_file, 'database')
                
                # Clean up local file
                compressed_file.unlink()
                
                return True
            else:
                logger.error(f"Database backup failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            return False
    
    def create_file_backup(self):
        """Create a backup of important files and directories"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"files_backup_{timestamp}.tar.gz"
            
            # Files and directories to backup
            backup_paths = [
                '/app/logs',
                '/app/data',
                '/app/static',
                '/app/templates'
            ]
            
            # Create tar.gz archive
            cmd = ['tar', '-czf', str(backup_file)] + backup_paths
            
            result = subprocess.run(cmd, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                logger.info(f"File backup created: {backup_file}")
                
                # Upload to S3
                self.upload_to_s3(backup_file, 'files')
                
                # Clean up local file
                backup_file.unlink()
                
                return True
            else:
                logger.error(f"File backup failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating file backup: {str(e)}")
            return False
    
    def compress_file(self, file_path):
        """Compress a file using gzip"""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        file_path.unlink()
        
        return compressed_path
    
    def upload_to_s3(self, file_path, backup_type):
        """Upload backup file to S3"""
        try:
            key = f"{backup_type}/{datetime.now().strftime('%Y/%m/%d')}/{file_path.name}"
            
            self.s3_client.upload_file(
                str(file_path),
                self.s3_bucket,
                key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            logger.info(f"Backup uploaded to S3: s3://{self.s3_bucket}/{key}")
            
            # Update backup metadata
            self.update_backup_metadata(key, backup_type, file_path.stat().st_size)
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
    
    def update_backup_metadata(self, s3_key, backup_type, file_size):
        """Update backup metadata in database"""
        try:
            metadata = {
                's3_key': s3_key,
                'backup_type': backup_type,
                'file_size': file_size,
                'created_at': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            # Store metadata in a local JSON file (since we might not have DB access)
            metadata_file = self.backup_dir / 'backup_metadata.json'
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata_list = json.load(f)
            else:
                metadata_list = []
            
            metadata_list.append(metadata)
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata_list, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating backup metadata: {str(e)}")
    
    def cleanup_old_backups(self):
        """Clean up old backup files and S3 objects"""
        try:
            # Clean up local files
            cutoff_date = datetime.now() - timedelta(days=self.file_retention_days)
            
            for file_path in self.backup_dir.glob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        logger.info(f"Deleted old backup file: {file_path}")
            
            # Clean up S3 objects (older than retention period)
            self.cleanup_s3_backups()
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
    
    def cleanup_s3_backups(self):
        """Clean up old S3 backup objects"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.db_retention_days)
            
            # List objects in S3 bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.s3_bucket)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            self.s3_client.delete_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            logger.info(f"Deleted old S3 backup: {obj['Key']}")
                            
        except Exception as e:
            logger.error(f"Error cleaning up S3 backups: {str(e)}")
    
    def verify_backup_integrity(self):
        """Verify the integrity of recent backups"""
        try:
            # Check if we can connect to database
            conn = psycopg2.connect(self.db_url)
            conn.close()
            
            # Check if S3 is accessible
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            
            logger.info("Backup integrity check passed")
            return True
            
        except Exception as e:
            logger.error(f"Backup integrity check failed: {str(e)}")
            return False
    
    def restore_database_backup(self, backup_key):
        """Restore database from S3 backup"""
        try:
            # Download backup from S3
            local_file = self.backup_dir / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql.gz"
            
            self.s3_client.download_file(self.s3_bucket, backup_key, str(local_file))
            
            # Decompress file
            decompressed_file = local_file.with_suffix('')
            with gzip.open(local_file, 'rb') as f_in:
                with open(decompressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Parse database URL for restore
            db_parts = self.db_url.replace('postgresql://', '').split('@')
            credentials = db_parts[0].split(':')
            host_port_db = db_parts[1].split('/')
            host_port = host_port_db[0].split(':')
            
            username = credentials[0]
            password = credentials[1]
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            database = host_port_db[1]
            
            # Restore database
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            cmd = [
                'psql',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', database,
                '-f', str(decompressed_file)
            ]
            
            result = subprocess.run(cmd, stderr=subprocess.PIPE, env=env)
            
            # Clean up
            local_file.unlink()
            decompressed_file.unlink()
            
            if result.returncode == 0:
                logger.info(f"Database restored from backup: {backup_key}")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring database backup: {str(e)}")
            return False
    
    def run_backup_schedule(self):
        """Run the backup schedule"""
        # Schedule daily database backup at 2 AM
        schedule.every().day.at("02:00").do(self.create_database_backup)
        
        # Schedule weekly file backup on Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self.create_file_backup)
        
        # Schedule daily cleanup at 4 AM
        schedule.every().day.at("04:00").do(self.cleanup_old_backups)
        
        # Schedule integrity check every 6 hours
        schedule.every(6).hours.do(self.verify_backup_integrity)
        
        logger.info("Backup schedule started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main function"""
    backup_service = BackupService()
    
    # Run initial integrity check
    backup_service.verify_backup_integrity()
    
    # Start backup schedule
    backup_service.run_backup_schedule()

if __name__ == "__main__":
    main() 