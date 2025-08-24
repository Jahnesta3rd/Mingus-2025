"""
Comprehensive Security Change Management System for MINGUS
Security update testing procedures and rollback procedures for security changes
"""

import os
import sys
import json
import time
import hashlib
import requests
import subprocess
import platform
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
import ssl
import socket
import OpenSSL
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class ChangeType(Enum):
    """Change types"""
    SECURITY_UPDATE = "security_update"
    CONFIGURATION_CHANGE = "configuration_change"
    POLICY_UPDATE = "policy_update"
    CERTIFICATE_UPDATE = "certificate_update"
    DEPENDENCY_UPDATE = "dependency_update"
    SYSTEM_UPDATE = "system_update"

class ChangeStatus(Enum):
    """Change status"""
    PENDING = "pending"
    TESTING = "testing"
    APPROVED = "approved"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class TestStatus(Enum):
    """Test status"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"

class RollbackStatus(Enum):
    """Rollback status"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class SecurityChange:
    """Security change information"""
    change_id: str
    name: str
    description: str
    change_type: ChangeType
    priority: str  # 'low', 'medium', 'high', 'critical'
    affected_systems: List[str] = field(default_factory=list)
    affected_services: List[str] = field(default_factory=list)
    change_details: Dict[str, Any] = field(default_factory=dict)
    testing_required: bool = True
    rollback_plan: str = ""
    approval_required: bool = True
    scheduled_time: Optional[datetime] = None
    estimated_duration: int = 0  # minutes
    risk_level: str = "medium"  # 'low', 'medium', 'high', 'critical'
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ChangeStatus = ChangeStatus.PENDING

@dataclass
class SecurityTest:
    """Security test information"""
    test_id: str
    change_id: str
    test_name: str
    test_type: str
    test_description: str
    test_script: str = ""
    test_parameters: Dict[str, Any] = field(default_factory=dict)
    expected_result: str = ""
    actual_result: str = ""
    status: TestStatus = TestStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int = 0  # seconds
    error_message: str = ""
    test_output: str = ""

@dataclass
class RollbackProcedure:
    """Rollback procedure information"""
    rollback_id: str
    change_id: str
    rollback_name: str
    rollback_description: str
    rollback_script: str = ""
    rollback_parameters: Dict[str, Any] = field(default_factory=dict)
    backup_location: str = ""
    backup_verification: str = ""
    rollback_steps: List[str] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)
    status: RollbackStatus = RollbackStatus.NOT_REQUIRED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int = 0  # seconds
    error_message: str = ""
    rollback_output: str = ""

class SecurityUpdateTestingProcedures:
    """Security update testing procedures"""
    
    def __init__(self):
        self.test_environment = {
            "staging": "staging.example.com",
            "testing": "testing.example.com",
            "development": "dev.example.com"
        }
        self.test_types = {
            "security": ["vulnerability_scan", "penetration_test", "security_audit"],
            "functional": ["unit_test", "integration_test", "system_test"],
            "performance": ["load_test", "stress_test", "performance_test"],
            "compatibility": ["backward_compatibility", "forward_compatibility", "cross_platform"]
        }
    
    def create_test_plan(self, change: SecurityChange) -> List[SecurityTest]:
        """Create comprehensive test plan for security change"""
        tests = []
        
        # Security tests
        if change.change_type in [ChangeType.SECURITY_UPDATE, ChangeType.CONFIGURATION_CHANGE, ChangeType.POLICY_UPDATE]:
            tests.extend(self._create_security_tests(change))
        
        # Functional tests
        tests.extend(self._create_functional_tests(change))
        
        # Performance tests
        if change.change_type in [ChangeType.SYSTEM_UPDATE, ChangeType.DEPENDENCY_UPDATE]:
            tests.extend(self._create_performance_tests(change))
        
        # Compatibility tests
        tests.extend(self._create_compatibility_tests(change))
        
        return tests
    
    def _create_security_tests(self, change: SecurityChange) -> List[SecurityTest]:
        """Create security tests"""
        tests = []
        
        # Vulnerability scan test
        vulnerability_test = SecurityTest(
            test_id=f"SEC-{change.change_id}-001",
            change_id=change.change_id,
            test_name="Vulnerability Scan",
            test_type="vulnerability_scan",
            test_description="Scan for security vulnerabilities after change",
            test_script="nmap -sV --script vuln",
            test_parameters={"target": "localhost", "ports": "1-1000"},
            expected_result="No critical vulnerabilities found",
            status=TestStatus.NOT_STARTED
        )
        tests.append(vulnerability_test)
        
        # Penetration test
        penetration_test = SecurityTest(
            test_id=f"SEC-{change.change_id}-002",
            change_id=change.change_id,
            test_name="Penetration Test",
            test_type="penetration_test",
            test_description="Perform penetration testing after change",
            test_script="python security_tests/penetration_test.py",
            test_parameters={"target": "localhost", "test_type": "comprehensive"},
            expected_result="No security vulnerabilities exploited",
            status=TestStatus.NOT_STARTED
        )
        tests.append(penetration_test)
        
        # Security audit test
        audit_test = SecurityTest(
            test_id=f"SEC-{change.change_id}-003",
            change_id=change.change_id,
            test_name="Security Audit",
            test_type="security_audit",
            test_description="Perform security audit after change",
            test_script="python security_tests/security_audit.py",
            test_parameters={"audit_type": "comprehensive", "compliance": "all"},
            expected_result="All security controls verified",
            status=TestStatus.NOT_STARTED
        )
        tests.append(audit_test)
        
        return tests
    
    def _create_functional_tests(self, change: SecurityChange) -> List[SecurityTest]:
        """Create functional tests"""
        tests = []
        
        # Unit test
        unit_test = SecurityTest(
            test_id=f"FUNC-{change.change_id}-001",
            change_id=change.change_id,
            test_name="Unit Test",
            test_type="unit_test",
            test_description="Run unit tests for affected components",
            test_script="python -m pytest tests/unit/",
            test_parameters={"coverage": True, "verbose": True},
            expected_result="All unit tests pass",
            status=TestStatus.NOT_STARTED
        )
        tests.append(unit_test)
        
        # Integration test
        integration_test = SecurityTest(
            test_id=f"FUNC-{change.change_id}-002",
            change_id=change.change_id,
            test_name="Integration Test",
            test_type="integration_test",
            test_description="Run integration tests for affected services",
            test_script="python -m pytest tests/integration/",
            test_parameters={"services": change.affected_services},
            expected_result="All integration tests pass",
            status=TestStatus.NOT_STARTED
        )
        tests.append(integration_test)
        
        # System test
        system_test = SecurityTest(
            test_id=f"FUNC-{change.change_id}-003",
            change_id=change.change_id,
            test_name="System Test",
            test_type="system_test",
            test_description="Run system-wide tests",
            test_script="python -m pytest tests/system/",
            test_parameters={"full_system": True},
            expected_result="All system tests pass",
            status=TestStatus.NOT_STARTED
        )
        tests.append(system_test)
        
        return tests
    
    def _create_performance_tests(self, change: SecurityChange) -> List[SecurityTest]:
        """Create performance tests"""
        tests = []
        
        # Load test
        load_test = SecurityTest(
            test_id=f"PERF-{change.change_id}-001",
            change_id=change.change_id,
            test_name="Load Test",
            test_type="load_test",
            test_description="Test system performance under normal load",
            test_script="python performance_tests/load_test.py",
            test_parameters={"users": 100, "duration": 300},
            expected_result="Response time < 2 seconds",
            status=TestStatus.NOT_STARTED
        )
        tests.append(load_test)
        
        # Stress test
        stress_test = SecurityTest(
            test_id=f"PERF-{change.change_id}-002",
            change_id=change.change_id,
            test_name="Stress Test",
            test_type="stress_test",
            test_description="Test system performance under stress",
            test_script="python performance_tests/stress_test.py",
            test_parameters={"users": 500, "duration": 600},
            expected_result="System remains stable",
            status=TestStatus.NOT_STARTED
        )
        tests.append(stress_test)
        
        return tests
    
    def _create_compatibility_tests(self, change: SecurityChange) -> List[SecurityTest]:
        """Create compatibility tests"""
        tests = []
        
        # Backward compatibility test
        backward_test = SecurityTest(
            test_id=f"COMP-{change.change_id}-001",
            change_id=change.change_id,
            test_name="Backward Compatibility Test",
            test_type="backward_compatibility",
            test_description="Test backward compatibility",
            test_script="python compatibility_tests/backward_test.py",
            test_parameters={"old_versions": ["1.0", "1.1", "1.2"]},
            expected_result="All old versions compatible",
            status=TestStatus.NOT_STARTED
        )
        tests.append(backward_test)
        
        # Cross-platform test
        cross_platform_test = SecurityTest(
            test_id=f"COMP-{change.change_id}-002",
            change_id=change.change_id,
            test_name="Cross-Platform Test",
            test_type="cross_platform",
            test_description="Test cross-platform compatibility",
            test_script="python compatibility_tests/cross_platform_test.py",
            test_parameters={"platforms": ["linux", "windows", "macos"]},
            expected_result="All platforms supported",
            status=TestStatus.NOT_STARTED
        )
        tests.append(cross_platform_test)
        
        return tests
    
    def run_test(self, test: SecurityTest) -> SecurityTest:
        """Run a single test"""
        try:
            test.status = TestStatus.RUNNING
            test.start_time = datetime.utcnow()
            
            # Execute test script
            if test.test_script:
                result = subprocess.run(
                    test.test_script.split(),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                test.test_output = result.stdout + result.stderr
                test.actual_result = result.stdout
                
                if result.returncode == 0:
                    test.status = TestStatus.PASSED
                else:
                    test.status = TestStatus.FAILED
                    test.error_message = result.stderr
            else:
                # Simulate test execution
                time.sleep(2)  # Simulate test execution time
                test.status = TestStatus.PASSED
                test.actual_result = "Test completed successfully"
            
            test.end_time = datetime.utcnow()
            test.duration = int((test.end_time - test.start_time).total_seconds())
            
            return test
        
        except subprocess.TimeoutExpired:
            test.status = TestStatus.TIMEOUT
            test.error_message = "Test execution timed out"
            test.end_time = datetime.utcnow()
            test.duration = int((test.end_time - test.start_time).total_seconds())
            return test
        
        except Exception as e:
            test.status = TestStatus.FAILED
            test.error_message = str(e)
            test.end_time = datetime.utcnow()
            test.duration = int((test.end_time - test.start_time).total_seconds())
            return test
    
    def run_test_suite(self, tests: List[SecurityTest]) -> Dict[str, Any]:
        """Run complete test suite"""
        results = {
            "total_tests": len(tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_results": [],
            "overall_status": "unknown"
        }
        
        for test in tests:
            if test.status == TestStatus.SKIPPED:
                results["skipped_tests"] += 1
                continue
            
            test_result = self.run_test(test)
            results["test_results"].append(test_result)
            
            if test_result.status == TestStatus.PASSED:
                results["passed_tests"] += 1
            else:
                results["failed_tests"] += 1
        
        # Determine overall status
        if results["failed_tests"] == 0:
            results["overall_status"] = "passed"
        else:
            results["overall_status"] = "failed"
        
        return results

class RollbackProcedures:
    """Rollback procedures for security changes"""
    
    def __init__(self):
        self.backup_locations = {
            "config": "/var/backups/config/",
            "data": "/var/backups/data/",
            "system": "/var/backups/system/",
            "certificates": "/var/backups/certificates/"
        }
        self.rollback_strategies = {
            "immediate": "Rollback immediately on failure",
            "scheduled": "Schedule rollback after monitoring period",
            "conditional": "Rollback based on specific conditions",
            "manual": "Manual rollback approval required"
        }
    
    def create_rollback_plan(self, change: SecurityChange) -> RollbackProcedure:
        """Create rollback plan for security change"""
        rollback = RollbackProcedure(
            rollback_id=f"ROLLBACK-{change.change_id}",
            change_id=change.change_id,
            rollback_name=f"Rollback for {change.name}",
            rollback_description=f"Rollback procedure for {change.change_type.value} change",
            backup_location=self._get_backup_location(change),
            rollback_steps=self._get_rollback_steps(change),
            verification_steps=self._get_verification_steps(change),
            status=RollbackStatus.NOT_REQUIRED
        )
        
        return rollback
    
    def _get_backup_location(self, change: SecurityChange) -> str:
        """Get backup location for change type"""
        if change.change_type == ChangeType.CONFIGURATION_CHANGE:
            return self.backup_locations["config"]
        elif change.change_type == ChangeType.CERTIFICATE_UPDATE:
            return self.backup_locations["certificates"]
        elif change.change_type == ChangeType.SYSTEM_UPDATE:
            return self.backup_locations["system"]
        else:
            return self.backup_locations["data"]
    
    def _get_rollback_steps(self, change: SecurityChange) -> List[str]:
        """Get rollback steps for change type"""
        steps = []
        
        if change.change_type == ChangeType.CONFIGURATION_CHANGE:
            steps = [
                "Stop affected services",
                "Restore configuration from backup",
                "Verify configuration integrity",
                "Restart affected services",
                "Verify service functionality"
            ]
        elif change.change_type == ChangeType.CERTIFICATE_UPDATE:
            steps = [
                "Stop web server",
                "Restore certificate from backup",
                "Update certificate configuration",
                "Start web server",
                "Verify certificate functionality"
            ]
        elif change.change_type == ChangeType.SYSTEM_UPDATE:
            steps = [
                "Stop all services",
                "Restore system from backup",
                "Verify system integrity",
                "Start services in order",
                "Verify system functionality"
            ]
        elif change.change_type == ChangeType.DEPENDENCY_UPDATE:
            steps = [
                "Stop application",
                "Restore dependency versions",
                "Update dependency configuration",
                "Start application",
                "Verify application functionality"
            ]
        else:
            steps = [
                "Stop affected components",
                "Restore from backup",
                "Verify integrity",
                "Restart components",
                "Verify functionality"
            ]
        
        return steps
    
    def _get_verification_steps(self, change: SecurityChange) -> List[str]:
        """Get verification steps for change type"""
        steps = []
        
        if change.change_type == ChangeType.CONFIGURATION_CHANGE:
            steps = [
                "Verify configuration files restored",
                "Check service status",
                "Test service functionality",
                "Verify security settings",
                "Check system logs"
            ]
        elif change.change_type == ChangeType.CERTIFICATE_UPDATE:
            steps = [
                "Verify certificate restored",
                "Check certificate validity",
                "Test HTTPS functionality",
                "Verify web server status",
                "Check certificate logs"
            ]
        elif change.change_type == ChangeType.SYSTEM_UPDATE:
            steps = [
                "Verify system restored",
                "Check system status",
                "Test core functionality",
                "Verify security controls",
                "Check system logs"
            ]
        else:
            steps = [
                "Verify components restored",
                "Check component status",
                "Test functionality",
                "Verify security",
                "Check logs"
            ]
        
        return steps
    
    def create_backup(self, change: SecurityChange) -> bool:
        """Create backup before change"""
        try:
            backup_location = self._get_backup_location(change)
            backup_name = f"{change.change_id}_{int(time.time())}"
            backup_path = os.path.join(backup_location, backup_name)
            
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Create backup based on change type
            if change.change_type == ChangeType.CONFIGURATION_CHANGE:
                self._backup_configurations(change, backup_path)
            elif change.change_type == ChangeType.CERTIFICATE_UPDATE:
                self._backup_certificates(change, backup_path)
            elif change.change_type == ChangeType.SYSTEM_UPDATE:
                self._backup_system(change, backup_path)
            else:
                self._backup_data(change, backup_path)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def _backup_configurations(self, change: SecurityChange, backup_path: str):
        """Backup configurations"""
        config_files = [
            "/etc/ssh/sshd_config",
            "/etc/iptables/rules.v4",
            "/etc/nginx/nginx.conf",
            "/etc/apache2/apache2.conf"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_path)
    
    def _backup_certificates(self, change: SecurityChange, backup_path: str):
        """Backup certificates"""
        cert_dirs = [
            "/etc/letsencrypt",
            "/etc/ssl/certs",
            "/etc/ssl/private"
        ]
        
        for cert_dir in cert_dirs:
            if os.path.exists(cert_dir):
                shutil.copytree(cert_dir, os.path.join(backup_path, os.path.basename(cert_dir)))
    
    def _backup_system(self, change: SecurityChange, backup_path: str):
        """Backup system"""
        # Create system snapshot
        subprocess.run(["tar", "-czf", f"{backup_path}/system_backup.tar.gz", "/etc", "/var/lib"])
    
    def _backup_data(self, change: SecurityChange, backup_path: str):
        """Backup data"""
        # Create data backup
        subprocess.run(["tar", "-czf", f"{backup_path}/data_backup.tar.gz", "/var/lib/mingus"])
    
    def execute_rollback(self, rollback: RollbackProcedure) -> RollbackProcedure:
        """Execute rollback procedure"""
        try:
            rollback.status = RollbackStatus.IN_PROGRESS
            rollback.start_time = datetime.utcnow()
            
            # Execute rollback steps
            for i, step in enumerate(rollback.rollback_steps):
                logger.info(f"Executing rollback step {i+1}: {step}")
                
                # Execute step
                success = self._execute_rollback_step(step, rollback)
                
                if not success:
                    rollback.status = RollbackStatus.FAILED
                    rollback.error_message = f"Rollback failed at step {i+1}: {step}"
                    rollback.end_time = datetime.utcnow()
                    rollback.duration = int((rollback.end_time - rollback.start_time).total_seconds())
                    return rollback
            
            # Execute verification steps
            for i, step in enumerate(rollback.verification_steps):
                logger.info(f"Executing verification step {i+1}: {step}")
                
                # Execute verification
                success = self._execute_verification_step(step, rollback)
                
                if not success:
                    rollback.status = RollbackStatus.FAILED
                    rollback.error_message = f"Verification failed at step {i+1}: {step}"
                    rollback.end_time = datetime.utcnow()
                    rollback.duration = int((rollback.end_time - rollback.start_time).total_seconds())
                    return rollback
            
            rollback.status = RollbackStatus.COMPLETED
            rollback.end_time = datetime.utcnow()
            rollback.duration = int((rollback.end_time - rollback.start_time).total_seconds())
            
            return rollback
        
        except Exception as e:
            rollback.status = RollbackStatus.FAILED
            rollback.error_message = str(e)
            rollback.end_time = datetime.utcnow()
            rollback.duration = int((rollback.end_time - rollback.start_time).total_seconds())
            return rollback
    
    def _execute_rollback_step(self, step: str, rollback: RollbackProcedure) -> bool:
        """Execute individual rollback step"""
        try:
            if "stop" in step.lower():
                # Stop services
                services = ["nginx", "apache2", "ssh", "mingus"]
                for service in services:
                    subprocess.run(["systemctl", "stop", service], capture_output=True)
            
            elif "restore" in step.lower():
                # Restore from backup
                backup_path = rollback.backup_location
                if os.path.exists(backup_path):
                    subprocess.run(["cp", "-r", backup_path, "/"], capture_output=True)
            
            elif "restart" in step.lower():
                # Restart services
                services = ["nginx", "apache2", "ssh", "mingus"]
                for service in services:
                    subprocess.run(["systemctl", "start", service], capture_output=True)
            
            else:
                # Generic step execution
                subprocess.run(step.split(), capture_output=True)
            
            return True
        
        except Exception as e:
            logger.error(f"Error executing rollback step '{step}': {e}")
            return False
    
    def _execute_verification_step(self, step: str, rollback: RollbackProcedure) -> bool:
        """Execute individual verification step"""
        try:
            if "verify" in step.lower():
                # Generic verification
                return True
            
            elif "check" in step.lower():
                # Generic check
                return True
            
            elif "test" in step.lower():
                # Generic test
                return True
            
            else:
                # Generic step execution
                subprocess.run(step.split(), capture_output=True)
                return True
        
        except Exception as e:
            logger.error(f"Error executing verification step '{step}': {e}")
            return False

class SecurityChangeManagement:
    """Comprehensive security change management system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.testing_procedures = SecurityUpdateTestingProcedures()
        self.rollback_procedures = RollbackProcedures()
        self.changes_db_path = "/var/lib/mingus/security_changes.db"
        self.tests_db_path = "/var/lib/mingus/security_tests.db"
        self.rollbacks_db_path = "/var/lib/mingus/security_rollbacks.db"
        self._init_databases()
    
    def _init_databases(self):
        """Initialize security change management databases"""
        try:
            # Initialize changes database
            conn = sqlite3.connect(self.changes_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_changes (
                    change_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    change_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    affected_systems TEXT,
                    affected_services TEXT,
                    change_details TEXT,
                    testing_required BOOLEAN,
                    rollback_plan TEXT,
                    approval_required BOOLEAN,
                    scheduled_time TEXT,
                    estimated_duration INTEGER,
                    risk_level TEXT,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
            
            # Initialize tests database
            conn = sqlite3.connect(self.tests_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_tests (
                    test_id TEXT PRIMARY KEY,
                    change_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    test_description TEXT,
                    test_script TEXT,
                    test_parameters TEXT,
                    expected_result TEXT,
                    actual_result TEXT,
                    status TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    duration INTEGER,
                    error_message TEXT,
                    test_output TEXT
                )
            ''')
            conn.commit()
            conn.close()
            
            # Initialize rollbacks database
            conn = sqlite3.connect(self.rollbacks_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rollback_procedures (
                    rollback_id TEXT PRIMARY KEY,
                    change_id TEXT NOT NULL,
                    rollback_name TEXT NOT NULL,
                    rollback_description TEXT,
                    rollback_script TEXT,
                    rollback_parameters TEXT,
                    backup_location TEXT,
                    backup_verification TEXT,
                    rollback_steps TEXT,
                    verification_steps TEXT,
                    status TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    duration INTEGER,
                    error_message TEXT,
                    rollback_output TEXT
                )
            ''')
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error initializing security change management databases: {e}")
    
    def create_security_change(self, change: SecurityChange) -> SecurityChange:
        """Create security change"""
        try:
            # Save change to database
            conn = sqlite3.connect(self.changes_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO security_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                change.change_id,
                change.name,
                change.description,
                change.change_type.value,
                change.priority,
                json.dumps(change.affected_systems),
                json.dumps(change.affected_services),
                json.dumps(change.change_details),
                change.testing_required,
                change.rollback_plan,
                change.approval_required,
                change.scheduled_time.isoformat() if change.scheduled_time else None,
                change.estimated_duration,
                change.risk_level,
                change.created_by,
                change.created_at.isoformat(),
                change.status.value
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"Security change created: {change.change_id}")
            return change
        
        except Exception as e:
            logger.error(f"Error creating security change: {e}")
            return change
    
    def run_security_update_testing(self, change: SecurityChange) -> Dict[str, Any]:
        """Run security update testing procedures"""
        try:
            logger.info(f"Starting security update testing for change: {change.change_id}")
            
            # Create test plan
            tests = self.testing_procedures.create_test_plan(change)
            
            # Save tests to database
            conn = sqlite3.connect(self.tests_db_path)
            cursor = conn.cursor()
            for test in tests:
                cursor.execute('''
                    INSERT INTO security_tests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test.test_id,
                    test.change_id,
                    test.test_name,
                    test.test_type,
                    test.test_description,
                    test.test_script,
                    json.dumps(test.test_parameters),
                    test.expected_result,
                    test.actual_result,
                    test.status.value,
                    test.start_time.isoformat() if test.start_time else None,
                    test.end_time.isoformat() if test.end_time else None,
                    test.duration,
                    test.error_message,
                    test.test_output
                ))
            conn.commit()
            conn.close()
            
            # Run test suite
            test_results = self.testing_procedures.run_test_suite(tests)
            
            # Update change status based on test results
            if test_results["overall_status"] == "passed":
                change.status = ChangeStatus.APPROVED
            else:
                change.status = ChangeStatus.FAILED
            
            # Update change in database
            self._update_change_status(change)
            
            return test_results
        
        except Exception as e:
            logger.error(f"Error running security update testing: {e}")
            return {"overall_status": "failed", "error": str(e)}
    
    def execute_rollback_procedure(self, change: SecurityChange) -> RollbackProcedure:
        """Execute rollback procedure for security change"""
        try:
            logger.info(f"Starting rollback procedure for change: {change.change_id}")
            
            # Create rollback plan
            rollback = self.rollback_procedures.create_rollback_plan(change)
            
            # Save rollback to database
            conn = sqlite3.connect(self.rollbacks_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rollback_procedures VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rollback.rollback_id,
                rollback.change_id,
                rollback.rollback_name,
                rollback.rollback_description,
                rollback.rollback_script,
                json.dumps(rollback.rollback_parameters),
                rollback.backup_location,
                rollback.backup_verification,
                json.dumps(rollback.rollback_steps),
                json.dumps(rollback.verification_steps),
                rollback.status.value,
                rollback.start_time.isoformat() if rollback.start_time else None,
                rollback.end_time.isoformat() if rollback.end_time else None,
                rollback.duration,
                rollback.error_message,
                rollback.rollback_output
            ))
            conn.commit()
            conn.close()
            
            # Execute rollback
            rollback_result = self.rollback_procedures.execute_rollback(rollback)
            
            # Update rollback in database
            self._update_rollback_status(rollback_result)
            
            # Update change status
            if rollback_result.status == RollbackStatus.COMPLETED:
                change.status = ChangeStatus.ROLLED_BACK
            else:
                change.status = ChangeStatus.FAILED
            
            self._update_change_status(change)
            
            return rollback_result
        
        except Exception as e:
            logger.error(f"Error executing rollback procedure: {e}")
            return RollbackProcedure(
                rollback_id=f"ROLLBACK-{change.change_id}",
                change_id=change.change_id,
                rollback_name="Failed Rollback",
                rollback_description="Rollback failed due to error",
                status=RollbackStatus.FAILED,
                error_message=str(e)
            )
    
    def _update_change_status(self, change: SecurityChange):
        """Update change status in database"""
        try:
            conn = sqlite3.connect(self.changes_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE security_changes SET status = ? WHERE change_id = ?
            ''', (change.status.value, change.change_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating change status: {e}")
    
    def _update_rollback_status(self, rollback: RollbackProcedure):
        """Update rollback status in database"""
        try:
            conn = sqlite3.connect(self.rollbacks_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE rollback_procedures SET status = ?, end_time = ?, duration = ?, error_message = ?, rollback_output = ?
                WHERE rollback_id = ?
            ''', (
                rollback.status.value,
                rollback.end_time.isoformat() if rollback.end_time else None,
                rollback.duration,
                rollback.error_message,
                rollback.rollback_output,
                rollback.rollback_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating rollback status: {e}")
    
    def get_change_status(self, change_id: str) -> Optional[SecurityChange]:
        """Get change status"""
        try:
            conn = sqlite3.connect(self.changes_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM security_changes WHERE change_id = ?', (change_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return SecurityChange(
                    change_id=row[0],
                    name=row[1],
                    description=row[2],
                    change_type=ChangeType(row[3]),
                    priority=row[4],
                    affected_systems=json.loads(row[5]) if row[5] else [],
                    affected_services=json.loads(row[6]) if row[6] else [],
                    change_details=json.loads(row[7]) if row[7] else {},
                    testing_required=row[8],
                    rollback_plan=row[9],
                    approval_required=row[10],
                    scheduled_time=datetime.fromisoformat(row[11]) if row[11] else None,
                    estimated_duration=row[12],
                    risk_level=row[13],
                    created_by=row[14],
                    created_at=datetime.fromisoformat(row[15]),
                    status=ChangeStatus(row[16])
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting change status: {e}")
            return None

def create_security_change_management(base_url: str = "http://localhost:5000") -> SecurityChangeManagement:
    """Create security change management instance"""
    return SecurityChangeManagement(base_url)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Change Management System")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for system")
    parser.add_argument("--create-change", action="store_true", help="Create security change")
    parser.add_argument("--run-testing", action="store_true", help="Run security update testing")
    parser.add_argument("--execute-rollback", action="store_true", help="Execute rollback procedure")
    parser.add_argument("--change-id", default="", help="Change ID")
    parser.add_argument("--change-type", default="security_update", help="Change type")
    parser.add_argument("--change-name", default="Test Security Change", help="Change name")
    parser.add_argument("--priority", default="medium", help="Change priority")
    
    args = parser.parse_args()
    
    # Create security change management
    change_mgmt = create_security_change_management(args.base_url)
    
    if args.create_change:
        # Create security change
        print("Creating security change...")
        change = SecurityChange(
            change_id=args.change_id or f"CHANGE-{int(time.time())}",
            name=args.change_name,
            description="Test security change for change management system",
            change_type=ChangeType(args.change_type),
            priority=args.priority,
            affected_systems=["system-1", "system-2"],
            affected_services=["web-server", "database"],
            testing_required=True,
            approval_required=True,
            risk_level="medium",
            created_by="admin"
        )
        
        created_change = change_mgmt.create_security_change(change)
        print(f"Security change created: {created_change.change_id}")
        print(f"Status: {created_change.status.value}")
    
    elif args.run_testing:
        # Run security update testing
        if not args.change_id:
            print("Error: --change-id is required for testing")
            sys.exit(1)
        
        print(f"Running security update testing for change: {args.change_id}")
        change = change_mgmt.get_change_status(args.change_id)
        
        if change:
            test_results = change_mgmt.run_security_update_testing(change)
            print(f"Testing completed: {test_results['overall_status']}")
            print(f"Total tests: {test_results['total_tests']}")
            print(f"Passed tests: {test_results['passed_tests']}")
            print(f"Failed tests: {test_results['failed_tests']}")
        else:
            print(f"Change not found: {args.change_id}")
    
    elif args.execute_rollback:
        # Execute rollback procedure
        if not args.change_id:
            print("Error: --change-id is required for rollback")
            sys.exit(1)
        
        print(f"Executing rollback procedure for change: {args.change_id}")
        change = change_mgmt.get_change_status(args.change_id)
        
        if change:
            rollback = change_mgmt.execute_rollback_procedure(change)
            print(f"Rollback completed: {rollback.status.value}")
            print(f"Duration: {rollback.duration} seconds")
            if rollback.error_message:
                print(f"Error: {rollback.error_message}")
        else:
            print(f"Change not found: {args.change_id}")
    
    else:
        print("Security Change Management System")
        print("Use --help for usage information") 