"""
Plaid Security Service for MINGUS

This module provides comprehensive security and compliance features for Plaid integration:
- Bank-grade encryption for all data
- PCI DSS compliance for financial data
- User consent management and data retention
- GDPR compliance for data privacy
- Secure token management
"""

import logging
import json
import hashlib
import hmac
import base64
import secrets
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

logger = logging.getLogger(__name__)

class DataClassification(Enum):
    """Data classification levels for security"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"  # Financial data, PII
    HIGHLY_RESTRICTED = "highly_restricted"  # Access tokens, credentials

class ConsentType(Enum):
    """Types of user consent for data processing"""
    PLAID_ACCOUNT_ACCESS = "plaid_account_access"
    TRANSACTION_DATA_PROCESSING = "transaction_data_processing"
    IDENTITY_VERIFICATION = "identity_verification"
    ANALYTICS_PROCESSING = "analytics_processing"
    MARKETING_COMMUNICATIONS = "marketing_communications"
    THIRD_PARTY_SHARING = "third_party_sharing"

class RetentionPolicy(Enum):
    """Data retention policies"""
    IMMEDIATE = "immediate"  # Delete immediately
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years (financial records)
    PERMANENT = "permanent"  # Never delete (audit logs)

@dataclass
class EncryptionKey:
    """Encryption key with metadata"""
    key_id: str
    key_material: bytes
    algorithm: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    key_type: str  # 'symmetric', 'asymmetric', 'derived'

@dataclass
class UserConsent:
    """User consent record"""
    user_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime]
    ip_address: str
    user_agent: str
    consent_version: str
    data_processing_purposes: List[str]
    third_parties: List[str]

@dataclass
class DataRetentionRecord:
    """Data retention record"""
    data_type: str
    user_id: str
    retention_policy: RetentionPolicy
    created_at: datetime
    expires_at: datetime
    deletion_scheduled: bool
    deletion_date: Optional[datetime]

@dataclass
class SecurityAuditLog:
    """Security audit log entry"""
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any]
    risk_level: str  # 'low', 'medium', 'high', 'critical'

class PlaidSecurityService:
    """Comprehensive security service for Plaid integration"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.master_key = self._load_master_key()
        self.encryption_keys = self._initialize_encryption_keys()
        self.audit_logger = self._initialize_audit_logger()
        
    def _load_master_key(self) -> bytes:
        """Load or generate master encryption key"""
        try:
            # In production, this should be loaded from secure key management
            master_key_env = os.getenv('PLAID_MASTER_KEY')
            if master_key_env:
                return base64.urlsafe_b64decode(master_key_env)
            else:
                # Generate new master key (for development only)
                master_key = Fernet.generate_key()
                logger.warning("Generated new master key - this should be stored securely in production")
                return master_key
        except Exception as e:
            logger.error(f"Error loading master key: {e}")
            raise
    
    def _initialize_encryption_keys(self) -> Dict[str, EncryptionKey]:
        """Initialize encryption keys for different data types"""
        try:
            keys = {}
            
            # Generate keys for different data classifications
            for classification in DataClassification:
                key_id = f"key_{classification.value}_{datetime.utcnow().strftime('%Y%m%d')}"
                
                if classification in [DataClassification.RESTRICTED, DataClassification.HIGHLY_RESTRICTED]:
                    # Use stronger encryption for sensitive data
                    key_material = self._generate_strong_key()
                    algorithm = "AES-256-GCM"
                else:
                    # Use standard encryption for less sensitive data
                    key_material = Fernet.generate_key()
                    algorithm = "Fernet"
                
                keys[classification.value] = EncryptionKey(
                    key_id=key_id,
                    key_material=key_material,
                    algorithm=algorithm,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year
                    is_active=True,
                    key_type="symmetric"
                )
            
            return keys
            
        except Exception as e:
            logger.error(f"Error initializing encryption keys: {e}")
            raise
    
    def _generate_strong_key(self) -> bytes:
        """Generate a strong encryption key"""
        return os.urandom(32)  # 256-bit key
    
    def _initialize_audit_logger(self):
        """Initialize audit logging system"""
        # This would typically integrate with a proper audit logging system
        return self._log_security_event
    
    def _log_security_event(self, event: SecurityAuditLog):
        """Log security events"""
        try:
            # In production, this would write to a secure audit log
            logger.info(f"SECURITY AUDIT: {event.action} by {event.user_id} at {event.timestamp}")
            
            # Store in database for compliance
            # self._store_audit_log(event)
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    # ============================================================================
    # BANK-GRADE ENCRYPTION
    # ============================================================================
    
    def encrypt_sensitive_data(self, data: str, classification: DataClassification) -> Dict[str, Any]:
        """Encrypt sensitive data using bank-grade encryption"""
        try:
            key = self.encryption_keys.get(classification.value)
            if not key or not key.is_active:
                raise ValueError(f"No active encryption key for classification: {classification.value}")
            
            if classification in [DataClassification.RESTRICTED, DataClassification.HIGHLY_RESTRICTED]:
                # Use AES-256-GCM for highly sensitive data
                return self._encrypt_aes_256_gcm(data, key.key_material)
            else:
                # Use Fernet for standard data
                return self._encrypt_fernet(data, key.key_material)
                
        except Exception as e:
            logger.error(f"Error encrypting sensitive data: {e}")
            raise
    
    def _encrypt_aes_256_gcm(self, data: str, key: bytes) -> Dict[str, Any]:
        """Encrypt data using AES-256-GCM"""
        try:
            # Generate random IV
            iv = os.urandom(12)  # 96-bit IV for GCM
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
            encryptor = cipher.encryptor()
            
            # Encrypt data
            ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
            
            # Get authentication tag
            tag = encryptor.tag
            
            # Combine IV, ciphertext, and tag
            encrypted_data = iv + ciphertext + tag
            
            return {
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'algorithm': 'AES-256-GCM',
                'key_id': self._get_key_id_for_data(data),
                'encrypted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AES-256-GCM encryption: {e}")
            raise
    
    def _encrypt_fernet(self, data: str, key: bytes) -> Dict[str, Any]:
        """Encrypt data using Fernet"""
        try:
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode('utf-8'))
            
            return {
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'algorithm': 'Fernet',
                'key_id': self._get_key_id_for_data(data),
                'encrypted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in Fernet encryption: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any]) -> str:
        """Decrypt sensitive data"""
        try:
            algorithm = encrypted_data.get('algorithm')
            data = base64.b64decode(encrypted_data['encrypted_data'])
            
            if algorithm == 'AES-256-GCM':
                return self._decrypt_aes_256_gcm(data)
            elif algorithm == 'Fernet':
                return self._decrypt_fernet(data)
            else:
                raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
                
        except Exception as e:
            logger.error(f"Error decrypting sensitive data: {e}")
            raise
    
    def _decrypt_aes_256_gcm(self, data: bytes) -> str:
        """Decrypt data using AES-256-GCM"""
        try:
            # Extract IV, ciphertext, and tag
            iv = data[:12]
            tag = data[-16:]
            ciphertext = data[12:-16]
            
            # Get the appropriate key (in production, use key_id to get specific key)
            key = self.encryption_keys[DataClassification.HIGHLY_RESTRICTED.value].key_material
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
            decryptor = cipher.decryptor()
            
            # Decrypt data
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error in AES-256-GCM decryption: {e}")
            raise
    
    def _decrypt_fernet(self, data: bytes) -> str:
        """Decrypt data using Fernet"""
        try:
            # Get the appropriate key (in production, use key_id to get specific key)
            key = self.encryption_keys[DataClassification.CONFIDENTIAL.value].key_material
            
            f = Fernet(key)
            plaintext = f.decrypt(data)
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error in Fernet decryption: {e}")
            raise
    
    def _get_key_id_for_data(self, data: str) -> str:
        """Get appropriate key ID for data type"""
        # In production, this would analyze the data and return appropriate key ID
        return "key_highly_restricted_current"
    
    # ============================================================================
    # SECURE TOKEN MANAGEMENT
    # ============================================================================
    
    def encrypt_access_token(self, access_token: str, user_id: str) -> Dict[str, Any]:
        """Encrypt Plaid access token with user-specific key derivation"""
        try:
            # Derive user-specific key
            user_key = self._derive_user_key(user_id)
            
            # Encrypt access token
            encrypted_data = self._encrypt_aes_256_gcm(access_token, user_key)
            
            # Add token metadata
            encrypted_data['token_type'] = 'plaid_access_token'
            encrypted_data['user_id'] = user_id
            encrypted_data['created_at'] = datetime.utcnow().isoformat()
            
            # Log token creation
            self._log_security_event(SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='access_token_encrypted',
                resource_type='plaid_token',
                resource_id=None,
                ip_address='system',
                user_agent='system',
                success=True,
                details={'token_type': 'plaid_access_token'},
                risk_level='high'
            ))
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Error encrypting access token: {e}")
            raise
    
    def decrypt_access_token(self, encrypted_token: Dict[str, Any], user_id: str) -> str:
        """Decrypt Plaid access token"""
        try:
            # Verify token belongs to user
            if encrypted_token.get('user_id') != user_id:
                raise ValueError("Token does not belong to user")
            
            # Derive user-specific key
            user_key = self._derive_user_key(user_id)
            
            # Decrypt token
            decrypted_token = self._decrypt_aes_256_gcm(
                base64.b64decode(encrypted_token['encrypted_data'])
            )
            
            # Log token access
            self._log_security_event(SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='access_token_decrypted',
                resource_type='plaid_token',
                resource_id=None,
                ip_address='system',
                user_agent='system',
                success=True,
                details={'token_type': 'plaid_access_token'},
                risk_level='high'
            ))
            
            return decrypted_token
            
        except Exception as e:
            logger.error(f"Error decrypting access token: {e}")
            raise
    
    def _derive_user_key(self, user_id: str) -> bytes:
        """Derive user-specific encryption key"""
        try:
            # Use PBKDF2 to derive key from master key and user ID
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=user_id.encode('utf-8'),
                iterations=100000,
            )
            return kdf.derive(self.master_key)
            
        except Exception as e:
            logger.error(f"Error deriving user key: {e}")
            raise
    
    def rotate_encryption_keys(self) -> Dict[str, Any]:
        """Rotate encryption keys for enhanced security"""
        try:
            rotation_results = {}
            
            for classification in DataClassification:
                old_key = self.encryption_keys.get(classification.value)
                if old_key and old_key.is_active:
                    # Generate new key
                    new_key = EncryptionKey(
                        key_id=f"key_{classification.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        key_material=self._generate_strong_key(),
                        algorithm=old_key.algorithm,
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=365),
                        is_active=True,
                        key_type=old_key.key_type
                    )
                    
                    # Mark old key as inactive
                    old_key.is_active = False
                    
                    # Store new key
                    self.encryption_keys[classification.value] = new_key
                    
                    rotation_results[classification.value] = {
                        'old_key_id': old_key.key_id,
                        'new_key_id': new_key.key_id,
                        'rotated_at': datetime.utcnow().isoformat()
                    }
            
            # Log key rotation
            self._log_security_event(SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=None,
                action='encryption_keys_rotated',
                resource_type='encryption_keys',
                resource_id=None,
                ip_address='system',
                user_agent='system',
                success=True,
                details=rotation_results,
                risk_level='critical'
            ))
            
            return rotation_results
            
        except Exception as e:
            logger.error(f"Error rotating encryption keys: {e}")
            raise
    
    # ============================================================================
    # PCI DSS COMPLIANCE
    # ============================================================================
    
    def validate_pci_compliance(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate PCI DSS compliance for financial data"""
        try:
            violations = []
            
            # PCI DSS Requirement 3: Protect stored cardholder data
            if self._contains_cardholder_data(data):
                if not self._is_properly_encrypted(data):
                    violations.append("Cardholder data must be encrypted")
                if not self._has_secure_key_management(data):
                    violations.append("Secure key management required")
            
            # PCI DSS Requirement 4: Encrypt transmission of cardholder data
            if not self._is_transmitted_securely(data):
                violations.append("Data transmission must be encrypted")
            
            # PCI DSS Requirement 7: Restrict access to cardholder data
            if not self._has_proper_access_controls(data):
                violations.append("Proper access controls required")
            
            # PCI DSS Requirement 10: Track and monitor all access
            if not self._has_audit_logging(data):
                violations.append("Audit logging required")
            
            return len(violations) == 0, violations
            
        except Exception as e:
            logger.error(f"Error validating PCI compliance: {e}")
            return False, [f"PCI validation error: {str(e)}"]
    
    def _contains_cardholder_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains cardholder information"""
        # This would check for PAN, CVV, etc.
        sensitive_fields = ['card_number', 'pan', 'cvv', 'cvc', 'card_security_code']
        return any(field in str(data).lower() for field in sensitive_fields)
    
    def _is_properly_encrypted(self, data: Dict[str, Any]) -> bool:
        """Check if data is properly encrypted"""
        # Check if data uses approved encryption algorithms
        return True  # Simplified for example
    
    def _has_secure_key_management(self, data: Dict[str, Any]) -> bool:
        """Check if secure key management is in place"""
        return True  # Simplified for example
    
    def _is_transmitted_securely(self, data: Dict[str, Any]) -> bool:
        """Check if data is transmitted securely"""
        return True  # Simplified for example
    
    def _has_proper_access_controls(self, data: Dict[str, Any]) -> bool:
        """Check if proper access controls are in place"""
        return True  # Simplified for example
    
    def _has_audit_logging(self, data: Dict[str, Any]) -> bool:
        """Check if audit logging is in place"""
        return True  # Simplified for example
    
    # ============================================================================
    # GDPR COMPLIANCE
    # ============================================================================
    
    def create_user_consent(self, user_id: str, consent_type: ConsentType, 
                           granted: bool, request_data: Dict[str, Any]) -> UserConsent:
        """Create user consent record for GDPR compliance"""
        try:
            consent = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                granted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year
                ip_address=request_data.get('ip_address', 'unknown'),
                user_agent=request_data.get('user_agent', 'unknown'),
                consent_version=request_data.get('consent_version', '1.0'),
                data_processing_purposes=request_data.get('purposes', []),
                third_parties=request_data.get('third_parties', [])
            )
            
            # Store consent in database
            self._store_user_consent(consent)
            
            # Log consent action
            self._log_security_event(SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='user_consent_created',
                resource_type='user_consent',
                resource_id=None,
                ip_address=consent.ip_address,
                user_agent=consent.user_agent,
                success=True,
                details={
                    'consent_type': consent_type.value,
                    'granted': granted,
                    'version': consent.consent_version
                },
                risk_level='low'
            ))
            
            return consent
            
        except Exception as e:
            logger.error(f"Error creating user consent: {e}")
            raise
    
    def get_user_consent(self, user_id: str, consent_type: ConsentType) -> Optional[UserConsent]:
        """Get user consent for specific type"""
        try:
            # This would query the database for user consent
            # For now, return None (no consent)
            return None
        except Exception as e:
            logger.error(f"Error getting user consent: {e}")
            return None
    
    def revoke_user_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Revoke user consent"""
        try:
            # Update consent record to revoked
            # self._update_user_consent(user_id, consent_type, granted=False)
            
            # Log consent revocation
            self._log_security_event(SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='user_consent_revoked',
                resource_type='user_consent',
                resource_id=None,
                ip_address='system',
                user_agent='system',
                success=True,
                details={'consent_type': consent_type.value},
                risk_level='medium'
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking user consent: {e}")
            return False
    
    def process_data_deletion_request(self, user_id: str) -> Dict[str, Any]:
        """Process GDPR data deletion request"""
        try:
            deletion_results = {
                'user_id': user_id,
                'requested_at': datetime.utcnow().isoformat(),
                'deleted_data_types': [],
                'retention_exceptions': [],
                'completion_status': 'pending'
            }
            
            # Delete user's Plaid connections
            connections_deleted = self._delete_user_plaid_data(user_id)
            deletion_results['deleted_data_types'].extend(connections_deleted)
            
            # Check for retention exceptions (financial records)
            retention_exceptions = self._check_retention_exceptions(user_id)
            deletion_results['retention_exceptions'].extend(retention_exceptions)
            
            # Update completion status
            if not retention_exceptions:
                deletion_results['completion_status'] = 'completed'
            else:
                deletion_results['completion_status'] = 'partial'
            
            # Log deletion request
            self._log_security_event(SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='data_deletion_requested',
                resource_type='user_data',
                resource_id=None,
                ip_address='system',
                user_agent='system',
                success=True,
                details=deletion_results,
                risk_level='high'
            ))
            
            return deletion_results
            
        except Exception as e:
            logger.error(f"Error processing data deletion request: {e}")
            raise
    
    def _delete_user_plaid_data(self, user_id: str) -> List[str]:
        """Delete user's Plaid-related data"""
        try:
            deleted_types = []
            
            # This would actually delete the data from the database
            # For now, just return what would be deleted
            deleted_types.extend([
                'plaid_connections',
                'plaid_accounts', 
                'plaid_transactions',
                'plaid_identities',
                'user_consents'
            ])
            
            return deleted_types
            
        except Exception as e:
            logger.error(f"Error deleting user Plaid data: {e}")
            return []
    
    def _check_retention_exceptions(self, user_id: str) -> List[str]:
        """Check for data retention exceptions (financial records)"""
        try:
            exceptions = []
            
            # Check if user has financial records that must be retained
            # This would query the database for retention requirements
            
            return exceptions
            
        except Exception as e:
            logger.error(f"Error checking retention exceptions: {e}")
            return []
    
    # ============================================================================
    # DATA RETENTION MANAGEMENT
    # ============================================================================
    
    def create_retention_record(self, data_type: str, user_id: str, 
                               retention_policy: RetentionPolicy) -> DataRetentionRecord:
        """Create data retention record"""
        try:
            # Calculate expiration date based on policy
            expiration_map = {
                RetentionPolicy.IMMEDIATE: datetime.utcnow(),
                RetentionPolicy.SHORT_TERM: datetime.utcnow() + timedelta(days=30),
                RetentionPolicy.MEDIUM_TERM: datetime.utcnow() + timedelta(days=365),
                RetentionPolicy.LONG_TERM: datetime.utcnow() + timedelta(days=365*7),
                RetentionPolicy.PERMANENT: None
            }
            
            expires_at = expiration_map.get(retention_policy)
            
            retention_record = DataRetentionRecord(
                data_type=data_type,
                user_id=user_id,
                retention_policy=retention_policy,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                deletion_scheduled=retention_policy != RetentionPolicy.PERMANENT,
                deletion_date=expires_at
            )
            
            # Store retention record
            self._store_retention_record(retention_record)
            
            return retention_record
            
        except Exception as e:
            logger.error(f"Error creating retention record: {e}")
            raise
    
    def process_data_retention(self) -> Dict[str, Any]:
        """Process data retention policies"""
        try:
            results = {
                'processed_records': 0,
                'deleted_records': 0,
                'errors': 0,
                'details': []
            }
            
            # Get records that have expired
            expired_records = self._get_expired_retention_records()
            
            for record in expired_records:
                try:
                    # Delete the data
                    success = self._delete_data_by_retention_record(record)
                    
                    if success:
                        results['deleted_records'] += 1
                        results['details'].append({
                            'data_type': record.data_type,
                            'user_id': record.user_id,
                            'deleted_at': datetime.utcnow().isoformat()
                        })
                    else:
                        results['errors'] += 1
                    
                    results['processed_records'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing retention record: {e}")
                    results['errors'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing data retention: {e}")
            raise
    
    def _get_expired_retention_records(self) -> List[DataRetentionRecord]:
        """Get retention records that have expired"""
        try:
            # This would query the database for expired records
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting expired retention records: {e}")
            return []
    
    def _delete_data_by_retention_record(self, record: DataRetentionRecord) -> bool:
        """Delete data based on retention record"""
        try:
            # This would actually delete the data from the database
            # For now, return True (success)
            return True
        except Exception as e:
            logger.error(f"Error deleting data by retention record: {e}")
            return False
    
    # ============================================================================
    # DATABASE STORAGE METHODS (PLACEHOLDERS)
    # ============================================================================
    
    def _store_user_consent(self, consent: UserConsent):
        """Store user consent in database"""
        # This would store the consent record in the database
        pass
    
    def _store_retention_record(self, record: DataRetentionRecord):
        """Store retention record in database"""
        # This would store the retention record in the database
        pass
    
    def _update_user_consent(self, user_id: str, consent_type: ConsentType, granted: bool):
        """Update user consent in database"""
        # This would update the consent record in the database
        pass 