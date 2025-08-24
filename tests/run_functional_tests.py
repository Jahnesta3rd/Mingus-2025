#!/usr/bin/env python3
"""
Plaid Functional Test Runner

This script provides a dedicated test runner for Plaid functional testing including
bank account connection flow, transaction data retrieval and processing, balance
update accuracy validation, webhook processing reliability, error handling and
recovery testing, and multi-account management testing.
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


class PlaidFunctionalTestRunner:
    """Dedicated test runner for Plaid functional tests"""
    
    def __init__(self, output_dir: str = "functional_test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_all_functional_tests(self, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run all Plaid functional tests"""
        print("🚀 Starting Plaid Functional Test Suite...")
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
            'functional_metrics': {},
            'performance_metrics': {},
            'reliability_metrics': {},
            'duration': 0
        }
        
        start_time = time.time()
        
        # Run functional test categories
        test_categories = [
            ('connection_flow', 'tests/test_plaid_functional.py::TestBankAccountConnectionFlow'),
            ('transaction_processing', 'tests/test_plaid_functional.py::TestTransactionDataRetrievalAndProcessing'),
            ('balance_validation', 'tests/test_plaid_functional.py::TestBalanceUpdateAccuracyValidation'),
            ('webhook_processing', 'tests/test_plaid_functional.py::TestWebhookProcessingReliability'),
            ('error_handling', 'tests/test_plaid_functional.py::TestErrorHandlingAndRecoveryTesting'),
            ('multi_account', 'tests/test_plaid_functional.py::TestMultiAccountManagementTesting')
        ]
        
        for category, test_path in test_categories:
            print(f"\n🔍 Running {category.replace('_', ' ').title()} tests...")
            category_results = self._run_functional_test_category(category, test_path, verbose, parallel)
            test_results['test_categories'][category] = category_results
            
            # Update totals
            test_results['total_tests'] += category_results['total']
            test_results['passed'] += category_results['passed']
            test_results['failed'] += category_results['failed']
            test_results['skipped'] += category_results['skipped']
            test_results['errors'] += category_results['errors']
        
        test_results['duration'] = time.time() - start_time
        
        # Calculate functional metrics
        test_results['functional_metrics'] = self._calculate_functional_metrics(test_results)
        
        # Generate reports
        self._generate_functional_reports(test_results)
        
        # Print summary
        self._print_functional_summary(test_results)
        
        return test_results
    
    def run_connection_flow_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run bank account connection flow tests only"""
        print("🔗 Running Bank Account Connection Flow Tests...")
        return self._run_functional_test_category(
            'connection_flow', 
            'tests/test_plaid_functional.py::TestBankAccountConnectionFlow', 
            verbose
        )
    
    def run_transaction_processing_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run transaction processing tests only"""
        print("💳 Running Transaction Processing Tests...")
        return self._run_functional_test_category(
            'transaction_processing', 
            'tests/test_plaid_functional.py::TestTransactionDataRetrievalAndProcessing', 
            verbose
        )
    
    def run_balance_validation_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run balance validation tests only"""
        print("💰 Running Balance Validation Tests...")
        return self._run_functional_test_category(
            'balance_validation', 
            'tests/test_plaid_functional.py::TestBalanceUpdateAccuracyValidation', 
            verbose
        )
    
    def run_webhook_processing_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run webhook processing tests only"""
        print("🔔 Running Webhook Processing Tests...")
        return self._run_functional_test_category(
            'webhook_processing', 
            'tests/test_plaid_functional.py::TestWebhookProcessingReliability', 
            verbose
        )
    
    def run_error_handling_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run error handling tests only"""
        print("⚠️ Running Error Handling Tests...")
        return self._run_functional_test_category(
            'error_handling', 
            'tests/test_plaid_functional.py::TestErrorHandlingAndRecoveryTesting', 
            verbose
        )
    
    def run_multi_account_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run multi-account management tests only"""
        print("🏦 Running Multi-Account Management Tests...")
        return self._run_functional_test_category(
            'multi_account', 
            'tests/test_plaid_functional.py::TestMultiAccountManagementTesting', 
            verbose
        )
    
    def _run_functional_test_category(self, category: str, test_path: str, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run tests for a specific functional category"""
        pytest_args = [
            'pytest',
            test_path,
            '-v' if verbose else '-q',
            '--tb=short',
            '--strict-markers',
            '--disable-warnings',
            f'--html={self.output_dir}/{category}_functional_report_{self.timestamp}.html',
            f'--json-report={self.output_dir}/{category}_functional_report_{self.timestamp}.json',
            f'--json-report-file={self.output_dir}/{category}_functional_report_{self.timestamp}.json'
        ]
        
        if parallel:
            pytest_args.extend(['-n', 'auto'])
        
        try:
            result = subprocess.run(pytest_args, capture_output=True, text=True, timeout=600)
            
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
                'error_message': 'Functional test execution timed out'
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
    
    def _calculate_functional_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate functional testing metrics"""
        metrics = {
            'connection_flow_reliability': 0.0,
            'transaction_processing_accuracy': 0.0,
            'balance_update_accuracy': 0.0,
            'webhook_processing_reliability': 0.0,
            'error_recovery_success_rate': 0.0,
            'multi_account_management_success': 0.0,
            'overall_functional_health': 0.0
        }
        
        if test_results['total_tests'] > 0:
            # Calculate category-specific metrics
            categories = test_results['test_categories']
            
            if 'connection_flow' in categories:
                cat = categories['connection_flow']
                if cat['total'] > 0:
                    metrics['connection_flow_reliability'] = (cat['passed'] / cat['total']) * 100
            
            if 'transaction_processing' in categories:
                cat = categories['transaction_processing']
                if cat['total'] > 0:
                    metrics['transaction_processing_accuracy'] = (cat['passed'] / cat['total']) * 100
            
            if 'balance_validation' in categories:
                cat = categories['balance_validation']
                if cat['total'] > 0:
                    metrics['balance_update_accuracy'] = (cat['passed'] / cat['total']) * 100
            
            if 'webhook_processing' in categories:
                cat = categories['webhook_processing']
                if cat['total'] > 0:
                    metrics['webhook_processing_reliability'] = (cat['passed'] / cat['total']) * 100
            
            if 'error_handling' in categories:
                cat = categories['error_handling']
                if cat['total'] > 0:
                    metrics['error_recovery_success_rate'] = (cat['passed'] / cat['total']) * 100
            
            if 'multi_account' in categories:
                cat = categories['multi_account']
                if cat['total'] > 0:
                    metrics['multi_account_management_success'] = (cat['passed'] / cat['total']) * 100
            
            # Calculate overall functional health
            metrics['overall_functional_health'] = (test_results['passed'] / test_results['total_tests']) * 100
        
        return metrics
    
    def _generate_functional_reports(self, test_results: Dict[str, Any]):
        """Generate comprehensive functional test reports"""
        # Generate JSON report
        json_report_path = self.output_dir / f"plaid_functional_test_report_{self.timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        # Generate HTML report
        html_report_path = self.output_dir / f"plaid_functional_test_report_{self.timestamp}.html"
        self._generate_functional_html_report(test_results, html_report_path)
        
        # Generate markdown report
        md_report_path = self.output_dir / f"plaid_functional_test_report_{self.timestamp}.md"
        self._generate_functional_markdown_report(test_results, md_report_path)
        
        print(f"\n📊 Functional test reports generated:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
        print(f"   Markdown: {md_report_path}")
    
    def _generate_functional_html_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate HTML functional test report"""
        metrics = test_results.get('functional_metrics', {})
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plaid Functional Test Report</title>
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
        .functional-metrics {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Plaid Functional Test Report</h1>
        <p>Generated: {test_results['timestamp']}</p>
        <p>Duration: {test_results['duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
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
    
    <div class="functional-metrics">
        <h2>Functional Health Metrics</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Connection Flow Reliability</h3>
                <p>{metrics.get('connection_flow_reliability', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Transaction Processing Accuracy</h3>
                <p>{metrics.get('transaction_processing_accuracy', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Balance Update Accuracy</h3>
                <p>{metrics.get('balance_update_accuracy', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Webhook Processing Reliability</h3>
                <p>{metrics.get('webhook_processing_reliability', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Error Recovery Success Rate</h3>
                <p>{metrics.get('error_recovery_success_rate', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Multi-Account Management Success</h3>
                <p>{metrics.get('multi_account_management_success', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Overall Functional Health</h3>
                <p>{metrics.get('overall_functional_health', 0):.1f}%</p>
            </div>
        </div>
    </div>
    
    <div class="categories">
        <h2>Functional Test Categories</h2>
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
    
    def _generate_functional_markdown_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate markdown functional test report"""
        metrics = test_results.get('functional_metrics', {})
        
        md_content = f"""# Plaid Functional Test Report

**Generated:** {test_results['timestamp']}  
**Duration:** {test_results['duration']:.2f} seconds

## Test Summary

| Metric | Count |
|--------|-------|
| Total Tests | {test_results['total_tests']} |
| Passed | {test_results['passed']} |
| Failed | {test_results['failed']} |
| Skipped | {test_results['skipped']} |
| Errors | {test_results['errors']} |

## Functional Health Metrics

| Metric | Success Rate |
|--------|-------------|
| Connection Flow Reliability | {metrics.get('connection_flow_reliability', 0):.1f}% |
| Transaction Processing Accuracy | {metrics.get('transaction_processing_accuracy', 0):.1f}% |
| Balance Update Accuracy | {metrics.get('balance_update_accuracy', 0):.1f}% |
| Webhook Processing Reliability | {metrics.get('webhook_processing_reliability', 0):.1f}% |
| Error Recovery Success Rate | {metrics.get('error_recovery_success_rate', 0):.1f}% |
| Multi-Account Management Success | {metrics.get('multi_account_management_success', 0):.1f}% |
| **Overall Functional Health** | **{metrics.get('overall_functional_health', 0):.1f}%** |

## Functional Test Categories

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
        
        md_content += """## Functional Testing Focus Areas

### 1. Bank Account Connection Flow Testing
- Link token creation and management
- Public token to access token exchange
- Account data retrieval and validation
- Multi-account connection handling
- Connection error scenarios

### 2. Transaction Data Retrieval and Processing
- Transaction data retrieval from Plaid API
- Transaction categorization and processing
- Large dataset handling
- Data validation and integrity checks
- Transaction reconciliation

### 3. Balance Update Accuracy Validation
- Real-time balance updates
- Balance discrepancy detection
- Transaction-based balance reconciliation
- Multi-currency balance handling
- Balance update error scenarios

### 4. Webhook Processing Reliability
- Transaction webhook processing
- Account update webhook handling
- Webhook signature validation
- Replay attack prevention
- Webhook error handling

### 5. Error Handling and Recovery Testing
- API error recovery mechanisms
- Database error handling
- Network timeout recovery
- Partial data recovery
- Graceful degradation

### 6. Multi-Account Management Testing
- Multiple account connection management
- Account priority management
- Account sync coordination
- Error isolation between accounts
- Data consistency validation

## Recommendations

Based on the functional test results, consider the following:

1. **Connection Flow**: Ensure all connection scenarios are working correctly
2. **Transaction Processing**: Verify transaction data accuracy and processing
3. **Balance Updates**: Monitor balance update accuracy and consistency
4. **Webhook Reliability**: Ensure webhook processing is reliable and secure
5. **Error Recovery**: Verify error handling and recovery mechanisms
6. **Multi-Account**: Test multi-account scenarios thoroughly

## Next Steps

1. Review failed functional tests and fix issues
2. Run tests again to verify fixes
3. Monitor functional health metrics in production
4. Implement continuous functional testing
5. Set up alerts for functional health degradation
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_functional_summary(self, test_results: Dict[str, Any]):
        """Print functional test summary to console"""
        metrics = test_results.get('functional_metrics', {})
        
        print("\n" + "=" * 80)
        print("📋 PLAID FUNCTIONAL TEST SUMMARY")
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
        
        print("\n🏥 Functional Health Metrics:")
        print(f"   🔗 Connection Flow Reliability: {metrics.get('connection_flow_reliability', 0):.1f}%")
        print(f"   💳 Transaction Processing Accuracy: {metrics.get('transaction_processing_accuracy', 0):.1f}%")
        print(f"   💰 Balance Update Accuracy: {metrics.get('balance_update_accuracy', 0):.1f}%")
        print(f"   🔔 Webhook Processing Reliability: {metrics.get('webhook_processing_reliability', 0):.1f}%")
        print(f"   ⚠️  Error Recovery Success Rate: {metrics.get('error_recovery_success_rate', 0):.1f}%")
        print(f"   🏦 Multi-Account Management Success: {metrics.get('multi_account_management_success', 0):.1f}%")
        print(f"   🎯 Overall Functional Health: {metrics.get('overall_functional_health', 0):.1f}%")
        
        print("\n📂 Functional Test Categories:")
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            print(f"   {category_name}: {status} ({results['passed']}/{results['total']})")
        
        print("\n" + "=" * 80)
        
        if test_results['failed'] > 0 or test_results['errors'] > 0:
            print("⚠️  Some functional tests failed. Please review the detailed reports.")
            sys.exit(1)
        else:
            print("🎉 All functional tests passed successfully!")


def main():
    """Main function for functional test runner"""
    parser = argparse.ArgumentParser(description='Plaid Functional Test Runner')
    parser.add_argument('--category', choices=['all', 'connection_flow', 'transaction_processing', 
                                              'balance_validation', 'webhook_processing', 
                                              'error_handling', 'multi_account'],
                       default='all', help='Functional test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output-dir', default='functional_test_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    runner = PlaidFunctionalTestRunner(args.output_dir)
    
    if args.category == 'all':
        runner.run_all_functional_tests(args.verbose, args.parallel)
    elif args.category == 'connection_flow':
        runner.run_connection_flow_tests(args.verbose)
    elif args.category == 'transaction_processing':
        runner.run_transaction_processing_tests(args.verbose)
    elif args.category == 'balance_validation':
        runner.run_balance_validation_tests(args.verbose)
    elif args.category == 'webhook_processing':
        runner.run_webhook_processing_tests(args.verbose)
    elif args.category == 'error_handling':
        runner.run_error_handling_tests(args.verbose)
    elif args.category == 'multi_account':
        runner.run_multi_account_tests(args.verbose)


if __name__ == '__main__':
    main() 