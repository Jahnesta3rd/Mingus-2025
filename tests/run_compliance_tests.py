#!/usr/bin/env python3
"""
Plaid Compliance Test Runner

This script provides a dedicated test runner for comprehensive Plaid compliance testing
including GDPR compliance validation, PCI DSS compliance verification, data retention
policy testing, audit trail completeness, regulatory reporting accuracy, and user
consent management testing.
"""

import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest


class PlaidComplianceTestRunner:
    """Dedicated test runner for Plaid compliance tests"""
    
    def __init__(self, output_dir: str = "compliance_test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_all_compliance_tests(self, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run all Plaid compliance tests"""
        print("🛡️ Starting Plaid Compliance Test Suite...")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⏰ Timestamp: {self.timestamp}")
        print("-" * 80)
        
        test_results = {
            'timestamp': self.timestamp,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'test_categories': {},
            'compliance_metrics': {},
            'regulatory_metrics': {},
            'privacy_metrics': {},
            'security_metrics': {},
            'duration': 0
        }
        
        start_time = time.time()
        
        # Run compliance test categories
        test_categories = [
            ('gdpr_compliance', 'tests/test_plaid_compliance.py::TestGDPRComplianceValidation'),
            ('pci_dss_compliance', 'tests/test_plaid_compliance.py::TestPCIDSSComplianceVerification'),
            ('data_retention_policy', 'tests/test_plaid_compliance.py::TestDataRetentionPolicyTesting'),
            ('audit_trail_completeness', 'tests/test_plaid_compliance.py::TestAuditTrailCompleteness'),
            ('regulatory_reporting', 'tests/test_plaid_compliance.py::TestRegulatoryReportingAccuracy'),
            ('user_consent_management', 'tests/test_plaid_compliance.py::TestUserConsentManagementTesting')
        ]
        
        for category, test_path in test_categories:
            print(f"\n🔍 Running {category.replace('_', ' ').title()} tests...")
            category_results = self._run_compliance_test_category(category, test_path, verbose, parallel)
            test_results['test_categories'][category] = category_results
            
            # Update totals
            test_results['total_tests'] += category_results['total']
            test_results['passed'] += category_results['passed']
            test_results['failed'] += category_results['failed']
            test_results['skipped'] += category_results['skipped']
            test_results['errors'] += category_results['errors']
        
        test_results['duration'] = time.time() - start_time
        
        # Calculate compliance metrics
        test_results['compliance_metrics'] = self._calculate_compliance_metrics(test_results)
        
        # Generate reports
        self._generate_compliance_reports(test_results)
        
        # Print summary
        self._print_compliance_summary(test_results)
        
        return test_results
    
    def run_gdpr_compliance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run GDPR compliance validation tests only"""
        print("🇪🇺 Running GDPR Compliance Validation Tests...")
        return self._run_compliance_test_category(
            'gdpr_compliance', 
            'tests/test_plaid_compliance.py::TestGDPRComplianceValidation', 
            verbose
        )
    
    def run_pci_dss_compliance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run PCI DSS compliance verification tests only"""
        print("💳 Running PCI DSS Compliance Verification Tests...")
        return self._run_compliance_test_category(
            'pci_dss_compliance', 
            'tests/test_plaid_compliance.py::TestPCIDSSComplianceVerification', 
            verbose
        )
    
    def run_data_retention_policy_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run data retention policy testing only"""
        print("📋 Running Data Retention Policy Tests...")
        return self._run_compliance_test_category(
            'data_retention_policy', 
            'tests/test_plaid_compliance.py::TestDataRetentionPolicyTesting', 
            verbose
        )
    
    def run_audit_trail_completeness_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run audit trail completeness tests only"""
        print("📊 Running Audit Trail Completeness Tests...")
        return self._run_compliance_test_category(
            'audit_trail_completeness', 
            'tests/test_plaid_compliance.py::TestAuditTrailCompleteness', 
            verbose
        )
    
    def run_regulatory_reporting_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run regulatory reporting accuracy tests only"""
        print("📈 Running Regulatory Reporting Accuracy Tests...")
        return self._run_compliance_test_category(
            'regulatory_reporting', 
            'tests/test_plaid_compliance.py::TestRegulatoryReportingAccuracy', 
            verbose
        )
    
    def run_user_consent_management_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run user consent management testing only"""
        print("✅ Running User Consent Management Tests...")
        return self._run_compliance_test_category(
            'user_consent_management', 
            'tests/test_plaid_compliance.py::TestUserConsentManagementTesting', 
            verbose
        )
    
    def _run_compliance_test_category(self, category: str, test_path: str, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run tests for a specific compliance category"""
        pytest_args = [
            'pytest',
            test_path,
            '-v' if verbose else '-q',
            '--tb=short',
            '--strict-markers',
            '--disable-warnings',
            f'--html={self.output_dir}/{category}_compliance_report_{self.timestamp}.html',
            f'--json-report={self.output_dir}/{category}_compliance_report_{self.timestamp}.json',
            f'--json-report-file={self.output_dir}/{category}_compliance_report_{self.timestamp}.json'
        ]
        
        if parallel:
            pytest_args.extend(['-n', 'auto'])
        
        try:
            result = subprocess.run(pytest_args, capture_output=True, text=True, timeout=600)  # 10 minutes timeout for compliance tests
            
            # Parse results
            results = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
            results['category'] = category
            results['test_path'] = test_path
            
            return results
            
        except subprocess.TimeoutExpired:
            return {
                'category': category,
                'test_path': test_path,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'error_message': 'Compliance test execution timed out'
            }
        except Exception as e:
            return {
                'category': category,
                'test_path': test_path,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 1,
                'error_message': str(e)
            }
    
    def _parse_pytest_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results"""
        results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': return_code
        }
        
        # Parse test results from output
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line and 'skipped' in line:
                # Extract numbers from summary line
                parts = line.split()
                for part in parts:
                    if part.isdigit():
                        if 'passed' in line and part in line.split()[:line.split().index('passed')]:
                            results['passed'] = int(part)
                        elif 'failed' in line and part in line.split()[:line.split().index('failed')]:
                            results['failed'] = int(part)
                        elif 'skipped' in line and part in line.split()[:line.split().index('skipped')]:
                            results['skipped'] = int(part)
                
                # Calculate total
                results['total'] = results['passed'] + results['failed'] + results['skipped']
                break
        
        return results
    
    def _calculate_compliance_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate compliance testing metrics"""
        metrics = {
            'gdpr_compliance_score': 0.0,
            'pci_dss_compliance_score': 0.0,
            'data_retention_compliance_score': 0.0,
            'audit_trail_compliance_score': 0.0,
            'regulatory_reporting_compliance_score': 0.0,
            'user_consent_compliance_score': 0.0,
            'overall_compliance_score': 0.0,
            'regulatory_risk_level': 'LOW',
            'privacy_protection_score': 0.0,
            'security_compliance_score': 0.0
        }
        
        if test_results['total_tests'] > 0:
            # Calculate category-specific metrics
            categories = test_results['test_categories']
            
            if 'gdpr_compliance' in categories:
                cat = categories['gdpr_compliance']
                if cat['total'] > 0:
                    metrics['gdpr_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'pci_dss_compliance' in categories:
                cat = categories['pci_dss_compliance']
                if cat['total'] > 0:
                    metrics['pci_dss_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'data_retention_policy' in categories:
                cat = categories['data_retention_policy']
                if cat['total'] > 0:
                    metrics['data_retention_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'audit_trail_completeness' in categories:
                cat = categories['audit_trail_completeness']
                if cat['total'] > 0:
                    metrics['audit_trail_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'regulatory_reporting' in categories:
                cat = categories['regulatory_reporting']
                if cat['total'] > 0:
                    metrics['regulatory_reporting_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'user_consent_management' in categories:
                cat = categories['user_consent_management']
                if cat['total'] > 0:
                    metrics['user_consent_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            # Calculate overall compliance score
            metrics['overall_compliance_score'] = (test_results['passed'] / test_results['total_tests']) * 100
            
            # Calculate additional metrics
            metrics['privacy_protection_score'] = (metrics['gdpr_compliance_score'] + metrics['user_consent_compliance_score']) / 2
            metrics['security_compliance_score'] = (metrics['pci_dss_compliance_score'] + metrics['audit_trail_compliance_score']) / 2
            
            # Determine regulatory risk level
            if metrics['overall_compliance_score'] >= 95:
                metrics['regulatory_risk_level'] = 'LOW'
            elif metrics['overall_compliance_score'] >= 85:
                metrics['regulatory_risk_level'] = 'MEDIUM'
            else:
                metrics['regulatory_risk_level'] = 'HIGH'
        
        return metrics
    
    def _generate_compliance_reports(self, test_results: Dict[str, Any]):
        """Generate comprehensive compliance test reports"""
        # Generate JSON report
        json_report_path = self.output_dir / f"plaid_compliance_test_report_{self.timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        # Generate HTML report
        html_report_path = self.output_dir / f"plaid_compliance_test_report_{self.timestamp}.html"
        self._generate_compliance_html_report(test_results, html_report_path)
        
        # Generate markdown report
        md_report_path = self.output_dir / f"plaid_compliance_test_report_{self.timestamp}.md"
        self._generate_compliance_markdown_report(test_results, md_report_path)
        
        print(f"\n📊 Compliance test reports generated:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
        print(f"   Markdown: {md_report_path}")
    
    def _generate_compliance_html_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate HTML compliance test report"""
        metrics = test_results.get('compliance_metrics', {})
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plaid Compliance Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .category {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 20px 0; }}
        .metric {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; text-align: center; }}
        .compliance-metrics {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .risk-assessment {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .risk-high {{ background-color: #f8d7da; color: #721c24; }}
        .risk-medium {{ background-color: #fff3cd; color: #856404; }}
        .risk-low {{ background-color: #d4edda; color: #155724; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Plaid Compliance Test Report</h1>
        <p>Generated: {test_results['timestamp']}</p>
        <p>Duration: {test_results['duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Compliance Test Summary</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Total Tests</h3>
                <p>{test_results['total_tests']}</p>
            </div>
            <div class="metric passed">
                <h3>Passed</h3>
                <p>{test_results['passed']}</p>
            </div>
            <div class="metric failed">
                <h3>Failed</h3>
                <p>{test_results['failed']}</p>
            </div>
            <div class="metric skipped">
                <h3>Skipped</h3>
                <p>{test_results['skipped']}</p>
            </div>
        </div>
    </div>
    
    <div class="compliance-metrics">
        <h2>🛡️ Compliance Health Metrics</h2>
        <div class="metrics">
            <div class="metric">
                <h3>GDPR Compliance Score</h3>
                <p>{metrics.get('gdpr_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>PCI DSS Compliance Score</h3>
                <p>{metrics.get('pci_dss_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Data Retention Compliance</h3>
                <p>{metrics.get('data_retention_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Audit Trail Compliance</h3>
                <p>{metrics.get('audit_trail_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Regulatory Reporting</h3>
                <p>{metrics.get('regulatory_reporting_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>User Consent Management</h3>
                <p>{metrics.get('user_consent_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Overall Compliance Score</h3>
                <p>{metrics.get('overall_compliance_score', 0):.1f}%</p>
            </div>
        </div>
    </div>
    
    <div class="risk-assessment">
        <h2>📊 Risk Assessment</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Regulatory Risk Level</h3>
                <p class="risk-{metrics.get('regulatory_risk_level', 'LOW').lower()}">{metrics.get('regulatory_risk_level', 'LOW')}</p>
            </div>
            <div class="metric">
                <h3>Privacy Protection Score</h3>
                <p>{metrics.get('privacy_protection_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Security Compliance Score</h3>
                <p>{metrics.get('security_compliance_score', 0):.1f}%</p>
            </div>
        </div>
    </div>
    
    <div class="categories">
        <h2>🔍 Compliance Test Categories</h2>
"""
        
        for category, results in test_results['test_categories'].items():
            status_class = 'passed' if results['failed'] == 0 and results['errors'] == 0 else 'failed'
            category_name = category.replace('_', ' ').title()
            html_content += f"""
        <div class="category {status_class}">
            <h3>{category_name} Tests</h3>
            <p>Total: {results['total']} | Passed: {results['passed']} | Failed: {results['failed']} | Skipped: {results['skipped']}</p>
            <p>Test Path: {results['test_path']}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_compliance_markdown_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate markdown compliance test report"""
        metrics = test_results.get('compliance_metrics', {})
        
        md_content = f"""# 🛡️ Plaid Compliance Test Report

**Generated:** {test_results['timestamp']}  
**Duration:** {test_results['duration']:.2f} seconds

## Compliance Test Summary

| Metric | Count |
|--------|-------|
| Total Tests | {test_results['total_tests']} |
| Passed | {test_results['passed']} |
| Failed | {test_results['failed']} |
| Skipped | {test_results['skipped']} |
| Errors | {test_results['errors']} |

## 🛡️ Compliance Health Metrics

| Metric | Score |
|--------|-------|
| GDPR Compliance Score | {metrics.get('gdpr_compliance_score', 0):.1f}% |
| PCI DSS Compliance Score | {metrics.get('pci_dss_compliance_score', 0):.1f}% |
| Data Retention Compliance | {metrics.get('data_retention_compliance_score', 0):.1f}% |
| Audit Trail Compliance | {metrics.get('audit_trail_compliance_score', 0):.1f}% |
| Regulatory Reporting | {metrics.get('regulatory_reporting_compliance_score', 0):.1f}% |
| User Consent Management | {metrics.get('user_consent_compliance_score', 0):.1f}% |
| **Overall Compliance Score** | **{metrics.get('overall_compliance_score', 0):.1f}%** |

## 📊 Risk Assessment

| Metric | Value |
|--------|-------|
| Regulatory Risk Level | {metrics.get('regulatory_risk_level', 'LOW')} |
| Privacy Protection Score | {metrics.get('privacy_protection_score', 0):.1f}% |
| Security Compliance Score | {metrics.get('security_compliance_score', 0):.1f}% |

## Compliance Test Categories

"""
        
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            md_content += f"""### {category_name} Tests {status}

- **Total:** {results['total']}
- **Passed:** {results['passed']}
- **Failed:** {results['failed']}
- **Skipped:** {results['skipped']}
- **Test Path:** {results['test_path']}

"""
        
        md_content += """## Compliance Testing Focus Areas

### 1. GDPR Compliance Validation
- Data processing lawfulness testing
- Data minimization compliance testing
- User rights fulfillment testing
- Data transfer compliance testing
- Breach notification compliance testing
- Privacy by design compliance testing

### 2. PCI DSS Compliance Verification
- Card data encryption testing
- Network security compliance testing
- Access control compliance testing
- Vulnerability management testing
- Security monitoring compliance testing
- Incident response compliance testing

### 3. Data Retention Policy Testing
- Retention policy enforcement testing
- Legal hold compliance testing
- Secure deletion compliance testing
- Retention audit compliance testing

### 4. Audit Trail Completeness
- Audit log completeness testing
- Audit log integrity testing
- Audit log retention testing
- Audit log analysis testing

### 5. Regulatory Reporting Accuracy
- Report accuracy validation testing
- Report completeness validation testing
- Report timeliness validation testing
- Report submission compliance testing

### 6. User Consent Management Testing
- Consent collection compliance testing
- Consent storage compliance testing
- Consent withdrawal compliance testing
- Consent audit compliance testing

## Compliance Recommendations

Based on the compliance test results, consider the following:

1. **GDPR Compliance**: Ensure proper GDPR compliance measures
2. **PCI DSS Compliance**: Maintain PCI DSS compliance standards
3. **Data Retention**: Implement proper data retention policies
4. **Audit Trails**: Maintain complete audit trails
5. **Regulatory Reporting**: Ensure accurate regulatory reporting
6. **User Consent**: Implement proper user consent management

## Next Steps

1. Review failed compliance tests and address issues
2. Run compliance tests again to verify fixes
3. Monitor compliance metrics in production
4. Implement continuous compliance testing
5. Set up alerts for compliance violations
6. Conduct regular compliance audits
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_compliance_summary(self, test_results: Dict[str, Any]):
        """Print compliance test summary to console"""
        metrics = test_results.get('compliance_metrics', {})
        
        print("\n" + "=" * 80)
        print("🛡️ PLAID COMPLIANCE TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Duration: {test_results['duration']:.2f} seconds")
        print(f"📊 Total Tests: {test_results['total_tests']}")
        print(f"✅ Passed: {test_results['passed']}")
        print(f"❌ Failed: {test_results['failed']}")
        print(f"⏭️  Skipped: {test_results['skipped']}")
        print(f"🚨 Errors: {test_results['errors']}")
        
        if test_results['total_tests'] > 0:
            success_rate = (test_results['passed'] / test_results['total_tests']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n🛡️ Compliance Health Metrics:")
        print(f"   🇪🇺 GDPR Compliance Score: {metrics.get('gdpr_compliance_score', 0):.1f}%")
        print(f"   💳 PCI DSS Compliance Score: {metrics.get('pci_dss_compliance_score', 0):.1f}%")
        print(f"   📋 Data Retention Compliance: {metrics.get('data_retention_compliance_score', 0):.1f}%")
        print(f"   📊 Audit Trail Compliance: {metrics.get('audit_trail_compliance_score', 0):.1f}%")
        print(f"   📈 Regulatory Reporting: {metrics.get('regulatory_reporting_compliance_score', 0):.1f}%")
        print(f"   ✅ User Consent Management: {metrics.get('user_consent_compliance_score', 0):.1f}%")
        print(f"   🎯 Overall Compliance Score: {metrics.get('overall_compliance_score', 0):.1f}%")
        
        print("\n📊 Risk Assessment:")
        print(f"   🚨 Regulatory Risk Level: {metrics.get('regulatory_risk_level', 'LOW')}")
        print(f"   🔒 Privacy Protection Score: {metrics.get('privacy_protection_score', 0):.1f}%")
        print(f"   🛡️ Security Compliance Score: {metrics.get('security_compliance_score', 0):.1f}%")
        
        print("\n🔍 Compliance Test Categories:")
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            print(f"   {category_name}: {status} ({results['passed']}/{results['total']})")
        
        print("\n" + "=" * 80)
        
        if test_results['failed'] > 0 or test_results['errors'] > 0:
            print("⚠️  Some compliance tests failed. Please review the detailed reports.")
            sys.exit(1)
        else:
            print("🎉 All compliance tests passed successfully!")


def main():
    """Main function for compliance test runner"""
    parser = argparse.ArgumentParser(description='Plaid Compliance Test Runner')
    parser.add_argument('--category', choices=['all', 'gdpr_compliance', 'pci_dss_compliance', 
                                              'data_retention_policy', 'audit_trail_completeness', 
                                              'regulatory_reporting', 'user_consent_management'],
                       default='all', help='Compliance test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output-dir', default='compliance_test_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    runner = PlaidComplianceTestRunner(args.output_dir)
    
    if args.category == 'all':
        runner.run_all_compliance_tests(args.verbose, args.parallel)
    elif args.category == 'gdpr_compliance':
        runner.run_gdpr_compliance_tests(args.verbose)
    elif args.category == 'pci_dss_compliance':
        runner.run_pci_dss_compliance_tests(args.verbose)
    elif args.category == 'data_retention_policy':
        runner.run_data_retention_policy_tests(args.verbose)
    elif args.category == 'audit_trail_completeness':
        runner.run_audit_trail_completeness_tests(args.verbose)
    elif args.category == 'regulatory_reporting':
        runner.run_regulatory_reporting_tests(args.verbose)
    elif args.category == 'user_consent_management':
        runner.run_user_consent_management_tests(args.verbose)


if __name__ == '__main__':
    main() 