"""
Security Best Practices Module
Comprehensive security best practices guidelines and tools for MINGUS
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3
from dataclasses_json import dataclass_json

logger = logging.getLogger(__name__)

class BestPracticeCategory(Enum):
    """Categories of security best practices"""
    PASSWORD_SECURITY = "password_security"
    EMAIL_SECURITY = "email_security"
    DEVICE_SECURITY = "device_security"
    NETWORK_SECURITY = "network_security"
    DATA_PROTECTION = "data_protection"
    ACCESS_CONTROL = "access_control"
    INCIDENT_RESPONSE = "incident_response"
    PHYSICAL_SECURITY = "physical_security"
    CLOUD_SECURITY = "cloud_security"
    MOBILE_SECURITY = "mobile_security"
    SOCIAL_ENGINEERING = "social_engineering"
    COMPLIANCE = "compliance"

class PracticeLevel(Enum):
    """Implementation levels for best practices"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"

class ImplementationStatus(Enum):
    """Status of best practice implementation"""
    NOT_IMPLEMENTED = "not_implemented"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    MAINTAINED = "maintained"

@dataclass_json
@dataclass
class SecurityBestPractice:
    """Security best practice definition"""
    practice_id: str
    category: BestPracticeCategory
    title: str
    description: str
    detailed_guidance: str
    implementation_steps: List[str]
    checkpoints: List[str]
    risk_level: str  # low, medium, high, critical
    practice_level: PracticeLevel
    compliance_requirements: List[str]
    estimated_effort: str  # low, medium, high
    resources_needed: List[str]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass_json
@dataclass
class BestPracticeImplementation:
    """Best practice implementation record"""
    implementation_id: str
    practice_id: str
    user_id: str
    status: ImplementationStatus
    implementation_date: Optional[datetime] = None
    verification_date: Optional[datetime] = None
    notes: str = ""
    evidence: List[str] = field(default_factory=list)
    reviewer: Optional[str] = None
    review_notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass_json
@dataclass
class SecurityChecklist:
    """Security checklist for best practices"""
    checklist_id: str
    title: str
    description: str
    category: BestPracticeCategory
    items: List[Dict[str, Any]]
    target_audience: List[str]
    frequency: str  # daily, weekly, monthly, quarterly, annually
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

@dataclass_json
@dataclass
class ChecklistResponse:
    """User response to security checklist"""
    response_id: str
    checklist_id: str
    user_id: str
    completed_date: datetime
    responses: List[Dict[str, Any]]
    score: Optional[int] = None
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

class SecurityBestPracticesSystem:
    """
    Comprehensive security best practices management system
    """
    
    def __init__(self, db_path: str = "/var/lib/mingus/security_best_practices.db"):
        self.db_path = db_path
        self._init_database()
        self._load_default_best_practices()
        self._load_default_checklists()
        
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_best_practices (
                        practice_id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        detailed_guidance TEXT NOT NULL,
                        implementation_steps TEXT,
                        checkpoints TEXT,
                        risk_level TEXT NOT NULL,
                        practice_level TEXT NOT NULL,
                        compliance_requirements TEXT,
                        estimated_effort TEXT NOT NULL,
                        resources_needed TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        tags TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS best_practice_implementations (
                        implementation_id TEXT PRIMARY KEY,
                        practice_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        implementation_date TEXT,
                        verification_date TEXT,
                        notes TEXT,
                        evidence TEXT,
                        reviewer TEXT,
                        review_notes TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_checklists (
                        checklist_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        category TEXT NOT NULL,
                        items TEXT,
                        target_audience TEXT,
                        frequency TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS checklist_responses (
                        response_id TEXT PRIMARY KEY,
                        checklist_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        completed_date TEXT NOT NULL,
                        responses TEXT,
                        score INTEGER,
                        recommendations TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_practice_category ON security_best_practices(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_practice_level ON security_best_practices(practice_level)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_implementation_user ON best_practice_implementations(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_implementation_practice ON best_practice_implementations(practice_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_checklist_category ON security_checklists(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_checklist_response_user ON checklist_responses(user_id)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _load_default_best_practices(self):
        """Load default security best practices"""
        default_practices = [
            SecurityBestPractice(
                practice_id="BP-001",
                category=BestPracticeCategory.PASSWORD_SECURITY,
                title="Strong Password Policy Implementation",
                description="Implement and enforce strong password policies across all systems",
                detailed_guidance=self._get_password_security_guidance(),
                implementation_steps=[
                    "Define password complexity requirements",
                    "Set minimum password length to 12 characters",
                    "Implement password history (prevent reuse of last 5 passwords)",
                    "Set maximum password age to 90 days",
                    "Enable account lockout after 5 failed attempts",
                    "Implement password expiration notifications"
                ],
                checkpoints=[
                    "Password policy documented and approved",
                    "Policy implemented across all systems",
                    "Users trained on password requirements",
                    "Regular password audits conducted",
                    "Policy compliance monitored"
                ],
                risk_level="high",
                practice_level=PracticeLevel.BASIC,
                compliance_requirements=["NIST", "ISO 27001", "PCI DSS"],
                estimated_effort="medium",
                resources_needed=["IT Administrator", "Security Team", "User Training"],
                created_by="security_team",
                tags=["authentication", "access-control", "compliance"]
            ),
            SecurityBestPractice(
                practice_id="BP-002",
                category=BestPracticeCategory.EMAIL_SECURITY,
                title="Email Security Best Practices",
                description="Implement comprehensive email security measures",
                detailed_guidance=self._get_email_security_guidance(),
                implementation_steps=[
                    "Enable SPF, DKIM, and DMARC for email authentication",
                    "Implement email filtering and anti-spam solutions",
                    "Configure email encryption for sensitive communications",
                    "Train users on phishing awareness",
                    "Implement email archiving and retention policies",
                    "Regular security awareness training"
                ],
                checkpoints=[
                    "Email authentication protocols configured",
                    "Anti-spam and anti-malware filters active",
                    "Email encryption implemented",
                    "Phishing simulation tests conducted",
                    "Email security incidents monitored"
                ],
                risk_level="high",
                practice_level=PracticeLevel.INTERMEDIATE,
                compliance_requirements=["GDPR", "HIPAA", "SOX"],
                estimated_effort="medium",
                resources_needed=["Email Administrator", "Security Team", "User Training"],
                created_by="security_team",
                tags=["email", "phishing", "encryption", "authentication"]
            ),
            SecurityBestPractice(
                practice_id="BP-003",
                category=BestPracticeCategory.DEVICE_SECURITY,
                title="Endpoint Security Hardening",
                description="Implement comprehensive endpoint security measures",
                detailed_guidance=self._get_device_security_guidance(),
                implementation_steps=[
                    "Install and configure endpoint protection software",
                    "Enable full disk encryption",
                    "Implement device control policies",
                    "Configure automatic software updates",
                    "Enable firewall and network protection",
                    "Implement application whitelisting"
                ],
                checkpoints=[
                    "Endpoint protection software deployed",
                    "Disk encryption enabled on all devices",
                    "Device control policies enforced",
                    "Software update process automated",
                    "Firewall rules configured and tested"
                ],
                risk_level="critical",
                practice_level=PracticeLevel.INTERMEDIATE,
                compliance_requirements=["ISO 27001", "PCI DSS", "HIPAA"],
                estimated_effort="high",
                resources_needed=["IT Administrator", "Security Team", "Endpoint Management Tools"],
                created_by="security_team",
                tags=["endpoint", "encryption", "malware", "updates"]
            ),
            SecurityBestPractice(
                practice_id="BP-004",
                category=BestPracticeCategory.DATA_PROTECTION,
                title="Data Classification and Protection",
                description="Implement data classification and protection framework",
                detailed_guidance=self._get_data_protection_guidance(),
                implementation_steps=[
                    "Define data classification levels",
                    "Implement data labeling and marking",
                    "Configure access controls based on classification",
                    "Implement data loss prevention (DLP) solutions",
                    "Establish data retention and disposal policies",
                    "Train users on data handling procedures"
                ],
                checkpoints=[
                    "Data classification policy approved",
                    "Data labeling system implemented",
                    "Access controls configured by classification",
                    "DLP solutions deployed and tested",
                    "Data handling procedures documented"
                ],
                risk_level="critical",
                practice_level=PracticeLevel.ADVANCED,
                compliance_requirements=["GDPR", "HIPAA", "PCI DSS", "SOX"],
                estimated_effort="high",
                resources_needed=["Data Protection Officer", "Security Team", "DLP Tools"],
                created_by="security_team",
                tags=["data-protection", "classification", "dlp", "compliance"]
            ),
            SecurityBestPractice(
                practice_id="BP-005",
                category=BestPracticeCategory.INCIDENT_RESPONSE,
                title="Incident Response Plan Development",
                description="Develop and implement comprehensive incident response procedures",
                detailed_guidance=self._get_incident_response_guidance(),
                implementation_steps=[
                    "Define incident response team roles and responsibilities",
                    "Establish incident classification and severity levels",
                    "Create incident response procedures and playbooks",
                    "Implement incident detection and monitoring tools",
                    "Establish communication and notification procedures",
                    "Conduct regular incident response exercises"
                ],
                checkpoints=[
                    "Incident response plan documented and approved",
                    "Response team trained and ready",
                    "Detection and monitoring tools operational",
                    "Communication procedures tested",
                    "Incident response exercises conducted quarterly"
                ],
                risk_level="critical",
                practice_level=PracticeLevel.ENTERPRISE,
                compliance_requirements=["ISO 27001", "NIST", "SOX"],
                estimated_effort="high",
                resources_needed=["Incident Response Team", "Security Tools", "Legal Team"],
                created_by="security_team",
                tags=["incident-response", "forensics", "communication", "recovery"]
            )
        ]
        
        for practice in default_practices:
            self.create_best_practice(practice)
    
    def _load_default_checklists(self):
        """Load default security checklists"""
        default_checklists = [
            SecurityChecklist(
                checklist_id="CL-001",
                title="Daily Security Checklist",
                description="Daily security tasks for all users",
                category=BestPracticeCategory.DEVICE_SECURITY,
                items=[
                    {"id": 1, "question": "Is your device locked when unattended?", "type": "yes_no", "critical": True},
                    {"id": 2, "question": "Are all software updates installed?", "type": "yes_no", "critical": False},
                    {"id": 3, "question": "Is your antivirus software running and updated?", "type": "yes_no", "critical": True},
                    {"id": 4, "question": "Have you reviewed any suspicious emails?", "type": "yes_no", "critical": True},
                    {"id": 5, "question": "Is your work area clean and secure?", "type": "yes_no", "critical": False}
                ],
                target_audience=["all_users"],
                frequency="daily",
                created_by="security_team"
            ),
            SecurityChecklist(
                checklist_id="CL-002",
                title="Weekly Security Review",
                description="Weekly security review for IT administrators",
                category=BestPracticeCategory.NETWORK_SECURITY,
                items=[
                    {"id": 1, "question": "Have all security patches been applied?", "type": "yes_no", "critical": True},
                    {"id": 2, "question": "Are firewall rules reviewed and updated?", "type": "yes_no", "critical": True},
                    {"id": 3, "question": "Have security logs been reviewed for anomalies?", "type": "yes_no", "critical": True},
                    {"id": 4, "question": "Are backup systems tested and verified?", "type": "yes_no", "critical": True},
                    {"id": 5, "question": "Have user access rights been reviewed?", "type": "yes_no", "critical": False}
                ],
                target_audience=["it_admin", "security_team"],
                frequency="weekly",
                created_by="security_team"
            ),
            SecurityChecklist(
                checklist_id="CL-003",
                title="Monthly Compliance Review",
                description="Monthly compliance and security review",
                category=BestPracticeCategory.COMPLIANCE,
                items=[
                    {"id": 1, "question": "Are all compliance requirements being met?", "type": "yes_no", "critical": True},
                    {"id": 2, "question": "Have security policies been reviewed and updated?", "type": "yes_no", "critical": True},
                    {"id": 3, "question": "Are security awareness training records current?", "type": "yes_no", "critical": True},
                    {"id": 4, "question": "Have incident response procedures been tested?", "type": "yes_no", "critical": True},
                    {"id": 5, "question": "Are risk assessments up to date?", "type": "yes_no", "critical": True}
                ],
                target_audience=["security_team", "compliance_team"],
                frequency="monthly",
                created_by="security_team"
            )
        ]
        
        for checklist in default_checklists:
            self.create_security_checklist(checklist)
    
    def create_best_practice(self, practice: SecurityBestPractice) -> bool:
        """Create a new security best practice"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO security_best_practices 
                    (practice_id, category, title, description, detailed_guidance, 
                     implementation_steps, checkpoints, risk_level, practice_level,
                     compliance_requirements, estimated_effort, resources_needed,
                     created_by, created_at, updated_at, is_active, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    practice.practice_id,
                    practice.category.value,
                    practice.title,
                    practice.description,
                    practice.detailed_guidance,
                    json.dumps(practice.implementation_steps),
                    json.dumps(practice.checkpoints),
                    practice.risk_level,
                    practice.practice_level.value,
                    json.dumps(practice.compliance_requirements),
                    practice.estimated_effort,
                    json.dumps(practice.resources_needed),
                    practice.created_by,
                    practice.created_at.isoformat(),
                    practice.updated_at.isoformat(),
                    practice.is_active,
                    json.dumps(practice.tags)
                ))
                conn.commit()
                logger.info(f"Created best practice: {practice.practice_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating best practice: {e}")
            return False
    
    def get_best_practices(self, category: Optional[BestPracticeCategory] = None, 
                         level: Optional[PracticeLevel] = None, 
                         active_only: bool = True) -> List[SecurityBestPractice]:
        """Get security best practices with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM security_best_practices WHERE is_active = ?"
                params = [active_only]
                
                if category:
                    query += " AND category = ?"
                    params.append(category.value)
                
                if level:
                    query += " AND practice_level = ?"
                    params.append(level.value)
                
                query += " ORDER BY risk_level DESC, title"
                
                cursor = conn.execute(query, params)
                
                practices = []
                for row in cursor.fetchall():
                    practice = SecurityBestPractice(
                        practice_id=row[0],
                        category=BestPracticeCategory(row[1]),
                        title=row[2],
                        description=row[3],
                        detailed_guidance=row[4],
                        implementation_steps=json.loads(row[5]),
                        checkpoints=json.loads(row[6]),
                        risk_level=row[7],
                        practice_level=PracticeLevel(row[8]),
                        compliance_requirements=json.loads(row[9]),
                        estimated_effort=row[10],
                        resources_needed=json.loads(row[11]),
                        created_by=row[12],
                        created_at=datetime.fromisoformat(row[13]),
                        updated_at=datetime.fromisoformat(row[14]),
                        is_active=bool(row[15]),
                        tags=json.loads(row[16]) if row[16] else []
                    )
                    practices.append(practice)
                
                return practices
        except Exception as e:
            logger.error(f"Error getting best practices: {e}")
            return []
    
    def create_security_checklist(self, checklist: SecurityChecklist) -> bool:
        """Create a new security checklist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO security_checklists 
                    (checklist_id, title, description, category, items, target_audience,
                     frequency, created_by, created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    checklist.checklist_id,
                    checklist.title,
                    checklist.description,
                    checklist.category.value,
                    json.dumps(checklist.items),
                    json.dumps(checklist.target_audience),
                    checklist.frequency,
                    checklist.created_by,
                    checklist.created_at.isoformat(),
                    checklist.updated_at.isoformat(),
                    checklist.is_active
                ))
                conn.commit()
                logger.info(f"Created security checklist: {checklist.checklist_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating security checklist: {e}")
            return False
    
    def get_security_checklists(self, category: Optional[BestPracticeCategory] = None,
                              frequency: Optional[str] = None,
                              target_audience: Optional[str] = None,
                              active_only: bool = True) -> List[SecurityChecklist]:
        """Get security checklists with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM security_checklists WHERE is_active = ?"
                params = [active_only]
                
                if category:
                    query += " AND category = ?"
                    params.append(category.value)
                
                if frequency:
                    query += " AND frequency = ?"
                    params.append(frequency)
                
                if target_audience:
                    query += " AND target_audience LIKE ?"
                    params.append(f"%{target_audience}%")
                
                query += " ORDER BY frequency, title"
                
                cursor = conn.execute(query, params)
                
                checklists = []
                for row in cursor.fetchall():
                    checklist = SecurityChecklist(
                        checklist_id=row[0],
                        title=row[1],
                        description=row[2],
                        category=BestPracticeCategory(row[3]),
                        items=json.loads(row[4]),
                        target_audience=json.loads(row[5]),
                        frequency=row[6],
                        created_by=row[7],
                        created_at=datetime.fromisoformat(row[8]),
                        updated_at=datetime.fromisoformat(row[9]),
                        is_active=bool(row[10])
                    )
                    checklists.append(checklist)
                
                return checklists
        except Exception as e:
            logger.error(f"Error getting security checklists: {e}")
            return []
    
    def submit_checklist_response(self, response: ChecklistResponse) -> bool:
        """Submit a checklist response"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO checklist_responses 
                    (response_id, checklist_id, user_id, completed_date, responses, score, recommendations, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    response.response_id,
                    response.checklist_id,
                    response.user_id,
                    response.completed_date.isoformat(),
                    json.dumps(response.responses),
                    response.score,
                    json.dumps(response.recommendations),
                    response.created_at.isoformat()
                ))
                conn.commit()
                logger.info(f"Submitted checklist response: {response.response_id}")
                return True
        except Exception as e:
            logger.error(f"Error submitting checklist response: {e}")
            return False
    
    def get_user_checklist_responses(self, user_id: str, 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> List[ChecklistResponse]:
        """Get checklist responses for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM checklist_responses WHERE user_id = ?"
                params = [user_id]
                
                if start_date:
                    query += " AND completed_date >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND completed_date <= ?"
                    params.append(end_date.isoformat())
                
                query += " ORDER BY completed_date DESC"
                
                cursor = conn.execute(query, params)
                
                responses = []
                for row in cursor.fetchall():
                    response = ChecklistResponse(
                        response_id=row[0],
                        checklist_id=row[1],
                        user_id=row[2],
                        completed_date=datetime.fromisoformat(row[3]),
                        responses=json.loads(row[4]),
                        score=row[5],
                        recommendations=json.loads(row[6]) if row[6] else [],
                        created_at=datetime.fromisoformat(row[7])
                    )
                    responses.append(response)
                
                return responses
        except Exception as e:
            logger.error(f"Error getting user checklist responses: {e}")
            return []
    
    def generate_best_practices_report(self, user_id: Optional[str] = None,
                                     category: Optional[BestPracticeCategory] = None,
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive best practices report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get best practices statistics
                query = "SELECT COUNT(*) as total, practice_level, risk_level FROM security_best_practices WHERE is_active = 1"
                params = []
                
                if category:
                    query += " AND category = ?"
                    params.append(category.value)
                
                query += " GROUP BY practice_level, risk_level"
                
                cursor = conn.execute(query, params)
                practice_stats = cursor.fetchall()
                
                # Get implementation statistics
                impl_query = "SELECT COUNT(*) as total, status FROM best_practice_implementations"
                impl_params = []
                
                if user_id:
                    impl_query += " WHERE user_id = ?"
                    impl_params.append(user_id)
                
                if start_date:
                    impl_query += " AND created_at >= ?"
                    impl_params.append(start_date.isoformat())
                
                if end_date:
                    impl_query += " AND created_at <= ?"
                    impl_params.append(end_date.isoformat())
                
                impl_query += " GROUP BY status"
                
                cursor = conn.execute(impl_query, impl_params)
                implementation_stats = cursor.fetchall()
                
                # Get checklist completion statistics
                checklist_query = "SELECT COUNT(*) as total, checklist_id FROM checklist_responses"
                checklist_params = []
                
                if user_id:
                    checklist_query += " WHERE user_id = ?"
                    checklist_params.append(user_id)
                
                if start_date:
                    checklist_query += " AND completed_date >= ?"
                    checklist_params.append(start_date.isoformat())
                
                if end_date:
                    checklist_query += " AND completed_date <= ?"
                    checklist_params.append(end_date.isoformat())
                
                checklist_query += " GROUP BY checklist_id"
                
                cursor = conn.execute(checklist_query, checklist_params)
                checklist_stats = cursor.fetchall()
                
                return {
                    'report_generated_at': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'category': category.value if category else 'all',
                    'best_practices_statistics': {
                        'total_practices': len(practice_stats),
                        'by_level': {row[1]: row[0] for row in practice_stats},
                        'by_risk': {row[2]: row[0] for row in practice_stats}
                    },
                    'implementation_statistics': {
                        'total_implementations': len(implementation_stats),
                        'by_status': {row[1]: row[0] for row in implementation_stats}
                    },
                    'checklist_statistics': {
                        'total_responses': len(checklist_stats),
                        'by_checklist': {row[1]: row[0] for row in checklist_stats}
                    }
                }
        except Exception as e:
            logger.error(f"Error generating best practices report: {e}")
            return {}
    
    # Guidance content generators
    def _get_password_security_guidance(self) -> str:
        return """
# Strong Password Policy Implementation Guide

## Overview
Implementing a strong password policy is fundamental to protecting organizational assets and user accounts from unauthorized access.

## Key Components

### 1. Password Complexity Requirements
- **Minimum Length**: 12 characters
- **Character Types**: Uppercase, lowercase, numbers, special characters
- **Avoid**: Common words, patterns, personal information
- **Examples**: 
  - Strong: `K9#mN2$pL8@vX`
  - Weak: `password123`

### 2. Password Management
- **History**: Prevent reuse of last 5 passwords
- **Expiration**: 90-day maximum password age
- **Lockout**: 5 failed attempts triggers account lockout
- **Recovery**: Secure password reset procedures

### 3. Multi-Factor Authentication
- **Enable MFA** on all critical systems
- **Use authenticator apps** or hardware tokens
- **Keep backup codes** in secure location
- **Regular MFA testing** and validation

## Implementation Steps

1. **Policy Development**
   - Define password requirements
   - Document exceptions and procedures
   - Get management approval

2. **System Configuration**
   - Configure password policies in all systems
   - Test policy enforcement
   - Monitor for compliance

3. **User Training**
   - Train users on password requirements
   - Provide password manager recommendations
   - Conduct regular awareness sessions

4. **Monitoring and Enforcement**
   - Regular password audits
   - Compliance monitoring
   - Policy violation handling

## Best Practices

- Use password managers for secure storage
- Never share passwords or write them down
- Change passwords immediately if compromised
- Use unique passwords for each account
- Enable MFA wherever possible
- Regular security awareness training
        """
    
    def _get_email_security_guidance(self) -> str:
        return """
# Email Security Best Practices Guide

## Overview
Email remains a primary attack vector for cyber threats. Implementing comprehensive email security measures is essential for protecting organizational communications and data.

## Key Components

### 1. Email Authentication
- **SPF (Sender Policy Framework)**: Prevent email spoofing
- **DKIM (DomainKeys Identified Mail)**: Email integrity verification
- **DMARC (Domain-based Message Authentication)**: Policy enforcement

### 2. Email Filtering
- **Anti-spam filters**: Block unwanted emails
- **Anti-malware scanning**: Detect malicious attachments
- **Content filtering**: Block inappropriate content
- **URL filtering**: Block malicious links

### 3. Email Encryption
- **TLS encryption**: Encrypt email in transit
- **End-to-end encryption**: For sensitive communications
- **Digital signatures**: Verify sender authenticity

## Implementation Steps

1. **Email Authentication Setup**
   - Configure SPF records
   - Implement DKIM signing
   - Deploy DMARC policies

2. **Security Filtering**
   - Deploy anti-spam solutions
   - Configure malware scanning
   - Set up content filtering rules

3. **User Training**
   - Phishing awareness training
   - Email security best practices
   - Incident reporting procedures

4. **Monitoring and Response**
   - Monitor email security events
   - Respond to security incidents
   - Regular security assessments

## Best Practices

- Never click suspicious links
- Verify sender addresses carefully
- Don't open unexpected attachments
- Report suspicious emails immediately
- Use encrypted email for sensitive data
- Regular security awareness training
- Keep email clients updated
- Use strong passwords for email accounts
        """
    
    def _get_device_security_guidance(self) -> str:
        return """
# Endpoint Security Hardening Guide

## Overview
Endpoint devices are the front line of defense against cyber threats. Implementing comprehensive endpoint security measures is critical for protecting organizational assets.

## Key Components

### 1. Endpoint Protection
- **Antivirus/Antimalware**: Real-time threat detection
- **Endpoint Detection and Response (EDR)**: Advanced threat detection
- **Application Control**: Whitelist approved applications
- **Device Control**: Manage USB and removable media

### 2. System Hardening
- **Full Disk Encryption**: Protect data at rest
- **Secure Boot**: Prevent unauthorized boot processes
- **Regular Updates**: Keep systems patched
- **Firewall Configuration**: Network traffic control

### 3. Access Control
- **User Authentication**: Strong authentication methods
- **Privilege Management**: Least privilege principle
- **Session Management**: Secure session handling
- **Remote Access Security**: Secure remote connections

## Implementation Steps

1. **Assessment and Planning**
   - Inventory all endpoints
   - Assess current security posture
   - Define security requirements
   - Plan implementation strategy

2. **Deployment and Configuration**
   - Deploy endpoint protection software
   - Configure security policies
   - Enable encryption
   - Set up monitoring

3. **User Training**
   - Security awareness training
   - Safe computing practices
   - Incident reporting procedures
   - Regular security updates

4. **Monitoring and Maintenance**
   - Regular security assessments
   - Policy updates and enforcement
   - Incident response procedures
   - Performance monitoring

## Best Practices

- Keep systems updated and patched
- Use strong authentication methods
- Enable full disk encryption
- Implement application whitelisting
- Regular security scans
- Monitor for suspicious activity
- Backup important data regularly
- Use secure network connections
        """
    
    def _get_data_protection_guidance(self) -> str:
        return """
# Data Classification and Protection Guide

## Overview
Data classification and protection is essential for ensuring sensitive information is handled appropriately and in compliance with regulatory requirements.

## Key Components

### 1. Data Classification Levels
- **Public**: Information approved for public release
- **Internal**: Information for internal use only
- **Confidential**: Sensitive business information
- **Restricted**: Highly sensitive information

### 2. Data Protection Measures
- **Access Controls**: Role-based access control
- **Encryption**: Data encryption at rest and in transit
- **Data Loss Prevention (DLP)**: Monitor and prevent data leaks
- **Backup and Recovery**: Secure backup procedures

### 3. Compliance Requirements
- **GDPR**: European data protection regulation
- **HIPAA**: Health information privacy
- **PCI DSS**: Payment card industry standards
- **SOX**: Financial reporting requirements

## Implementation Steps

1. **Data Inventory and Classification**
   - Identify all data assets
   - Classify data by sensitivity
   - Document data flows
   - Map compliance requirements

2. **Protection Implementation**
   - Implement access controls
   - Deploy encryption solutions
   - Configure DLP systems
   - Set up monitoring

3. **Policy and Procedure Development**
   - Data handling procedures
   - Retention and disposal policies
   - Incident response procedures
   - User training programs

4. **Monitoring and Compliance**
   - Regular compliance audits
   - Data protection monitoring
   - Incident response testing
   - Policy updates

## Best Practices

- Classify all data appropriately
- Use encryption for sensitive data
- Implement least privilege access
- Regular security assessments
- Monitor data access and usage
- Train users on data protection
- Maintain audit trails
- Regular policy reviews
        """
    
    def _get_incident_response_guidance(self) -> str:
        return """
# Incident Response Plan Development Guide

## Overview
A comprehensive incident response plan is essential for effectively managing and responding to security incidents while minimizing impact and ensuring business continuity.

## Key Components

### 1. Incident Response Team
- **Team Roles**: Define responsibilities and authority
- **Communication Plan**: Establish communication procedures
- **Escalation Procedures**: Define escalation paths
- **External Contacts**: Law enforcement, vendors, legal

### 2. Incident Classification
- **Severity Levels**: Critical, High, Medium, Low
- **Response Times**: Define response time requirements
- **Notification Procedures**: Internal and external notifications
- **Documentation Requirements**: Incident documentation standards

### 3. Response Procedures
- **Detection and Analysis**: Identify and assess incidents
- **Containment**: Isolate affected systems
- **Eradication**: Remove threat and vulnerabilities
- **Recovery**: Restore normal operations
- **Lessons Learned**: Post-incident review

## Implementation Steps

1. **Plan Development**
   - Define incident response procedures
   - Establish team roles and responsibilities
   - Create communication templates
   - Develop escalation procedures

2. **Team Training**
   - Train response team members
   - Conduct tabletop exercises
   - Test communication procedures
   - Validate response procedures

3. **Tool Implementation**
   - Deploy monitoring and detection tools
   - Implement logging and analysis tools
   - Configure alerting systems
   - Set up incident tracking

4. **Testing and Validation**
   - Regular incident response exercises
   - Test communication procedures
   - Validate response times
   - Update procedures based on lessons learned

## Best Practices

- Regular incident response training
- Test procedures regularly
- Maintain updated contact information
- Document all incidents thoroughly
- Learn from each incident
- Update procedures continuously
- Coordinate with external parties
- Maintain evidence integrity
        """

def create_security_best_practices_system(base_url: str = "http://localhost:5000") -> SecurityBestPracticesSystem:
    """Create and configure security best practices system"""
    try:
        system = SecurityBestPracticesSystem()
        logger.info("Security best practices system created successfully")
        return system
    except Exception as e:
        logger.error(f"Error creating security best practices system: {e}")
        raise 