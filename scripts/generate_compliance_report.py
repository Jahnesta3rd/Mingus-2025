#!/usr/bin/env python3
"""
Security Compliance Report Generator
Generates comprehensive compliance reports for security testing results
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ComplianceReportGenerator:
    """Generate comprehensive security compliance reports"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()
        self.compliance_data = {}
        self.report_data = {}
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default compliance configuration"""
        return {
            'compliance_frameworks': [
                'OWASP_TOP_10',
                'NIST_CYBERSECURITY_FRAMEWORK',
                'ISO_27001',
                'SOC_2',
                'GDPR',
                'CCPA'
            ],
            'report_formats': ['html', 'pdf', 'json'],
            'include_recommendations': True,
            'include_remediation_plan': True,
            'compliance_threshold': 85.0
        }
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        print("📋 Generating Security Compliance Report...")
        
        # Load security test results
        self._load_security_test_results()
        
        # Analyze compliance against frameworks
        compliance_results = self._analyze_compliance()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create remediation plan
        remediation_plan = self._create_remediation_plan()
        
        # Compile final report
        self.report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'compliance_frameworks': self.config['compliance_frameworks'],
                'compliance_threshold': self.config['compliance_threshold'],
                'report_version': '1.0'
            },
            'executive_summary': self._generate_executive_summary(),
            'compliance_results': compliance_results,
            'security_test_results': self.compliance_data.get('security_tests', {}),
            'recommendations': recommendations,
            'remediation_plan': remediation_plan,
            'risk_assessment': self._assess_risk_levels(),
            'compliance_score': self._calculate_compliance_score(compliance_results)
        }
        
        # Save reports
        self._save_reports()
        
        return self.report_data
    
    def _load_security_test_results(self):
        """Load security test results from files"""
        reports_dir = Path('reports')
        
        # Load security test summary
        summary_file = reports_dir / 'security_test_summary.json'
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                self.compliance_data['security_tests'] = json.load(f)
        
        # Load static analysis results
        bandit_file = reports_dir / 'bandit_results.json'
        if bandit_file.exists():
            with open(bandit_file, 'r') as f:
                self.compliance_data['static_analysis'] = json.load(f)
        
        # Load dependency scan results
        safety_file = reports_dir / 'safety_results.json'
        if safety_file.exists():
            with open(safety_file, 'r') as f:
                self.compliance_data['dependency_scan'] = json.load(f)
    
    def _analyze_compliance(self) -> Dict[str, Any]:
        """Analyze compliance against security frameworks"""
        compliance_results = {}
        
        for framework in self.config['compliance_frameworks']:
            compliance_results[framework] = self._analyze_framework_compliance(framework)
        
        return compliance_results
    
    def _analyze_framework_compliance(self, framework: str) -> Dict[str, Any]:
        """Analyze compliance for a specific framework"""
        if framework == 'OWASP_TOP_10':
            return self._analyze_owasp_compliance()
        elif framework == 'NIST_CYBERSECURITY_FRAMEWORK':
            return self._analyze_nist_compliance()
        elif framework == 'ISO_27001':
            return self._analyze_iso27001_compliance()
        elif framework == 'SOC_2':
            return self._analyze_soc2_compliance()
        elif framework == 'GDPR':
            return self._analyze_gdpr_compliance()
        elif framework == 'CCPA':
            return self._analyze_ccpa_compliance()
        else:
            return {
                'compliant': False,
                'score': 0.0,
                'findings': [f'Framework {framework} not implemented'],
                'recommendations': [f'Implement {framework} compliance analysis']
            }
    
    def _analyze_owasp_compliance(self) -> Dict[str, Any]:
        """Analyze OWASP Top 10 compliance"""
        findings = []
        recommendations = []
        score = 100.0
        
        security_tests = self.compliance_data.get('security_tests', {})
        test_results = security_tests.get('test_results', {})
        
        # A01:2021 - Broken Access Control
        if not test_results.get('csrf_protection', {}).get('success', False):
            findings.append("A01:2021 - CSRF protection not properly implemented")
            recommendations.append("Implement proper CSRF token validation")
            score -= 15.0
        
        # A02:2021 - Cryptographic Failures
        if not test_results.get('jwt_security', {}).get('success', False):
            findings.append("A02:2021 - JWT security not properly implemented")
            recommendations.append("Implement secure JWT handling with proper validation")
            score -= 15.0
        
        # A03:2021 - Injection
        if not test_results.get('input_validation', {}).get('success', False):
            findings.append("A03:2021 - Input validation not properly implemented")
            recommendations.append("Implement comprehensive input validation and sanitization")
            score -= 20.0
        
        # A04:2021 - Insecure Design
        if not test_results.get('security_headers', {}).get('success', False):
            findings.append("A04:2021 - Security headers not properly configured")
            recommendations.append("Configure proper security headers")
            score -= 10.0
        
        # A05:2021 - Security Misconfiguration
        if not test_results.get('penetration_tests', {}).get('success', False):
            findings.append("A05:2021 - Security misconfigurations detected")
            recommendations.append("Review and fix security configurations")
            score -= 10.0
        
        # A06:2021 - Vulnerable and Outdated Components
        dependency_scan = self.compliance_data.get('dependency_scan', {})
        if dependency_scan.get('high_severity_vulns', 0) > 0:
            findings.append("A06:2021 - Vulnerable dependencies detected")
            recommendations.append("Update vulnerable dependencies")
            score -= 15.0
        
        # A07:2021 - Identification and Authentication Failures
        if not test_results.get('rate_limiting', {}).get('success', False):
            findings.append("A07:2021 - Rate limiting not properly implemented")
            recommendations.append("Implement proper rate limiting for authentication")
            score -= 10.0
        
        # A08:2021 - Software and Data Integrity Failures
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("A08:2021 - Data integrity protection not implemented")
            recommendations.append("Implement data integrity checks and protection")
            score -= 5.0
        
        return {
            'compliant': score >= self.config['compliance_threshold'],
            'score': max(0.0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _analyze_nist_compliance(self) -> Dict[str, Any]:
        """Analyze NIST Cybersecurity Framework compliance"""
        findings = []
        recommendations = []
        score = 100.0
        
        security_tests = self.compliance_data.get('security_tests', {})
        test_results = security_tests.get('test_results', {})
        
        # IDENTIFY function
        if not test_results.get('input_validation', {}).get('success', False):
            findings.append("IDENTIFY - Asset vulnerabilities not properly identified")
            recommendations.append("Implement comprehensive vulnerability assessment")
            score -= 20.0
        
        # PROTECT function
        if not test_results.get('security_headers', {}).get('success', False):
            findings.append("PROTECT - Security controls not properly implemented")
            recommendations.append("Implement security controls and configurations")
            score -= 20.0
        
        # DETECT function
        if not test_results.get('security_monitoring', {}).get('success', False):
            findings.append("DETECT - Security monitoring not implemented")
            recommendations.append("Implement security monitoring and detection")
            score -= 20.0
        
        # RESPOND function
        if not test_results.get('rate_limiting', {}).get('success', False):
            findings.append("RESPOND - Incident response not properly configured")
            recommendations.append("Implement incident response procedures")
            score -= 20.0
        
        # RECOVER function
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("RECOVER - Data recovery procedures not implemented")
            recommendations.append("Implement data backup and recovery procedures")
            score -= 20.0
        
        return {
            'compliant': score >= self.config['compliance_threshold'],
            'score': max(0.0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _analyze_iso27001_compliance(self) -> Dict[str, Any]:
        """Analyze ISO 27001 compliance"""
        findings = []
        recommendations = []
        score = 100.0
        
        security_tests = self.compliance_data.get('security_tests', {})
        test_results = security_tests.get('test_results', {})
        
        # A.9 Access Control
        if not test_results.get('csrf_protection', {}).get('success', False):
            findings.append("A.9 - Access control not properly implemented")
            recommendations.append("Implement proper access control mechanisms")
            score -= 15.0
        
        # A.12 Operations Security
        if not test_results.get('security_headers', {}).get('success', False):
            findings.append("A.12 - Operations security not properly configured")
            recommendations.append("Configure operations security controls")
            score -= 15.0
        
        # A.13 Communications Security
        if not test_results.get('jwt_security', {}).get('success', False):
            findings.append("A.13 - Communications security not properly implemented")
            recommendations.append("Implement secure communications")
            score -= 15.0
        
        # A.14 System Acquisition, Development and Maintenance
        if not test_results.get('input_validation', {}).get('success', False):
            findings.append("A.14 - Secure development practices not followed")
            recommendations.append("Implement secure development practices")
            score -= 20.0
        
        # A.15 Supplier Relationships
        dependency_scan = self.compliance_data.get('dependency_scan', {})
        if dependency_scan.get('high_severity_vulns', 0) > 0:
            findings.append("A.15 - Supplier security not properly managed")
            recommendations.append("Manage supplier security requirements")
            score -= 10.0
        
        # A.16 Incident Management
        if not test_results.get('rate_limiting', {}).get('success', False):
            findings.append("A.16 - Incident management not properly implemented")
            recommendations.append("Implement incident management procedures")
            score -= 15.0
        
        # A.17 Business Continuity Management
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("A.17 - Business continuity not properly planned")
            recommendations.append("Implement business continuity planning")
            score -= 10.0
        
        return {
            'compliant': score >= self.config['compliance_threshold'],
            'score': max(0.0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _analyze_soc2_compliance(self) -> Dict[str, Any]:
        """Analyze SOC 2 compliance"""
        findings = []
        recommendations = []
        score = 100.0
        
        security_tests = self.compliance_data.get('security_tests', {})
        test_results = security_tests.get('test_results', {})
        
        # Security
        if not test_results.get('input_validation', {}).get('success', False):
            findings.append("Security - Input validation not properly implemented")
            recommendations.append("Implement comprehensive input validation")
            score -= 25.0
        
        # Availability
        if not test_results.get('rate_limiting', {}).get('success', False):
            findings.append("Availability - Rate limiting not properly implemented")
            recommendations.append("Implement rate limiting to prevent DoS")
            score -= 25.0
        
        # Processing Integrity
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("Processing Integrity - Data protection not implemented")
            recommendations.append("Implement data integrity checks")
            score -= 25.0
        
        # Confidentiality
        if not test_results.get('jwt_security', {}).get('success', False):
            findings.append("Confidentiality - Authentication not properly implemented")
            recommendations.append("Implement secure authentication")
            score -= 25.0
        
        return {
            'compliant': score >= self.config['compliance_threshold'],
            'score': max(0.0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _analyze_gdpr_compliance(self) -> Dict[str, Any]:
        """Analyze GDPR compliance"""
        findings = []
        recommendations = []
        score = 100.0
        
        security_tests = self.compliance_data.get('security_tests', {})
        test_results = security_tests.get('test_results', {})
        
        # Article 32 - Security of Processing
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("Article 32 - Data protection not properly implemented")
            recommendations.append("Implement appropriate data protection measures")
            score -= 30.0
        
        # Article 25 - Data Protection by Design
        if not test_results.get('input_validation', {}).get('success', False):
            findings.append("Article 25 - Privacy by design not implemented")
            recommendations.append("Implement privacy by design principles")
            score -= 25.0
        
        # Article 32 - Breach Notification
        if not test_results.get('security_monitoring', {}).get('success', False):
            findings.append("Article 32 - Breach detection not implemented")
            recommendations.append("Implement breach detection and notification")
            score -= 25.0
        
        # Article 17 - Right to Erasure
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("Article 17 - Data deletion not properly implemented")
            recommendations.append("Implement proper data deletion procedures")
            score -= 20.0
        
        return {
            'compliant': score >= self.config['compliance_threshold'],
            'score': max(0.0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _analyze_ccpa_compliance(self) -> Dict[str, Any]:
        """Analyze CCPA compliance"""
        findings = []
        recommendations = []
        score = 100.0
        
        security_tests = self.compliance_data.get('security_tests', {})
        test_results = security_tests.get('test_results', {})
        
        # Section 1798.100 - Consumer Rights
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("Section 1798.100 - Consumer data rights not protected")
            recommendations.append("Implement consumer data rights protection")
            score -= 40.0
        
        # Section 1798.105 - Right to Deletion
        if not test_results.get('data_protection', {}).get('success', False):
            findings.append("Section 1798.105 - Data deletion not implemented")
            recommendations.append("Implement data deletion capabilities")
            score -= 30.0
        
        # Section 1798.110 - Right to Know
        if not test_results.get('security_monitoring', {}).get('success', False):
            findings.append("Section 1798.110 - Data transparency not implemented")
            recommendations.append("Implement data transparency and logging")
            score -= 30.0
        
        return {
            'compliant': score >= self.config['compliance_threshold'],
            'score': max(0.0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate security recommendations"""
        recommendations = []
        
        # Collect all recommendations from compliance analysis
        compliance_results = self.report_data.get('compliance_results', {})
        for framework, result in compliance_results.items():
            for rec in result.get('recommendations', []):
                recommendations.append({
                    'framework': framework,
                    'recommendation': rec,
                    'priority': 'HIGH' if framework in ['OWASP_TOP_10', 'NIST_CYBERSECURITY_FRAMEWORK'] else 'MEDIUM',
                    'effort': 'MEDIUM'
                })
        
        # Remove duplicates
        unique_recommendations = []
        seen = set()
        for rec in recommendations:
            if rec['recommendation'] not in seen:
                unique_recommendations.append(rec)
                seen.add(rec['recommendation'])
        
        return unique_recommendations
    
    def _create_remediation_plan(self) -> Dict[str, Any]:
        """Create remediation plan for security issues"""
        plan = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'timeline': {
                'immediate': '1-7 days',
                'short_term': '1-4 weeks',
                'long_term': '1-6 months'
            }
        }
        
        # Categorize recommendations by priority and effort
        recommendations = self.report_data.get('recommendations', [])
        
        for rec in recommendations:
            if rec['priority'] == 'HIGH':
                plan['immediate_actions'].append(rec)
            elif rec['priority'] == 'MEDIUM':
                plan['short_term_actions'].append(rec)
            else:
                plan['long_term_actions'].append(rec)
        
        return plan
    
    def _assess_risk_levels(self) -> Dict[str, Any]:
        """Assess overall risk levels"""
        security_tests = self.compliance_data.get('security_tests', {})
        test_results = security_tests.get('test_results', {})
        
        risk_factors = {
            'authentication': 0,
            'authorization': 0,
            'input_validation': 0,
            'data_protection': 0,
            'configuration': 0,
            'dependencies': 0
        }
        
        # Assess each risk factor
        if not test_results.get('jwt_security', {}).get('success', False):
            risk_factors['authentication'] += 3
        
        if not test_results.get('csrf_protection', {}).get('success', False):
            risk_factors['authorization'] += 3
        
        if not test_results.get('input_validation', {}).get('success', False):
            risk_factors['input_validation'] += 4
        
        if not test_results.get('data_protection', {}).get('success', False):
            risk_factors['data_protection'] += 3
        
        if not test_results.get('security_headers', {}).get('success', False):
            risk_factors['configuration'] += 2
        
        dependency_scan = self.compliance_data.get('dependency_scan', {})
        if dependency_scan.get('high_severity_vulns', 0) > 0:
            risk_factors['dependencies'] += dependency_scan['high_severity_vulns']
        
        # Calculate overall risk level
        total_risk = sum(risk_factors.values())
        
        if total_risk >= 15:
            risk_level = 'CRITICAL'
        elif total_risk >= 10:
            risk_level = 'HIGH'
        elif total_risk >= 5:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'overall_risk_level': risk_level,
            'risk_factors': risk_factors,
            'total_risk_score': total_risk
        }
    
    def _calculate_compliance_score(self, compliance_results: Dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        if not compliance_results:
            return 0.0
        
        total_score = 0.0
        framework_count = len(compliance_results)
        
        for framework, result in compliance_results.items():
            total_score += result.get('score', 0.0)
        
        return total_score / framework_count if framework_count > 0 else 0.0
    
    def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary"""
        compliance_score = self.report_data.get('compliance_score', 0.0)
        risk_assessment = self.report_data.get('risk_assessment', {})
        
        return {
            'overall_compliance_score': compliance_score,
            'compliance_status': 'COMPLIANT' if compliance_score >= self.config['compliance_threshold'] else 'NON_COMPLIANT',
            'risk_level': risk_assessment.get('overall_risk_level', 'UNKNOWN'),
            'critical_findings': len([f for f in self.report_data.get('compliance_results', {}).values() if not f.get('compliant', False)]),
            'total_recommendations': len(self.report_data.get('recommendations', [])),
            'next_steps': self._generate_next_steps()
        }
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for compliance improvement"""
        next_steps = []
        
        compliance_score = self.report_data.get('compliance_score', 0.0)
        
        if compliance_score < self.config['compliance_threshold']:
            next_steps.append("Address critical security findings immediately")
            next_steps.append("Implement high-priority recommendations")
            next_steps.append("Schedule security review with stakeholders")
        
        next_steps.append("Establish regular security testing schedule")
        next_steps.append("Implement continuous monitoring")
        next_steps.append("Train development team on security best practices")
        
        return next_steps
    
    def _save_reports(self):
        """Save compliance reports in various formats"""
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        with open(reports_dir / 'compliance_report.json', 'w') as f:
            json.dump(self.report_data, f, indent=2)
        
        # Save compliance status
        compliance_status = {
            'compliant': self.report_data['executive_summary']['compliance_status'] == 'COMPLIANT',
            'score': self.report_data['compliance_score'],
            'risk_level': self.report_data['risk_assessment']['overall_risk_level'],
            'timestamp': datetime.now().isoformat()
        }
        
        with open(reports_dir / 'compliance_status.json', 'w') as f:
            json.dump(compliance_status, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report()
        
        # Generate markdown report
        self._generate_markdown_report()
        
        print(f"📄 Compliance reports saved to: {reports_dir.absolute()}")
    
    def _generate_html_report(self):
        """Generate HTML compliance report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Compliance Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .framework {{ margin: 20px 0; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; }}
        .compliant {{ border-left: 5px solid #28a745; }}
        .non-compliant {{ border-left: 5px solid #dc3545; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        .high-score {{ color: #28a745; }}
        .medium-score {{ color: #ffc107; }}
        .low-score {{ color: #dc3545; }}
        .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .risk-assessment {{ background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Security Compliance Report</h1>
        <p><strong>Generated:</strong> {self.report_data['metadata']['generated_at']}</p>
        <p><strong>Compliance Threshold:</strong> {self.report_data['metadata']['compliance_threshold']}%</p>
    </div>
    
    <div class="summary">
        <h2>📊 Executive Summary</h2>
        <p><strong>Overall Compliance Score:</strong> 
           <span class="score {'high-score' if self.report_data['compliance_score'] >= 85 else 'medium-score' if self.report_data['compliance_score'] >= 70 else 'low-score'}">
               {self.report_data['compliance_score']:.1f}%
           </span>
        </p>
        <p><strong>Compliance Status:</strong> {self.report_data['executive_summary']['compliance_status']}</p>
        <p><strong>Risk Level:</strong> {self.report_data['risk_assessment']['overall_risk_level']}</p>
        <p><strong>Critical Findings:</strong> {self.report_data['executive_summary']['critical_findings']}</p>
        <p><strong>Total Recommendations:</strong> {self.report_data['executive_summary']['total_recommendations']}</p>
    </div>
    
    <div class="risk-assessment">
        <h2>⚠️ Risk Assessment</h2>
        <p><strong>Overall Risk Level:</strong> {self.report_data['risk_assessment']['overall_risk_level']}</p>
        <p><strong>Total Risk Score:</strong> {self.report_data['risk_assessment']['total_risk_score']}</p>
        <h3>Risk Factors:</h3>
        <ul>
"""
        
        for factor, score in self.report_data['risk_assessment']['risk_factors'].items():
            html_content += f"            <li><strong>{factor.replace('_', ' ').title()}:</strong> {score}</li>\n"
        
        html_content += """
        </ul>
    </div>
    
    <div class="framework-results">
        <h2>🏛️ Compliance Framework Results</h2>
"""
        
        for framework, result in self.report_data['compliance_results'].items():
            status_class = 'compliant' if result['compliant'] else 'non-compliant'
            score_class = 'high-score' if result['score'] >= 85 else 'medium-score' if result['score'] >= 70 else 'low-score'
            
            html_content += f"""
        <div class="framework {status_class}">
            <h3>{framework.replace('_', ' ').title()}</h3>
            <p><strong>Score:</strong> <span class="{score_class}">{result['score']:.1f}%</span></p>
            <p><strong>Status:</strong> {'✅ COMPLIANT' if result['compliant'] else '❌ NON-COMPLIANT'}</p>
            
            {f'<h4>Findings:</h4><ul>' + ''.join([f'<li>{finding}</li>' for finding in result['findings']]) + '</ul>' if result['findings'] else ''}
            
            {f'<h4>Recommendations:</h4><ul>' + ''.join([f'<li>{rec}</li>' for rec in result['recommendations']]) + '</ul>' if result['recommendations'] else ''}
        </div>
"""
        
        html_content += """
    </div>
    
    <div class="recommendations">
        <h2>📋 Recommendations</h2>
        <h3>Immediate Actions (1-7 days)</h3>
        <ul>
"""
        
        for action in self.report_data['remediation_plan']['immediate_actions']:
            html_content += f"            <li><strong>{action['framework']}:</strong> {action['recommendation']}</li>\n"
        
        html_content += """
        </ul>
        
        <h3>Short-term Actions (1-4 weeks)</h3>
        <ul>
"""
        
        for action in self.report_data['remediation_plan']['short_term_actions']:
            html_content += f"            <li><strong>{action['framework']}:</strong> {action['recommendation']}</li>\n"
        
        html_content += """
        </ul>
        
        <h3>Long-term Actions (1-6 months)</h3>
        <ul>
"""
        
        for action in self.report_data['remediation_plan']['long_term_actions']:
            html_content += f"            <li><strong>{action['framework']}:</strong> {action['recommendation']}</li>\n"
        
        html_content += """
        </ul>
    </div>
    
    <div class="next-steps">
        <h2>🎯 Next Steps</h2>
        <ul>
"""
        
        for step in self.report_data['executive_summary']['next_steps']:
            html_content += f"            <li>{step}</li>\n"
        
        html_content += """
        </ul>
    </div>
</body>
</html>
"""
        
        with open('reports/compliance_report.html', 'w') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self):
        """Generate markdown compliance report"""
        markdown_content = f"""# Security Compliance Report

**Generated:** {self.report_data['metadata']['generated_at']}  
**Compliance Threshold:** {self.report_data['metadata']['compliance_threshold']}%

## Executive Summary

- **Overall Compliance Score:** {self.report_data['compliance_score']:.1f}%
- **Compliance Status:** {self.report_data['executive_summary']['compliance_status']}
- **Risk Level:** {self.report_data['risk_assessment']['overall_risk_level']}
- **Critical Findings:** {self.report_data['executive_summary']['critical_findings']}
- **Total Recommendations:** {self.report_data['executive_summary']['total_recommendations']}

## Risk Assessment

**Overall Risk Level:** {self.report_data['risk_assessment']['overall_risk_level']}  
**Total Risk Score:** {self.report_data['risk_assessment']['total_risk_score']}

### Risk Factors

"""
        
        for factor, score in self.report_data['risk_assessment']['risk_factors'].items():
            markdown_content += f"- **{factor.replace('_', ' ').title()}:** {score}\n"
        
        markdown_content += "\n## Compliance Framework Results\n\n"
        
        for framework, result in self.report_data['compliance_results'].items():
            status_icon = "✅" if result['compliant'] else "❌"
            markdown_content += f"### {framework.replace('_', ' ').title()}\n"
            markdown_content += f"**Score:** {result['score']:.1f}%  \n"
            markdown_content += f"**Status:** {status_icon} {'COMPLIANT' if result['compliant'] else 'NON-COMPLIANT'}\n\n"
            
            if result['findings']:
                markdown_content += "**Findings:**\n"
                for finding in result['findings']:
                    markdown_content += f"- {finding}\n"
                markdown_content += "\n"
            
            if result['recommendations']:
                markdown_content += "**Recommendations:**\n"
                for rec in result['recommendations']:
                    markdown_content += f"- {rec}\n"
                markdown_content += "\n"
        
        markdown_content += "## Recommendations\n\n"
        
        markdown_content += "### Immediate Actions (1-7 days)\n"
        for action in self.report_data['remediation_plan']['immediate_actions']:
            markdown_content += f"- **{action['framework']}:** {action['recommendation']}\n"
        
        markdown_content += "\n### Short-term Actions (1-4 weeks)\n"
        for action in self.report_data['remediation_plan']['short_term_actions']:
            markdown_content += f"- **{action['framework']}:** {action['recommendation']}\n"
        
        markdown_content += "\n### Long-term Actions (1-6 months)\n"
        for action in self.report_data['remediation_plan']['long_term_actions']:
            markdown_content += f"- **{action['framework']}:** {action['recommendation']}\n"
        
        markdown_content += "\n## Next Steps\n\n"
        for step in self.report_data['executive_summary']['next_steps']:
            markdown_content += f"- {step}\n"
        
        with open('reports/compliance_report.md', 'w') as f:
            f.write(markdown_content)


def main():
    """Main entry point for compliance report generator"""
    parser = argparse.ArgumentParser(description='Generate security compliance reports')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--output-format', choices=['html', 'json', 'markdown', 'all'], 
                       default='all', help='Output format for reports')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Create and run compliance report generator
    generator = ComplianceReportGenerator(config)
    report_data = generator.generate_compliance_report()
    
    # Check compliance status
    if report_data['executive_summary']['compliance_status'] == 'COMPLIANT':
        print("✅ Compliance check passed")
        sys.exit(0)
    else:
        print("❌ Compliance check failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
