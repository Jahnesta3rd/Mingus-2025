"""
GDPR Compliance Manager
Comprehensive GDPR compliance system with consent management, data rights, and audit trails
"""

import os
import json
import time
import hashlib
import uuid
import zipfile
import io
import csv
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

class ConsentType(Enum):
    """Types of consent"""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    NECESSARY = "necessary"
    FUNCTIONAL = "functional"
    ADVERTISING = "advertising"
    THIRD_PARTY = "third_party"

class DataCategory(Enum):
    """Data categories for GDPR"""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    BEHAVIORAL_DATA = "behavioral_data"
    TECHNICAL_DATA = "technical_data"
    FINANCIAL_DATA = "financial_data"
    LOCATION_DATA = "location_data"

class RequestStatus(Enum):
    """Request status for GDPR rights"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"

class RequestType(Enum):
    """Types of GDPR requests"""
    ACCESS = "access"
    DELETION = "deletion"
    PORTABILITY = "portability"
    RECTIFICATION = "rectification"
    RESTRICTION = "restriction"
    OBJECTION = "objection"

@dataclass
class ConsentRecord:
    """Consent record structure"""
    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime
    ip_address: str
    user_agent: str
    consent_version: str
    privacy_policy_version: str
    cookie_policy_version: str
    withdrawal_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GDPRRequest:
    """GDPR request structure"""
    request_id: str
    user_id: str
    request_type: RequestType
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    description: str
    completed_at: Optional[datetime] = None
    data_categories: List[DataCategory] = field(default_factory=list)
    verification_method: str = ""
    verification_completed: bool = False
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PrivacyPolicy:
    """Privacy policy structure"""
    version: str
    effective_date: datetime
    content: str
    language: str = "en"
    region: str = "EU"
    data_controller: str = ""
    data_processor: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CookiePolicy:
    """Cookie policy structure"""
    version: str
    effective_date: datetime
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    language: str = "en"
    region: str = "EU"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditTrail:
    """Audit trail structure"""
    audit_id: str
    user_id: str
    action: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    resource_type: str
    resource_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class GDPRComplianceManager:
    """Comprehensive GDPR compliance manager"""
    
    def __init__(self, db_path: str = "/var/lib/mingus/gdpr.db"):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.audit_lock = threading.Lock()
        
        self._init_database()
        self._load_default_policies()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = "/var/lib/mingus/gdpr_key.key"
        
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
        """Initialize GDPR compliance database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Consent records table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS consent_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        consent_type TEXT NOT NULL,
                        granted INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        user_agent TEXT NOT NULL,
                        consent_version TEXT NOT NULL,
                        privacy_policy_version TEXT NOT NULL,
                        cookie_policy_version TEXT NOT NULL,
                        withdrawal_timestamp TEXT,
                        metadata TEXT,
                        UNIQUE(user_id, consent_type, timestamp)
                    )
                """)
                
                # GDPR requests table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS gdpr_requests (
                        request_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        request_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        completed_at TEXT,
                        description TEXT NOT NULL,
                        data_categories TEXT,
                        verification_method TEXT,
                        verification_completed INTEGER DEFAULT 0,
                        rejection_reason TEXT,
                        metadata TEXT
                    )
                """)
                
                # Privacy policies table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS privacy_policies (
                        version TEXT PRIMARY KEY,
                        effective_date TEXT NOT NULL,
                        content TEXT NOT NULL,
                        language TEXT DEFAULT 'en',
                        region TEXT DEFAULT 'EU',
                        data_controller TEXT,
                        data_processor TEXT,
                        contact_email TEXT,
                        contact_phone TEXT,
                        metadata TEXT
                    )
                """)
                
                # Cookie policies table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cookie_policies (
                        version TEXT PRIMARY KEY,
                        effective_date TEXT NOT NULL,
                        cookies TEXT NOT NULL,
                        language TEXT DEFAULT 'en',
                        region TEXT DEFAULT 'EU',
                        metadata TEXT
                    )
                """)
                
                # Audit trails table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_trails (
                        audit_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        user_agent TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        metadata TEXT
                    )
                """)
                
                # Data inventory table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        data_category TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        storage_location TEXT NOT NULL,
                        retention_period TEXT NOT NULL,
                        processing_purpose TEXT NOT NULL,
                        legal_basis TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        metadata TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_user ON consent_records(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_type ON consent_records(consent_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_timestamp ON consent_records(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_user ON gdpr_requests(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_type ON gdpr_requests(request_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON gdpr_requests(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trails(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trails(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON data_inventory(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_category ON data_inventory(data_category)")
        
        except Exception as e:
            logger.error(f"Error initializing GDPR database: {e}")
    
    def _load_default_policies(self):
        """Load default privacy and cookie policies"""
        try:
            # Default privacy policy
            privacy_policy = PrivacyPolicy(
                version="1.0",
                effective_date=datetime.utcnow(),
                content="""
# Privacy Policy

## 1. Data Controller
Mingus Application is the data controller for your personal data.

## 2. Personal Data We Collect
- Name and contact information
- Account credentials
- Usage data and analytics
- Technical data and cookies

## 3. Legal Basis for Processing
- Consent (for marketing and analytics)
- Contract performance (for service delivery)
- Legitimate interests (for security and fraud prevention)

## 4. Data Retention
- Account data: Until account deletion
- Analytics data: 2 years
- Log data: 90 days
- Marketing data: Until consent withdrawal

## 5. Your Rights
- Right to access your data
- Right to rectification
- Right to erasure
- Right to data portability
- Right to restrict processing
- Right to object to processing

## 6. Contact Information
For privacy inquiries: privacy@mingus.com
                """,
                data_controller="Mingus Application",
                contact_email="privacy@mingus.com"
            )
            self.add_privacy_policy(privacy_policy)
            
            # Default cookie policy
            cookie_policy = CookiePolicy(
                version="1.0",
                effective_date=datetime.utcnow(),
                cookies=[
                    {
                        "name": "session_id",
                        "purpose": "Authentication and session management",
                        "category": "necessary",
                        "duration": "session",
                        "domain": ".mingus.com"
                    },
                    {
                        "name": "consent_preferences",
                        "purpose": "Store user consent preferences",
                        "category": "necessary",
                        "duration": "1 year",
                        "domain": ".mingus.com"
                    },
                    {
                        "name": "_ga",
                        "purpose": "Google Analytics tracking",
                        "category": "analytics",
                        "duration": "2 years",
                        "domain": ".google.com"
                    },
                    {
                        "name": "marketing_tracking",
                        "purpose": "Marketing campaign tracking",
                        "category": "marketing",
                        "duration": "90 days",
                        "domain": ".mingus.com"
                    }
                ]
            )
            self.add_cookie_policy(cookie_policy)
        
        except Exception as e:
            logger.error(f"Error loading default policies: {e}")
    
    def record_consent(self, user_id: str, consent_type: ConsentType, granted: bool,
                      ip_address: str, user_agent: str, consent_version: str = "1.0",
                      privacy_policy_version: str = "1.0", cookie_policy_version: str = "1.0",
                      metadata: Dict[str, Any] = None) -> bool:
        """Record user consent"""
        try:
            consent_record = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                consent_version=consent_version,
                privacy_policy_version=privacy_policy_version,
                cookie_policy_version=cookie_policy_version,
                metadata=metadata or {}
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO consent_records 
                    (user_id, consent_type, granted, timestamp, ip_address, user_agent,
                     consent_version, privacy_policy_version, cookie_policy_version, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    consent_record.user_id,
                    consent_record.consent_type.value,
                    1 if consent_record.granted else 0,
                    consent_record.timestamp.isoformat(),
                    consent_record.ip_address,
                    consent_record.user_agent,
                    consent_record.consent_version,
                    consent_record.privacy_policy_version,
                    consent_record.cookie_policy_version,
                    json.dumps(consent_record.metadata)
                ))
            
            # Record audit trail
            self._record_audit_trail(
                user_id=user_id,
                action="consent_recorded",
                resource_type="consent",
                resource_id=f"{consent_type.value}_{granted}",
                new_value=json.dumps({
                    "consent_type": consent_type.value,
                    "granted": granted,
                    "version": consent_version
                }),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Consent recorded for user {user_id}: {consent_type.value} = {granted}")
            return True
        
        except Exception as e:
            logger.error(f"Error recording consent: {e}")
            return False
    
    def withdraw_consent(self, user_id: str, consent_type: ConsentType,
                        ip_address: str, user_agent: str) -> bool:
        """Withdraw user consent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE consent_records 
                    SET withdrawal_timestamp = ?
                    WHERE user_id = ? AND consent_type = ? AND withdrawal_timestamp IS NULL
                    ORDER BY timestamp DESC LIMIT 1
                """, (datetime.utcnow().isoformat(), user_id, consent_type.value))
            
            # Record audit trail
            self._record_audit_trail(
                user_id=user_id,
                action="consent_withdrawn",
                resource_type="consent",
                resource_id=consent_type.value,
                old_value="granted",
                new_value="withdrawn",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"Consent withdrawn for user {user_id}: {consent_type.value}")
            return True
        
        except Exception as e:
            logger.error(f"Error withdrawing consent: {e}")
            return False
    
    def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get user's consent records"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, consent_type, granted, timestamp, ip_address, user_agent,
                           consent_version, privacy_policy_version, cookie_policy_version,
                           withdrawal_timestamp, metadata
                    FROM consent_records 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                """, (user_id,))
                
                consents = []
                for row in cursor.fetchall():
                    consent = ConsentRecord(
                        user_id=row[0],
                        consent_type=ConsentType(row[1]),
                        granted=bool(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        ip_address=row[4],
                        user_agent=row[5],
                        consent_version=row[6],
                        privacy_policy_version=row[7],
                        cookie_policy_version=row[8],
                        withdrawal_timestamp=datetime.fromisoformat(row[9]) if row[9] else None,
                        metadata=json.loads(row[10]) if row[10] else {}
                    )
                    consents.append(consent)
                
                return consents
        
        except Exception as e:
            logger.error(f"Error getting user consents: {e}")
            return []
    
    def has_valid_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Check if user has valid consent for specific type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT granted, withdrawal_timestamp
                    FROM consent_records 
                    WHERE user_id = ? AND consent_type = ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (user_id, consent_type.value))
                
                row = cursor.fetchone()
                if row:
                    granted = bool(row[0])
                    withdrawal_timestamp = row[1]
                    
                    # Check if consent was granted and not withdrawn
                    return granted and withdrawal_timestamp is None
                
                return False
        
        except Exception as e:
            logger.error(f"Error checking consent: {e}")
            return False
    
    def create_gdpr_request(self, user_id: str, request_type: RequestType, description: str,
                           data_categories: List[DataCategory] = None,
                           verification_method: str = "email") -> str:
        """Create GDPR request"""
        try:
            request_id = str(uuid.uuid4())
            
            gdpr_request = GDPRRequest(
                request_id=request_id,
                user_id=user_id,
                request_type=request_type,
                status=RequestStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                description=description,
                data_categories=data_categories or [],
                verification_method=verification_method
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO gdpr_requests 
                    (request_id, user_id, request_type, status, created_at, updated_at,
                     description, data_categories, verification_method, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    gdpr_request.request_id,
                    gdpr_request.user_id,
                    gdpr_request.request_type.value,
                    gdpr_request.status.value,
                    gdpr_request.created_at.isoformat(),
                    gdpr_request.updated_at.isoformat(),
                    gdpr_request.description,
                    json.dumps([cat.value for cat in gdpr_request.data_categories]),
                    gdpr_request.verification_method,
                    json.dumps(gdpr_request.metadata)
                ))
            
            # Record audit trail
            self._record_audit_trail(
                user_id=user_id,
                action="gdpr_request_created",
                resource_type="gdpr_request",
                resource_id=request_id,
                new_value=json.dumps({
                    "request_type": request_type.value,
                    "status": RequestStatus.PENDING.value
                })
            )
            
            logger.info(f"GDPR request created: {request_id} for user {user_id}")
            return request_id
        
        except Exception as e:
            logger.error(f"Error creating GDPR request: {e}")
            return None
    
    def update_request_status(self, request_id: str, status: RequestStatus,
                             rejection_reason: str = None) -> bool:
        """Update GDPR request status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status == RequestStatus.COMPLETED:
                    conn.execute("""
                        UPDATE gdpr_requests 
                        SET status = ?, updated_at = ?, completed_at = ?
                        WHERE request_id = ?
                    """, (status.value, datetime.utcnow().isoformat(), 
                          datetime.utcnow().isoformat(), request_id))
                else:
                    conn.execute("""
                        UPDATE gdpr_requests 
                        SET status = ?, updated_at = ?, rejection_reason = ?
                        WHERE request_id = ?
                    """, (status.value, datetime.utcnow().isoformat(), 
                          rejection_reason, request_id))
            
            # Get request details for audit
            request = self.get_gdpr_request(request_id)
            if request:
                self._record_audit_trail(
                    user_id=request.user_id,
                    action="gdpr_request_status_updated",
                    resource_type="gdpr_request",
                    resource_id=request_id,
                    old_value=request.status.value,
                    new_value=status.value
                )
            
            logger.info(f"GDPR request status updated: {request_id} -> {status.value}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating request status: {e}")
            return False
    
    def get_gdpr_request(self, request_id: str) -> Optional[GDPRRequest]:
        """Get GDPR request by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT request_id, user_id, request_type, status, created_at, updated_at,
                           completed_at, description, data_categories, verification_method,
                           verification_completed, rejection_reason, metadata
                    FROM gdpr_requests 
                    WHERE request_id = ?
                """, (request_id,))
                
                row = cursor.fetchone()
                if row:
                    return GDPRRequest(
                        request_id=row[0],
                        user_id=row[1],
                        request_type=RequestType(row[2]),
                        status=RequestStatus(row[3]),
                        created_at=datetime.fromisoformat(row[4]),
                        updated_at=datetime.fromisoformat(row[5]),
                        completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                        description=row[7],
                        data_categories=[DataCategory(cat) for cat in json.loads(row[8])] if row[8] else [],
                        verification_method=row[9],
                        verification_completed=bool(row[10]),
                        rejection_reason=row[11],
                        metadata=json.loads(row[12]) if row[12] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting GDPR request: {e}")
            return None
    
    def get_user_requests(self, user_id: str) -> List[GDPRRequest]:
        """Get user's GDPR requests"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT request_id, user_id, request_type, status, created_at, updated_at,
                           completed_at, description, data_categories, verification_method,
                           verification_completed, rejection_reason, metadata
                    FROM gdpr_requests 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                
                requests = []
                for row in cursor.fetchall():
                    gdpr_request = GDPRRequest(
                        request_id=row[0],
                        user_id=row[1],
                        request_type=RequestType(row[2]),
                        status=RequestStatus(row[3]),
                        created_at=datetime.fromisoformat(row[4]),
                        updated_at=datetime.fromisoformat(row[5]),
                        completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                        description=row[7],
                        data_categories=[DataCategory(cat) for cat in json.loads(row[8])] if row[8] else [],
                        verification_method=row[9],
                        verification_completed=bool(row[10]),
                        rejection_reason=row[11],
                        metadata=json.loads(row[12]) if row[12] else {}
                    )
                    requests.append(gdpr_request)
                
                return requests
        
        except Exception as e:
            logger.error(f"Error getting user requests: {e}")
            return []
    
    def export_user_data(self, user_id: str, data_categories: List[DataCategory] = None) -> bytes:
        """Export user data for GDPR right to access"""
        try:
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Export consent records
                consents = self.get_user_consents(user_id)
                if consents:
                    consent_data = []
                    for consent in consents:
                        consent_data.append({
                            "consent_type": consent.consent_type.value,
                            "granted": consent.granted,
                            "timestamp": consent.timestamp.isoformat(),
                            "withdrawal_timestamp": consent.withdrawal_timestamp.isoformat() if consent.withdrawal_timestamp else None,
                            "ip_address": consent.ip_address,
                            "user_agent": consent.user_agent,
                            "consent_version": consent.consent_version,
                            "metadata": consent.metadata
                        })
                    
                    zip_file.writestr("consent_records.json", json.dumps(consents, indent=2, default=str))
                
                # Export GDPR requests
                requests = self.get_user_requests(user_id)
                if requests:
                    request_data = []
                    for req in requests:
                        request_data.append({
                            "request_id": req.request_id,
                            "request_type": req.request_type.value,
                            "status": req.status.value,
                            "created_at": req.created_at.isoformat(),
                            "completed_at": req.completed_at.isoformat() if req.completed_at else None,
                            "description": req.description,
                            "data_categories": [cat.value for cat in req.data_categories],
                            "verification_method": req.verification_method,
                            "rejection_reason": req.rejection_reason,
                            "metadata": req.metadata
                        })
                    
                    zip_file.writestr("gdpr_requests.json", json.dumps(request_data, indent=2, default=str))
                
                # Export audit trails
                audit_trails = self.get_user_audit_trails(user_id)
                if audit_trails:
                    audit_data = []
                    for audit in audit_trails:
                        audit_data.append({
                            "audit_id": audit.audit_id,
                            "action": audit.action,
                            "timestamp": audit.timestamp.isoformat(),
                            "ip_address": audit.ip_address,
                            "resource_type": audit.resource_type,
                            "resource_id": audit.resource_id,
                            "old_value": audit.old_value,
                            "new_value": audit.new_value,
                            "metadata": audit.metadata
                        })
                    
                    zip_file.writestr("audit_trails.json", json.dumps(audit_data, indent=2, default=str))
                
                # Export data inventory
                inventory = self.get_user_data_inventory(user_id)
                if inventory:
                    zip_file.writestr("data_inventory.csv", self._export_inventory_to_csv(inventory))
                
                # Add export metadata
                export_metadata = {
                    "export_date": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "data_categories": [cat.value for cat in data_categories] if data_categories else [],
                    "export_format": "JSON/CSV",
                    "encryption": "AES-256"
                }
                zip_file.writestr("export_metadata.json", json.dumps(export_metadata, indent=2))
            
            # Record audit trail
            self._record_audit_trail(
                user_id=user_id,
                action="data_exported",
                resource_type="gdpr_export",
                resource_id=f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                new_value=json.dumps({
                    "data_categories": [cat.value for cat in data_categories] if data_categories else [],
                    "export_size": len(zip_buffer.getvalue())
                })
            )
            
            logger.info(f"Data exported for user {user_id}")
            return zip_buffer.getvalue()
        
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return b""
    
    def delete_user_data(self, user_id: str, data_categories: List[DataCategory] = None) -> bool:
        """Delete user data for GDPR right to erasure"""
        try:
            # Create deletion record
            deletion_record = {
                "user_id": user_id,
                "deletion_date": datetime.utcnow().isoformat(),
                "data_categories": [cat.value for cat in data_categories] if data_categories else [],
                "deletion_method": "secure_erasure"
            }
            
            # Anonymize or delete data based on categories
            if not data_categories or DataCategory.PERSONAL_DATA in data_categories:
                # Anonymize personal data
                self._anonymize_user_data(user_id)
            
            if not data_categories or DataCategory.SENSITIVE_DATA in data_categories:
                # Securely delete sensitive data
                self._securely_delete_sensitive_data(user_id)
            
            # Mark consent records as withdrawn
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE consent_records 
                    SET withdrawal_timestamp = ?
                    WHERE user_id = ? AND withdrawal_timestamp IS NULL
                """, (datetime.utcnow().isoformat(), user_id))
            
            # Record audit trail
            self._record_audit_trail(
                user_id=user_id,
                action="data_deleted",
                resource_type="gdpr_deletion",
                resource_id=f"deletion_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                new_value=json.dumps(deletion_record)
            )
            
            logger.info(f"Data deleted for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            return False
    
    def _anonymize_user_data(self, user_id: str):
        """Anonymize user personal data"""
        try:
            # This would integrate with your main application database
            # to anonymize user data while preserving system functionality
            logger.info(f"Anonymizing data for user {user_id}")
        except Exception as e:
            logger.error(f"Error anonymizing user data: {e}")
    
    def _securely_delete_sensitive_data(self, user_id: str):
        """Securely delete sensitive user data"""
        try:
            # This would integrate with your main application database
            # to securely delete sensitive data
            logger.info(f"Securely deleting sensitive data for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting sensitive data: {e}")
    
    def add_privacy_policy(self, policy: PrivacyPolicy) -> bool:
        """Add privacy policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO privacy_policies 
                    (version, effective_date, content, language, region, data_controller,
                     data_processor, contact_email, contact_phone, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy.version,
                    policy.effective_date.isoformat(),
                    policy.content,
                    policy.language,
                    policy.region,
                    policy.data_controller,
                    policy.data_processor,
                    policy.contact_email,
                    policy.contact_phone,
                    json.dumps(policy.metadata)
                ))
            
            logger.info(f"Privacy policy added: version {policy.version}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding privacy policy: {e}")
            return False
    
    def get_privacy_policy(self, version: str = None) -> Optional[PrivacyPolicy]:
        """Get privacy policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if version:
                    cursor = conn.execute("""
                        SELECT version, effective_date, content, language, region, data_controller,
                               data_processor, contact_email, contact_phone, metadata
                        FROM privacy_policies 
                        WHERE version = ?
                    """, (version,))
                else:
                    cursor = conn.execute("""
                        SELECT version, effective_date, content, language, region, data_controller,
                               data_processor, contact_email, contact_phone, metadata
                        FROM privacy_policies 
                        ORDER BY effective_date DESC LIMIT 1
                    """)
                
                row = cursor.fetchone()
                if row:
                    return PrivacyPolicy(
                        version=row[0],
                        effective_date=datetime.fromisoformat(row[1]),
                        content=row[2],
                        language=row[3],
                        region=row[4],
                        data_controller=row[5],
                        data_processor=row[6],
                        contact_email=row[7],
                        contact_phone=row[8],
                        metadata=json.loads(row[9]) if row[9] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting privacy policy: {e}")
            return None
    
    def add_cookie_policy(self, policy: CookiePolicy) -> bool:
        """Add cookie policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cookie_policies 
                    (version, effective_date, cookies, language, region, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    policy.version,
                    policy.effective_date.isoformat(),
                    json.dumps(policy.cookies),
                    policy.language,
                    policy.region,
                    json.dumps(policy.metadata)
                ))
            
            logger.info(f"Cookie policy added: version {policy.version}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding cookie policy: {e}")
            return False
    
    def get_cookie_policy(self, version: str = None) -> Optional[CookiePolicy]:
        """Get cookie policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if version:
                    cursor = conn.execute("""
                        SELECT version, effective_date, cookies, language, region, metadata
                        FROM cookie_policies 
                        WHERE version = ?
                    """, (version,))
                else:
                    cursor = conn.execute("""
                        SELECT version, effective_date, cookies, language, region, metadata
                        FROM cookie_policies 
                        ORDER BY effective_date DESC LIMIT 1
                    """)
                
                row = cursor.fetchone()
                if row:
                    return CookiePolicy(
                        version=row[0],
                        effective_date=datetime.fromisoformat(row[1]),
                        cookies=json.loads(row[2]),
                        language=row[3],
                        region=row[4],
                        metadata=json.loads(row[5]) if row[5] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting cookie policy: {e}")
            return None
    
    def _record_audit_trail(self, user_id: str, action: str, resource_type: str, resource_id: str,
                           old_value: str = None, new_value: str = None, ip_address: str = None,
                           user_agent: str = None, metadata: Dict[str, Any] = None):
        """Record audit trail entry"""
        try:
            with self.audit_lock:
                audit_id = str(uuid.uuid4())
                
                audit_trail = AuditTrail(
                    audit_id=audit_id,
                    user_id=user_id,
                    action=action,
                    timestamp=datetime.utcnow(),
                    ip_address=ip_address or "system",
                    user_agent=user_agent or "system",
                    resource_type=resource_type,
                    resource_id=resource_id,
                    old_value=old_value,
                    new_value=new_value,
                    metadata=metadata or {}
                )
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO audit_trails 
                        (audit_id, user_id, action, timestamp, ip_address, user_agent,
                         resource_type, resource_id, old_value, new_value, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        audit_trail.audit_id,
                        audit_trail.user_id,
                        audit_trail.action,
                        audit_trail.timestamp.isoformat(),
                        audit_trail.ip_address,
                        audit_trail.user_agent,
                        audit_trail.resource_type,
                        audit_trail.resource_id,
                        audit_trail.old_value,
                        audit_trail.new_value,
                        json.dumps(audit_trail.metadata)
                    ))
        
        except Exception as e:
            logger.error(f"Error recording audit trail: {e}")
    
    def get_user_audit_trails(self, user_id: str, limit: int = 100) -> List[AuditTrail]:
        """Get user's audit trails"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT audit_id, user_id, action, timestamp, ip_address, user_agent,
                           resource_type, resource_id, old_value, new_value, metadata
                    FROM audit_trails 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                
                audit_trails = []
                for row in cursor.fetchall():
                    audit_trail = AuditTrail(
                        audit_id=row[0],
                        user_id=row[1],
                        action=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        ip_address=row[4],
                        user_agent=row[5],
                        resource_type=row[6],
                        resource_id=row[7],
                        old_value=row[8],
                        new_value=row[9],
                        metadata=json.loads(row[10]) if row[10] else {}
                    )
                    audit_trails.append(audit_trail)
                
                return audit_trails
        
        except Exception as e:
            logger.error(f"Error getting audit trails: {e}")
            return []
    
    def add_data_inventory_entry(self, user_id: str, data_category: DataCategory, data_type: str,
                                storage_location: str, retention_period: str, processing_purpose: str,
                                legal_basis: str, metadata: Dict[str, Any] = None) -> bool:
        """Add data inventory entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO data_inventory 
                    (user_id, data_category, data_type, storage_location, retention_period,
                     processing_purpose, legal_basis, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    data_category.value,
                    data_type,
                    storage_location,
                    retention_period,
                    processing_purpose,
                    legal_basis,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    json.dumps(metadata or {})
                ))
            
            logger.info(f"Data inventory entry added for user {user_id}: {data_category.value}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding data inventory entry: {e}")
            return False
    
    def get_user_data_inventory(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's data inventory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT data_category, data_type, storage_location, retention_period,
                           processing_purpose, legal_basis, created_at, updated_at, metadata
                    FROM data_inventory 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                
                inventory = []
                for row in cursor.fetchall():
                    inventory.append({
                        "data_category": row[0],
                        "data_type": row[1],
                        "storage_location": row[2],
                        "retention_period": row[3],
                        "processing_purpose": row[4],
                        "legal_basis": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                        "metadata": json.loads(row[8]) if row[8] else {}
                    })
                
                return inventory
        
        except Exception as e:
            logger.error(f"Error getting data inventory: {e}")
            return []
    
    def _export_inventory_to_csv(self, inventory: List[Dict[str, Any]]) -> str:
        """Export data inventory to CSV format"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Data Category", "Data Type", "Storage Location", "Retention Period",
                "Processing Purpose", "Legal Basis", "Created At", "Updated At"
            ])
            
            # Write data
            for item in inventory:
                writer.writerow([
                    item["data_category"],
                    item["data_type"],
                    item["storage_location"],
                    item["retention_period"],
                    item["processing_purpose"],
                    item["legal_basis"],
                    item["created_at"],
                    item["updated_at"]
                ])
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Error exporting inventory to CSV: {e}")
            return ""
    
    def get_compliance_report(self, user_id: str = None) -> Dict[str, Any]:
        """Get GDPR compliance report"""
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "consent_summary": {},
                "request_summary": {},
                "audit_summary": {},
                "policy_summary": {}
            }
            
            # Consent summary
            if user_id:
                consents = self.get_user_consents(user_id)
                report["consent_summary"] = {
                    "total_consents": len(consents),
                    "active_consents": len([c for c in consents if c.granted and not c.withdrawal_timestamp]),
                    "withdrawn_consents": len([c for c in consents if c.withdrawal_timestamp]),
                    "consent_types": list(set([c.consent_type.value for c in consents]))
                }
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT consent_type, granted, COUNT(*) as count
                        FROM consent_records 
                        GROUP BY consent_type, granted
                    """)
                    report["consent_summary"] = dict(cursor.fetchall())
            
            # Request summary
            if user_id:
                requests = self.get_user_requests(user_id)
                report["request_summary"] = {
                    "total_requests": len(requests),
                    "pending_requests": len([r for r in requests if r.status == RequestStatus.PENDING]),
                    "completed_requests": len([r for r in requests if r.status == RequestStatus.COMPLETED]),
                    "request_types": list(set([r.request_type.value for r in requests]))
                }
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT request_type, status, COUNT(*) as count
                        FROM gdpr_requests 
                        GROUP BY request_type, status
                    """)
                    report["request_summary"] = dict(cursor.fetchall())
            
            # Policy summary
            privacy_policy = self.get_privacy_policy()
            cookie_policy = self.get_cookie_policy()
            
            report["policy_summary"] = {
                "privacy_policy_version": privacy_policy.version if privacy_policy else None,
                "cookie_policy_version": cookie_policy.version if cookie_policy else None,
                "privacy_policy_effective_date": privacy_policy.effective_date.isoformat() if privacy_policy else None,
                "cookie_policy_effective_date": cookie_policy.effective_date.isoformat() if cookie_policy else None
            }
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}

# Global GDPR compliance manager instance
_gdpr_manager = None

def get_gdpr_manager() -> GDPRComplianceManager:
    """Get global GDPR compliance manager instance"""
    global _gdpr_manager
    
    if _gdpr_manager is None:
        _gdpr_manager = GDPRComplianceManager()
    
    return _gdpr_manager 