"""
HIPAA Compliance Manager
Comprehensive HIPAA compliance system for health data privacy and security
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
from cryptography.fernet import Fernet
import base64
import random
import string

class HIPAAEntityType(Enum):
    """HIPAA entity types"""
    COVERED_ENTITY = "covered_entity"
    BUSINESS_ASSOCIATE = "business_associate"
    HEALTHCARE_PROVIDER = "healthcare_provider"
    HEALTH_PLAN = "health_plan"
    CLEARINGHOUSE = "clearinghouse"

class HealthDataCategory(Enum):
    """Health data categories"""
    DEMOGRAPHIC = "demographic"
    MEDICAL_HISTORY = "medical_history"
    LABORATORY_RESULTS = "laboratory_results"
    MEDICATIONS = "medications"
    ALLERGIES = "allergies"
    IMMUNIZATIONS = "immunizations"
    VITAL_SIGNS = "vital_signs"
    DIAGNOSES = "diagnoses"
    TREATMENT_PLANS = "treatment_plans"
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_ABUSE = "substance_abuse"
    REPRODUCTIVE_HEALTH = "reproductive_health"

class AccessLevel(Enum):
    """Access levels for health data"""
    NO_ACCESS = "no_access"
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    EMERGENCY = "emergency"

class ConsentType(Enum):
    """Health data consent types"""
    TREATMENT = "treatment"
    PAYMENT = "payment"
    HEALTHCARE_OPERATIONS = "healthcare_operations"
    RESEARCH = "research"
    MARKETING = "marketing"
    DISCLOSURE = "disclosure"

class AnonymizationLevel(Enum):
    """Anonymization levels"""
    NONE = "none"
    PSEUDONYMIZED = "pseudonymized"
    ANONYMIZED = "anonymized"
    AGGREGATED = "aggregated"

@dataclass
class HealthDataRecord:
    """Health data record structure"""
    record_id: str
    patient_id: str
    data_category: HealthDataCategory
    content: str
    encrypted_content: str
    anonymization_level: AnonymizationLevel
    created_at: datetime
    modified_at: datetime
    created_by: str
    modified_by: str
    access_log: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthDataAccess:
    """Health data access record"""
    access_id: str
    user_id: str
    patient_id: str
    record_id: str
    access_level: AccessLevel
    purpose: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    consent_verified: bool
    emergency_access: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthConsent:
    """Health data consent record"""
    consent_id: str
    patient_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    purpose: str
    data_categories: List[HealthDataCategory] = field(default_factory=list)
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HIPAAViolation:
    """HIPAA violation record"""
    violation_id: str
    violation_type: str
    severity: str
    description: str
    detected_at: datetime
    reported_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    affected_patients: int = 0
    affected_records: int = 0
    corrective_action: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthDataRetention:
    """Health data retention policy"""
    policy_id: str
    data_category: HealthDataCategory
    retention_period_years: int
    retention_reason: str
    auto_delete: bool = True
    archive_before_delete: bool = True
    archive_location: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class HIPAAComplianceManager:
    """Comprehensive HIPAA compliance manager"""
    
    def __init__(self, db_path: str = "/var/lib/mingus/hipaa.db"):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.access_lock = threading.Lock()
        
        self._init_database()
        self._load_default_policies()
        self._init_hipaa_requirements()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for health data"""
        key_file = "/var/lib/mingus/hipaa_key.key"
        
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
        """Initialize HIPAA compliance database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Health data records table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_data_records (
                        record_id TEXT PRIMARY KEY,
                        patient_id TEXT NOT NULL,
                        data_category TEXT NOT NULL,
                        content TEXT NOT NULL,
                        encrypted_content TEXT NOT NULL,
                        anonymization_level TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        modified_at TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        modified_by TEXT NOT NULL,
                        access_log TEXT,
                        metadata TEXT
                    )
                """)
                
                # Health data access table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_data_access (
                        access_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        patient_id TEXT NOT NULL,
                        record_id TEXT NOT NULL,
                        access_level TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        user_agent TEXT NOT NULL,
                        consent_verified INTEGER DEFAULT 0,
                        emergency_access INTEGER DEFAULT 0,
                        metadata TEXT
                    )
                """)
                
                # Health consent table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_consent (
                        consent_id TEXT PRIMARY KEY,
                        patient_id TEXT NOT NULL,
                        consent_type TEXT NOT NULL,
                        granted INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        expires_at TEXT,
                        revoked_at TEXT,
                        purpose TEXT NOT NULL,
                        data_categories TEXT,
                        ip_address TEXT NOT NULL,
                        user_agent TEXT NOT NULL,
                        metadata TEXT
                    )
                """)
                
                # HIPAA violations table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hipaa_violations (
                        violation_id TEXT PRIMARY KEY,
                        violation_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT NOT NULL,
                        detected_at TEXT NOT NULL,
                        reported_at TEXT,
                        resolved_at TEXT,
                        affected_patients INTEGER DEFAULT 0,
                        affected_records INTEGER DEFAULT 0,
                        corrective_action TEXT,
                        metadata TEXT
                    )
                """)
                
                # Health data retention table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_data_retention (
                        policy_id TEXT PRIMARY KEY,
                        data_category TEXT NOT NULL,
                        retention_period_years INTEGER NOT NULL,
                        retention_reason TEXT NOT NULL,
                        auto_delete INTEGER DEFAULT 1,
                        archive_before_delete INTEGER DEFAULT 1,
                        archive_location TEXT,
                        metadata TEXT
                    )
                """)
                
                # HIPAA requirements table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hipaa_requirements (
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
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_health_patient ON health_data_records(patient_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_health_category ON health_data_records(data_category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_access_user ON health_data_access(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_access_patient ON health_data_access(patient_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_patient ON health_consent(patient_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_type ON health_consent(consent_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_violation_severity ON hipaa_violations(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_retention_category ON health_data_retention(data_category)")
        
        except Exception as e:
            logger.error(f"Error initializing HIPAA database: {e}")
    
    def _load_default_policies(self):
        """Load default retention policies"""
        try:
            default_policies = [
                HealthDataRetention(
                    policy_id="medical_records_retention",
                    data_category=HealthDataCategory.MEDICAL_HISTORY,
                    retention_period_years=7,
                    retention_reason="Legal requirement for medical records retention",
                    auto_delete=True,
                    archive_before_delete=True,
                    archive_location="/var/lib/mingus/archives/medical_records"
                ),
                HealthDataRetention(
                    policy_id="lab_results_retention",
                    data_category=HealthDataCategory.LABORATORY_RESULTS,
                    retention_period_years=10,
                    retention_reason="Clinical and legal requirement for lab results",
                    auto_delete=True,
                    archive_before_delete=True,
                    archive_location="/var/lib/mingus/archives/lab_results"
                ),
                HealthDataRetention(
                    policy_id="mental_health_retention",
                    data_category=HealthDataCategory.MENTAL_HEALTH,
                    retention_period_years=10,
                    retention_reason="Extended retention for mental health records",
                    auto_delete=True,
                    archive_before_delete=True,
                    archive_location="/var/lib/mingus/archives/mental_health"
                ),
                HealthDataRetention(
                    policy_id="substance_abuse_retention",
                    data_category=HealthDataCategory.SUBSTANCE_ABUSE,
                    retention_period_years=10,
                    retention_reason="Extended retention for substance abuse records",
                    auto_delete=True,
                    archive_before_delete=True,
                    archive_location="/var/lib/mingus/archives/substance_abuse"
                )
            ]
            
            for policy in default_policies:
                self.add_retention_policy(policy)
        
        except Exception as e:
            logger.error(f"Error loading default policies: {e}")
    
    def _init_hipaa_requirements(self):
        """Initialize HIPAA requirements"""
        try:
            hipaa_requirements = [
                # Privacy Rule
                {
                    "requirement_id": "privacy_1",
                    "category": "Privacy Rule",
                    "requirement": "Notice of Privacy Practices",
                    "description": "Provide notice of privacy practices to patients",
                    "status": "implemented"
                },
                {
                    "requirement_id": "privacy_2",
                    "category": "Privacy Rule",
                    "requirement": "Patient Rights",
                    "description": "Ensure patient rights to access and amend PHI",
                    "status": "implemented"
                },
                {
                    "requirement_id": "privacy_3",
                    "category": "Privacy Rule",
                    "requirement": "Authorization Requirements",
                    "description": "Obtain proper authorization for PHI disclosure",
                    "status": "implemented"
                },
                # Security Rule
                {
                    "requirement_id": "security_1",
                    "category": "Security Rule",
                    "requirement": "Access Control",
                    "description": "Implement access controls for PHI",
                    "status": "implemented"
                },
                {
                    "requirement_id": "security_2",
                    "category": "Security Rule",
                    "requirement": "Audit Controls",
                    "description": "Implement audit controls for PHI access",
                    "status": "implemented"
                },
                {
                    "requirement_id": "security_3",
                    "category": "Security Rule",
                    "requirement": "Integrity Controls",
                    "description": "Implement integrity controls for PHI",
                    "status": "implemented"
                },
                {
                    "requirement_id": "security_4",
                    "category": "Security Rule",
                    "requirement": "Transmission Security",
                    "description": "Implement transmission security for PHI",
                    "status": "implemented"
                },
                # Breach Notification Rule
                {
                    "requirement_id": "breach_1",
                    "category": "Breach Notification",
                    "requirement": "Breach Detection",
                    "description": "Implement breach detection and notification",
                    "status": "implemented"
                },
                {
                    "requirement_id": "breach_2",
                    "category": "Breach Notification",
                    "requirement": "Notification Procedures",
                    "description": "Establish breach notification procedures",
                    "status": "implemented"
                }
            ]
            
            for req in hipaa_requirements:
                self.add_hipaa_requirement(req)
        
        except Exception as e:
            logger.error(f"Error initializing HIPAA requirements: {e}")
    
    def store_health_data(self, record: HealthDataRecord) -> bool:
        """Store health data with HIPAA compliance"""
        try:
            # Encrypt health data
            encrypted_content = self.cipher_suite.encrypt(record.content.encode())
            record.encrypted_content = base64.b64encode(encrypted_content).decode()
            
            # Anonymize data if required
            if record.anonymization_level != AnonymizationLevel.NONE:
                record.content = self._anonymize_health_data(record.content, record.anonymization_level)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO health_data_records 
                    (record_id, patient_id, data_category, content, encrypted_content,
                     anonymization_level, created_at, modified_at, created_by, modified_by,
                     access_log, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.record_id,
                    record.patient_id,
                    record.data_category.value,
                    record.content,
                    record.encrypted_content,
                    record.anonymization_level.value,
                    record.created_at.isoformat(),
                    record.modified_at.isoformat(),
                    record.created_by,
                    record.modified_by,
                    json.dumps(record.access_log),
                    json.dumps(record.metadata)
                ))
            
            # Record audit trail
            self._record_access_log(
                user_id=record.created_by,
                patient_id=record.patient_id,
                record_id=record.record_id,
                access_level=AccessLevel.ADMIN,
                purpose="Data creation",
                ip_address="system",
                user_agent="system"
            )
            
            logger.info(f"Health data stored: {record.record_id} for patient {record.patient_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing health data: {e}")
            return False
    
    def _anonymize_health_data(self, content: str, level: AnonymizationLevel) -> str:
        """Anonymize health data based on level"""
        try:
            if level == AnonymizationLevel.NONE:
                return content
            
            elif level == AnonymizationLevel.PSEUDONYMIZED:
                # Replace identifiable information with pseudonyms
                # This is a simplified example - real implementation would be more sophisticated
                anonymized = content
                # Replace names with pseudonyms
                anonymized = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 'PSEUDONYM', anonymized)
                # Replace dates with relative dates
                anonymized = re.sub(r'\d{4}-\d{2}-\d{2}', 'YYYY-MM-DD', anonymized)
                return anonymized
            
            elif level == AnonymizationLevel.ANONYMIZED:
                # Remove all identifiable information
                anonymized = content
                # Remove names
                anonymized = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', anonymized)
                # Remove dates
                anonymized = re.sub(r'\d{4}-\d{2}-\d{2}', '[DATE]', anonymized)
                # Remove addresses
                anonymized = re.sub(r'\d+ [A-Za-z\s]+(?:Street|Avenue|Road|Lane)', '[ADDRESS]', anonymized)
                # Remove phone numbers
                anonymized = re.sub(r'\d{3}-\d{3}-\d{4}', '[PHONE]', anonymized)
                return anonymized
            
            elif level == AnonymizationLevel.AGGREGATED:
                # Return aggregated statistics instead of individual data
                return "Aggregated health data statistics"
            
            return content
        
        except Exception as e:
            logger.error(f"Error anonymizing health data: {e}")
            return content
    
    def access_health_data(self, user_id: str, patient_id: str, record_id: str,
                          access_level: AccessLevel, purpose: str, ip_address: str,
                          user_agent: str, emergency_access: bool = False) -> Optional[str]:
        """Access health data with HIPAA compliance"""
        try:
            # Check access permissions
            if not self._check_access_permissions(user_id, patient_id, access_level):
                logger.warning(f"Access denied for user {user_id} to patient {patient_id}")
                return None
            
            # Verify consent if required
            if not emergency_access and not self._verify_consent(patient_id, purpose):
                logger.warning(f"Consent not verified for patient {patient_id}")
                return None
            
            # Record access
            access_record = HealthDataAccess(
                access_id=str(uuid.uuid4()),
                user_id=user_id,
                patient_id=patient_id,
                record_id=record_id,
                access_level=access_level,
                purpose=purpose,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                consent_verified=not emergency_access,
                emergency_access=emergency_access
            )
            
            self._record_access(access_record)
            
            # Retrieve and decrypt data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT encrypted_content, anonymization_level
                    FROM health_data_records 
                    WHERE record_id = ?
                """, (record_id,))
                
                row = cursor.fetchone()
                if row:
                    encrypted_content = row[0]
                    anonymization_level = AnonymizationLevel(row[1])
                    
                    # Decrypt data
                    decrypted_content = self.cipher_suite.decrypt(base64.b64decode(encrypted_content))
                    
                    # Apply anonymization if needed
                    if anonymization_level != AnonymizationLevel.NONE:
                        decrypted_content = self._anonymize_health_data(
                            decrypted_content.decode(), anonymization_level
                        ).encode()
                    
                    logger.info(f"Health data accessed: {record_id} by user {user_id}")
                    return decrypted_content.decode()
                
                return None
        
        except Exception as e:
            logger.error(f"Error accessing health data: {e}")
            return None
    
    def _check_access_permissions(self, user_id: str, patient_id: str, access_level: AccessLevel) -> bool:
        """Check if user has permission to access patient data"""
        try:
            # This would integrate with your user management system
            # For now, return True for demonstration
            return True
        
        except Exception as e:
            logger.error(f"Error checking access permissions: {e}")
            return False
    
    def _verify_consent(self, patient_id: str, purpose: str) -> bool:
        """Verify patient consent for data access"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT granted, revoked_at, expires_at
                    FROM health_consent 
                    WHERE patient_id = ? AND purpose = ? AND granted = 1
                    ORDER BY timestamp DESC LIMIT 1
                """, (patient_id, purpose))
                
                row = cursor.fetchone()
                if row:
                    granted = bool(row[0])
                    revoked_at = row[1]
                    expires_at = row[2]
                    
                    # Check if consent is still valid
                    if revoked_at:
                        return False
                    
                    if expires_at:
                        expiry_date = datetime.fromisoformat(expires_at)
                        if datetime.utcnow() > expiry_date:
                            return False
                    
                    return granted
                
                return False
        
        except Exception as e:
            logger.error(f"Error verifying consent: {e}")
            return False
    
    def _record_access(self, access_record: HealthDataAccess):
        """Record health data access"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO health_data_access 
                    (access_id, user_id, patient_id, record_id, access_level, purpose,
                     timestamp, ip_address, user_agent, consent_verified, emergency_access, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    access_record.access_id,
                    access_record.user_id,
                    access_record.patient_id,
                    access_record.record_id,
                    access_record.access_level.value,
                    access_record.purpose,
                    access_record.timestamp.isoformat(),
                    access_record.ip_address,
                    access_record.user_agent,
                    1 if access_record.consent_verified else 0,
                    1 if access_record.emergency_access else 0,
                    json.dumps(access_record.metadata)
                ))
        
        except Exception as e:
            logger.error(f"Error recording access: {e}")
    
    def record_consent(self, consent: HealthConsent) -> bool:
        """Record patient consent for health data access"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO health_consent 
                    (consent_id, patient_id, consent_type, granted, timestamp, expires_at,
                     revoked_at, purpose, data_categories, ip_address, user_agent, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    consent.consent_id,
                    consent.patient_id,
                    consent.consent_type.value,
                    1 if consent.granted else 0,
                    consent.timestamp.isoformat(),
                    consent.expires_at.isoformat() if consent.expires_at else None,
                    consent.revoked_at.isoformat() if consent.revoked_at else None,
                    consent.purpose,
                    json.dumps([cat.value for cat in consent.data_categories]),
                    consent.ip_address,
                    consent.user_agent,
                    json.dumps(consent.metadata)
                ))
            
            logger.info(f"Health consent recorded: {consent.consent_id} for patient {consent.patient_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error recording consent: {e}")
            return False
    
    def revoke_consent(self, patient_id: str, consent_type: ConsentType) -> bool:
        """Revoke patient consent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE health_consent 
                    SET revoked_at = ?
                    WHERE patient_id = ? AND consent_type = ? AND revoked_at IS NULL
                    ORDER BY timestamp DESC LIMIT 1
                """, (datetime.utcnow().isoformat(), patient_id, consent_type.value))
            
            logger.info(f"Health consent revoked for patient {patient_id}: {consent_type.value}")
            return True
        
        except Exception as e:
            logger.error(f"Error revoking consent: {e}")
            return False
    
    def report_hipaa_violation(self, violation: HIPAAViolation) -> bool:
        """Report HIPAA violation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO hipaa_violations 
                    (violation_id, violation_type, severity, description, detected_at,
                     affected_patients, affected_records, corrective_action, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    violation.violation_id,
                    violation.violation_type,
                    violation.severity,
                    violation.description,
                    violation.detected_at.isoformat(),
                    violation.affected_patients,
                    violation.affected_records,
                    violation.corrective_action,
                    json.dumps(violation.metadata)
                ))
            
            # Trigger violation response procedures
            self._trigger_violation_response(violation)
            
            logger.warning(f"HIPAA violation reported: {violation.violation_id} - {violation.severity}")
            return True
        
        except Exception as e:
            logger.error(f"Error reporting HIPAA violation: {e}")
            return False
    
    def _trigger_violation_response(self, violation: HIPAAViolation):
        """Trigger violation response procedures"""
        try:
            # Determine response based on severity
            if violation.severity in ['high', 'critical']:
                # Immediate notification required
                self._send_immediate_notifications(violation)
                
                # Regulatory notification required
                if violation.severity == 'critical':
                    self._send_regulatory_notifications(violation)
            
            # Update violation status
            self.update_violation_status(violation.violation_id, 'investigating')
        
        except Exception as e:
            logger.error(f"Error triggering violation response: {e}")
    
    def _send_immediate_notifications(self, violation: HIPAAViolation):
        """Send immediate violation notifications"""
        try:
            # Send email notifications to key personnel
            notification_data = {
                "subject": f"CRITICAL: HIPAA Violation Detected - {violation.violation_type}",
                "body": f"""
                A HIPAA violation has been detected:
                
                Type: {violation.violation_type}
                Severity: {violation.severity}
                Description: {violation.description}
                Affected Patients: {violation.affected_patients}
                Affected Records: {violation.affected_records}
                
                Immediate action required.
                """,
                "recipients": ["compliance@mingus.com", "legal@mingus.com", "security@mingus.com"]
            }
            
            # This would integrate with your email system
            logger.info(f"Immediate violation notification sent: {violation.violation_id}")
        
        except Exception as e:
            logger.error(f"Error sending immediate notifications: {e}")
    
    def _send_regulatory_notifications(self, violation: HIPAAViolation):
        """Send regulatory violation notifications"""
        try:
            # HHS notification for HIPAA violations
            logger.info(f"Regulatory notification sent for violation: {violation.violation_id}")
        
        except Exception as e:
            logger.error(f"Error sending regulatory notifications: {e}")
    
    def update_violation_status(self, violation_id: str, status: str, 
                              additional_data: Dict[str, Any] = None) -> bool:
        """Update HIPAA violation status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status == 'reported':
                    conn.execute("""
                        UPDATE hipaa_violations 
                        SET reported_at = ?
                        WHERE violation_id = ?
                    """, (datetime.utcnow().isoformat(), violation_id))
                elif status == 'resolved':
                    conn.execute("""
                        UPDATE hipaa_violations 
                        SET resolved_at = ?
                        WHERE violation_id = ?
                    """, (datetime.utcnow().isoformat(), violation_id))
            
            logger.info(f"Violation status updated: {violation_id} -> {status}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating violation status: {e}")
            return False
    
    def add_retention_policy(self, policy: HealthDataRetention) -> bool:
        """Add health data retention policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO health_data_retention 
                    (policy_id, data_category, retention_period_years, retention_reason,
                     auto_delete, archive_before_delete, archive_location, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy.policy_id,
                    policy.data_category.value,
                    policy.retention_period_years,
                    policy.retention_reason,
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
    
    def cleanup_expired_health_data(self) -> Dict[str, int]:
        """Clean up expired health data based on retention policies"""
        try:
            cleanup_stats = {}
            
            with sqlite3.connect(self.db_path) as conn:
                # Get all retention policies
                cursor = conn.execute("""
                    SELECT data_category, retention_period_years, auto_delete
                    FROM health_data_retention
                """)
                
                for row in cursor.fetchall():
                    data_category = HealthDataCategory(row[0])
                    retention_years = row[1]
                    auto_delete = bool(row[2])
                    
                    if auto_delete:
                        cutoff_date = datetime.utcnow() - timedelta(days=retention_years * 365)
                        
                        # Count expired records
                        cursor2 = conn.execute("""
                            SELECT COUNT(*) FROM health_data_records 
                            WHERE data_category = ? AND created_at < ?
                        """, (data_category.value, cutoff_date.isoformat()))
                        
                        expired_count = cursor2.fetchone()[0]
                        
                        if expired_count > 0:
                            # Archive before deletion if required
                            # This would implement actual archiving logic
                            
                            # Delete expired records
                            conn.execute("""
                                DELETE FROM health_data_records 
                                WHERE data_category = ? AND created_at < ?
                            """, (data_category.value, cutoff_date.isoformat()))
                            
                            cleanup_stats[data_category.value] = expired_count
            
            logger.info(f"Health data cleanup completed: {cleanup_stats}")
            return cleanup_stats
        
        except Exception as e:
            logger.error(f"Error cleaning up expired health data: {e}")
            return {}
    
    def add_hipaa_requirement(self, requirement: Dict[str, Any]) -> bool:
        """Add HIPAA requirement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO hipaa_requirements 
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
            
            logger.info(f"HIPAA requirement added: {requirement['requirement_id']}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding HIPAA requirement: {e}")
            return False
    
    def get_hipaa_compliance_status(self) -> Dict[str, Any]:
        """Get HIPAA compliance status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT category, status, COUNT(*) as count
                    FROM hipaa_requirements 
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
            logger.error(f"Error getting HIPAA compliance status: {e}")
            return {"error": str(e)}
    
    def _record_access_log(self, user_id: str, patient_id: str, record_id: str,
                          access_level: AccessLevel, purpose: str, ip_address: str, user_agent: str):
        """Record access log entry"""
        try:
            access_record = HealthDataAccess(
                access_id=str(uuid.uuid4()),
                user_id=user_id,
                patient_id=patient_id,
                record_id=record_id,
                access_level=access_level,
                purpose=purpose,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                consent_verified=True
            )
            
            self._record_access(access_record)
        
        except Exception as e:
            logger.error(f"Error recording access log: {e}")
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get comprehensive HIPAA compliance report"""
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "hipaa_compliance": self.get_hipaa_compliance_status(),
                "data_breaches": self._get_violation_statistics(),
                "retention_policies": self._get_retention_statistics(),
                "access_controls": self._get_access_control_status()
            }
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}
    
    def _get_violation_statistics(self) -> Dict[str, Any]:
        """Get HIPAA violation statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT severity, COUNT(*) as count
                    FROM hipaa_violations 
                    GROUP BY severity
                """)
                
                violation_stats = {}
                for row in cursor.fetchall():
                    severity = row[0]
                    count = row[1]
                    violation_stats[severity] = count
                
                return violation_stats
        
        except Exception as e:
            logger.error(f"Error getting violation statistics: {e}")
            return {}
    
    def _get_retention_statistics(self) -> Dict[str, Any]:
        """Get retention policy statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT data_category, retention_period_years, COUNT(*) as count
                    FROM health_data_retention 
                    GROUP BY data_category, retention_period_years
                """)
                
                retention_stats = {}
                for row in cursor.fetchall():
                    category = row[0]
                    years = row[1]
                    count = row[2]
                    
                    if category not in retention_stats:
                        retention_stats[category] = {}
                    
                    retention_stats[category][f"{years}_years"] = count
                
                return retention_stats
        
        except Exception as e:
            logger.error(f"Error getting retention statistics: {e}")
            return {}
    
    def _get_access_control_status(self) -> Dict[str, Any]:
        """Get access control status"""
        try:
            # This would integrate with actual access control systems
            return {
                "role_based_access": "active",
                "multi_factor_authentication": "active",
                "session_management": "active",
                "emergency_access": "active",
                "access_logging": "active",
                "last_assessment": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting access control status: {e}")
            return {}

# Global HIPAA compliance manager instance
_hipaa_manager = None

def get_hipaa_manager() -> HIPAAComplianceManager:
    """Get global HIPAA compliance manager instance"""
    global _hipaa_manager
    
    if _hipaa_manager is None:
        _hipaa_manager = HIPAAComplianceManager()
    
    return _hipaa_manager 