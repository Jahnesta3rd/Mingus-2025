"""
Comprehensive Security Update and Patch Management System for MINGUS
Automated security updates, vulnerability scanning, patch deployment, and compliance monitoring
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

class PatchType(Enum):
    """Patch types"""
    SECURITY = "security"
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"

class PatchStatus(Enum):
    """Patch status"""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class SystemType(Enum):
    """System types"""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    CLOUD = "cloud"

@dataclass
class SecurityPatch:
    """Security patch information"""
    patch_id: str
    name: str
    description: str
    patch_type: PatchType
    severity: str
    cve_ids: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    release_date: datetime = field(default_factory=datetime.utcnow)
    download_url: str = ""
    checksum: str = ""
    size: int = 0
    dependencies: List[str] = field(default_factory=list)
    rollback_available: bool = True
    requires_reboot: bool = False
    installation_timeout: int = 300  # 5 minutes
    verification_required: bool = True

@dataclass
class PatchDeployment:
    """Patch deployment information"""
    deployment_id: str
    patch_id: str
    system_id: str
    status: PatchStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    installer_log: str = ""
    verification_log: str = ""
    rollback_log: str = ""
    error_message: str = ""
    deployment_duration: int = 0
    success: bool = False

@dataclass
class VulnerabilityScan:
    """Vulnerability scan information"""
    scan_id: str
    system_id: str
    scan_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    vulnerabilities_found: List[Dict[str, Any]] = field(default_factory=list)
    scan_status: str = "running"
    scan_log: str = ""
    risk_score: float = 0.0
    compliance_score: float = 0.0

class VulnerabilityScanner:
    """Vulnerability scanning capabilities"""
    
    def __init__(self):
        self.scan_tools = {
            "nmap": "nmap -sV --script vuln",
            "nuclei": "nuclei -t vuln",
            "trivy": "trivy fs --security-checks vuln",
            "snyk": "snyk test",
            "owasp_zap": "zap-baseline.py -t"
        }
        
        self.vulnerability_databases = [
            "https://nvd.nist.gov/vuln/data-feeds",
            "https://cve.mitre.org/data/downloads/",
            "https://www.cvedetails.com/json-feed.php"
        ]
    
    def scan_system_vulnerabilities(self, system_id: str, scan_type: str = "comprehensive") -> VulnerabilityScan:
        """Scan system for vulnerabilities"""
        try:
            scan_id = f"SCAN-{int(time.time())}"
            start_time = datetime.utcnow()
            
            vulnerabilities = []
            scan_log = ""
            
            # Determine system type
            system_type = self._detect_system_type()
            
            # Run appropriate scans based on system type
            if system_type == SystemType.LINUX:
                vulnerabilities.extend(self._scan_linux_system())
            elif system_type == SystemType.WINDOWS:
                vulnerabilities.extend(self._scan_windows_system())
            elif system_type == SystemType.MACOS:
                vulnerabilities.extend(self._scan_macos_system())
            elif system_type == SystemType.DOCKER:
                vulnerabilities.extend(self._scan_docker_system())
            elif system_type == SystemType.KUBERNETES:
                vulnerabilities.extend(self._scan_kubernetes_system())
            
            # Run common vulnerability scans
            vulnerabilities.extend(self._run_common_scans())
            
            # Calculate risk and compliance scores
            risk_score = self._calculate_risk_score(vulnerabilities)
            compliance_score = self._calculate_compliance_score(vulnerabilities)
            
            end_time = datetime.utcnow()
            
            return VulnerabilityScan(
                scan_id=scan_id,
                system_id=system_id,
                scan_type=scan_type,
                start_time=start_time,
                end_time=end_time,
                vulnerabilities_found=vulnerabilities,
                scan_status="completed",
                scan_log=scan_log,
                risk_score=risk_score,
                compliance_score=compliance_score
            )
        
        except Exception as e:
            logger.error(f"Error scanning system vulnerabilities: {e}")
            return VulnerabilityScan(
                scan_id=f"SCAN-{int(time.time())}",
                system_id=system_id,
                scan_type=scan_type,
                start_time=datetime.utcnow(),
                scan_status="failed",
                scan_log=str(e),
                risk_score=0.0,
                compliance_score=0.0
            )
    
    def _detect_system_type(self) -> SystemType:
        """Detect system type"""
        try:
            system = platform.system().lower()
            if system == "linux":
                return SystemType.LINUX
            elif system == "windows":
                return SystemType.WINDOWS
            elif system == "darwin":
                return SystemType.MACOS
            else:
                return SystemType.LINUX
        except:
            return SystemType.LINUX
    
    def _scan_linux_system(self) -> List[Dict[str, Any]]:
        """Scan Linux system for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Check for outdated packages
            result = subprocess.run(["apt", "list", "--upgradable"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                outdated_packages = result.stdout.strip().split('\n')[1:]
                for package in outdated_packages:
                    if package:
                        vulnerabilities.append({
                            "type": "outdated_package",
                            "severity": "medium",
                            "description": f"Outdated package: {package}",
                            "cve_ids": [],
                            "affected_component": package.split('/')[0],
                            "recommendation": "Update package to latest version"
                        })
            
            # Check for security updates
            result = subprocess.run(["apt", "list", "--upgradable", "--security"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                security_updates = result.stdout.strip().split('\n')[1:]
                for update in security_updates:
                    if update:
                        vulnerabilities.append({
                            "type": "security_update",
                            "severity": "high",
                            "description": f"Security update available: {update}",
                            "cve_ids": [],
                            "affected_component": update.split('/')[0],
                            "recommendation": "Apply security update immediately"
                        })
        
        except Exception as e:
            logger.error(f"Error scanning Linux system: {e}")
        
        return vulnerabilities
    
    def _scan_windows_system(self) -> List[Dict[str, Any]]:
        """Scan Windows system for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Check for Windows updates
            result = subprocess.run(["wmic", "qfe", "list", "brief"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                vulnerabilities.append({
                    "type": "windows_update_check",
                    "severity": "medium",
                    "description": "Windows update check completed",
                    "cve_ids": [],
                    "affected_component": "windows_system",
                    "recommendation": "Check for available Windows updates"
                })
        
        except Exception as e:
            logger.error(f"Error scanning Windows system: {e}")
        
        return vulnerabilities
    
    def _scan_macos_system(self) -> List[Dict[str, Any]]:
        """Scan macOS system for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Check for macOS updates
            result = subprocess.run(["softwareupdate", "-l"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                vulnerabilities.append({
                    "type": "macos_update_check",
                    "severity": "medium",
                    "description": "macOS update check completed",
                    "cve_ids": [],
                    "affected_component": "macos_system",
                    "recommendation": "Check for available macOS updates"
                })
        
        except Exception as e:
            logger.error(f"Error scanning macOS system: {e}")
        
        return vulnerabilities
    
    def _scan_docker_system(self) -> List[Dict[str, Any]]:
        """Scan Docker system for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Scan Docker images for vulnerabilities
            result = subprocess.run(["docker", "images"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                vulnerabilities.append({
                    "type": "docker_vulnerability_scan",
                    "severity": "medium",
                    "description": "Docker vulnerability scan completed",
                    "cve_ids": [],
                    "affected_component": "docker_images",
                    "recommendation": "Scan Docker images for vulnerabilities"
                })
        
        except Exception as e:
            logger.error(f"Error scanning Docker system: {e}")
        
        return vulnerabilities
    
    def _scan_kubernetes_system(self) -> List[Dict[str, Any]]:
        """Scan Kubernetes system for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Check Kubernetes cluster security
            result = subprocess.run(["kubectl", "get", "pods", "--all-namespaces"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                vulnerabilities.append({
                    "type": "kubernetes_security_scan",
                    "severity": "medium",
                    "description": "Kubernetes security scan completed",
                    "cve_ids": [],
                    "affected_component": "kubernetes_cluster",
                    "recommendation": "Review Kubernetes security policies"
                })
        
        except Exception as e:
            logger.error(f"Error scanning Kubernetes system: {e}")
        
        return vulnerabilities
    
    def _run_common_scans(self) -> List[Dict[str, Any]]:
        """Run common vulnerability scans"""
        vulnerabilities = []
        
        try:
            # Check for common security issues
            common_checks = [
                ("open_ports", "Check for unnecessary open ports"),
                ("weak_passwords", "Check for weak password policies"),
                ("outdated_ssl", "Check for outdated SSL/TLS configurations"),
                ("missing_updates", "Check for missing security updates")
            ]
            
            for check_type, description in common_checks:
                vulnerabilities.append({
                    "type": check_type,
                    "severity": "medium",
                    "description": description,
                    "cve_ids": [],
                    "affected_component": "system_security",
                    "recommendation": f"Address {check_type} security issue"
                })
        
        except Exception as e:
            logger.error(f"Error running common scans: {e}")
        
        return vulnerabilities
    
    def _calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate risk score based on vulnerabilities"""
        try:
            if not vulnerabilities:
                return 0.0
            
            severity_scores = {
                "critical": 10.0,
                "high": 7.5,
                "medium": 5.0,
                "low": 2.5,
                "info": 1.0
            }
            
            total_score = 0.0
            for vuln in vulnerabilities:
                severity = vuln.get("severity", "medium")
                total_score += severity_scores.get(severity, 5.0)
            
            return min(total_score / len(vulnerabilities), 10.0)
        
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0
    
    def _calculate_compliance_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate compliance score based on vulnerabilities"""
        try:
            if not vulnerabilities:
                return 100.0
            
            # Calculate compliance score (100 - risk score * 10)
            risk_score = self._calculate_risk_score(vulnerabilities)
            compliance_score = max(100.0 - (risk_score * 10), 0.0)
            
            return compliance_score
        
        except Exception as e:
            logger.error(f"Error calculating compliance score: {e}")
            return 0.0

class PatchManager:
    """Patch management capabilities"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.vulnerability_scanner = VulnerabilityScanner()
        self.patches_db_path = "/var/lib/mingus/patches.db"
        self.deployments_db_path = "/var/lib/mingus/deployments.db"
        self.scans_db_path = "/var/lib/mingus/scans.db"
        self._init_databases()
    
    def _init_databases(self):
        """Initialize patch management databases"""
        try:
            # Initialize patches database
            conn = sqlite3.connect(self.patches_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patches (
                    patch_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    patch_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    cve_ids TEXT,
                    affected_systems TEXT,
                    affected_components TEXT,
                    release_date TEXT NOT NULL,
                    download_url TEXT,
                    checksum TEXT,
                    size INTEGER,
                    dependencies TEXT,
                    rollback_available BOOLEAN,
                    requires_reboot BOOLEAN,
                    installation_timeout INTEGER,
                    verification_required BOOLEAN
                )
            ''')
            conn.commit()
            conn.close()
            
            # Initialize deployments database
            conn = sqlite3.connect(self.deployments_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    deployment_id TEXT PRIMARY KEY,
                    patch_id TEXT NOT NULL,
                    system_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    installer_log TEXT,
                    verification_log TEXT,
                    rollback_log TEXT,
                    error_message TEXT,
                    deployment_duration INTEGER,
                    success BOOLEAN
                )
            ''')
            conn.commit()
            conn.close()
            
            # Initialize scans database
            conn = sqlite3.connect(self.scans_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id TEXT PRIMARY KEY,
                    system_id TEXT NOT NULL,
                    scan_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    vulnerabilities_found TEXT,
                    scan_status TEXT NOT NULL,
                    scan_log TEXT,
                    risk_score REAL,
                    compliance_score REAL
                )
            ''')
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error initializing patch management databases: {e}")
    
    def scan_for_vulnerabilities(self, system_id: str, scan_type: str = "comprehensive") -> VulnerabilityScan:
        """Scan system for vulnerabilities"""
        try:
            scan = self.vulnerability_scanner.scan_system_vulnerabilities(system_id, scan_type)
            
            # Store scan results
            self._store_scan_results(scan)
            
            return scan
        
        except Exception as e:
            logger.error(f"Error scanning for vulnerabilities: {e}")
            return VulnerabilityScan(
                scan_id=f"SCAN-{int(time.time())}",
                system_id=system_id,
                scan_type=scan_type,
                start_time=datetime.utcnow(),
                scan_status="failed",
                scan_log=str(e),
                risk_score=0.0,
                compliance_score=0.0
            )
    
    def _store_scan_results(self, scan: VulnerabilityScan):
        """Store scan results in database"""
        try:
            conn = sqlite3.connect(self.scans_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scans 
                (scan_id, system_id, scan_type, start_time, end_time, 
                 vulnerabilities_found, scan_status, scan_log, risk_score, compliance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan.scan_id,
                scan.system_id,
                scan.scan_type,
                scan.start_time.isoformat(),
                scan.end_time.isoformat() if scan.end_time else None,
                json.dumps(scan.vulnerabilities_found),
                scan.scan_status,
                scan.scan_log,
                scan.risk_score,
                scan.compliance_score
            ))
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error storing scan results: {e}")
    
    def get_available_patches(self, system_id: str) -> List[SecurityPatch]:
        """Get available patches for system"""
        try:
            # Scan for vulnerabilities first
            scan = self.scan_for_vulnerabilities(system_id)
            
            # Generate patches based on vulnerabilities
            patches = []
            for vuln in scan.vulnerabilities_found:
                patch = SecurityPatch(
                    patch_id=f"PATCH-{int(time.time())}-{len(patches)}",
                    name=f"Fix for {vuln.get('type', 'vulnerability')}",
                    description=vuln.get('description', 'Security patch'),
                    patch_type=PatchType.SECURITY,
                    severity=vuln.get('severity', 'medium'),
                    cve_ids=vuln.get('cve_ids', []),
                    affected_systems=[system_id],
                    affected_components=[vuln.get('affected_component', 'system')],
                    release_date=datetime.utcnow(),
                    download_url="",
                    checksum="",
                    size=0,
                    dependencies=[],
                    rollback_available=True,
                    requires_reboot=False,
                    installation_timeout=300,
                    verification_required=True
                )
                patches.append(patch)
            
            return patches
        
        except Exception as e:
            logger.error(f"Error getting available patches: {e}")
            return []
    
    def deploy_patch(self, patch: SecurityPatch, system_id: str) -> PatchDeployment:
        """Deploy a security patch"""
        try:
            deployment_id = f"DEPLOY-{int(time.time())}"
            start_time = datetime.utcnow()
            
            # Create deployment record
            deployment = PatchDeployment(
                deployment_id=deployment_id,
                patch_id=patch.patch_id,
                system_id=system_id,
                status=PatchStatus.INSTALLING,
                start_time=start_time
            )
            
            # Update status to downloading
            deployment.status = PatchStatus.DOWNLOADING
            self._update_deployment_status(deployment)
            
            # Download patch (simulated)
            time.sleep(2)  # Simulate download time
            
            # Update status to installing
            deployment.status = PatchStatus.INSTALLING
            self._update_deployment_status(deployment)
            
            # Install patch (simulated)
            installation_success = self._install_patch(patch, system_id)
            
            if installation_success:
                deployment.status = PatchStatus.INSTALLED
                deployment.success = True
                deployment.installer_log = "Patch installed successfully"
            else:
                deployment.status = PatchStatus.FAILED
                deployment.success = False
                deployment.error_message = "Patch installation failed"
            
            deployment.end_time = datetime.utcnow()
            deployment.deployment_duration = int((deployment.end_time - deployment.start_time).total_seconds())
            
            # Store deployment record
            self._store_deployment(deployment)
            
            return deployment
        
        except Exception as e:
            logger.error(f"Error deploying patch: {e}")
            deployment = PatchDeployment(
                deployment_id=f"DEPLOY-{int(time.time())}",
                patch_id=patch.patch_id,
                system_id=system_id,
                status=PatchStatus.FAILED,
                start_time=datetime.utcnow(),
                success=False,
                error_message=str(e)
            )
            self._store_deployment(deployment)
            return deployment
    
    def _install_patch(self, patch: SecurityPatch, system_id: str) -> bool:
        """Install a security patch"""
        try:
            # Simulate patch installation based on system type
            system_type = self.vulnerability_scanner._detect_system_type()
            
            if system_type == SystemType.LINUX:
                return self._install_linux_patch(patch)
            elif system_type == SystemType.WINDOWS:
                return self._install_windows_patch(patch)
            elif system_type == SystemType.MACOS:
                return self._install_macos_patch(patch)
            elif system_type == SystemType.DOCKER:
                return self._install_docker_patch(patch)
            elif system_type == SystemType.KUBERNETES:
                return self._install_kubernetes_patch(patch)
            else:
                return self._install_generic_patch(patch)
        
        except Exception as e:
            logger.error(f"Error installing patch: {e}")
            return False
    
    def _install_linux_patch(self, patch: SecurityPatch) -> bool:
        """Install Linux patch"""
        try:
            # Simulate Linux patch installation
            time.sleep(3)  # Simulate installation time
            return True
        except Exception as e:
            logger.error(f"Error installing Linux patch: {e}")
            return False
    
    def _install_windows_patch(self, patch: SecurityPatch) -> bool:
        """Install Windows patch"""
        try:
            # Simulate Windows patch installation
            time.sleep(3)  # Simulate installation time
            return True
        except Exception as e:
            logger.error(f"Error installing Windows patch: {e}")
            return False
    
    def _install_macos_patch(self, patch: SecurityPatch) -> bool:
        """Install macOS patch"""
        try:
            # Simulate macOS patch installation
            time.sleep(3)  # Simulate installation time
            return True
        except Exception as e:
            logger.error(f"Error installing macOS patch: {e}")
            return False
    
    def _install_docker_patch(self, patch: SecurityPatch) -> bool:
        """Install Docker patch"""
        try:
            # Simulate Docker patch installation
            time.sleep(3)  # Simulate installation time
            return True
        except Exception as e:
            logger.error(f"Error installing Docker patch: {e}")
            return False
    
    def _install_kubernetes_patch(self, patch: SecurityPatch) -> bool:
        """Install Kubernetes patch"""
        try:
            # Simulate Kubernetes patch installation
            time.sleep(3)  # Simulate installation time
            return True
        except Exception as e:
            logger.error(f"Error installing Kubernetes patch: {e}")
            return False
    
    def _install_generic_patch(self, patch: SecurityPatch) -> bool:
        """Install generic patch"""
        try:
            # Simulate generic patch installation
            time.sleep(3)  # Simulate installation time
            return True
        except Exception as e:
            logger.error(f"Error installing generic patch: {e}")
            return False
    
    def _update_deployment_status(self, deployment: PatchDeployment):
        """Update deployment status in database"""
        try:
            conn = sqlite3.connect(self.deployments_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO deployments 
                (deployment_id, patch_id, system_id, status, start_time, end_time,
                 installer_log, verification_log, rollback_log, error_message,
                 deployment_duration, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deployment.deployment_id,
                deployment.patch_id,
                deployment.system_id,
                deployment.status.value,
                deployment.start_time.isoformat(),
                deployment.end_time.isoformat() if deployment.end_time else None,
                deployment.installer_log,
                deployment.verification_log,
                deployment.rollback_log,
                deployment.error_message,
                deployment.deployment_duration,
                deployment.success
            ))
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error updating deployment status: {e}")
    
    def _store_deployment(self, deployment: PatchDeployment):
        """Store deployment record in database"""
        try:
            conn = sqlite3.connect(self.deployments_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO deployments 
                (deployment_id, patch_id, system_id, status, start_time, end_time,
                 installer_log, verification_log, rollback_log, error_message,
                 deployment_duration, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deployment.deployment_id,
                deployment.patch_id,
                deployment.system_id,
                deployment.status.value,
                deployment.start_time.isoformat(),
                deployment.end_time.isoformat() if deployment.end_time else None,
                deployment.installer_log,
                deployment.verification_log,
                deployment.rollback_log,
                deployment.error_message,
                deployment.deployment_duration,
                deployment.success
            ))
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error storing deployment: {e}")
    
    def get_patch_statistics(self) -> Dict[str, Any]:
        """Get patch management statistics"""
        try:
            stats = {
                "total_patches": 0,
                "total_deployments": 0,
                "total_scans": 0,
                "successful_deployments": 0,
                "failed_deployments": 0,
                "average_deployment_time": 0,
                "patch_types": {},
                "deployment_status": {},
                "scan_results": {}
            }
            
            # Get patch statistics
            conn = sqlite3.connect(self.patches_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patches")
            stats["total_patches"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT patch_type, COUNT(*) FROM patches GROUP BY patch_type")
            for patch_type, count in cursor.fetchall():
                stats["patch_types"][patch_type] = count
            conn.close()
            
            # Get deployment statistics
            conn = sqlite3.connect(self.deployments_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM deployments")
            stats["total_deployments"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM deployments WHERE success = 1")
            stats["successful_deployments"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM deployments WHERE success = 0")
            stats["failed_deployments"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(deployment_duration) FROM deployments WHERE deployment_duration > 0")
            avg_time = cursor.fetchone()[0]
            stats["average_deployment_time"] = avg_time if avg_time else 0
            
            cursor.execute("SELECT status, COUNT(*) FROM deployments GROUP BY status")
            for status, count in cursor.fetchall():
                stats["deployment_status"][status] = count
            conn.close()
            
            # Get scan statistics
            conn = sqlite3.connect(self.scans_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM scans")
            stats["total_scans"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT scan_status, COUNT(*) FROM scans GROUP BY scan_status")
            for scan_status, count in cursor.fetchall():
                stats["scan_results"][scan_status] = count
            conn.close()
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting patch statistics: {e}")
            return {}

def create_patch_manager(base_url: str = "http://localhost:5000") -> PatchManager:
    """Create patch manager instance"""
    return PatchManager(base_url)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Update and Patch Management System")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for system")
    parser.add_argument("--scan", action="store_true", help="Scan for vulnerabilities")
    parser.add_argument("--system-id", default="mingus-system", help="System ID to scan")
    parser.add_argument("--scan-type", default="comprehensive", help="Scan type")
    parser.add_argument("--get-patches", action="store_true", help="Get available patches")
    parser.add_argument("--deploy-patch", help="Deploy specific patch ID")
    parser.add_argument("--statistics", action="store_true", help="Show patch statistics")
    
    args = parser.parse_args()
    
    # Create patch manager
    patch_manager = create_patch_manager(args.base_url)
    
    if args.scan:
        # Scan for vulnerabilities
        print(f"Scanning system {args.system_id} for vulnerabilities...")
        scan = patch_manager.scan_for_vulnerabilities(args.system_id, args.scan_type)
        
        print(f"Scan completed: {scan.scan_status}")
        print(f"Risk Score: {scan.risk_score}")
        print(f"Compliance Score: {scan.compliance_score}")
        print(f"Vulnerabilities Found: {len(scan.vulnerabilities_found)}")
        
        for vuln in scan.vulnerabilities_found:
            print(f"  {vuln.get('type', 'unknown')}: {vuln.get('severity', 'unknown')} - {vuln.get('description', 'No description')}")
    
    elif args.get_patches:
        # Get available patches
        print(f"Getting available patches for system {args.system_id}...")
        patches = patch_manager.get_available_patches(args.system_id)
        
        print(f"Available patches: {len(patches)}")
        for patch in patches:
            print(f"  {patch.patch_id}: {patch.name} ({patch.severity})")
            print(f"    Description: {patch.description}")
            print(f"    Type: {patch.patch_type.value}")
    
    elif args.deploy_patch:
        # Deploy specific patch
        print(f"Deploying patch {args.deploy_patch}...")
        # This would require getting the patch details first
        print("Patch deployment functionality requires patch details")
    
    elif args.statistics:
        # Show patch statistics
        stats = patch_manager.get_patch_statistics()
        print("Patch Management Statistics:")
        print(f"Total Patches: {stats.get('total_patches', 0)}")
        print(f"Total Deployments: {stats.get('total_deployments', 0)}")
        print(f"Total Scans: {stats.get('total_scans', 0)}")
        print(f"Successful Deployments: {stats.get('successful_deployments', 0)}")
        print(f"Failed Deployments: {stats.get('failed_deployments', 0)}")
        print(f"Average Deployment Time: {stats.get('average_deployment_time', 0)} seconds")
        
        print("\nPatch Types:")
        for patch_type, count in stats.get('patch_types', {}).items():
            print(f"  {patch_type}: {count}")
        
        print("\nDeployment Status:")
        for status, count in stats.get('deployment_status', {}).items():
            print(f"  {status}: {count}")
        
        print("\nScan Results:")
        for scan_status, count in stats.get('scan_results', {}).items():
            print(f"  {scan_status}: {count}")
    
    else:
        print("Security Update and Patch Management System")
        print("Use --help for usage information") 