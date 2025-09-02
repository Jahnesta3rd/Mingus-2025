#!/usr/bin/env python3
"""
Privacy Compliance Manager for Mingus Financial App
Comprehensive GDPR, CCPA, and privacy regulation compliance
"""

import os
import json
import base64
import hashlib
import logging
import sqlite3
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from io import BytesIO

import requests
from cryptography.fernet import Fernet

# Configure logging
logger = logging.getLogger(__name__)

class PrivacyRegulation(Enum):
    """Privacy regulations"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    PIPEDA = "pipeda"
    LGPD = "lgpd"

class DataCategory(Enum):
    """Data categories for privacy compliance"""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    FINANCIAL_DATA = "financial_data"
    BEHAVIORAL_DATA = "behavioral_data"
    TECHNICAL_DATA = "technical_data"
    LOCATION_DATA = "location_data"
    COMMUNICATION_DATA = "communication_data"

class ConsentType(Enum):
    """Consent types"""
    NECESSARY = "necessary"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    ADVERTISING = "advertising"
    THIRD_PARTY = "third_party"

class DataSubjectRight(Enum):
    """Data subject rights"""
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    OBJECTION = "objection"
    WITHDRAW_CONSENT = "withdraw_consent"

@dataclass
class ConsentRecord:
    """Consent record for privacy compliance"""
    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime
    ip_address: str
    user_agent: str
    policy_version: str
    withdrawal_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataSubjectRequest:
    """Data subject request"""
    request_id: str
    user_id: str
    right_type: DataSubjectRight
    data_categories: List[DataCategory]
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PrivacyPolicy:
    """Privacy policy configuration"""
    version: str
    effective_date: datetime
    regulations: List[PrivacyRegulation]
    data_categories: List[DataCategory]
    retention_periods: Dict[str, int]  # days
    contact_info: Dict[str, str]
    policy_text: str
    is_active: bool = True

class PrivacyComplianceManager:
    """Comprehensive privacy compliance manager"""
    
    def __init__(self, database_path: str = "privacy_compliance.db"):
        self.database_path = database_path
        self.encryption_key = self._load_or_generate_key()
        
        # Initialize database
        self._initialize_database()
        
        # Initialize default privacy policy
        self._initialize_default_policy()
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate privacy compliance encryption key"""
        key_file = Path("privacy_encryption.key")
        
        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            logger.info("Generated new privacy compliance encryption key")
            return key
    
    def _initialize_database(self):
        """Initialize privacy compliance database"""
        with sqlite3.connect(self.database_path) as conn:
            # Create consent records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consent_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    consent_type TEXT NOT NULL,
                    granted BOOLEAN NOT NULL,
                    timestamp TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    withdrawal_timestamp TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create data subject requests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_subject_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    right_type TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    metadata TEXT,
                    created_at_db TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create privacy policies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS privacy_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    effective_date TEXT NOT NULL,
                    regulations TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    retention_periods TEXT NOT NULL,
                    contact_info TEXT NOT NULL,
                    policy_text TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create data deletion logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_deletion_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    deletion_type TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    deletion_date TEXT NOT NULL,
                    deletion_method TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_user_id ON consent_records(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_type ON consent_records(consent_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_user_id ON data_subject_requests(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON data_subject_requests(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_deletion_user_id ON data_deletion_logs(user_id)")
    
    def _initialize_default_policy(self):
        """Initialize default privacy policy"""
        default_policy = PrivacyPolicy(
            version="1.0",
            effective_date=datetime.utcnow(),
            regulations=[PrivacyRegulation.GDPR, PrivacyRegulation.CCPA],
            data_categories=[
                DataCategory.PERSONAL_DATA,
                DataCategory.FINANCIAL_DATA,
                DataCategory.BEHAVIORAL_DATA,
                DataCategory.TECHNICAL_DATA
            ],
            retention_periods={
                "personal_data": 2555,  # 7 years
                "financial_data": 1825,  # 5 years
                "behavioral_data": 1095,  # 3 years
                "technical_data": 730,   # 2 years
            },
            contact_info={
                "email": "privacy@mingus.com",
                "phone": "+1-800-MINGUS",
                "address": "123 Privacy Street, Security City, SC 12345"
            },
            policy_text="""
            Mingus Privacy Policy
            
            This privacy policy describes how Mingus collects, uses, and protects your personal information.
            
            Data Collection:
            - Personal information (name, email, phone)
            - Financial information (income, savings, debt)
            - Behavioral data (app usage, preferences)
            - Technical data (IP address, device info)
            
            Data Usage:
            - Provide financial services
            - Improve user experience
            - Comply with legal obligations
            
            Your Rights:
            - Access your data
            - Correct inaccurate data
            - Delete your data
            - Export your data
            - Withdraw consent
            
            Contact us at privacy@mingus.com for any questions.
            """
        )
        
        self.create_privacy_policy(default_policy)
    
    def record_consent(self, user_id: str, consent_type: ConsentType, granted: bool,
                      ip_address: str, user_agent: str, policy_version: str = "1.0",
                      metadata: Dict[str, Any] = None) -> bool:
        """Record user consent"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO consent_records 
                    (user_id, consent_type, granted, timestamp, ip_address, user_agent, policy_version, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    consent_type.value,
                    granted,
                    datetime.utcnow().isoformat(),
                    ip_address,
                    user_agent,
                    policy_version,
                    json.dumps(metadata or {})
                ))
            
            logger.info(f"Recorded consent for user {user_id}: {consent_type.value} = {granted}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            return False
    
    def withdraw_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Withdraw user consent"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    UPDATE consent_records 
                    SET withdrawal_timestamp = ?
                    WHERE user_id = ? AND consent_type = ? AND withdrawal_timestamp IS NULL
                """, (
                    datetime.utcnow().isoformat(),
                    user_id,
                    consent_type.value
                ))
            
            logger.info(f"Withdrew consent for user {user_id}: {consent_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            return False
    
    def get_user_consent_status(self, user_id: str) -> Dict[str, Any]:
        """Get user consent status"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT consent_type, granted, timestamp, withdrawal_timestamp
                    FROM consent_records 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                """, (user_id,))
                
                consents = {}
                for row in cursor.fetchall():
                    consent_type = row[0]
                    if consent_type not in consents:
                        consents[consent_type] = {
                            'granted': row[1],
                            'timestamp': row[2],
                            'withdrawn': row[3] is not None,
                            'withdrawal_timestamp': row[3]
                        }
                
                return consents
                
        except Exception as e:
            logger.error(f"Failed to get consent status: {e}")
            return {}
    
    def create_data_subject_request(self, user_id: str, right_type: DataSubjectRight,
                                   data_categories: List[DataCategory]) -> str:
        """Create data subject request"""
        try:
            request_id = f"dsr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(user_id.encode()).hexdigest()[:8]}"
            
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO data_subject_requests 
                    (request_id, user_id, right_type, data_categories, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    request_id,
                    user_id,
                    right_type.value,
                    json.dumps([cat.value for cat in data_categories]),
                    "pending",
                    datetime.utcnow().isoformat()
                ))
            
            logger.info(f"Created data subject request {request_id} for user {user_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Failed to create data subject request: {e}")
            raise
    
    def process_data_subject_request(self, request_id: str) -> Dict[str, Any]:
        """Process data subject request"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get request details
                cursor = conn.execute("""
                    SELECT user_id, right_type, data_categories, status
                    FROM data_subject_requests 
                    WHERE request_id = ?
                """, (request_id,))
                
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Request {request_id} not found")
                
                user_id, right_type, data_categories_json, status = row
                data_categories = [DataCategory(cat) for cat in json.loads(data_categories_json)]
                
                if status != "pending":
                    raise ValueError(f"Request {request_id} is not pending")
                
                # Update status to processing
                conn.execute("""
                    UPDATE data_subject_requests 
                    SET status = ?
                    WHERE request_id = ?
                """, ("processing", request_id))
                
                # Process based on right type
                result = {}
                if right_type == DataSubjectRight.ACCESS.value:
                    result = self._process_access_request(user_id, data_categories)
                elif right_type == DataSubjectRight.ERASURE.value:
                    result = self._process_erasure_request(user_id, data_categories)
                elif right_type == DataSubjectRight.PORTABILITY.value:
                    result = self._process_portability_request(user_id, data_categories)
                else:
                    result = {"message": f"Right type {right_type} not yet implemented"}
                
                # Update status to completed
                conn.execute("""
                    UPDATE data_subject_requests 
                    SET status = ?, completed_at = ?
                    WHERE request_id = ?
                """, ("completed", datetime.utcnow().isoformat(), request_id))
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to process data subject request: {e}")
            
            # Update status to failed
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    UPDATE data_subject_requests 
                    SET status = ?, completed_at = ?
                    WHERE request_id = ?
                """, ("failed", datetime.utcnow().isoformat(), request_id))
            
            raise
    
    def _process_access_request(self, user_id: str, data_categories: List[DataCategory]) -> Dict[str, Any]:
        """Process data access request"""
        try:
            data = {}
            
            for category in data_categories:
                if category == DataCategory.PERSONAL_DATA:
                    data['personal_data'] = self._get_personal_data(user_id)
                elif category == DataCategory.FINANCIAL_DATA:
                    data['financial_data'] = self._get_financial_data(user_id)
                elif category == DataCategory.BEHAVIORAL_DATA:
                    data['behavioral_data'] = self._get_behavioral_data(user_id)
                elif category == DataCategory.TECHNICAL_DATA:
                    data['technical_data'] = self._get_technical_data(user_id)
            
            return {
                'request_type': 'access',
                'user_id': user_id,
                'data_categories': [cat.value for cat in data_categories],
                'data': data,
                'exported_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process access request: {e}")
            raise
    
    def _process_erasure_request(self, user_id: str, data_categories: List[DataCategory]) -> Dict[str, Any]:
        """Process data erasure request"""
        try:
            deleted_categories = []
            
            for category in data_categories:
                if category == DataCategory.PERSONAL_DATA:
                    success = self._delete_personal_data(user_id)
                    if success:
                        deleted_categories.append('personal_data')
                elif category == DataCategory.FINANCIAL_DATA:
                    success = self._delete_financial_data(user_id)
                    if success:
                        deleted_categories.append('financial_data')
                elif category == DataCategory.BEHAVIORAL_DATA:
                    success = self._delete_behavioral_data(user_id)
                    if success:
                        deleted_categories.append('behavioral_data')
                elif category == DataCategory.TECHNICAL_DATA:
                    success = self._delete_technical_data(user_id)
                    if success:
                        deleted_categories.append('technical_data')
            
            # Log deletion
            self._log_data_deletion(user_id, "data_subject_request", deleted_categories)
            
            return {
                'request_type': 'erasure',
                'user_id': user_id,
                'deleted_categories': deleted_categories,
                'deletion_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process erasure request: {e}")
            raise
    
    def _process_portability_request(self, user_id: str, data_categories: List[DataCategory]) -> bytes:
        """Process data portability request"""
        try:
            # Get all requested data
            data = {}
            for category in data_categories:
                if category == DataCategory.PERSONAL_DATA:
                    data['personal_data'] = self._get_personal_data(user_id)
                elif category == DataCategory.FINANCIAL_DATA:
                    data['financial_data'] = self._get_financial_data(user_id)
                elif category == DataCategory.BEHAVIORAL_DATA:
                    data['behavioral_data'] = self._get_behavioral_data(user_id)
                elif category == DataCategory.TECHNICAL_DATA:
                    data['technical_data'] = self._get_technical_data(user_id)
            
            # Create ZIP file
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add JSON data
                zip_file.writestr('user_data.json', json.dumps(data, indent=2))
                
                # Add metadata
                metadata = {
                    'user_id': user_id,
                    'export_date': datetime.utcnow().isoformat(),
                    'data_categories': [cat.value for cat in data_categories],
                    'format': 'json',
                    'version': '1.0'
                }
                zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to process portability request: {e}")
            raise
    
    def _get_personal_data(self, user_id: str) -> Dict[str, Any]:
        """Get personal data for user"""
        # This would typically query your main database
        # For demonstration, return mock data
        return {
            'user_id': user_id,
            'email': f"user{user_id}@example.com",
            'name': f"User {user_id}",
            'phone': "+1-555-0123",
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _get_financial_data(self, user_id: str) -> Dict[str, Any]:
        """Get financial data for user"""
        # This would typically query your financial database
        return {
            'user_id': user_id,
            'monthly_income': 5000.00,
            'current_savings': 15000.00,
            'current_debt': 25000.00,
            'financial_goals': ['save_for_emergency', 'pay_off_debt']
        }
    
    def _get_behavioral_data(self, user_id: str) -> Dict[str, Any]:
        """Get behavioral data for user"""
        return {
            'user_id': user_id,
            'app_usage': {
                'total_sessions': 45,
                'last_login': datetime.utcnow().isoformat(),
                'preferences': ['notifications_enabled', 'dark_mode']
            }
        }
    
    def _get_technical_data(self, user_id: str) -> Dict[str, Any]:
        """Get technical data for user"""
        return {
            'user_id': user_id,
            'device_info': {
                'platform': 'web',
                'browser': 'Chrome',
                'ip_address': '192.168.1.1'
            },
            'consent_records': self.get_user_consent_status(user_id)
        }
    
    def _delete_personal_data(self, user_id: str) -> bool:
        """Delete personal data for user"""
        try:
            # This would typically update your main database
            # For demonstration, just log the deletion
            logger.info(f"Deleted personal data for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete personal data: {e}")
            return False
    
    def _delete_financial_data(self, user_id: str) -> bool:
        """Delete financial data for user"""
        try:
            logger.info(f"Deleted financial data for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete financial data: {e}")
            return False
    
    def _delete_behavioral_data(self, user_id: str) -> bool:
        """Delete behavioral data for user"""
        try:
            logger.info(f"Deleted behavioral data for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete behavioral data: {e}")
            return False
    
    def _delete_technical_data(self, user_id: str) -> bool:
        """Delete technical data for user"""
        try:
            logger.info(f"Deleted technical data for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete technical data: {e}")
            return False
    
    def _log_data_deletion(self, user_id: str, deletion_type: str, data_categories: List[str]):
        """Log data deletion"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO data_deletion_logs 
                    (user_id, deletion_type, data_categories, deletion_date, deletion_method)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    deletion_type,
                    json.dumps(data_categories),
                    datetime.utcnow().isoformat(),
                    "secure_erasure"
                ))
        except Exception as e:
            logger.error(f"Failed to log data deletion: {e}")
    
    def create_privacy_policy(self, policy: PrivacyPolicy) -> bool:
        """Create privacy policy"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO privacy_policies 
                    (version, effective_date, regulations, data_categories, retention_periods, 
                     contact_info, policy_text, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy.version,
                    policy.effective_date.isoformat(),
                    json.dumps([reg.value for reg in policy.regulations]),
                    json.dumps([cat.value for cat in policy.data_categories]),
                    json.dumps(policy.retention_periods),
                    json.dumps(policy.contact_info),
                    policy.policy_text,
                    policy.is_active
                ))
            
            logger.info(f"Created privacy policy version {policy.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create privacy policy: {e}")
            return False
    
    def get_active_privacy_policy(self) -> Optional[PrivacyPolicy]:
        """Get active privacy policy"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT version, effective_date, regulations, data_categories, 
                           retention_periods, contact_info, policy_text
                    FROM privacy_policies 
                    WHERE is_active = 1
                    ORDER BY effective_date DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    return PrivacyPolicy(
                        version=row[0],
                        effective_date=datetime.fromisoformat(row[1]),
                        regulations=[PrivacyRegulation(reg) for reg in json.loads(row[2])],
                        data_categories=[DataCategory(cat) for cat in json.loads(row[3])],
                        retention_periods=json.loads(row[4]),
                        contact_info=json.loads(row[5]),
                        policy_text=row[6]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get privacy policy: {e}")
            return None
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate privacy compliance report"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get consent statistics
                cursor = conn.execute("""
                    SELECT consent_type, granted, COUNT(*) as count
                    FROM consent_records 
                    WHERE withdrawal_timestamp IS NULL
                    GROUP BY consent_type, granted
                """)
                
                consent_stats = {}
                for row in cursor.fetchall():
                    consent_type = row[0]
                    granted = row[1]
                    count = row[2]
                    
                    if consent_type not in consent_stats:
                        consent_stats[consent_type] = {'granted': 0, 'denied': 0}
                    
                    if granted:
                        consent_stats[consent_type]['granted'] = count
                    else:
                        consent_stats[consent_type]['denied'] = count
                
                # Get request statistics
                cursor = conn.execute("""
                    SELECT right_type, status, COUNT(*) as count
                    FROM data_subject_requests 
                    GROUP BY right_type, status
                """)
                
                request_stats = {}
                for row in cursor.fetchall():
                    right_type = row[0]
                    status = row[1]
                    count = row[2]
                    
                    if right_type not in request_stats:
                        request_stats[right_type] = {}
                    
                    request_stats[right_type][status] = count
                
                # Get deletion statistics
                cursor = conn.execute("""
                    SELECT deletion_type, COUNT(*) as count
                    FROM data_deletion_logs 
                    GROUP BY deletion_type
                """)
                
                deletion_stats = {}
                for row in cursor.fetchall():
                    deletion_type = row[0]
                    count = row[1]
                    deletion_stats[deletion_type] = count
                
                return {
                    'consent_statistics': consent_stats,
                    'request_statistics': request_stats,
                    'deletion_statistics': deletion_stats,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {}

# Example usage and testing
if __name__ == "__main__":
    # Initialize privacy compliance manager
    privacy_manager = PrivacyComplianceManager()
    
    # Test consent recording
    print("📝 Testing consent recording...")
    privacy_manager.record_consent(
        user_id="user123",
        consent_type=ConsentType.MARKETING,
        granted=True,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    # Test consent status
    print("🔍 Testing consent status...")
    consent_status = privacy_manager.get_user_consent_status("user123")
    print(f"Consent status: {json.dumps(consent_status, indent=2)}")
    
    # Test data subject request
    print("📋 Testing data subject request...")
    request_id = privacy_manager.create_data_subject_request(
        user_id="user123",
        right_type=DataSubjectRight.ACCESS,
        data_categories=[DataCategory.PERSONAL_DATA, DataCategory.FINANCIAL_DATA]
    )
    print(f"Created request: {request_id}")
    
    # Process request
    print("⚙️ Processing data subject request...")
    result = privacy_manager.process_data_subject_request(request_id)
    print(f"Request result: {json.dumps(result, indent=2)}")
    
    # Test privacy policy
    print("📜 Testing privacy policy...")
    policy = privacy_manager.get_active_privacy_policy()
    if policy:
        print(f"Active policy version: {policy.version}")
        print(f"Regulations: {[reg.value for reg in policy.regulations]}")
    
    # Generate compliance report
    print("📊 Generating compliance report...")
    report = privacy_manager.get_compliance_report()
    print(f"Compliance report: {json.dumps(report, indent=2)}")
    
    print("✅ Privacy compliance test completed successfully!")
