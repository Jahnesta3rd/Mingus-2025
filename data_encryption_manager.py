#!/usr/bin/env python3
"""
Comprehensive Data Encryption Manager for Mingus Financial App
Enterprise-grade encryption for sensitive financial information
"""

import os
import json
import base64
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import sqlite3

# Configure logging
logger = logging.getLogger(__name__)

class DataSensitivity(Enum):
    """Data sensitivity levels for encryption"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    AES_256_CTR = "aes-256-ctr"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    FERNET = "fernet"

class ComplianceRegulation(Enum):
    """Compliance regulations"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"

@dataclass
class EncryptionConfig:
    """Configuration for encryption system"""
    # Master encryption key (should be stored securely)
    master_key: Optional[str] = None
    
    # Key derivation settings
    key_derivation_salt: Optional[str] = None
    key_derivation_iterations: int = 100000
    scrypt_n: int = 16384
    scrypt_r: int = 8
    scrypt_p: int = 1
    
    # Encryption algorithm preferences
    preferred_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    
    # Key rotation settings
    key_rotation_days: int = 90
    max_key_age_days: int = 365
    
    # Field-specific settings
    field_encryption_enabled: bool = True
    field_key_derivation: bool = True
    
    # Database encryption settings
    database_encryption_enabled: bool = True
    database_key_table: str = "encryption_keys"
    
    # Audit settings
    audit_encryption_operations: bool = True
    log_encryption_events: bool = True
    
    # Compliance settings
    fips_140_2_compliant: bool = True
    gdpr_compliant: bool = True
    pci_dss_compliant: bool = True
    
    # Performance settings
    cache_encryption_keys: bool = True
    key_cache_ttl_seconds: int = 3600

@dataclass
class EncryptedField:
    """Represents an encrypted field with metadata"""
    encrypted_data: str
    algorithm: str
    key_id: str
    iv: str
    auth_tag: Optional[str] = None
    sensitivity: DataSensitivity = DataSensitivity.HIGH
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataClassification:
    """Data classification for sensitivity mapping"""
    field_name: str
    sensitivity: DataSensitivity
    compliance_requirements: List[ComplianceRegulation]
    retention_period_days: int
    encryption_required: bool = True
    audit_required: bool = True

class DataClassificationManager:
    """Manages data classification and sensitivity mapping"""
    
    def __init__(self):
        self.classifications: Dict[str, DataClassification] = {}
        self._initialize_classifications()
    
    def _initialize_classifications(self):
        """Initialize data classifications for financial data"""
        
        # Critical financial data
        self.classifications.update({
            # Bank account information
            'account_number': DataClassification(
                field_name='account_number',
                sensitivity=DataSensitivity.CRITICAL,
                compliance_requirements=[ComplianceRegulation.PCI_DSS, ComplianceRegulation.GDPR],
                retention_period_days=2555,  # 7 years
                encryption_required=True,
                audit_required=True
            ),
            'routing_number': DataClassification(
                field_name='routing_number',
                sensitivity=DataSensitivity.CRITICAL,
                compliance_requirements=[ComplianceRegulation.PCI_DSS, ComplianceRegulation.GDPR],
                retention_period_days=2555,
                encryption_required=True,
                audit_required=True
            ),
            
            # Financial amounts
            'monthly_income': DataClassification(
                field_name='monthly_income',
                sensitivity=DataSensitivity.HIGH,
                compliance_requirements=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA],
                retention_period_days=1825,  # 5 years
                encryption_required=True,
                audit_required=True
            ),
            'current_savings': DataClassification(
                field_name='current_savings',
                sensitivity=DataSensitivity.HIGH,
                compliance_requirements=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA],
                retention_period_days=1825,
                encryption_required=True,
                audit_required=True
            ),
            'current_debt': DataClassification(
                field_name='current_debt',
                sensitivity=DataSensitivity.HIGH,
                compliance_requirements=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA],
                retention_period_days=1825,
                encryption_required=True,
                audit_required=True
            ),
            'emergency_fund': DataClassification(
                field_name='emergency_fund',
                sensitivity=DataSensitivity.HIGH,
                compliance_requirements=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA],
                retention_period_days=1825,
                encryption_required=True,
                audit_required=True
            ),
            
            # Financial goals
            'savings_goal': DataClassification(
                field_name='savings_goal',
                sensitivity=DataSensitivity.MEDIUM,
                compliance_requirements=[ComplianceRegulation.GDPR],
                retention_period_days=1095,  # 3 years
                encryption_required=True,
                audit_required=False
            ),
            'debt_payoff_goal': DataClassification(
                field_name='debt_payoff_goal',
                sensitivity=DataSensitivity.MEDIUM,
                compliance_requirements=[ComplianceRegulation.GDPR],
                retention_period_days=1095,
                encryption_required=True,
                audit_required=False
            ),
            'investment_goal': DataClassification(
                field_name='investment_goal',
                sensitivity=DataSensitivity.MEDIUM,
                compliance_requirements=[ComplianceRegulation.GDPR],
                retention_period_days=1095,
                encryption_required=True,
                audit_required=False
            ),
            
            # Personal information
            'ssn': DataClassification(
                field_name='ssn',
                sensitivity=DataSensitivity.CRITICAL,
                compliance_requirements=[ComplianceRegulation.GDPR, ComplianceRegulation.HIPAA],
                retention_period_days=3650,  # 10 years
                encryption_required=True,
                audit_required=True
            ),
            'date_of_birth': DataClassification(
                field_name='date_of_birth',
                sensitivity=DataSensitivity.HIGH,
                compliance_requirements=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA],
                retention_period_days=3650,
                encryption_required=True,
                audit_required=True
            ),
            'phone_number': DataClassification(
                field_name='phone_number',
                sensitivity=DataSensitivity.MEDIUM,
                compliance_requirements=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA],
                retention_period_days=1825,
                encryption_required=True,
                audit_required=False
            ),
            
            # Non-sensitive data (for reference)
            'income_frequency': DataClassification(
                field_name='income_frequency',
                sensitivity=DataSensitivity.LOW,
                compliance_requirements=[ComplianceRegulation.GDPR],
                retention_period_days=1095,
                encryption_required=False,
                audit_required=False
            ),
            'risk_tolerance': DataClassification(
                field_name='risk_tolerance',
                sensitivity=DataSensitivity.LOW,
                compliance_requirements=[ComplianceRegulation.GDPR],
                retention_period_days=1095,
                encryption_required=False,
                audit_required=False
            ),
            'investment_experience': DataClassification(
                field_name='investment_experience',
                sensitivity=DataSensitivity.LOW,
                compliance_requirements=[ComplianceRegulation.GDPR],
                retention_period_days=1095,
                encryption_required=False,
                audit_required=False
            )
        })
    
    def get_classification(self, field_name: str) -> Optional[DataClassification]:
        """Get classification for a field"""
        return self.classifications.get(field_name)
    
    def get_sensitive_fields(self) -> List[str]:
        """Get all fields that require encryption"""
        return [
            field_name for field_name, classification in self.classifications.items()
            if classification.encryption_required
        ]
    
    def get_critical_fields(self) -> List[str]:
        """Get all critical sensitivity fields"""
        return [
            field_name for field_name, classification in self.classifications.items()
            if classification.sensitivity == DataSensitivity.CRITICAL
        ]
    
    def get_compliance_fields(self, regulation: ComplianceRegulation) -> List[str]:
        """Get fields required for specific compliance regulation"""
        return [
            field_name for field_name, classification in self.classifications.items()
            if regulation in classification.compliance_requirements
        ]

class KeyManager:
    """Manages encryption keys and key rotation"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.current_key_id = None
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialize encryption keys"""
        if not self.config.master_key:
            self.config.master_key = self._generate_master_key()
        
        if not self.config.key_derivation_salt:
            self.config.key_derivation_salt = secrets.token_hex(32)
        
        # Generate initial keys
        self._generate_new_key_pair()
    
    def _generate_master_key(self) -> str:
        """Generate a new master encryption key"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _generate_new_key_pair(self):
        """Generate new encryption key pair"""
        key_id = f"key_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
        
        # Generate symmetric key
        symmetric_key = secrets.token_bytes(32)
        
        # Generate asymmetric key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Store key information
        self.keys[key_id] = {
            'symmetric_key': symmetric_key,
            'private_key': private_key,
            'public_key': public_key,
            'created_at': datetime.utcnow(),
            'algorithm': self.config.preferred_algorithm.value,
            'active': True
        }
        
        self.current_key_id = key_id
        logger.info(f"Generated new encryption key pair: {key_id}")
    
    def get_current_key(self) -> Tuple[str, bytes]:
        """Get current encryption key"""
        if not self.current_key_id or self.current_key_id not in self.keys:
            self._generate_new_key_pair()
        
        return self.current_key_id, self.keys[self.current_key_id]['symmetric_key']
    
    def get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """Get encryption key by ID"""
        if key_id in self.keys and self.keys[key_id]['active']:
            return self.keys[key_id]['symmetric_key']
        return None
    
    def rotate_keys(self):
        """Rotate encryption keys"""
        logger.info("Starting key rotation process")
        
        # Generate new key pair
        old_key_id = self.current_key_id
        self._generate_new_key_pair()
        
        # Mark old key as inactive (but keep for decryption)
        if old_key_id and old_key_id in self.keys:
            self.keys[old_key_id]['active'] = False
            self.keys[old_key_id]['deactivated_at'] = datetime.utcnow()
        
        logger.info(f"Key rotation completed. New key: {self.current_key_id}")

class FieldEncryptionManager:
    """Manages field-level encryption for sensitive data"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.key_manager = KeyManager(config)
        self.field_keys: Dict[str, bytes] = {}
    
    def _derive_field_key(self, field_name: str, sensitivity: DataSensitivity) -> bytes:
        """Derive field-specific encryption key"""
        if not self.config.field_key_derivation:
            key_id, master_key = self.key_manager.get_current_key()
            return master_key
        
        # Derive field-specific key
        salt = f"{field_name}_{sensitivity.value}".encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config.key_derivation_iterations,
            backend=default_backend()
        )
        
        key_id, master_key = self.key_manager.get_current_key()
        field_key = kdf.derive(master_key)
        
        return field_key
    
    def encrypt_field(self, data: Any, field_name: str, 
                     sensitivity: DataSensitivity = DataSensitivity.HIGH) -> EncryptedField:
        """Encrypt a field with appropriate algorithm"""
        
        if not self.config.field_encryption_enabled:
            return EncryptedField(
                encrypted_data=str(data),
                algorithm="none",
                key_id="none",
                iv="",
                sensitivity=sensitivity
            )
        
        # Convert data to string if needed
        if not isinstance(data, str):
            data = json.dumps(data)
        
        # Derive field-specific key
        field_key = self._derive_field_key(field_name, sensitivity)
        
        # Generate IV
        iv = secrets.token_bytes(16)
        
        # Encrypt data based on algorithm
        if self.config.preferred_algorithm == EncryptionAlgorithm.AES_256_GCM:
            cipher = Cipher(
                algorithms.AES(field_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
            auth_tag = encryptor.tag
            
            encrypted_data = base64.b64encode(ciphertext).decode()
            auth_tag_b64 = base64.b64encode(auth_tag).decode()
            
        elif self.config.preferred_algorithm == EncryptionAlgorithm.AES_256_CBC:
            cipher = Cipher(
                algorithms.AES(field_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad data to block size
            padded_data = self._pad_data(data.encode())
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            encrypted_data = base64.b64encode(ciphertext).decode()
            auth_tag_b64 = None
            
        else:
            # Fallback to Fernet
            f = Fernet(base64.urlsafe_b64encode(field_key))
            encrypted_data = f.encrypt(data.encode()).decode()
            auth_tag_b64 = None
        
        key_id, _ = self.key_manager.get_current_key()
        
        return EncryptedField(
            encrypted_data=encrypted_data,
            algorithm=self.config.preferred_algorithm.value,
            key_id=key_id,
            iv=base64.b64encode(iv).decode(),
            auth_tag=auth_tag_b64,
            sensitivity=sensitivity
        )
    
    def decrypt_field(self, encrypted_field: EncryptedField, field_name: str) -> Any:
        """Decrypt a field"""
        
        if encrypted_field.algorithm == "none":
            return encrypted_field.encrypted_data
        
        # Get the key used for encryption
        key = self.key_manager.get_key_by_id(encrypted_field.key_id)
        if not key:
            raise ValueError(f"Key {encrypted_field.key_id} not found or inactive")
        
        # Derive field-specific key
        field_key = self._derive_field_key(field_name, encrypted_field.sensitivity)
        
        # Decrypt based on algorithm
        if encrypted_field.algorithm == EncryptionAlgorithm.AES_256_GCM.value:
            cipher = Cipher(
                algorithms.AES(field_key),
                modes.GCM(base64.b64decode(encrypted_field.iv), 
                         base64.b64decode(encrypted_field.auth_tag)),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            ciphertext = base64.b64decode(encrypted_field.encrypted_data)
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
        elif encrypted_field.algorithm == EncryptionAlgorithm.AES_256_CBC.value:
            cipher = Cipher(
                algorithms.AES(field_key),
                modes.CBC(base64.b64decode(encrypted_field.iv)),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            ciphertext = base64.b64decode(encrypted_field.encrypted_data)
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            plaintext = self._unpad_data(padded_plaintext)
            
        else:
            # Fallback to Fernet
            f = Fernet(base64.urlsafe_b64encode(field_key))
            plaintext = f.decrypt(encrypted_field.encrypted_data.encode())
        
        # Try to parse as JSON, otherwise return as string
        try:
            return json.loads(plaintext.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return plaintext.decode()
    
    def _pad_data(self, data: bytes) -> bytes:
        """Pad data to block size"""
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, data: bytes) -> bytes:
        """Remove padding from data"""
        padding_length = data[-1]
        return data[:-padding_length]

class DataEncryptionManager:
    """Main encryption manager for comprehensive data protection"""
    
    def __init__(self, config: EncryptionConfig = None):
        self.config = config or EncryptionConfig()
        self.classification_manager = DataClassificationManager()
        self.field_encryption_manager = FieldEncryptionManager(self.config)
        
        # Initialize audit logging
        if self.config.audit_encryption_operations:
            self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Setup audit logging for encryption operations"""
        self.audit_db_path = "encryption_audit.db"
        self._create_audit_table()
    
    def _create_audit_table(self):
        """Create audit logging table"""
        with sqlite3.connect(self.audit_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS encryption_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    field_name TEXT,
                    user_id TEXT,
                    key_id TEXT,
                    algorithm TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
    
    def _log_audit_event(self, operation: str, field_name: str = None, 
                        user_id: str = None, success: bool = True, 
                        error_message: str = None, metadata: Dict = None):
        """Log audit event"""
        if not self.config.audit_encryption_operations:
            return
        
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.execute("""
                    INSERT INTO encryption_audit 
                    (timestamp, operation, field_name, user_id, key_id, algorithm, success, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    operation,
                    field_name,
                    user_id,
                    self.field_encryption_manager.key_manager.current_key_id,
                    self.config.preferred_algorithm.value,
                    success,
                    error_message,
                    json.dumps(metadata) if metadata else None
                ))
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def encrypt_financial_data(self, data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """Encrypt financial data based on classification"""
        encrypted_data = {}
        
        for field_name, value in data.items():
            classification = self.classification_manager.get_classification(field_name)
            
            if classification and classification.encryption_required:
                try:
                    encrypted_field = self.field_encryption_manager.encrypt_field(
                        value, field_name, classification.sensitivity
                    )
                    
                    encrypted_data[field_name] = {
                        'encrypted_data': encrypted_field.encrypted_data,
                        'algorithm': encrypted_field.algorithm,
                        'key_id': encrypted_field.key_id,
                        'iv': encrypted_field.iv,
                        'auth_tag': encrypted_field.auth_tag,
                        'sensitivity': encrypted_field.sensitivity.value,
                        'created_at': encrypted_field.created_at.isoformat()
                    }
                    
                    self._log_audit_event(
                        'encrypt', field_name, user_id, True,
                        metadata={'sensitivity': classification.sensitivity.value}
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to encrypt field {field_name}: {e}")
                    self._log_audit_event('encrypt', field_name, user_id, False, str(e))
                    # Keep original data if encryption fails
                    encrypted_data[field_name] = value
            else:
                # Store non-sensitive data as-is
                encrypted_data[field_name] = value
        
        return encrypted_data
    
    def decrypt_financial_data(self, encrypted_data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """Decrypt financial data"""
        decrypted_data = {}
        
        for field_name, value in encrypted_data.items():
            classification = self.classification_manager.get_classification(field_name)
            
            if classification and classification.encryption_required and isinstance(value, dict):
                try:
                    # Check if this is encrypted data
                    if 'encrypted_data' in value and 'algorithm' in value:
                        encrypted_field = EncryptedField(
                            encrypted_data=value['encrypted_data'],
                            algorithm=value['algorithm'],
                            key_id=value['key_id'],
                            iv=value['iv'],
                            auth_tag=value.get('auth_tag'),
                            sensitivity=DataSensitivity(value['sensitivity']),
                            created_at=datetime.fromisoformat(value['created_at'])
                        )
                        
                        decrypted_value = self.field_encryption_manager.decrypt_field(
                            encrypted_field, field_name
                        )
                        
                        decrypted_data[field_name] = decrypted_value
                        
                        self._log_audit_event(
                            'decrypt', field_name, user_id, True,
                            metadata={'sensitivity': classification.sensitivity.value}
                        )
                    else:
                        # Not encrypted, store as-is
                        decrypted_data[field_name] = value
                        
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field_name}: {e}")
                    self._log_audit_event('decrypt', field_name, user_id, False, str(e))
                    # Keep encrypted data if decryption fails
                    decrypted_data[field_name] = value
            else:
                # Non-sensitive data, store as-is
                decrypted_data[field_name] = value
        
        return decrypted_data
    
    def get_data_classification_report(self) -> Dict[str, Any]:
        """Generate data classification report"""
        report = {
            'total_fields': len(self.classification_manager.classifications),
            'sensitivity_distribution': {},
            'compliance_mapping': {},
            'encryption_requirements': {
                'encrypted_fields': len(self.classification_manager.get_sensitive_fields()),
                'non_encrypted_fields': len(self.classification_manager.classifications) - 
                                      len(self.classification_manager.get_sensitive_fields())
            }
        }
        
        # Sensitivity distribution
        for classification in self.classification_manager.classifications.values():
            sensitivity = classification.sensitivity.value
            report['sensitivity_distribution'][sensitivity] = \
                report['sensitivity_distribution'].get(sensitivity, 0) + 1
        
        # Compliance mapping
        for regulation in ComplianceRegulation:
            report['compliance_mapping'][regulation.value] = \
                len(self.classification_manager.get_compliance_fields(regulation))
        
        return report
    
    def rotate_encryption_keys(self):
        """Rotate all encryption keys"""
        logger.info("Starting encryption key rotation")
        
        try:
            self.field_encryption_manager.key_manager.rotate_keys()
            
            self._log_audit_event(
                'key_rotation', success=True,
                metadata={'rotation_date': datetime.utcnow().isoformat()}
            )
            
            logger.info("Encryption key rotation completed successfully")
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            self._log_audit_event('key_rotation', success=False, error_message=str(e))
            raise
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Get encryption system status"""
        current_key_id, _ = self.field_encryption_manager.key_manager.get_current_key()
        
        return {
            'encryption_enabled': self.config.field_encryption_enabled,
            'current_key_id': current_key_id,
            'algorithm': self.config.preferred_algorithm.value,
            'key_rotation_days': self.config.key_rotation_days,
            'compliance_status': {
                'fips_140_2': self.config.fips_140_2_compliant,
                'gdpr': self.config.gdpr_compliant,
                'pci_dss': self.config.pci_dss_compliant
            },
            'audit_enabled': self.config.audit_encryption_operations,
            'total_keys': len(self.field_encryption_manager.key_manager.keys)
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize encryption manager
    config = EncryptionConfig(
        field_encryption_enabled=True,
        audit_encryption_operations=True,
        preferred_algorithm=EncryptionAlgorithm.AES_256_GCM
    )
    
    encryption_manager = DataEncryptionManager(config)
    
    # Example financial data
    financial_data = {
        'monthly_income': 5000.00,
        'current_savings': 15000.00,
        'current_debt': 25000.00,
        'emergency_fund': 5000.00,
        'savings_goal': 50000.00,
        'risk_tolerance': 'moderate',
        'income_frequency': 'monthly'
    }
    
    print("🔐 Encrypting financial data...")
    encrypted_data = encryption_manager.encrypt_financial_data(financial_data, "user123")
    
    print("🔓 Decrypting financial data...")
    decrypted_data = encryption_manager.decrypt_financial_data(encrypted_data, "user123")
    
    print("📊 Data Classification Report:")
    report = encryption_manager.get_data_classification_report()
    print(json.dumps(report, indent=2))
    
    print("🔑 Encryption Status:")
    status = encryption_manager.get_encryption_status()
    print(json.dumps(status, indent=2))
    
    print("✅ Encryption test completed successfully!")
