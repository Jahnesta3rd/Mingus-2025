"""
Security Incident Response System for MINGUS
Comprehensive incident handling, threat detection, and response workflows
"""

import os
import sys
import json
import time
import hashlib
import requests
import subprocess
import ssl
import socket
import re
import random
import string
import threading
import asyncio
import aiohttp
import multiprocessing
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import unittest
from loguru import logger
import sqlite3
import psutil
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import urllib.parse
import queue
import statistics
import concurrent.futures
import threading
import signal
import gc
import schedule
import git
import docker
import kubernetes
from pathlib import Path
import tempfile
import shutil
import xml.etree.ElementTree as ET
import csv
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import slack_sdk
import discord
import telegram

class IncidentSeverity(Enum):
    """Incident severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

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
    MALWARE = "malware"
    PHISHING = "phishing"
    DATA_BREACH = "data_breach"
    DDOS_ATTACK = "ddos_attack"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    BRUTE_FORCE = "brute_force"
    INSIDER_THREAT = "insider_threat"
    RANSOMWARE = "ransomware"
    APT = "apt"
    ZERO_DAY = "zero_day"
    CONFIGURATION_ERROR = "configuration_error"
    COMPLIANCE_VIOLATION = "compliance_violation"

class ThreatLevel(Enum):
    """Threat levels"""
    IMMINENT = "imminent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

@dataclass
class SecurityIncident:
    """Security incident structure"""
    incident_id: str
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    threat_level: ThreatLevel
    discovery_time: datetime
    affected_systems: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    indicators_of_compromise: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    assigned_team: str = ""
    assigned_analyst: str = ""
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    related_incidents: List[str] = field(default_factory=list)
    containment_actions: List[str] = field(default_factory=list)
    eradication_actions: List[str] = field(default_factory=list)
    recovery_actions: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)

@dataclass
class ThreatIntelligence:
    """Threat intelligence structure"""
    threat_id: str
    threat_name: str
    threat_type: str
    description: str
    indicators: List[str] = field(default_factory=list)
    tactics: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    procedures: List[str] = field(default_factory=list)
    severity: ThreatLevel = ThreatLevel.MEDIUM
    confidence: float = 0.5
    source: str = ""
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    mitigation: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

@dataclass
class IncidentResponse:
    """Incident response structure"""
    response_id: str
    incident_id: str
    response_type: str
    description: str
    actions_taken: List[str] = field(default_factory=list)
    evidence_collected: List[str] = field(default_factory=list)
    systems_affected: List[str] = field(default_factory=list)
    users_notified: List[str] = field(default_factory=list)
    containment_effective: bool = False
    eradication_complete: bool = False
    recovery_successful: bool = False
    response_time: float = 0.0
    analyst: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

class AutomatedIncidentHandler:
    """Automated incident handling system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.incidents_db = "security/incidents.db"
        self.threat_intel_db = "security/threat_intelligence.db"
        self.response_playbooks = {}
        self.threat_indicators = {}
        self._init_databases()
        self._load_playbooks()
        self._load_threat_intelligence()
    
    def _init_databases(self):
        """Initialize incident and threat intelligence databases"""
        # Initialize incidents database
        conn = sqlite3.connect(self.incidents_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                incident_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                threat_level TEXT NOT NULL,
                discovery_time TEXT NOT NULL,
                affected_systems TEXT,
                affected_users TEXT,
                indicators_of_compromise TEXT,
                evidence TEXT,
                timeline TEXT,
                assigned_team TEXT,
                assigned_analyst TEXT,
                priority INTEGER DEFAULT 0,
                tags TEXT,
                related_incidents TEXT,
                containment_actions TEXT,
                eradication_actions TEXT,
                recovery_actions TEXT,
                lessons_learned TEXT
            )
        ''')
        
        # Initialize threat intelligence database
        conn_threat = sqlite3.connect(self.threat_intel_db)
        cursor_threat = conn_threat.cursor()
        
        cursor_threat.execute('''
            CREATE TABLE IF NOT EXISTS threat_intelligence (
                threat_id TEXT PRIMARY KEY,
                threat_name TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                description TEXT,
                indicators TEXT,
                tactics TEXT,
                techniques TEXT,
                procedures TEXT,
                severity TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                source TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                mitigation TEXT,
                references TEXT
            )
        ''')
        
        conn.commit()
        conn_threat.commit()
        conn.close()
        conn_threat.close()
    
    def _load_playbooks(self):
        """Load incident response playbooks"""
        playbooks_file = "security/playbooks/incident_response_playbooks.json"
        if os.path.exists(playbooks_file):
            try:
                with open(playbooks_file, 'r') as f:
                    self.response_playbooks = json.load(f)
            except Exception as e:
                logger.error(f"Error loading playbooks: {e}")
                self._create_default_playbooks()
        else:
            self._create_default_playbooks()
    
    def _create_default_playbooks(self):
        """Create default incident response playbooks"""
        self.response_playbooks = {
            "malware": {
                "name": "Malware Incident Response",
                "description": "Standard response for malware incidents",
                "severity": "high",
                "steps": [
                    "Isolate affected systems",
                    "Collect malware samples",
                    "Analyze malware behavior",
                    "Remove malware",
                    "Restore from clean backup",
                    "Update security controls"
                ],
                "automated_actions": [
                    "block_ips",
                    "quarantine_systems",
                    "collect_artifacts",
                    "update_antivirus"
                ]
            },
            "data_breach": {
                "name": "Data Breach Response",
                "description": "Standard response for data breach incidents",
                "severity": "critical",
                "steps": [
                    "Assess scope of breach",
                    "Contain the breach",
                    "Preserve evidence",
                    "Notify stakeholders",
                    "Report to authorities",
                    "Implement additional controls"
                ],
                "automated_actions": [
                    "freeze_accounts",
                    "backup_evidence",
                    "enable_monitoring",
                    "notify_compliance"
                ]
            },
            "ddos_attack": {
                "name": "DDoS Attack Response",
                "description": "Standard response for DDoS attacks",
                "severity": "high",
                "steps": [
                    "Activate DDoS protection",
                    "Monitor traffic patterns",
                    "Block malicious traffic",
                    "Scale resources",
                    "Analyze attack vectors",
                    "Implement additional protections"
                ],
                "automated_actions": [
                    "enable_ddos_protection",
                    "block_ips",
                    "scale_resources",
                    "monitor_traffic"
                ]
            },
            "unauthorized_access": {
                "name": "Unauthorized Access Response",
                "description": "Standard response for unauthorized access",
                "severity": "high",
                "steps": [
                    "Identify compromised accounts",
                    "Disable affected accounts",
                    "Investigate access patterns",
                    "Reset credentials",
                    "Implement additional monitoring",
                    "Review access controls"
                ],
                "automated_actions": [
                    "disable_accounts",
                    "reset_passwords",
                    "enable_monitoring",
                    "block_ips"
                ]
            }
        }
    
    def _load_threat_intelligence(self):
        """Load threat intelligence data"""
        threat_file = "security/threat_intelligence.json"
        if os.path.exists(threat_file):
            try:
                with open(threat_file, 'r') as f:
                    threat_data = json.load(f)
                    for threat in threat_data:
                        self.threat_indicators[threat["threat_id"]] = threat
            except Exception as e:
                logger.error(f"Error loading threat intelligence: {e}")
                self._create_default_threat_intelligence()
        else:
            self._create_default_threat_intelligence()
    
    def _create_default_threat_intelligence(self):
        """Create default threat intelligence"""
        self.threat_indicators = {
            "APT-001": {
                "threat_id": "APT-001",
                "threat_name": "Advanced Persistent Threat",
                "threat_type": "apt",
                "description": "Sophisticated long-term cyber attack",
                "indicators": ["suspicious_network_traffic", "unusual_login_patterns"],
                "tactics": ["initial_access", "persistence", "privilege_escalation"],
                "techniques": ["spear_phishing", "malware_deployment"],
                "severity": "critical",
                "confidence": 0.8
            },
            "MALWARE-001": {
                "threat_id": "MALWARE-001",
                "threat_name": "Ransomware Attack",
                "threat_type": "ransomware",
                "description": "Encrypts files and demands ransom",
                "indicators": ["file_encryption", "ransom_note", "unusual_processes"],
                "tactics": ["impact"],
                "techniques": ["data_encrypted_for_impact"],
                "severity": "critical",
                "confidence": 0.9
            }
        }
    
    def detect_incident(self, event_data: Dict[str, Any]) -> Optional[SecurityIncident]:
        """Detect security incident from event data"""
        try:
            # Analyze event data for incident indicators
            incident_indicators = self._analyze_event_indicators(event_data)
            
            if incident_indicators:
                # Determine incident type and severity
                incident_type = self._determine_incident_type(incident_indicators)
                severity = self._determine_incident_severity(incident_indicators)
                threat_level = self._assess_threat_level(incident_indicators)
                
                # Create incident
                incident = SecurityIncident(
                    incident_id=f"INC-{int(time.time())}",
                    title=self._generate_incident_title(incident_type, event_data),
                    description=self._generate_incident_description(incident_indicators, event_data),
                    incident_type=incident_type,
                    severity=severity,
                    status=IncidentStatus.OPEN,
                    threat_level=threat_level,
                    discovery_time=datetime.utcnow(),
                    affected_systems=event_data.get("affected_systems", []),
                    affected_users=event_data.get("affected_users", []),
                    indicators_of_compromise=incident_indicators,
                    evidence=event_data,
                    priority=self._calculate_priority(severity, threat_level)
                )
                
                # Save incident to database
                self._save_incident(incident)
                
                logger.warning(f"Security incident detected: {incident.incident_id} - {incident.title}")
                return incident
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting incident: {e}")
            return None
    
    def _analyze_event_indicators(self, event_data: Dict[str, Any]) -> List[str]:
        """Analyze event data for incident indicators"""
        indicators = []
        
        # Check for common attack patterns
        if "sql_injection" in str(event_data).lower():
            indicators.append("sql_injection_attempt")
        
        if "xss" in str(event_data).lower():
            indicators.append("xss_attempt")
        
        if "brute_force" in str(event_data).lower():
            indicators.append("brute_force_attempt")
        
        if "ddos" in str(event_data).lower():
            indicators.append("ddos_attack")
        
        if "malware" in str(event_data).lower():
            indicators.append("malware_detected")
        
        if "unauthorized_access" in str(event_data).lower():
            indicators.append("unauthorized_access")
        
        if "data_exfiltration" in str(event_data).lower():
            indicators.append("data_breach")
        
        # Check for suspicious patterns
        if event_data.get("failed_login_attempts", 0) > 10:
            indicators.append("excessive_failed_logins")
        
        if event_data.get("unusual_network_traffic", False):
            indicators.append("suspicious_network_activity")
        
        if event_data.get("privilege_escalation", False):
            indicators.append("privilege_escalation_attempt")
        
        return indicators
    
    def _determine_incident_type(self, indicators: List[str]) -> IncidentType:
        """Determine incident type from indicators"""
        if "sql_injection_attempt" in indicators:
            return IncidentType.SQL_INJECTION
        elif "xss_attempt" in indicators:
            return IncidentType.XSS_ATTACK
        elif "brute_force_attempt" in indicators:
            return IncidentType.BRUTE_FORCE
        elif "ddos_attack" in indicators:
            return IncidentType.DDOS_ATTACK
        elif "malware_detected" in indicators:
            return IncidentType.MALWARE
        elif "unauthorized_access" in indicators:
            return IncidentType.UNAUTHORIZED_ACCESS
        elif "data_breach" in indicators:
            return IncidentType.DATA_BREACH
        else:
            return IncidentType.UNAUTHORIZED_ACCESS
    
    def _determine_incident_severity(self, indicators: List[str]) -> IncidentSeverity:
        """Determine incident severity from indicators"""
        critical_indicators = ["data_breach", "malware_detected", "ransomware"]
        high_indicators = ["sql_injection_attempt", "xss_attempt", "ddos_attack"]
        medium_indicators = ["brute_force_attempt", "unauthorized_access"]
        
        for indicator in indicators:
            if indicator in critical_indicators:
                return IncidentSeverity.CRITICAL
            elif indicator in high_indicators:
                return IncidentSeverity.HIGH
            elif indicator in medium_indicators:
                return IncidentSeverity.MEDIUM
        
        return IncidentSeverity.LOW
    
    def _assess_threat_level(self, indicators: List[str]) -> ThreatLevel:
        """Assess threat level from indicators"""
        if any(indicator in ["data_breach", "malware_detected", "ransomware"] for indicator in indicators):
            return ThreatLevel.IMMINENT
        elif any(indicator in ["sql_injection_attempt", "xss_attempt", "ddos_attack"] for indicator in indicators):
            return ThreatLevel.HIGH
        elif any(indicator in ["brute_force_attempt", "unauthorized_access"] for indicator in indicators):
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _calculate_priority(self, severity: IncidentSeverity, threat_level: ThreatLevel) -> int:
        """Calculate incident priority"""
        severity_scores = {
            IncidentSeverity.CRITICAL: 5,
            IncidentSeverity.HIGH: 4,
            IncidentSeverity.MEDIUM: 3,
            IncidentSeverity.LOW: 2,
            IncidentSeverity.INFO: 1
        }
        
        threat_scores = {
            ThreatLevel.IMMINENT: 5,
            ThreatLevel.HIGH: 4,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.LOW: 2,
            ThreatLevel.NONE: 1
        }
        
        return severity_scores[severity] + threat_scores[threat_level]
    
    def _generate_incident_title(self, incident_type: IncidentType, event_data: Dict[str, Any]) -> str:
        """Generate incident title"""
        base_titles = {
            IncidentType.SQL_INJECTION: "SQL Injection Attempt",
            IncidentType.XSS_ATTACK: "Cross-Site Scripting Attack",
            IncidentType.BRUTE_FORCE: "Brute Force Attack",
            IncidentType.DDOS_ATTACK: "DDoS Attack",
            IncidentType.MALWARE: "Malware Detection",
            IncidentType.UNAUTHORIZED_ACCESS: "Unauthorized Access Attempt",
            IncidentType.DATA_BREACH: "Data Breach Incident",
            IncidentType.RANSOMWARE: "Ransomware Attack"
        }
        
        return base_titles.get(incident_type, "Security Incident")
    
    def _generate_incident_description(self, indicators: List[str], event_data: Dict[str, Any]) -> str:
        """Generate incident description"""
        description = f"Security incident detected with indicators: {', '.join(indicators)}. "
        
        if event_data.get("source_ip"):
            description += f"Source IP: {event_data['source_ip']}. "
        
        if event_data.get("affected_systems"):
            description += f"Affected systems: {', '.join(event_data['affected_systems'])}. "
        
        if event_data.get("timestamp"):
            description += f"Detected at: {event_data['timestamp']}."
        
        return description
    
    def _save_incident(self, incident: SecurityIncident):
        """Save incident to database"""
        conn = sqlite3.connect(self.incidents_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO incidents (
                incident_id, title, description, incident_type, severity, status,
                threat_level, discovery_time, affected_systems, affected_users,
                indicators_of_compromise, evidence, timeline, assigned_team,
                assigned_analyst, priority, tags, related_incidents,
                containment_actions, eradication_actions, recovery_actions, lessons_learned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incident.incident_id,
            incident.title,
            incident.description,
            incident.incident_type.value,
            incident.severity.value,
            incident.status.value,
            incident.threat_level.value,
            incident.discovery_time.isoformat(),
            json.dumps(incident.affected_systems),
            json.dumps(incident.affected_users),
            json.dumps(incident.indicators_of_compromise),
            json.dumps(incident.evidence),
            json.dumps(incident.timeline),
            incident.assigned_team,
            incident.assigned_analyst,
            incident.priority,
            json.dumps(incident.tags),
            json.dumps(incident.related_incidents),
            json.dumps(incident.containment_actions),
            json.dumps(incident.eradication_actions),
            json.dumps(incident.recovery_actions),
            json.dumps(incident.lessons_learned)
        ))
        
        conn.commit()
        conn.close()

class IncidentResponseWorkflow:
    """Incident response workflow management"""
    
    def __init__(self, incident_handler: AutomatedIncidentHandler):
        self.incident_handler = incident_handler
        self.response_teams = {
            "critical": ["security_team", "management", "legal", "pr"],
            "high": ["security_team", "management"],
            "medium": ["security_team"],
            "low": ["security_team"]
        }
        self.escalation_thresholds = {
            "critical": 0,  # Immediate escalation
            "high": 30,     # 30 minutes
            "medium": 120,  # 2 hours
            "low": 480      # 8 hours
        }
    
    def handle_incident(self, incident: SecurityIncident) -> IncidentResponse:
        """Handle security incident with automated response"""
        try:
            logger.info(f"Starting incident response for {incident.incident_id}")
            
            # Create response record
            response = IncidentResponse(
                response_id=f"RESP-{incident.incident_id}",
                incident_id=incident.incident_id,
                response_type="automated",
                description=f"Automated response for {incident.title}",
                analyst="automated_system"
            )
            
            start_time = time.time()
            
            # Execute response workflow
            self._execute_response_workflow(incident, response)
            
            response.response_time = time.time() - start_time
            
            # Update incident status
            self._update_incident_status(incident, response)
            
            # Notify stakeholders
            self._notify_stakeholders(incident, response)
            
            logger.info(f"Incident response completed for {incident.incident_id}")
            return response
        
        except Exception as e:
            logger.error(f"Error handling incident {incident.incident_id}: {e}")
            return None
    
    def _execute_response_workflow(self, incident: SecurityIncident, response: IncidentResponse):
        """Execute incident response workflow"""
        # Get appropriate playbook
        playbook = self.incident_handler.response_playbooks.get(incident.incident_type.value, {})
        
        if not playbook:
            logger.warning(f"No playbook found for incident type: {incident.incident_type.value}")
            return
        
        # Execute automated actions
        automated_actions = playbook.get("automated_actions", [])
        for action in automated_actions:
            try:
                self._execute_automated_action(action, incident, response)
            except Exception as e:
                logger.error(f"Error executing automated action {action}: {e}")
        
        # Execute manual steps
        manual_steps = playbook.get("steps", [])
        for step in manual_steps:
            response.actions_taken.append(f"Manual step required: {step}")
        
        # Update response status
        if "containment" in str(automated_actions).lower():
            response.containment_effective = True
        
        if "eradication" in str(automated_actions).lower():
            response.eradication_complete = True
    
    def _execute_automated_action(self, action: str, incident: SecurityIncident, response: IncidentResponse):
        """Execute automated response action"""
        if action == "block_ips":
            self._block_malicious_ips(incident, response)
        elif action == "quarantine_systems":
            self._quarantine_affected_systems(incident, response)
        elif action == "collect_artifacts":
            self._collect_incident_artifacts(incident, response)
        elif action == "update_antivirus":
            self._update_antivirus_signatures(incident, response)
        elif action == "freeze_accounts":
            self._freeze_compromised_accounts(incident, response)
        elif action == "backup_evidence":
            self._backup_incident_evidence(incident, response)
        elif action == "enable_monitoring":
            self._enable_enhanced_monitoring(incident, response)
        elif action == "notify_compliance":
            self._notify_compliance_team(incident, response)
        elif action == "enable_ddos_protection":
            self._enable_ddos_protection(incident, response)
        elif action == "scale_resources":
            self._scale_resources_for_attack(incident, response)
        elif action == "monitor_traffic":
            self._monitor_network_traffic(incident, response)
        elif action == "disable_accounts":
            self._disable_compromised_accounts(incident, response)
        elif action == "reset_passwords":
            self._reset_affected_passwords(incident, response)
    
    def _block_malicious_ips(self, incident: SecurityIncident, response: IncidentResponse):
        """Block malicious IP addresses"""
        try:
            # Extract IP addresses from incident evidence
            ips_to_block = []
            if "source_ip" in incident.evidence:
                ips_to_block.append(incident.evidence["source_ip"])
            
            # Block IPs using firewall
            for ip in ips_to_block:
                # Simulate IP blocking
                logger.info(f"Blocking malicious IP: {ip}")
                response.actions_taken.append(f"Blocked IP: {ip}")
            
            response.evidence_collected.append("blocked_ips")
        
        except Exception as e:
            logger.error(f"Error blocking IPs: {e}")
    
    def _quarantine_affected_systems(self, incident: SecurityIncident, response: IncidentResponse):
        """Quarantine affected systems"""
        try:
            for system in incident.affected_systems:
                logger.info(f"Quarantining system: {system}")
                response.actions_taken.append(f"Quarantined system: {system}")
            
            response.evidence_collected.append("quarantined_systems")
        
        except Exception as e:
            logger.error(f"Error quarantining systems: {e}")
    
    def _collect_incident_artifacts(self, incident: SecurityIncident, response: IncidentResponse):
        """Collect incident artifacts"""
        try:
            artifacts = [
                "system_logs",
                "network_logs",
                "memory_dumps",
                "disk_images"
            ]
            
            for artifact in artifacts:
                logger.info(f"Collecting artifact: {artifact}")
                response.actions_taken.append(f"Collected artifact: {artifact}")
            
            response.evidence_collected.extend(artifacts)
        
        except Exception as e:
            logger.error(f"Error collecting artifacts: {e}")
    
    def _update_antivirus_signatures(self, incident: SecurityIncident, response: IncidentResponse):
        """Update antivirus signatures"""
        try:
            logger.info("Updating antivirus signatures")
            response.actions_taken.append("Updated antivirus signatures")
            response.evidence_collected.append("antivirus_updated")
        
        except Exception as e:
            logger.error(f"Error updating antivirus: {e}")
    
    def _freeze_compromised_accounts(self, incident: SecurityIncident, response: IncidentResponse):
        """Freeze compromised accounts"""
        try:
            for user in incident.affected_users:
                logger.info(f"Freezing account: {user}")
                response.actions_taken.append(f"Frozen account: {user}")
            
            response.evidence_collected.append("frozen_accounts")
        
        except Exception as e:
            logger.error(f"Error freezing accounts: {e}")
    
    def _backup_incident_evidence(self, incident: SecurityIncident, response: IncidentResponse):
        """Backup incident evidence"""
        try:
            logger.info("Backing up incident evidence")
            response.actions_taken.append("Backed up incident evidence")
            response.evidence_collected.append("evidence_backup")
        
        except Exception as e:
            logger.error(f"Error backing up evidence: {e}")
    
    def _enable_enhanced_monitoring(self, incident: SecurityIncident, response: IncidentResponse):
        """Enable enhanced monitoring"""
        try:
            logger.info("Enabling enhanced monitoring")
            response.actions_taken.append("Enabled enhanced monitoring")
            response.evidence_collected.append("enhanced_monitoring")
        
        except Exception as e:
            logger.error(f"Error enabling monitoring: {e}")
    
    def _notify_compliance_team(self, incident: SecurityIncident, response: IncidentResponse):
        """Notify compliance team"""
        try:
            logger.info("Notifying compliance team")
            response.actions_taken.append("Notified compliance team")
            response.users_notified.append("compliance_team")
        
        except Exception as e:
            logger.error(f"Error notifying compliance team: {e}")
    
    def _enable_ddos_protection(self, incident: SecurityIncident, response: IncidentResponse):
        """Enable DDoS protection"""
        try:
            logger.info("Enabling DDoS protection")
            response.actions_taken.append("Enabled DDoS protection")
            response.evidence_collected.append("ddos_protection_enabled")
        
        except Exception as e:
            logger.error(f"Error enabling DDoS protection: {e}")
    
    def _scale_resources_for_attack(self, incident: SecurityIncident, response: IncidentResponse):
        """Scale resources for attack"""
        try:
            logger.info("Scaling resources for attack")
            response.actions_taken.append("Scaled resources for attack")
            response.evidence_collected.append("resources_scaled")
        
        except Exception as e:
            logger.error(f"Error scaling resources: {e}")
    
    def _monitor_network_traffic(self, incident: SecurityIncident, response: IncidentResponse):
        """Monitor network traffic"""
        try:
            logger.info("Monitoring network traffic")
            response.actions_taken.append("Monitoring network traffic")
            response.evidence_collected.append("traffic_monitoring")
        
        except Exception as e:
            logger.error(f"Error monitoring traffic: {e}")
    
    def _disable_compromised_accounts(self, incident: SecurityIncident, response: IncidentResponse):
        """Disable compromised accounts"""
        try:
            for user in incident.affected_users:
                logger.info(f"Disabling account: {user}")
                response.actions_taken.append(f"Disabled account: {user}")
            
            response.evidence_collected.append("disabled_accounts")
        
        except Exception as e:
            logger.error(f"Error disabling accounts: {e}")
    
    def _reset_affected_passwords(self, incident: SecurityIncident, response: IncidentResponse):
        """Reset affected passwords"""
        try:
            for user in incident.affected_users:
                logger.info(f"Resetting password for: {user}")
                response.actions_taken.append(f"Reset password for: {user}")
            
            response.evidence_collected.append("passwords_reset")
        
        except Exception as e:
            logger.error(f"Error resetting passwords: {e}")
    
    def _update_incident_status(self, incident: SecurityIncident, response: IncidentResponse):
        """Update incident status based on response"""
        if response.containment_effective:
            incident.status = IncidentStatus.CONTAINED
        elif response.eradication_complete:
            incident.status = IncidentStatus.RESOLVED
        else:
            incident.status = IncidentStatus.INVESTIGATING
        
        # Update incident timeline
        incident.timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "Automated response completed",
            "analyst": "automated_system",
            "details": f"Response time: {response.response_time:.2f}s"
        })
        
        # Save updated incident
        self.incident_handler._save_incident(incident)
    
    def _notify_stakeholders(self, incident: SecurityIncident, response: IncidentResponse):
        """Notify stakeholders about incident"""
        try:
            # Determine notification level based on severity
            notification_teams = self.response_teams.get(incident.severity.value, ["security_team"])
            
            for team in notification_teams:
                logger.info(f"Notifying team: {team}")
                response.users_notified.append(team)
            
            # Send notifications
            self._send_notifications(incident, response, notification_teams)
        
        except Exception as e:
            logger.error(f"Error notifying stakeholders: {e}")
    
    def _send_notifications(self, incident: SecurityIncident, response: IncidentResponse, teams: List[str]):
        """Send notifications to teams"""
        try:
            # Email notification
            self._send_email_notification(incident, response, teams)
            
            # Slack notification
            self._send_slack_notification(incident, response, teams)
            
            # SMS notification for critical incidents
            if incident.severity == IncidentSeverity.CRITICAL:
                self._send_sms_notification(incident, response, teams)
        
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def _send_email_notification(self, incident: SecurityIncident, response: IncidentResponse, teams: List[str]):
        """Send email notification"""
        try:
            subject = f"Security Incident Alert: {incident.incident_id}"
            body = f"""
            Security Incident Detected
            
            Incident ID: {incident.incident_id}
            Title: {incident.title}
            Severity: {incident.severity.value}
            Status: {incident.status.value}
            Discovery Time: {incident.discovery_time}
            
            Response Actions Taken:
            {chr(10).join(response.actions_taken)}
            
            Please review and take appropriate action.
            """
            
            # Simulate email sending
            logger.info(f"Email notification sent for incident {incident.incident_id}")
        
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def _send_slack_notification(self, incident: SecurityIncident, response: IncidentResponse, teams: List[str]):
        """Send Slack notification"""
        try:
            message = f"""
            🚨 Security Incident Alert 🚨
            
            *Incident ID:* {incident.incident_id}
            *Title:* {incident.title}
            *Severity:* {incident.severity.value}
            *Status:* {incident.status.value}
            
            *Response Actions:*
            {chr(10).join(f"• {action}" for action in response.actions_taken)}
            """
            
            # Simulate Slack notification
            logger.info(f"Slack notification sent for incident {incident.incident_id}")
        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def _send_sms_notification(self, incident: SecurityIncident, response: IncidentResponse, teams: List[str]):
        """Send SMS notification"""
        try:
            message = f"CRITICAL: Security incident {incident.incident_id} detected. Severity: {incident.severity.value}. Check email for details."
            
            # Simulate SMS sending
            logger.info(f"SMS notification sent for incident {incident.incident_id}")
        
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")

class SecurityIncidentResponseSystem:
    """Main security incident response system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.incident_handler = AutomatedIncidentHandler(base_url)
        self.response_workflow = IncidentResponseWorkflow(self.incident_handler)
        self.active_incidents = {}
        self.incident_history = []
    
    def process_security_event(self, event_data: Dict[str, Any]) -> Optional[SecurityIncident]:
        """Process security event and handle incident if detected"""
        try:
            # Detect incident from event
            incident = self.incident_handler.detect_incident(event_data)
            
            if incident:
                # Handle incident with automated response
                response = self.response_workflow.handle_incident(incident)
                
                # Store incident
                self.active_incidents[incident.incident_id] = incident
                self.incident_history.append({
                    "incident": incident,
                    "response": response,
                    "timestamp": datetime.utcnow()
                })
                
                logger.warning(f"Security incident processed: {incident.incident_id}")
                return incident
            
            return None
        
        except Exception as e:
            logger.error(f"Error processing security event: {e}")
            return None
    
    def get_active_incidents(self) -> Dict[str, SecurityIncident]:
        """Get all active incidents"""
        return self.active_incidents
    
    def get_incident_history(self) -> List[Dict[str, Any]]:
        """Get incident history"""
        return self.incident_history
    
    def get_incident_by_id(self, incident_id: str) -> Optional[SecurityIncident]:
        """Get incident by ID"""
        return self.active_incidents.get(incident_id)
    
    def update_incident_status(self, incident_id: str, status: IncidentStatus, analyst: str = ""):
        """Update incident status"""
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
            incident.status = status
            incident.assigned_analyst = analyst
            
            # Update timeline
            incident.timeline.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": f"Status updated to {status.value}",
                "analyst": analyst or "system",
                "details": f"Status changed from {incident.status.value} to {status.value}"
            })
            
            # Save to database
            self.incident_handler._save_incident(incident)
            
            logger.info(f"Incident {incident_id} status updated to {status.value}")
    
    def close_incident(self, incident_id: str, analyst: str = "", lessons_learned: List[str] = None):
        """Close incident"""
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
            incident.status = IncidentStatus.CLOSED
            incident.assigned_analyst = analyst
            
            if lessons_learned:
                incident.lessons_learned.extend(lessons_learned)
            
            # Update timeline
            incident.timeline.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "Incident closed",
                "analyst": analyst or "system",
                "details": "Incident resolution completed"
            })
            
            # Save to database
            self.incident_handler._save_incident(incident)
            
            # Remove from active incidents
            del self.active_incidents[incident_id]
            
            logger.info(f"Incident {incident_id} closed")

def create_security_incident_response_system(base_url: str = "http://localhost:5000") -> SecurityIncidentResponseSystem:
    """Create security incident response system"""
    return SecurityIncidentResponseSystem(base_url)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Incident Response System")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for system")
    parser.add_argument("--event-file", help="Path to security event JSON file")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring mode")
    parser.add_argument("--list-incidents", action="store_true", help="List active incidents")
    
    args = parser.parse_args()
    
    # Create incident response system
    ir_system = create_security_incident_response_system(args.base_url)
    
    if args.event_file:
        # Process event file
        with open(args.event_file, 'r') as f:
            event_data = json.load(f)
        
        incident = ir_system.process_security_event(event_data)
        if incident:
            print(f"Security incident detected: {incident.incident_id}")
            print(f"Title: {incident.title}")
            print(f"Severity: {incident.severity.value}")
            print(f"Status: {incident.status.value}")
        else:
            print("No security incident detected")
    
    elif args.list_incidents:
        # List active incidents
        active_incidents = ir_system.get_active_incidents()
        if active_incidents:
            print("Active Security Incidents:")
            for incident_id, incident in active_incidents.items():
                print(f"  {incident_id}: {incident.title} ({incident.severity.value})")
        else:
            print("No active incidents")
    
    elif args.monitor:
        # Start monitoring mode
        print("Starting security incident monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Simulate monitoring
                time.sleep(60)
                print("Monitoring for security incidents...")
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    
    else:
        print("Security Incident Response System")
        print("Use --help for usage information") 