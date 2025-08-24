"""
Comprehensive Dependency Security Monitoring System for MINGUS
Python package vulnerability scanning and JavaScript dependency security checks
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

class DependencyType(Enum):
    """Dependency types"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    NODEJS = "nodejs"
    NPM = "npm"
    YARN = "yarn"
    PIP = "pip"
    CONDA = "conda"
    POETRY = "poetry"

class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ScanStatus(Enum):
    """Scan status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class DependencyVulnerability:
    """Dependency vulnerability information"""
    vulnerability_id: str
    package_name: str
    package_version: str
    dependency_type: DependencyType
    severity: VulnerabilitySeverity
    cve_id: str = ""
    description: str = ""
    affected_versions: List[str] = field(default_factory=list)
    fixed_versions: List[str] = field(default_factory=list)
    cvss_score: float = 0.0
    published_date: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    references: List[str] = field(default_factory=list)
    exploit_available: bool = False
    patch_available: bool = True
    recommended_action: str = ""

@dataclass
class DependencyScan:
    """Dependency scan information"""
    scan_id: str
    project_path: str
    dependency_type: DependencyType
    scan_status: ScanStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    vulnerabilities_found: List[DependencyVulnerability] = field(default_factory=list)
    scan_log: str = ""
    risk_score: float = 0.0
    compliance_score: float = 0.0
    total_dependencies: int = 0
    vulnerable_dependencies: int = 0
    outdated_dependencies: int = 0

@dataclass
class DependencyInfo:
    """Dependency information"""
    name: str
    version: str
    latest_version: str = ""
    dependency_type: DependencyType = DependencyType.PYTHON
    is_outdated: bool = False
    is_vulnerable: bool = False
    vulnerabilities: List[DependencyVulnerability] = field(default_factory=list)
    license: str = ""
    maintainer: str = ""
    repository: str = ""

class PythonDependencyScanner:
    """Python dependency vulnerability scanner"""
    
    def __init__(self):
        self.vulnerability_sources = [
            "https://pypi.org/pypi/{package}/json",
            "https://safety-db.pypa.io/vulnerabilities.json",
            "https://nvd.nist.gov/vuln/data-feeds"
        ]
        
        self.scan_tools = {
            "safety": "safety check",
            "bandit": "bandit -r .",
            "snyk": "snyk test",
            "pip-audit": "pip-audit",
            "trivy": "trivy fs --security-checks vuln"
        }
    
    def scan_python_dependencies(self, project_path: str) -> DependencyScan:
        """Scan Python dependencies for vulnerabilities"""
        try:
            scan_id = f"PYTHON-SCAN-{int(time.time())}"
            start_time = datetime.utcnow()
            
            # Initialize scan
            scan = DependencyScan(
                scan_id=scan_id,
                project_path=project_path,
                dependency_type=DependencyType.PYTHON,
                scan_status=ScanStatus.RUNNING,
                start_time=start_time
            )
            
            # Find Python dependency files
            dependency_files = self._find_python_dependency_files(project_path)
            
            if not dependency_files:
                scan.scan_status = ScanStatus.COMPLETED
                scan.end_time = datetime.utcnow()
                scan.scan_log = "No Python dependency files found"
                return scan
            
            # Parse dependencies
            dependencies = self._parse_python_dependencies(dependency_files)
            scan.total_dependencies = len(dependencies)
            
            # Scan for vulnerabilities
            vulnerabilities = []
            outdated_count = 0
            
            for dep in dependencies:
                # Check for vulnerabilities
                dep_vulnerabilities = self._check_package_vulnerabilities(dep)
                if dep_vulnerabilities:
                    vulnerabilities.extend(dep_vulnerabilities)
                    dep.is_vulnerable = True
                    scan.vulnerable_dependencies += 1
                
                # Check if outdated
                if dep.is_outdated:
                    outdated_count += 1
            
            scan.outdated_dependencies = outdated_count
            scan.vulnerabilities_found = vulnerabilities
            
            # Calculate risk and compliance scores
            scan.risk_score = self._calculate_risk_score(vulnerabilities)
            scan.compliance_score = self._calculate_compliance_score(vulnerabilities, dependencies)
            
            scan.scan_status = ScanStatus.COMPLETED
            scan.end_time = datetime.utcnow()
            
            return scan
        
        except Exception as e:
            logger.error(f"Error scanning Python dependencies: {e}")
            return DependencyScan(
                scan_id=f"PYTHON-SCAN-{int(time.time())}",
                project_path=project_path,
                dependency_type=DependencyType.PYTHON,
                scan_status=ScanStatus.FAILED,
                start_time=datetime.utcnow(),
                scan_log=str(e),
                risk_score=0.0,
                compliance_score=0.0
            )
    
    def _find_python_dependency_files(self, project_path: str) -> List[str]:
        """Find Python dependency files"""
        dependency_files = []
        
        try:
            project_dir = Path(project_path)
            
            # Common Python dependency files
            dependency_patterns = [
                "requirements.txt",
                "requirements/*.txt",
                "setup.py",
                "pyproject.toml",
                "Pipfile",
                "Pipfile.lock",
                "poetry.lock",
                "environment.yml",
                "conda-env.yml"
            ]
            
            for pattern in dependency_patterns:
                files = list(project_dir.glob(pattern))
                dependency_files.extend([str(f) for f in files])
            
            return dependency_files
        
        except Exception as e:
            logger.error(f"Error finding Python dependency files: {e}")
            return []
    
    def _parse_python_dependencies(self, dependency_files: List[str]) -> List[DependencyInfo]:
        """Parse Python dependencies from files"""
        dependencies = []
        
        try:
            for file_path in dependency_files:
                file_deps = []
                
                if file_path.endswith("requirements.txt"):
                    file_deps = self._parse_requirements_txt(file_path)
                elif file_path.endswith("setup.py"):
                    file_deps = self._parse_setup_py(file_path)
                elif file_path.endswith("pyproject.toml"):
                    file_deps = self._parse_pyproject_toml(file_path)
                elif file_path.endswith("Pipfile"):
                    file_deps = self._parse_pipfile(file_path)
                elif file_path.endswith("environment.yml"):
                    file_deps = self._parse_conda_env(file_path)
                
                dependencies.extend(file_deps)
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing Python dependencies: {e}")
            return []
    
    def _parse_requirements_txt(self, file_path: str) -> List[DependencyInfo]:
        """Parse requirements.txt file"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package name and version
                        if '==' in line:
                            name, version = line.split('==', 1)
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                        elif '<=' in line:
                            name, version = line.split('<=', 1)
                        elif '~=' in line:
                            name, version = line.split('~=', 1)
                        else:
                            name, version = line, ""
                        
                        dep = DependencyInfo(
                            name=name.strip(),
                            version=version.strip(),
                            dependency_type=DependencyType.PYTHON
                        )
                        dependencies.append(dep)
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing requirements.txt: {e}")
            return []
    
    def _parse_setup_py(self, file_path: str) -> List[DependencyInfo]:
        """Parse setup.py file"""
        dependencies = []
        
        try:
            # Simple parsing for setup.py
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for install_requires
                if 'install_requires' in content:
                    # Extract dependencies (simplified)
                    lines = content.split('\n')
                    for line in lines:
                        if 'install_requires' in line and '=' in line:
                            deps_str = line.split('=', 1)[1].strip()
                            if deps_str.startswith('['):
                                # Parse list of dependencies
                                deps = deps_str.strip('[]').split(',')
                                for dep in deps:
                                    dep = dep.strip().strip('"\'')
                                    if dep:
                                        dependencies.append(DependencyInfo(
                                            name=dep,
                                            version="",
                                            dependency_type=DependencyType.PYTHON
                                        ))
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing setup.py: {e}")
            return []
    
    def _parse_pyproject_toml(self, file_path: str) -> List[DependencyInfo]:
        """Parse pyproject.toml file"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for dependencies section
                if '[tool.poetry.dependencies]' in content:
                    lines = content.split('\n')
                    in_deps = False
                    
                    for line in lines:
                        if '[tool.poetry.dependencies]' in line:
                            in_deps = True
                            continue
                        elif line.startswith('[') and in_deps:
                            break
                        elif in_deps and '=' in line and not line.startswith('#'):
                            name = line.split('=')[0].strip()
                            dependencies.append(DependencyInfo(
                                name=name,
                                version="",
                                dependency_type=DependencyType.PYTHON
                            ))
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml: {e}")
            return []
    
    def _parse_pipfile(self, file_path: str) -> List[DependencyInfo]:
        """Parse Pipfile"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for [packages] section
                if '[packages]' in content:
                    lines = content.split('\n')
                    in_packages = False
                    
                    for line in lines:
                        if '[packages]' in line:
                            in_packages = True
                            continue
                        elif line.startswith('[') and in_packages:
                            break
                        elif in_packages and '=' in line and not line.startswith('#'):
                            name = line.split('=')[0].strip()
                            dependencies.append(DependencyInfo(
                                name=name,
                                version="",
                                dependency_type=DependencyType.PYTHON
                            ))
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing Pipfile: {e}")
            return []
    
    def _parse_conda_env(self, file_path: str) -> List[DependencyInfo]:
        """Parse conda environment file"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for dependencies section
                if 'dependencies:' in content:
                    lines = content.split('\n')
                    in_deps = False
                    
                    for line in lines:
                        if 'dependencies:' in line:
                            in_deps = True
                            continue
                        elif line.startswith('-') and in_deps:
                            dep_name = line.strip('- ').strip()
                            if '=' in dep_name:
                                name, version = dep_name.split('=', 1)
                            else:
                                name, version = dep_name, ""
                            
                            dependencies.append(DependencyInfo(
                                name=name,
                                version=version,
                                dependency_type=DependencyType.PYTHON
                            ))
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing conda environment: {e}")
            return []
    
    def _check_package_vulnerabilities(self, dependency: DependencyInfo) -> List[DependencyVulnerability]:
        """Check package for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Simulate vulnerability check
            # In a real implementation, this would query vulnerability databases
            
            # Example vulnerabilities for demonstration
            if dependency.name.lower() in ['requests', 'urllib3', 'cryptography']:
                vuln = DependencyVulnerability(
                    vulnerability_id=f"VULN-{int(time.time())}",
                    package_name=dependency.name,
                    package_version=dependency.version,
                    dependency_type=DependencyType.PYTHON,
                    severity=VulnerabilitySeverity.HIGH,
                    cve_id="CVE-2024-1234",
                    description=f"Security vulnerability in {dependency.name}",
                    affected_versions=[dependency.version],
                    fixed_versions=["2.0.0"],
                    cvss_score=7.5,
                    published_date=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                    references=["https://nvd.nist.gov/vuln/detail/CVE-2024-1234"],
                    exploit_available=False,
                    patch_available=True,
                    recommended_action=f"Upgrade {dependency.name} to version 2.0.0 or later"
                )
                vulnerabilities.append(vuln)
            
            return vulnerabilities
        
        except Exception as e:
            logger.error(f"Error checking package vulnerabilities: {e}")
            return []
    
    def _calculate_risk_score(self, vulnerabilities: List[DependencyVulnerability]) -> float:
        """Calculate risk score based on vulnerabilities"""
        try:
            if not vulnerabilities:
                return 0.0
            
            severity_scores = {
                VulnerabilitySeverity.CRITICAL: 10.0,
                VulnerabilitySeverity.HIGH: 7.5,
                VulnerabilitySeverity.MEDIUM: 5.0,
                VulnerabilitySeverity.LOW: 2.5,
                VulnerabilitySeverity.INFO: 1.0
            }
            
            total_score = 0.0
            for vuln in vulnerabilities:
                total_score += severity_scores.get(vuln.severity, 5.0)
            
            return min(total_score / len(vulnerabilities), 10.0)
        
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0
    
    def _calculate_compliance_score(self, vulnerabilities: List[DependencyVulnerability], dependencies: List[DependencyInfo]) -> float:
        """Calculate compliance score"""
        try:
            if not dependencies:
                return 100.0
            
            # Calculate compliance score (100 - risk score * 10)
            risk_score = self._calculate_risk_score(vulnerabilities)
            compliance_score = max(100.0 - (risk_score * 10), 0.0)
            
            return compliance_score
        
        except Exception as e:
            logger.error(f"Error calculating compliance score: {e}")
            return 0.0

class JavaScriptDependencyScanner:
    """JavaScript dependency vulnerability scanner"""
    
    def __init__(self):
        self.vulnerability_sources = [
            "https://registry.npmjs.org/{package}",
            "https://snyk.io/vuln/npm:{package}",
            "https://nvd.nist.gov/vuln/data-feeds"
        ]
        
        self.scan_tools = {
            "npm": "npm audit",
            "yarn": "yarn audit",
            "snyk": "snyk test",
            "trivy": "trivy fs --security-checks vuln",
            "npm-check": "npm-check -u"
        }
    
    def scan_javascript_dependencies(self, project_path: str) -> DependencyScan:
        """Scan JavaScript dependencies for vulnerabilities"""
        try:
            scan_id = f"JS-SCAN-{int(time.time())}"
            start_time = datetime.utcnow()
            
            # Initialize scan
            scan = DependencyScan(
                scan_id=scan_id,
                project_path=project_path,
                dependency_type=DependencyType.JAVASCRIPT,
                scan_status=ScanStatus.RUNNING,
                start_time=start_time
            )
            
            # Find JavaScript dependency files
            dependency_files = self._find_javascript_dependency_files(project_path)
            
            if not dependency_files:
                scan.scan_status = ScanStatus.COMPLETED
                scan.end_time = datetime.utcnow()
                scan.scan_log = "No JavaScript dependency files found"
                return scan
            
            # Parse dependencies
            dependencies = self._parse_javascript_dependencies(dependency_files)
            scan.total_dependencies = len(dependencies)
            
            # Scan for vulnerabilities
            vulnerabilities = []
            outdated_count = 0
            
            for dep in dependencies:
                # Check for vulnerabilities
                dep_vulnerabilities = self._check_package_vulnerabilities(dep)
                if dep_vulnerabilities:
                    vulnerabilities.extend(dep_vulnerabilities)
                    dep.is_vulnerable = True
                    scan.vulnerable_dependencies += 1
                
                # Check if outdated
                if dep.is_outdated:
                    outdated_count += 1
            
            scan.outdated_dependencies = outdated_count
            scan.vulnerabilities_found = vulnerabilities
            
            # Calculate risk and compliance scores
            scan.risk_score = self._calculate_risk_score(vulnerabilities)
            scan.compliance_score = self._calculate_compliance_score(vulnerabilities, dependencies)
            
            scan.scan_status = ScanStatus.COMPLETED
            scan.end_time = datetime.utcnow()
            
            return scan
        
        except Exception as e:
            logger.error(f"Error scanning JavaScript dependencies: {e}")
            return DependencyScan(
                scan_id=f"JS-SCAN-{int(time.time())}",
                project_path=project_path,
                dependency_type=DependencyType.JAVASCRIPT,
                scan_status=ScanStatus.FAILED,
                start_time=datetime.utcnow(),
                scan_log=str(e),
                risk_score=0.0,
                compliance_score=0.0
            )
    
    def _find_javascript_dependency_files(self, project_path: str) -> List[str]:
        """Find JavaScript dependency files"""
        dependency_files = []
        
        try:
            project_dir = Path(project_path)
            
            # Common JavaScript dependency files
            dependency_patterns = [
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                "bower.json"
            ]
            
            for pattern in dependency_patterns:
                files = list(project_dir.glob(pattern))
                dependency_files.extend([str(f) for f in files])
            
            return dependency_files
        
        except Exception as e:
            logger.error(f"Error finding JavaScript dependency files: {e}")
            return []
    
    def _parse_javascript_dependencies(self, dependency_files: List[str]) -> List[DependencyInfo]:
        """Parse JavaScript dependencies from files"""
        dependencies = []
        
        try:
            for file_path in dependency_files:
                file_deps = []
                
                if file_path.endswith("package.json"):
                    file_deps = self._parse_package_json(file_path)
                elif file_path.endswith("bower.json"):
                    file_deps = self._parse_bower_json(file_path)
                
                dependencies.extend(file_deps)
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing JavaScript dependencies: {e}")
            return []
    
    def _parse_package_json(self, file_path: str) -> List[DependencyInfo]:
        """Parse package.json file"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Parse dependencies
                for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                    if dep_type in data:
                        for name, version in data[dep_type].items():
                            dep = DependencyInfo(
                                name=name,
                                version=version,
                                dependency_type=DependencyType.JAVASCRIPT
                            )
                            dependencies.append(dep)
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing package.json: {e}")
            return []
    
    def _parse_bower_json(self, file_path: str) -> List[DependencyInfo]:
        """Parse bower.json file"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Parse dependencies
                if 'dependencies' in data:
                    for name, version in data['dependencies'].items():
                        dep = DependencyInfo(
                            name=name,
                            version=version,
                            dependency_type=DependencyType.JAVASCRIPT
                        )
                        dependencies.append(dep)
            
            return dependencies
        
        except Exception as e:
            logger.error(f"Error parsing bower.json: {e}")
            return []
    
    def _check_package_vulnerabilities(self, dependency: DependencyInfo) -> List[DependencyVulnerability]:
        """Check package for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Simulate vulnerability check
            # In a real implementation, this would query vulnerability databases
            
            # Example vulnerabilities for demonstration
            if dependency.name.lower() in ['lodash', 'jquery', 'moment']:
                vuln = DependencyVulnerability(
                    vulnerability_id=f"VULN-{int(time.time())}",
                    package_name=dependency.name,
                    package_version=dependency.version,
                    dependency_type=DependencyType.JAVASCRIPT,
                    severity=VulnerabilitySeverity.HIGH,
                    cve_id="CVE-2024-5678",
                    description=f"Security vulnerability in {dependency.name}",
                    affected_versions=[dependency.version],
                    fixed_versions=["4.0.0"],
                    cvss_score=8.0,
                    published_date=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                    references=["https://nvd.nist.gov/vuln/detail/CVE-2024-5678"],
                    exploit_available=True,
                    patch_available=True,
                    recommended_action=f"Upgrade {dependency.name} to version 4.0.0 or later"
                )
                vulnerabilities.append(vuln)
            
            return vulnerabilities
        
        except Exception as e:
            logger.error(f"Error checking package vulnerabilities: {e}")
            return []
    
    def _calculate_risk_score(self, vulnerabilities: List[DependencyVulnerability]) -> float:
        """Calculate risk score based on vulnerabilities"""
        try:
            if not vulnerabilities:
                return 0.0
            
            severity_scores = {
                VulnerabilitySeverity.CRITICAL: 10.0,
                VulnerabilitySeverity.HIGH: 7.5,
                VulnerabilitySeverity.MEDIUM: 5.0,
                VulnerabilitySeverity.LOW: 2.5,
                VulnerabilitySeverity.INFO: 1.0
            }
            
            total_score = 0.0
            for vuln in vulnerabilities:
                total_score += severity_scores.get(vuln.severity, 5.0)
            
            return min(total_score / len(vulnerabilities), 10.0)
        
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0
    
    def _calculate_compliance_score(self, vulnerabilities: List[DependencyVulnerability], dependencies: List[DependencyInfo]) -> float:
        """Calculate compliance score"""
        try:
            if not dependencies:
                return 100.0
            
            # Calculate compliance score (100 - risk score * 10)
            risk_score = self._calculate_risk_score(vulnerabilities)
            compliance_score = max(100.0 - (risk_score * 10), 0.0)
            
            return compliance_score
        
        except Exception as e:
            logger.error(f"Error calculating compliance score: {e}")
            return 0.0

class DependencySecurityMonitor:
    """Comprehensive dependency security monitoring system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.python_scanner = PythonDependencyScanner()
        self.javascript_scanner = JavaScriptDependencyScanner()
        self.scans_db_path = "/var/lib/mingus/dependency_scans.db"
        self.vulnerabilities_db_path = "/var/lib/mingus/dependency_vulnerabilities.db"
        self._init_databases()
    
    def _init_databases(self):
        """Initialize dependency monitoring databases"""
        try:
            # Initialize scans database
            conn = sqlite3.connect(self.scans_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependency_scans (
                    scan_id TEXT PRIMARY KEY,
                    project_path TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    scan_status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    vulnerabilities_found TEXT,
                    scan_log TEXT,
                    risk_score REAL,
                    compliance_score REAL,
                    total_dependencies INTEGER,
                    vulnerable_dependencies INTEGER,
                    outdated_dependencies INTEGER
                )
            ''')
            conn.commit()
            conn.close()
            
            # Initialize vulnerabilities database
            conn = sqlite3.connect(self.vulnerabilities_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependency_vulnerabilities (
                    vulnerability_id TEXT PRIMARY KEY,
                    package_name TEXT NOT NULL,
                    package_version TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    cve_id TEXT,
                    description TEXT,
                    affected_versions TEXT,
                    fixed_versions TEXT,
                    cvss_score REAL,
                    published_date TEXT,
                    last_updated TEXT,
                    references TEXT,
                    exploit_available BOOLEAN,
                    patch_available BOOLEAN,
                    recommended_action TEXT
                )
            ''')
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error initializing dependency monitoring databases: {e}")
    
    def scan_project_dependencies(self, project_path: str) -> List[DependencyScan]:
        """Scan project for all dependency types"""
        try:
            scans = []
            
            # Scan Python dependencies
            python_scan = self.python_scanner.scan_python_dependencies(project_path)
            scans.append(python_scan)
            self._store_scan_results(python_scan)
            
            # Scan JavaScript dependencies
            javascript_scan = self.javascript_scanner.scan_javascript_dependencies(project_path)
            scans.append(javascript_scan)
            self._store_scan_results(javascript_scan)
            
            return scans
        
        except Exception as e:
            logger.error(f"Error scanning project dependencies: {e}")
            return []
    
    def _store_scan_results(self, scan: DependencyScan):
        """Store scan results in database"""
        try:
            conn = sqlite3.connect(self.scans_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO dependency_scans 
                (scan_id, project_path, dependency_type, scan_status, start_time, end_time,
                 vulnerabilities_found, scan_log, risk_score, compliance_score,
                 total_dependencies, vulnerable_dependencies, outdated_dependencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan.scan_id,
                scan.project_path,
                scan.dependency_type.value,
                scan.scan_status.value,
                scan.start_time.isoformat(),
                scan.end_time.isoformat() if scan.end_time else None,
                json.dumps([v.__dict__ for v in scan.vulnerabilities_found]),
                scan.scan_log,
                scan.risk_score,
                scan.compliance_score,
                scan.total_dependencies,
                scan.vulnerable_dependencies,
                scan.outdated_dependencies
            ))
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error storing scan results: {e}")
    
    def get_dependency_statistics(self) -> Dict[str, Any]:
        """Get dependency monitoring statistics"""
        try:
            stats = {
                "total_scans": 0,
                "total_vulnerabilities": 0,
                "total_dependencies": 0,
                "vulnerable_dependencies": 0,
                "outdated_dependencies": 0,
                "scan_types": {},
                "vulnerability_severities": {},
                "dependency_types": {},
                "recent_scans": []
            }
            
            # Get scan statistics
            conn = sqlite3.connect(self.scans_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM dependency_scans")
            stats["total_scans"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT dependency_type, COUNT(*) FROM dependency_scans GROUP BY dependency_type")
            for dep_type, count in cursor.fetchall():
                stats["scan_types"][dep_type] = count
            
            cursor.execute("SELECT SUM(total_dependencies) FROM dependency_scans")
            total_deps = cursor.fetchone()[0]
            stats["total_dependencies"] = total_deps if total_deps else 0
            
            cursor.execute("SELECT SUM(vulnerable_dependencies) FROM dependency_scans")
            vuln_deps = cursor.fetchone()[0]
            stats["vulnerable_dependencies"] = vuln_deps if vuln_deps else 0
            
            cursor.execute("SELECT SUM(outdated_dependencies) FROM dependency_scans")
            outdated_deps = cursor.fetchone()[0]
            stats["outdated_dependencies"] = outdated_deps if outdated_deps else 0
            
            # Get recent scans
            cursor.execute("SELECT scan_id, dependency_type, scan_status, risk_score FROM dependency_scans ORDER BY start_time DESC LIMIT 10")
            recent_scans = cursor.fetchall()
            stats["recent_scans"] = [
                {
                    "scan_id": scan[0],
                    "dependency_type": scan[1],
                    "scan_status": scan[2],
                    "risk_score": scan[3]
                }
                for scan in recent_scans
            ]
            conn.close()
            
            # Get vulnerability statistics
            conn = sqlite3.connect(self.vulnerabilities_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM dependency_vulnerabilities")
            stats["total_vulnerabilities"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT severity, COUNT(*) FROM dependency_vulnerabilities GROUP BY severity")
            for severity, count in cursor.fetchall():
                stats["vulnerability_severities"][severity] = count
            
            cursor.execute("SELECT dependency_type, COUNT(*) FROM dependency_vulnerabilities GROUP BY dependency_type")
            for dep_type, count in cursor.fetchall():
                stats["dependency_types"][dep_type] = count
            conn.close()
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting dependency statistics: {e}")
            return {}

def create_dependency_monitor(base_url: str = "http://localhost:5000") -> DependencySecurityMonitor:
    """Create dependency security monitor instance"""
    return DependencySecurityMonitor(base_url)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dependency Security Monitoring System")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for system")
    parser.add_argument("--project-path", default=".", help="Project path to scan")
    parser.add_argument("--scan-python", action="store_true", help="Scan Python dependencies")
    parser.add_argument("--scan-javascript", action="store_true", help="Scan JavaScript dependencies")
    parser.add_argument("--scan-all", action="store_true", help="Scan all dependency types")
    parser.add_argument("--statistics", action="store_true", help="Show dependency statistics")
    
    args = parser.parse_args()
    
    # Create dependency monitor
    monitor = create_dependency_monitor(args.base_url)
    
    if args.scan_python:
        # Scan Python dependencies
        print(f"Scanning Python dependencies in {args.project_path}...")
        scan = monitor.python_scanner.scan_python_dependencies(args.project_path)
        
        print(f"Python scan completed: {scan.scan_status.value}")
        print(f"Risk Score: {scan.risk_score}")
        print(f"Compliance Score: {scan.compliance_score}")
        print(f"Total Dependencies: {scan.total_dependencies}")
        print(f"Vulnerable Dependencies: {scan.vulnerable_dependencies}")
        print(f"Outdated Dependencies: {scan.outdated_dependencies}")
        print(f"Vulnerabilities Found: {len(scan.vulnerabilities_found)}")
        
        for vuln in scan.vulnerabilities_found:
            print(f"  {vuln.package_name} {vuln.package_version}: {vuln.severity.value} - {vuln.description}")
    
    elif args.scan_javascript:
        # Scan JavaScript dependencies
        print(f"Scanning JavaScript dependencies in {args.project_path}...")
        scan = monitor.javascript_scanner.scan_javascript_dependencies(args.project_path)
        
        print(f"JavaScript scan completed: {scan.scan_status.value}")
        print(f"Risk Score: {scan.risk_score}")
        print(f"Compliance Score: {scan.compliance_score}")
        print(f"Total Dependencies: {scan.total_dependencies}")
        print(f"Vulnerable Dependencies: {scan.vulnerable_dependencies}")
        print(f"Outdated Dependencies: {scan.outdated_dependencies}")
        print(f"Vulnerabilities Found: {len(scan.vulnerabilities_found)}")
        
        for vuln in scan.vulnerabilities_found:
            print(f"  {vuln.package_name} {vuln.package_version}: {vuln.severity.value} - {vuln.description}")
    
    elif args.scan_all:
        # Scan all dependency types
        print(f"Scanning all dependencies in {args.project_path}...")
        scans = monitor.scan_project_dependencies(args.project_path)
        
        for scan in scans:
            print(f"\n{scan.dependency_type.value.upper()} Dependencies:")
            print(f"  Scan Status: {scan.scan_status.value}")
            print(f"  Risk Score: {scan.risk_score}")
            print(f"  Compliance Score: {scan.compliance_score}")
            print(f"  Total Dependencies: {scan.total_dependencies}")
            print(f"  Vulnerable Dependencies: {scan.vulnerable_dependencies}")
            print(f"  Outdated Dependencies: {scan.outdated_dependencies}")
            print(f"  Vulnerabilities Found: {len(scan.vulnerabilities_found)}")
            
            for vuln in scan.vulnerabilities_found:
                print(f"    {vuln.package_name} {vuln.package_version}: {vuln.severity.value} - {vuln.description}")
    
    elif args.statistics:
        # Show dependency statistics
        stats = monitor.get_dependency_statistics()
        print("Dependency Security Monitoring Statistics:")
        print(f"Total Scans: {stats.get('total_scans', 0)}")
        print(f"Total Vulnerabilities: {stats.get('total_vulnerabilities', 0)}")
        print(f"Total Dependencies: {stats.get('total_dependencies', 0)}")
        print(f"Vulnerable Dependencies: {stats.get('vulnerable_dependencies', 0)}")
        print(f"Outdated Dependencies: {stats.get('outdated_dependencies', 0)}")
        
        print("\nScan Types:")
        for scan_type, count in stats.get('scan_types', {}).items():
            print(f"  {scan_type}: {count}")
        
        print("\nVulnerability Severities:")
        for severity, count in stats.get('vulnerability_severities', {}).items():
            print(f"  {severity}: {count}")
        
        print("\nDependency Types:")
        for dep_type, count in stats.get('dependency_types', {}).items():
            print(f"  {dep_type}: {count}")
        
        print("\nRecent Scans:")
        for scan in stats.get('recent_scans', []):
            print(f"  {scan['scan_id']}: {scan['dependency_type']} - {scan['scan_status']} (Risk: {scan['risk_score']})")
    
    else:
        print("Dependency Security Monitoring System")
        print("Use --help for usage information") 