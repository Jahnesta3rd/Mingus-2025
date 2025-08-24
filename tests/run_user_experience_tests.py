#!/usr/bin/env python3
"""
Plaid User Experience Test Runner

This script provides a dedicated test runner for comprehensive Plaid user experience testing
including connection flow usability testing, mobile responsiveness testing, error message
clarity and helpfulness, accessibility compliance testing, cross-browser compatibility,
and offline functionality testing.
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


class PlaidUserExperienceTestRunner:
    """Dedicated test runner for Plaid user experience tests"""
    
    def __init__(self, output_dir: str = "user_experience_test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_all_user_experience_tests(self, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run all Plaid user experience tests"""
        print("👤 Starting Plaid User Experience Test Suite...")
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
            'user_experience_metrics': {},
            'usability_metrics': {},
            'accessibility_metrics': {},
            'performance_metrics': {},
            'duration': 0
        }
        
        start_time = time.time()
        
        # Run user experience test categories
        test_categories = [
            ('connection_flow_usability', 'tests/test_plaid_user_experience.py::TestConnectionFlowUsabilityTesting'),
            ('mobile_responsiveness', 'tests/test_plaid_user_experience.py::TestMobileResponsivenessTesting'),
            ('error_message_clarity', 'tests/test_plaid_user_experience.py::TestErrorMessageClarityAndHelpfulness'),
            ('accessibility_compliance', 'tests/test_plaid_user_experience.py::TestAccessibilityComplianceTesting'),
            ('cross_browser_compatibility', 'tests/test_plaid_user_experience.py::TestCrossBrowserCompatibility'),
            ('offline_functionality', 'tests/test_plaid_user_experience.py::TestOfflineFunctionalityTesting')
        ]
        
        for category, test_path in test_categories:
            print(f"\n🔍 Running {category.replace('_', ' ').title()} tests...")
            category_results = self._run_user_experience_test_category(category, test_path, verbose, parallel)
            test_results['test_categories'][category] = category_results
            
            # Update totals
            test_results['total_tests'] += category_results['total']
            test_results['passed'] += category_results['passed']
            test_results['failed'] += category_results['failed']
            test_results['skipped'] += category_results['skipped']
            test_results['errors'] += category_results['errors']
        
        test_results['duration'] = time.time() - start_time
        
        # Calculate user experience metrics
        test_results['user_experience_metrics'] = self._calculate_user_experience_metrics(test_results)
        
        # Generate reports
        self._generate_user_experience_reports(test_results)
        
        # Print summary
        self._print_user_experience_summary(test_results)
        
        return test_results
    
    def run_connection_flow_usability_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run connection flow usability testing only"""
        print("🔄 Running Connection Flow Usability Tests...")
        return self._run_user_experience_test_category(
            'connection_flow_usability', 
            'tests/test_plaid_user_experience.py::TestConnectionFlowUsabilityTesting', 
            verbose
        )
    
    def run_mobile_responsiveness_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run mobile responsiveness testing only"""
        print("📱 Running Mobile Responsiveness Tests...")
        return self._run_user_experience_test_category(
            'mobile_responsiveness', 
            'tests/test_plaid_user_experience.py::TestMobileResponsivenessTesting', 
            verbose
        )
    
    def run_error_message_clarity_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run error message clarity and helpfulness testing only"""
        print("💬 Running Error Message Clarity Tests...")
        return self._run_user_experience_test_category(
            'error_message_clarity', 
            'tests/test_plaid_user_experience.py::TestErrorMessageClarityAndHelpfulness', 
            verbose
        )
    
    def run_accessibility_compliance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run accessibility compliance testing only"""
        print("♿ Running Accessibility Compliance Tests...")
        return self._run_user_experience_test_category(
            'accessibility_compliance', 
            'tests/test_plaid_user_experience.py::TestAccessibilityComplianceTesting', 
            verbose
        )
    
    def run_cross_browser_compatibility_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run cross-browser compatibility testing only"""
        print("🌐 Running Cross-Browser Compatibility Tests...")
        return self._run_user_experience_test_category(
            'cross_browser_compatibility', 
            'tests/test_plaid_user_experience.py::TestCrossBrowserCompatibility', 
            verbose
        )
    
    def run_offline_functionality_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run offline functionality testing only"""
        print("📴 Running Offline Functionality Tests...")
        return self._run_user_experience_test_category(
            'offline_functionality', 
            'tests/test_plaid_user_experience.py::TestOfflineFunctionalityTesting', 
            verbose
        )
    
    def _run_user_experience_test_category(self, category: str, test_path: str, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run tests for a specific user experience category"""
        pytest_args = [
            'pytest',
            test_path,
            '-v' if verbose else '-q',
            '--tb=short',
            '--strict-markers',
            '--disable-warnings',
            f'--html={self.output_dir}/{category}_user_experience_report_{self.timestamp}.html',
            f'--json-report={self.output_dir}/{category}_user_experience_report_{self.timestamp}.json',
            f'--json-report-file={self.output_dir}/{category}_user_experience_report_{self.timestamp}.json'
        ]
        
        if parallel:
            pytest_args.extend(['-n', 'auto'])
        
        try:
            result = subprocess.run(pytest_args, capture_output=True, text=True, timeout=600)  # 10 minutes timeout for UX tests
            
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
                'error_message': 'User experience test execution timed out'
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
    
    def _calculate_user_experience_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate user experience testing metrics"""
        metrics = {
            'connection_flow_usability_score': 0.0,
            'mobile_responsiveness_score': 0.0,
            'error_message_clarity_score': 0.0,
            'accessibility_compliance_score': 0.0,
            'cross_browser_compatibility_score': 0.0,
            'offline_functionality_score': 0.0,
            'overall_user_experience_score': 0.0,
            'usability_rating': 'EXCELLENT',
            'accessibility_rating': 'EXCELLENT',
            'performance_rating': 'EXCELLENT'
        }
        
        if test_results['total_tests'] > 0:
            # Calculate category-specific metrics
            categories = test_results['test_categories']
            
            if 'connection_flow_usability' in categories:
                cat = categories['connection_flow_usability']
                if cat['total'] > 0:
                    metrics['connection_flow_usability_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'mobile_responsiveness' in categories:
                cat = categories['mobile_responsiveness']
                if cat['total'] > 0:
                    metrics['mobile_responsiveness_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'error_message_clarity' in categories:
                cat = categories['error_message_clarity']
                if cat['total'] > 0:
                    metrics['error_message_clarity_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'accessibility_compliance' in categories:
                cat = categories['accessibility_compliance']
                if cat['total'] > 0:
                    metrics['accessibility_compliance_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'cross_browser_compatibility' in categories:
                cat = categories['cross_browser_compatibility']
                if cat['total'] > 0:
                    metrics['cross_browser_compatibility_score'] = (cat['passed'] / cat['total']) * 100
            
            if 'offline_functionality' in categories:
                cat = categories['offline_functionality']
                if cat['total'] > 0:
                    metrics['offline_functionality_score'] = (cat['passed'] / cat['total']) * 100
            
            # Calculate overall user experience score
            metrics['overall_user_experience_score'] = (test_results['passed'] / test_results['total_tests']) * 100
            
            # Calculate additional metrics
            usability_score = (metrics['connection_flow_usability_score'] + metrics['mobile_responsiveness_score'] + metrics['error_message_clarity_score']) / 3
            accessibility_score = metrics['accessibility_compliance_score']
            performance_score = (metrics['cross_browser_compatibility_score'] + metrics['offline_functionality_score']) / 2
            
            # Determine ratings
            if usability_score >= 95:
                metrics['usability_rating'] = 'EXCELLENT'
            elif usability_score >= 85:
                metrics['usability_rating'] = 'GOOD'
            elif usability_score >= 75:
                metrics['usability_rating'] = 'FAIR'
            else:
                metrics['usability_rating'] = 'POOR'
            
            if accessibility_score >= 95:
                metrics['accessibility_rating'] = 'EXCELLENT'
            elif accessibility_score >= 85:
                metrics['accessibility_rating'] = 'GOOD'
            elif accessibility_score >= 75:
                metrics['accessibility_rating'] = 'FAIR'
            else:
                metrics['accessibility_rating'] = 'POOR'
            
            if performance_score >= 95:
                metrics['performance_rating'] = 'EXCELLENT'
            elif performance_score >= 85:
                metrics['performance_rating'] = 'GOOD'
            elif performance_score >= 75:
                metrics['performance_rating'] = 'FAIR'
            else:
                metrics['performance_rating'] = 'POOR'
        
        return metrics
    
    def _generate_user_experience_reports(self, test_results: Dict[str, Any]):
        """Generate comprehensive user experience test reports"""
        # Generate JSON report
        json_report_path = self.output_dir / f"plaid_user_experience_test_report_{self.timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        # Generate HTML report
        html_report_path = self.output_dir / f"plaid_user_experience_test_report_{self.timestamp}.html"
        self._generate_user_experience_html_report(test_results, html_report_path)
        
        # Generate markdown report
        md_report_path = self.output_dir / f"plaid_user_experience_test_report_{self.timestamp}.md"
        self._generate_user_experience_markdown_report(test_results, md_report_path)
        
        print(f"\n📊 User experience test reports generated:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
        print(f"   Markdown: {md_report_path}")
    
    def _generate_user_experience_html_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate HTML user experience test report"""
        metrics = test_results.get('user_experience_metrics', {})
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plaid User Experience Test Report</title>
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
        .user-experience-metrics {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .rating-assessment {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .rating-excellent {{ background-color: #d4edda; color: #155724; }}
        .rating-good {{ background-color: #d1ecf1; color: #0c5460; }}
        .rating-fair {{ background-color: #fff3cd; color: #856404; }}
        .rating-poor {{ background-color: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>👤 Plaid User Experience Test Report</h1>
        <p>Generated: {test_results['timestamp']}</p>
        <p>Duration: {test_results['duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>User Experience Test Summary</h2>
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
    
    <div class="user-experience-metrics">
        <h2>👤 User Experience Health Metrics</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Connection Flow Usability</h3>
                <p>{metrics.get('connection_flow_usability_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Mobile Responsiveness</h3>
                <p>{metrics.get('mobile_responsiveness_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Error Message Clarity</h3>
                <p>{metrics.get('error_message_clarity_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Accessibility Compliance</h3>
                <p>{metrics.get('accessibility_compliance_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Cross-Browser Compatibility</h3>
                <p>{metrics.get('cross_browser_compatibility_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Offline Functionality</h3>
                <p>{metrics.get('offline_functionality_score', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Overall User Experience</h3>
                <p>{metrics.get('overall_user_experience_score', 0):.1f}%</p>
            </div>
        </div>
    </div>
    
    <div class="rating-assessment">
        <h2>📊 User Experience Rating Assessment</h2>
        <div class="metrics">
            <div class="metric rating-{metrics.get('usability_rating', 'EXCELLENT').lower()}">
                <h3>Usability Rating</h3>
                <p>{metrics.get('usability_rating', 'EXCELLENT')}</p>
            </div>
            <div class="metric rating-{metrics.get('accessibility_rating', 'EXCELLENT').lower()}">
                <h3>Accessibility Rating</h3>
                <p>{metrics.get('accessibility_rating', 'EXCELLENT')}</p>
            </div>
            <div class="metric rating-{metrics.get('performance_rating', 'EXCELLENT').lower()}">
                <h3>Performance Rating</h3>
                <p>{metrics.get('performance_rating', 'EXCELLENT')}</p>
            </div>
        </div>
    </div>
    
    <div class="categories">
        <h2>🔍 User Experience Test Categories</h2>
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
    
    def _generate_user_experience_markdown_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate markdown user experience test report"""
        metrics = test_results.get('user_experience_metrics', {})
        
        md_content = f"""# 👤 Plaid User Experience Test Report

**Generated:** {test_results['timestamp']}  
**Duration:** {test_results['duration']:.2f} seconds

## User Experience Test Summary

| Metric | Count |
|--------|-------|
| Total Tests | {test_results['total_tests']} |
| Passed | {test_results['passed']} |
| Failed | {test_results['failed']} |
| Skipped | {test_results['skipped']} |
| Errors | {test_results['errors']} |

## 👤 User Experience Health Metrics

| Metric | Score |
|--------|-------|
| Connection Flow Usability | {metrics.get('connection_flow_usability_score', 0):.1f}% |
| Mobile Responsiveness | {metrics.get('mobile_responsiveness_score', 0):.1f}% |
| Error Message Clarity | {metrics.get('error_message_clarity_score', 0):.1f}% |
| Accessibility Compliance | {metrics.get('accessibility_compliance_score', 0):.1f}% |
| Cross-Browser Compatibility | {metrics.get('cross_browser_compatibility_score', 0):.1f}% |
| Offline Functionality | {metrics.get('offline_functionality_score', 0):.1f}% |
| **Overall User Experience** | **{metrics.get('overall_user_experience_score', 0):.1f}%** |

## 📊 User Experience Rating Assessment

| Metric | Rating |
|--------|--------|
| Usability Rating | {metrics.get('usability_rating', 'EXCELLENT')} |
| Accessibility Rating | {metrics.get('accessibility_rating', 'EXCELLENT')} |
| Performance Rating | {metrics.get('performance_rating', 'EXCELLENT')} |

## User Experience Test Categories

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
        
        md_content += """## User Experience Testing Focus Areas

### 1. Connection Flow Usability Testing
- Connection flow simplicity and ease of use
- Connection flow guidance and instructions
- Connection flow feedback and progress indication
- Connection flow error recovery and resilience
- Connection flow completion success rate

### 2. Mobile Responsiveness Testing
- Mobile screen adaptation and responsive design
- Mobile touch interactions and usability
- Mobile performance optimization
- Mobile offline capability and functionality

### 3. Error Message Clarity and Helpfulness
- Error message clarity and understandability
- Error message helpfulness and actionability
- Error message consistency across the application
- Error message localization and internationalization

### 4. Accessibility Compliance Testing
- WCAG 2.1 compliance standards
- Screen reader compatibility and support
- Keyboard navigation and accessibility
- Color contrast compliance for accessibility
- Assistive technology support and compatibility

### 5. Cross-Browser Compatibility
- Major browser compatibility testing
- Mobile browser compatibility testing
- Feature detection and graceful fallbacks
- CSS compatibility across browsers
- JavaScript compatibility across browsers

### 6. Offline Functionality Testing
- Offline data caching and storage
- Offline synchronization and data sync
- Offline user experience and functionality
- Offline performance and responsiveness
- Offline error handling and recovery

## User Experience Recommendations

Based on the user experience test results, consider the following:

1. **Connection Flow**: Optimize connection flow usability and simplicity
2. **Mobile Experience**: Improve mobile responsiveness and touch interactions
3. **Error Handling**: Enhance error message clarity and helpfulness
4. **Accessibility**: Ensure comprehensive accessibility compliance
5. **Browser Support**: Maintain cross-browser compatibility
6. **Offline Functionality**: Improve offline capabilities and user experience

## Next Steps

1. Review failed user experience tests and address issues
2. Run user experience tests again to verify improvements
3. Monitor user experience metrics in production
4. Implement continuous user experience testing
5. Set up alerts for user experience degradation
6. Conduct regular user experience audits
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_user_experience_summary(self, test_results: Dict[str, Any]):
        """Print user experience test summary to console"""
        metrics = test_results.get('user_experience_metrics', {})
        
        print("\n" + "=" * 80)
        print("👤 PLAID USER EXPERIENCE TEST SUMMARY")
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
        
        print("\n👤 User Experience Health Metrics:")
        print(f"   🔄 Connection Flow Usability: {metrics.get('connection_flow_usability_score', 0):.1f}%")
        print(f"   📱 Mobile Responsiveness: {metrics.get('mobile_responsiveness_score', 0):.1f}%")
        print(f"   💬 Error Message Clarity: {metrics.get('error_message_clarity_score', 0):.1f}%")
        print(f"   ♿ Accessibility Compliance: {metrics.get('accessibility_compliance_score', 0):.1f}%")
        print(f"   🌐 Cross-Browser Compatibility: {metrics.get('cross_browser_compatibility_score', 0):.1f}%")
        print(f"   📴 Offline Functionality: {metrics.get('offline_functionality_score', 0):.1f}%")
        print(f"   🎯 Overall User Experience: {metrics.get('overall_user_experience_score', 0):.1f}%")
        
        print("\n📊 User Experience Rating Assessment:")
        print(f"   🎨 Usability Rating: {metrics.get('usability_rating', 'EXCELLENT')}")
        print(f"   ♿ Accessibility Rating: {metrics.get('accessibility_rating', 'EXCELLENT')}")
        print(f"   ⚡ Performance Rating: {metrics.get('performance_rating', 'EXCELLENT')}")
        
        print("\n🔍 User Experience Test Categories:")
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            print(f"   {category_name}: {status} ({results['passed']}/{results['total']})")
        
        print("\n" + "=" * 80)
        
        if test_results['failed'] > 0 or test_results['errors'] > 0:
            print("⚠️  Some user experience tests failed. Please review the detailed reports.")
            sys.exit(1)
        else:
            print("🎉 All user experience tests passed successfully!")


def main():
    """Main function for user experience test runner"""
    parser = argparse.ArgumentParser(description='Plaid User Experience Test Runner')
    parser.add_argument('--category', choices=['all', 'connection_flow_usability', 'mobile_responsiveness', 
                                              'error_message_clarity', 'accessibility_compliance', 
                                              'cross_browser_compatibility', 'offline_functionality'],
                       default='all', help='User experience test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output-dir', default='user_experience_test_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    runner = PlaidUserExperienceTestRunner(args.output_dir)
    
    if args.category == 'all':
        runner.run_all_user_experience_tests(args.verbose, args.parallel)
    elif args.category == 'connection_flow_usability':
        runner.run_connection_flow_usability_tests(args.verbose)
    elif args.category == 'mobile_responsiveness':
        runner.run_mobile_responsiveness_tests(args.verbose)
    elif args.category == 'error_message_clarity':
        runner.run_error_message_clarity_tests(args.verbose)
    elif args.category == 'accessibility_compliance':
        runner.run_accessibility_compliance_tests(args.verbose)
    elif args.category == 'cross_browser_compatibility':
        runner.run_cross_browser_compatibility_tests(args.verbose)
    elif args.category == 'offline_functionality':
        runner.run_offline_functionality_tests(args.verbose)


if __name__ == '__main__':
    main() 