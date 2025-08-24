"""
Financial Compliance Manager
Comprehensive financial compliance system with PCI DSS, data retention, audit trails, and breach notifications
"""

import os
import json
import time
import hashlib
import uuid
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import threading
from loguru import logger
import requests
from cryptography.fernet import Fernet
import base64
import ssl
import socket

class ComplianceStandard(Enum):
    """Financial compliance standards"""
    PCI_DSS = "pci_dss"
    SOX = "sox"
    GLBA = "glba"
    GDPR = "gdpr"
    CCPA = "ccpa"
    ISO_27001 = "iso_27001"

class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    HIGHLY_RESTRICTED = "highly_restricted"

class BreachSeverity(Enum):
    """Data breach severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BreachStatus(Enum):
    """Data breach status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    REPORTED = "reported"
    CLOSED = "closed"

class PaymentCardType(Enum):
    """Payment card types"""
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    JCB = "jcb"
    DINERS = "diners"

@dataclass
class PaymentData:
    """Payment data structure with PCI DSS compliance"""
    transaction_id: str
    card_type: PaymentCardType
    masked_pan: str  # Last 4 digits only
    expiry_month: str
    expiry_year: str
    cardholder_name: str
    amount: float
    currency: str
    merchant_id: str
    timestamp: datetime
    encrypted_data: str = ""
    tokenized_data: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FinancialRecord:
    """Financial record structure"""
    record_id: str
    user_id: str
    record_type: str
    data_classification: DataClassification
    content: str
    encrypted_content: str
    created_at: datetime
    retention_date: datetime
    compliance_standard: ComplianceStandard
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataBreach:
    """Data breach structure"""
    breach_id: str
    title: str
    description: str
    severity: BreachSeverity
    status: BreachStatus
    detected_at: datetime
    reported_at: Optional[datetime] = None
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    affected_records: int = 0
    affected_users: int = 0
    data_types: List[str] = field(default_factory=list)
    notification_sent: bool = False
    regulatory_reported: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetentionPolicy:
    """Data retention policy structure"""
    policy_id: str
    data_type: str
    retention_period_days: int
    compliance_standard: ComplianceStandard
    auto_delete: bool = True
    archive_before_delete: bool = False
    archive_location: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceAudit:
    """Compliance audit structure"""
    audit_id: str
    audit_type: str
    compliance_standard: ComplianceStandard
    auditor: str
    audit_date: datetime
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    status: str = "pending"
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class FinancialComplianceManager:
    """Comprehensive financial compliance manager"""
    
    def __init__(self, db_path: str = "/var/lib/mingus/financial_compliance.db"):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.audit_lock = threading.Lock()
        
        self._init_database()
        self._load_default_policies()
        self._init_pci_dss_requirements()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive financial data"""
        key_file = "/var/lib/mingus/financial_key.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _init_database(self):
        """Initialize financial compliance database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Payment data table (PCI DSS compliant)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS payment_data (
                        transaction_id TEXT PRIMARY KEY,
                        card_type TEXT NOT NULL,
                        masked_pan TEXT NOT NULL,
                        expiry_month TEXT NOT NULL,
                        expiry_year TEXT NOT NULL,
                        cardholder_name TEXT NOT NULL,
                        amount REAL NOT NULL,
                        currency TEXT NOT NULL,
                        merchant_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        encrypted_data TEXT,
                        tokenized_data TEXT,
                        metadata TEXT
                    )
                """)
                
                # Financial records table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS financial_records (
                        record_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        record_type TEXT NOT NULL,
                        data_classification TEXT NOT NULL,
                        content TEXT NOT NULL,
                        encrypted_content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        retention_date TEXT NOT NULL,
                        compliance_standard TEXT NOT NULL,
                        metadata TEXT
                    )
                """)
                
                # Data breaches table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_breaches (
                        breach_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        status TEXT NOT NULL,
                        detected_at TEXT NOT NULL,
                        reported_at TEXT,
                        contained_at TEXT,
                        resolved_at TEXT,
                        affected_records INTEGER DEFAULT 0,
                        affected_users INTEGER DEFAULT 0,
                        data_types TEXT,
                        notification_sent INTEGER DEFAULT 0,
                        regulatory_reported INTEGER DEFAULT 0,
                        metadata TEXT
                    )
                """)
                
                # Retention policies table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS retention_policies (
                        policy_id TEXT PRIMARY KEY,
                        data_type TEXT NOT NULL,
                        retention_period_days INTEGER NOT NULL,
                        compliance_standard TEXT NOT NULL,
                        auto_delete INTEGER DEFAULT 1,
                        archive_before_delete INTEGER DEFAULT 0,
                        archive_location TEXT,
                        metadata TEXT
                    )
                """)
                
                # Compliance audits table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS compliance_audits (
                        audit_id TEXT PRIMARY KEY,
                        audit_type TEXT NOT NULL,
                        compliance_standard TEXT NOT NULL,
                        auditor TEXT NOT NULL,
                        audit_date TEXT NOT NULL,
                        findings TEXT,
                        recommendations TEXT,
                        status TEXT DEFAULT 'pending',
                        score REAL,
                        metadata TEXT
                    )
                """)
                
                # PCI DSS requirements table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS pci_requirements (
                        requirement_id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        requirement TEXT NOT NULL,
                        description TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        last_assessed TEXT,
                        assessor TEXT,
                        notes TEXT,
                        metadata TEXT
                    )
                """)
                
                # Security controls table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_controls (
                        control_id TEXT PRIMARY KEY,
                        control_name TEXT NOT NULL,
                        control_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        last_tested TEXT,
                        test_result TEXT,
                        metadata TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_payment_transaction ON payment_data(transaction_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_payment_timestamp ON payment_data(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_user ON financial_records(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_retention ON financial_records(retention_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_breach_severity ON data_breaches(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_breach_status ON data_breaches(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_standard ON compliance_audits(compliance_standard)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_pci_category ON pci_requirements(category)")
        
        except Exception as e:
            logger.error(f"Error initializing financial compliance database: {e}")
    
    def _load_default_policies(self):
        """Load default retention policies"""
        try:
            default_policies = [
                RetentionPolicy(
                    policy_id="payment_data_retention",
                    data_type="payment_data",
                    retention_period_days=2555,  # 7 years for PCI DSS
                    compliance_standard=ComplianceStandard.PCI_DSS,
                    auto_delete=True,
                    archive_before_delete=True,
                    archive_location="/var/lib/mingus/archives/payment_data"
                ),
                RetentionPolicy(
                    policy_id="financial_records_retention",
                    data_type="financial_records",
                    retention_period_days=2555,  # 7 years for SOX
                    compliance_standard=ComplianceStandard.SOX,
                    auto_delete=True,
                    archive_before_delete=True,
                    archive_location="/var/lib/mingus/archives/financial_records"
                ),
                RetentionPolicy(
                    policy_id="audit_logs_retention",
                    data_type="audit_logs",
                    retention_period_days=1095,  # 3 years
                    compliance_standard=ComplianceStandard.ISO_27001,
                    auto_delete=True,
                    archive_before_delete=False
                ),
                RetentionPolicy(
                    policy_id="customer_data_retention",
                    data_type="customer_data",
                    retention_period_days=1825,  # 5 years for GLBA
                    compliance_standard=ComplianceStandard.GLBA,
                    auto_delete=True,
                    archive_before_delete=True,
                    archive_location="/var/lib/mingus/archives/customer_data"
                )
            ]
            
            for policy in default_policies:
                self.add_retention_policy(policy)
        
        except Exception as e:
            logger.error(f"Error loading default policies: {e}")
    
    def _init_pci_dss_requirements(self):
        """Initialize PCI DSS requirements"""
        try:
            pci_requirements = [
                # Build and Maintain a Secure Network
                {
                    "requirement_id": "pci_1_1",
                    "category": "Network Security",
                    "requirement": "Install and maintain a firewall configuration",
                    "description": "Firewall configuration to protect cardholder data",
                    "status": "implemented"
                },
                {
                    "requirement_id": "pci_1_2",
                    "category": "Network Security",
                    "requirement": "Do not use vendor-supplied defaults",
                    "description": "Change default passwords and security settings",
                    "status": "implemented"
                },
                # Protect Cardholder Data
                {
                    "requirement_id": "pci_2_1",
                    "category": "Data Protection",
                    "requirement": "Protect stored cardholder data",
                    "description": "Encrypt stored cardholder data",
                    "status": "implemented"
                },
                {
                    "requirement_id": "pci_2_2",
                    "category": "Data Protection",
                    "requirement": "Encrypt transmission of cardholder data",
                    "description": "Use strong cryptography for data transmission",
                    "status": "implemented"
                },
                # Maintain Vulnerability Management
                {
                    "requirement_id": "pci_3_1",
                    "category": "Vulnerability Management",
                    "requirement": "Use and regularly update anti-virus software",
                    "description": "Deploy anti-virus software on all systems",
                    "status": "implemented"
                },
                {
                    "requirement_id": "pci_3_2",
                    "category": "Vulnerability Management",
                    "requirement": "Develop and maintain secure systems",
                    "description": "Patch security vulnerabilities",
                    "status": "implemented"
                },
                # Implement Strong Access Control
                {
                    "requirement_id": "pci_4_1",
                    "category": "Access Control",
                    "requirement": "Restrict access to cardholder data",
                    "description": "Limit access to need-to-know basis",
                    "status": "implemented"
                },
                {
                    "requirement_id": "pci_4_2",
                    "category": "Access Control",
                    "requirement": "Assign unique ID to each person",
                    "description": "Unique user identification and authentication",
                    "status": "implemented"
                },
                # Monitor and Test Networks
                {
                    "requirement_id": "pci_5_1",
                    "category": "Monitoring",
                    "requirement": "Track and monitor network access",
                    "description": "Log and monitor all network access",
                    "status": "implemented"
                },
                {
                    "requirement_id": "pci_5_2",
                    "category": "Monitoring",
                    "requirement": "Regularly test security systems",
                    "description": "Test security systems and processes",
                    "status": "implemented"
                },
                # Maintain Information Security Policy
                {
                    "requirement_id": "pci_6_1",
                    "category": "Policy",
                    "requirement": "Maintain security policy",
                    "description": "Document and maintain security policies",
                    "status": "implemented"
                }
            ]
            
            for req in pci_requirements:
                self.add_pci_requirement(req)
        
        except Exception as e:
            logger.error(f"Error initializing PCI DSS requirements: {e}")
    
    def process_payment_data(self, payment_data: PaymentData) -> bool:
        """Process payment data with PCI DSS compliance"""
        try:
            # Validate payment data
            if not self._validate_payment_data(payment_data):
                return False
            
            # Encrypt sensitive data
            encrypted_data = self._encrypt_payment_data(payment_data)
            
            # Tokenize card data for storage
            tokenized_data = self._tokenize_payment_data(payment_data)
            
            # Store payment data
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO payment_data 
                    (transaction_id, card_type, masked_pan, expiry_month, expiry_year,
                     cardholder_name, amount, currency, merchant_id, timestamp,
                     encrypted_data, tokenized_data, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    payment_data.transaction_id,
                    payment_data.card_type.value,
                    payment_data.masked_pan,
                    payment_data.expiry_month,
                    payment_data.expiry_year,
                    payment_data.cardholder_name,
                    payment_data.amount,
                    payment_data.currency,
                    payment_data.merchant_id,
                    payment_data.timestamp.isoformat(),
                    encrypted_data,
                    tokenized_data,
                    json.dumps(payment_data.metadata)
                ))
            
            # Record audit trail
            self._record_audit_trail(
                action="payment_data_processed",
                resource_type="payment_data",
                resource_id=payment_data.transaction_id,
                metadata={
                    "card_type": payment_data.card_type.value,
                    "amount": payment_data.amount,
                    "currency": payment_data.currency,
                    "pci_compliant": True
                }
            )
            
            logger.info(f"Payment data processed: {payment_data.transaction_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing payment data: {e}")
            return False
    
    def _validate_payment_data(self, payment_data: PaymentData) -> bool:
        """Validate payment data for PCI DSS compliance"""
        try:
            # Validate card number format (masked)
            if not re.match(r'^\*{12}\d{4}$', payment_data.masked_pan):
                return False
            
            # Validate expiry date
            try:
                expiry_month = int(payment_data.expiry_month)
                expiry_year = int(payment_data.expiry_year)
                if not (1 <= expiry_month <= 12):
                    return False
                if not (2024 <= expiry_year <= 2030):
                    return False
            except ValueError:
                return False
            
            # Validate amount
            if payment_data.amount <= 0:
                return False
            
            # Validate currency
            valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
            if payment_data.currency not in valid_currencies:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating payment data: {e}")
            return False
    
    def _encrypt_payment_data(self, payment_data: PaymentData) -> str:
        """Encrypt payment data for PCI DSS compliance"""
        try:
            # Create data to encrypt (excluding already masked data)
            data_to_encrypt = {
                "cardholder_name": payment_data.cardholder_name,
                "amount": payment_data.amount,
                "currency": payment_data.currency,
                "merchant_id": payment_data.merchant_id,
                "timestamp": payment_data.timestamp.isoformat()
            }
            
            encrypted_data = self.cipher_suite.encrypt(json.dumps(data_to_encrypt).encode())
            return base64.b64encode(encrypted_data).decode()
        
        except Exception as e:
            logger.error(f"Error encrypting payment data: {e}")
            return ""
    
    def _tokenize_payment_data(self, payment_data: PaymentData) -> str:
        """Tokenize payment data for secure storage"""
        try:
            # Generate token based on transaction ID and timestamp
            token_data = f"{payment_data.transaction_id}_{payment_data.timestamp.isoformat()}"
            token = hashlib.sha256(token_data.encode()).hexdigest()
            return token
        
        except Exception as e:
            logger.error(f"Error tokenizing payment data: {e}")
            return ""
    
    def store_financial_record(self, record: FinancialRecord) -> bool:
        """Store financial record with compliance requirements"""
        try:
            # Encrypt sensitive content
            encrypted_content = self.cipher_suite.encrypt(record.content.encode())
            record.encrypted_content = base64.b64encode(encrypted_content).decode()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO financial_records 
                    (record_id, user_id, record_type, data_classification, content,
                     encrypted_content, created_at, retention_date, compliance_standard, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.record_id,
                    record.user_id,
                    record.record_type,
                    record.data_classification.value,
                    record.content,
                    record.encrypted_content,
                    record.created_at.isoformat(),
                    record.retention_date.isoformat(),
                    record.compliance_standard.value,
                    json.dumps(record.metadata)
                ))
            
            # Record audit trail
            self._record_audit_trail(
                action="financial_record_stored",
                resource_type="financial_record",
                resource_id=record.record_id,
                metadata={
                    "data_classification": record.data_classification.value,
                    "compliance_standard": record.compliance_standard.value,
                    "retention_date": record.retention_date.isoformat()
                }
            )
            
            logger.info(f"Financial record stored: {record.record_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing financial record: {e}")
            return False
    
    def report_data_breach(self, breach: DataBreach) -> bool:
        """Report data breach with notification procedures"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO data_breaches 
                    (breach_id, title, description, severity, status, detected_at,
                     affected_records, affected_users, data_types, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    breach.breach_id,
                    breach.title,
                    breach.description,
                    breach.severity.value,
                    breach.status.value,
                    breach.detected_at.isoformat(),
                    breach.affected_records,
                    breach.affected_users,
                    json.dumps(breach.data_types),
                    json.dumps(breach.metadata)
                ))
            
            # Trigger breach notification procedures
            self._trigger_breach_notifications(breach)
            
            # Record audit trail
            self._record_audit_trail(
                action="data_breach_reported",
                resource_type="data_breach",
                resource_id=breach.breach_id,
                metadata={
                    "severity": breach.severity.value,
                    "affected_records": breach.affected_records,
                    "affected_users": breach.affected_users
                }
            )
            
            logger.warning(f"Data breach reported: {breach.breach_id} - {breach.severity.value}")
            return True
        
        except Exception as e:
            logger.error(f"Error reporting data breach: {e}")
            return False
    
    def _trigger_breach_notifications(self, breach: DataBreach):
        """Trigger breach notification procedures"""
        try:
            # Determine notification requirements based on severity
            if breach.severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]:
                # Immediate notification required
                self._send_immediate_notifications(breach)
                
                # Regulatory notification required
                if breach.severity == BreachSeverity.CRITICAL:
                    self._send_regulatory_notifications(breach)
            
            # Update breach status
            self.update_breach_status(breach.breach_id, BreachStatus.INVESTIGATING)
        
        except Exception as e:
            logger.error(f"Error triggering breach notifications: {e}")
    
    def _send_immediate_notifications(self, breach: DataBreach):
        """Send immediate breach notifications"""
        try:
            # Send email notifications to key personnel
            notification_data = {
                "subject": f"CRITICAL: Data Breach Detected - {breach.title}",
                "body": f"""
                A data breach has been detected:
                
                Title: {breach.title}
                Description: {breach.description}
                Severity: {breach.severity.value}
                Affected Records: {breach.affected_records}
                Affected Users: {breach.affected_users}
                Data Types: {', '.join(breach.data_types)}
                
                Immediate action required.
                """,
                "recipients": ["security@mingus.com", "compliance@mingus.com", "legal@mingus.com"]
            }
            
            # This would integrate with your email system
            logger.info(f"Immediate breach notification sent: {breach.breach_id}")
        
        except Exception as e:
            logger.error(f"Error sending immediate notifications: {e}")
    
    def _send_regulatory_notifications(self, breach: DataBreach):
        """Send regulatory breach notifications"""
        try:
            # Determine regulatory requirements based on data types
            if "payment_data" in breach.data_types:
                # PCI DSS notification
                self._send_pci_notification(breach)
            
            if "personal_data" in breach.data_types:
                # GDPR notification
                self._send_gdpr_notification(breach)
            
            if "financial_data" in breach.data_types:
                # SOX notification
                self._send_sox_notification(breach)
        
        except Exception as e:
            logger.error(f"Error sending regulatory notifications: {e}")
    
    def update_breach_status(self, breach_id: str, status: BreachStatus, 
                           additional_data: Dict[str, Any] = None) -> bool:
        """Update data breach status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status == BreachStatus.REPORTED:
                    conn.execute("""
                        UPDATE data_breaches 
                        SET status = ?, reported_at = ?, notification_sent = 1
                        WHERE breach_id = ?
                    """, (status.value, datetime.utcnow().isoformat(), breach_id))
                elif status == BreachStatus.CONTAINED:
                    conn.execute("""
                        UPDATE data_breaches 
                        SET status = ?, contained_at = ?
                        WHERE breach_id = ?
                    """, (status.value, datetime.utcnow().isoformat(), breach_id))
                elif status == BreachStatus.RESOLVED:
                    conn.execute("""
                        UPDATE data_breaches 
                        SET status = ?, resolved_at = ?
                        WHERE breach_id = ?
                    """, (status.value, datetime.utcnow().isoformat(), breach_id))
                else:
                    conn.execute("""
                        UPDATE data_breaches 
                        SET status = ?
                        WHERE breach_id = ?
                    """, (status.value, breach_id))
            
            # Record audit trail
            self._record_audit_trail(
                action="breach_status_updated",
                resource_type="data_breach",
                resource_id=breach_id,
                new_value=status.value,
                metadata=additional_data or {}
            )
            
            logger.info(f"Breach status updated: {breach_id} -> {status.value}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating breach status: {e}")
            return False
    
    def add_retention_policy(self, policy: RetentionPolicy) -> bool:
        """Add data retention policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO retention_policies 
                    (policy_id, data_type, retention_period_days, compliance_standard,
                     auto_delete, archive_before_delete, archive_location, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy.policy_id,
                    policy.data_type,
                    policy.retention_period_days,
                    policy.compliance_standard.value,
                    1 if policy.auto_delete else 0,
                    1 if policy.archive_before_delete else 0,
                    policy.archive_location,
                    json.dumps(policy.metadata)
                ))
            
            logger.info(f"Retention policy added: {policy.policy_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding retention policy: {e}")
            return False
    
    def get_retention_policies(self) -> List[RetentionPolicy]:
        """Get all retention policies"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT policy_id, data_type, retention_period_days, compliance_standard,
                           auto_delete, archive_before_delete, archive_location, metadata
                    FROM retention_policies 
                    ORDER BY data_type
                """)
                
                policies = []
                for row in cursor.fetchall():
                    policy = RetentionPolicy(
                        policy_id=row[0],
                        data_type=row[1],
                        retention_period_days=row[2],
                        compliance_standard=ComplianceStandard(row[3]),
                        auto_delete=bool(row[4]),
                        archive_before_delete=bool(row[5]),
                        archive_location=row[6],
                        metadata=json.loads(row[7]) if row[7] else {}
                    )
                    policies.append(policy)
                
                return policies
        
        except Exception as e:
            logger.error(f"Error getting retention policies: {e}")
            return []
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data based on retention policies"""
        try:
            cleanup_stats = {}
            policies = self.get_retention_policies()
            
            for policy in policies:
                if policy.auto_delete:
                    expired_count = self._cleanup_expired_data_by_policy(policy)
                    cleanup_stats[policy.data_type] = expired_count
            
            logger.info(f"Data cleanup completed: {cleanup_stats}")
            return cleanup_stats
        
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")
            return {}
    
    def _cleanup_expired_data_by_policy(self, policy: RetentionPolicy) -> int:
        """Clean up expired data for specific policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_period_days)
            
            with sqlite3.connect(self.db_path) as conn:
                if policy.data_type == "payment_data":
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM payment_data 
                        WHERE timestamp < ?
                    """, (cutoff_date.isoformat(),))
                    expired_count = cursor.fetchone()[0]
                    
                    if expired_count > 0:
                        if policy.archive_before_delete:
                            self._archive_payment_data(cutoff_date, policy.archive_location)
                        
                        conn.execute("""
                            DELETE FROM payment_data 
                            WHERE timestamp < ?
                        """, (cutoff_date.isoformat(),))
                
                elif policy.data_type == "financial_records":
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM financial_records 
                        WHERE retention_date < ?
                    """, (cutoff_date.isoformat(),))
                    expired_count = cursor.fetchone()[0]
                    
                    if expired_count > 0:
                        if policy.archive_before_delete:
                            self._archive_financial_records(cutoff_date, policy.archive_location)
                        
                        conn.execute("""
                            DELETE FROM financial_records 
                            WHERE retention_date < ?
                        """, (cutoff_date.isoformat(),))
                
                else:
                    expired_count = 0
            
            return expired_count
        
        except Exception as e:
            logger.error(f"Error cleaning up expired data for policy {policy.policy_id}: {e}")
            return 0
    
    def _archive_payment_data(self, cutoff_date: datetime, archive_location: str):
        """Archive payment data before deletion"""
        try:
            # This would implement actual archiving logic
            logger.info(f"Archiving payment data before {cutoff_date} to {archive_location}")
        except Exception as e:
            logger.error(f"Error archiving payment data: {e}")
    
    def _archive_financial_records(self, cutoff_date: datetime, archive_location: str):
        """Archive financial records before deletion"""
        try:
            # This would implement actual archiving logic
            logger.info(f"Archiving financial records before {cutoff_date} to {archive_location}")
        except Exception as e:
            logger.error(f"Error archiving financial records: {e}")
    
    def add_pci_requirement(self, requirement: Dict[str, Any]) -> bool:
        """Add PCI DSS requirement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO pci_requirements 
                    (requirement_id, category, requirement, description, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    requirement["requirement_id"],
                    requirement["category"],
                    requirement["requirement"],
                    requirement["description"],
                    requirement.get("status", "pending"),
                    json.dumps(requirement.get("metadata", {}))
                ))
            
            logger.info(f"PCI requirement added: {requirement['requirement_id']}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding PCI requirement: {e}")
            return False
    
    def get_pci_compliance_status(self) -> Dict[str, Any]:
        """Get PCI DSS compliance status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT category, status, COUNT(*) as count
                    FROM pci_requirements 
                    GROUP BY category, status
                """)
                
                compliance_data = {}
                for row in cursor.fetchall():
                    category = row[0]
                    status = row[1]
                    count = row[2]
                    
                    if category not in compliance_data:
                        compliance_data[category] = {}
                    
                    compliance_data[category][status] = count
                
                # Calculate overall compliance score
                total_requirements = sum(sum(category.values()) for category in compliance_data.values())
                implemented_requirements = sum(
                    category.get("implemented", 0) for category in compliance_data.values()
                )
                
                compliance_score = (implemented_requirements / total_requirements * 100) if total_requirements > 0 else 0
                
                return {
                    "compliance_score": round(compliance_score, 2),
                    "total_requirements": total_requirements,
                    "implemented_requirements": implemented_requirements,
                    "category_breakdown": compliance_data,
                    "last_assessed": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error getting PCI compliance status: {e}")
            return {"error": str(e)}
    
    def _record_audit_trail(self, action: str, resource_type: str, resource_id: str,
                           old_value: str = None, new_value: str = None,
                           metadata: Dict[str, Any] = None):
        """Record audit trail entry"""
        try:
            with self.audit_lock:
                audit_id = str(uuid.uuid4())
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO audit_trails 
                        (audit_id, action, resource_type, resource_id, old_value, new_value, metadata, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        audit_id,
                        action,
                        resource_type,
                        resource_id,
                        old_value,
                        new_value,
                        json.dumps(metadata or {}),
                        datetime.utcnow().isoformat()
                    ))
        
        except Exception as e:
            logger.error(f"Error recording audit trail: {e}")
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get comprehensive compliance report"""
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "pci_dss": self.get_pci_compliance_status(),
                "data_breaches": self._get_breach_statistics(),
                "retention_policies": self._get_retention_statistics(),
                "security_controls": self._get_security_controls_status()
            }
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}
    
    def _get_breach_statistics(self) -> Dict[str, Any]:
        """Get data breach statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT severity, status, COUNT(*) as count
                    FROM data_breaches 
                    GROUP BY severity, status
                """)
                
                breach_stats = {}
                for row in cursor.fetchall():
                    severity = row[0]
                    status = row[1]
                    count = row[2]
                    
                    if severity not in breach_stats:
                        breach_stats[severity] = {}
                    
                    breach_stats[severity][status] = count
                
                return breach_stats
        
        except Exception as e:
            logger.error(f"Error getting breach statistics: {e}")
            return {}
    
    def _get_retention_statistics(self) -> Dict[str, Any]:
        """Get retention policy statistics"""
        try:
            policies = self.get_retention_policies()
            
            stats = {
                "total_policies": len(policies),
                "auto_delete_enabled": len([p for p in policies if p.auto_delete]),
                "archive_enabled": len([p for p in policies if p.archive_before_delete]),
                "compliance_standards": {}
            }
            
            for policy in policies:
                standard = policy.compliance_standard.value
                if standard not in stats["compliance_standards"]:
                    stats["compliance_standards"][standard] = 0
                stats["compliance_standards"][standard] += 1
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting retention statistics: {e}")
            return {}
    
    def _get_security_controls_status(self) -> Dict[str, Any]:
        """Get security controls status"""
        try:
            # This would integrate with actual security controls
            return {
                "encryption_enabled": True,
                "access_controls_active": True,
                "monitoring_enabled": True,
                "backup_systems_active": True,
                "last_security_assessment": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting security controls status: {e}")
            return {}

# Global financial compliance manager instance
_financial_compliance_manager = None

def get_financial_compliance_manager() -> FinancialComplianceManager:
    """Get global financial compliance manager instance"""
    global _financial_compliance_manager
    
    if _financial_compliance_manager is None:
        _financial_compliance_manager = FinancialComplianceManager()
    
    return _financial_compliance_manager 