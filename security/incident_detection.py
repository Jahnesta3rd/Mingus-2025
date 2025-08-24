"""
Comprehensive Incident Detection System for MINGUS
Specialized detection for data breaches, unauthorized access, payment fraud, account compromise, system intrusion, data exfiltration, and service disruption attacks
"""

import os
import sys
import json
import time
import hashlib
import requests
import re
import random
import string
import threading
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import sqlite3
import yaml
from cryptography.fernet import Fernet
import base64
import urllib.parse
import queue
import statistics
import concurrent.futures
import threading
import signal
import gc
import schedule
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

class DetectionType(Enum):
    """Detection types"""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PAYMENT_FRAUD = "payment_fraud"
    ACCOUNT_COMPROMISE = "account_compromise"
    SYSTEM_INTRUSION = "system_intrusion"
    DATA_EXFILTRATION = "data_exfiltration"
    SERVICE_DISRUPTION = "service_disruption"

class DetectionSeverity(Enum):
    """Detection severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class DetectionConfidence(Enum):
    """Detection confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class DetectionRule:
    """Detection rule structure"""
    rule_id: str
    name: str
    description: str
    detection_type: DetectionType
    severity: DetectionSeverity
    confidence: DetectionConfidence
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    threshold: int = 1
    time_window: int = 300  # 5 minutes
    tags: List[str] = field(default_factory=list)

@dataclass
class DetectionEvent:
    """Detection event structure"""
    event_id: str
    rule_id: str
    detection_type: DetectionType
    severity: DetectionSeverity
    confidence: DetectionConfidence
    timestamp: datetime
    source_ip: str = ""
    source_user: str = ""
    affected_systems: List[str] = field(default_factory=list)
    affected_data: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

class DataBreachDetector:
    """Data breach detection capabilities"""
    
    def __init__(self):
        self.sensitive_data_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP address
            r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b',  # IBAN
            r'\b\d{10,11}\b',  # Phone number
        ]
        
        self.data_access_patterns = [
            "bulk_data_export",
            "database_dump",
            "mass_data_download",
            "unauthorized_data_access",
            "privileged_data_query"
        ]
    
    def detect_data_breach(self, event_data: Dict[str, Any]) -> Optional[DetectionEvent]:
        """Detect data breach attempts"""
        try:
            indicators = []
            evidence = {}
            
            # Check for sensitive data patterns
            if "data_content" in event_data:
                content = str(event_data["data_content"])
                for pattern in self.sensitive_data_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        indicators.append(f"sensitive_data_detected_{pattern}")
                        evidence[f"sensitive_data_{pattern}"] = len(matches)
            
            # Check for bulk data access
            if "data_volume" in event_data:
                volume = event_data["data_volume"]
                if volume > 1000:  # More than 1000 records
                    indicators.append("bulk_data_access")
                    evidence["data_volume"] = volume
            
            # Check for unauthorized data access
            if "access_type" in event_data:
                access_type = event_data["access_type"]
                if access_type in self.data_access_patterns:
                    indicators.append("unauthorized_data_access")
                    evidence["access_type"] = access_type
            
            # Check for data export activities
            if "export_format" in event_data:
                indicators.append("data_export_attempt")
                evidence["export_format"] = event_data["export_format"]
            
            # Check for unusual data queries
            if "query_pattern" in event_data:
                query = event_data["query_pattern"]
                if "SELECT *" in query or "UNION" in query:
                    indicators.append("suspicious_data_query")
                    evidence["query_pattern"] = query
            
            if indicators:
                return DetectionEvent(
                    event_id=f"DB-{int(time.time())}",
                    rule_id="DATA_BREACH_001",
                    detection_type=DetectionType.DATA_BREACH,
                    severity=DetectionSeverity.HIGH,
                    confidence=DetectionConfidence.MEDIUM,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip", ""),
                    source_user=event_data.get("source_user", ""),
                    affected_systems=event_data.get("affected_systems", []),
                    affected_data=event_data.get("affected_data", []),
                    indicators=indicators,
                    evidence=evidence,
                    context=event_data
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting data breach: {e}")
            return None

class UnauthorizedAccessDetector:
    """Unauthorized access detection capabilities"""
    
    def __init__(self):
        self.access_patterns = [
            "failed_authentication",
            "privilege_escalation",
            "unauthorized_endpoint",
            "session_hijacking",
            "credential_stuffing"
        ]
        
        self.suspicious_ips = []
        self.failed_attempts = {}
    
    def detect_unauthorized_access(self, event_data: Dict[str, Any]) -> Optional[DetectionEvent]:
        """Detect unauthorized access attempts"""
        try:
            indicators = []
            evidence = {}
            
            # Check for failed authentication attempts
            if "failed_attempts" in event_data:
                attempts = event_data["failed_attempts"]
                if attempts > 5:
                    indicators.append("excessive_failed_attempts")
                    evidence["failed_attempts"] = attempts
            
            # Check for privilege escalation
            if "privilege_level" in event_data and "requested_level" in event_data:
                current_level = event_data["privilege_level"]
                requested_level = event_data["requested_level"]
                if requested_level > current_level:
                    indicators.append("privilege_escalation_attempt")
                    evidence["privilege_escalation"] = f"{current_level} -> {requested_level}"
            
            # Check for unauthorized endpoint access
            if "endpoint" in event_data:
                endpoint = event_data["endpoint"]
                if "/admin/" in endpoint or "/internal/" in endpoint:
                    if not event_data.get("authorized", False):
                        indicators.append("unauthorized_endpoint_access")
                        evidence["endpoint"] = endpoint
            
            # Check for session anomalies
            if "session_anomaly" in event_data:
                indicators.append("session_anomaly")
                evidence["session_anomaly"] = event_data["session_anomaly"]
            
            # Check for credential stuffing
            if "credential_stuffing" in event_data:
                indicators.append("credential_stuffing_attempt")
                evidence["credential_stuffing"] = event_data["credential_stuffing"]
            
            # Check for brute force attempts
            if "brute_force_indicators" in event_data:
                indicators.append("brute_force_attempt")
                evidence["brute_force"] = event_data["brute_force_indicators"]
            
            if indicators:
                return DetectionEvent(
                    event_id=f"UA-{int(time.time())}",
                    rule_id="UNAUTHORIZED_ACCESS_001",
                    detection_type=DetectionType.UNAUTHORIZED_ACCESS,
                    severity=DetectionSeverity.HIGH,
                    confidence=DetectionConfidence.MEDIUM,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip", ""),
                    source_user=event_data.get("source_user", ""),
                    affected_systems=event_data.get("affected_systems", []),
                    indicators=indicators,
                    evidence=evidence,
                    context=event_data
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting unauthorized access: {e}")
            return None

class PaymentFraudDetector:
    """Payment fraud detection capabilities"""
    
    def __init__(self):
        self.fraud_patterns = [
            "card_testing",
            "velocity_anomaly",
            "geographic_anomaly",
            "device_fingerprint_mismatch",
            "transaction_pattern_anomaly"
        ]
        
        self.velocity_thresholds = {
            "transactions_per_minute": 10,
            "transactions_per_hour": 50,
            "transactions_per_day": 200
        }
    
    def detect_payment_fraud(self, event_data: Dict[str, Any]) -> Optional[DetectionEvent]:
        """Detect payment fraud attempts"""
        try:
            indicators = []
            evidence = {}
            
            # Check for card testing
            if "card_testing" in event_data:
                indicators.append("card_testing_detected")
                evidence["card_testing"] = event_data["card_testing"]
            
            # Check for velocity anomalies
            if "transaction_velocity" in event_data:
                velocity = event_data["transaction_velocity"]
                for threshold_type, threshold_value in self.velocity_thresholds.items():
                    if velocity.get(threshold_type, 0) > threshold_value:
                        indicators.append(f"velocity_anomaly_{threshold_type}")
                        evidence[f"velocity_{threshold_type}"] = velocity.get(threshold_type, 0)
            
            # Check for geographic anomalies
            if "geographic_anomaly" in event_data:
                indicators.append("geographic_anomaly")
                evidence["geographic_anomaly"] = event_data["geographic_anomaly"]
            
            # Check for device fingerprint mismatch
            if "device_fingerprint_mismatch" in event_data:
                indicators.append("device_fingerprint_mismatch")
                evidence["device_fingerprint_mismatch"] = event_data["device_fingerprint_mismatch"]
            
            # Check for transaction pattern anomalies
            if "transaction_pattern_anomaly" in event_data:
                indicators.append("transaction_pattern_anomaly")
                evidence["transaction_pattern_anomaly"] = event_data["transaction_pattern_anomaly"]
            
            # Check for suspicious payment amounts
            if "payment_amount" in event_data:
                amount = event_data["payment_amount"]
                if amount > 10000:  # High value transaction
                    indicators.append("high_value_transaction")
                    evidence["payment_amount"] = amount
            
            # Check for multiple failed payments
            if "failed_payments" in event_data:
                failed_count = event_data["failed_payments"]
                if failed_count > 3:
                    indicators.append("multiple_failed_payments")
                    evidence["failed_payments"] = failed_count
            
            if indicators:
                return DetectionEvent(
                    event_id=f"PF-{int(time.time())}",
                    rule_id="PAYMENT_FRAUD_001",
                    detection_type=DetectionType.PAYMENT_FRAUD,
                    severity=DetectionSeverity.HIGH,
                    confidence=DetectionConfidence.MEDIUM,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip", ""),
                    source_user=event_data.get("source_user", ""),
                    affected_systems=event_data.get("affected_systems", []),
                    indicators=indicators,
                    evidence=evidence,
                    context=event_data
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting payment fraud: {e}")
            return None

class AccountCompromiseDetector:
    """Account compromise detection capabilities"""
    
    def __init__(self):
        self.compromise_indicators = [
            "password_change",
            "email_change",
            "phone_change",
            "unusual_login_location",
            "unusual_login_time",
            "multiple_failed_logins",
            "account_lockout"
        ]
    
    def detect_account_compromise(self, event_data: Dict[str, Any]) -> Optional[DetectionEvent]:
        """Detect account compromise indicators"""
        try:
            indicators = []
            evidence = {}
            
            # Check for unusual login location
            if "login_location" in event_data and "usual_locations" in event_data:
                current_location = event_data["login_location"]
                usual_locations = event_data["usual_locations"]
                if current_location not in usual_locations:
                    indicators.append("unusual_login_location")
                    evidence["login_location"] = current_location
            
            # Check for unusual login time
            if "login_time" in event_data and "usual_login_times" in event_data:
                current_time = event_data["login_time"]
                usual_times = event_data["usual_login_times"]
                if not self._is_usual_time(current_time, usual_times):
                    indicators.append("unusual_login_time")
                    evidence["login_time"] = current_time
            
            # Check for multiple failed logins
            if "failed_logins" in event_data:
                failed_count = event_data["failed_logins"]
                if failed_count > 5:
                    indicators.append("multiple_failed_logins")
                    evidence["failed_logins"] = failed_count
            
            # Check for account lockout
            if "account_locked" in event_data and event_data["account_locked"]:
                indicators.append("account_lockout")
                evidence["account_locked"] = True
            
            # Check for password change
            if "password_changed" in event_data and event_data["password_changed"]:
                indicators.append("password_change")
                evidence["password_changed"] = True
            
            # Check for email change
            if "email_changed" in event_data and event_data["email_changed"]:
                indicators.append("email_change")
                evidence["email_changed"] = True
            
            # Check for phone change
            if "phone_changed" in event_data and event_data["phone_changed"]:
                indicators.append("phone_change")
                evidence["phone_changed"] = True
            
            # Check for suspicious account activity
            if "suspicious_activity" in event_data:
                indicators.append("suspicious_account_activity")
                evidence["suspicious_activity"] = event_data["suspicious_activity"]
            
            if indicators:
                return DetectionEvent(
                    event_id=f"AC-{int(time.time())}",
                    rule_id="ACCOUNT_COMPROMISE_001",
                    detection_type=DetectionType.ACCOUNT_COMPROMISE,
                    severity=DetectionSeverity.MEDIUM,
                    confidence=DetectionConfidence.MEDIUM,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip", ""),
                    source_user=event_data.get("source_user", ""),
                    affected_systems=event_data.get("affected_systems", []),
                    indicators=indicators,
                    evidence=evidence,
                    context=event_data
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting account compromise: {e}")
            return None
    
    def _is_usual_time(self, current_time: str, usual_times: List[str]) -> bool:
        """Check if current time is within usual login times"""
        try:
            current_hour = int(current_time.split(":")[0])
            for time_range in usual_times:
                if "-" in time_range:
                    start, end = map(int, time_range.split("-"))
                    if start <= current_hour <= end:
                        return True
            return False
        except:
            return True

class SystemIntrusionDetector:
    """System intrusion detection capabilities"""
    
    def __init__(self):
        self.intrusion_patterns = [
            "malware_detection",
            "rootkit_detection",
            "backdoor_detection",
            "privilege_escalation",
            "persistence_mechanism"
        ]
        
        self.suspicious_processes = [
            "nc.exe", "netcat", "wget", "curl", "powershell",
            "cmd.exe", "reg.exe", "schtasks.exe", "at.exe"
        ]
    
    def detect_system_intrusion(self, event_data: Dict[str, Any]) -> Optional[DetectionEvent]:
        """Detect system intrusion attempts"""
        try:
            indicators = []
            evidence = {}
            
            # Check for malware detection
            if "malware_detected" in event_data and event_data["malware_detected"]:
                indicators.append("malware_detected")
                evidence["malware_type"] = event_data.get("malware_type", "unknown")
            
            # Check for rootkit detection
            if "rootkit_detected" in event_data and event_data["rootkit_detected"]:
                indicators.append("rootkit_detected")
                evidence["rootkit_type"] = event_data.get("rootkit_type", "unknown")
            
            # Check for backdoor detection
            if "backdoor_detected" in event_data and event_data["backdoor_detected"]:
                indicators.append("backdoor_detected")
                evidence["backdoor_type"] = event_data.get("backdoor_type", "unknown")
            
            # Check for privilege escalation
            if "privilege_escalation" in event_data and event_data["privilege_escalation"]:
                indicators.append("privilege_escalation")
                evidence["privilege_escalation"] = event_data["privilege_escalation"]
            
            # Check for suspicious processes
            if "suspicious_processes" in event_data:
                processes = event_data["suspicious_processes"]
                for process in processes:
                    if process in self.suspicious_processes:
                        indicators.append("suspicious_process_execution")
                        evidence["suspicious_process"] = process
            
            # Check for persistence mechanisms
            if "persistence_mechanism" in event_data:
                indicators.append("persistence_mechanism_detected")
                evidence["persistence_mechanism"] = event_data["persistence_mechanism"]
            
            # Check for unauthorized system changes
            if "unauthorized_changes" in event_data:
                indicators.append("unauthorized_system_changes")
                evidence["unauthorized_changes"] = event_data["unauthorized_changes"]
            
            # Check for network anomalies
            if "network_anomaly" in event_data:
                indicators.append("network_anomaly")
                evidence["network_anomaly"] = event_data["network_anomaly"]
            
            if indicators:
                return DetectionEvent(
                    event_id=f"SI-{int(time.time())}",
                    rule_id="SYSTEM_INTRUSION_001",
                    detection_type=DetectionType.SYSTEM_INTRUSION,
                    severity=DetectionSeverity.CRITICAL,
                    confidence=DetectionConfidence.HIGH,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip", ""),
                    source_user=event_data.get("source_user", ""),
                    affected_systems=event_data.get("affected_systems", []),
                    indicators=indicators,
                    evidence=evidence,
                    context=event_data
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting system intrusion: {e}")
            return None

class DataExfiltrationDetector:
    """Data exfiltration detection capabilities"""
    
    def __init__(self):
        self.exfiltration_patterns = [
            "large_data_transfer",
            "unusual_data_access",
            "data_compression",
            "encrypted_transfer",
            "external_upload"
        ]
    
    def detect_data_exfiltration(self, event_data: Dict[str, Any]) -> Optional[DetectionEvent]:
        """Detect data exfiltration attempts"""
        try:
            indicators = []
            evidence = {}
            
            # Check for large data transfers
            if "data_transfer_size" in event_data:
                transfer_size = event_data["data_transfer_size"]
                if transfer_size > 100 * 1024 * 1024:  # 100MB
                    indicators.append("large_data_transfer")
                    evidence["transfer_size"] = transfer_size
            
            # Check for unusual data access patterns
            if "unusual_data_access" in event_data:
                indicators.append("unusual_data_access")
                evidence["unusual_data_access"] = event_data["unusual_data_access"]
            
            # Check for data compression
            if "data_compression" in event_data and event_data["data_compression"]:
                indicators.append("data_compression")
                evidence["compression_ratio"] = event_data.get("compression_ratio", 0)
            
            # Check for encrypted transfers
            if "encrypted_transfer" in event_data and event_data["encrypted_transfer"]:
                indicators.append("encrypted_transfer")
                evidence["encryption_type"] = event_data.get("encryption_type", "unknown")
            
            # Check for external uploads
            if "external_upload" in event_data and event_data["external_upload"]:
                indicators.append("external_upload")
                evidence["upload_destination"] = event_data.get("upload_destination", "unknown")
            
            # Check for bulk data export
            if "bulk_export" in event_data and event_data["bulk_export"]:
                indicators.append("bulk_data_export")
                evidence["export_volume"] = event_data.get("export_volume", 0)
            
            # Check for unusual file access
            if "unusual_file_access" in event_data:
                indicators.append("unusual_file_access")
                evidence["file_access_pattern"] = event_data["unusual_file_access"]
            
            if indicators:
                return DetectionEvent(
                    event_id=f"DE-{int(time.time())}",
                    rule_id="DATA_EXFILTRATION_001",
                    detection_type=DetectionType.DATA_EXFILTRATION,
                    severity=DetectionSeverity.CRITICAL,
                    confidence=DetectionConfidence.MEDIUM,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip", ""),
                    source_user=event_data.get("source_user", ""),
                    affected_systems=event_data.get("affected_systems", []),
                    affected_data=event_data.get("affected_data", []),
                    indicators=indicators,
                    evidence=evidence,
                    context=event_data
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting data exfiltration: {e}")
            return None

class ServiceDisruptionDetector:
    """Service disruption detection capabilities"""
    
    def __init__(self):
        self.disruption_patterns = [
            "ddos_attack",
            "resource_exhaustion",
            "service_degradation",
            "availability_impact"
        ]
        
        self.thresholds = {
            "request_rate": 1000,  # requests per second
            "error_rate": 0.1,     # 10% error rate
            "response_time": 5.0,  # 5 seconds
            "cpu_usage": 0.9,      # 90% CPU
            "memory_usage": 0.9,   # 90% memory
            "disk_usage": 0.95     # 95% disk
        }
    
    def detect_service_disruption(self, event_data: Dict[str, Any]) -> Optional[DetectionEvent]:
        """Detect service disruption attacks"""
        try:
            indicators = []
            evidence = {}
            
            # Check for DDoS attack
            if "ddos_attack" in event_data and event_data["ddos_attack"]:
                indicators.append("ddos_attack")
                evidence["ddos_type"] = event_data.get("ddos_type", "unknown")
                evidence["attack_volume"] = event_data.get("attack_volume", 0)
            
            # Check for resource exhaustion
            if "resource_exhaustion" in event_data:
                resources = event_data["resource_exhaustion"]
                for resource, usage in resources.items():
                    threshold = self.thresholds.get(resource, 0.8)
                    if usage > threshold:
                        indicators.append(f"{resource}_exhaustion")
                        evidence[f"{resource}_usage"] = usage
            
            # Check for service degradation
            if "service_degradation" in event_data:
                degradation = event_data["service_degradation"]
                if degradation.get("response_time", 0) > self.thresholds["response_time"]:
                    indicators.append("response_time_degradation")
                    evidence["response_time"] = degradation["response_time"]
                
                if degradation.get("error_rate", 0) > self.thresholds["error_rate"]:
                    indicators.append("error_rate_increase")
                    evidence["error_rate"] = degradation["error_rate"]
            
            # Check for availability impact
            if "availability_impact" in event_data:
                impact = event_data["availability_impact"]
                if impact.get("uptime", 1.0) < 0.99:  # Less than 99% uptime
                    indicators.append("availability_impact")
                    evidence["uptime"] = impact["uptime"]
            
            # Check for unusual request patterns
            if "unusual_requests" in event_data:
                indicators.append("unusual_request_patterns")
                evidence["request_patterns"] = event_data["unusual_requests"]
            
            # Check for service unavailability
            if "service_unavailable" in event_data and event_data["service_unavailable"]:
                indicators.append("service_unavailable")
                evidence["downtime_duration"] = event_data.get("downtime_duration", 0)
            
            if indicators:
                return DetectionEvent(
                    event_id=f"SD-{int(time.time())}",
                    rule_id="SERVICE_DISRUPTION_001",
                    detection_type=DetectionType.SERVICE_DISRUPTION,
                    severity=DetectionSeverity.HIGH,
                    confidence=DetectionConfidence.MEDIUM,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip", ""),
                    source_user=event_data.get("source_user", ""),
                    affected_systems=event_data.get("affected_systems", []),
                    indicators=indicators,
                    evidence=evidence,
                    context=event_data
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting service disruption: {e}")
            return None

class ComprehensiveIncidentDetector:
    """Comprehensive incident detection system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.data_breach_detector = DataBreachDetector()
        self.unauthorized_access_detector = UnauthorizedAccessDetector()
        self.payment_fraud_detector = PaymentFraudDetector()
        self.account_compromise_detector = AccountCompromiseDetector()
        self.system_intrusion_detector = SystemIntrusionDetector()
        self.data_exfiltration_detector = DataExfiltrationDetector()
        self.service_disruption_detector = ServiceDisruptionDetector()
        self.detection_history = []
    
    def detect_incidents(self, event_data: Dict[str, Any]) -> List[DetectionEvent]:
        """Detect all types of security incidents"""
        try:
            detections = []
            
            # Data breach detection
            data_breach = self.data_breach_detector.detect_data_breach(event_data)
            if data_breach:
                detections.append(data_breach)
            
            # Unauthorized access detection
            unauthorized_access = self.unauthorized_access_detector.detect_unauthorized_access(event_data)
            if unauthorized_access:
                detections.append(unauthorized_access)
            
            # Payment fraud detection
            payment_fraud = self.payment_fraud_detector.detect_payment_fraud(event_data)
            if payment_fraud:
                detections.append(payment_fraud)
            
            # Account compromise detection
            account_compromise = self.account_compromise_detector.detect_account_compromise(event_data)
            if account_compromise:
                detections.append(account_compromise)
            
            # System intrusion detection
            system_intrusion = self.system_intrusion_detector.detect_system_intrusion(event_data)
            if system_intrusion:
                detections.append(system_intrusion)
            
            # Data exfiltration detection
            data_exfiltration = self.data_exfiltration_detector.detect_data_exfiltration(event_data)
            if data_exfiltration:
                detections.append(data_exfiltration)
            
            # Service disruption detection
            service_disruption = self.service_disruption_detector.detect_service_disruption(event_data)
            if service_disruption:
                detections.append(service_disruption)
            
            # Store detections in history
            for detection in detections:
                self.detection_history.append({
                    "detection": detection,
                    "timestamp": datetime.utcnow(),
                    "event_data": event_data
                })
            
            return detections
        
        except Exception as e:
            logger.error(f"Error detecting incidents: {e}")
            return []
    
    def get_detection_history(self) -> List[Dict[str, Any]]:
        """Get detection history"""
        return self.detection_history
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        try:
            stats = {
                "total_detections": len(self.detection_history),
                "detection_types": {},
                "severity_distribution": {},
                "confidence_distribution": {},
                "recent_detections": []
            }
            
            for record in self.detection_history:
                detection = record["detection"]
                
                # Count by detection type
                detection_type = detection.detection_type.value
                stats["detection_types"][detection_type] = stats["detection_types"].get(detection_type, 0) + 1
                
                # Count by severity
                severity = detection.severity.value
                stats["severity_distribution"][severity] = stats["severity_distribution"].get(severity, 0) + 1
                
                # Count by confidence
                confidence = detection.confidence.value
                stats["confidence_distribution"][confidence] = stats["confidence_distribution"].get(confidence, 0) + 1
            
            # Get recent detections (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_detections = [
                record for record in self.detection_history
                if record["timestamp"] > cutoff_time
            ]
            stats["recent_detections"] = len(recent_detections)
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting detection statistics: {e}")
            return {}

def create_comprehensive_incident_detector(base_url: str = "http://localhost:5000") -> ComprehensiveIncidentDetector:
    """Create comprehensive incident detector"""
    return ComprehensiveIncidentDetector(base_url)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Incident Detection System")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for system")
    parser.add_argument("--event-file", help="Path to security event JSON file")
    parser.add_argument("--detect-all", action="store_true", help="Detect all incident types")
    parser.add_argument("--statistics", action="store_true", help="Show detection statistics")
    
    args = parser.parse_args()
    
    # Create incident detector
    detector = create_comprehensive_incident_detector(args.base_url)
    
    if args.event_file:
        # Process event file
        with open(args.event_file, 'r') as f:
            event_data = json.load(f)
        
        detections = detector.detect_incidents(event_data)
        
        if detections:
            print(f"Detected {len(detections)} security incidents:")
            for detection in detections:
                print(f"  {detection.event_id}: {detection.detection_type.value} ({detection.severity.value})")
                print(f"    Indicators: {', '.join(detection.indicators)}")
                print(f"    Confidence: {detection.confidence.value}")
                print()
        else:
            print("No security incidents detected")
    
    elif args.statistics:
        # Show detection statistics
        stats = detector.get_detection_statistics()
        print("Detection Statistics:")
        print(f"Total Detections: {stats.get('total_detections', 0)}")
        print(f"Recent Detections (24h): {stats.get('recent_detections', 0)}")
        
        print("\nDetection Types:")
        for detection_type, count in stats.get('detection_types', {}).items():
            print(f"  {detection_type}: {count}")
        
        print("\nSeverity Distribution:")
        for severity, count in stats.get('severity_distribution', {}).items():
            print(f"  {severity}: {count}")
    
    else:
        print("Comprehensive Incident Detection System")
        print("Use --help for usage information") 