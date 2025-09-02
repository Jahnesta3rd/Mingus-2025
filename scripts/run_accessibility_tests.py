#!/usr/bin/env python3
"""
Accessibility Testing Runner for CI/CD
Integrates with GitHub Actions, Jenkins, and other CI/CD tools
"""

import os
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_accessibility import AccessibilityTester, run_accessibility_tests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CICDAccessibilityRunner:
    """CI/CD accessibility testing runner"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:5000')
        self.pages = config.get('pages', ['/', '/forms', '/calculator'])
        self.headless = config.get('headless', True)
        self.output_dir = config.get('output_dir', 'reports')
        self.fail_on_critical = config.get('fail_on_critical', True)
        self.generate_report = config.get('generate_report', True)
        self.notify_slack = config.get('notify_slack', False)
        self.slack_webhook = config.get('slack_webhook', '')
        
        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def run_tests(self) -> Dict:
        """Run accessibility tests and return results"""
        logger.info("Starting CI/CD accessibility testing")
        logger.info(f"Testing URL: {self.base_url}")
        logger.info(f"Testing pages: {self.pages}")
        
        try:
            # Run accessibility tests
            results = run_accessibility_tests(
                base_url=self.base_url,
                pages=self.pages,
                headless=self.headless
            )
            
            if results.get('success'):
                logger.info("Accessibility tests completed successfully")
                self._process_results(results)
                return results
            else:
                logger.error(f"Accessibility tests failed: {results.get('error')}")
                return results
                
        except Exception as e:
            logger.error(f"Accessibility testing failed with exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_results(self, results: Dict):
        """Process test results and generate outputs"""
        try:
            # Save detailed results
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            results_file = Path(self.output_dir) / f"ci_accessibility_results_{timestamp}.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {results_file}")
            
            # Generate CI/CD specific outputs
            self._generate_ci_outputs(results)
            
            # Check for critical issues
            if self.fail_on_critical:
                self._check_critical_issues(results)
                
            # Generate report if requested
            if self.generate_report:
                self._generate_report(results)
                
            # Notify if configured
            if self.notify_slack and self.slack_webhook:
                self._notify_slack(results)
                
        except Exception as e:
            logger.error(f"Failed to process results: {e}")
    
    def _generate_ci_outputs(self, results: Dict):
        """Generate CI/CD specific output files"""
        try:
            # Generate JUnit XML for CI tools
            self._generate_junit_xml(results)
            
            # Generate summary for GitHub Actions
            self._generate_github_summary(results)
            
            # Generate exit code file
            self._generate_exit_code(results)
            
        except Exception as e:
            logger.error(f"Failed to generate CI outputs: {e}")
    
    def _generate_junit_xml(self, results: Dict):
        """Generate JUnit XML format for CI tools"""
        try:
            junit_file = Path(self.output_dir) / "junit.xml"
            
            # Convert accessibility results to JUnit format
            junit_content = self._convert_to_junit(results)
            
            with open(junit_file, 'w', encoding='utf-8') as f:
                f.write(junit_content)
            
            logger.info(f"JUnit XML generated: {junit_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate JUnit XML: {e}")
    
    def _convert_to_junit(self, results: Dict) -> str:
        """Convert accessibility results to JUnit XML format"""
        try:
            report = results.get('report', {})
            summary = report.get('summary', {})
            
            # Count test cases
            total_tests = summary.get('total_tests', 0)
            failed_tests = summary.get('tests_failed', 0)
            passed_tests = summary.get('tests_passed', 0)
            
            # Generate JUnit XML
            junit_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Accessibility Tests" tests="{total_tests}" failures="{failed_tests}" errors="0" time="0">
  <testsuite name="WCAG Compliance" tests="{total_tests}" failures="{failed_tests}" errors="0" time="0">
"""
            
            # Add test cases
            if failed_tests > 0:
                critical_issues = report.get('details', {}).get('critical_issues', [])
                for i, issue in enumerate(critical_issues[:failed_tests]):
                    junit_xml += f"""    <testcase name="Accessibility Test {i+1}" classname="WCAG Compliance" time="0">
      <failure message="Critical accessibility issue found" type="failure">{issue}</failure>
    </testcase>
"""
            
            # Add passed tests
            for i in range(passed_tests):
                junit_xml += f"""    <testcase name="Accessibility Test {i+1}" classname="WCAG Compliance" time="0" />
"""
            
            junit_xml += """  </testsuite>
</testsuites>"""
            
            return junit_xml
            
        except Exception as e:
            logger.error(f"Failed to convert to JUnit: {e}")
            return ""
    
    def _generate_github_summary(self, results: Dict):
        """Generate GitHub Actions summary"""
        try:
            summary_file = Path(self.output_dir) / "github-summary.md"
            
            report = results.get('report', {})
            summary = report.get('summary', {})
            critical_issues = report.get('details', {}).get('critical_issues', [])
            recommendations = report.get('recommendations', [])
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("# Accessibility Test Results\n\n")
                
                f.write("## Summary\n")
                f.write(f"- **Total Tests**: {summary.get('total_tests', 0)}\n")
                f.write(f"- **Tests Passed**: {summary.get('tests_passed', 0)}\n")
                f.write(f"- **Tests Failed**: {summary.get('tests_failed', 0)}\n")
                f.write(f"- **Success Rate**: {summary.get('success_rate', 0):.1f}%\n")
                f.write(f"- **WCAG AA Compliant**: {'✅ Yes' if summary.get('wcag_aa_compliant') else '❌ No'}\n\n")
                
                if critical_issues:
                    f.write("## Critical Issues\n")
                    for issue in critical_issues:
                        f.write(f"- ❌ {issue}\n")
                    f.write("\n")
                
                if recommendations:
                    f.write("## Recommendations\n")
                    for rec in recommendations:
                        f.write(f"- 💡 {rec}\n")
                    f.write("\n")
                
                f.write("---\n")
                f.write(f"*Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
            
            logger.info(f"GitHub summary generated: {summary_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate GitHub summary: {e}")
    
    def _generate_exit_code(self, results: Dict):
        """Generate exit code file for CI tools"""
        try:
            exit_code_file = Path(self.output_dir) / "exit_code.txt"
            
            # Determine exit code
            if results.get('success') and not self._has_critical_issues(results):
                exit_code = "0"  # Success
            else:
                exit_code = "1"  # Failure
            
            with open(exit_code_file, 'w') as f:
                f.write(exit_code)
            
            logger.info(f"Exit code generated: {exit_code_code}")
            
        except Exception as e:
            logger.error(f"Failed to generate exit code: {e}")
    
    def _check_critical_issues(self, results: Dict):
        """Check for critical accessibility issues"""
        try:
            if self._has_critical_issues(results):
                critical_issues = results.get('report', {}).get('details', {}).get('critical_issues', [])
                logger.error(f"Found {len(critical_issues)} critical accessibility issues:")
                for issue in critical_issues:
                    logger.error(f"  - {issue}")
                
                if self.fail_on_critical:
                    logger.error("Failing build due to critical accessibility issues")
                    sys.exit(1)
            else:
                logger.info("No critical accessibility issues found")
                
        except Exception as e:
            logger.error(f"Failed to check critical issues: {e}")
    
    def _has_critical_issues(self, results: Dict) -> bool:
        """Check if results contain critical issues"""
        try:
            critical_issues = results.get('report', {}).get('details', {}).get('critical_issues', [])
            return len(critical_issues) > 0
        except Exception:
            return False
    
    def _generate_report(self, results: Dict):
        """Generate comprehensive accessibility report"""
        try:
            report_file = Path(self.output_dir) / "accessibility_report.html"
            
            # Use pytest-html to generate report
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/test_accessibility.py",
                "--html", str(report_file),
                "--self-contained-html",
                "--tb", "short"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"HTML report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
    
    def _notify_slack(self, results: Dict):
        """Send notification to Slack"""
        try:
            if not self.slack_webhook:
                return
            
            report = results.get('report', {})
            summary = report.get('summary', {})
            
            # Prepare Slack message
            message = {
                "text": "Accessibility Test Results",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🔍 Accessibility Test Results"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Tests Passed:* {summary.get('tests_passed', 0)}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Tests Failed:* {summary.get('tests_failed', 0)}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Success Rate:* {summary.get('success_rate', 0):.1f}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*WCAG AA Compliant:* {'✅ Yes' if summary.get('wcag_aa_compliant') else '❌ No'}"
                            }
                        ]
                    }
                ]
            }
            
            # Add critical issues if any
            critical_issues = report.get('details', {}).get('critical_issues', [])
            if critical_issues:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Critical Issues Found:*\n{chr(10).join(['• ' + issue for issue in critical_issues[:3]])}"
                    }
                })
            
            # Send to Slack
            import requests
            response = requests.post(self.slack_webhook, json=message)
            response.raise_for_status()
            
            logger.info("Slack notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="CI/CD Accessibility Testing Runner")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--base-url", "-u", help="Base URL to test")
    parser.add_argument("--pages", "-p", nargs="+", help="Pages to test")
    parser.add_argument("--output-dir", "-o", help="Output directory")
    parser.add_argument("--fail-on-critical", action="store_true", help="Fail on critical issues")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation")
    parser.add_argument("--slack-webhook", help="Slack webhook URL for notifications")
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override with command line arguments
    if args.base_url:
        config['base_url'] = args.base_url
    if args.pages:
        config['pages'] = args.pages
    if args.output_dir:
        config['output_dir'] = args.output_dir
    if args.fail_on_critical:
        config['fail_on_critical'] = True
    if args.no_report:
        config['generate_report'] = False
    if args.slack_webhook:
        config['slack_webhook'] = args.slack_webhook
        config['notify_slack'] = True
    
    # Set defaults
    config.setdefault('base_url', 'http://localhost:5000')
    config.setdefault('pages', ['/', '/forms', '/calculator'])
    config.setdefault('headless', True)
    config.setdefault('output_dir', 'reports')
    config.setdefault('fail_on_critical', True)
    config.setdefault('generate_report', True)
    config.setdefault('notify_slack', False)
    
    # Run tests
    runner = CICDAccessibilityRunner(config)
    results = runner.run_tests()
    
    # Exit with appropriate code
    if results.get('success') and not runner._has_critical_issues(results):
        logger.info("Accessibility testing completed successfully")
        sys.exit(0)
    else:
        logger.error("Accessibility testing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
