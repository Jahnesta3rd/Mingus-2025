# Dependency Security Monitoring System Guide

## Overview

This guide provides comprehensive dependency security monitoring for MINGUS, covering Python package vulnerability scanning and JavaScript dependency security checks with automated vulnerability detection and risk assessment.

## 🔒 **Dependency Monitoring Components**

### **1. Python Dependency Scanner**
- **Multi-Format Support**: requirements.txt, setup.py, pyproject.toml, Pipfile, conda environment files
- **Vulnerability Detection**: CVE scanning, security advisories, known vulnerabilities
- **Risk Assessment**: Risk score calculation based on vulnerability severity
- **Compliance Monitoring**: Compliance score calculation for security standards
- **Automated Scanning**: Continuous dependency vulnerability monitoring

### **2. JavaScript Dependency Scanner**
- **Multi-Package Manager Support**: npm, yarn, pnpm, bower
- **Vulnerability Detection**: npm audit, Snyk integration, CVE scanning
- **Security Checks**: Known vulnerabilities, outdated packages, security advisories
- **Risk Assessment**: Risk score calculation for JavaScript dependencies
- **Compliance Monitoring**: Compliance score calculation for security standards

### **3. Dependency Types Supported**
- **Python Dependencies**: pip, conda, poetry, pipenv
- **JavaScript Dependencies**: npm, yarn, pnpm, bower
- **Node.js Dependencies**: npm packages, yarn packages
- **Package Managers**: Multiple package manager support
- **Lock Files**: Package lock file analysis

### **4. Vulnerability Sources**
- **CVE Database**: National Vulnerability Database (NVD)
- **Package Registries**: PyPI, npm registry
- **Security Advisories**: Vendor security advisories
- **Community Sources**: Security community reports
- **Automated Tools**: Safety, npm audit, Snyk, Trivy

## 🚀 **Usage**

### **Create Dependency Monitor**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

# Scan project dependencies
scans = monitor.scan_project_dependencies("./mingus-project")

for scan in scans:
    print(f"{scan.dependency_type.value.upper()} Dependencies:")
    print(f"  Scan Status: {scan.scan_status.value}")
    print(f"  Risk Score: {scan.risk_score}")
    print(f"  Compliance Score: {scan.compliance_score}")
    print(f"  Total Dependencies: {scan.total_dependencies}")
    print(f"  Vulnerable Dependencies: {scan.vulnerable_dependencies}")
    print(f"  Outdated Dependencies: {scan.outdated_dependencies}")
    print(f"  Vulnerabilities Found: {len(scan.vulnerabilities_found)}")
    
    for vuln in scan.vulnerabilities_found:
        print(f"    {vuln.package_name} {vuln.package_version}: {vuln.severity.value} - {vuln.description}")
```

### **Scan Python Dependencies**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

# Scan Python dependencies
scan = monitor.python_scanner.scan_python_dependencies("./mingus-project")

print(f"Python scan completed: {scan.scan_status.value}")
print(f"Risk Score: {scan.risk_score}")
print(f"Compliance Score: {scan.compliance_score}")
print(f"Total Dependencies: {scan.total_dependencies}")
print(f"Vulnerable Dependencies: {scan.vulnerable_dependencies}")
print(f"Outdated Dependencies: {scan.outdated_dependencies}")
print(f"Vulnerabilities Found: {len(scan.vulnerabilities_found)}")

for vuln in scan.vulnerabilities_found:
    print(f"  {vuln.package_name} {vuln.package_version}: {vuln.severity.value} - {vuln.description}")
    print(f"    CVE ID: {vuln.cve_id}")
    print(f"    CVSS Score: {vuln.cvss_score}")
    print(f"    Fixed Versions: {', '.join(vuln.fixed_versions)}")
    print(f"    Recommended Action: {vuln.recommended_action}")
```

### **Scan JavaScript Dependencies**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

# Scan JavaScript dependencies
scan = monitor.javascript_scanner.scan_javascript_dependencies("./mingus-project")

print(f"JavaScript scan completed: {scan.scan_status.value}")
print(f"Risk Score: {scan.risk_score}")
print(f"Compliance Score: {scan.compliance_score}")
print(f"Total Dependencies: {scan.total_dependencies}")
print(f"Vulnerable Dependencies: {scan.vulnerable_dependencies}")
print(f"Outdated Dependencies: {scan.outdated_dependencies}")
print(f"Vulnerabilities Found: {len(scan.vulnerabilities_found)}")

for vuln in scan.vulnerabilities_found:
    print(f"  {vuln.package_name} {vuln.package_version}: {vuln.severity.value} - {vuln.description}")
    print(f"    CVE ID: {vuln.cve_id}")
    print(f"    CVSS Score: {vuln.cvss_score}")
    print(f"    Fixed Versions: {', '.join(vuln.fixed_versions)}")
    print(f"    Recommended Action: {vuln.recommended_action}")
```

### **Get Dependency Statistics**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

# Get dependency statistics
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
```

## 🔧 **Command Line Usage**

### **Scan Python Dependencies**
```bash
# Scan Python dependencies
python security/dependency_monitoring.py \
    --scan-python \
    --project-path ./mingus-project \
    --base-url http://localhost:5000

# Example output:
# Scanning Python dependencies in ./mingus-project...
# Python scan completed: completed
# Risk Score: 7.5
# Compliance Score: 25.0
# Total Dependencies: 45
# Vulnerable Dependencies: 3
# Outdated Dependencies: 8
# Vulnerabilities Found: 5
#   requests 2.25.1: high - Security vulnerability in requests
#     CVE ID: CVE-2024-1234
#     CVSS Score: 7.5
#     Fixed Versions: 2.0.0
#     Recommended Action: Upgrade requests to version 2.0.0 or later
#   urllib3 1.26.5: medium - Security vulnerability in urllib3
#     CVE ID: CVE-2024-5678
#     CVSS Score: 5.0
#     Fixed Versions: 1.26.6
#     Recommended Action: Upgrade urllib3 to version 1.26.6 or later
```

### **Scan JavaScript Dependencies**
```bash
# Scan JavaScript dependencies
python security/dependency_monitoring.py \
    --scan-javascript \
    --project-path ./mingus-project \
    --base-url http://localhost:5000

# Example output:
# Scanning JavaScript dependencies in ./mingus-project...
# JavaScript scan completed: completed
# Risk Score: 8.0
# Compliance Score: 20.0
# Total Dependencies: 67
# Vulnerable Dependencies: 4
# Outdated Dependencies: 12
# Vulnerabilities Found: 6
#   lodash 4.17.20: high - Security vulnerability in lodash
#     CVE ID: CVE-2024-5678
#     CVSS Score: 8.0
#     Fixed Versions: 4.0.0
#     Recommended Action: Upgrade lodash to version 4.0.0 or later
#   jquery 3.5.1: medium - Security vulnerability in jquery
#     CVE ID: CVE-2024-9012
#     CVSS Score: 6.5
#     Fixed Versions: 3.6.0
#     Recommended Action: Upgrade jquery to version 3.6.0 or later
```

### **Scan All Dependencies**
```bash
# Scan all dependency types
python security/dependency_monitoring.py \
    --scan-all \
    --project-path ./mingus-project \
    --base-url http://localhost:5000

# Example output:
# Scanning all dependencies in ./mingus-project...
# 
# PYTHON Dependencies:
#   Scan Status: completed
#   Risk Score: 7.5
#   Compliance Score: 25.0
#   Total Dependencies: 45
#   Vulnerable Dependencies: 3
#   Outdated Dependencies: 8
#   Vulnerabilities Found: 5
#     requests 2.25.1: high - Security vulnerability in requests
#     urllib3 1.26.5: medium - Security vulnerability in urllib3
# 
# JAVASCRIPT Dependencies:
#   Scan Status: completed
#   Risk Score: 8.0
#   Compliance Score: 20.0
#   Total Dependencies: 67
#   Vulnerable Dependencies: 4
#   Outdated Dependencies: 12
#   Vulnerabilities Found: 6
#     lodash 4.17.20: high - Security vulnerability in lodash
#     jquery 3.5.1: medium - Security vulnerability in jquery
```

### **Show Dependency Statistics**
```bash
# Show dependency monitoring statistics
python security/dependency_monitoring.py \
    --statistics \
    --base-url http://localhost:5000

# Example output:
# Dependency Security Monitoring Statistics:
# Total Scans: 25
# Total Vulnerabilities: 15
# Total Dependencies: 112
# Vulnerable Dependencies: 7
# Outdated Dependencies: 20
# 
# Scan Types:
#   python: 12
#   javascript: 13
# 
# Vulnerability Severities:
#   high: 8
#   medium: 5
#   low: 2
# 
# Dependency Types:
#   python: 9
#   javascript: 6
# 
# Recent Scans:
#   PYTHON-SCAN-1703123456: python - completed (Risk: 7.5)
#   JS-SCAN-1703123457: javascript - completed (Risk: 8.0)
#   PYTHON-SCAN-1703123458: python - completed (Risk: 6.0)
```

## 📊 **Dependency Scanning Examples**

### **Python Dependencies Example**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

# Example Python project structure
python_project = {
    "requirements.txt": """
flask==2.0.1
requests==2.25.1
urllib3==1.26.5
cryptography==3.4.8
django==3.2.7
    """,
    "setup.py": """
from setuptools import setup, find_packages

setup(
    name="mingus-app",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "requests>=2.25.0",
        "cryptography>=3.4.0",
    ],
)
    """,
    "pyproject.toml": """
[tool.poetry]
name = "mingus-app"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.8"
flask = "^2.0.0"
requests = "^2.25.0"
cryptography = "^3.4.0"
    """
}

# Scan Python dependencies
scan = monitor.python_scanner.scan_python_dependencies("./python-project")

print("Python Dependencies Scan Results:")
print(f"Risk Score: {scan.risk_score}")
print(f"Compliance Score: {scan.compliance_score}")
print(f"Total Dependencies: {scan.total_dependencies}")
print(f"Vulnerable Dependencies: {scan.vulnerable_dependencies}")

for vuln in scan.vulnerabilities_found:
    print(f"\nVulnerability: {vuln.package_name} {vuln.package_version}")
    print(f"  Severity: {vuln.severity.value}")
    print(f"  CVE ID: {vuln.cve_id}")
    print(f"  CVSS Score: {vuln.cvss_score}")
    print(f"  Description: {vuln.description}")
    print(f"  Fixed Versions: {', '.join(vuln.fixed_versions)}")
    print(f"  Recommended Action: {vuln.recommended_action}")
    print(f"  Exploit Available: {vuln.exploit_available}")
    print(f"  Patch Available: {vuln.patch_available}")
```

### **JavaScript Dependencies Example**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

# Example JavaScript project structure
javascript_project = {
    "package.json": """
{
  "name": "mingus-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^17.0.2",
    "lodash": "^4.17.20",
    "jquery": "^3.5.1",
    "moment": "^2.29.1",
    "axios": "^0.21.1"
  },
  "devDependencies": {
    "webpack": "^5.0.0",
    "babel": "^7.0.0",
    "eslint": "^7.0.0"
  }
}
    """
}

# Scan JavaScript dependencies
scan = monitor.javascript_scanner.scan_javascript_dependencies("./javascript-project")

print("JavaScript Dependencies Scan Results:")
print(f"Risk Score: {scan.risk_score}")
print(f"Compliance Score: {scan.compliance_score}")
print(f"Total Dependencies: {scan.total_dependencies}")
print(f"Vulnerable Dependencies: {scan.vulnerable_dependencies}")

for vuln in scan.vulnerabilities_found:
    print(f"\nVulnerability: {vuln.package_name} {vuln.package_version}")
    print(f"  Severity: {vuln.severity.value}")
    print(f"  CVE ID: {vuln.cve_id}")
    print(f"  CVSS Score: {vuln.cvss_score}")
    print(f"  Description: {vuln.description}")
    print(f"  Fixed Versions: {', '.join(vuln.fixed_versions)}")
    print(f"  Recommended Action: {vuln.recommended_action}")
    print(f"  Exploit Available: {vuln.exploit_available}")
    print(f"  Patch Available: {vuln.patch_available}")
```

### **Comprehensive Dependency Analysis**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

def comprehensive_dependency_analysis(project_path: str):
    """Comprehensive dependency analysis"""
    try:
        print(f"Analyzing dependencies in {project_path}...")
        
        # 1. Scan all dependencies
        scans = monitor.scan_project_dependencies(project_path)
        
        # 2. Analyze results
        total_vulnerabilities = 0
        total_dependencies = 0
        critical_vulnerabilities = 0
        high_vulnerabilities = 0
        
        for scan in scans:
            print(f"\n{scan.dependency_type.value.upper()} Analysis:")
            print(f"  Total Dependencies: {scan.total_dependencies}")
            print(f"  Vulnerable Dependencies: {scan.vulnerable_dependencies}")
            print(f"  Outdated Dependencies: {scan.outdated_dependencies}")
            print(f"  Risk Score: {scan.risk_score}")
            print(f"  Compliance Score: {scan.compliance_score}")
            
            total_dependencies += scan.total_dependencies
            total_vulnerabilities += len(scan.vulnerabilities_found)
            
            for vuln in scan.vulnerabilities_found:
                if vuln.severity.value == "critical":
                    critical_vulnerabilities += 1
                elif vuln.severity.value == "high":
                    high_vulnerabilities += 1
        
        # 3. Generate summary
        print(f"\nComprehensive Dependency Analysis Summary:")
        print(f"  Total Dependencies Scanned: {total_dependencies}")
        print(f"  Total Vulnerabilities Found: {total_vulnerabilities}")
        print(f"  Critical Vulnerabilities: {critical_vulnerabilities}")
        print(f"  High Vulnerabilities: {high_vulnerabilities}")
        
        # 4. Risk assessment
        if critical_vulnerabilities > 0:
            print(f"  ⚠ CRITICAL: {critical_vulnerabilities} critical vulnerabilities found!")
        if high_vulnerabilities > 0:
            print(f"  ⚠ HIGH: {high_vulnerabilities} high severity vulnerabilities found!")
        
        if total_vulnerabilities == 0:
            print(f"  ✓ No vulnerabilities found - dependencies are secure!")
        else:
            print(f"  ⚠ {total_vulnerabilities} vulnerabilities need attention")
        
        # 5. Recommendations
        print(f"\nRecommendations:")
        if critical_vulnerabilities > 0:
            print(f"  - IMMEDIATE: Address {critical_vulnerabilities} critical vulnerabilities")
        if high_vulnerabilities > 0:
            print(f"  - URGENT: Address {high_vulnerabilities} high severity vulnerabilities")
        
        print(f"  - Regular: Implement automated dependency scanning")
        print(f"  - Continuous: Monitor for new vulnerabilities")
        print(f"  - Updates: Keep dependencies updated regularly")
    
    except Exception as e:
        print(f"Error in comprehensive dependency analysis: {e}")

# Run comprehensive analysis
comprehensive_dependency_analysis("./mingus-project")
```

## 🔧 **Configuration**

### **Dependency Monitoring Configuration**
```yaml
# dependency_monitoring_config.yml
base_url: "http://localhost:5000"

scanning:
  enabled: true
  scan_interval: 3600  # 1 hour
  scan_types:
    - "python"
    - "javascript"
    - "comprehensive"
  
  vulnerability_sources:
    python:
      - "https://pypi.org/pypi/{package}/json"
      - "https://safety-db.pypa.io/vulnerabilities.json"
      - "https://nvd.nist.gov/vuln/data-feeds"
    
    javascript:
      - "https://registry.npmjs.org/{package}"
      - "https://snyk.io/vuln/npm:{package}"
      - "https://nvd.nist.gov/vuln/data-feeds"
  
  scan_tools:
    python:
      safety: "safety check"
      bandit: "bandit -r ."
      snyk: "snyk test"
      pip-audit: "pip-audit"
      trivy: "trivy fs --security-checks vuln"
    
    javascript:
      npm: "npm audit"
      yarn: "yarn audit"
      snyk: "snyk test"
      trivy: "trivy fs --security-checks vuln"
      npm-check: "npm-check -u"

python_support:
  enabled: true
  dependency_files:
    - "requirements.txt"
    - "requirements/*.txt"
    - "setup.py"
    - "pyproject.toml"
    - "Pipfile"
    - "Pipfile.lock"
    - "poetry.lock"
    - "environment.yml"
    - "conda-env.yml"
  
  package_managers:
    pip: true
    conda: true
    poetry: true
    pipenv: true

javascript_support:
  enabled: true
  dependency_files:
    - "package.json"
    - "package-lock.json"
    - "yarn.lock"
    - "pnpm-lock.yaml"
    - "bower.json"
  
  package_managers:
    npm: true
    yarn: true
    pnpm: true
    bower: true

monitoring:
  enabled: true
  metrics_collection: true
  alerting: true
  
  thresholds:
    risk_score_critical: 8.0
    risk_score_high: 6.0
    risk_score_medium: 4.0
    compliance_score_minimum: 80.0
  
  alert_channels:
    email: true
    slack: true
    sms: true
    webhook: true

storage:
  scans_db_path: "/var/lib/mingus/dependency_scans.db"
  vulnerabilities_db_path: "/var/lib/mingus/dependency_vulnerabilities.db"
  backup_enabled: true
  backup_interval: 86400  # 24 hours
  retention_period: 365  # 1 year

performance:
  parallel_scanning: true
  caching: true
  optimization: true
```

### **Vulnerability Scanning Configuration**
```yaml
# vulnerability_scanning_config.yml
vulnerability_sources:
  cve_database:
    enabled: true
    sources:
      - "https://nvd.nist.gov/vuln/data-feeds"
      - "https://cve.mitre.org/data/downloads/"
      - "https://www.cvedetails.com/json-feed.php"
    update_interval: 3600  # 1 hour
  
  package_registries:
    python:
      - "https://pypi.org/pypi/{package}/json"
      - "https://safety-db.pypa.io/vulnerabilities.json"
    
    javascript:
      - "https://registry.npmjs.org/{package}"
      - "https://snyk.io/vuln/npm:{package}"
  
  security_advisories:
    enabled: true
    sources:
      - "https://github.com/advisories"
      - "https://security.gentoo.org/glsa/"
      - "https://www.debian.org/security/"

scanning_tools:
  python:
    safety:
      enabled: true
      command: "safety check"
      timeout: 300
    
    bandit:
      enabled: true
      command: "bandit -r ."
      timeout: 300
    
    snyk:
      enabled: true
      command: "snyk test"
      timeout: 300
    
    pip-audit:
      enabled: true
      command: "pip-audit"
      timeout: 300
    
    trivy:
      enabled: true
      command: "trivy fs --security-checks vuln"
      timeout: 300
  
  javascript:
    npm:
      enabled: true
      command: "npm audit"
      timeout: 300
    
    yarn:
      enabled: true
      command: "yarn audit"
      timeout: 300
    
    snyk:
      enabled: true
      command: "snyk test"
      timeout: 300
    
    trivy:
      enabled: true
      command: "trivy fs --security-checks vuln"
      timeout: 300

risk_assessment:
  severity_weights:
    critical: 10.0
    high: 7.5
    medium: 5.0
    low: 2.5
    info: 1.0
  
  cvss_thresholds:
    critical: 9.0
    high: 7.0
    medium: 4.0
    low: 0.1
  
  compliance_thresholds:
    minimum_score: 80.0
    target_score: 95.0
```

## 📊 **Dependency Monitoring Examples**

### **Automated Dependency Scanning**
```python
from security.dependency_monitoring import create_dependency_monitor
import schedule
import time

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

def automated_dependency_scanning():
    """Automated dependency scanning function"""
    try:
        print("Starting automated dependency scanning...")
        
        # Scan project dependencies
        scans = monitor.scan_project_dependencies("./mingus-project")
        
        total_vulnerabilities = 0
        critical_vulnerabilities = 0
        
        for scan in scans:
            total_vulnerabilities += len(scan.vulnerabilities_found)
            
            for vuln in scan.vulnerabilities_found:
                if vuln.severity.value == "critical":
                    critical_vulnerabilities += 1
        
        if critical_vulnerabilities > 0:
            print(f"⚠ CRITICAL: {critical_vulnerabilities} critical vulnerabilities found!")
            # Send critical alert
            send_critical_alert(critical_vulnerabilities)
        
        if total_vulnerabilities > 0:
            print(f"⚠ {total_vulnerabilities} vulnerabilities found")
            # Send vulnerability report
            send_vulnerability_report(scans)
        else:
            print("✓ No vulnerabilities found - dependencies are secure!")
    
    except Exception as e:
        print(f"Error in automated dependency scanning: {e}")

def send_critical_alert(critical_count: int):
    """Send critical vulnerability alert"""
    print(f"Sending critical alert for {critical_count} critical vulnerabilities")

def send_vulnerability_report(scans):
    """Send vulnerability report"""
    print("Sending vulnerability report")

# Schedule automated scanning
schedule.every().day.at("02:00").do(automated_dependency_scanning)
schedule.every().hour.do(automated_dependency_scanning)

# Run scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(60)
```

### **Dependency Vulnerability Dashboard**
```python
from security.dependency_monitoring import create_dependency_monitor
import matplotlib.pyplot as plt
import seaborn as sns

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

def generate_dependency_dashboard():
    """Generate dependency vulnerability dashboard"""
    try:
        # Get statistics
        stats = monitor.get_dependency_statistics()
        
        # Create dashboard
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Vulnerability Severities
        severities = list(stats.get('vulnerability_severities', {}).keys())
        severity_counts = list(stats.get('vulnerability_severities', {}).values())
        
        colors = ['red', 'orange', 'yellow', 'lightblue', 'green']
        ax1.pie(severity_counts, labels=severities, autopct='%1.1f%%', colors=colors)
        ax1.set_title('Vulnerability Severities Distribution')
        
        # Dependency Types
        dep_types = list(stats.get('dependency_types', {}).keys())
        dep_counts = list(stats.get('dependency_types', {}).values())
        
        ax2.bar(dep_types, dep_counts)
        ax2.set_title('Vulnerabilities by Dependency Type')
        ax2.set_ylabel('Count')
        
        # Scan Types
        scan_types = list(stats.get('scan_types', {}).keys())
        scan_counts = list(stats.get('scan_types', {}).values())
        
        ax3.bar(scan_types, scan_counts)
        ax3.set_title('Scans by Type')
        ax3.set_ylabel('Count')
        
        # Key Metrics
        metrics = ['Total Dependencies', 'Vulnerable Dependencies', 'Outdated Dependencies', 'Total Scans']
        values = [
            stats.get('total_dependencies', 0),
            stats.get('vulnerable_dependencies', 0),
            stats.get('outdated_dependencies', 0),
            stats.get('total_scans', 0)
        ]
        
        ax4.bar(metrics, values)
        ax4.set_title('Key Metrics')
        ax4.set_ylabel('Count')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('dependency_monitoring_dashboard.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("Dependency Monitoring Dashboard generated successfully!")
        
    except Exception as e:
        print(f"Error generating dependency dashboard: {e}")

# Generate dashboard
generate_dependency_dashboard()
```

### **Vulnerability Remediation Workflow**
```python
from security.dependency_monitoring import create_dependency_monitor

# Create dependency monitor
monitor = create_dependency_monitor(base_url="http://localhost:5000")

def vulnerability_remediation_workflow(project_path: str):
    """Vulnerability remediation workflow"""
    try:
        print(f"Starting vulnerability remediation workflow for {project_path}...")
        
        # 1. Scan for vulnerabilities
        print("Step 1: Scanning for vulnerabilities...")
        scans = monitor.scan_project_dependencies(project_path)
        
        # 2. Categorize vulnerabilities
        print("Step 2: Categorizing vulnerabilities...")
        critical_vulns = []
        high_vulns = []
        medium_vulns = []
        low_vulns = []
        
        for scan in scans:
            for vuln in scan.vulnerabilities_found:
                if vuln.severity.value == "critical":
                    critical_vulns.append(vuln)
                elif vuln.severity.value == "high":
                    high_vulns.append(vuln)
                elif vuln.severity.value == "medium":
                    medium_vulns.append(vuln)
                elif vuln.severity.value == "low":
                    low_vulns.append(vuln)
        
        # 3. Prioritize remediation
        print("Step 3: Prioritizing remediation...")
        print(f"  Critical vulnerabilities: {len(critical_vulns)}")
        print(f"  High vulnerabilities: {len(high_vulns)}")
        print(f"  Medium vulnerabilities: {len(medium_vulns)}")
        print(f"  Low vulnerabilities: {len(low_vulns)}")
        
        # 4. Generate remediation plan
        print("Step 4: Generating remediation plan...")
        
        if critical_vulns:
            print("\nCRITICAL VULNERABILITIES - IMMEDIATE ACTION REQUIRED:")
            for vuln in critical_vulns:
                print(f"  {vuln.package_name} {vuln.package_version}: {vuln.description}")
                print(f"    CVE: {vuln.cve_id}")
                print(f"    CVSS: {vuln.cvss_score}")
                print(f"    Action: {vuln.recommended_action}")
                print()
        
        if high_vulns:
            print("\nHIGH VULNERABILITIES - URGENT ACTION REQUIRED:")
            for vuln in high_vulns:
                print(f"  {vuln.package_name} {vuln.package_version}: {vuln.description}")
                print(f"    CVE: {vuln.cve_id}")
                print(f"    CVSS: {vuln.cvss_score}")
                print(f"    Action: {vuln.recommended_action}")
                print()
        
        if medium_vulns:
            print("\nMEDIUM VULNERABILITIES - SCHEDULED ACTION:")
            for vuln in medium_vulns:
                print(f"  {vuln.package_name} {vuln.package_version}: {vuln.description}")
                print(f"    CVE: {vuln.cve_id}")
                print(f"    CVSS: {vuln.cvss_score}")
                print(f"    Action: {vuln.recommended_action}")
                print()
        
        # 5. Generate update commands
        print("Step 5: Generating update commands...")
        
        python_updates = []
        javascript_updates = []
        
        for scan in scans:
            if scan.dependency_type.value == "python":
                for vuln in scan.vulnerabilities_found:
                    if vuln.fixed_versions:
                        python_updates.append(f"pip install {vuln.package_name}>={vuln.fixed_versions[0]}")
            elif scan.dependency_type.value == "javascript":
                for vuln in scan.vulnerabilities_found:
                    if vuln.fixed_versions:
                        javascript_updates.append(f"npm install {vuln.package_name}@{vuln.fixed_versions[0]}")
        
        if python_updates:
            print("\nPython Update Commands:")
            for cmd in python_updates:
                print(f"  {cmd}")
        
        if javascript_updates:
            print("\nJavaScript Update Commands:")
            for cmd in javascript_updates:
                print(f"  {cmd}")
        
        # 6. Verification plan
        print("\nStep 6: Verification Plan:")
        print("  - Run dependency scans after updates")
        print("  - Test application functionality")
        print("  - Verify vulnerability resolution")
        print("  - Update dependency lock files")
        
        print("\nVulnerability remediation workflow completed!")
    
    except Exception as e:
        print(f"Error in vulnerability remediation workflow: {e}")

# Run vulnerability remediation workflow
vulnerability_remediation_workflow("./mingus-project")
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Scan Issues**
```bash
# Check dependency monitoring configuration
cat security/dependency_monitoring_config.yml

# Verify scan tools availability
which safety
which bandit
which snyk
which npm
which yarn

# Check dependency monitoring database
sqlite3 /var/lib/mingus/dependency_scans.db ".tables"
sqlite3 /var/lib/mingus/dependency_scans.db "SELECT * FROM dependency_scans LIMIT 5;"
```

#### **Python Scanning Issues**
```bash
# Check Python dependency files
find . -name "requirements.txt" -o -name "setup.py" -o -name "pyproject.toml"

# Verify Python package managers
pip --version
conda --version
poetry --version

# Check Python scan tools
safety --version
bandit --version
pip-audit --version
```

#### **JavaScript Scanning Issues**
```bash
# Check JavaScript dependency files
find . -name "package.json" -o -name "yarn.lock" -o -name "bower.json"

# Verify JavaScript package managers
npm --version
yarn --version
pnpm --version

# Check JavaScript scan tools
npm audit --version
yarn audit --version
snyk --version
```

### **Performance Optimization**

#### **Dependency Monitoring Performance**
```python
# Optimize dependency monitoring performance
monitoring_optimization = {
    "parallel_scanning": True,
    "scan_caching": True,
    "database_optimization": True,
    "memory_optimization": True,
    "incremental_scanning": True
}
```

#### **Scanning Performance**
```python
# Optimize scanning performance
scanning_optimization = {
    "tool_parallelization": True,
    "result_caching": True,
    "vulnerability_cache": True,
    "scan_optimization": True,
    "resource_monitoring": True
}
```

## 📚 **Additional Resources**

### **Documentation**
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [Snyk Documentation](https://docs.snyk.io/)
- [Safety Documentation](https://pyup.io/safety/)

### **Tools**
- [Safety](https://pyup.io/safety/)
- [Bandit](https://bandit.readthedocs.io/)
- [Snyk](https://snyk.io/)
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [Trivy](https://trivy.dev/)

### **Standards**
- [ISO 27001](https://www.iso.org/isoiec-27001-information-security.html)
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CVE Database](https://cve.mitre.org/)

## 🎯 **Dependency Monitoring Benefits**

### **Automated Vulnerability Detection**
- **Continuous Monitoring**: Continuous dependency vulnerability monitoring
- **Automated Scanning**: Automatic detection of security vulnerabilities
- **Timely Updates**: Timely identification of vulnerable dependencies
- **Risk Reduction**: Reduction of security risks from dependencies

### **Comprehensive Coverage**
- **Multi-Language Support**: Support for Python and JavaScript dependencies
- **Multi-Package Manager**: Support for multiple package managers
- **Vulnerability Databases**: Integration with multiple vulnerability databases
- **Security Tools**: Integration with security scanning tools

### **Operational Efficiency**
- **Automated Processes**: Automated dependency scanning processes
- **Reduced Manual Work**: Reduction in manual security tasks
- **Faster Response**: Faster response to dependency vulnerabilities
- **Better Visibility**: Better visibility into dependency security posture

## 🔄 **Updates and Maintenance**

### **Dependency Monitoring Maintenance**

1. **Regular Updates**
   - Update vulnerability databases daily
   - Update scan tools weekly
   - Update dependency sources monthly
   - Update scanning procedures quarterly

2. **System Validation**
   - Validate scan results regularly
   - Validate vulnerability detection
   - Review false positive rates
   - Update scan thresholds

3. **Performance Monitoring**
   - Monitor dependency monitoring performance
   - Track scan success rates
   - Analyze scan coverage
   - Optimize monitoring efficiency

### **Continuous Improvement**

1. **System Enhancement**
   - Add new scan tools
   - Enhance vulnerability detection
   - Improve dependency parsing
   - Add new package manager support

2. **Integration Enhancement**
   - Add new data sources
   - Enhance vulnerability databases
   - Improve compliance monitoring
   - Add new scanning tools

3. **Training and Awareness**
   - Regular team training
   - Dependency monitoring training
   - Security awareness training
   - Scanning procedure training

---

*This comprehensive dependency security monitoring system guide ensures that MINGUS provides automated vulnerability scanning and security checks for Python and JavaScript dependencies with comprehensive risk assessment and compliance monitoring.* 