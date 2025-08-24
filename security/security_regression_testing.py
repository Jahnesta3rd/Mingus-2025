"""
Security Regression Testing for MINGUS
Automated security test suite with continuous testing and CI/CD integration
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

class RegressionTestType(Enum):
    """Types of security regression tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"
    PERFORMANCE = "performance"
    PENETRATION = "penetration"
    COMPLIANCE = "compliance"

class RegressionTestStatus(Enum):
    """Regression test status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"

class RegressionTestSeverity(Enum):
    """Regression test severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class RegressionTest:
    """Security regression test structure"""
    test_id: str
    name: str
    test_type: RegressionTestType
    severity: RegressionTestSeverity
    description: str
    test_function: Callable
    timeout: int = 300
    retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    baseline_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RegressionTestResult:
    """Regression test result structure"""
    test_id: str
    test_name: str
    status: RegressionTestStatus
    severity: RegressionTestSeverity
    execution_time: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    baseline_comparison: Dict[str, Any] = field(default_factory=dict)

class AutomatedSecurityTestSuite:
    """Automated security test suite for regression testing"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests = {}
        self.results = {}
        self.baseline_data = {}
        self._load_baseline_data()
    
    def _load_baseline_data(self):
        """Load baseline test data"""
        baseline_file = "security/baseline_test_data.json"
        if os.path.exists(baseline_file):
            try:
                with open(baseline_file, 'r') as f:
                    self.baseline_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading baseline data: {e}")
    
    def register_test(self, test: RegressionTest):
        """Register a security regression test"""
        self.tests[test.test_id] = test
        logger.info(f"Registered test: {test.name} ({test.test_id})")
    
    def run_test(self, test_id: str) -> RegressionTestResult:
        """Run a single security regression test"""
        if test_id not in self.tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.tests[test_id]
        start_time = time.time()
        
        try:
            logger.info(f"Running test: {test.name}")
            
            # Run the test function
            test_details = test.test_function()
            
            execution_time = time.time() - start_time
            
            # Determine test status
            if test_details.get("success", False):
                status = RegressionTestStatus.PASSED
                error_message = None
            else:
                status = RegressionTestStatus.FAILED
                error_message = test_details.get("error", "Test failed")
            
            # Compare with baseline
            baseline_comparison = self._compare_with_baseline(test_id, test_details)
            
            result = RegressionTestResult(
                test_id=test_id,
                test_name=test.name,
                status=status,
                severity=test.severity,
                execution_time=execution_time,
                timestamp=datetime.utcnow(),
                details=test_details,
                error_message=error_message,
                baseline_comparison=baseline_comparison
            )
            
            self.results[test_id] = result
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error running test {test_id}: {e}")
            
            result = RegressionTestResult(
                test_id=test_id,
                test_name=test.name,
                status=RegressionTestStatus.ERROR,
                severity=test.severity,
                execution_time=execution_time,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
            
            self.results[test_id] = result
            return result
    
    def run_test_suite(self, test_types: Optional[List[RegressionTestType]] = None) -> Dict[str, RegressionTestResult]:
        """Run a complete test suite"""
        logger.info("Starting security regression test suite")
        
        if test_types:
            tests_to_run = {tid: test for tid, test in self.tests.items() 
                           if test.test_type in test_types}
        else:
            tests_to_run = self.tests
        
        results = {}
        
        for test_id in tests_to_run:
            result = self.run_test(test_id)
            results[test_id] = result
            
            # Log result
            status_emoji = "✅" if result.status == RegressionTestStatus.PASSED else "❌"
            logger.info(f"{status_emoji} {result.test_name}: {result.status.value}")
        
        logger.info(f"Test suite completed. {len(results)} tests run.")
        return results
    
    def _compare_with_baseline(self, test_id: str, test_details: Dict[str, Any]) -> Dict[str, Any]:
        """Compare test results with baseline data"""
        if test_id not in self.baseline_data:
            return {"baseline_available": False}
        
        baseline = self.baseline_data[test_id]
        comparison = {"baseline_available": True}
        
        # Compare key metrics
        for key in ["execution_time", "vulnerabilities", "security_score"]:
            if key in test_details and key in baseline:
                current_value = test_details[key]
                baseline_value = baseline[key]
                
                if isinstance(current_value, (int, float)) and isinstance(baseline_value, (int, float)):
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100
                    comparison[f"{key}_change"] = change_percent
                    comparison[f"{key}_regression"] = change_percent > 10  # 10% threshold
        
        return comparison

class ContinuousSecurityTesting:
    """Continuous security testing system"""
    
    def __init__(self, test_suite: AutomatedSecurityTestSuite):
        self.test_suite = test_suite
        self.scheduler = schedule.Scheduler()
        self.running = False
        self.test_history = []
        self.alert_thresholds = {
            RegressionTestSeverity.CRITICAL: 0,
            RegressionTestSeverity.HIGH: 2,
            RegressionTestSeverity.MEDIUM: 5,
            RegressionTestSeverity.LOW: 10
        }
    
    def start_continuous_testing(self, interval_minutes: int = 60):
        """Start continuous security testing"""
        logger.info(f"Starting continuous security testing (interval: {interval_minutes} minutes)")
        
        # Schedule regular test runs
        self.scheduler.every(interval_minutes).minutes.do(self._run_scheduled_tests)
        
        # Schedule daily comprehensive tests
        self.scheduler.every().day.at("02:00").do(self._run_comprehensive_tests)
        
        # Schedule weekly deep security scans
        self.scheduler.every().sunday.at("03:00").do(self._run_deep_security_scan)
        
        self.running = True
        
        while self.running:
            self.scheduler.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_continuous_testing(self):
        """Stop continuous security testing"""
        logger.info("Stopping continuous security testing")
        self.running = False
    
    def _run_scheduled_tests(self):
        """Run scheduled security tests"""
        logger.info("Running scheduled security tests")
        
        # Run critical and high severity tests
        critical_tests = {tid: test for tid, test in self.test_suite.tests.items()
                         if test.severity in [RegressionTestSeverity.CRITICAL, RegressionTestSeverity.HIGH]}
        
        results = {}
        for test_id in critical_tests:
            result = self.test_suite.run_test(test_id)
            results[test_id] = result
        
        # Store in history
        test_run = {
            "timestamp": datetime.utcnow(),
            "type": "scheduled",
            "results": results
        }
        self.test_history.append(test_run)
        
        # Check for alerts
        self._check_alerts(results)
        
        return results
    
    def _run_comprehensive_tests(self):
        """Run comprehensive security tests"""
        logger.info("Running comprehensive security tests")
        
        # Run all tests
        results = self.test_suite.run_test_suite()
        
        # Store in history
        test_run = {
            "timestamp": datetime.utcnow(),
            "type": "comprehensive",
            "results": results
        }
        self.test_history.append(test_run)
        
        # Generate comprehensive report
        self._generate_comprehensive_report(results)
        
        return results
    
    def _run_deep_security_scan(self):
        """Run deep security scan"""
        logger.info("Running deep security scan")
        
        # Run all test types including penetration tests
        results = self.test_suite.run_test_suite([
            RegressionTestType.UNIT,
            RegressionTestType.INTEGRATION,
            RegressionTestType.END_TO_END,
            RegressionTestType.PERFORMANCE,
            RegressionTestType.PENETRATION,
            RegressionTestType.COMPLIANCE
        ])
        
        # Store in history
        test_run = {
            "timestamp": datetime.utcnow(),
            "type": "deep_scan",
            "results": results
        }
        self.test_history.append(test_run)
        
        # Generate deep scan report
        self._generate_deep_scan_report(results)
        
        return results
    
    def _check_alerts(self, results: Dict[str, RegressionTestResult]):
        """Check for security alerts"""
        failed_tests = {tid: result for tid, result in results.items()
                       if result.status == RegressionTestStatus.FAILED}
        
        for severity in RegressionTestSeverity:
            threshold = self.alert_thresholds.get(severity, 0)
            severity_failures = [result for result in failed_tests.values()
                               if result.severity == severity]
            
            if len(severity_failures) > threshold:
                self._send_security_alert(severity, severity_failures)
    
    def _send_security_alert(self, severity: RegressionTestSeverity, failed_tests: List[RegressionTestResult]):
        """Send security alert"""
        logger.warning(f"Security alert: {len(failed_tests)} {severity.value} tests failed")
        
        # Send email alert
        self._send_email_alert(severity, failed_tests)
        
        # Send Slack alert
        self._send_slack_alert(severity, failed_tests)
        
        # Send Discord alert
        self._send_discord_alert(severity, failed_tests)

class SecurityTestReporting:
    """Security test reporting system"""
    
    def __init__(self, test_suite: AutomatedSecurityTestSuite):
        self.test_suite = test_suite
        self.reports_dir = "security/reports"
        self._ensure_reports_directory()
    
    def _ensure_reports_directory(self):
        """Ensure reports directory exists"""
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_test_report(self, results: Dict[str, RegressionTestResult], report_type: str = "standard") -> str:
        """Generate security test report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.reports_dir}/security_test_report_{report_type}_{timestamp}.html"
        
        # Generate report data
        report_data = self._prepare_report_data(results)
        
        # Generate HTML report
        html_content = self._generate_html_report(report_data, report_type)
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Security test report generated: {report_file}")
        return report_file
    
    def generate_comprehensive_report(self, results: Dict[str, RegressionTestResult]) -> str:
        """Generate comprehensive security test report"""
        return self.generate_test_report(results, "comprehensive")
    
    def generate_deep_scan_report(self, results: Dict[str, RegressionTestResult]) -> str:
        """Generate deep security scan report"""
        return self.generate_test_report(results, "deep_scan")
    
    def _prepare_report_data(self, results: Dict[str, RegressionTestResult]) -> Dict[str, Any]:
        """Prepare data for report generation"""
        total_tests = len(results)
        passed_tests = len([r for r in results.values() if r.status == RegressionTestStatus.PASSED])
        failed_tests = len([r for r in results.values() if r.status == RegressionTestStatus.FAILED])
        error_tests = len([r for r in results.values() if r.status == RegressionTestStatus.ERROR])
        
        # Group by severity
        severity_stats = {}
        for severity in RegressionTestSeverity:
            severity_tests = [r for r in results.values() if r.severity == severity]
            severity_stats[severity.value] = {
                "total": len(severity_tests),
                "passed": len([r for r in severity_tests if r.status == RegressionTestStatus.PASSED]),
                "failed": len([r for r in severity_tests if r.status == RegressionTestStatus.FAILED]),
                "error": len([r for r in severity_tests if r.status == RegressionTestStatus.ERROR])
            }
        
        # Group by test type
        type_stats = {}
        for test_type in RegressionTestType:
            type_tests = [r for r in results.values() 
                         if self.test_suite.tests[r.test_id].test_type == test_type]
            type_stats[test_type.value] = {
                "total": len(type_tests),
                "passed": len([r for r in type_tests if r.status == RegressionTestStatus.PASSED]),
                "failed": len([r for r in type_tests if r.status == RegressionTestStatus.FAILED]),
                "error": len([r for r in type_tests if r.status == RegressionTestStatus.ERROR])
            }
        
        # Calculate security score
        security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "timestamp": datetime.utcnow(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "security_score": security_score,
            "severity_stats": severity_stats,
            "type_stats": type_stats,
            "results": results,
            "critical_issues": [r for r in results.values() 
                              if r.severity == RegressionTestSeverity.CRITICAL and 
                              r.status == RegressionTestStatus.FAILED]
        }
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Generate HTML security test report"""
        template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Test Report - {{ report_type.title() }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .summary-card h3 { margin: 0 0 10px 0; color: #333; }
        .summary-card .number { font-size: 2em; font-weight: bold; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .error { color: #ffc107; }
        .critical { color: #dc3545; }
        .high { color: #fd7e14; }
        .medium { color: #ffc107; }
        .low { color: #28a745; }
        .info { color: #17a2b8; }
        .security-score { font-size: 3em; font-weight: bold; text-align: center; margin: 20px 0; }
        .score-excellent { color: #28a745; }
        .score-good { color: #17a2b8; }
        .score-warning { color: #ffc107; }
        .score-danger { color: #dc3545; }
        .results-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .results-table th, .results-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .results-table th { background-color: #f8f9fa; font-weight: bold; }
        .status-passed { color: #28a745; font-weight: bold; }
        .status-failed { color: #dc3545; font-weight: bold; }
        .status-error { color: #ffc107; font-weight: bold; }
        .severity-critical { background-color: #f8d7da; }
        .severity-high { background-color: #fff3cd; }
        .severity-medium { background-color: #d1ecf1; }
        .severity-low { background-color: #d4edda; }
        .severity-info { background-color: #e2e3e5; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Security Test Report</h1>
            <p>{{ report_type.title() }} - {{ report_data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</p>
        </div>
        
        <div class="security-score score-{{ 'excellent' if report_data.security_score >= 90 else 'good' if report_data.security_score >= 70 else 'warning' if report_data.security_score >= 50 else 'danger' }}">
            {{ "%.1f"|format(report_data.security_score) }}%
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="number">{{ report_data.total_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="number passed">{{ report_data.passed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="number failed">{{ report_data.failed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Errors</h3>
                <div class="number error">{{ report_data.error_tests }}</div>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Execution Time</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {% for test_id, result in report_data.results.items() %}
                <tr class="severity-{{ result.severity.value }}">
                    <td>{{ result.test_name }}</td>
                    <td>{{ test_suite.tests[test_id].test_type.value }}</td>
                    <td class="{{ result.severity.value }}">{{ result.severity.value.title() }}</td>
                    <td class="status-{{ result.status.value }}">{{ result.status.value.title() }}</td>
                    <td>{{ "%.2f"|format(result.execution_time) }}s</td>
                    <td>
                        {% if result.error_message %}
                            <strong>Error:</strong> {{ result.error_message }}
                        {% endif %}
                        {% if result.baseline_comparison.baseline_available %}
                            <br><strong>Baseline:</strong> 
                            {% for key, value in result.baseline_comparison.items() %}
                                {% if key != 'baseline_available' %}
                                    {{ key }}: {{ value }}
                                {% endif %}
                            {% endfor %}
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        {% if report_data.critical_issues %}
        <h2>Critical Issues</h2>
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #721c24; margin-top: 0;">⚠️ Critical Security Issues Detected</h3>
            <ul>
                {% for issue in report_data.critical_issues %}
                <li><strong>{{ issue.test_name }}</strong>: {{ issue.error_message or 'Test failed' }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """
        
        template_obj = Template(template)
        return template_obj.render(
            report_type=report_type,
            report_data=report_data,
            test_suite=self.test_suite
        )

class CICDIntegration:
    """CI/CD pipeline integration for security testing"""
    
    def __init__(self, test_suite: AutomatedSecurityTestSuite):
        self.test_suite = test_suite
        self.reporting = SecurityTestReporting(test_suite)
        self.ci_configs = {
            "github": "security/.github/workflows/security-tests.yml",
            "gitlab": "security/.gitlab-ci.yml",
            "jenkins": "security/Jenkinsfile",
            "azure": "security/azure-pipelines.yml"
        }
    
    def generate_github_actions_config(self) -> str:
        """Generate GitHub Actions configuration for security testing"""
        config = """
name: Security Regression Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  security-tests:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r security/requirements.txt
    
    - name: Start application
      run: |
        python backend/app.py &
        sleep 30  # Wait for app to start
    
    - name: Run security regression tests
      run: |
        python security/security_regression_testing.py --ci-mode
    
    - name: Generate security report
      run: |
        python security/security_regression_testing.py --generate-report
    
    - name: Upload security report
      uses: actions/upload-artifact@v3
      with:
        name: security-test-report
        path: security/reports/
    
    - name: Security test results
      if: always()
      run: |
        python security/security_regression_testing.py --check-results
    
    - name: Notify on failure
      if: failure()
      run: |
        python security/security_regression_testing.py --send-alerts
        """
        
        return config
    
    def generate_gitlab_ci_config(self) -> str:
        """Generate GitLab CI configuration for security testing"""
        config = """
stages:
  - security-test

security_regression_tests:
  stage: security-test
  image: python:3.11
  before_script:
    - pip install -r requirements.txt
    - pip install -r security/requirements.txt
  script:
    - python backend/app.py &
    - sleep 30
    - python security/security_regression_testing.py --ci-mode
    - python security/security_regression_testing.py --generate-report
  artifacts:
    reports:
      junit: security/reports/junit.xml
    paths:
      - security/reports/
    expire_in: 1 week
  only:
    - main
    - develop
    - merge_requests
  except:
    - tags
        """
        
        return config
    
    def generate_jenkins_pipeline(self) -> str:
        """Generate Jenkins pipeline for security testing"""
        pipeline = """
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                sh 'python -m pip install --upgrade pip'
                sh 'pip install -r requirements.txt'
                sh 'pip install -r security/requirements.txt'
            }
        }
        
        stage('Start Application') {
            steps {
                sh 'python backend/app.py &'
                sh 'sleep 30'
            }
        }
        
        stage('Security Tests') {
            steps {
                sh 'python security/security_regression_testing.py --ci-mode'
            }
            post {
                always {
                    sh 'python security/security_regression_testing.py --generate-report'
                    archiveArtifacts artifacts: 'security/reports/*', fingerprint: true
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'security/reports',
                        reportFiles: '*.html',
                        reportName: 'Security Test Report'
                    ])
                }
            }
        }
        
        stage('Results Check') {
            steps {
                sh 'python security/security_regression_testing.py --check-results'
            }
        }
    }
    
    post {
        failure {
            sh 'python security/security_regression_testing.py --send-alerts'
        }
    }
}
        """
        
        return pipeline
    
    def setup_ci_integration(self, ci_platform: str = "github"):
        """Setup CI/CD integration for specified platform"""
        if ci_platform not in self.ci_configs:
            raise ValueError(f"Unsupported CI platform: {ci_platform}")
        
        config_path = self.ci_configs[ci_platform]
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        if ci_platform == "github":
            config_content = self.generate_github_actions_config()
        elif ci_platform == "gitlab":
            config_content = self.generate_gitlab_ci_config()
        elif ci_platform == "jenkins":
            config_content = self.generate_jenkins_pipeline()
        else:
            config_content = ""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"CI/CD configuration generated: {config_path}")
        return config_path

# Predefined security regression tests
def create_security_regression_tests(base_url: str) -> List[RegressionTest]:
    """Create predefined security regression tests"""
    tests = []
    
    # Authentication security tests
    def test_authentication_security():
        try:
            # Test login with valid credentials
            response = requests.post(f"{base_url}/api/auth/login", 
                                   json={"username": "test_user", "password": "test_pass"})
            
            if response.status_code == 200:
                token = response.json().get("token")
                
                # Test protected endpoint
                headers = {"Authorization": f"Bearer {token}"}
                protected_response = requests.get(f"{base_url}/api/protected", headers=headers)
                
                return {
                    "success": protected_response.status_code == 200,
                    "authentication_working": True,
                    "authorization_working": protected_response.status_code == 200
                }
            else:
                return {"success": False, "error": "Authentication failed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    tests.append(RegressionTest(
        test_id="auth_security",
        name="Authentication Security Test",
        test_type=RegressionTestType.UNIT,
        severity=RegressionTestSeverity.CRITICAL,
        description="Test authentication and authorization mechanisms",
        test_function=test_authentication_security
    ))
    
    # Input validation tests
    def test_input_validation():
        try:
            # Test SQL injection prevention
            sql_payloads = ["' OR '1'='1", "'; DROP TABLE users; --", "1' UNION SELECT * FROM users --"]
            
            for payload in sql_payloads:
                response = requests.post(f"{base_url}/api/search", 
                                       json={"query": payload})
                
                if response.status_code == 400 or "error" in response.text.lower():
                    continue
                else:
                    return {"success": False, "error": f"SQL injection vulnerability: {payload}"}
            
            # Test XSS prevention
            xss_payloads = ["<script>alert('XSS')</script>", "<img src=x onerror=alert('XSS')>"]
            
            for payload in xss_payloads:
                response = requests.post(f"{base_url}/api/comment", 
                                       json={"content": payload})
                
                if payload in response.text:
                    return {"success": False, "error": f"XSS vulnerability: {payload}"}
            
            return {"success": True, "input_validation_working": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    tests.append(RegressionTest(
        test_id="input_validation",
        name="Input Validation Security Test",
        test_type=RegressionTestType.UNIT,
        severity=RegressionTestSeverity.HIGH,
        description="Test input validation and sanitization",
        test_function=test_input_validation
    ))
    
    # Rate limiting tests
    def test_rate_limiting():
        try:
            # Send rapid requests
            for i in range(100):
                response = requests.get(f"{base_url}/api/users")
                
                if response.status_code == 429:  # Rate limited
                    return {"success": True, "rate_limiting_working": True}
                
                time.sleep(0.01)
            
            return {"success": False, "error": "Rate limiting not enforced"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    tests.append(RegressionTest(
        test_id="rate_limiting",
        name="Rate Limiting Security Test",
        test_type=RegressionTestType.INTEGRATION,
        severity=RegressionTestSeverity.MEDIUM,
        description="Test rate limiting mechanisms",
        test_function=test_rate_limiting
    ))
    
    # SSL/TLS tests
    def test_ssl_security():
        try:
            if base_url.startswith("https"):
                # Test SSL certificate
                response = requests.get(base_url, verify=True)
                
                if response.status_code == 200:
                    return {"success": True, "ssl_working": True}
                else:
                    return {"success": False, "error": "SSL certificate issues"}
            else:
                return {"success": False, "error": "HTTPS not enabled"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    tests.append(RegressionTest(
        test_id="ssl_security",
        name="SSL/TLS Security Test",
        test_type=RegressionTestType.INTEGRATION,
        severity=RegressionTestSeverity.HIGH,
        description="Test SSL/TLS configuration",
        test_function=test_ssl_security
    ))
    
    return tests

# Main security regression testing runner
class SecurityRegressionTestingRunner:
    """Main security regression testing runner"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_suite = AutomatedSecurityTestSuite(base_url)
        self.continuous_testing = ContinuousSecurityTesting(self.test_suite)
        self.reporting = SecurityTestReporting(self.test_suite)
        self.cicd = CICDIntegration(self.test_suite)
        
        # Register predefined tests
        self._register_predefined_tests()
    
    def _register_predefined_tests(self):
        """Register predefined security regression tests"""
        tests = create_security_regression_tests(self.base_url)
        for test in tests:
            self.test_suite.register_test(test)
    
    def run_regression_tests(self, test_types: Optional[List[RegressionTestType]] = None) -> Dict[str, RegressionTestResult]:
        """Run security regression tests"""
        return self.test_suite.run_test_suite(test_types)
    
    def start_continuous_testing(self, interval_minutes: int = 60):
        """Start continuous security testing"""
        self.continuous_testing.start_continuous_testing(interval_minutes)
    
    def generate_report(self, results: Dict[str, RegressionTestResult], report_type: str = "standard") -> str:
        """Generate security test report"""
        return self.reporting.generate_test_report(results, report_type)
    
    def setup_cicd(self, platform: str = "github") -> str:
        """Setup CI/CD integration"""
        return self.cicd.setup_ci_integration(platform)

def run_security_regression_testing(base_url: str = "http://localhost:5000", 
                                  test_types: Optional[List[RegressionTestType]] = None,
                                  generate_report: bool = True,
                                  ci_mode: bool = False) -> Dict[str, Any]:
    """Run comprehensive security regression testing"""
    
    runner = SecurityRegressionTestingRunner(base_url)
    
    # Run tests
    results = runner.run_regression_tests(test_types)
    
    # Generate report if requested
    report_file = None
    if generate_report:
        report_file = runner.generate_report(results)
    
    # Return results
    return {
        "results": results,
        "report_file": report_file,
        "summary": {
            "total_tests": len(results),
            "passed": len([r for r in results.values() if r.status == RegressionTestStatus.PASSED]),
            "failed": len([r for r in results.values() if r.status == RegressionTestStatus.FAILED]),
            "errors": len([r for r in results.values() if r.status == RegressionTestStatus.ERROR])
        }
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Regression Testing")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for testing")
    parser.add_argument("--test-types", nargs="+", choices=[t.value for t in RegressionTestType], 
                       help="Test types to run")
    parser.add_argument("--generate-report", action="store_true", help="Generate HTML report")
    parser.add_argument("--ci-mode", action="store_true", help="Run in CI mode")
    parser.add_argument("--continuous", action="store_true", help="Start continuous testing")
    parser.add_argument("--setup-cicd", choices=["github", "gitlab", "jenkins"], help="Setup CI/CD integration")
    
    args = parser.parse_args()
    
    if args.setup_cicd:
        runner = SecurityRegressionTestingRunner(args.base_url)
        config_file = runner.setup_cicd(args.setup_cicd)
        print(f"CI/CD configuration created: {config_file}")
    
    elif args.continuous:
        runner = SecurityRegressionTestingRunner(args.base_url)
        print("Starting continuous security testing...")
        runner.start_continuous_testing()
    
    else:
        test_types = [RegressionTestType(t) for t in args.test_types] if args.test_types else None
        results = run_security_regression_testing(
            base_url=args.base_url,
            test_types=test_types,
            generate_report=args.generate_report,
            ci_mode=args.ci_mode
        )
        
        print("Security Regression Testing Results:")
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Errors: {results['summary']['errors']}")
        
        if results['report_file']:
            print(f"Report generated: {results['report_file']}") 