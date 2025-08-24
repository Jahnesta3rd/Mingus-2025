"""
Incident Response Training Module
Comprehensive incident response training and simulation for MINGUS
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

class IncidentType(Enum):
    """Types of security incidents"""
    MALWARE_INFECTION = "malware_infection"
    PHISHING_ATTACK = "phishing_attack"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DOS_ATTACK = "dos_attack"
    INSIDER_THREAT = "insider_threat"
    PHYSICAL_SECURITY = "physical_security"
    SOCIAL_ENGINEERING = "social_engineering"

class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TrainingScenarioType(Enum):
    """Types of training scenarios"""
    TABLETOP_EXERCISE = "tabletop_exercise"
    SIMULATION = "simulation"
    RED_TEAM_EXERCISE = "red_team_exercise"
    INCIDENT_WALKTHROUGH = "incident_walkthrough"

@dataclass_json
@dataclass
class IncidentResponseScenario:
    """Incident response training scenario"""
    scenario_id: str
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    scenario_type: TrainingScenarioType
    scenario_content: str
    objectives: List[str]
    participants: List[str]
    duration_minutes: int
    difficulty_level: str
    prerequisites: List[str]
    materials_needed: List[str]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

@dataclass_json
@dataclass
class ScenarioExecution:
    """Scenario execution record"""
    execution_id: str
    scenario_id: str
    facilitator: str
    participants: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str  # planned, in_progress, completed, cancelled
    notes: str = ""
    lessons_learned: List[str] = field(default_factory=list)
    participant_feedback: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass_json
@dataclass
class IncidentResponseProcedure:
    """Incident response procedure"""
    procedure_id: str
    incident_type: IncidentType
    title: str
    description: str
    steps: List[Dict[str, Any]]
    escalation_path: List[str]
    contact_list: Dict[str, str]
    tools_needed: List[str]
    documentation_requirements: List[str]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

class IncidentResponseTrainingSystem:
    """
    Comprehensive incident response training system
    """
    
    def __init__(self, db_path: str = "/var/lib/mingus/incident_response_training.db"):
        self.db_path = db_path
        self._init_database()
        self._load_default_scenarios()
        self._load_default_procedures()
        
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incident_response_scenarios (
                        scenario_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        incident_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        scenario_type TEXT NOT NULL,
                        scenario_content TEXT NOT NULL,
                        objectives TEXT,
                        participants TEXT,
                        duration_minutes INTEGER NOT NULL,
                        difficulty_level TEXT NOT NULL,
                        prerequisites TEXT,
                        materials_needed TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scenario_executions (
                        execution_id TEXT PRIMARY KEY,
                        scenario_id TEXT NOT NULL,
                        facilitator TEXT NOT NULL,
                        participants TEXT,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        status TEXT NOT NULL,
                        notes TEXT,
                        lessons_learned TEXT,
                        participant_feedback TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incident_response_procedures (
                        procedure_id TEXT PRIMARY KEY,
                        incident_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        steps TEXT,
                        escalation_path TEXT,
                        contact_list TEXT,
                        tools_needed TEXT,
                        documentation_requirements TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_scenario_type ON incident_response_scenarios(incident_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_scenario_severity ON incident_response_scenarios(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_execution_scenario ON scenario_executions(scenario_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_procedure_type ON incident_response_procedures(incident_type)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _load_default_scenarios(self):
        """Load default incident response scenarios"""
        default_scenarios = [
            IncidentResponseScenario(
                scenario_id="SCEN-001",
                title="Phishing Attack Response",
                description="Respond to a sophisticated phishing attack targeting employees",
                incident_type=IncidentType.PHISHING_ATTACK,
                severity=IncidentSeverity.HIGH,
                scenario_type=TrainingScenarioType.TABLETOP_EXERCISE,
                scenario_content=self._get_phishing_scenario_content(),
                objectives=[
                    "Identify phishing indicators",
                    "Execute incident response procedures",
                    "Communicate with stakeholders",
                    "Document incident details"
                ],
                participants=["incident_response_team", "it_support", "communications"],
                duration_minutes=90,
                difficulty_level="intermediate",
                prerequisites=["basic_incident_response_training"],
                materials_needed=["incident_response_playbook", "communication_templates"],
                created_by="security_team"
            ),
            IncidentResponseScenario(
                scenario_id="SCEN-002",
                title="Malware Outbreak Response",
                description="Respond to a widespread malware infection",
                incident_type=IncidentType.MALWARE_INFECTION,
                severity=IncidentSeverity.CRITICAL,
                scenario_type=TrainingScenarioType.SIMULATION,
                scenario_content=self._get_malware_scenario_content(),
                objectives=[
                    "Contain malware spread",
                    "Isolate affected systems",
                    "Coordinate with IT teams",
                    "Implement recovery procedures"
                ],
                participants=["incident_response_team", "it_operations", "security_team"],
                duration_minutes=120,
                difficulty_level="advanced",
                prerequisites=["malware_analysis_training"],
                materials_needed=["malware_analysis_tools", "system_restoration_procedures"],
                created_by="security_team"
            ),
            IncidentResponseScenario(
                scenario_id="SCEN-003",
                title="Data Breach Response",
                description="Respond to a suspected data breach",
                incident_type=IncidentType.DATA_BREACH,
                severity=IncidentSeverity.CRITICAL,
                scenario_type=TrainingScenarioType.TABLETOP_EXERCISE,
                scenario_content=self._get_data_breach_scenario_content(),
                objectives=[
                    "Assess breach scope",
                    "Notify appropriate authorities",
                    "Communicate with affected parties",
                    "Implement containment measures"
                ],
                participants=["incident_response_team", "legal_team", "privacy_officer"],
                duration_minutes=150,
                difficulty_level="advanced",
                prerequisites=["data_protection_training", "legal_compliance_training"],
                materials_needed=["breach_notification_templates", "legal_guidance"],
                created_by="security_team"
            )
        ]
        
        for scenario in default_scenarios:
            self.create_scenario(scenario)
    
    def _load_default_procedures(self):
        """Load default incident response procedures"""
        default_procedures = [
            IncidentResponseProcedure(
                procedure_id="PROC-001",
                incident_type=IncidentType.PHISHING_ATTACK,
                title="Phishing Incident Response Procedure",
                description="Standard procedure for responding to phishing attacks",
                steps=self._get_phishing_response_steps(),
                escalation_path=["security_team", "it_support", "management"],
                contact_list={
                    "security_team": "security@company.com",
                    "it_support": "support@company.com",
                    "management": "management@company.com"
                },
                tools_needed=["email_analysis_tools", "phishing_reporting_system"],
                documentation_requirements=[
                    "Incident report",
                    "Email analysis report",
                    "User impact assessment",
                    "Lessons learned document"
                ],
                created_by="security_team"
            ),
            IncidentResponseProcedure(
                procedure_id="PROC-002",
                incident_type=IncidentType.MALWARE_INFECTION,
                title="Malware Incident Response Procedure",
                description="Standard procedure for responding to malware infections",
                steps=self._get_malware_response_steps(),
                escalation_path=["security_team", "it_operations", "management"],
                contact_list={
                    "security_team": "security@company.com",
                    "it_operations": "ops@company.com",
                    "management": "management@company.com"
                },
                tools_needed=["malware_analysis_tools", "system_restoration_tools"],
                documentation_requirements=[
                    "Incident report",
                    "Malware analysis report",
                    "System restoration report",
                    "Lessons learned document"
                ],
                created_by="security_team"
            )
        ]
        
        for procedure in default_procedures:
            self.create_procedure(procedure)
    
    def create_scenario(self, scenario: IncidentResponseScenario) -> bool:
        """Create a new incident response scenario"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO incident_response_scenarios 
                    (scenario_id, title, description, incident_type, severity, scenario_type,
                     scenario_content, objectives, participants, duration_minutes, difficulty_level,
                     prerequisites, materials_needed, created_by, created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    scenario.scenario_id,
                    scenario.title,
                    scenario.description,
                    scenario.incident_type.value,
                    scenario.severity.value,
                    scenario.scenario_type.value,
                    scenario.scenario_content,
                    json.dumps(scenario.objectives),
                    json.dumps(scenario.participants),
                    scenario.duration_minutes,
                    scenario.difficulty_level,
                    json.dumps(scenario.prerequisites),
                    json.dumps(scenario.materials_needed),
                    scenario.created_by,
                    scenario.created_at.isoformat(),
                    scenario.updated_at.isoformat(),
                    scenario.is_active
                ))
                conn.commit()
                logger.info(f"Created incident response scenario: {scenario.scenario_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating scenario: {e}")
            return False
    
    def get_scenarios(self, incident_type: Optional[IncidentType] = None,
                     severity: Optional[IncidentSeverity] = None,
                     scenario_type: Optional[TrainingScenarioType] = None,
                     active_only: bool = True) -> List[IncidentResponseScenario]:
        """Get incident response scenarios with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM incident_response_scenarios WHERE is_active = ?"
                params = [active_only]
                
                if incident_type:
                    query += " AND incident_type = ?"
                    params.append(incident_type.value)
                
                if severity:
                    query += " AND severity = ?"
                    params.append(severity.value)
                
                if scenario_type:
                    query += " AND scenario_type = ?"
                    params.append(scenario_type.value)
                
                query += " ORDER BY severity DESC, title"
                
                cursor = conn.execute(query, params)
                
                scenarios = []
                for row in cursor.fetchall():
                    scenario = IncidentResponseScenario(
                        scenario_id=row[0],
                        title=row[1],
                        description=row[2],
                        incident_type=IncidentType(row[3]),
                        severity=IncidentSeverity(row[4]),
                        scenario_type=TrainingScenarioType(row[5]),
                        scenario_content=row[6],
                        objectives=json.loads(row[7]),
                        participants=json.loads(row[8]),
                        duration_minutes=row[9],
                        difficulty_level=row[10],
                        prerequisites=json.loads(row[11]),
                        materials_needed=json.loads(row[12]),
                        created_by=row[13],
                        created_at=datetime.fromisoformat(row[14]),
                        updated_at=datetime.fromisoformat(row[15]),
                        is_active=bool(row[16])
                    )
                    scenarios.append(scenario)
                
                return scenarios
        except Exception as e:
            logger.error(f"Error getting scenarios: {e}")
            return []
    
    def create_procedure(self, procedure: IncidentResponseProcedure) -> bool:
        """Create a new incident response procedure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO incident_response_procedures 
                    (procedure_id, incident_type, title, description, steps, escalation_path,
                     contact_list, tools_needed, documentation_requirements, created_by,
                     created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    procedure.procedure_id,
                    procedure.incident_type.value,
                    procedure.title,
                    procedure.description,
                    json.dumps(procedure.steps),
                    json.dumps(procedure.escalation_path),
                    json.dumps(procedure.contact_list),
                    json.dumps(procedure.tools_needed),
                    json.dumps(procedure.documentation_requirements),
                    procedure.created_by,
                    procedure.created_at.isoformat(),
                    procedure.updated_at.isoformat(),
                    procedure.is_active
                ))
                conn.commit()
                logger.info(f"Created incident response procedure: {procedure.procedure_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating procedure: {e}")
            return False
    
    def get_procedures(self, incident_type: Optional[IncidentType] = None,
                      active_only: bool = True) -> List[IncidentResponseProcedure]:
        """Get incident response procedures"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM incident_response_procedures WHERE is_active = ?"
                params = [active_only]
                
                if incident_type:
                    query += " AND incident_type = ?"
                    params.append(incident_type.value)
                
                query += " ORDER BY incident_type, title"
                
                cursor = conn.execute(query, params)
                
                procedures = []
                for row in cursor.fetchall():
                    procedure = IncidentResponseProcedure(
                        procedure_id=row[0],
                        incident_type=IncidentType(row[1]),
                        title=row[2],
                        description=row[3],
                        steps=json.loads(row[4]),
                        escalation_path=json.loads(row[5]),
                        contact_list=json.loads(row[6]),
                        tools_needed=json.loads(row[7]),
                        documentation_requirements=json.loads(row[8]),
                        created_by=row[9],
                        created_at=datetime.fromisoformat(row[10]),
                        updated_at=datetime.fromisoformat(row[11]),
                        is_active=bool(row[12])
                    )
                    procedures.append(procedure)
                
                return procedures
        except Exception as e:
            logger.error(f"Error getting procedures: {e}")
            return []
    
    def execute_scenario(self, execution: ScenarioExecution) -> bool:
        """Execute a training scenario"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO scenario_executions 
                    (execution_id, scenario_id, facilitator, participants, start_time,
                     end_time, status, notes, lessons_learned, participant_feedback, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    execution.scenario_id,
                    execution.facilitator,
                    json.dumps(execution.participants),
                    execution.start_time.isoformat(),
                    execution.end_time.isoformat() if execution.end_time else None,
                    execution.status,
                    execution.notes,
                    json.dumps(execution.lessons_learned),
                    json.dumps(execution.participant_feedback),
                    execution.created_at.isoformat()
                ))
                conn.commit()
                logger.info(f"Executed scenario: {execution.execution_id}")
                return True
        except Exception as e:
            logger.error(f"Error executing scenario: {e}")
            return False
    
    def get_execution_history(self, scenario_id: Optional[str] = None,
                            facilitator: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[ScenarioExecution]:
        """Get scenario execution history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM scenario_executions WHERE 1=1"
                params = []
                
                if scenario_id:
                    query += " AND scenario_id = ?"
                    params.append(scenario_id)
                
                if facilitator:
                    query += " AND facilitator = ?"
                    params.append(facilitator)
                
                if start_date:
                    query += " AND start_time >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND start_time <= ?"
                    params.append(end_date.isoformat())
                
                query += " ORDER BY start_time DESC"
                
                cursor = conn.execute(query, params)
                
                executions = []
                for row in cursor.fetchall():
                    execution = ScenarioExecution(
                        execution_id=row[0],
                        scenario_id=row[1],
                        facilitator=row[2],
                        participants=json.loads(row[3]),
                        start_time=datetime.fromisoformat(row[4]),
                        end_time=datetime.fromisoformat(row[5]) if row[5] else None,
                        status=row[6],
                        notes=row[7],
                        lessons_learned=json.loads(row[8]) if row[8] else [],
                        participant_feedback=json.loads(row[9]) if row[9] else {},
                        created_at=datetime.fromisoformat(row[10])
                    )
                    executions.append(execution)
                
                return executions
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return []
    
    # Scenario content generators
    def _get_phishing_scenario_content(self) -> str:
        return """
# Phishing Attack Response Scenario

## Scenario Overview
A sophisticated phishing campaign has been detected targeting company employees. The campaign uses convincing emails that appear to come from legitimate sources and contain malicious links or attachments.

## Initial Situation
- Multiple employees report suspicious emails
- Some employees may have clicked on links or opened attachments
- IT security team detects unusual network activity
- Management is concerned about potential data compromise

## Key Events
1. **Detection**: Security team identifies phishing campaign
2. **Assessment**: Determine scope and impact
3. **Containment**: Isolate affected systems
4. **Communication**: Notify stakeholders
5. **Recovery**: Restore normal operations

## Learning Objectives
- Practice incident response procedures
- Improve communication during incidents
- Test coordination between teams
- Validate response effectiveness

## Discussion Points
- How would you assess the scope of the attack?
- What communication channels would you use?
- How would you prevent similar attacks?
- What lessons can be learned?
        """
    
    def _get_malware_scenario_content(self) -> str:
        return """
# Malware Outbreak Response Scenario

## Scenario Overview
A malware outbreak has been detected across multiple systems in the organization. The malware appears to be spreading rapidly and may be stealing sensitive data.

## Initial Situation
- Multiple systems showing signs of infection
- Network traffic analysis indicates data exfiltration
- Some critical systems are affected
- Business operations are impacted

## Key Events
1. **Detection**: Identify malware outbreak
2. **Containment**: Isolate infected systems
3. **Analysis**: Determine malware type and impact
4. **Eradication**: Remove malware from systems
5. **Recovery**: Restore affected systems

## Learning Objectives
- Practice malware response procedures
- Test system isolation techniques
- Improve incident coordination
- Validate recovery procedures

## Discussion Points
- How would you contain the outbreak?
- What systems are most critical?
- How would you communicate with stakeholders?
- What recovery steps would you take?
        """
    
    def _get_data_breach_scenario_content(self) -> str:
        return """
# Data Breach Response Scenario

## Scenario Overview
A suspected data breach has been detected involving customer personal information. The breach may have exposed sensitive data to unauthorized parties.

## Initial Situation
- Unusual access patterns detected
- Customer data may have been compromised
- Legal and compliance teams need to be involved
- Potential regulatory reporting requirements

## Key Events
1. **Detection**: Identify potential data breach
2. **Assessment**: Determine scope and data types
3. **Notification**: Notify appropriate authorities
4. **Communication**: Inform affected parties
5. **Remediation**: Implement security improvements

## Learning Objectives
- Practice breach response procedures
- Test legal and compliance coordination
- Improve stakeholder communication
- Validate notification procedures

## Discussion Points
- What data types are involved?
- When should authorities be notified?
- How would you communicate with customers?
- What security improvements are needed?
        """
    
    # Response procedure generators
    def _get_phishing_response_steps(self) -> List[Dict[str, Any]]:
        return [
            {
                "step": 1,
                "action": "Immediate Response",
                "description": "Isolate affected systems and accounts",
                "duration": "15 minutes",
                "responsible": "IT Support"
            },
            {
                "step": 2,
                "action": "Assessment",
                "description": "Analyze phishing emails and determine scope",
                "duration": "30 minutes",
                "responsible": "Security Team"
            },
            {
                "step": 3,
                "action": "Communication",
                "description": "Notify affected users and management",
                "duration": "45 minutes",
                "responsible": "Communications Team"
            },
            {
                "step": 4,
                "action": "Containment",
                "description": "Implement additional security measures",
                "duration": "60 minutes",
                "responsible": "IT Operations"
            },
            {
                "step": 5,
                "action": "Documentation",
                "description": "Document incident details and lessons learned",
                "duration": "30 minutes",
                "responsible": "Security Team"
            }
        ]
    
    def _get_malware_response_steps(self) -> List[Dict[str, Any]]:
        return [
            {
                "step": 1,
                "action": "Detection and Isolation",
                "description": "Identify and isolate infected systems",
                "duration": "30 minutes",
                "responsible": "Security Team"
            },
            {
                "step": 2,
                "action": "Analysis",
                "description": "Analyze malware type and behavior",
                "duration": "60 minutes",
                "responsible": "Security Team"
            },
            {
                "step": 3,
                "action": "Containment",
                "description": "Prevent further spread of malware",
                "duration": "45 minutes",
                "responsible": "IT Operations"
            },
            {
                "step": 4,
                "action": "Eradication",
                "description": "Remove malware from affected systems",
                "duration": "120 minutes",
                "responsible": "IT Operations"
            },
            {
                "step": 5,
                "action": "Recovery",
                "description": "Restore systems and verify functionality",
                "duration": "90 minutes",
                "responsible": "IT Operations"
            }
        ]

def create_incident_response_training_system(base_url: str = "http://localhost:5000") -> IncidentResponseTrainingSystem:
    """Create and configure incident response training system"""
    try:
        system = IncidentResponseTrainingSystem()
        logger.info("Incident response training system created successfully")
        return system
    except Exception as e:
        logger.error(f"Error creating incident response training system: {e}")
        raise 