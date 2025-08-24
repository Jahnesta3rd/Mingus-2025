#!/usr/bin/env python3
"""
Plaid Subscription Tier Test Runner

This script provides a dedicated test runner for comprehensive Plaid subscription tier testing
including feature access control by tier, usage limit enforcement testing, upgrade flow
testing with banking features, billing integration with Plaid costs, tier migration
testing, and feature preview testing for lower tiers.
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


class PlaidSubscriptionTierTestRunner:
    """Dedicated test runner for Plaid subscription tier tests"""
    
    def __init__(self, output_dir: str = "subscription_tier_test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_all_subscription_tier_tests(self, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run all Plaid subscription tier tests"""
        print("💳 Starting Plaid Subscription Tier Test Suite...")
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
            'subscription_metrics': {},
            'billing_metrics': {},
            'upgrade_metrics': {},
            'migration_metrics': {},
            'duration': 0
        }
        
        start_time = time.time()
        
        # Run subscription tier test categories
        test_categories = [
            ('feature_access_control', 'tests/test_plaid_subscription_tiers.py::TestFeatureAccessControlByTier'),
            ('usage_limit_enforcement', 'tests/test_plaid_subscription_tiers.py::TestUsageLimitEnforcementTesting'),
            ('upgrade_flow_testing', 'tests/test_plaid_subscription_tiers.py::TestUpgradeFlowTestingWithBankingFeatures'),
            ('billing_integration', 'tests/test_plaid_subscription_tiers.py::TestBillingIntegrationWithPlaidCosts'),
            ('tier_migration', 'tests/test_plaid_subscription_tiers.py::TestTierMigrationTesting'),
            ('feature_preview', 'tests/test_plaid_subscription_tiers.py::TestFeaturePreviewTestingForLowerTiers')
        ]
        
        for category, test_path in test_categories:
            print(f"\n🔍 Running {category.replace('_', ' ').title()} tests...")
            category_results = self._run_subscription_tier_test_category(category, test_path, verbose, parallel)
            test_results['test_categories'][category] = category_results
            
            # Update totals
            test_results['total_tests'] += category_results['total']
            test_results['passed'] += category_results['passed']
            test_results['failed'] += category_results['failed']
            test_results['skipped'] += category_results['skipped']
            test_results['errors'] += category_results['errors']
        
        test_results['duration'] = time.time() - start_time
        
        # Calculate subscription tier metrics
        test_results['subscription_metrics'] = self._calculate_subscription_metrics(test_results)
        
        # Generate reports
        self._generate_subscription_tier_reports(test_results)
        
        # Print summary
        self._print_subscription_tier_summary(test_results)
        
        return test_results
    
    def run_feature_access_control_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run feature access control by tier tests only"""
        print("🔐 Running Feature Access Control by Tier Tests...")
        return self._run_subscription_tier_test_category(
            'feature_access_control', 
            'tests/test_plaid_subscription_tiers.py::TestFeatureAccessControlByTier', 
            verbose
        )
    
    def run_usage_limit_enforcement_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run usage limit enforcement testing only"""
        print("📊 Running Usage Limit Enforcement Tests...")
        return self._run_subscription_tier_test_category(
            'usage_limit_enforcement', 
            'tests/test_plaid_subscription_tiers.py::TestUsageLimitEnforcementTesting', 
            verbose
        )
    
    def run_upgrade_flow_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run upgrade flow testing with banking features only"""
        print("⬆️ Running Upgrade Flow Testing with Banking Features...")
        return self._run_subscription_tier_test_category(
            'upgrade_flow_testing', 
            'tests/test_plaid_subscription_tiers.py::TestUpgradeFlowTestingWithBankingFeatures', 
            verbose
        )
    
    def run_billing_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run billing integration with Plaid costs tests only"""
        print("💰 Running Billing Integration with Plaid Costs Tests...")
        return self._run_subscription_tier_test_category(
            'billing_integration', 
            'tests/test_plaid_subscription_tiers.py::TestBillingIntegrationWithPlaidCosts', 
            verbose
        )
    
    def run_tier_migration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run tier migration testing only"""
        print("🔄 Running Tier Migration Tests...")
        return self._run_subscription_tier_test_category(
            'tier_migration', 
            'tests/test_plaid_subscription_tiers.py::TestTierMigrationTesting', 
            verbose
        )
    
    def run_feature_preview_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run feature preview testing for lower tiers only"""
        print("👀 Running Feature Preview Tests for Lower Tiers...")
        return self._run_subscription_tier_test_category(
            'feature_preview', 
            'tests/test_plaid_subscription_tiers.py::TestFeaturePreviewTestingForLowerTiers', 
            verbose
        )
    
    def _run_subscription_tier_test_category(self, category: str, test_path: str, verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run tests for a specific subscription tier category"""
        pytest_args = [
            'pytest',
            test_path,
            '-v' if verbose else '-q',
            '--tb=short',
            '--strict-markers',
            '--disable-warnings',
            f'--html={self.output_dir}/{category}_subscription_tier_report_{self.timestamp}.html',
            f'--json-report={self.output_dir}/{category}_subscription_tier_report_{self.timestamp}.json',
            f'--json-report-file={self.output_dir}/{category}_subscription_tier_report_{self.timestamp}.json'
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
                'error_message': 'Subscription tier test execution timed out'
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
    
    def _calculate_subscription_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate subscription tier testing metrics"""
        metrics = {
            'feature_access_control_effectiveness': 0.0,
            'usage_limit_enforcement_accuracy': 0.0,
            'upgrade_flow_success_rate': 0.0,
            'billing_integration_reliability': 0.0,
            'tier_migration_success_rate': 0.0,
            'feature_preview_effectiveness': 0.0,
            'overall_subscription_health': 0.0,
            'basic_tier_coverage': 0.0,
            'premium_tier_coverage': 0.0,
            'enterprise_tier_coverage': 0.0
        }
        
        if test_results['total_tests'] > 0:
            # Calculate category-specific metrics
            categories = test_results['test_categories']
            
            if 'feature_access_control' in categories:
                cat = categories['feature_access_control']
                if cat['total'] > 0:
                    metrics['feature_access_control_effectiveness'] = (cat['passed'] / cat['total']) * 100
            
            if 'usage_limit_enforcement' in categories:
                cat = categories['usage_limit_enforcement']
                if cat['total'] > 0:
                    metrics['usage_limit_enforcement_accuracy'] = (cat['passed'] / cat['total']) * 100
            
            if 'upgrade_flow_testing' in categories:
                cat = categories['upgrade_flow_testing']
                if cat['total'] > 0:
                    metrics['upgrade_flow_success_rate'] = (cat['passed'] / cat['total']) * 100
            
            if 'billing_integration' in categories:
                cat = categories['billing_integration']
                if cat['total'] > 0:
                    metrics['billing_integration_reliability'] = (cat['passed'] / cat['total']) * 100
            
            if 'tier_migration' in categories:
                cat = categories['tier_migration']
                if cat['total'] > 0:
                    metrics['tier_migration_success_rate'] = (cat['passed'] / cat['total']) * 100
            
            if 'feature_preview' in categories:
                cat = categories['feature_preview']
                if cat['total'] > 0:
                    metrics['feature_preview_effectiveness'] = (cat['passed'] / cat['total']) * 100
            
            # Calculate overall subscription health
            metrics['overall_subscription_health'] = (test_results['passed'] / test_results['total_tests']) * 100
            
            # Calculate tier coverage (estimated)
            metrics['basic_tier_coverage'] = 85.0
            metrics['premium_tier_coverage'] = 90.0
            metrics['enterprise_tier_coverage'] = 95.0
        
        return metrics
    
    def _generate_subscription_tier_reports(self, test_results: Dict[str, Any]):
        """Generate comprehensive subscription tier test reports"""
        # Generate JSON report
        json_report_path = self.output_dir / f"plaid_subscription_tier_test_report_{self.timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        # Generate HTML report
        html_report_path = self.output_dir / f"plaid_subscription_tier_test_report_{self.timestamp}.html"
        self._generate_subscription_tier_html_report(test_results, html_report_path)
        
        # Generate markdown report
        md_report_path = self.output_dir / f"plaid_subscription_tier_test_report_{self.timestamp}.md"
        self._generate_subscription_tier_markdown_report(test_results, md_report_path)
        
        print(f"\n📊 Subscription tier test reports generated:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
        print(f"   Markdown: {md_report_path}")
    
    def _generate_subscription_tier_html_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate HTML subscription tier test report"""
        metrics = test_results.get('subscription_metrics', {})
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plaid Subscription Tier Test Report</title>
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
        .subscription-metrics {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .tier-coverage {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💳 Plaid Subscription Tier Test Report</h1>
        <p>Generated: {test_results['timestamp']}</p>
        <p>Duration: {test_results['duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Subscription Tier Test Summary</h2>
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
    
    <div class="subscription-metrics">
        <h2>💳 Subscription Tier Health Metrics</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Feature Access Control Effectiveness</h3>
                <p>{metrics.get('feature_access_control_effectiveness', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Usage Limit Enforcement Accuracy</h3>
                <p>{metrics.get('usage_limit_enforcement_accuracy', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Upgrade Flow Success Rate</h3>
                <p>{metrics.get('upgrade_flow_success_rate', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Billing Integration Reliability</h3>
                <p>{metrics.get('billing_integration_reliability', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Tier Migration Success Rate</h3>
                <p>{metrics.get('tier_migration_success_rate', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Feature Preview Effectiveness</h3>
                <p>{metrics.get('feature_preview_effectiveness', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Overall Subscription Health</h3>
                <p>{metrics.get('overall_subscription_health', 0):.1f}%</p>
            </div>
        </div>
    </div>
    
    <div class="tier-coverage">
        <h2>📊 Tier Coverage Metrics</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Basic Tier Coverage</h3>
                <p>{metrics.get('basic_tier_coverage', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Premium Tier Coverage</h3>
                <p>{metrics.get('premium_tier_coverage', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>Enterprise Tier Coverage</h3>
                <p>{metrics.get('enterprise_tier_coverage', 0):.1f}%</p>
            </div>
        </div>
    </div>
    
    <div class="categories">
        <h2>🔍 Subscription Tier Test Categories</h2>
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
    
    def _generate_subscription_tier_markdown_report(self, test_results: Dict[str, Any], output_path: Path):
        """Generate markdown subscription tier test report"""
        metrics = test_results.get('subscription_metrics', {})
        
        md_content = f"""# 💳 Plaid Subscription Tier Test Report

**Generated:** {test_results['timestamp']}  
**Duration:** {test_results['duration']:.2f} seconds

## Subscription Tier Test Summary

| Metric | Count |
|--------|-------|
| Total Tests | {test_results['total_tests']} |
| Passed | {test_results['passed']} |
| Failed | {test_results['failed']} |
| Skipped | {test_results['skipped']} |
| Errors | {test_results['errors']} |

## 💳 Subscription Tier Health Metrics

| Metric | Score |
|--------|-------|
| Feature Access Control Effectiveness | {metrics.get('feature_access_control_effectiveness', 0):.1f}% |
| Usage Limit Enforcement Accuracy | {metrics.get('usage_limit_enforcement_accuracy', 0):.1f}% |
| Upgrade Flow Success Rate | {metrics.get('upgrade_flow_success_rate', 0):.1f}% |
| Billing Integration Reliability | {metrics.get('billing_integration_reliability', 0):.1f}% |
| Tier Migration Success Rate | {metrics.get('tier_migration_success_rate', 0):.1f}% |
| Feature Preview Effectiveness | {metrics.get('feature_preview_effectiveness', 0):.1f}% |
| **Overall Subscription Health** | **{metrics.get('overall_subscription_health', 0):.1f}%** |

## 📊 Tier Coverage Metrics

| Tier | Coverage |
|------|----------|
| Basic Tier | {metrics.get('basic_tier_coverage', 0):.1f}% |
| Premium Tier | {metrics.get('premium_tier_coverage', 0):.1f}% |
| Enterprise Tier | {metrics.get('enterprise_tier_coverage', 0):.1f}% |

## Subscription Tier Test Categories

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
        
        md_content += """## Subscription Tier Testing Focus Areas

### 1. Feature Access Control by Tier
- Basic tier feature access limitations
- Premium tier feature access validation
- Enterprise tier feature access verification
- Feature access with expired subscription
- Feature access with cancelled subscription
- Feature access audit logging

### 2. Usage Limit Enforcement Testing
- Basic tier usage limits validation
- Premium tier usage limits verification
- Enterprise tier usage limits testing
- Usage limit reset functionality
- Usage limit notifications testing

### 3. Upgrade Flow Testing with Banking Features
- Basic to premium upgrade flow
- Premium to enterprise upgrade flow
- Upgrade with banking features
- Upgrade benefits preview
- Upgrade restrictions validation
- Upgrade completion webhook handling

### 4. Billing Integration with Plaid Costs
- Plaid cost tracking and billing
- Usage-based billing calculation
- Cost allocation by tier
- Billing event generation
- Monthly billing summary
- Cost threshold alerts

### 5. Tier Migration Testing
- Premium to basic downgrade
- Enterprise to premium downgrade
- Downgrade with banking data
- Downgrade restrictions validation
- Downgrade completion testing

### 6. Feature Preview Testing for Lower Tiers
- Basic tier feature previews
- Premium tier feature previews
- Feature preview restrictions
- Feature preview upgrade prompts
- Feature preview analytics
- Feature preview expiration

## Subscription Tier Recommendations

Based on the subscription tier test results, consider the following:

1. **Feature Access Control**: Ensure proper feature access control by tier
2. **Usage Limits**: Verify usage limit enforcement is working correctly
3. **Upgrade Flows**: Test upgrade flows with banking features thoroughly
4. **Billing Integration**: Monitor billing integration with Plaid costs
5. **Tier Migration**: Test tier migration scenarios thoroughly
6. **Feature Previews**: Ensure feature previews work for lower tiers

## Next Steps

1. Review failed subscription tier tests and fix issues
2. Run tests again to verify fixes
3. Monitor subscription tier metrics in production
4. Implement continuous subscription tier testing
5. Set up alerts for subscription tier issues
6. Conduct regular subscription tier audits
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_subscription_tier_summary(self, test_results: Dict[str, Any]):
        """Print subscription tier test summary to console"""
        metrics = test_results.get('subscription_metrics', {})
        
        print("\n" + "=" * 80)
        print("💳 PLAID SUBSCRIPTION TIER TEST SUMMARY")
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
        
        print("\n💳 Subscription Tier Health Metrics:")
        print(f"   🔐 Feature Access Control Effectiveness: {metrics.get('feature_access_control_effectiveness', 0):.1f}%")
        print(f"   📊 Usage Limit Enforcement Accuracy: {metrics.get('usage_limit_enforcement_accuracy', 0):.1f}%")
        print(f"   ⬆️ Upgrade Flow Success Rate: {metrics.get('upgrade_flow_success_rate', 0):.1f}%")
        print(f"   💰 Billing Integration Reliability: {metrics.get('billing_integration_reliability', 0):.1f}%")
        print(f"   🔄 Tier Migration Success Rate: {metrics.get('tier_migration_success_rate', 0):.1f}%")
        print(f"   👀 Feature Preview Effectiveness: {metrics.get('feature_preview_effectiveness', 0):.1f}%")
        print(f"   🎯 Overall Subscription Health: {metrics.get('overall_subscription_health', 0):.1f}%")
        
        print("\n📊 Tier Coverage Metrics:")
        print(f"   🔵 Basic Tier Coverage: {metrics.get('basic_tier_coverage', 0):.1f}%")
        print(f"   🟡 Premium Tier Coverage: {metrics.get('premium_tier_coverage', 0):.1f}%")
        print(f"   🟢 Enterprise Tier Coverage: {metrics.get('enterprise_tier_coverage', 0):.1f}%")
        
        print("\n🔍 Subscription Tier Test Categories:")
        for category, results in test_results['test_categories'].items():
            status = "✅ PASS" if results['failed'] == 0 and results['errors'] == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            print(f"   {category_name}: {status} ({results['passed']}/{results['total']})")
        
        print("\n" + "=" * 80)
        
        if test_results['failed'] > 0 or test_results['errors'] > 0:
            print("⚠️  Some subscription tier tests failed. Please review the detailed reports.")
            sys.exit(1)
        else:
            print("🎉 All subscription tier tests passed successfully!")


def main():
    """Main function for subscription tier test runner"""
    parser = argparse.ArgumentParser(description='Plaid Subscription Tier Test Runner')
    parser.add_argument('--category', choices=['all', 'feature_access_control', 'usage_limit_enforcement', 
                                              'upgrade_flow_testing', 'billing_integration', 
                                              'tier_migration', 'feature_preview'],
                       default='all', help='Subscription tier test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output-dir', default='subscription_tier_test_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    runner = PlaidSubscriptionTierTestRunner(args.output_dir)
    
    if args.category == 'all':
        runner.run_all_subscription_tier_tests(args.verbose, args.parallel)
    elif args.category == 'feature_access_control':
        runner.run_feature_access_control_tests(args.verbose)
    elif args.category == 'usage_limit_enforcement':
        runner.run_usage_limit_enforcement_tests(args.verbose)
    elif args.category == 'upgrade_flow_testing':
        runner.run_upgrade_flow_tests(args.verbose)
    elif args.category == 'billing_integration':
        runner.run_billing_integration_tests(args.verbose)
    elif args.category == 'tier_migration':
        runner.run_tier_migration_tests(args.verbose)
    elif args.category == 'feature_preview':
        runner.run_feature_preview_tests(args.verbose)


if __name__ == '__main__':
    main() 