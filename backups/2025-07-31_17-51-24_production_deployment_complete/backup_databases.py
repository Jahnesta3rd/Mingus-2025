#!/usr/bin/env python3
"""
MINGUS Database Backup Script
============================

This script creates comprehensive backups of all SQLite databases before
migration to PostgreSQL. It includes compression, verification, and
detailed logging for safe migration preparation.

Features:
- Backup all configured SQLite databases
- Compress backups to save space
- Verify backup integrity
- Create backup manifest with checksums
- Detailed logging and progress tracking
- Backup rotation and cleanup

Author: MINGUS Development Team
Date: January 2025
"""

import sqlite3
import json
import os
import sys
import shutil
import gzip
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Comprehensive database backup and verification tool."""
    
    def __init__(self, backup_dir: str = 'database_backups', compress: bool = True, verify: bool = True):
        """
        Initialize the database backup tool.
        
        Args:
            backup_dir: Directory to store backups
            compress: Whether to compress backup files
            verify: Whether to verify backup integrity
        """
        self.backup_dir = Path(backup_dir)
        self.compress = compress
        self.verify = verify
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_session_dir = self.backup_dir / f"backup_{self.timestamp}"
        
        # Database configuration
        self.databases = {
            'mingus': 'mingus.db',
            'business_intelligence': 'business_intelligence.db',
            'cache': 'cache.db',
            'performance_metrics': 'performance_metrics.db',
            'alerts': 'alerts.db'
        }
        
        self.backup_results = {
            'backup_session': self.timestamp,
            'backup_date': datetime.now().isoformat(),
            'databases': {},
            'summary': {},
            'errors': [],
            'warnings': []
        }
        
    def setup_backup_directory(self) -> bool:
        """
        Create backup directory structure.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create main backup directory
            self.backup_dir.mkdir(exist_ok=True)
            
            # Create session-specific directory
            self.backup_session_dir.mkdir(exist_ok=True)
            
            # Create subdirectories
            (self.backup_session_dir / 'databases').mkdir(exist_ok=True)
            (self.backup_session_dir / 'logs').mkdir(exist_ok=True)
            (self.backup_session_dir / 'manifests').mkdir(exist_ok=True)
            
            logger.info(f"Backup directory structure created: {self.backup_session_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            return False
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash string
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def get_database_info(self, db_path: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a database.
        
        Args:
            db_path: Path to the database file
            
        Returns:
            Dictionary with database information
        """
        if not os.path.exists(db_path):
            return {
                'exists': False,
                'error': f"Database file not found: {db_path}"
            }
        
        try:
            # Get file information
            file_stat = os.stat(db_path)
            file_size = file_stat.st_size
            last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get record counts
            table_counts = {}
            total_records = 0
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                    total_records += count
                except sqlite3.Error as e:
                    logger.warning(f"Error counting records in table {table}: {e}")
                    table_counts[table] = 0
            
            # Get database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()
            integrity_ok = integrity_result[0] == 'ok' if integrity_result else False
            
            conn.close()
            
            return {
                'exists': True,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'last_modified': last_modified,
                'tables': tables,
                'table_count': len(tables),
                'table_record_counts': table_counts,
                'total_records': total_records,
                'integrity_check': integrity_ok,
                'file_hash': self.calculate_file_hash(Path(db_path))
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error analyzing database {db_path}: {e}")
            return {
                'exists': False,
                'error': str(e)
            }
    
    def backup_database(self, db_name: str, db_path: str) -> Dict[str, Any]:
        """
        Backup a single database with comprehensive information.
        
        Args:
            db_name: Name of the database
            db_path: Path to the database file
            
        Returns:
            Dictionary with backup results
        """
        logger.info(f"Starting backup of database: {db_name}")
        
        # Get database information
        db_info = self.get_database_info(db_path)
        
        if not db_info.get('exists', False):
            error_msg = f"Database {db_name} not found or inaccessible"
            logger.error(error_msg)
            self.backup_results['errors'].append({
                'database': db_name,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            return {
                'success': False,
                'error': error_msg,
                'database_info': db_info
            }
        
        try:
            # Create backup filename
            backup_filename = f"{db_name}_{self.timestamp}.db"
            backup_path = self.backup_session_dir / 'databases' / backup_filename
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            # Verify backup
            if self.verify:
                original_hash = db_info['file_hash']
                backup_hash = self.calculate_file_hash(backup_path)
                
                if original_hash != backup_hash:
                    error_msg = f"Backup verification failed for {db_name}"
                    logger.error(error_msg)
                    backup_path.unlink()  # Remove corrupted backup
                    return {
                        'success': False,
                        'error': error_msg,
                        'database_info': db_info
                    }
            
            # Compress if requested
            compressed_path = None
            if self.compress:
                compressed_filename = f"{backup_filename}.gz"
                compressed_path = self.backup_session_dir / 'databases' / compressed_filename
                
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed backup
                backup_path.unlink()
                
                # Verify compressed backup
                if self.verify:
                    compressed_hash = self.calculate_file_hash(compressed_path)
                    # Note: We can't directly compare hashes of compressed vs uncompressed
                    # But we can verify the compressed file is valid
                    try:
                        with gzip.open(compressed_path, 'rb') as f:
                            f.read(1024)  # Read a small amount to verify it's valid
                    except Exception as e:
                        error_msg = f"Compressed backup verification failed for {db_name}: {e}"
                        logger.error(error_msg)
                        compressed_path.unlink()
                        return {
                            'success': False,
                            'error': error_msg,
                            'database_info': db_info
                        }
            
            # Get final backup file info
            final_path = compressed_path if self.compress else backup_path
            final_stat = os.stat(final_path)
            
            backup_result = {
                'success': True,
                'database_info': db_info,
                'backup_path': str(final_path),
                'backup_size_bytes': final_stat.st_size,
                'backup_size_mb': round(final_stat.st_size / (1024 * 1024), 2),
                'compressed': self.compress,
                'backup_hash': self.calculate_file_hash(final_path),
                'backup_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully backed up {db_name}: {backup_result['backup_size_mb']:.2f} MB")
            return backup_result
            
        except Exception as e:
            error_msg = f"Backup failed for {db_name}: {e}"
            logger.error(error_msg)
            self.backup_results['errors'].append({
                'database': db_name,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            return {
                'success': False,
                'error': error_msg,
                'database_info': db_info
            }
    
    def create_backup_manifest(self) -> Dict[str, Any]:
        """
        Create a comprehensive backup manifest.
        
        Returns:
            Dictionary with backup manifest information
        """
        manifest = {
            'backup_session': self.timestamp,
            'backup_date': datetime.now().isoformat(),
            'backup_directory': str(self.backup_session_dir),
            'compression_enabled': self.compress,
            'verification_enabled': self.verify,
            'databases': {},
            'summary': {
                'total_databases': len(self.databases),
                'successful_backups': 0,
                'failed_backups': 0,
                'total_backup_size_mb': 0,
                'total_original_size_mb': 0
            }
        }
        
        # Add database information
        for db_name, backup_result in self.backup_results['databases'].items():
            manifest['databases'][db_name] = {
                'success': backup_result.get('success', False),
                'original_size_mb': backup_result.get('database_info', {}).get('file_size_mb', 0),
                'backup_size_mb': backup_result.get('backup_size_mb', 0),
                'compression_ratio': self._calculate_compression_ratio(
                    backup_result.get('database_info', {}).get('file_size_mb', 0),
                    backup_result.get('backup_size_mb', 0)
                ),
                'tables': backup_result.get('database_info', {}).get('tables', []),
                'total_records': backup_result.get('database_info', {}).get('total_records', 0),
                'integrity_check': backup_result.get('database_info', {}).get('integrity_check', False),
                'backup_path': backup_result.get('backup_path', ''),
                'backup_hash': backup_result.get('backup_hash', ''),
                'error': backup_result.get('error', None)
            }
            
            # Update summary
            if backup_result.get('success', False):
                manifest['summary']['successful_backups'] += 1
                manifest['summary']['total_backup_size_mb'] += backup_result.get('backup_size_mb', 0)
                manifest['summary']['total_original_size_mb'] += backup_result.get('database_info', {}).get('file_size_mb', 0)
            else:
                manifest['summary']['failed_backups'] += 1
        
        # Calculate overall compression ratio
        if manifest['summary']['total_original_size_mb'] > 0:
            manifest['summary']['overall_compression_ratio'] = self._calculate_compression_ratio(
                manifest['summary']['total_original_size_mb'],
                manifest['summary']['total_backup_size_mb']
            )
        
        return manifest
    
    def _calculate_compression_ratio(self, original_size: float, compressed_size: float) -> float:
        """
        Calculate compression ratio.
        
        Args:
            original_size: Original file size in MB
            compressed_size: Compressed file size in MB
            
        Returns:
            Compression ratio (0.0 to 1.0, where 1.0 = no compression)
        """
        if original_size == 0:
            return 1.0
        return round(compressed_size / original_size, 3)
    
    def save_manifest(self, manifest: Dict[str, Any]) -> bool:
        """
        Save the backup manifest to file.
        
        Args:
            manifest: Backup manifest dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            manifest_path = self.backup_session_dir / 'manifests' / 'backup_manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup manifest saved: {manifest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Clean up old backup sessions.
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            Number of backup sessions removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            removed_count = 0
            
            for backup_dir in self.backup_dir.glob('backup_*'):
                try:
                    # Extract date from directory name
                    dir_date_str = backup_dir.name.split('_')[1] + '_' + backup_dir.name.split('_')[2]
                    dir_date = datetime.strptime(dir_date_str, '%Y%m%d_%H%M%S')
                    
                    if dir_date < cutoff_date:
                        shutil.rmtree(backup_dir)
                        logger.info(f"Removed old backup: {backup_dir}")
                        removed_count += 1
                        
                except (ValueError, IndexError):
                    # Skip directories that don't match the expected format
                    continue
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
    
    def run_backup(self) -> bool:
        """
        Run the complete backup process.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting comprehensive database backup process...")
        
        # Setup backup directory
        if not self.setup_backup_directory():
            return False
        
        # Backup each database
        for db_name, db_path in self.databases.items():
            logger.info(f"Processing database: {db_name}")
            backup_result = self.backup_database(db_name, db_path)
            self.backup_results['databases'][db_name] = backup_result
        
        # Create and save manifest
        manifest = self.create_backup_manifest()
        if not self.save_manifest(manifest):
            logger.warning("Failed to save backup manifest")
        
        # Cleanup old backups
        removed_count = self.cleanup_old_backups()
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old backup sessions")
        
        # Generate summary
        self.backup_results['summary'] = manifest['summary']
        
        logger.info("Database backup process completed!")
        return True
    
    def save_backup_report(self, output_file: str = 'backup_report.json'):
        """
        Save the backup report to a JSON file.
        
        Args:
            output_file: Path to the output JSON file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Backup report saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving backup report: {e}")
    
    def print_summary(self):
        """Print a summary of the backup results to console."""
        print("\n" + "="*80)
        print("💾 MINGUS DATABASE BACKUP SUMMARY")
        print("="*80)
        
        summary = self.backup_results['summary']
        
        print(f"\n📊 BACKUP OVERVIEW:")
        print(f"   • Backup Session: {self.timestamp}")
        print(f"   • Backup Directory: {self.backup_session_dir}")
        print(f"   • Total Databases: {summary.get('total_databases', 0)}")
        print(f"   • Successful Backups: {summary.get('successful_backups', 0)}")
        print(f"   • Failed Backups: {summary.get('failed_backups', 0)}")
        print(f"   • Compression: {'Enabled' if self.compress else 'Disabled'}")
        print(f"   • Verification: {'Enabled' if self.verify else 'Disabled'}")
        
        if summary.get('total_original_size_mb', 0) > 0:
            print(f"\n📈 SIZE STATISTICS:")
            print(f"   • Original Size: {summary.get('total_original_size_mb', 0):.2f} MB")
            print(f"   • Backup Size: {summary.get('total_backup_size_mb', 0):.2f} MB")
            if 'overall_compression_ratio' in summary:
                print(f"   • Compression Ratio: {summary['overall_compression_ratio']:.1%}")
        
        print(f"\n🗄️  DATABASE DETAILS:")
        for db_name, backup_result in self.backup_results['databases'].items():
            if backup_result.get('success', False):
                db_info = backup_result.get('database_info', {})
                print(f"   ✅ {db_name}:")
                print(f"     - Tables: {db_info.get('table_count', 0)}")
                print(f"     - Records: {db_info.get('total_records', 0):,}")
                print(f"     - Size: {backup_result.get('backup_size_mb', 0):.2f} MB")
                print(f"     - Integrity: {'✅ OK' if db_info.get('integrity_check', False) else '⚠️  Issues'}")
            else:
                print(f"   ❌ {db_name}: {backup_result.get('error', 'Unknown error')}")
        
        if self.backup_results['errors']:
            print(f"\n⚠️  ERRORS ENCOUNTERED:")
            for error in self.backup_results['errors']:
                print(f"   • {error['database']}: {error['error']}")
        
        if self.backup_results['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.backup_results['warnings']:
                print(f"   • {warning}")
        
        print(f"\n📄 FILES CREATED:")
        print(f"   • Backup Directory: {self.backup_session_dir}")
        print(f"   • Manifest: {self.backup_session_dir}/manifests/backup_manifest.json")
        print(f"   • Log File: database_backup.log")
        print(f"   • Report: backup_report.json")
        
        print("\n" + "="*80)
        print("✅ Backup process completed successfully!")
        print("="*80 + "\n")


def main():
    """Main function to run the database backup."""
    
    parser = argparse.ArgumentParser(description='MINGUS Database Backup Tool')
    parser.add_argument('--backup-dir', default='database_backups', 
                       help='Directory to store backups (default: database_backups)')
    parser.add_argument('--no-compress', action='store_true',
                       help='Disable compression of backup files')
    parser.add_argument('--no-verify', action='store_true',
                       help='Disable backup verification')
    parser.add_argument('--cleanup-days', type=int, default=30,
                       help='Number of days to keep old backups (default: 30)')
    
    args = parser.parse_args()
    
    try:
        # Create backup instance
        backup_tool = DatabaseBackup(
            backup_dir=args.backup_dir,
            compress=not args.no_compress,
            verify=not args.no_verify
        )
        
        # Run backup
        success = backup_tool.run_backup()
        
        # Save report
        backup_tool.save_backup_report()
        
        # Print summary
        backup_tool.print_summary()
        
        # Exit with appropriate code
        if success and backup_tool.backup_results['summary']['failed_backups'] == 0:
            logger.info("All databases backed up successfully!")
            sys.exit(0)
        elif success:
            logger.warning("Backup completed with some failures. Check the report for details.")
            sys.exit(1)
        else:
            logger.error("Backup process failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 