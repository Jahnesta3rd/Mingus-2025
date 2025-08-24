"""
Detailed Security Test Reporting for MINGUS
Comprehensive security reporting with test results, coverage, vulnerabilities, and remediation
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

class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SecurityPostureLevel(Enum):
    """Security posture levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class TestCoverageType(Enum):
    """Test coverage types"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    SESSION_MANAGEMENT = "session_management"
    CRYPTOGRAPHY = "cryptography"
    NETWORK_SECURITY = "network_security"
    DATA_PROTECTION = "data_protection"
    API_SECURITY = "api_security"
    FILE_UPLOAD = "file_upload"
    PAYMENT_SECURITY = "payment_security"

@dataclass
class VulnerabilityFinding:
    """Vulnerability finding structure"""
    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: float
    cwe_id: str
    affected_component: str
    test_id: str
    discovery_date: datetime
    status: str = "open"
    remediation_priority: str = "medium"
    remediation_effort: str = "medium"
    remediation_cost: str = "medium"
    false_positive: bool = False
    verified: bool = False
    references: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestCoverage:
    """Test coverage structure"""
    coverage_type: TestCoverageType
    total_tests: int
    passed_tests: int
    failed_tests: int
    coverage_percentage: float
    critical_gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class SecurityPostureAssessment:
    """Security posture assessment structure"""
    overall_score: float
    posture_level: SecurityPostureLevel
    risk_level: str
    compliance_status: Dict[str, bool] = field(default_factory=dict)
    security_gaps: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)

@dataclass
class RemediationRecommendation:
    """Remediation recommendation structure"""
    id: str
    title: str
    description: str
    priority: str
    effort: str
    cost: str
    timeline: str
    resources_required: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    related_vulnerabilities: List[str] = field(default_factory=list)

class DetailedSecurityReporting:
    """Comprehensive security test reporting system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.reports_dir = "security/reports"
        self.vulnerabilities_db = "security/vulnerabilities.db"
        self._ensure_directories()
        self._init_vulnerabilities_db()
    
    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs("security/data", exist_ok=True)
        os.makedirs("security/templates", exist_ok=True)
    
    def _init_vulnerabilities_db(self):
        """Initialize vulnerabilities database"""
        conn = sqlite3.connect(self.vulnerabilities_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT NOT NULL,
                cvss_score REAL,
                cwe_id TEXT,
                affected_component TEXT,
                test_id TEXT,
                discovery_date TEXT,
                status TEXT DEFAULT 'open',
                remediation_priority TEXT DEFAULT 'medium',
                remediation_effort TEXT DEFAULT 'medium',
                remediation_cost TEXT DEFAULT 'medium',
                false_positive BOOLEAN DEFAULT 0,
                verified BOOLEAN DEFAULT 0,
                references TEXT,
                evidence TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_comprehensive_report(self, test_results: Dict[str, Any], 
                                    include_vulnerabilities: bool = True,
                                    include_coverage: bool = True,
                                    include_posture: bool = True,
                                    include_remediation: bool = True) -> str:
        """Generate comprehensive security test report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.reports_dir}/comprehensive_security_report_{timestamp}.html"
        
        # Collect all report data
        report_data = {
            "timestamp": datetime.utcnow(),
            "base_url": self.base_url,
            "test_results": test_results,
            "summary": self._generate_test_summary(test_results)
        }
        
        if include_vulnerabilities:
            report_data["vulnerabilities"] = self._analyze_vulnerabilities(test_results)
        
        if include_coverage:
            report_data["coverage"] = self._analyze_test_coverage(test_results)
        
        if include_posture:
            report_data["posture"] = self._assess_security_posture(test_results, report_data.get("vulnerabilities", []))
        
        if include_remediation:
            report_data["remediation"] = self._generate_remediation_recommendations(
                report_data.get("vulnerabilities", []),
                report_data.get("posture", None)
            )
        
        # Generate HTML report
        html_content = self._generate_comprehensive_html_report(report_data)
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        # Generate JSON report
        json_file = f"{self.reports_dir}/comprehensive_security_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Generate CSV report
        csv_file = f"{self.reports_dir}/comprehensive_security_report_{timestamp}.csv"
        self._generate_csv_report(report_data, csv_file)
        
        logger.info(f"Comprehensive security report generated: {report_file}")
        return report_file
    
    def _generate_test_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test results summary"""
        results = test_results.get("results", {})
        
        total_tests = len(results)
        passed_tests = len([r for r in results.values() if r.get("status") == "passed"])
        failed_tests = len([r for r in results.values() if r.get("status") == "failed"])
        error_tests = len([r for r in results.values() if r.get("status") == "error"])
        
        # Calculate security score
        security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group by severity
        severity_stats = {}
        for severity in ["critical", "high", "medium", "low", "info"]:
            severity_tests = [r for r in results.values() if r.get("severity") == severity]
            severity_stats[severity] = {
                "total": len(severity_tests),
                "passed": len([r for r in severity_tests if r.get("status") == "passed"]),
                "failed": len([r for r in severity_tests if r.get("status") == "failed"]),
                "error": len([r for r in severity_tests if r.get("status") == "error"])
            }
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "security_score": security_score,
            "severity_stats": severity_stats,
            "execution_time": sum(r.get("execution_time", 0) for r in results.values()),
            "average_execution_time": statistics.mean([r.get("execution_time", 0) for r in results.values()]) if results else 0
        }
    
    def _analyze_vulnerabilities(self, test_results: Dict[str, Any]) -> List[VulnerabilityFinding]:
        """Analyze vulnerabilities from test results"""
        vulnerabilities = []
        results = test_results.get("results", {})
        
        for test_id, result in results.items():
            if result.get("status") == "failed":
                # Analyze failed test for vulnerabilities
                vuln = self._extract_vulnerability_from_test(test_id, result)
                if vuln:
                    vulnerabilities.append(vuln)
        
        # Add known vulnerability patterns
        known_vulns = self._detect_known_vulnerability_patterns(test_results)
        vulnerabilities.extend(known_vulns)
        
        return vulnerabilities
    
    def _extract_vulnerability_from_test(self, test_id: str, result: Dict[str, Any]) -> Optional[VulnerabilityFinding]:
        """Extract vulnerability information from failed test"""
        error_message = result.get("error_message", "")
        test_name = result.get("test_name", "")
        severity = result.get("severity", "medium")
        
        # Map test types to vulnerability categories
        vulnerability_mapping = {
            "auth_security": {
                "title": "Authentication Bypass",
                "description": "Authentication mechanism can be bypassed",
                "cwe_id": "CWE-287",
                "cvss_score": 9.8
            },
            "input_validation": {
                "title": "Input Validation Failure",
                "description": "Input validation and sanitization is insufficient",
                "cwe_id": "CWE-20",
                "cvss_score": 7.5
            },
            "rate_limiting": {
                "title": "Rate Limiting Bypass",
                "description": "Rate limiting mechanism can be bypassed",
                "cwe_id": "CWE-770",
                "cvss_score": 5.3
            },
            "ssl_security": {
                "title": "SSL/TLS Configuration Issue",
                "description": "SSL/TLS configuration is insecure",
                "cwe_id": "CWE-327",
                "cvss_score": 7.5
            }
        }
        
        if test_id in vulnerability_mapping:
            vuln_info = vulnerability_mapping[test_id]
            return VulnerabilityFinding(
                id=f"VULN-{test_id}-{int(time.time())}",
                title=vuln_info["title"],
                description=vuln_info["description"],
                severity=VulnerabilitySeverity(severity),
                cvss_score=vuln_info["cvss_score"],
                cwe_id=vuln_info["cwe_id"],
                affected_component=test_id,
                test_id=test_id,
                discovery_date=datetime.utcnow(),
                evidence={"error_message": error_message, "test_name": test_name}
            )
        
        return None
    
    def _detect_known_vulnerability_patterns(self, test_results: Dict[str, Any]) -> List[VulnerabilityFinding]:
        """Detect known vulnerability patterns"""
        vulnerabilities = []
        
        # Check for common security issues
        if "sql_injection" in str(test_results).lower():
            vulnerabilities.append(VulnerabilityFinding(
                id=f"VULN-SQL-{int(time.time())}",
                title="SQL Injection Vulnerability",
                description="Application is vulnerable to SQL injection attacks",
                severity=VulnerabilitySeverity.CRITICAL,
                cvss_score=9.8,
                cwe_id="CWE-89",
                affected_component="database_layer",
                test_id="sql_injection_test",
                discovery_date=datetime.utcnow()
            ))
        
        if "xss" in str(test_results).lower():
            vulnerabilities.append(VulnerabilityFinding(
                id=f"VULN-XSS-{int(time.time())}",
                title="Cross-Site Scripting (XSS)",
                description="Application is vulnerable to XSS attacks",
                severity=VulnerabilitySeverity.HIGH,
                cvss_score=6.1,
                cwe_id="CWE-79",
                affected_component="web_interface",
                test_id="xss_test",
                discovery_date=datetime.utcnow()
            ))
        
        return vulnerabilities
    
    def _analyze_test_coverage(self, test_results: Dict[str, Any]) -> Dict[str, TestCoverage]:
        """Analyze test coverage by security category"""
        coverage = {}
        results = test_results.get("results", {})
        
        # Define coverage categories
        coverage_categories = {
            TestCoverageType.AUTHENTICATION: ["auth_security", "login_test", "logout_test"],
            TestCoverageType.AUTHORIZATION: ["authorization_test", "access_control_test"],
            TestCoverageType.INPUT_VALIDATION: ["input_validation", "sql_injection_test", "xss_test"],
            TestCoverageType.SESSION_MANAGEMENT: ["session_test", "csrf_test"],
            TestCoverageType.CRYPTOGRAPHY: ["ssl_security", "encryption_test"],
            TestCoverageType.NETWORK_SECURITY: ["network_test", "firewall_test"],
            TestCoverageType.DATA_PROTECTION: ["data_protection_test", "privacy_test"],
            TestCoverageType.API_SECURITY: ["api_security_test", "rate_limiting"],
            TestCoverageType.FILE_UPLOAD: ["file_upload_test", "file_validation_test"],
            TestCoverageType.PAYMENT_SECURITY: ["payment_test", "pci_compliance_test"]
        }
        
        for category, test_ids in coverage_categories.items():
            category_tests = [r for r in results.values() if any(test_id in r.get("test_id", "") for test_id in test_ids)]
            
            total_tests = len(category_tests)
            passed_tests = len([t for t in category_tests if t.get("status") == "passed"])
            failed_tests = len([t for t in category_tests if t.get("status") == "failed"])
            
            coverage_percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Identify critical gaps
            critical_gaps = []
            if coverage_percentage < 80:
                critical_gaps.append(f"Low test coverage ({coverage_percentage:.1f}%)")
            if failed_tests > 0:
                critical_gaps.append(f"{failed_tests} failed tests")
            
            # Generate recommendations
            recommendations = []
            if coverage_percentage < 80:
                recommendations.append("Increase test coverage for this security category")
            if failed_tests > 0:
                recommendations.append("Fix failing tests and address underlying security issues")
            if total_tests == 0:
                recommendations.append("Implement comprehensive security tests for this category")
            
            coverage[category.value] = TestCoverage(
                coverage_type=category,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                coverage_percentage=coverage_percentage,
                critical_gaps=critical_gaps,
                recommendations=recommendations
            )
        
        return coverage
    
    def _assess_security_posture(self, test_results: Dict[str, Any], 
                               vulnerabilities: List[VulnerabilityFinding]) -> SecurityPostureAssessment:
        """Assess overall security posture"""
        summary = self._generate_test_summary(test_results)
        security_score = summary["security_score"]
        
        # Calculate risk level based on vulnerabilities
        critical_vulns = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL])
        high_vulns = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.HIGH])
        medium_vulns = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM])
        
        # Determine posture level
        if security_score >= 90 and critical_vulns == 0 and high_vulns <= 1:
            posture_level = SecurityPostureLevel.EXCELLENT
            risk_level = "Low"
        elif security_score >= 80 and critical_vulns == 0 and high_vulns <= 3:
            posture_level = SecurityPostureLevel.GOOD
            risk_level = "Low-Medium"
        elif security_score >= 70 and critical_vulns <= 1 and high_vulns <= 5:
            posture_level = SecurityPostureLevel.FAIR
            risk_level = "Medium"
        elif security_score >= 50 and critical_vulns <= 2:
            posture_level = SecurityPostureLevel.POOR
            risk_level = "High"
        else:
            posture_level = SecurityPostureLevel.CRITICAL
            risk_level = "Critical"
        
        # Identify security gaps
        security_gaps = []
        if critical_vulns > 0:
            security_gaps.append(f"{critical_vulns} critical vulnerabilities detected")
        if high_vulns > 3:
            security_gaps.append(f"{high_vulns} high-severity vulnerabilities detected")
        if security_score < 80:
            security_gaps.append("Low overall security test score")
        
        # Identify strengths
        strengths = []
        if security_score >= 80:
            strengths.append("Good overall security test performance")
        if critical_vulns == 0:
            strengths.append("No critical vulnerabilities detected")
        if summary["passed_tests"] > summary["failed_tests"]:
            strengths.append("Majority of security tests passing")
        
        # Identify improvement areas
        improvement_areas = []
        if security_score < 90:
            improvement_areas.append("Improve overall security test score")
        if critical_vulns > 0:
            improvement_areas.append("Address critical vulnerabilities immediately")
        if high_vulns > 3:
            improvement_areas.append("Reduce high-severity vulnerabilities")
        
        # Check compliance status
        compliance_status = {
            "OWASP_Top_10": critical_vulns == 0 and high_vulns <= 2,
            "PCI_DSS": critical_vulns == 0 and security_score >= 85,
            "GDPR": security_score >= 80,
            "ISO_27001": security_score >= 85 and critical_vulns == 0
        }
        
        return SecurityPostureAssessment(
            overall_score=security_score,
            posture_level=posture_level,
            risk_level=risk_level,
            compliance_status=compliance_status,
            security_gaps=security_gaps,
            strengths=strengths,
            improvement_areas=improvement_areas
        )
    
    def _generate_remediation_recommendations(self, vulnerabilities: List[VulnerabilityFinding],
                                            posture: SecurityPostureAssessment) -> List[RemediationRecommendation]:
        """Generate remediation recommendations"""
        recommendations = []
        
        # Generate recommendations for each vulnerability
        for vuln in vulnerabilities:
            if vuln.severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]:
                recommendation = self._create_vulnerability_recommendation(vuln)
                recommendations.append(recommendation)
        
        # Generate general security improvement recommendations
        if posture.overall_score < 90:
            recommendations.append(RemediationRecommendation(
                id="REC-GEN-001",
                title="Improve Overall Security Score",
                description="Implement comprehensive security improvements to achieve 90%+ security score",
                priority="high",
                effort="medium",
                cost="medium",
                timeline="3-6 months",
                resources_required=["Security team", "Development team", "QA team"],
                implementation_steps=[
                    "Conduct security gap analysis",
                    "Prioritize security improvements",
                    "Implement security controls",
                    "Conduct security testing",
                    "Monitor and validate improvements"
                ],
                validation_steps=[
                    "Run comprehensive security tests",
                    "Verify security score improvement",
                    "Conduct penetration testing",
                    "Review security metrics"
                ]
            ))
        
        # Generate compliance recommendations
        for compliance, status in posture.compliance_status.items():
            if not status:
                recommendations.append(RemediationRecommendation(
                    id=f"REC-COMP-{compliance}",
                    title=f"Achieve {compliance} Compliance",
                    description=f"Implement controls to achieve {compliance} compliance",
                    priority="medium",
                    effort="high",
                    cost="high",
                    timeline="6-12 months",
                    resources_required=["Compliance team", "Security team", "Legal team"],
                    implementation_steps=[
                        f"Conduct {compliance} gap analysis",
                        "Implement required controls",
                        "Document compliance procedures",
                        "Train staff on compliance requirements",
                        "Conduct compliance audits"
                    ],
                    validation_steps=[
                        "Conduct compliance assessment",
                        "Review compliance documentation",
                        "Validate control effectiveness",
                        "Obtain compliance certification"
                    ]
                ))
        
        return recommendations
    
    def _create_vulnerability_recommendation(self, vuln: VulnerabilityFinding) -> RemediationRecommendation:
        """Create remediation recommendation for specific vulnerability"""
        priority_mapping = {
            VulnerabilitySeverity.CRITICAL: "critical",
            VulnerabilitySeverity.HIGH: "high",
            VulnerabilitySeverity.MEDIUM: "medium",
            VulnerabilitySeverity.LOW: "low"
        }
        
        effort_mapping = {
            VulnerabilitySeverity.CRITICAL: "low",
            VulnerabilitySeverity.HIGH: "medium",
            VulnerabilitySeverity.MEDIUM: "medium",
            VulnerabilitySeverity.LOW: "high"
        }
        
        timeline_mapping = {
            VulnerabilitySeverity.CRITICAL: "immediate",
            VulnerabilitySeverity.HIGH: "1-2 weeks",
            VulnerabilitySeverity.MEDIUM: "1-2 months",
            VulnerabilitySeverity.LOW: "3-6 months"
        }
        
        return RemediationRecommendation(
            id=f"REC-{vuln.id}",
            title=f"Remediate {vuln.title}",
            description=vuln.description,
            priority=priority_mapping.get(vuln.severity, "medium"),
            effort=effort_mapping.get(vuln.severity, "medium"),
            cost=vuln.remediation_cost,
            timeline=timeline_mapping.get(vuln.severity, "1-2 months"),
            resources_required=["Security team", "Development team"],
            implementation_steps=[
                "Analyze vulnerability root cause",
                "Design secure implementation",
                "Implement security fix",
                "Test security fix",
                "Deploy to production",
                "Verify fix effectiveness"
            ],
            validation_steps=[
                "Run vulnerability-specific tests",
                "Conduct security review",
                "Verify no regression issues",
                "Monitor for similar vulnerabilities"
            ],
            related_vulnerabilities=[vuln.id]
        )
    
    def _generate_comprehensive_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate comprehensive HTML security report"""
        template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Security Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #007bff; padding-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
        .summary-card h3 { margin: 0 0 10px 0; color: #333; }
        .summary-card .number { font-size: 2em; font-weight: bold; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .error { color: #ffc107; }
        .security-score { font-size: 3em; font-weight: bold; text-align: center; margin: 20px 0; }
        .score-excellent { color: #28a745; }
        .score-good { color: #17a2b8; }
        .score-fair { color: #ffc107; }
        .score-poor { color: #fd7e14; }
        .score-critical { color: #dc3545; }
        .section { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .section h2 { color: #007bff; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; }
        .vulnerability { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid; }
        .vulnerability.critical { border-left-color: #dc3545; background-color: #f8d7da; }
        .vulnerability.high { border-left-color: #fd7e14; background-color: #fff3cd; }
        .vulnerability.medium { border-left-color: #ffc107; background-color: #d1ecf1; }
        .vulnerability.low { border-left-color: #28a745; background-color: #d4edda; }
        .coverage-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
        .coverage-card { background: white; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; }
        .coverage-percentage { font-size: 1.5em; font-weight: bold; text-align: center; }
        .coverage-good { color: #28a745; }
        .coverage-warning { color: #ffc107; }
        .coverage-poor { color: #dc3545; }
        .recommendation { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .priority-critical { border-left-color: #dc3545; }
        .priority-high { border-left-color: #fd7e14; }
        .priority-medium { border-left-color: #ffc107; }
        .priority-low { border-left-color: #28a745; }
        .table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background-color: #f8f9fa; font-weight: bold; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
        .badge-critical { background-color: #dc3545; color: white; }
        .badge-high { background-color: #fd7e14; color: white; }
        .badge-medium { background-color: #ffc107; color: black; }
        .badge-low { background-color: #28a745; color: white; }
        .badge-info { background-color: #17a2b8; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Comprehensive Security Test Report</h1>
            <p>{{ report_data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }} | {{ report_data.base_url }}</p>
        </div>
        
        <div class="security-score score-{{ 'excellent' if report_data.summary.security_score >= 90 else 'good' if report_data.summary.security_score >= 80 else 'fair' if report_data.summary.security_score >= 70 else 'poor' if report_data.summary.security_score >= 50 else 'critical' }}">
            {{ "%.1f"|format(report_data.summary.security_score) }}%
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="number">{{ report_data.summary.total_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="number passed">{{ report_data.summary.passed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="number failed">{{ report_data.summary.failed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Errors</h3>
                <div class="number error">{{ report_data.summary.error_tests }}</div>
            </div>
        </div>
        
        {% if report_data.vulnerabilities %}
        <div class="section">
            <h2>🔍 Vulnerability Findings</h2>
            <p><strong>{{ report_data.vulnerabilities|length }}</strong> vulnerabilities detected</p>
            
            {% for vuln in report_data.vulnerabilities %}
            <div class="vulnerability {{ vuln.severity.value }}">
                <h3>{{ vuln.title }}</h3>
                <p><strong>Severity:</strong> <span class="badge badge-{{ vuln.severity.value }}">{{ vuln.severity.value.title() }}</span></p>
                <p><strong>CVSS Score:</strong> {{ vuln.cvss_score }}</p>
                <p><strong>CWE ID:</strong> {{ vuln.cwe_id }}</p>
                <p><strong>Affected Component:</strong> {{ vuln.affected_component }}</p>
                <p><strong>Description:</strong> {{ vuln.description }}</p>
                {% if vuln.evidence %}
                <p><strong>Evidence:</strong> {{ vuln.evidence }}</p>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if report_data.coverage %}
        <div class="section">
            <h2>📊 Test Coverage Analysis</h2>
            <div class="coverage-grid">
                {% for category, coverage in report_data.coverage.items() %}
                <div class="coverage-card">
                    <h3>{{ category.replace('_', ' ').title() }}</h3>
                    <div class="coverage-percentage coverage-{{ 'good' if coverage.coverage_percentage >= 80 else 'warning' if coverage.coverage_percentage >= 60 else 'poor' }}">
                        {{ "%.1f"|format(coverage.coverage_percentage) }}%
                    </div>
                    <p><strong>Tests:</strong> {{ coverage.passed_tests }}/{{ coverage.total_tests }} passed</p>
                    {% if coverage.critical_gaps %}
                    <p><strong>Critical Gaps:</strong></p>
                    <ul>
                        {% for gap in coverage.critical_gaps %}
                        <li>{{ gap }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if report_data.posture %}
        <div class="section">
            <h2>🛡️ Security Posture Assessment</h2>
            <p><strong>Overall Score:</strong> {{ "%.1f"|format(report_data.posture.overall_score) }}%</p>
            <p><strong>Posture Level:</strong> <span class="badge badge-{{ report_data.posture.posture_level.value }}">{{ report_data.posture.posture_level.value.title() }}</span></p>
            <p><strong>Risk Level:</strong> {{ report_data.posture.risk_level }}</p>
            
            <h3>Compliance Status</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Standard</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for standard, status in report_data.posture.compliance_status.items() %}
                    <tr>
                        <td>{{ standard.replace('_', ' ') }}</td>
                        <td><span class="badge badge-{{ 'good' if status else 'critical' }}">{{ 'Compliant' if status else 'Non-Compliant' }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            {% if report_data.posture.strengths %}
            <h3>Security Strengths</h3>
            <ul>
                {% for strength in report_data.posture.strengths %}
                <li>{{ strength }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            {% if report_data.posture.security_gaps %}
            <h3>Security Gaps</h3>
            <ul>
                {% for gap in report_data.posture.security_gaps %}
                <li>{{ gap }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            {% if report_data.posture.improvement_areas %}
            <h3>Improvement Areas</h3>
            <ul>
                {% for area in report_data.posture.improvement_areas %}
                <li>{{ area }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endif %}
        
        {% if report_data.remediation %}
        <div class="section">
            <h2>🔧 Remediation Recommendations</h2>
            <p><strong>{{ report_data.remediation|length }}</strong> recommendations generated</p>
            
            {% for rec in report_data.remediation %}
            <div class="recommendation priority-{{ rec.priority }}">
                <h3>{{ rec.title }}</h3>
                <p><strong>Priority:</strong> <span class="badge badge-{{ rec.priority }}">{{ rec.priority.title() }}</span></p>
                <p><strong>Effort:</strong> {{ rec.effort.title() }}</p>
                <p><strong>Cost:</strong> {{ rec.cost.title() }}</p>
                <p><strong>Timeline:</strong> {{ rec.timeline }}</p>
                <p><strong>Description:</strong> {{ rec.description }}</p>
                
                {% if rec.implementation_steps %}
                <h4>Implementation Steps</h4>
                <ol>
                    {% for step in rec.implementation_steps %}
                    <li>{{ step }}</li>
                    {% endfor %}
                </ol>
                {% endif %}
                
                {% if rec.validation_steps %}
                <h4>Validation Steps</h4>
                <ol>
                    {% for step in rec.validation_steps %}
                    <li>{{ step }}</li>
                    {% endfor %}
                </ol>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
        """
        
        template_obj = Template(template)
        return template_obj.render(report_data=report_data)
    
    def _generate_csv_report(self, report_data: Dict[str, Any], csv_file: str):
        """Generate CSV security report"""
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write summary
            writer.writerow(['Security Test Summary'])
            writer.writerow(['Total Tests', report_data['summary']['total_tests']])
            writer.writerow(['Passed Tests', report_data['summary']['passed_tests']])
            writer.writerow(['Failed Tests', report_data['summary']['failed_tests']])
            writer.writerow(['Error Tests', report_data['summary']['error_tests']])
            writer.writerow(['Security Score', f"{report_data['summary']['security_score']:.1f}%"])
            writer.writerow([])
            
            # Write vulnerabilities
            if 'vulnerabilities' in report_data:
                writer.writerow(['Vulnerability Findings'])
                writer.writerow(['ID', 'Title', 'Severity', 'CVSS Score', 'CWE ID', 'Affected Component', 'Description'])
                for vuln in report_data['vulnerabilities']:
                    writer.writerow([
                        vuln.id,
                        vuln.title,
                        vuln.severity.value,
                        vuln.cvss_score,
                        vuln.cwe_id,
                        vuln.affected_component,
                        vuln.description
                    ])
                writer.writerow([])
            
            # Write coverage
            if 'coverage' in report_data:
                writer.writerow(['Test Coverage Analysis'])
                writer.writerow(['Category', 'Total Tests', 'Passed Tests', 'Failed Tests', 'Coverage Percentage'])
                for category, coverage in report_data['coverage'].items():
                    writer.writerow([
                        category,
                        coverage.total_tests,
                        coverage.passed_tests,
                        coverage.failed_tests,
                        f"{coverage.coverage_percentage:.1f}%"
                    ])
                writer.writerow([])
            
            # Write posture assessment
            if 'posture' in report_data:
                writer.writerow(['Security Posture Assessment'])
                writer.writerow(['Overall Score', f"{report_data['posture'].overall_score:.1f}%"])
                writer.writerow(['Posture Level', report_data['posture'].posture_level.value])
                writer.writerow(['Risk Level', report_data['posture'].risk_level])
                writer.writerow([])
                
                writer.writerow(['Compliance Status'])
                for standard, status in report_data['posture'].compliance_status.items():
                    writer.writerow([standard, 'Compliant' if status else 'Non-Compliant'])
                writer.writerow([])
            
            # Write remediation recommendations
            if 'remediation' in report_data:
                writer.writerow(['Remediation Recommendations'])
                writer.writerow(['ID', 'Title', 'Priority', 'Effort', 'Cost', 'Timeline', 'Description'])
                for rec in report_data['remediation']:
                    writer.writerow([
                        rec.id,
                        rec.title,
                        rec.priority,
                        rec.effort,
                        rec.cost,
                        rec.timeline,
                        rec.description
                    ])

def generate_detailed_security_report(test_results: Dict[str, Any], 
                                    base_url: str = "http://localhost:5000",
                                    include_vulnerabilities: bool = True,
                                    include_coverage: bool = True,
                                    include_posture: bool = True,
                                    include_remediation: bool = True) -> str:
    """Generate detailed security test report"""
    
    reporter = DetailedSecurityReporting(base_url)
    report_file = reporter.generate_comprehensive_report(
        test_results=test_results,
        include_vulnerabilities=include_vulnerabilities,
        include_coverage=include_coverage,
        include_posture=include_posture,
        include_remediation=include_remediation
    )
    
    return report_file

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Detailed Security Test Reporting")
    parser.add_argument("--test-results", required=True, help="Path to test results JSON file")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for testing")
    parser.add_argument("--include-vulnerabilities", action="store_true", default=True, help="Include vulnerability analysis")
    parser.add_argument("--include-coverage", action="store_true", default=True, help="Include coverage analysis")
    parser.add_argument("--include-posture", action="store_true", default=True, help="Include posture assessment")
    parser.add_argument("--include-remediation", action="store_true", default=True, help="Include remediation recommendations")
    
    args = parser.parse_args()
    
    # Load test results
    with open(args.test_results, 'r') as f:
        test_results = json.load(f)
    
    # Generate report
    report_file = generate_detailed_security_report(
        test_results=test_results,
        base_url=args.base_url,
        include_vulnerabilities=args.include_vulnerabilities,
        include_coverage=args.include_coverage,
        include_posture=args.include_posture,
        include_remediation=args.include_remediation
    )
    
    print(f"Detailed security report generated: {report_file}") 