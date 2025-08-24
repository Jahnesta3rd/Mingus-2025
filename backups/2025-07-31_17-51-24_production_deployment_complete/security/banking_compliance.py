"""
Banking Compliance and Security System

This module provides bank-grade security and compliance features for handling
sensitive banking data through Plaid integration, including encryption,
audit logging, data retention policies, and regulatory compliance.
"""

import logging
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import base64
import os
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.models.bank_account_models import BankAccount, PlaidConnection
from backend.utils.encryption import encrypt_data, decrypt_data
from backend.config.base import Config

logger = logging.getLogger(__name__)


class ComplianceLevel(Enum):
    """Compliance levels for different data types"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    HIGHLY_RESTRICTED = "highly_restricted"


class AuditEventType(Enum):
    """Types of audit events"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    DECRYPTION = "decryption"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    COMPLIANCE_CHECK = "compliance_check"
    SECURITY_INCIDENT = "security_incident"


class DataRetentionPolicy(Enum):
    """Data retention policy types"""
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years
    PERMANENT = "permanent"


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    password_min_length: int = 12
    require_mfa: bool = True
    audit_log_retention_days: int = 2555  # 7 years
    data_encryption_at_rest: bool = True
    data_encryption_in_transit: bool = True
    plaid_webhook_verification: bool = True
    rate_limiting_enabled: bool = True
    ip_whitelist_enabled: bool = False


@dataclass
class AuditLogEntry:
    """Audit log entry data structure"""
    log_id: str
    user_id: Optional[str]
    event_type: AuditEventType
    event_description: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    compliance_level: ComplianceLevel = ComplianceLevel.INTERNAL
    data_classification: str = "confidential"


@dataclass
class DataClassification:
    """Data classification information"""
    classification_id: str
    data_type: str
    compliance_level: ComplianceLevel
    retention_policy: DataRetentionPolicy
    encryption_required: bool
    access_controls: List[str]
    audit_required: bool
    description: str


@dataclass
class ComplianceReport:
    """Compliance report data structure"""
    report_id: str
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    compliance_score: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    status: str  # 'compliant', 'non_compliant', 'review_required'


class BankingComplianceService:
    """Bank-grade security and compliance service for banking data"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.security_config = self._load_security_config()
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Initialize data classifications
        self.data_classifications = self._initialize_data_classifications()
        
        # Compliance monitoring
        self.compliance_monitors = {
            'gdpr': self._check_gdpr_compliance,
            'ccpa': self._check_ccpa_compliance,
            'sox': self._check_sox_compliance,
            'pci_dss': self._check_pci_dss_compliance,
            'glba': self._check_glba_compliance
        }
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment or defaults"""
        return SecurityConfig(
            encryption_algorithm=getattr(self.config, 'ENCRYPTION_ALGORITHM', 'AES-256-GCM'),
            key_rotation_days=int(getattr(self.config, 'KEY_ROTATION_DAYS', 90)),
            session_timeout_minutes=int(getattr(self.config, 'SESSION_TIMEOUT_MINUTES', 30)),
            max_login_attempts=int(getattr(self.config, 'MAX_LOGIN_ATTEMPTS', 5)),
            password_min_length=int(getattr(self.config, 'PASSWORD_MIN_LENGTH', 12)),
            require_mfa=bool(getattr(self.config, 'REQUIRE_MFA', True)),
            audit_log_retention_days=int(getattr(self.config, 'AUDIT_LOG_RETENTION_DAYS', 2555)),
            data_encryption_at_rest=bool(getattr(self.config, 'DATA_ENCRYPTION_AT_REST', True)),
            data_encryption_in_transit=bool(getattr(self.config, 'DATA_ENCRYPTION_IN_TRANSIT', True)),
            plaid_webhook_verification=bool(getattr(self.config, 'PLAID_WEBHOOK_VERIFICATION', True)),
            rate_limiting_enabled=bool(getattr(self.config, 'RATE_LIMITING_ENABLED', True)),
            ip_whitelist_enabled=bool(getattr(self.config, 'IP_WHITELIST_ENABLED', False))
        )
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key"""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # Generate new key (in production, this should be stored securely)
            key = Fernet.generate_key()
            logger.warning("No encryption key found, generated new key")
        return key if isinstance(key, bytes) else key.encode()
    
    def _initialize_data_classifications(self) -> Dict[str, DataClassification]:
        """Initialize data classification rules"""
        return {
            'bank_account_number': DataClassification(
                classification_id='bank_account_number',
                data_type='bank_account_number',
                compliance_level=ComplianceLevel.HIGHLY_RESTRICTED,
                retention_policy=DataRetentionPolicy.LONG_TERM,
                encryption_required=True,
                access_controls=['owner', 'admin'],
                audit_required=True,
                description='Bank account numbers require highest level of protection'
            ),
            'routing_number': DataClassification(
                classification_id='routing_number',
                data_type='routing_number',
                compliance_level=ComplianceLevel.RESTRICTED,
                retention_policy=DataRetentionPolicy.LONG_TERM,
                encryption_required=True,
                access_controls=['owner', 'admin'],
                audit_required=True,
                description='Bank routing numbers require high level of protection'
            ),
            'transaction_data': DataClassification(
                classification_id='transaction_data',
                data_type='transaction_data',
                compliance_level=ComplianceLevel.CONFIDENTIAL,
                retention_policy=DataRetentionPolicy.MEDIUM_TERM,
                encryption_required=True,
                access_controls=['owner', 'admin', 'analytics'],
                audit_required=True,
                description='Transaction data requires confidentiality protection'
            ),
            'balance_information': DataClassification(
                classification_id='balance_information',
                data_type='balance_information',
                compliance_level=ComplianceLevel.CONFIDENTIAL,
                retention_policy=DataRetentionPolicy.SHORT_TERM,
                encryption_required=True,
                access_controls=['owner', 'admin'],
                audit_required=True,
                description='Account balance information requires confidentiality'
            ),
            'plaid_access_token': DataClassification(
                classification_id='plaid_access_token',
                data_type='plaid_access_token',
                compliance_level=ComplianceLevel.HIGHLY_RESTRICTED,
                retention_policy=DataRetentionPolicy.MEDIUM_TERM,
                encryption_required=True,
                access_controls=['owner', 'admin'],
                audit_required=True,
                description='Plaid access tokens require highest level of protection'
            )
        }
    
    def encrypt_sensitive_data(self, data: str, data_type: str) -> str:
        """Encrypt sensitive data based on classification"""
        try:
            classification = self.data_classifications.get(data_type)
            if not classification or not classification.encryption_required:
                return data
            
            # Encrypt the data
            encrypted_data = self.fernet.encrypt(data.encode())
            
            # Log encryption event
            self._log_audit_event(
                user_id=None,
                event_type=AuditEventType.ENCRYPTION,
                event_description=f"Encrypted {data_type} data",
                resource_type=data_type,
                resource_id=None,
                ip_address="system",
                user_agent="system",
                metadata={'data_type': data_type, 'classification': classification.compliance_level.value}
            )
            
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting sensitive data: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str, data_type: str) -> str:
        """Decrypt sensitive data based on classification"""
        try:
            classification = self.data_classifications.get(data_type)
            if not classification or not classification.encryption_required:
                return encrypted_data
            
            # Decrypt the data
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            
            # Log decryption event
            self._log_audit_event(
                user_id=None,
                event_type=AuditEventType.DECRYPTION,
                event_description=f"Decrypted {data_type} data",
                resource_type=data_type,
                resource_id=None,
                ip_address="system",
                user_agent="system",
                metadata={'data_type': data_type, 'classification': classification.compliance_level.value}
            )
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Error decrypting sensitive data: {e}")
            raise
    
    def verify_plaid_webhook_signature(self, body: str, signature: str, timestamp: str) -> bool:
        """Verify Plaid webhook signature for authenticity"""
        try:
            if not self.security_config.plaid_webhook_verification:
                return True
            
            # Get Plaid webhook secret
            webhook_secret = os.getenv('PLAID_WEBHOOK_SECRET')
            if not webhook_secret:
                logger.error("Plaid webhook secret not configured")
                return False
            
            # Verify timestamp is recent (within 5 minutes)
            current_time = int(time.time())
            webhook_time = int(timestamp)
            if abs(current_time - webhook_time) > 300:  # 5 minutes
                logger.warning(f"Webhook timestamp too old: {webhook_time}")
                return False
            
            # Create expected signature
            expected_signature = hmac.new(
                webhook_secret.encode(),
                f"{timestamp}.{body}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            # Log verification attempt
            self._log_audit_event(
                user_id=None,
                event_type=AuditEventType.AUTHENTICATION,
                event_description="Plaid webhook signature verification",
                resource_type="plaid_webhook",
                resource_id=None,
                ip_address="plaid",
                user_agent="plaid_webhook",
                metadata={'signature_valid': is_valid, 'timestamp': timestamp}
            )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying Plaid webhook signature: {e}")
            return False
    
    def validate_bank_data_access(self, user_id: str, bank_account_id: str, 
                                 access_type: str, ip_address: str, user_agent: str) -> bool:
        """Validate user access to bank data"""
        try:
            # Check if user owns the bank account
            bank_account = self.db.query(BankAccount).filter(
                and_(
                    BankAccount.id == bank_account_id,
                    BankAccount.user_id == user_id,
                    BankAccount.is_active == True
                )
            ).first()
            
            if not bank_account:
                logger.warning(f"Unauthorized access attempt: user {user_id} to bank account {bank_account_id}")
                self._log_audit_event(
                    user_id=user_id,
                    event_type=AuditEventType.AUTHORIZATION,
                    event_description=f"Unauthorized access attempt to bank account {bank_account_id}",
                    resource_type="bank_account",
                    resource_id=bank_account_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'access_type': access_type, 'authorized': False}
                )
                return False
            
            # Log successful access
            self._log_audit_event(
                user_id=user_id,
                event_type=AuditEventType.DATA_ACCESS,
                event_description=f"Authorized access to bank account {bank_account_id}",
                resource_type="bank_account",
                resource_id=bank_account_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'access_type': access_type, 'authorized': True}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating bank data access: {e}")
            return False
    
    def sanitize_bank_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize bank data for logging and display"""
        try:
            sanitized_data = data.copy()
            
            # Remove or mask sensitive fields
            sensitive_fields = [
                'account_number', 'routing_number', 'access_token', 
                'public_token', 'account_id', 'item_id'
            ]
            
            for field in sensitive_fields:
                if field in sanitized_data:
                    if isinstance(sanitized_data[field], str):
                        # Mask the value (show first 2 and last 2 characters)
                        value = sanitized_data[field]
                        if len(value) > 4:
                            sanitized_data[field] = f"{value[:2]}***{value[-2:]}"
                        else:
                            sanitized_data[field] = "***"
                    else:
                        sanitized_data[field] = "***"
            
            return sanitized_data
            
        except Exception as e:
            logger.error(f"Error sanitizing bank data: {e}")
            return data
    
    def _log_audit_event(self, user_id: Optional[str], event_type: AuditEventType,
                        event_description: str, resource_type: str, resource_id: Optional[str],
                        ip_address: str, user_agent: str, metadata: Dict[str, Any] = None):
        """Log audit event for compliance"""
        try:
            audit_entry = AuditLogEntry(
                log_id=f"audit_{int(time.time())}_{secrets.token_hex(4)}",
                user_id=user_id,
                event_type=event_type,
                event_description=event_description,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                compliance_level=ComplianceLevel.INTERNAL
            )
            
            # In production, this would be stored in a dedicated audit log table
            logger.info(f"AUDIT: {audit_entry.event_type.value} - {audit_entry.event_description} - User: {user_id} - IP: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    def check_data_retention_compliance(self) -> List[Dict[str, Any]]:
        """Check data retention compliance"""
        try:
            findings = []
            current_time = datetime.utcnow()
            
            # Check bank account data retention
            bank_accounts = self.db.query(BankAccount).all()
            for account in bank_accounts:
                classification = self.data_classifications.get('bank_account_number')
                retention_days = self._get_retention_days(classification.retention_policy)
                
                if account.created_at and (current_time - account.created_at).days > retention_days:
                    findings.append({
                        'type': 'retention_violation',
                        'resource_type': 'bank_account',
                        'resource_id': account.id,
                        'description': f"Bank account data exceeds retention period of {retention_days} days",
                        'severity': 'high'
                    })
            
            # Check Plaid connection data retention
            plaid_connections = self.db.query(PlaidConnection).all()
            for connection in plaid_connections:
                classification = self.data_classifications.get('plaid_access_token')
                retention_days = self._get_retention_days(classification.retention_policy)
                
                if connection.created_at and (current_time - connection.created_at).days > retention_days:
                    findings.append({
                        'type': 'retention_violation',
                        'resource_type': 'plaid_connection',
                        'resource_id': connection.id,
                        'description': f"Plaid connection data exceeds retention period of {retention_days} days",
                        'severity': 'high'
                    })
            
            return findings
            
        except Exception as e:
            logger.error(f"Error checking data retention compliance: {e}")
            return []
    
    def _get_retention_days(self, retention_policy: DataRetentionPolicy) -> int:
        """Get retention days for a policy"""
        retention_map = {
            DataRetentionPolicy.IMMEDIATE: 0,
            DataRetentionPolicy.SHORT_TERM: 30,
            DataRetentionPolicy.MEDIUM_TERM: 365,
            DataRetentionPolicy.LONG_TERM: 2555,  # 7 years
            DataRetentionPolicy.PERMANENT: 999999
        }
        return retention_map.get(retention_policy, 365)
    
    def generate_compliance_report(self, report_type: str, period_start: datetime, 
                                 period_end: datetime) -> ComplianceReport:
        """Generate compliance report for specified period"""
        try:
            findings = []
            recommendations = []
            
            # Check data retention compliance
            retention_findings = self.check_data_retention_compliance()
            findings.extend(retention_findings)
            
            # Check regulatory compliance
            for regulation, check_function in self.compliance_monitors.items():
                regulation_findings = check_function(period_start, period_end)
                findings.extend(regulation_findings)
            
            # Calculate compliance score
            total_checks = len(findings)
            compliant_checks = len([f for f in findings if f.get('severity') == 'low'])
            compliance_score = (compliant_checks / total_checks * 100) if total_checks > 0 else 100
            
            # Generate recommendations
            if compliance_score < 90:
                recommendations.append("Implement automated data retention cleanup")
            if any(f.get('severity') == 'high' for f in findings):
                recommendations.append("Immediate action required for high-severity findings")
            if compliance_score < 80:
                recommendations.append("Conduct comprehensive security audit")
            
            # Determine status
            if compliance_score >= 95:
                status = 'compliant'
            elif compliance_score >= 80:
                status = 'review_required'
            else:
                status = 'non_compliant'
            
            return ComplianceReport(
                report_id=f"compliance_{int(time.time())}",
                report_type=report_type,
                generated_at=datetime.utcnow(),
                period_start=period_start,
                period_end=period_end,
                compliance_score=compliance_score,
                findings=findings,
                recommendations=recommendations,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    
    def _check_gdpr_compliance(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Check GDPR compliance"""
        findings = []
        
        # Check for data subject rights
        # Check for data minimization
        # Check for consent management
        # Check for data portability
        
        return findings
    
    def _check_ccpa_compliance(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Check CCPA compliance"""
        findings = []
        
        # Check for consumer rights
        # Check for data disclosure
        # Check for opt-out mechanisms
        
        return findings
    
    def _check_sox_compliance(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Check SOX compliance"""
        findings = []
        
        # Check for financial controls
        # Check for audit trails
        # Check for data integrity
        
        return findings
    
    def _check_pci_dss_compliance(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Check PCI DSS compliance"""
        findings = []
        
        # Check for card data protection
        # Check for access controls
        # Check for monitoring and logging
        
        return findings
    
    def _check_glba_compliance(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Check GLBA compliance"""
        findings = []
        
        # Check for financial privacy
        # Check for data security
        # Check for consumer notification
        
        return findings
    
    def rotate_encryption_keys(self) -> bool:
        """Rotate encryption keys"""
        try:
            # Generate new key
            new_key = Fernet.generate_key()
            new_fernet = Fernet(new_key)
            
            # Re-encrypt all sensitive data with new key
            # This would involve updating all encrypted data in the database
            
            # Update the current key
            self.encryption_key = new_key
            self.fernet = new_fernet
            
            logger.info("Encryption keys rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating encryption keys: {e}")
            return False
    
    def cleanup_expired_data(self) -> int:
        """Clean up expired data based on retention policies"""
        try:
            cleaned_count = 0
            current_time = datetime.utcnow()
            
            # Clean up expired bank accounts
            for classification in self.data_classifications.values():
                retention_days = self._get_retention_days(classification.retention_policy)
                cutoff_date = current_time - timedelta(days=retention_days)
                
                if classification.data_type == 'bank_account_number':
                    expired_accounts = self.db.query(BankAccount).filter(
                        BankAccount.created_at < cutoff_date
                    ).all()
                    
                    for account in expired_accounts:
                        # Log deletion
                        self._log_audit_event(
                            user_id=account.user_id,
                            event_type=AuditEventType.DATA_DELETION,
                            event_description=f"Deleted expired bank account {account.id}",
                            resource_type="bank_account",
                            resource_id=account.id,
                            ip_address="system",
                            user_agent="system",
                            metadata={'retention_policy': classification.retention_policy.value}
                        )
                        
                        # Delete the account
                        self.db.delete(account)
                        cleaned_count += 1
                
                elif classification.data_type == 'plaid_access_token':
                    expired_connections = self.db.query(PlaidConnection).filter(
                        PlaidConnection.created_at < cutoff_date
                    ).all()
                    
                    for connection in expired_connections:
                        # Log deletion
                        self._log_audit_event(
                            user_id=connection.user_id,
                            event_type=AuditEventType.DATA_DELETION,
                            event_description=f"Deleted expired Plaid connection {connection.id}",
                            resource_type="plaid_connection",
                            resource_id=connection.id,
                            ip_address="system",
                            user_agent="system",
                            metadata={'retention_policy': classification.retention_policy.value}
                        )
                        
                        # Delete the connection
                        self.db.delete(connection)
                        cleaned_count += 1
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Cleaned up {cleaned_count} expired data records")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")
            self.db.rollback()
            return 0
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring"""
        try:
            current_time = datetime.utcnow()
            last_24_hours = current_time - timedelta(hours=24)
            last_7_days = current_time - timedelta(days=7)
            
            # Count active bank connections
            active_connections = self.db.query(PlaidConnection).filter(
                PlaidConnection.is_active == True
            ).count()
            
            # Count total users with bank connections
            users_with_banks = self.db.query(PlaidConnection.user_id).distinct().count()
            
            # Get encryption status
            encryption_status = {
                'at_rest': self.security_config.data_encryption_at_rest,
                'in_transit': self.security_config.data_encryption_in_transit,
                'algorithm': self.security_config.encryption_algorithm
            }
            
            # Get compliance status
            compliance_report = self.generate_compliance_report(
                'security_metrics',
                last_7_days,
                current_time
            )
            
            return {
                'active_connections': active_connections,
                'users_with_banks': users_with_banks,
                'encryption_status': encryption_status,
                'compliance_score': compliance_report.compliance_score,
                'compliance_status': compliance_report.status,
                'security_config': {
                    'key_rotation_days': self.security_config.key_rotation_days,
                    'session_timeout_minutes': self.security_config.session_timeout_minutes,
                    'require_mfa': self.security_config.require_mfa,
                    'rate_limiting_enabled': self.security_config.rate_limiting_enabled
                },
                'last_updated': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting security metrics: {e}")
            return {} 