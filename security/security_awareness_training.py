"""
Security Awareness and Training System
Comprehensive security education and policy management for MINGUS
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

class TrainingModuleType(Enum):
    """Types of security training modules"""
    SECURITY_BASICS = "security_basics"
    PASSWORD_SECURITY = "password_security"
    PHISHING_AWARENESS = "phishing_awareness"
    DATA_PROTECTION = "data_protection"
    SOCIAL_ENGINEERING = "social_engineering"
    INCIDENT_RESPONSE = "incident_response"
    COMPLIANCE_TRAINING = "compliance_training"
    PRIVACY_AWARENESS = "privacy_awareness"
    MOBILE_SECURITY = "mobile_security"
    CLOUD_SECURITY = "cloud_security"

class PolicyType(Enum):
    """Types of security policies"""
    ACCEPTABLE_USE = "acceptable_use"
    PASSWORD_POLICY = "password_policy"
    DATA_CLASSIFICATION = "data_classification"
    ACCESS_CONTROL = "access_control"
    INCIDENT_RESPONSE = "incident_response"
    PRIVACY_POLICY = "privacy_policy"
    REMOTE_WORK = "remote_work"
    MOBILE_DEVICE = "mobile_device"
    CLOUD_USAGE = "cloud_usage"
    THIRD_PARTY = "third_party"

class TrainingStatus(Enum):
    """Training completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    OVERDUE = "overdue"

@dataclass_json
@dataclass
class SecurityPolicy:
    """Security policy document"""
    policy_id: str
    policy_type: PolicyType
    title: str
    description: str
    content: str
    version: str
    effective_date: datetime
    review_date: datetime
    applicable_to: List[str]  # User roles or groups
    compliance_requirements: List[str]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    requires_acknowledgment: bool = True
    acknowledgment_deadline: Optional[datetime] = None

@dataclass_json
@dataclass
class TrainingModule:
    """Security training module"""
    module_id: str
    module_type: TrainingModuleType
    title: str
    description: str
    content: str
    duration_minutes: int
    difficulty_level: str  # beginner, intermediate, advanced
    prerequisites: List[str]
    learning_objectives: List[str]
    quiz_questions: List[Dict[str, Any]]
    passing_score: int = 80
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass_json
@dataclass
class UserTrainingRecord:
    """User training completion record"""
    record_id: str
    user_id: str
    module_id: str
    status: TrainingStatus
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    score: Optional[int] = None
    attempts: int = 0
    time_spent_minutes: int = 0
    certificate_issued: bool = False
    certificate_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass_json
@dataclass
class PolicyAcknowledgment:
    """Policy acknowledgment record"""
    acknowledgment_id: str
    user_id: str
    policy_id: str
    acknowledged_at: datetime
    ip_address: str
    user_agent: str
    acknowledgment_text: str
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass_json
@dataclass
class SecurityAwarenessCampaign:
    """Security awareness campaign"""
    campaign_id: str
    title: str
    description: str
    campaign_type: str  # phishing_simulation, security_quiz, awareness_video
    target_audience: List[str]
    start_date: datetime
    end_date: datetime
    content: Dict[str, Any]
    success_metrics: Dict[str, Any]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

class SecurityAwarenessTrainingSystem:
    """
    Comprehensive security awareness and training system
    """
    
    def __init__(self, db_path: str = "/var/lib/mingus/security_training.db"):
        self.db_path = db_path
        self._init_database()
        self._load_default_policies()
        self._load_default_training_modules()
        
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_policies (
                        policy_id TEXT PRIMARY KEY,
                        policy_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        content TEXT NOT NULL,
                        version TEXT NOT NULL,
                        effective_date TEXT NOT NULL,
                        review_date TEXT NOT NULL,
                        applicable_to TEXT,
                        compliance_requirements TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        requires_acknowledgment BOOLEAN DEFAULT 1,
                        acknowledgment_deadline TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS training_modules (
                        module_id TEXT PRIMARY KEY,
                        module_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        content TEXT NOT NULL,
                        duration_minutes INTEGER NOT NULL,
                        difficulty_level TEXT NOT NULL,
                        prerequisites TEXT,
                        learning_objectives TEXT,
                        quiz_questions TEXT,
                        passing_score INTEGER DEFAULT 80,
                        created_by TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        tags TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_training_records (
                        record_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        module_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        start_date TEXT,
                        completion_date TEXT,
                        score INTEGER,
                        attempts INTEGER DEFAULT 0,
                        time_spent_minutes INTEGER DEFAULT 0,
                        certificate_issued BOOLEAN DEFAULT 0,
                        certificate_id TEXT,
                        expires_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS policy_acknowledgments (
                        acknowledgment_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        policy_id TEXT NOT NULL,
                        acknowledged_at TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        acknowledgment_text TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS awareness_campaigns (
                        campaign_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        campaign_type TEXT NOT NULL,
                        target_audience TEXT,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        content TEXT,
                        success_metrics TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_training_user_id ON user_training_records(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_training_module_id ON user_training_records(module_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_ack_user_id ON policy_acknowledgments(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_ack_policy_id ON policy_acknowledgments(policy_id)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _load_default_policies(self):
        """Load default security policies"""
        default_policies = [
            SecurityPolicy(
                policy_id="POL-001",
                policy_type=PolicyType.ACCEPTABLE_USE,
                title="Acceptable Use Policy",
                description="Defines acceptable use of MINGUS systems and data",
                content=self._get_acceptable_use_policy_content(),
                version="1.0",
                effective_date=datetime.utcnow(),
                review_date=datetime.utcnow() + timedelta(days=365),
                applicable_to=["all_users"],
                compliance_requirements=["GDPR", "PCI DSS"],
                created_by="security_team"
            ),
            SecurityPolicy(
                policy_id="POL-002",
                policy_type=PolicyType.PASSWORD_POLICY,
                title="Password Security Policy",
                description="Requirements for strong password creation and management",
                content=self._get_password_policy_content(),
                version="1.0",
                effective_date=datetime.utcnow(),
                review_date=datetime.utcnow() + timedelta(days=365),
                applicable_to=["all_users"],
                compliance_requirements=["NIST", "ISO 27001"],
                created_by="security_team"
            ),
            SecurityPolicy(
                policy_id="POL-003",
                policy_type=PolicyType.DATA_CLASSIFICATION,
                title="Data Classification Policy",
                description="Guidelines for classifying and handling different types of data",
                content=self._get_data_classification_policy_content(),
                version="1.0",
                effective_date=datetime.utcnow(),
                review_date=datetime.utcnow() + timedelta(days=365),
                applicable_to=["all_users"],
                compliance_requirements=["GDPR", "HIPAA"],
                created_by="security_team"
            ),
            SecurityPolicy(
                policy_id="POL-004",
                policy_type=PolicyType.PRIVACY_POLICY,
                title="Privacy Policy",
                description="How MINGUS collects, uses, and protects personal data",
                content=self._get_privacy_policy_content(),
                version="1.0",
                effective_date=datetime.utcnow(),
                review_date=datetime.utcnow() + timedelta(days=365),
                applicable_to=["all_users"],
                compliance_requirements=["GDPR", "CCPA"],
                created_by="legal_team"
            )
        ]
        
        for policy in default_policies:
            self.create_security_policy(policy)
    
    def _load_default_training_modules(self):
        """Load default training modules"""
        default_modules = [
            TrainingModule(
                module_id="TRAIN-001",
                module_type=TrainingModuleType.SECURITY_BASICS,
                title="Security Fundamentals",
                description="Introduction to basic security concepts and best practices",
                content=self._get_security_basics_content(),
                duration_minutes=30,
                difficulty_level="beginner",
                prerequisites=[],
                learning_objectives=[
                    "Understand basic security concepts",
                    "Identify common security threats",
                    "Learn fundamental security practices"
                ],
                quiz_questions=self._get_security_basics_quiz(),
                created_by="security_team"
            ),
            TrainingModule(
                module_id="TRAIN-002",
                module_type=TrainingModuleType.PHISHING_AWARENESS,
                title="Phishing Awareness Training",
                description="Learn to identify and avoid phishing attacks",
                content=self._get_phishing_awareness_content(),
                duration_minutes=45,
                difficulty_level="beginner",
                prerequisites=["TRAIN-001"],
                learning_objectives=[
                    "Recognize phishing email indicators",
                    "Understand social engineering tactics",
                    "Learn safe email practices"
                ],
                quiz_questions=self._get_phishing_quiz(),
                created_by="security_team"
            ),
            TrainingModule(
                module_id="TRAIN-003",
                module_type=TrainingModuleType.PASSWORD_SECURITY,
                title="Password Security Best Practices",
                description="Creating and managing strong, secure passwords",
                content=self._get_password_security_content(),
                duration_minutes=25,
                difficulty_level="beginner",
                prerequisites=[],
                learning_objectives=[
                    "Create strong passwords",
                    "Use password managers effectively",
                    "Implement multi-factor authentication"
                ],
                quiz_questions=self._get_password_security_quiz(),
                created_by="security_team"
            )
        ]
        
        for module in default_modules:
            self.create_training_module(module)
    
    def create_security_policy(self, policy: SecurityPolicy) -> bool:
        """Create a new security policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO security_policies 
                    (policy_id, policy_type, title, description, content, version, 
                     effective_date, review_date, applicable_to, compliance_requirements,
                     created_by, created_at, updated_at, is_active, requires_acknowledgment,
                     acknowledgment_deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy.policy_id,
                    policy.policy_type.value,
                    policy.title,
                    policy.description,
                    policy.content,
                    policy.version,
                    policy.effective_date.isoformat(),
                    policy.review_date.isoformat(),
                    json.dumps(policy.applicable_to),
                    json.dumps(policy.compliance_requirements),
                    policy.created_by,
                    policy.created_at.isoformat(),
                    policy.updated_at.isoformat(),
                    policy.is_active,
                    policy.requires_acknowledgment,
                    policy.acknowledgment_deadline.isoformat() if policy.acknowledgment_deadline else None
                ))
                conn.commit()
                logger.info(f"Created security policy: {policy.policy_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating security policy: {e}")
            return False
    
    def get_security_policies(self, user_role: str = "all_users", active_only: bool = True) -> List[SecurityPolicy]:
        """Get security policies applicable to a user role"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM security_policies 
                    WHERE (applicable_to LIKE ? OR applicable_to LIKE ?)
                    AND is_active = ?
                    ORDER BY effective_date DESC
                """, (f"%{user_role}%", "%all_users%", active_only))
                
                policies = []
                for row in cursor.fetchall():
                    policy = SecurityPolicy(
                        policy_id=row[0],
                        policy_type=PolicyType(row[1]),
                        title=row[2],
                        description=row[3],
                        content=row[4],
                        version=row[5],
                        effective_date=datetime.fromisoformat(row[6]),
                        review_date=datetime.fromisoformat(row[7]),
                        applicable_to=json.loads(row[8]),
                        compliance_requirements=json.loads(row[9]),
                        created_by=row[10],
                        created_at=datetime.fromisoformat(row[11]),
                        updated_at=datetime.fromisoformat(row[12]),
                        is_active=bool(row[13]),
                        requires_acknowledgment=bool(row[14]),
                        acknowledgment_deadline=datetime.fromisoformat(row[15]) if row[15] else None
                    )
                    policies.append(policy)
                
                return policies
        except Exception as e:
            logger.error(f"Error getting security policies: {e}")
            return []
    
    def create_training_module(self, module: TrainingModule) -> bool:
        """Create a new training module"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO training_modules 
                    (module_id, module_type, title, description, content, duration_minutes,
                     difficulty_level, prerequisites, learning_objectives, quiz_questions,
                     passing_score, created_by, created_at, updated_at, is_active, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    module.module_id,
                    module.module_type.value,
                    module.title,
                    module.description,
                    module.content,
                    module.duration_minutes,
                    module.difficulty_level,
                    json.dumps(module.prerequisites),
                    json.dumps(module.learning_objectives),
                    json.dumps(module.quiz_questions),
                    module.passing_score,
                    module.created_by,
                    module.created_at.isoformat(),
                    module.updated_at.isoformat(),
                    module.is_active,
                    json.dumps(module.tags)
                ))
                conn.commit()
                logger.info(f"Created training module: {module.module_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating training module: {e}")
            return False
    
    def get_training_modules(self, user_role: str = "all_users", active_only: bool = True) -> List[TrainingModule]:
        """Get available training modules"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM training_modules 
                    WHERE is_active = ?
                    ORDER BY difficulty_level, title
                """, (active_only,))
                
                modules = []
                for row in cursor.fetchall():
                    module = TrainingModule(
                        module_id=row[0],
                        module_type=TrainingModuleType(row[1]),
                        title=row[2],
                        description=row[3],
                        content=row[4],
                        duration_minutes=row[5],
                        difficulty_level=row[6],
                        prerequisites=json.loads(row[7]),
                        learning_objectives=json.loads(row[8]),
                        quiz_questions=json.loads(row[9]),
                        passing_score=row[10],
                        created_by=row[11],
                        created_at=datetime.fromisoformat(row[12]),
                        updated_at=datetime.fromisoformat(row[13]),
                        is_active=bool(row[14]),
                        tags=json.loads(row[15]) if row[15] else []
                    )
                    modules.append(module)
                
                return modules
        except Exception as e:
            logger.error(f"Error getting training modules: {e}")
            return []
    
    def assign_training_to_user(self, user_id: str, module_id: str, 
                              due_date: Optional[datetime] = None) -> bool:
        """Assign a training module to a user"""
        try:
            record = UserTrainingRecord(
                record_id=str(uuid.uuid4()),
                user_id=user_id,
                module_id=module_id,
                status=TrainingStatus.NOT_STARTED,
                expires_at=due_date
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_training_records 
                    (record_id, user_id, module_id, status, start_date, completion_date,
                     score, attempts, time_spent_minutes, certificate_issued, certificate_id,
                     expires_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.record_id,
                    record.user_id,
                    record.module_id,
                    record.status.value,
                    record.start_date.isoformat() if record.start_date else None,
                    record.completion_date.isoformat() if record.completion_date else None,
                    record.score,
                    record.attempts,
                    record.time_spent_minutes,
                    record.certificate_issued,
                    record.certificate_id,
                    record.expires_at.isoformat() if record.expires_at else None,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat()
                ))
                conn.commit()
                logger.info(f"Assigned training {module_id} to user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error assigning training: {e}")
            return False
    
    def get_user_training_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive training status for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get user's training records
                cursor = conn.execute("""
                    SELECT utr.*, tm.title, tm.module_type, tm.duration_minutes
                    FROM user_training_records utr
                    JOIN training_modules tm ON utr.module_id = tm.module_id
                    WHERE utr.user_id = ?
                    ORDER BY utr.created_at DESC
                """, (user_id,))
                
                training_records = []
                completed_count = 0
                overdue_count = 0
                total_modules = 0
                
                for row in cursor.fetchall():
                    record = {
                        'record_id': row[0],
                        'module_id': row[1],
                        'module_title': row[13],
                        'module_type': row[14],
                        'status': row[3],
                        'start_date': row[4],
                        'completion_date': row[5],
                        'score': row[6],
                        'attempts': row[7],
                        'time_spent_minutes': row[8],
                        'certificate_issued': row[9],
                        'expires_at': row[11],
                        'duration_minutes': row[15]
                    }
                    training_records.append(record)
                    
                    if record['status'] == TrainingStatus.COMPLETED.value:
                        completed_count += 1
                    elif record['status'] == TrainingStatus.OVERDUE.value:
                        overdue_count += 1
                    total_modules += 1
                
                # Get policy acknowledgments
                cursor = conn.execute("""
                    SELECT pa.*, sp.title as policy_title
                    FROM policy_acknowledgments pa
                    JOIN security_policies sp ON pa.policy_id = sp.policy_id
                    WHERE pa.user_id = ?
                    ORDER BY pa.acknowledged_at DESC
                """, (user_id,))
                
                policy_acknowledgments = []
                for row in cursor.fetchall():
                    acknowledgment = {
                        'acknowledgment_id': row[0],
                        'policy_id': row[1],
                        'policy_title': row[7],
                        'acknowledged_at': row[3],
                        'ip_address': row[4],
                        'user_agent': row[5]
                    }
                    policy_acknowledgments.append(acknowledgment)
                
                # Calculate completion percentage
                completion_percentage = (completed_count / total_modules * 100) if total_modules > 0 else 0
                
                return {
                    'user_id': user_id,
                    'training_records': training_records,
                    'policy_acknowledgments': policy_acknowledgments,
                    'completion_percentage': completion_percentage,
                    'completed_count': completed_count,
                    'overdue_count': overdue_count,
                    'total_modules': total_modules,
                    'compliance_status': 'compliant' if overdue_count == 0 else 'non_compliant'
                }
        except Exception as e:
            logger.error(f"Error getting user training status: {e}")
            return {}
    
    def acknowledge_policy(self, user_id: str, policy_id: str, 
                         ip_address: str, user_agent: str) -> bool:
        """Record policy acknowledgment by user"""
        try:
            acknowledgment = PolicyAcknowledgment(
                acknowledgment_id=str(uuid.uuid4()),
                user_id=user_id,
                policy_id=policy_id,
                acknowledged_at=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                acknowledgment_text="I acknowledge that I have read and understood this policy."
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO policy_acknowledgments 
                    (acknowledgment_id, user_id, policy_id, acknowledged_at, 
                     ip_address, user_agent, acknowledgment_text, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    acknowledgment.acknowledgment_id,
                    acknowledgment.user_id,
                    acknowledgment.policy_id,
                    acknowledgment.acknowledged_at.isoformat(),
                    acknowledgment.ip_address,
                    acknowledgment.user_agent,
                    acknowledgment.acknowledgment_text,
                    acknowledgment.created_at.isoformat()
                ))
                conn.commit()
                logger.info(f"Policy {policy_id} acknowledged by user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error acknowledging policy: {e}")
            return False
    
    def create_awareness_campaign(self, campaign: SecurityAwarenessCampaign) -> bool:
        """Create a new security awareness campaign"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO awareness_campaigns 
                    (campaign_id, title, description, campaign_type, target_audience,
                     start_date, end_date, content, success_metrics, created_by, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    campaign.campaign_id,
                    campaign.title,
                    campaign.description,
                    campaign.campaign_type,
                    json.dumps(campaign.target_audience),
                    campaign.start_date.isoformat(),
                    campaign.end_date.isoformat(),
                    json.dumps(campaign.content),
                    json.dumps(campaign.success_metrics),
                    campaign.created_by,
                    campaign.created_at.isoformat(),
                    campaign.is_active
                ))
                conn.commit()
                logger.info(f"Created awareness campaign: {campaign.campaign_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating awareness campaign: {e}")
            return False
    
    def get_active_campaigns(self, user_role: str = "all_users") -> List[SecurityAwarenessCampaign]:
        """Get active awareness campaigns for a user role"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM awareness_campaigns 
                    WHERE is_active = 1 
                    AND start_date <= ? 
                    AND end_date >= ?
                    ORDER BY start_date DESC
                """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
                
                campaigns = []
                for row in cursor.fetchall():
                    campaign = SecurityAwarenessCampaign(
                        campaign_id=row[0],
                        title=row[1],
                        description=row[2],
                        campaign_type=row[3],
                        target_audience=json.loads(row[4]),
                        start_date=datetime.fromisoformat(row[5]),
                        end_date=datetime.fromisoformat(row[6]),
                        content=json.loads(row[7]),
                        success_metrics=json.loads(row[8]),
                        created_by=row[9],
                        created_at=datetime.fromisoformat(row[10]),
                        is_active=bool(row[11])
                    )
                    campaigns.append(campaign)
                
                return campaigns
        except Exception as e:
            logger.error(f"Error getting active campaigns: {e}")
            return []
    
    def generate_training_report(self, user_id: Optional[str] = None, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive training and awareness report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Training completion statistics
                if user_id:
                    cursor = conn.execute("""
                        SELECT COUNT(*) as total, 
                               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                               SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue
                        FROM user_training_records 
                        WHERE user_id = ?
                    """, (user_id,))
                else:
                    cursor = conn.execute("""
                        SELECT COUNT(*) as total, 
                               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                               SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue
                        FROM user_training_records
                    """)
                
                training_stats = cursor.fetchone()
                
                # Policy acknowledgment statistics
                if user_id:
                    cursor = conn.execute("""
                        SELECT COUNT(DISTINCT policy_id) as acknowledged_policies
                        FROM policy_acknowledgments 
                        WHERE user_id = ?
                    """, (user_id,))
                else:
                    cursor = conn.execute("""
                        SELECT COUNT(DISTINCT policy_id) as acknowledged_policies
                        FROM policy_acknowledgments
                    """)
                
                policy_stats = cursor.fetchone()
                
                # Campaign participation
                if user_id:
                    cursor = conn.execute("""
                        SELECT COUNT(*) as campaign_participation
                        FROM awareness_campaigns 
                        WHERE is_active = 1 
                        AND start_date <= ? 
                        AND end_date >= ?
                    """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
                else:
                    cursor = conn.execute("""
                        SELECT COUNT(*) as campaign_participation
                        FROM awareness_campaigns 
                        WHERE is_active = 1 
                        AND start_date <= ? 
                        AND end_date >= ?
                    """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
                
                campaign_stats = cursor.fetchone()
                
                return {
                    'report_generated_at': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'training_statistics': {
                        'total_assignments': training_stats[0] if training_stats else 0,
                        'completed_trainings': training_stats[1] if training_stats else 0,
                        'overdue_trainings': training_stats[2] if training_stats else 0,
                        'completion_rate': (training_stats[1] / training_stats[0] * 100) if training_stats and training_stats[0] > 0 else 0
                    },
                    'policy_statistics': {
                        'acknowledged_policies': policy_stats[0] if policy_stats else 0
                    },
                    'campaign_statistics': {
                        'active_campaigns': campaign_stats[0] if campaign_stats else 0
                    },
                    'compliance_status': 'compliant' if (training_stats and training_stats[2] == 0) else 'non_compliant'
                }
        except Exception as e:
            logger.error(f"Error generating training report: {e}")
            return {}
    
    # Policy content generators
    def _get_acceptable_use_policy_content(self) -> str:
        return """
# Acceptable Use Policy

## 1. Purpose
This policy defines acceptable use of MINGUS systems, networks, and data resources.

## 2. Scope
This policy applies to all users of MINGUS systems and services.

## 3. Acceptable Use
- Use systems for authorized business purposes only
- Protect confidential information and data
- Report security incidents immediately
- Follow password and access control procedures
- Use approved software and applications only

## 4. Prohibited Activities
- Unauthorized access to systems or data
- Sharing credentials or access tokens
- Installing unauthorized software
- Circumventing security controls
- Using systems for personal gain or illegal activities

## 5. Data Protection
- Classify data according to sensitivity levels
- Use encryption for sensitive data transmission
- Follow data retention and disposal procedures
- Report data breaches immediately

## 6. Compliance
- Comply with all applicable laws and regulations
- Follow industry best practices
- Participate in required security training
- Acknowledge policy understanding annually
        """
    
    def _get_password_policy_content(self) -> str:
        return """
# Password Security Policy

## 1. Password Requirements
- Minimum 12 characters in length
- Include uppercase and lowercase letters
- Include numbers and special characters
- Avoid common words and patterns
- No personal information (names, dates, etc.)

## 2. Password Management
- Use unique passwords for each account
- Change passwords every 90 days
- Use password managers for secure storage
- Never share passwords or write them down
- Enable multi-factor authentication where available

## 3. Password Reset Procedures
- Use secure password reset methods
- Verify identity before resetting passwords
- Choose new passwords that meet requirements
- Update all related accounts if compromised

## 4. Multi-Factor Authentication
- Enable MFA on all supported accounts
- Use authenticator apps or hardware tokens
- Keep backup codes in secure location
- Report lost or stolen authentication devices

## 5. Password Security Best Practices
- Log out of accounts when finished
- Use secure networks for password entry
- Be aware of phishing attempts
- Report suspicious password-related activities
        """
    
    def _get_data_classification_policy_content(self) -> str:
        return """
# Data Classification Policy

## 1. Data Classification Levels

### Public Data
- Information approved for public release
- No special handling required
- Examples: marketing materials, public announcements

### Internal Data
- Information for internal use only
- Basic security controls required
- Examples: internal communications, operational data

### Confidential Data
- Sensitive business information
- Enhanced security controls required
- Examples: financial data, customer information

### Restricted Data
- Highly sensitive information
- Maximum security controls required
- Examples: personal health data, payment card data

## 2. Handling Requirements
- Label data according to classification
- Use appropriate storage and transmission methods
- Apply access controls based on classification
- Follow retention and disposal procedures

## 3. Data Protection Measures
- Encryption for confidential and restricted data
- Access logging and monitoring
- Regular security assessments
- Incident response procedures

## 4. Compliance Requirements
- Follow industry-specific regulations
- Maintain audit trails
- Report data breaches promptly
- Regular policy review and updates
        """
    
    def _get_privacy_policy_content(self) -> str:
        return """
# Privacy Policy

## 1. Information We Collect
- Personal information (name, email, contact details)
- Financial information (income, expenses, goals)
- Health information (wellness metrics, check-ins)
- Career information (resume data, job preferences)
- Usage data (app interactions, preferences)

## 2. How We Use Information
- Provide personalized financial and wellness insights
- Deliver career recommendations and job matching
- Improve our services and user experience
- Comply with legal and regulatory requirements
- Send relevant notifications and updates

## 3. Information Sharing
- We do not sell personal information
- Share data only with user consent
- Use third-party services with appropriate safeguards
- Comply with legal requests when required

## 4. Data Security
- Implement industry-standard security measures
- Use encryption for data transmission and storage
- Regular security assessments and updates
- Access controls and monitoring

## 5. User Rights
- Access and review personal data
- Request data correction or deletion
- Opt out of certain data processing
- Export data in portable format
- Withdraw consent at any time

## 6. Data Retention
- Retain data only as long as necessary
- Delete data upon user request
- Maintain records for legal compliance
- Secure disposal of data

## 7. Contact Information
- Privacy questions: privacy@mingus.com
- Data requests: data@mingus.com
- Security concerns: security@mingus.com
        """
    
    # Training content generators
    def _get_security_basics_content(self) -> str:
        return """
# Security Fundamentals

## What is Information Security?
Information security protects data from unauthorized access, use, disclosure, disruption, modification, or destruction.

## The CIA Triad
- **Confidentiality**: Information is accessible only to authorized users
- **Integrity**: Information is accurate and complete
- **Availability**: Information is accessible when needed

## Common Security Threats
- **Malware**: Viruses, ransomware, spyware
- **Phishing**: Deceptive emails and websites
- **Social Engineering**: Manipulation of people
- **Password Attacks**: Brute force, dictionary attacks
- **Physical Security**: Unauthorized access to devices

## Basic Security Practices
- Use strong, unique passwords
- Enable multi-factor authentication
- Keep software updated
- Be cautious with email attachments
- Lock devices when unattended
- Report suspicious activities

## Incident Response
- Recognize security incidents
- Report incidents immediately
- Follow incident response procedures
- Preserve evidence when possible
- Learn from incidents to prevent recurrence
        """
    
    def _get_phishing_awareness_content(self) -> str:
        return """
# Phishing Awareness Training

## What is Phishing?
Phishing is a cyber attack that uses deceptive emails, websites, or messages to steal sensitive information.

## Common Phishing Indicators
- **Urgency**: "Act now or account will be closed"
- **Authority**: Impersonating trusted organizations
- **Emotion**: Creating fear, excitement, or curiosity
- **Suspicious Links**: URLs that don't match the sender
- **Poor Grammar**: Spelling and grammar errors
- **Requests for Information**: Asking for passwords, SSN, etc.

## Types of Phishing
- **Email Phishing**: Deceptive emails
- **Spear Phishing**: Targeted attacks
- **Whaling**: Attacks on executives
- **Vishing**: Voice-based phishing
- **Smishing**: SMS-based phishing

## How to Spot Phishing
- Check sender email addresses carefully
- Hover over links before clicking
- Look for HTTPS in URLs
- Verify requests through official channels
- Trust your instincts - if it seems suspicious, it probably is

## Safe Email Practices
- Don't click suspicious links
- Don't download unexpected attachments
- Don't reply to suspicious emails
- Don't provide sensitive information via email
- Use spam filters and security software

## Reporting Phishing
- Report suspicious emails to IT security
- Forward phishing emails to security team
- Don't delete evidence
- Follow organization's reporting procedures
        """
    
    def _get_password_security_content(self) -> str:
        return """
# Password Security Best Practices

## Creating Strong Passwords
- Use at least 12 characters
- Include uppercase and lowercase letters
- Include numbers and special characters
- Avoid common words and patterns
- Don't use personal information

## Password Examples
**Weak**: password123, john1985, qwerty
**Strong**: K9#mN2$pL8@vX, Tr0ub4dor&3, correcthorsebatterystaple

## Password Management
- Use unique passwords for each account
- Use a password manager
- Never share passwords
- Don't write passwords down
- Change passwords regularly

## Multi-Factor Authentication (MFA)
- Enable MFA on all accounts
- Use authenticator apps
- Keep backup codes secure
- Report lost devices immediately

## Password Security Tips
- Use passphrases for better memorability
- Consider password strength checkers
- Be aware of password breaches
- Update passwords after data breaches
- Use different passwords for work and personal accounts

## Common Password Mistakes
- Using the same password everywhere
- Using simple patterns
- Sharing passwords with others
- Storing passwords in plain text
- Not changing default passwords
        """
    
    # Quiz generators
    def _get_security_basics_quiz(self) -> List[Dict[str, Any]]:
        return [
            {
                "question": "What does the 'C' in CIA triad stand for?",
                "options": ["Confidentiality", "Control", "Compliance", "Confidence"],
                "correct_answer": 0,
                "explanation": "Confidentiality ensures that information is accessible only to authorized users."
            },
            {
                "question": "Which of the following is NOT a common security threat?",
                "options": ["Malware", "Phishing", "Social Engineering", "Rainbow attacks"],
                "correct_answer": 3,
                "explanation": "Rainbow attacks are not a common security threat. The other options are well-known threats."
            },
            {
                "question": "What should you do if you suspect a security incident?",
                "options": ["Ignore it", "Report it immediately", "Try to fix it yourself", "Wait and see"],
                "correct_answer": 1,
                "explanation": "Security incidents should be reported immediately to the appropriate team."
            }
        ]
    
    def _get_phishing_quiz(self) -> List[Dict[str, Any]]:
        return [
            {
                "question": "Which of the following is a red flag for phishing emails?",
                "options": ["Professional formatting", "Urgent action required", "Clear sender address", "Proper grammar"],
                "correct_answer": 1,
                "explanation": "Urgent action required is a common phishing tactic to pressure victims into acting quickly."
            },
            {
                "question": "What should you do with a suspicious email?",
                "options": ["Click all links to investigate", "Reply to the sender", "Forward to security team", "Delete immediately"],
                "correct_answer": 2,
                "explanation": "Forwarding suspicious emails to the security team helps them investigate and protect others."
            },
            {
                "question": "Which URL is most likely legitimate?",
                "options": ["www.bank-secure.com", "www.bank.com.secure.net", "www.bank.com", "www.secure-bank.net"],
                "correct_answer": 2,
                "explanation": "Simple, well-known domain names are more likely to be legitimate than complex variations."
            }
        ]
    
    def _get_password_security_quiz(self) -> List[Dict[str, Any]]:
        return [
            {
                "question": "What is the minimum recommended password length?",
                "options": ["8 characters", "10 characters", "12 characters", "16 characters"],
                "correct_answer": 2,
                "explanation": "12 characters is the current industry standard for minimum password length."
            },
            {
                "question": "Which password is strongest?",
                "options": ["password123", "P@ssw0rd", "MyDogSpot2023!", "CorrectHorseBatteryStaple"],
                "correct_answer": 2,
                "explanation": "This password includes uppercase, lowercase, numbers, and special characters."
            },
            {
                "question": "What should you do if you suspect your password has been compromised?",
                "options": ["Wait and see", "Change it immediately", "Tell a friend", "Ignore it"],
                "correct_answer": 1,
                "explanation": "Immediately changing a compromised password helps prevent unauthorized access."
            }
        ]

def create_security_awareness_training_system(base_url: str = "http://localhost:5000") -> SecurityAwarenessTrainingSystem:
    """Create and configure security awareness training system"""
    try:
        system = SecurityAwarenessTrainingSystem()
        logger.info("Security awareness training system created successfully")
        return system
    except Exception as e:
        logger.error(f"Error creating security awareness training system: {e}")
        raise 