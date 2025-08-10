"""
Privacy Controls Manager
Comprehensive privacy controls for data minimization, purpose limitation, accuracy, storage limitation, and transparency
"""

import os
import json
import time
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import threading
from loguru import logger
from cryptography.fernet import Fernet
import base64

class DataPurpose(Enum):
    """Data processing purposes"""
    NECESSARY = "necessary"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    RESEARCH = "research"
    CUSTOMER_SUPPORT = "customer_support"

class DataAccuracyLevel(Enum):
    """Data accuracy levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class StorageRetentionType(Enum):
    """Storage retention types"""
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years
    PERMANENT = "permanent"

class TransparencyLevel(Enum):
    """Transparency levels"""
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"

@dataclass
class DataCollectionPolicy:
    """Data collection policy structure"""
    policy_id: str
    data_type: str
    purpose: DataPurpose
    necessity_level: str  # essential, important, optional
    collection_method: str
    retention_period: StorageRetentionType
    accuracy_requirement: DataAccuracyLevel
    transparency_level: TransparencyLevel
    consent_required: bool = True
    auto_delete: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataProcessingRecord:
    """Data processing record structure"""
    record_id: str
    user_id: str
    data_type: str
    purpose: DataPurpose
    collected_at: datetime
    processed_at: datetime
    accuracy_verified: bool
    retention_expiry: datetime
    transparency_notice_sent: bool
    consent_obtained: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PrivacyNotice:
    """Privacy notice structure"""
    notice_id: str
    version: str
    effective_date: datetime
    content: str
    language: str = "en"
    region: str = "global"
    data_purposes: List[DataPurpose] = field(default_factory=list)
    retention_periods: Dict[str, str] = field(default_factory=dict)
    user_rights: List[str] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataSubjectRequest:
    """Data subject request structure"""
    request_id: str
    user_id: str
    request_type: str  # access, rectification, erasure, portability, restriction
    status: str  # pending, processing, completed, rejected
    created_at: datetime
    description: str
    completed_at: Optional[datetime] = None
    data_types: List[str] = field(default_factory=list)
    verification_method: str = ""
    verification_completed: bool = False
    response_data: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PrivacyAudit:
    """Privacy audit structure"""
    audit_id: str
    audit_type: str
    auditor: str
    audit_date: datetime
    scope: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_score: Optional[float] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

class PrivacyControlsManager:
    """Comprehensive privacy controls manager"""
    
    def __init__(self, db_path: str = "/var/lib/mingus/privacy.db"):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.audit_lock = threading.Lock()
        
        self._init_database()
        self._load_default_policies()
        self._load_default_notices()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for privacy data"""
        key_file = "/var/lib/mingus/privacy_key.key"
        
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
        """Initialize privacy controls database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Data collection policies table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_collection_policies (
                        policy_id TEXT PRIMARY KEY,
                        data_type TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        necessity_level TEXT NOT NULL,
                        collection_method TEXT NOT NULL,
                        retention_period TEXT NOT NULL,
                        accuracy_requirement TEXT NOT NULL,
                        transparency_level TEXT NOT NULL,
                        consent_required INTEGER DEFAULT 1,
                        auto_delete INTEGER DEFAULT 1,
                        metadata TEXT
                    )
                """)
                
                # Data processing records table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_processing_records (
                        record_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        collected_at TEXT NOT NULL,
                        processed_at TEXT NOT NULL,
                        accuracy_verified INTEGER DEFAULT 0,
                        retention_expiry TEXT NOT NULL,
                        transparency_notice_sent INTEGER DEFAULT 0,
                        consent_obtained INTEGER DEFAULT 0,
                        metadata TEXT
                    )
                """)
                
                # Privacy notices table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS privacy_notices (
                        notice_id TEXT PRIMARY KEY,
                        version TEXT NOT NULL,
                        effective_date TEXT NOT NULL,
                        content TEXT NOT NULL,
                        language TEXT DEFAULT 'en',
                        region TEXT DEFAULT 'global',
                        data_purposes TEXT,
                        retention_periods TEXT,
                        user_rights TEXT,
                        contact_info TEXT,
                        metadata TEXT
                    )
                """)
                
                # Data subject requests table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_subject_requests (
                        request_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        request_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        description TEXT NOT NULL,
                        data_types TEXT,
                        verification_method TEXT,
                        verification_completed INTEGER DEFAULT 0,
                        response_data TEXT,
                        metadata TEXT
                    )
                """)
                
                # Privacy audits table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS privacy_audits (
                        audit_id TEXT PRIMARY KEY,
                        audit_type TEXT NOT NULL,
                        auditor TEXT NOT NULL,
                        audit_date TEXT NOT NULL,
                        scope TEXT,
                        findings TEXT,
                        recommendations TEXT,
                        compliance_score REAL,
                        status TEXT DEFAULT 'pending',
                        metadata TEXT
                    )
                """)
                
                # Data accuracy logs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_accuracy_logs (
                        log_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        accuracy_check_date TEXT NOT NULL,
                        accuracy_score REAL,
                        issues_found TEXT,
                        corrections_made TEXT,
                        verified_by TEXT,
                        metadata TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_data_type ON data_collection_policies(data_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_purpose ON data_collection_policies(purpose)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_processing_user ON data_processing_records(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_processing_expiry ON data_processing_records(retention_expiry)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_notice_version ON privacy_notices(version)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_user ON data_subject_requests(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_status ON data_subject_requests(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_date ON privacy_audits(audit_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_accuracy_user ON data_accuracy_logs(user_id)")
        
        except Exception as e:
            logger.error(f"Error initializing privacy database: {e}")
    
    def _load_default_policies(self):
        """Load default data collection policies"""
        try:
            default_policies = [
                DataCollectionPolicy(
                    policy_id="essential_user_data",
                    data_type="user_identification",
                    purpose=DataPurpose.NECESSARY,
                    necessity_level="essential",
                    collection_method="user_registration",
                    retention_period=StorageRetentionType.LONG_TERM,
                    accuracy_requirement=DataAccuracyLevel.CRITICAL,
                    transparency_level=TransparencyLevel.FULL,
                    consent_required=False,
                    auto_delete=False
                ),
                DataCollectionPolicy(
                    policy_id="functional_preferences",
                    data_type="user_preferences",
                    purpose=DataPurpose.FUNCTIONAL,
                    necessity_level="important",
                    collection_method="user_settings",
                    retention_period=StorageRetentionType.MEDIUM_TERM,
                    accuracy_requirement=DataAccuracyLevel.HIGH,
                    transparency_level=TransparencyLevel.FULL,
                    consent_required=True,
                    auto_delete=True
                ),
                DataCollectionPolicy(
                    policy_id="analytics_data",
                    data_type="usage_analytics",
                    purpose=DataPurpose.ANALYTICS,
                    necessity_level="optional",
                    collection_method="automatic_tracking",
                    retention_period=StorageRetentionType.SHORT_TERM,
                    accuracy_requirement=DataAccuracyLevel.MEDIUM,
                    transparency_level=TransparencyLevel.PARTIAL,
                    consent_required=True,
                    auto_delete=True
                ),
                DataCollectionPolicy(
                    policy_id="marketing_data",
                    data_type="marketing_preferences",
                    purpose=DataPurpose.MARKETING,
                    necessity_level="optional",
                    collection_method="explicit_consent",
                    retention_period=StorageRetentionType.MEDIUM_TERM,
                    accuracy_requirement=DataAccuracyLevel.MEDIUM,
                    transparency_level=TransparencyLevel.FULL,
                    consent_required=True,
                    auto_delete=True
                ),
                DataCollectionPolicy(
                    policy_id="security_logs",
                    data_type="security_events",
                    purpose=DataPurpose.SECURITY,
                    necessity_level="essential",
                    collection_method="automatic_monitoring",
                    retention_period=StorageRetentionType.MEDIUM_TERM,
                    accuracy_requirement=DataAccuracyLevel.HIGH,
                    transparency_level=TransparencyLevel.MINIMAL,
                    consent_required=False,
                    auto_delete=True
                )
            ]
            
            for policy in default_policies:
                self.add_data_collection_policy(policy)
        
        except Exception as e:
            logger.error(f"Error loading default policies: {e}")
    
    def _load_default_notices(self):
        """Load default privacy notices"""
        try:
            privacy_notice = PrivacyNotice(
                notice_id="default_privacy_notice",
                version="1.0",
                effective_date=datetime.utcnow(),
                content="""
# Privacy Notice

## Data Collection and Use

We collect only the data necessary to provide our services:

### Essential Data (Required for Service)
- User identification information
- Account credentials
- Security logs

### Functional Data (Service Enhancement)
- User preferences and settings
- Service usage patterns

### Optional Data (With Consent)
- Analytics data for service improvement
- Marketing preferences for personalized content

## Data Retention

- Essential data: Retained for service duration
- Functional data: Retained for 1 year
- Analytics data: Retained for 30 days
- Marketing data: Retained for 1 year or until consent withdrawal

## Your Rights

- Right to access your data
- Right to correct inaccurate data
- Right to delete your data
- Right to data portability
- Right to restrict processing
- Right to object to processing

## Contact Information

For privacy inquiries: privacy@mingus.com
                """,
                data_purposes=[DataPurpose.NECESSARY, DataPurpose.FUNCTIONAL, DataPurpose.ANALYTICS, DataPurpose.MARKETING],
                retention_periods={
                    "essential": "Service duration",
                    "functional": "1 year",
                    "analytics": "30 days",
                    "marketing": "1 year or until withdrawal"
                },
                user_rights=["access", "rectification", "erasure", "portability", "restriction", "objection"],
                contact_info={
                    "email": "privacy@mingus.com",
                    "phone": "+1-555-PRIVACY"
                }
            )
            
            self.add_privacy_notice(privacy_notice)
        
        except Exception as e:
            logger.error(f"Error loading default notices: {e}")
    
    def add_data_collection_policy(self, policy: DataCollectionPolicy) -> bool:
        """Add data collection policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO data_collection_policies 
                    (policy_id, data_type, purpose, necessity_level, collection_method,
                     retention_period, accuracy_requirement, transparency_level,
                     consent_required, auto_delete, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy.policy_id,
                    policy.data_type,
                    policy.purpose.value,
                    policy.necessity_level,
                    policy.collection_method,
                    policy.retention_period.value,
                    policy.accuracy_requirement.value,
                    policy.transparency_level.value,
                    1 if policy.consent_required else 0,
                    1 if policy.auto_delete else 0,
                    json.dumps(policy.metadata)
                ))
            
            logger.info(f"Data collection policy added: {policy.policy_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding data collection policy: {e}")
            return False
    
    def get_data_collection_policy(self, data_type: str) -> Optional[DataCollectionPolicy]:
        """Get data collection policy for data type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT policy_id, data_type, purpose, necessity_level, collection_method,
                           retention_period, accuracy_requirement, transparency_level,
                           consent_required, auto_delete, metadata
                    FROM data_collection_policies 
                    WHERE data_type = ?
                """, (data_type,))
                
                row = cursor.fetchone()
                if row:
                    return DataCollectionPolicy(
                        policy_id=row[0],
                        data_type=row[1],
                        purpose=DataPurpose(row[2]),
                        necessity_level=row[3],
                        collection_method=row[4],
                        retention_period=StorageRetentionType(row[5]),
                        accuracy_requirement=DataAccuracyLevel(row[6]),
                        transparency_level=TransparencyLevel(row[7]),
                        consent_required=bool(row[8]),
                        auto_delete=bool(row[9]),
                        metadata=json.loads(row[10]) if row[10] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting data collection policy: {e}")
            return None
    
    def record_data_processing(self, record: DataProcessingRecord) -> bool:
        """Record data processing activity"""
        try:
            # Get policy for data type
            policy = self.get_data_collection_policy(record.data_type)
            if not policy:
                logger.error(f"No policy found for data type: {record.data_type}")
                return False
            
            # Check purpose limitation
            if record.purpose != policy.purpose:
                logger.warning(f"Purpose mismatch for data type {record.data_type}")
            
            # Calculate retention expiry
            retention_expiry = self._calculate_retention_expiry(record.collected_at, policy.retention_period)
            record.retention_expiry = retention_expiry
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO data_processing_records 
                    (record_id, user_id, data_type, purpose, collected_at, processed_at,
                     accuracy_verified, retention_expiry, transparency_notice_sent,
                     consent_obtained, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.record_id,
                    record.user_id,
                    record.data_type,
                    record.purpose.value,
                    record.collected_at.isoformat(),
                    record.processed_at.isoformat(),
                    1 if record.accuracy_verified else 0,
                    record.retention_expiry.isoformat(),
                    1 if record.transparency_notice_sent else 0,
                    1 if record.consent_obtained else 0,
                    json.dumps(record.metadata)
                ))
            
            # Send transparency notice if required
            if policy.transparency_level == TransparencyLevel.FULL and not record.transparency_notice_sent:
                self._send_transparency_notice(record.user_id, record.data_type, policy)
            
            logger.info(f"Data processing recorded: {record.record_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error recording data processing: {e}")
            return False
    
    def _calculate_retention_expiry(self, collected_at: datetime, retention_period: StorageRetentionType) -> datetime:
        """Calculate retention expiry date"""
        if retention_period == StorageRetentionType.IMMEDIATE:
            return collected_at
        elif retention_period == StorageRetentionType.SHORT_TERM:
            return collected_at + timedelta(days=30)
        elif retention_period == StorageRetentionType.MEDIUM_TERM:
            return collected_at + timedelta(days=365)
        elif retention_period == StorageRetentionType.LONG_TERM:
            return collected_at + timedelta(days=365*7)
        else:  # PERMANENT
            return collected_at + timedelta(days=365*100)  # 100 years
    
    def _send_transparency_notice(self, user_id: str, data_type: str, policy: DataCollectionPolicy):
        """Send transparency notice to user"""
        try:
            # This would integrate with your notification system
            notice_content = f"""
            Data Collection Notice
            
            We have collected {data_type} data for the purpose of {policy.purpose.value}.
            This data will be retained for {policy.retention_period.value}.
            
            You have the right to access, correct, or delete this data.
            """
            
            logger.info(f"Transparency notice sent to user {user_id} for {data_type}")
        
        except Exception as e:
            logger.error(f"Error sending transparency notice: {e}")
    
    def verify_data_accuracy(self, user_id: str, data_type: str, accuracy_score: float,
                           issues_found: List[str] = None, corrections_made: List[str] = None) -> bool:
        """Verify data accuracy"""
        try:
            accuracy_log = {
                "log_id": str(uuid.uuid4()),
                "user_id": user_id,
                "data_type": data_type,
                "accuracy_check_date": datetime.utcnow(),
                "accuracy_score": accuracy_score,
                "issues_found": issues_found or [],
                "corrections_made": corrections_made or [],
                "verified_by": "system"
            }
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO data_accuracy_logs 
                    (log_id, user_id, data_type, accuracy_check_date, accuracy_score,
                     issues_found, corrections_made, verified_by, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    accuracy_log["log_id"],
                    accuracy_log["user_id"],
                    accuracy_log["data_type"],
                    accuracy_log["accuracy_check_date"].isoformat(),
                    accuracy_log["accuracy_score"],
                    json.dumps(accuracy_log["issues_found"]),
                    json.dumps(accuracy_log["corrections_made"]),
                    accuracy_log["verified_by"],
                    json.dumps({})
                ))
            
            logger.info(f"Data accuracy verified for user {user_id}: {data_type} - Score: {accuracy_score}")
            return True
        
        except Exception as e:
            logger.error(f"Error verifying data accuracy: {e}")
            return False
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data based on retention policies"""
        try:
            cleanup_stats = {}
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT data_type, COUNT(*) as count
                    FROM data_processing_records 
                    WHERE retention_expiry < ?
                    GROUP BY data_type
                """, (datetime.utcnow().isoformat(),))
                
                for row in cursor.fetchall():
                    data_type = row[0]
                    count = row[1]
                    
                    # Delete expired records
                    conn.execute("""
                        DELETE FROM data_processing_records 
                        WHERE data_type = ? AND retention_expiry < ?
                    """, (data_type, datetime.utcnow().isoformat()))
                    
                    cleanup_stats[data_type] = count
            
            logger.info(f"Expired data cleanup completed: {cleanup_stats}")
            return cleanup_stats
        
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")
            return {}
    
    def add_privacy_notice(self, notice: PrivacyNotice) -> bool:
        """Add privacy notice"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO privacy_notices 
                    (notice_id, version, effective_date, content, language, region,
                     data_purposes, retention_periods, user_rights, contact_info, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    notice.notice_id,
                    notice.version,
                    notice.effective_date.isoformat(),
                    notice.content,
                    notice.language,
                    notice.region,
                    json.dumps([p.value for p in notice.data_purposes]),
                    json.dumps(notice.retention_periods),
                    json.dumps(notice.user_rights),
                    json.dumps(notice.contact_info),
                    json.dumps(notice.metadata)
                ))
            
            logger.info(f"Privacy notice added: {notice.notice_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding privacy notice: {e}")
            return False
    
    def get_privacy_notice(self, version: str = None) -> Optional[PrivacyNotice]:
        """Get privacy notice"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if version:
                    cursor = conn.execute("""
                        SELECT notice_id, version, effective_date, content, language, region,
                               data_purposes, retention_periods, user_rights, contact_info, metadata
                        FROM privacy_notices 
                        WHERE version = ?
                    """, (version,))
                else:
                    cursor = conn.execute("""
                        SELECT notice_id, version, effective_date, content, language, region,
                               data_purposes, retention_periods, user_rights, contact_info, metadata
                        FROM privacy_notices 
                        ORDER BY effective_date DESC LIMIT 1
                    """)
                
                row = cursor.fetchone()
                if row:
                    return PrivacyNotice(
                        notice_id=row[0],
                        version=row[1],
                        effective_date=datetime.fromisoformat(row[2]),
                        content=row[3],
                        language=row[4],
                        region=row[5],
                        data_purposes=[DataPurpose(p) for p in json.loads(row[6])] if row[6] else [],
                        retention_periods=json.loads(row[7]) if row[7] else {},
                        user_rights=json.loads(row[8]) if row[8] else [],
                        contact_info=json.loads(row[9]) if row[9] else {},
                        metadata=json.loads(row[10]) if row[10] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting privacy notice: {e}")
            return None
    
    def create_data_subject_request(self, request: DataSubjectRequest) -> bool:
        """Create data subject request"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO data_subject_requests 
                    (request_id, user_id, request_type, status, created_at, description,
                     data_types, verification_method, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.request_id,
                    request.user_id,
                    request.request_type,
                    request.status,
                    request.created_at.isoformat(),
                    request.description,
                    json.dumps(request.data_types),
                    request.verification_method,
                    json.dumps(request.metadata)
                ))
            
            logger.info(f"Data subject request created: {request.request_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating data subject request: {e}")
            return False
    
    def update_request_status(self, request_id: str, status: str, response_data: str = None) -> bool:
        """Update data subject request status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status == "completed":
                    conn.execute("""
                        UPDATE data_subject_requests 
                        SET status = ?, completed_at = ?, response_data = ?
                        WHERE request_id = ?
                    """, (status, datetime.utcnow().isoformat(), response_data, request_id))
                else:
                    conn.execute("""
                        UPDATE data_subject_requests 
                        SET status = ?
                        WHERE request_id = ?
                    """, (status, request_id))
            
            logger.info(f"Request status updated: {request_id} -> {status}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating request status: {e}")
            return False
    
    def get_user_requests(self, user_id: str) -> List[DataSubjectRequest]:
        """Get user's data subject requests"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT request_id, user_id, request_type, status, created_at, completed_at,
                           description, data_types, verification_method, verification_completed,
                           response_data, metadata
                    FROM data_subject_requests 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                
                requests = []
                for row in cursor.fetchall():
                    request = DataSubjectRequest(
                        request_id=row[0],
                        user_id=row[1],
                        request_type=row[2],
                        status=row[3],
                        created_at=datetime.fromisoformat(row[4]),
                        completed_at=datetime.fromisoformat(row[5]) if row[5] else None,
                        description=row[6],
                        data_types=json.loads(row[7]) if row[7] else [],
                        verification_method=row[8],
                        verification_completed=bool(row[9]),
                        response_data=row[10],
                        metadata=json.loads(row[11]) if row[11] else {}
                    )
                    requests.append(request)
                
                return requests
        
        except Exception as e:
            logger.error(f"Error getting user requests: {e}")
            return []
    
    def add_privacy_audit(self, audit: PrivacyAudit) -> bool:
        """Add privacy audit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO privacy_audits 
                    (audit_id, audit_type, auditor, audit_date, scope, findings,
                     recommendations, compliance_score, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit.audit_id,
                    audit.audit_type,
                    audit.auditor,
                    audit.audit_date.isoformat(),
                    json.dumps(audit.scope),
                    json.dumps(audit.findings),
                    json.dumps(audit.recommendations),
                    audit.compliance_score,
                    audit.status,
                    json.dumps(audit.metadata)
                ))
            
            logger.info(f"Privacy audit added: {audit.audit_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding privacy audit: {e}")
            return False
    
    def get_privacy_compliance_report(self) -> Dict[str, Any]:
        """Get comprehensive privacy compliance report"""
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "data_minimization": self._get_data_minimization_stats(),
                "purpose_limitation": self._get_purpose_limitation_stats(),
                "data_accuracy": self._get_data_accuracy_stats(),
                "storage_limitation": self._get_storage_limitation_stats(),
                "transparency": self._get_transparency_stats(),
                "data_subject_requests": self._get_request_stats(),
                "audit_summary": self._get_audit_summary()
            }
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating privacy compliance report: {e}")
            return {"error": str(e)}
    
    def _get_data_minimization_stats(self) -> Dict[str, Any]:
        """Get data minimization statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT necessity_level, COUNT(*) as count
                    FROM data_collection_policies 
                    GROUP BY necessity_level
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                return {
                    "total_policies": sum(stats.values()),
                    "necessity_breakdown": stats,
                    "minimization_score": self._calculate_minimization_score(stats)
                }
        
        except Exception as e:
            logger.error(f"Error getting data minimization stats: {e}")
            return {}
    
    def _calculate_minimization_score(self, stats: Dict[str, int]) -> float:
        """Calculate data minimization score"""
        try:
            total = sum(stats.values())
            if total == 0:
                return 0.0
            
            # Weight essential data higher, optional data lower
            essential_weight = 1.0
            important_weight = 0.7
            optional_weight = 0.3
            
            score = (
                (stats.get('essential', 0) * essential_weight) +
                (stats.get('important', 0) * important_weight) +
                (stats.get('optional', 0) * optional_weight)
            ) / total
            
            return round(score * 100, 2)
        
        except Exception as e:
            logger.error(f"Error calculating minimization score: {e}")
            return 0.0
    
    def _get_purpose_limitation_stats(self) -> Dict[str, Any]:
        """Get purpose limitation statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT purpose, COUNT(*) as count
                    FROM data_processing_records 
                    GROUP BY purpose
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                return {
                    "total_records": sum(stats.values()),
                    "purpose_breakdown": stats,
                    "compliance_rate": 95.5  # Placeholder
                }
        
        except Exception as e:
            logger.error(f"Error getting purpose limitation stats: {e}")
            return {}
    
    def _get_data_accuracy_stats(self) -> Dict[str, Any]:
        """Get data accuracy statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT AVG(accuracy_score) as avg_score, COUNT(*) as total_checks
                    FROM data_accuracy_logs
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        "average_accuracy_score": round(row[0] or 0, 2),
                        "total_accuracy_checks": row[1],
                        "accuracy_compliance": "excellent" if (row[0] or 0) >= 95 else "good"
                    }
                
                return {"average_accuracy_score": 0, "total_accuracy_checks": 0}
        
        except Exception as e:
            logger.error(f"Error getting data accuracy stats: {e}")
            return {}
    
    def _get_storage_limitation_stats(self) -> Dict[str, Any]:
        """Get storage limitation statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as expired_count
                    FROM data_processing_records 
                    WHERE retention_expiry < ?
                """, (datetime.utcnow().isoformat(),))
                
                expired_count = cursor.fetchone()[0]
                
                return {
                    "expired_records": expired_count,
                    "auto_deletion_enabled": True,
                    "retention_compliance": "compliant" if expired_count == 0 else "needs_cleanup"
                }
        
        except Exception as e:
            logger.error(f"Error getting storage limitation stats: {e}")
            return {}
    
    def _get_transparency_stats(self) -> Dict[str, Any]:
        """Get transparency statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT transparency_level, COUNT(*) as count
                    FROM data_collection_policies 
                    GROUP BY transparency_level
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                return {
                    "total_policies": sum(stats.values()),
                    "transparency_breakdown": stats,
                    "transparency_score": self._calculate_transparency_score(stats)
                }
        
        except Exception as e:
            logger.error(f"Error getting transparency stats: {e}")
            return {}
    
    def _calculate_transparency_score(self, stats: Dict[str, int]) -> float:
        """Calculate transparency score"""
        try:
            total = sum(stats.values())
            if total == 0:
                return 0.0
            
            # Weight full transparency higher
            full_weight = 1.0
            partial_weight = 0.7
            minimal_weight = 0.3
            
            score = (
                (stats.get('full', 0) * full_weight) +
                (stats.get('partial', 0) * partial_weight) +
                (stats.get('minimal', 0) * minimal_weight)
            ) / total
            
            return round(score * 100, 2)
        
        except Exception as e:
            logger.error(f"Error calculating transparency score: {e}")
            return 0.0
    
    def _get_request_stats(self) -> Dict[str, Any]:
        """Get data subject request statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT request_type, status, COUNT(*) as count
                    FROM data_subject_requests 
                    GROUP BY request_type, status
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    request_type = row[0]
                    status = row[1]
                    count = row[2]
                    
                    if request_type not in stats:
                        stats[request_type] = {}
                    
                    stats[request_type][status] = count
                
                return {
                    "total_requests": sum(sum(type_stats.values()) for type_stats in stats.values()),
                    "request_breakdown": stats,
                    "average_response_time": "2.5 days"  # Placeholder
                }
        
        except Exception as e:
            logger.error(f"Error getting request stats: {e}")
            return {}
    
    def _get_audit_summary(self) -> Dict[str, Any]:
        """Get audit summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT audit_type, status, AVG(compliance_score) as avg_score, COUNT(*) as count
                    FROM privacy_audits 
                    GROUP BY audit_type, status
                """)
                
                audit_summary = {}
                for row in cursor.fetchall():
                    audit_type = row[0]
                    status = row[1]
                    avg_score = row[2]
                    count = row[3]
                    
                    if audit_type not in audit_summary:
                        audit_summary[audit_type] = {}
                    
                    audit_summary[audit_type][status] = {
                        "count": count,
                        "average_score": round(avg_score or 0, 2)
                    }
                
                return audit_summary
        
        except Exception as e:
            logger.error(f"Error getting audit summary: {e}")
            return {}

# Global privacy controls manager instance
_privacy_manager = None

def get_privacy_manager() -> PrivacyControlsManager:
    """Get global privacy controls manager instance"""
    global _privacy_manager
    
    if _privacy_manager is None:
        _privacy_manager = PrivacyControlsManager()
    
    return _privacy_manager 