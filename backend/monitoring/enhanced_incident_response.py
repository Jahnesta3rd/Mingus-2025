"""
Enhanced Security Incident Response Workflow System
Advanced incident management with automated playbooks and team collaboration
"""

import os
import json
import time
import threading
import queue
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from loguru import logger
import sqlite3
from enum import Enum
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    """Incident status levels"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"

class IncidentType(Enum):
    """Incident types"""
    SECURITY_BREACH = "security_breach"
    DATA_BREACH = "data_breach"
    MALWARE_INFECTION = "malware_infection"
    DDOS_ATTACK = "ddos_attack"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PHISHING_ATTACK = "phishing_attack"
    INSIDER_THREAT = "insider_threat"
    SYSTEM_COMPROMISE = "system_compromise"
    NETWORK_INTRUSION = "network_intrusion"
    APPLICATION_ATTACK = "application_attack"

class PlaybookAction(Enum):
    """Playbook action types"""
    NOTIFY_TEAM = "notify_team"
    ISOLATE_SYSTEM = "isolate_system"
    BLOCK_IP = "block_ip"
    RESET_CREDENTIALS = "reset_credentials"
    ENABLE_MFA = "enable_mfa"
    SCAN_SYSTEM = "scan_system"
    BACKUP_DATA = "backup_data"
    CONTACT_LAW_ENFORCEMENT = "contact_law_enforcement"
    UPDATE_FIREWALL = "update_firewall"
    REVIEW_LOGS = "review_logs"

@dataclass
class IncidentResponseConfig:
    """Incident response configuration"""
    enabled: bool = True
    auto_escalation: bool = True
    escalation_threshold: int = 3
    response_team: List[str] = field(default_factory=list)
    escalation_team: List[str] = field(default_factory=list)
    playbooks: Dict[str, str] = field(default_factory=dict)
    notification_channels: List[str] = field(default_factory=lambda: ["email", "slack"])
    
    # Email configuration
    email_enabled: bool = True
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = "incidents@mingus.com"
    
    # Slack configuration
    slack_enabled: bool = True
    slack_webhook_url: str = ""
    slack_channel: str = "#incidents"
    
    # Auto-response settings
    auto_containment: bool = True
    auto_notification: bool = True
    auto_documentation: bool = True
    
    # Escalation settings
    escalation_timeout_minutes: int = 30
    critical_escalation_timeout_minutes: int = 15

@dataclass
class Incident:
    """Incident structure"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    incident_type: IncidentType
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    playbook: Optional[str] = None
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_alert: Optional[Dict[str, Any]] = None

@dataclass
class Playbook:
    """Playbook structure"""
    name: str
    description: str
    severity: IncidentSeverity
    incident_type: IncidentType
    actions: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    auto_execute: bool = True

class EnhancedSecurityIncidentManager:
    """Enhanced security incident response workflow management"""
    
    def __init__(self, config: IncidentResponseConfig):
        self.config = config
        self.db_path = "/var/lib/mingus/incidents.db"
        self.incidents = {}
        self.playbooks = {}
        self.escalation_queue = queue.Queue()
        self.response_workers = []
        self.escalation_timers = {}
        
        self._init_database()
        self._load_default_playbooks()
        self.start_response_workers()
    
    def _init_database(self):
        """Initialize incident response database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Incidents table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_incidents (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        incident_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        assigned_to TEXT,
                        playbook TEXT,
                        timeline TEXT,
                        resolution TEXT,
                        metadata TEXT,
                        source_alert TEXT
                    )
                """)
                
                # Incident events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incident_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        incident_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        user_id TEXT,
                        metadata TEXT,
                        FOREIGN KEY (incident_id) REFERENCES security_incidents (id)
                    )
                """)
                
                # Playbooks table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incident_playbooks (
                        name TEXT PRIMARY KEY,
                        description TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        incident_type TEXT NOT NULL,
                        actions TEXT NOT NULL,
                        conditions TEXT,
                        auto_execute INTEGER DEFAULT 1
                    )
                """)
                
                # Team assignments table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incident_assignments (
                        incident_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        assigned_at TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        PRIMARY KEY (incident_id, user_id)
                    )
                """)
                
                # Escalation history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS escalation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        incident_id TEXT NOT NULL,
                        escalated_at TEXT NOT NULL,
                        escalated_by TEXT,
                        reason TEXT NOT NULL,
                        previous_status TEXT NOT NULL,
                        new_status TEXT NOT NULL
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON security_incidents(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_created ON security_incidents(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_incident ON incident_events(incident_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON incident_events(timestamp)")
        
        except Exception as e:
            logger.error(f"Error initializing incident database: {e}")
    
    def _load_default_playbooks(self):
        """Load default incident response playbooks"""
        default_playbooks = {
            "critical_security_breach": Playbook(
                name="critical_security_breach",
                description="Response playbook for critical security breaches",
                severity=IncidentSeverity.CRITICAL,
                incident_type=IncidentType.SECURITY_BREACH,
                auto_execute=True,
                actions=[
                    {
                        "action": PlaybookAction.NOTIFY_TEAM.value,
                        "description": "Notify security team immediately",
                        "parameters": {"team": "security", "priority": "critical"}
                    },
                    {
                        "action": PlaybookAction.ISOLATE_SYSTEM.value,
                        "description": "Isolate affected systems",
                        "parameters": {"systems": "affected_systems"}
                    },
                    {
                        "action": PlaybookAction.BLOCK_IP.value,
                        "description": "Block suspicious IP addresses",
                        "parameters": {"ips": "suspicious_ips"}
                    },
                    {
                        "action": PlaybookAction.RESET_CREDENTIALS.value,
                        "description": "Reset compromised credentials",
                        "parameters": {"users": "affected_users"}
                    },
                    {
                        "action": PlaybookAction.CONTACT_LAW_ENFORCEMENT.value,
                        "description": "Contact law enforcement if required",
                        "parameters": {"agency": "cyber_crime_unit"}
                    }
                ]
            ),
            "data_breach_response": Playbook(
                name="data_breach_response",
                description="Response playbook for data breaches",
                severity=IncidentSeverity.HIGH,
                incident_type=IncidentType.DATA_BREACH,
                auto_execute=True,
                actions=[
                    {
                        "action": PlaybookAction.NOTIFY_TEAM.value,
                        "description": "Notify data protection team",
                        "parameters": {"team": "data_protection", "priority": "high"}
                    },
                    {
                        "action": PlaybookAction.BACKUP_DATA.value,
                        "description": "Create forensic backup",
                        "parameters": {"scope": "affected_data"}
                    },
                    {
                        "action": PlaybookAction.REVIEW_LOGS.value,
                        "description": "Review access logs",
                        "parameters": {"timeframe": "last_30_days"}
                    },
                    {
                        "action": PlaybookAction.RESET_CREDENTIALS.value,
                        "description": "Reset affected user credentials",
                        "parameters": {"users": "affected_users"}
                    }
                ]
            ),
            "malware_infection": Playbook(
                name="malware_infection",
                description="Response playbook for malware infections",
                severity=IncidentSeverity.HIGH,
                incident_type=IncidentType.MALWARE_INFECTION,
                auto_execute=True,
                actions=[
                    {
                        "action": PlaybookAction.ISOLATE_SYSTEM.value,
                        "description": "Isolate infected systems",
                        "parameters": {"systems": "infected_systems"}
                    },
                    {
                        "action": PlaybookAction.SCAN_SYSTEM.value,
                        "description": "Perform malware scan",
                        "parameters": {"scan_type": "full_system"}
                    },
                    {
                        "action": PlaybookAction.UPDATE_FIREWALL.value,
                        "description": "Update firewall rules",
                        "parameters": {"rules": "malware_prevention"}
                    },
                    {
                        "action": PlaybookAction.NOTIFY_TEAM.value,
                        "description": "Notify IT security team",
                        "parameters": {"team": "it_security", "priority": "high"}
                    }
                ]
            ),
            "ddos_attack": Playbook(
                name="ddos_attack",
                description="Response playbook for DDoS attacks",
                severity=IncidentSeverity.HIGH,
                incident_type=IncidentType.DDOS_ATTACK,
                auto_execute=True,
                actions=[
                    {
                        "action": PlaybookAction.NOTIFY_TEAM.value,
                        "description": "Notify network security team",
                        "parameters": {"team": "network_security", "priority": "high"}
                    },
                    {
                        "action": PlaybookAction.UPDATE_FIREWALL.value,
                        "description": "Enable DDoS protection",
                        "parameters": {"protection": "ddos_mitigation"}
                    },
                    {
                        "action": PlaybookAction.BLOCK_IP.value,
                        "description": "Block attack sources",
                        "parameters": {"ips": "attack_sources"}
                    }
                ]
            )
        }
        
        for playbook in default_playbooks.values():
            self.add_playbook(playbook)
    
    def add_playbook(self, playbook: Playbook):
        """Add incident response playbook"""
        self.playbooks[playbook.name] = playbook
        
        # Store in database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO incident_playbooks 
                    (name, description, severity, incident_type, actions, conditions, auto_execute)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    playbook.name,
                    playbook.description,
                    playbook.severity.value,
                    playbook.incident_type.value,
                    json.dumps(playbook.actions),
                    json.dumps(playbook.conditions),
                    1 if playbook.auto_execute else 0
                ))
        except Exception as e:
            logger.error(f"Error storing playbook: {e}")
    
    def start_response_workers(self):
        """Start incident response workers"""
        for i in range(3):  # 3 response worker threads
            worker = threading.Thread(target=self._response_worker, daemon=True, name=f"incident_worker_{i}")
            worker.start()
            self.response_workers.append(worker)
    
    def _response_worker(self):
        """Background worker for incident response"""
        while True:
            try:
                incident = self.escalation_queue.get(timeout=1)
                self._handle_incident_escalation(incident)
                self.escalation_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in incident response worker: {e}")
    
    def create_incident(self, title: str, description: str, severity: IncidentSeverity,
                       incident_type: IncidentType, source_alert: Dict[str, Any] = None) -> str:
        """Create a new security incident"""
        try:
            incident_id = str(uuid.uuid4())
            
            incident = Incident(
                id=incident_id,
                title=title,
                description=description,
                severity=severity,
                incident_type=incident_type,
                status=IncidentStatus.OPEN,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_alert=source_alert
            )
            
            # Determine appropriate playbook
            playbook = self._get_playbook(severity, incident_type)
            if playbook:
                incident.playbook = playbook.name
            
            # Store incident
            self._store_incident(incident)
            self.incidents[incident_id] = incident
            
            # Add initial event
            self.add_incident_event(incident_id, "incident_created", 
                                   f"Incident created with severity: {severity.value}")
            
            # Execute playbook if auto-execute is enabled
            if playbook and playbook.auto_execute:
                self._execute_playbook(incident, playbook)
            
            # Set escalation timer
            self._set_escalation_timer(incident)
            
            # Send notifications
            if self.config.auto_notification:
                self._send_incident_notifications(incident)
            
            logger.info(f"Incident created: {incident_id} - {title}")
            return incident_id
        
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            return None
    
    def _get_playbook(self, severity: IncidentSeverity, incident_type: IncidentType) -> Optional[Playbook]:
        """Get appropriate playbook for incident"""
        for playbook in self.playbooks.values():
            if (playbook.severity == severity and 
                playbook.incident_type == incident_type):
                return playbook
        
        # Fallback to severity-based playbook
        for playbook in self.playbooks.values():
            if playbook.severity == severity:
                return playbook
        
        return None
    
    def _execute_playbook(self, incident: Incident, playbook: Playbook):
        """Execute incident response playbook"""
        try:
            logger.info(f"Executing playbook: {playbook.name} for incident: {incident.id}")
            
            for action in playbook.actions:
                self._execute_playbook_action(incident, action)
            
            # Add playbook execution event
            self.add_incident_event(
                incident.id,
                "playbook_executed",
                f"Playbook '{playbook.name}' executed with {len(playbook.actions)} actions"
            )
        
        except Exception as e:
            logger.error(f"Error executing playbook: {e}")
    
    def _execute_playbook_action(self, incident: Incident, action: Dict[str, Any]):
        """Execute individual playbook action"""
        try:
            action_type = action["action"]
            description = action["description"]
            parameters = action.get("parameters", {})
            
            if action_type == PlaybookAction.NOTIFY_TEAM.value:
                self._notify_team(incident, parameters)
            elif action_type == PlaybookAction.ISOLATE_SYSTEM.value:
                self._isolate_system(incident, parameters)
            elif action_type == PlaybookAction.BLOCK_IP.value:
                self._block_ip(incident, parameters)
            elif action_type == PlaybookAction.RESET_CREDENTIALS.value:
                self._reset_credentials(incident, parameters)
            elif action_type == PlaybookAction.ENABLE_MFA.value:
                self._enable_mfa(incident, parameters)
            elif action_type == PlaybookAction.SCAN_SYSTEM.value:
                self._scan_system(incident, parameters)
            elif action_type == PlaybookAction.BACKUP_DATA.value:
                self._backup_data(incident, parameters)
            elif action_type == PlaybookAction.CONTACT_LAW_ENFORCEMENT.value:
                self._contact_law_enforcement(incident, parameters)
            elif action_type == PlaybookAction.UPDATE_FIREWALL.value:
                self._update_firewall(incident, parameters)
            elif action_type == PlaybookAction.REVIEW_LOGS.value:
                self._review_logs(incident, parameters)
            
            # Add action execution event
            self.add_incident_event(
                incident.id,
                "playbook_action_executed",
                f"Action executed: {description}",
                metadata={"action": action_type, "parameters": parameters}
            )
        
        except Exception as e:
            logger.error(f"Error executing playbook action: {e}")
            self.add_incident_event(
                incident.id,
                "playbook_action_failed",
                f"Action failed: {description}",
                metadata={"action": action_type, "error": str(e)}
            )
    
    def _notify_team(self, incident: Incident, parameters: Dict[str, Any]):
        """Notify team about incident"""
        team = parameters.get("team", "security")
        priority = parameters.get("priority", "medium")
        
        if self.config.email_enabled:
            self._send_email_notification(incident, team, priority)
        
        if self.config.slack_enabled:
            self._send_slack_notification(incident, team, priority)
    
    def _isolate_system(self, incident: Incident, parameters: Dict[str, Any]):
        """Isolate affected systems"""
        systems = parameters.get("systems", "affected_systems")
        # Implementation would integrate with system management tools
        logger.info(f"Isolating systems: {systems} for incident: {incident.id}")
    
    def _block_ip(self, incident: Incident, parameters: Dict[str, Any]):
        """Block suspicious IP addresses"""
        ips = parameters.get("ips", "suspicious_ips")
        # Implementation would integrate with firewall/network security tools
        logger.info(f"Blocking IPs: {ips} for incident: {incident.id}")
    
    def _reset_credentials(self, incident: Incident, parameters: Dict[str, Any]):
        """Reset compromised credentials"""
        users = parameters.get("users", "affected_users")
        # Implementation would integrate with identity management systems
        logger.info(f"Resetting credentials for users: {users} for incident: {incident.id}")
    
    def _enable_mfa(self, incident: Incident, parameters: Dict[str, Any]):
        """Enable multi-factor authentication"""
        users = parameters.get("users", "affected_users")
        # Implementation would integrate with MFA systems
        logger.info(f"Enabling MFA for users: {users} for incident: {incident.id}")
    
    def _scan_system(self, incident: Incident, parameters: Dict[str, Any]):
        """Perform system scan"""
        scan_type = parameters.get("scan_type", "full_system")
        # Implementation would integrate with security scanning tools
        logger.info(f"Performing {scan_type} scan for incident: {incident.id}")
    
    def _backup_data(self, incident: Incident, parameters: Dict[str, Any]):
        """Create forensic backup"""
        scope = parameters.get("scope", "affected_data")
        # Implementation would integrate with backup systems
        logger.info(f"Creating forensic backup for scope: {scope} for incident: {incident.id}")
    
    def _contact_law_enforcement(self, incident: Incident, parameters: Dict[str, Any]):
        """Contact law enforcement"""
        agency = parameters.get("agency", "cyber_crime_unit")
        # Implementation would integrate with law enforcement contact systems
        logger.info(f"Contacting law enforcement agency: {agency} for incident: {incident.id}")
    
    def _update_firewall(self, incident: Incident, parameters: Dict[str, Any]):
        """Update firewall rules"""
        rules = parameters.get("rules", "security_rules")
        # Implementation would integrate with firewall management systems
        logger.info(f"Updating firewall rules: {rules} for incident: {incident.id}")
    
    def _review_logs(self, incident: Incident, parameters: Dict[str, Any]):
        """Review system logs"""
        timeframe = parameters.get("timeframe", "last_30_days")
        # Implementation would integrate with log analysis systems
        logger.info(f"Reviewing logs for timeframe: {timeframe} for incident: {incident.id}")
    
    def _set_escalation_timer(self, incident: Incident):
        """Set escalation timer for incident"""
        if not self.config.auto_escalation:
            return
        
        # Determine escalation timeout based on severity
        if incident.severity == IncidentSeverity.CRITICAL:
            timeout_minutes = self.config.critical_escalation_timeout_minutes
        else:
            timeout_minutes = self.config.escalation_timeout_minutes
        
        # Set timer
        timer = threading.Timer(
            timeout_minutes * 60,
            self._escalate_incident,
            args=[incident.id]
        )
        timer.start()
        self.escalation_timers[incident.id] = timer
    
    def _escalate_incident(self, incident_id: str):
        """Escalate incident"""
        try:
            if incident_id not in self.incidents:
                return
            
            incident = self.incidents[incident_id]
            
            # Check if incident is still open
            if incident.status not in [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]:
                return
            
            # Escalate incident
            old_status = incident.status
            incident.status = IncidentStatus.ESCALATED
            incident.updated_at = datetime.utcnow()
            
            # Update database
            self._update_incident_status(incident_id, IncidentStatus.ESCALATED)
            
            # Add escalation event
            self.add_incident_event(
                incident_id,
                "incident_escalated",
                f"Incident escalated from {old_status.value} to {incident.status.value}",
                metadata={"reason": "timeout_escalation"}
            )
            
            # Send escalation notifications
            self._send_escalation_notifications(incident)
            
            # Add to escalation queue
            self.escalation_queue.put(incident)
            
            logger.warning(f"Incident escalated: {incident_id}")
        
        except Exception as e:
            logger.error(f"Error escalating incident: {e}")
    
    def _send_incident_notifications(self, incident: Incident):
        """Send incident notifications"""
        try:
            if self.config.email_enabled:
                self._send_email_notification(incident, "security", incident.severity.value)
            
            if self.config.slack_enabled:
                self._send_slack_notification(incident, "security", incident.severity.value)
        
        except Exception as e:
            logger.error(f"Error sending incident notifications: {e}")
    
    def _send_escalation_notifications(self, incident: Incident):
        """Send escalation notifications"""
        try:
            if self.config.email_enabled:
                self._send_email_notification(incident, "escalation", "critical")
            
            if self.config.slack_enabled:
                self._send_slack_notification(incident, "escalation", "critical")
        
        except Exception as e:
            logger.error(f"Error sending escalation notifications: {e}")
    
    def _send_email_notification(self, incident: Incident, team: str, priority: str):
        """Send email notification"""
        try:
            if not self.config.email_enabled:
                return
            
            subject = f"🚨 Security Incident: {incident.title}"
            
            body = f"""
Security Incident Alert

Incident ID: {incident.id}
Title: {incident.title}
Description: {incident.description}
Severity: {incident.severity.value.upper()}
Type: {incident.incident_type.value}
Status: {incident.status.value}
Created: {incident.created_at.isoformat()}

Please review this incident immediately.

Best regards,
Mingus Security Team
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.config.from_email
            msg['To'] = ', '.join(self.config.response_team)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
        
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def _send_slack_notification(self, incident: Incident, team: str, priority: str):
        """Send Slack notification"""
        try:
            if not self.config.slack_enabled:
                return
            
            # Determine color based on severity
            severity_colors = {
                "critical": "#d32f2f",
                "high": "#f57c00",
                "medium": "#fbc02d",
                "low": "#388e3c"
            }
            
            color = severity_colors.get(incident.severity.value, "#757575")
            
            payload = {
                "channel": self.config.slack_channel,
                "username": "Mingus Incident Response",
                "icon_emoji": ":warning:",
                "attachments": [{
                    "color": color,
                    "title": f"Security Incident: {incident.title}",
                    "text": incident.description,
                    "fields": [
                        {
                            "title": "Incident ID",
                            "value": incident.id,
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": incident.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Type",
                            "value": incident.incident_type.value,
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": incident.status.value,
                            "short": True
                        },
                        {
                            "title": "Created",
                            "value": incident.created_at.isoformat(),
                            "short": False
                        }
                    ],
                    "footer": "Mingus Security Incident Response"
                }]
            }
            
            response = requests.post(self.config.slack_webhook_url, json=payload)
            response.raise_for_status()
        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def update_incident_status(self, incident_id: str, status: IncidentStatus,
                              user_id: str = None, resolution: str = None):
        """Update incident status"""
        try:
            if incident_id not in self.incidents:
                return False
            
            old_status = self.incidents[incident_id].status
            self.incidents[incident_id].status = status
            self.incidents[incident_id].updated_at = datetime.utcnow()
            
            if resolution:
                self.incidents[incident_id].resolution = resolution
            
            # Update database
            self._update_incident_status(incident_id, status, resolution)
            
            # Add status change event
            self.add_incident_event(
                incident_id,
                "status_changed",
                f"Status changed from {old_status.value} to {status.value}",
                user_id
            )
            
            # Cancel escalation timer if incident is resolved
            if status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                self._cancel_escalation_timer(incident_id)
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating incident status: {e}")
            return False
    
    def _cancel_escalation_timer(self, incident_id: str):
        """Cancel escalation timer for incident"""
        if incident_id in self.escalation_timers:
            self.escalation_timers[incident_id].cancel()
            del self.escalation_timers[incident_id]
    
    def add_incident_event(self, incident_id: str, event_type: str, description: str,
                          user_id: str = None, metadata: Dict[str, Any] = None):
        """Add event to incident timeline"""
        try:
            event = {
                "event_type": event_type,
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            # Add to incident timeline
            if incident_id in self.incidents:
                self.incidents[incident_id].timeline.append(event)
            
            # Store in database
            self._store_incident_event(incident_id, event)
        
        except Exception as e:
            logger.error(f"Error adding incident event: {e}")
    
    def assign_incident(self, incident_id: str, user_id: str, role: str = "responder"):
        """Assign incident to team member"""
        try:
            if incident_id not in self.incidents:
                return False
            
            self.incidents[incident_id].assigned_to = user_id
            
            # Update database
            self._update_incident_assignment(incident_id, user_id, role)
            
            # Add assignment event
            self.add_incident_event(
                incident_id,
                "incident_assigned",
                f"Incident assigned to {user_id} as {role}",
                user_id
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error assigning incident: {e}")
            return False
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID"""
        return self.incidents.get(incident_id)
    
    def get_active_incidents(self) -> List[Incident]:
        """Get all active incidents"""
        return [
            incident for incident in self.incidents.values()
            if incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]
        ]
    
    def get_incident_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get incident statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Total incidents
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_incidents 
                    WHERE created_at >= ?
                """, (cutoff_date.isoformat(),))
                total_incidents = cursor.fetchone()[0]
                
                # Incidents by severity
                cursor = conn.execute("""
                    SELECT severity, COUNT(*) FROM security_incidents 
                    WHERE created_at >= ?
                    GROUP BY severity
                """, (cutoff_date.isoformat(),))
                by_severity = dict(cursor.fetchall())
                
                # Incidents by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) FROM security_incidents 
                    WHERE created_at >= ?
                    GROUP BY status
                """, (cutoff_date.isoformat(),))
                by_status = dict(cursor.fetchall())
                
                # Incidents by type
                cursor = conn.execute("""
                    SELECT incident_type, COUNT(*) FROM security_incidents 
                    WHERE created_at >= ?
                    GROUP BY incident_type
                """, (cutoff_date.isoformat(),))
                by_type = dict(cursor.fetchall())
                
                # Active incidents
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_incidents 
                    WHERE status NOT IN ('resolved', 'closed')
                """)
                active_incidents = cursor.fetchone()[0]
            
            return {
                "total_incidents": total_incidents,
                "by_severity": by_severity,
                "by_status": by_status,
                "by_type": by_type,
                "active_incidents": active_incidents,
                "days": days
            }
        
        except Exception as e:
            logger.error(f"Error getting incident statistics: {e}")
            return {"error": str(e)}
    
    def _store_incident(self, incident: Incident):
        """Store incident in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO security_incidents 
                    (id, title, description, severity, incident_type, status, created_at, updated_at, 
                     assigned_to, playbook, timeline, resolution, metadata, source_alert)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident.id,
                    incident.title,
                    incident.description,
                    incident.severity.value,
                    incident.incident_type.value,
                    incident.status.value,
                    incident.created_at.isoformat(),
                    incident.updated_at.isoformat(),
                    incident.assigned_to,
                    incident.playbook,
                    json.dumps(incident.timeline),
                    incident.resolution,
                    json.dumps(incident.metadata),
                    json.dumps(incident.source_alert) if incident.source_alert else None
                ))
        except Exception as e:
            logger.error(f"Error storing incident: {e}")
    
    def _update_incident_status(self, incident_id: str, status: IncidentStatus, resolution: str = None):
        """Update incident status in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if resolution:
                    conn.execute("""
                        UPDATE security_incidents 
                        SET status = ?, updated_at = ?, resolution = ?
                        WHERE id = ?
                    """, (status.value, datetime.utcnow().isoformat(), resolution, incident_id))
                else:
                    conn.execute("""
                        UPDATE security_incidents 
                        SET status = ?, updated_at = ?
                        WHERE id = ?
                    """, (status.value, datetime.utcnow().isoformat(), incident_id))
        except Exception as e:
            logger.error(f"Error updating incident status: {e}")
    
    def _store_incident_event(self, incident_id: str, event: Dict[str, Any]):
        """Store incident event in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO incident_events 
                    (incident_id, event_type, description, timestamp, user_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    incident_id,
                    event["event_type"],
                    event["description"],
                    event["timestamp"],
                    event["user_id"],
                    json.dumps(event["metadata"])
                ))
        except Exception as e:
            logger.error(f"Error storing incident event: {e}")
    
    def _update_incident_assignment(self, incident_id: str, user_id: str, role: str):
        """Update incident assignment in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO incident_assignments 
                    (incident_id, user_id, role, assigned_at, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    incident_id,
                    user_id,
                    role,
                    datetime.utcnow().isoformat(),
                    "active"
                ))
        except Exception as e:
            logger.error(f"Error updating incident assignment: {e}")

# Factory function for creating incident response configuration
def create_incident_response_config() -> IncidentResponseConfig:
    """Create incident response configuration from environment variables"""
    return IncidentResponseConfig(
        enabled=os.getenv('INCIDENT_RESPONSE_ENABLED', 'true').lower() == 'true',
        auto_escalation=os.getenv('INCIDENT_AUTO_ESCALATION', 'true').lower() == 'true',
        escalation_threshold=int(os.getenv('INCIDENT_ESCALATION_THRESHOLD', '3')),
        response_team=os.getenv('INCIDENT_RESPONSE_TEAM', '').split(',') if os.getenv('INCIDENT_RESPONSE_TEAM') else [],
        escalation_team=os.getenv('INCIDENT_ESCALATION_TEAM', '').split(',') if os.getenv('INCIDENT_ESCALATION_TEAM') else [],
        playbooks=json.loads(os.getenv('INCIDENT_PLAYBOOKS', '{}')),
        notification_channels=os.getenv('INCIDENT_NOTIFICATION_CHANNELS', 'email,slack').split(','),
        
        email_enabled=os.getenv('INCIDENT_EMAIL_ENABLED', 'true').lower() == 'true',
        smtp_server=os.getenv('INCIDENT_SMTP_SERVER', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('INCIDENT_SMTP_PORT', '587')),
        smtp_username=os.getenv('INCIDENT_SMTP_USERNAME', ''),
        smtp_password=os.getenv('INCIDENT_SMTP_PASSWORD', ''),
        from_email=os.getenv('INCIDENT_FROM_EMAIL', 'incidents@mingus.com'),
        
        slack_enabled=os.getenv('INCIDENT_SLACK_ENABLED', 'true').lower() == 'true',
        slack_webhook_url=os.getenv('INCIDENT_SLACK_WEBHOOK_URL', ''),
        slack_channel=os.getenv('INCIDENT_SLACK_CHANNEL', '#incidents'),
        
        auto_containment=os.getenv('INCIDENT_AUTO_CONTAINMENT', 'true').lower() == 'true',
        auto_notification=os.getenv('INCIDENT_AUTO_NOTIFICATION', 'true').lower() == 'true',
        auto_documentation=os.getenv('INCIDENT_AUTO_DOCUMENTATION', 'true').lower() == 'true',
        
        escalation_timeout_minutes=int(os.getenv('INCIDENT_ESCALATION_TIMEOUT_MINUTES', '30')),
        critical_escalation_timeout_minutes=int(os.getenv('INCIDENT_CRITICAL_ESCALATION_TIMEOUT_MINUTES', '15'))
    )

# Global incident manager instance
_incident_manager = None

def get_incident_manager() -> EnhancedSecurityIncidentManager:
    """Get global incident manager instance"""
    global _incident_manager
    
    if _incident_manager is None:
        config = create_incident_response_config()
        _incident_manager = EnhancedSecurityIncidentManager(config)
    
    return _incident_manager 