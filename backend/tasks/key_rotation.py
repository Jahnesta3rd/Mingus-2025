"""
Key Rotation Tasks
==================
Celery tasks for automated encryption key rotation, data migration,
and encryption monitoring for the Mingus Flask application.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from celery import current_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from backend.security.key_manager import get_key_manager, KeyType
from backend.security.encryption_service import get_encryption_service
from backend.security.crypto_config import get_crypto_config

logger = logging.getLogger(__name__)

class KeyRotationTasks:
    """
    Celery tasks for encryption key rotation and management
    """
    
    def __init__(self):
        self.key_manager = get_key_manager()
        self.encryption_service = get_encryption_service()
        self.config = get_crypto_config()
    
    def rotate_keys_scheduled(self) -> Dict[str, Any]:
        """
        Scheduled task to rotate encryption keys based on policies
        
        Returns:
            Dictionary with rotation results
        """
        try:
            logger.info("Starting scheduled key rotation")
            rotation_results = {
                'rotated_keys': [],
                'failed_rotations': [],
                'total_processed': 0,
                'start_time': datetime.utcnow().isoformat()
            }
            
            # Get all key types and check if rotation is needed
            for key_type in KeyType:
                try:
                    policy = self.config.get_rotation_policy(key_type)
                    if not policy.auto_rotation:
                        logger.info(f"Auto-rotation disabled for {key_type.value}")
                        continue
                    
                    # Check if rotation is needed
                    current_key = self.key_manager.get_active_key(key_type)
                    if current_key:
                        days_until_expiry = (current_key.expires_at - datetime.utcnow()).days
                        if days_until_expiry <= policy.grace_period_days:
                            logger.info(f"Rotating {key_type.value} key (expires in {days_until_expiry} days)")
                            
                            # Perform key rotation
                            new_key = self.key_manager.rotate_key(key_type, force=False)
                            
                            rotation_results['rotated_keys'].append({
                                'key_type': key_type.value,
                                'old_key_id': current_key.key_id,
                                'new_key_id': new_key.key_id,
                                'rotation_reason': f"Expires in {days_until_expiry} days"
                            })
                            
                            # Schedule data re-encryption for this key type
                            self._schedule_data_reencryption.delay(key_type.value, current_key.key_id)
                            
                        else:
                            logger.info(f"Key rotation not needed for {key_type.value} (expires in {days_until_expiry} days)")
                    else:
                        logger.warning(f"No active key found for {key_type.value}")
                
                except Exception as e:
                    logger.error(f"Failed to rotate {key_type.value} key: {e}")
                    rotation_results['failed_rotations'].append({
                        'key_type': key_type.value,
                        'error': str(e)
                    })
                
                rotation_results['total_processed'] += 1
            
            rotation_results['end_time'] = datetime.utcnow().isoformat()
            rotation_results['success'] = len(rotation_results['failed_rotations']) == 0
            
            logger.info(f"Key rotation completed: {len(rotation_results['rotated_keys'])} keys rotated, "
                       f"{len(rotation_results['failed_rotations'])} failed")
            
            return rotation_results
        
        except Exception as e:
            logger.error(f"Scheduled key rotation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'start_time': datetime.utcnow().isoformat(),
                'end_time': datetime.utcnow().isoformat()
            }
    
    def rotate_key_manual(self, key_type: str, force: bool = False) -> Dict[str, Any]:
        """
        Manual key rotation task
        
        Args:
            key_type: Type of key to rotate
            force: Force rotation even if not needed
            
        Returns:
            Dictionary with rotation results
        """
        try:
            logger.info(f"Starting manual key rotation for {key_type}")
            
            # Validate key type
            try:
                key_type_enum = KeyType(key_type)
            except ValueError:
                return {
                    'success': False,
                    'error': f"Invalid key type: {key_type}"
                }
            
            # Perform rotation
            current_key = self.key_manager.get_active_key(key_type_enum)
            new_key = self.key_manager.rotate_key(key_type_enum, force=force)
            
            result = {
                'success': True,
                'key_type': key_type,
                'old_key_id': current_key.key_id if current_key else None,
                'new_key_id': new_key.key_id,
                'rotation_time': datetime.utcnow().isoformat(),
                'forced': force
            }
            
            # Schedule data re-encryption if there was a previous key
            if current_key:
                self._schedule_data_reencryption.delay(key_type, current_key.key_id)
            
            logger.info(f"Manual key rotation completed for {key_type}")
            return result
        
        except Exception as e:
            logger.error(f"Manual key rotation failed for {key_type}: {e}")
            return {
                'success': False,
                'error': str(e),
                'key_type': key_type
            }
    
    def reencrypt_data_with_new_key(self, key_type: str, old_key_id: str, 
                                   batch_size: int = 1000) -> Dict[str, Any]:
        """
        Re-encrypt data that was encrypted with the old key using the new key
        
        Args:
            key_type: Type of encryption key
            old_key_id: ID of the old key
            batch_size: Number of records to process per batch
            
        Returns:
            Dictionary with re-encryption results
        """
        try:
            logger.info(f"Starting data re-encryption for {key_type} key {old_key_id}")
            
            # Get the old and new keys
            old_key = self.key_manager.get_key(old_key_id)
            if not old_key:
                return {
                    'success': False,
                    'error': f"Old key {old_key_id} not found"
                }
            
            key_type_enum = KeyType(key_type)
            new_key = self.key_manager.get_active_key(key_type_enum)
            if not new_key:
                return {
                    'success': False,
                    'error': f"No active key found for {key_type}"
                }
            
            # Get database connection
            db_engine = self._get_database_engine()
            SessionLocal = sessionmaker(bind=db_engine)
            db_session = SessionLocal()
            
            try:
                reencryption_results = {
                    'key_type': key_type,
                    'old_key_id': old_key_id,
                    'new_key_id': new_key.key_id,
                    'total_records': 0,
                    'processed_records': 0,
                    'failed_records': 0,
                    'start_time': datetime.utcnow().isoformat(),
                    'errors': []
                }
                
                # Get tables that contain encrypted data for this key type
                tables_to_process = self._get_tables_for_key_type(key_type_enum)
                
                for table_name, encrypted_columns in tables_to_process.items():
                    logger.info(f"Processing table {table_name} with columns {encrypted_columns}")
                    
                    # Get total count of records to process
                    count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = db_session.execute(count_query).scalar()
                    reencryption_results['total_records'] += total_count
                    
                    # Process in batches
                    offset = 0
                    while offset < total_count:
                        try:
                            # Get batch of records
                            batch_query = text(f"""
                                SELECT id, {', '.join(encrypted_columns)} 
                                FROM {table_name} 
                                ORDER BY id 
                                LIMIT {batch_size} OFFSET {offset}
                            """)
                            
                            batch_results = db_session.execute(batch_query)
                            
                            for row in batch_results:
                                try:
                                    # Re-encrypt each encrypted column
                                    for column_name in encrypted_columns:
                                        if row[column_name]:
                                            # Decrypt with old key
                                            decrypted_value = self._decrypt_with_key(
                                                row[column_name], old_key
                                            )
                                            
                                            if decrypted_value is not None:
                                                # Re-encrypt with new key
                                                reencrypted_value = self.encryption_service.encrypt_field(
                                                    decrypted_value, key_type_enum
                                                )
                                                
                                                # Update the record
                                                update_query = text(f"""
                                                    UPDATE {table_name} 
                                                    SET {column_name} = :encrypted_value 
                                                    WHERE id = :record_id
                                                """)
                                                
                                                db_session.execute(update_query, {
                                                    'encrypted_value': reencrypted_value,
                                                    'record_id': row.id
                                                })
                                                
                                                reencryption_results['processed_records'] += 1
                                
                                except Exception as e:
                                    logger.error(f"Failed to re-encrypt record {row.id} in {table_name}: {e}")
                                    reencryption_results['failed_records'] += 1
                                    reencryption_results['errors'].append({
                                        'table': table_name,
                                        'record_id': row.id,
                                        'error': str(e)
                                    })
                            
                            # Commit batch
                            db_session.commit()
                            
                            # Update progress
                            offset += batch_size
                            
                            # Update Celery task progress
                            if current_task:
                                progress = min(100, (offset / total_count) * 100)
                                current_task.update_state(
                                    state='PROGRESS',
                                    meta={'progress': progress, 'offset': offset, 'total': total_count}
                                )
                            
                            logger.info(f"Processed batch: {offset}/{total_count} records")
                            
                        except Exception as e:
                            logger.error(f"Failed to process batch for {table_name}: {e}")
                            db_session.rollback()
                            reencryption_results['errors'].append({
                                'table': table_name,
                                'error': f"Batch processing failed: {str(e)}"
                            })
                
                reencryption_results['end_time'] = datetime.utcnow().isoformat()
                reencryption_results['success'] = reencryption_results['failed_records'] == 0
                
                logger.info(f"Data re-encryption completed: {reencryption_results['processed_records']} records processed, "
                           f"{reencryption_results['failed_records']} failed")
                
                return reencryption_results
            
            finally:
                db_session.close()
        
        except Exception as e:
            logger.error(f"Data re-encryption failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'key_type': key_type,
                'old_key_id': old_key_id
            }
    
    def cleanup_expired_keys(self) -> Dict[str, Any]:
        """
        Clean up expired encryption keys
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            logger.info("Starting expired key cleanup")
            
            # Get expired keys count
            expired_keys_before = len([
                key for key in self.key_manager.keys.values()
                if key.status.value == 'expired'
            ])
            
            # Clean up expired keys
            cleaned_count = self.key_manager.cleanup_expired_keys()
            
            # Get expired keys count after cleanup
            expired_keys_after = len([
                key for key in self.key_manager.keys.values()
                if key.status.value == 'expired'
            ])
            
            result = {
                'success': True,
                'keys_cleaned': cleaned_count,
                'expired_keys_before': expired_keys_before,
                'expired_keys_after': expired_keys_after,
                'cleanup_time': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Expired key cleanup completed: {cleaned_count} keys cleaned")
            return result
        
        except Exception as e:
            logger.error(f"Expired key cleanup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_encryption_status_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive encryption status report
        
        Returns:
            Dictionary with encryption status information
        """
        try:
            logger.info("Generating encryption status report")
            
            # Get key statistics
            key_stats = self.key_manager.get_key_statistics()
            
            # Get encryption service stats
            encryption_stats = self.encryption_service.get_encryption_stats()
            
            # Get database encryption status
            db_encryption_status = self._get_database_encryption_status()
            
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'key_management': key_stats,
                'encryption_service': encryption_stats,
                'database_encryption': db_encryption_status,
                'recommendations': self._generate_encryption_recommendations(key_stats, db_encryption_status)
            }
            
            logger.info("Encryption status report generated successfully")
            return report
        
        except Exception as e:
            logger.error(f"Failed to generate encryption status report: {e}")
            return {
                'success': False,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _get_database_engine(self):
        """Get database engine for direct SQL operations"""
        # This would typically come from your Flask app configuration
        database_url = "postgresql://user:password@localhost/mingus_db"
        return create_engine(database_url)
    
    def _get_tables_for_key_type(self, key_type: KeyType) -> Dict[str, List[str]]:
        """Get tables and encrypted columns for a specific key type"""
        if key_type == KeyType.FINANCIAL_DATA:
            return {
                'users': [
                    'encrypted_monthly_income', 'encrypted_current_savings', 
                    'encrypted_current_debt', 'encrypted_emergency_fund'
                ],
                'encrypted_financial_profiles': [
                    'monthly_income', 'current_savings', 'current_debt', 'emergency_fund'
                ],
                'salary_data': ['amount', 'bonus_amount', 'overtime_amount'],
                'manual_transactions': ['amount', 'balance']
            }
        elif key_type == KeyType.PII:
            return {
                'users': [
                    'encrypted_ssn', 'encrypted_tax_id', 'encrypted_address', 
                    'encrypted_birth_date'
                ],
                'user_profiles': ['ssn', 'tax_id', 'address', 'birth_date']
            }
        elif key_type == KeyType.SESSION:
            return {
                'sessions': ['session_data', 'user_data'],
                'auth_tokens': ['token_data', 'refresh_token']
            }
        else:
            return {}
    
    def _decrypt_with_key(self, encrypted_value: str, key) -> Any:
        """Decrypt value using a specific key (for re-encryption)"""
        try:
            # This is a simplified version - you'd need to implement proper decryption
            # with the specific key's algorithm and parameters
            return self.encryption_service.decrypt_field(encrypted_value, key.key_type)
        except Exception as e:
            logger.error(f"Failed to decrypt value with key {key.key_id}: {e}")
            return None
    
    def _get_database_encryption_status(self) -> Dict[str, Any]:
        """Get database encryption status"""
        try:
            # This would query your database to check encryption status
            # For now, return a placeholder
            return {
                'encrypted_tables': ['users', 'encrypted_financial_profiles', 'salary_data'],
                'total_encrypted_records': 0,  # Would be calculated from actual data
                'encryption_coverage': 'partial',  # partial, full, none
                'last_encryption_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get database encryption status: {e}")
            return {'error': str(e)}
    
    def _generate_encryption_recommendations(self, key_stats: Dict[str, Any], 
                                          db_status: Dict[str, Any]) -> List[str]:
        """Generate encryption recommendations based on current status"""
        recommendations = []
        
        # Check key rotation needs
        for rotation_info in key_stats.get('rotation_needed', []):
            recommendations.append(
                f"Rotate {rotation_info['key_type']} key {rotation_info['key_id']} "
                f"(expires in {rotation_info['days_until_expiry']} days)"
            )
        
        # Check database encryption coverage
        if db_status.get('encryption_coverage') == 'none':
            recommendations.append("Enable database encryption for sensitive tables")
        elif db_status.get('encryption_coverage') == 'partial':
            recommendations.append("Complete database encryption coverage")
        
        # Check for expired keys
        expired_count = key_stats.get('by_status', {}).get('expired', 0)
        if expired_count > 0:
            recommendations.append(f"Clean up {expired_count} expired encryption keys")
        
        if not recommendations:
            recommendations.append("Encryption system is healthy and up to date")
        
        return recommendations

# Create task instances
key_rotation_tasks = KeyRotationTasks()

# Celery task definitions
def rotate_keys_scheduled():
    """Celery task wrapper for scheduled key rotation"""
    return key_rotation_tasks.rotate_keys_scheduled()

def rotate_key_manual(key_type: str, force: bool = False):
    """Celery task wrapper for manual key rotation"""
    return key_rotation_tasks.rotate_key_manual(key_type, force)

def reencrypt_data_with_new_key(key_type: str, old_key_id: str, batch_size: int = 1000):
    """Celery task wrapper for data re-encryption"""
    return key_rotation_tasks.reencrypt_data_with_new_key(key_type, old_key_id, batch_size)

def cleanup_expired_keys():
    """Celery task wrapper for expired key cleanup"""
    return key_rotation_tasks.cleanup_expired_keys()

def get_encryption_status_report():
    """Celery task wrapper for encryption status report"""
    return key_rotation_tasks.get_encryption_status_report()

# Task scheduling configuration
TASK_SCHEDULE = {
    'rotate_keys_scheduled': {
        'task': 'backend.tasks.key_rotation.rotate_keys_scheduled',
        'schedule': 86400.0,  # Daily
        'options': {'queue': 'encryption'}
    },
    'cleanup_expired_keys': {
        'task': 'backend.tasks.key_rotation.cleanup_expired_keys',
        'schedule': 604800.0,  # Weekly
        'options': {'queue': 'encryption'}
    },
    'get_encryption_status_report': {
        'task': 'backend.tasks.key_rotation.get_encryption_status_report',
        'schedule': 3600.0,  # Hourly
        'options': {'queue': 'monitoring'}
    }
}
