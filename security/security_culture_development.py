"""
Security Culture Development Module
Comprehensive security culture assessment and development for MINGUS
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

class CultureDimension(Enum):
    """Security culture dimensions"""
    AWARENESS = "awareness"
    ATTITUDE = "attitude"
    BEHAVIOR = "behavior"
    COMPLIANCE = "compliance"
    LEADERSHIP = "leadership"
    COMMUNICATION = "communication"
    TRAINING = "training"
    INCENTIVES = "incentives"

class MaturityLevel(Enum):
    """Security culture maturity levels"""
    INITIAL = "initial"
    DEVELOPING = "developing"
    DEFINED = "defined"
    MANAGED = "managed"
    OPTIMIZING = "optimizing"

class AssessmentType(Enum):
    """Types of security culture assessments"""
    SURVEY = "survey"
    INTERVIEW = "interview"
    OBSERVATION = "observation"
    METRICS_ANALYSIS = "metrics_analysis"
    FOCUS_GROUP = "focus_group"

@dataclass_json
@dataclass
class SecurityCultureAssessment:
    """Security culture assessment"""
    assessment_id: str
    title: str
    description: str
    assessment_type: AssessmentType
    dimensions: List[CultureDimension]
    questions: List[Dict[str, Any]]
    target_audience: List[str]
    duration_minutes: int
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

@dataclass_json
@dataclass
class AssessmentResponse:
    """Assessment response from participant"""
    response_id: str
    assessment_id: str
    participant_id: str
    department: str
    role: str
    responses: List[Dict[str, Any]]
    completion_date: datetime
    score: Optional[float] = None
    insights: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass_json
@dataclass
class SecurityCultureInitiative:
    """Security culture improvement initiative"""
    initiative_id: str
    title: str
    description: str
    target_dimensions: List[CultureDimension]
    objectives: List[str]
    activities: List[Dict[str, Any]]
    target_audience: List[str]
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = None
    success_metrics: List[str]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

@dataclass_json
@dataclass
class CultureMetrics:
    """Security culture metrics"""
    metrics_id: str
    dimension: CultureDimension
    metric_name: str
    metric_value: float
    target_value: float
    measurement_date: datetime
    department: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

class SecurityCultureDevelopmentSystem:
    """
    Comprehensive security culture development system
    """
    
    def __init__(self, db_path: str = "/var/lib/mingus/security_culture.db"):
        self.db_path = db_path
        self._init_database()
        self._load_default_assessments()
        self._load_default_initiatives()
        
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_culture_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        assessment_type TEXT NOT NULL,
                        dimensions TEXT,
                        questions TEXT,
                        target_audience TEXT,
                        duration_minutes INTEGER NOT NULL,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS assessment_responses (
                        response_id TEXT PRIMARY KEY,
                        assessment_id TEXT NOT NULL,
                        participant_id TEXT NOT NULL,
                        department TEXT,
                        role TEXT,
                        responses TEXT,
                        completion_date TEXT NOT NULL,
                        score REAL,
                        insights TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_culture_initiatives (
                        initiative_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        target_dimensions TEXT,
                        objectives TEXT,
                        activities TEXT,
                        target_audience TEXT,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        budget REAL,
                        success_metrics TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS culture_metrics (
                        metrics_id TEXT PRIMARY KEY,
                        dimension TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        target_value REAL NOT NULL,
                        measurement_date TEXT NOT NULL,
                        department TEXT,
                        notes TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_assessment_type ON security_culture_assessments(assessment_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_response_assessment ON assessment_responses(assessment_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_response_participant ON assessment_responses(participant_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_initiative_dimensions ON security_culture_initiatives(target_dimensions)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_dimension ON culture_metrics(dimension)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _load_default_assessments(self):
        """Load default security culture assessments"""
        default_assessments = [
            SecurityCultureAssessment(
                assessment_id="ASSESS-001",
                title="Security Culture Survey",
                description="Comprehensive security culture assessment survey",
                assessment_type=AssessmentType.SURVEY,
                dimensions=[
                    CultureDimension.AWARENESS,
                    CultureDimension.ATTITUDE,
                    CultureDimension.BEHAVIOR,
                    CultureDimension.COMPLIANCE
                ],
                questions=self._get_culture_survey_questions(),
                target_audience=["all_employees"],
                duration_minutes=15,
                created_by="security_team"
            ),
            SecurityCultureAssessment(
                assessment_id="ASSESS-002",
                title="Leadership Security Culture Assessment",
                description="Assessment focused on leadership security culture",
                assessment_type=AssessmentType.INTERVIEW,
                dimensions=[
                    CultureDimension.LEADERSHIP,
                    CultureDimension.COMMUNICATION,
                    CultureDimension.ATTITUDE
                ],
                questions=self._get_leadership_assessment_questions(),
                target_audience=["managers", "executives"],
                duration_minutes=45,
                created_by="security_team"
            )
        ]
        
        for assessment in default_assessments:
            self.create_assessment(assessment)
    
    def _load_default_initiatives(self):
        """Load default security culture initiatives"""
        default_initiatives = [
            SecurityCultureInitiative(
                initiative_id="INIT-001",
                title="Security Champions Program",
                description="Establish security champions across departments",
                target_dimensions=[
                    CultureDimension.LEADERSHIP,
                    CultureDimension.COMMUNICATION,
                    CultureDimension.AWARENESS
                ],
                objectives=[
                    "Increase security awareness across departments",
                    "Improve security communication",
                    "Build security leadership capabilities"
                ],
                activities=self._get_security_champions_activities(),
                target_audience=["department_representatives"],
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365),
                budget=50000.0,
                success_metrics=[
                    "Number of security champions",
                    "Department engagement levels",
                    "Security awareness scores"
                ],
                created_by="security_team"
            ),
            SecurityCultureInitiative(
                initiative_id="INIT-002",
                title="Security Recognition Program",
                description="Recognize and reward security-conscious behavior",
                target_dimensions=[
                    CultureDimension.BEHAVIOR,
                    CultureDimension.ATTITUDE,
                    CultureDimension.INCENTIVES
                ],
                objectives=[
                    "Encourage security-conscious behavior",
                    "Improve security attitudes",
                    "Create positive security culture"
                ],
                activities=self._get_recognition_program_activities(),
                target_audience=["all_employees"],
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=180),
                budget=25000.0,
                success_metrics=[
                    "Security incident reduction",
                    "Employee participation rates",
                    "Security behavior improvements"
                ],
                created_by="security_team"
            )
        ]
        
        for initiative in default_initiatives:
            self.create_initiative(initiative)
    
    def create_assessment(self, assessment: SecurityCultureAssessment) -> bool:
        """Create a new security culture assessment"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO security_culture_assessments 
                    (assessment_id, title, description, assessment_type, dimensions,
                     questions, target_audience, duration_minutes, created_by,
                     created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    assessment.assessment_id,
                    assessment.title,
                    assessment.description,
                    assessment.assessment_type.value,
                    json.dumps([d.value for d in assessment.dimensions]),
                    json.dumps(assessment.questions),
                    json.dumps(assessment.target_audience),
                    assessment.duration_minutes,
                    assessment.created_by,
                    assessment.created_at.isoformat(),
                    assessment.updated_at.isoformat(),
                    assessment.is_active
                ))
                conn.commit()
                logger.info(f"Created security culture assessment: {assessment.assessment_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating assessment: {e}")
            return False
    
    def get_assessments(self, assessment_type: Optional[AssessmentType] = None,
                       target_audience: Optional[str] = None,
                       active_only: bool = True) -> List[SecurityCultureAssessment]:
        """Get security culture assessments with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM security_culture_assessments WHERE is_active = ?"
                params = [active_only]
                
                if assessment_type:
                    query += " AND assessment_type = ?"
                    params.append(assessment_type.value)
                
                if target_audience:
                    query += " AND target_audience LIKE ?"
                    params.append(f"%{target_audience}%")
                
                query += " ORDER BY created_at DESC"
                
                cursor = conn.execute(query, params)
                
                assessments = []
                for row in cursor.fetchall():
                    assessment = SecurityCultureAssessment(
                        assessment_id=row[0],
                        title=row[1],
                        description=row[2],
                        assessment_type=AssessmentType(row[3]),
                        dimensions=[CultureDimension(d) for d in json.loads(row[4])],
                        questions=json.loads(row[5]),
                        target_audience=json.loads(row[6]),
                        duration_minutes=row[7],
                        created_by=row[8],
                        created_at=datetime.fromisoformat(row[9]),
                        updated_at=datetime.fromisoformat(row[10]),
                        is_active=bool(row[11])
                    )
                    assessments.append(assessment)
                
                return assessments
        except Exception as e:
            logger.error(f"Error getting assessments: {e}")
            return []
    
    def submit_assessment_response(self, response: AssessmentResponse) -> bool:
        """Submit an assessment response"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO assessment_responses 
                    (response_id, assessment_id, participant_id, department, role,
                     responses, completion_date, score, insights, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    response.response_id,
                    response.assessment_id,
                    response.participant_id,
                    response.department,
                    response.role,
                    json.dumps(response.responses),
                    response.completion_date.isoformat(),
                    response.score,
                    json.dumps(response.insights),
                    response.created_at.isoformat()
                ))
                conn.commit()
                logger.info(f"Submitted assessment response: {response.response_id}")
                return True
        except Exception as e:
            logger.error(f"Error submitting assessment response: {e}")
            return False
    
    def create_initiative(self, initiative: SecurityCultureInitiative) -> bool:
        """Create a new security culture initiative"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO security_culture_initiatives 
                    (initiative_id, title, description, target_dimensions, objectives,
                     activities, target_audience, start_date, end_date, budget,
                     success_metrics, created_by, created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    initiative.initiative_id,
                    initiative.title,
                    initiative.description,
                    json.dumps([d.value for d in initiative.target_dimensions]),
                    json.dumps(initiative.objectives),
                    json.dumps(initiative.activities),
                    json.dumps(initiative.target_audience),
                    initiative.start_date.isoformat(),
                    initiative.end_date.isoformat(),
                    initiative.budget,
                    json.dumps(initiative.success_metrics),
                    initiative.created_by,
                    initiative.created_at.isoformat(),
                    initiative.updated_at.isoformat(),
                    initiative.is_active
                ))
                conn.commit()
                logger.info(f"Created security culture initiative: {initiative.initiative_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating initiative: {e}")
            return False
    
    def get_initiatives(self, target_dimension: Optional[CultureDimension] = None,
                       active_only: bool = True) -> List[SecurityCultureInitiative]:
        """Get security culture initiatives"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM security_culture_initiatives WHERE is_active = ?"
                params = [active_only]
                
                if target_dimension:
                    query += " AND target_dimensions LIKE ?"
                    params.append(f"%{target_dimension.value}%")
                
                query += " ORDER BY start_date DESC"
                
                cursor = conn.execute(query, params)
                
                initiatives = []
                for row in cursor.fetchall():
                    initiative = SecurityCultureInitiative(
                        initiative_id=row[0],
                        title=row[1],
                        description=row[2],
                        target_dimensions=[CultureDimension(d) for d in json.loads(row[3])],
                        objectives=json.loads(row[4]),
                        activities=json.loads(row[5]),
                        target_audience=json.loads(row[6]),
                        start_date=datetime.fromisoformat(row[7]),
                        end_date=datetime.fromisoformat(row[8]),
                        budget=row[9],
                        success_metrics=json.loads(row[10]),
                        created_by=row[11],
                        created_at=datetime.fromisoformat(row[12]),
                        updated_at=datetime.fromisoformat(row[13]),
                        is_active=bool(row[14])
                    )
                    initiatives.append(initiative)
                
                return initiatives
        except Exception as e:
            logger.error(f"Error getting initiatives: {e}")
            return []
    
    def record_culture_metrics(self, metrics: CultureMetrics) -> bool:
        """Record security culture metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO culture_metrics 
                    (metrics_id, dimension, metric_name, metric_value, target_value,
                     measurement_date, department, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.metrics_id,
                    metrics.dimension.value,
                    metrics.metric_name,
                    metrics.metric_value,
                    metrics.target_value,
                    metrics.measurement_date.isoformat(),
                    metrics.department,
                    metrics.notes,
                    metrics.created_at.isoformat()
                ))
                conn.commit()
                logger.info(f"Recorded culture metrics: {metrics.metrics_id}")
                return True
        except Exception as e:
            logger.error(f"Error recording culture metrics: {e}")
            return False
    
    def get_culture_metrics(self, dimension: Optional[CultureDimension] = None,
                          department: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[CultureMetrics]:
        """Get security culture metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM culture_metrics WHERE 1=1"
                params = []
                
                if dimension:
                    query += " AND dimension = ?"
                    params.append(dimension.value)
                
                if department:
                    query += " AND department = ?"
                    params.append(department)
                
                if start_date:
                    query += " AND measurement_date >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND measurement_date <= ?"
                    params.append(end_date.isoformat())
                
                query += " ORDER BY measurement_date DESC"
                
                cursor = conn.execute(query, params)
                
                metrics_list = []
                for row in cursor.fetchall():
                    metrics = CultureMetrics(
                        metrics_id=row[0],
                        dimension=CultureDimension(row[1]),
                        metric_name=row[2],
                        metric_value=row[3],
                        target_value=row[4],
                        measurement_date=datetime.fromisoformat(row[5]),
                        department=row[6],
                        notes=row[7],
                        created_at=datetime.fromisoformat(row[8])
                    )
                    metrics_list.append(metrics)
                
                return metrics_list
        except Exception as e:
            logger.error(f"Error getting culture metrics: {e}")
            return []
    
    def generate_culture_report(self, department: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive security culture report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get assessment statistics
                query = "SELECT COUNT(*) as total, assessment_type FROM security_culture_assessments WHERE is_active = 1"
                cursor = conn.execute(query)
                assessment_stats = cursor.fetchall()
                
                # Get response statistics
                resp_query = "SELECT COUNT(*) as total, department FROM assessment_responses"
                resp_params = []
                
                if start_date:
                    resp_query += " WHERE completion_date >= ?"
                    resp_params.append(start_date.isoformat())
                
                if end_date:
                    resp_query += " AND completion_date <= ?"
                    resp_params.append(end_date.isoformat())
                
                resp_query += " GROUP BY department"
                
                cursor = conn.execute(resp_query, resp_params)
                response_stats = cursor.fetchall()
                
                # Get initiative statistics
                init_query = "SELECT COUNT(*) as total, target_dimensions FROM security_culture_initiatives WHERE is_active = 1"
                cursor = conn.execute(init_query)
                initiative_stats = cursor.fetchall()
                
                # Get metrics statistics
                metrics_query = "SELECT AVG(metric_value) as avg_value, dimension FROM culture_metrics"
                metrics_params = []
                
                if department:
                    metrics_query += " WHERE department = ?"
                    metrics_params.append(department)
                
                if start_date:
                    metrics_query += " AND measurement_date >= ?"
                    metrics_params.append(start_date.isoformat())
                
                if end_date:
                    metrics_query += " AND measurement_date <= ?"
                    metrics_params.append(end_date.isoformat())
                
                metrics_query += " GROUP BY dimension"
                
                cursor = conn.execute(metrics_query, metrics_params)
                metrics_stats = cursor.fetchall()
                
                return {
                    'report_generated_at': datetime.utcnow().isoformat(),
                    'department': department,
                    'date_range': {
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None
                    },
                    'assessment_statistics': {
                        'total_assessments': len(assessment_stats),
                        'by_type': {row[1]: row[0] for row in assessment_stats}
                    },
                    'response_statistics': {
                        'total_responses': len(response_stats),
                        'by_department': {row[1]: row[0] for row in response_stats}
                    },
                    'initiative_statistics': {
                        'total_initiatives': len(initiative_stats),
                        'by_dimension': {row[1]: row[0] for row in initiative_stats}
                    },
                    'metrics_statistics': {
                        'average_scores': {row[1]: row[0] for row in metrics_stats}
                    }
                }
        except Exception as e:
            logger.error(f"Error generating culture report: {e}")
            return {}
    
    # Question generators
    def _get_culture_survey_questions(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": 1,
                "dimension": "awareness",
                "question": "How familiar are you with the organization's security policies?",
                "type": "scale",
                "options": ["Not familiar", "Somewhat familiar", "Familiar", "Very familiar", "Expert"],
                "weight": 1.0
            },
            {
                "id": 2,
                "dimension": "attitude",
                "question": "How important do you think security is to the organization's success?",
                "type": "scale",
                "options": ["Not important", "Somewhat important", "Important", "Very important", "Critical"],
                "weight": 1.0
            },
            {
                "id": 3,
                "dimension": "behavior",
                "question": "How often do you follow security best practices in your daily work?",
                "type": "scale",
                "options": ["Never", "Rarely", "Sometimes", "Often", "Always"],
                "weight": 1.0
            },
            {
                "id": 4,
                "dimension": "compliance",
                "question": "How confident are you in your ability to comply with security requirements?",
                "type": "scale",
                "options": ["Not confident", "Somewhat confident", "Confident", "Very confident", "Expert"],
                "weight": 1.0
            }
        ]
    
    def _get_leadership_assessment_questions(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": 1,
                "dimension": "leadership",
                "question": "How do you demonstrate security leadership in your role?",
                "type": "open_ended",
                "weight": 1.0
            },
            {
                "id": 2,
                "dimension": "communication",
                "question": "How do you communicate security priorities to your team?",
                "type": "open_ended",
                "weight": 1.0
            },
            {
                "id": 3,
                "dimension": "attitude",
                "question": "What is your approach to balancing security with business needs?",
                "type": "open_ended",
                "weight": 1.0
            }
        ]
    
    # Activity generators
    def _get_security_champions_activities(self) -> List[Dict[str, Any]]:
        return [
            {
                "activity": "Champion Selection",
                "description": "Identify and select security champions from each department",
                "duration": "2 weeks",
                "resources": ["HR team", "Department managers"]
            },
            {
                "activity": "Champion Training",
                "description": "Provide specialized training for security champions",
                "duration": "1 week",
                "resources": ["Security team", "Training materials"]
            },
            {
                "activity": "Department Engagement",
                "description": "Champions conduct security awareness sessions in their departments",
                "duration": "Ongoing",
                "resources": ["Champions", "Presentation materials"]
            },
            {
                "activity": "Feedback and Improvement",
                "description": "Regular feedback sessions and program improvements",
                "duration": "Monthly",
                "resources": ["Champions", "Security team"]
            }
        ]
    
    def _get_recognition_program_activities(self) -> List[Dict[str, Any]]:
        return [
            {
                "activity": "Program Design",
                "description": "Design recognition program structure and criteria",
                "duration": "2 weeks",
                "resources": ["HR team", "Security team"]
            },
            {
                "activity": "Program Launch",
                "description": "Launch recognition program with communication campaign",
                "duration": "1 week",
                "resources": ["Communications team", "Marketing materials"]
            },
            {
                "activity": "Nomination and Selection",
                "description": "Process nominations and select winners",
                "duration": "Monthly",
                "resources": ["Selection committee", "Nomination system"]
            },
            {
                "activity": "Recognition Events",
                "description": "Host recognition events and award ceremonies",
                "duration": "Quarterly",
                "resources": ["Event planning team", "Awards and prizes"]
            }
        ]

def create_security_culture_development_system(base_url: str = "http://localhost:5000") -> SecurityCultureDevelopmentSystem:
    """Create and configure security culture development system"""
    try:
        system = SecurityCultureDevelopmentSystem()
        logger.info("Security culture development system created successfully")
        return system
    except Exception as e:
        logger.error(f"Error creating security culture development system: {e}")
        raise 