#!/usr/bin/env python3
"""
PostgreSQL Performance Test Runner
=================================

User-friendly interface for running comprehensive PostgreSQL performance tests.
Provides various testing options, configurations, and result reporting.

Usage:
    python run_postgresql_performance_tests.py [options]

Options:
    --quick          Run quick tests only (subset of full test suite)
    --full           Run complete test suite (default)
    --load-test      Run additional load testing
    --report-only    Generate report from existing results
    --config FILE    Use custom configuration file
    --output DIR     Specify output directory for results
    --verbose        Enable verbose logging
    --help           Show this help message
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from postgresql_performance_testing import PostgreSQLPerformanceTester


class PerformanceTestRunner:
    """Test runner with configuration management and result reporting"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.results_dir = Path(self.config.get('output_dir', 'performance_test_results'))
        self.results_dir.mkdir(exist_ok=True)
        
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'database_url': os.getenv('DATABASE_URL', 'postgresql://localhost/mingus'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'celery_broker': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
            'output_dir': 'performance_test_results',
            'test_timeout': 300,  # 5 minutes
            'max_workers': 20,
            'quick_test_queries': 10,
            'full_test_queries': 100,
            'load_test_duration': 60,  # seconds
            'load_test_users': 10
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    custom_config = json.load(f)
                default_config.update(custom_config)
                print(f"Loaded configuration from {config_file}")
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        return default_config
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run a subset of tests for quick validation"""
        print("🚀 Running Quick Performance Tests...")
        print("=" * 50)
        
        # Modify config for quick tests
        quick_config = self.config.copy()
        quick_config['quick_test_queries'] = 5
        quick_config['max_workers'] = 5
        
        tester = PostgreSQLPerformanceTester(quick_config)
        
        try:
            # Run only essential tests
            results = {
                'timestamp': datetime.now().isoformat(),
                'test_type': 'quick',
                'tests': []
            }
            
            # Essential test categories
            essential_tests = [
                ('Database Connection Pooling', tester.test_connection_pooling),
                ('Query Performance', tester.test_query_performance),
                ('Redis Caching', tester.test_redis_caching),
                ('System Resources', tester.test_system_resources)
            ]
            
            for category_name, test_func in essential_tests:
                try:
                    print(f"Running {category_name}...")
                    result = test_func()
                    results['tests'].append({
                        'category': category_name,
                        'result': result
                    })
                    print(f"✅ {category_name} completed")
                except Exception as e:
                    print(f"❌ {category_name} failed: {e}")
                    results['tests'].append({
                        'category': category_name,
                        'error': str(e)
                    })
            
            # Generate summary
            results['summary'] = tester._generate_summary(results['tests'])
            
            return results
            
        finally:
            tester.cleanup()
    
    def run_full_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🚀 Running Full Performance Test Suite...")
        print("=" * 50)
        
        tester = PostgreSQLPerformanceTester(self.config)
        
        try:
            results = tester.run_all_tests()
            results['test_type'] = 'full'
            return results
        finally:
            tester.cleanup()
    
    def run_load_tests(self) -> Dict[str, Any]:
        """Run additional load testing"""
        print("🚀 Running Load Performance Tests...")
        print("=" * 50)
        
        # This would integrate with Locust or similar load testing tool
        # For now, we'll use the built-in load testing from the main tester
        
        tester = PostgreSQLPerformanceTester(self.config)
        
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'test_type': 'load',
                'tests': []
            }
            
            # Run load-specific tests
            load_tests = [
                ('Load Performance', tester.test_load_performance),
                ('System Resources', tester.test_system_resources),
                ('Database Connection Pooling', tester.test_connection_pooling)
            ]
            
            for category_name, test_func in load_tests:
                try:
                    print(f"Running {category_name} under load...")
                    result = test_func()
                    results['tests'].append({
                        'category': category_name,
                        'result': result
                    })
                    print(f"✅ {category_name} completed")
                except Exception as e:
                    print(f"❌ {category_name} failed: {e}")
                    results['tests'].append({
                        'category': category_name,
                        'error': str(e)
                    })
            
            # Generate summary
            results['summary'] = tester._generate_summary(results['tests'])
            
            return results
            
        finally:
            tester.cleanup()
    
    def save_results(self, results: Dict[str, Any], test_type: str) -> str:
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{test_type}_performance_test_results_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return str(filepath)
    
    def generate_report(self, results_file: str) -> str:
        """Generate a human-readable report from test results"""
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except Exception as e:
            print(f"Error reading results file: {e}")
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"performance_test_report_{timestamp}.md"
        report_path = self.results_dir / report_filename
        
        with open(report_path, 'w') as f:
            f.write(self._generate_markdown_report(results))
        
        return str(report_path)
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report from test results"""
        report = []
        
        # Header
        report.append("# PostgreSQL Performance Test Report")
        report.append("")
        report.append(f"**Generated:** {results.get('timestamp', 'Unknown')}")
        report.append(f"**Test Type:** {results.get('test_type', 'Unknown')}")
        report.append("")
        
        # Summary
        summary = results.get('summary', {})
        report.append("## 📊 Executive Summary")
        report.append("")
        report.append(f"- **Total Tests:** {summary.get('total_tests', 0)}")
        report.append(f"- **Passed:** {summary.get('passed_tests', 0)}")
        report.append(f"- **Failed:** {summary.get('failed_tests', 0)}")
        report.append(f"- **Warnings:** {summary.get('warning_tests', 0)}")
        report.append(f"- **Success Rate:** {summary.get('success_rate', 0):.2%}")
        report.append("")
        
        # Overall Performance
        overall_perf = summary.get('overall_performance', {})
        report.append("## ⚡ Overall Performance")
        report.append("")
        report.append(f"- **Average Response Time:** {overall_perf.get('avg_response_time_ms', 0):.2f}ms")
        report.append(f"- **Average Memory Usage:** {overall_perf.get('avg_memory_usage_mb', 0):.2f}MB")
        report.append(f"- **Average CPU Usage:** {overall_perf.get('avg_cpu_usage_percent', 0):.2f}%")
        report.append("")
        
        # Test Results
        report.append("## 🧪 Test Results")
        report.append("")
        
        for test in results.get('tests', []):
            category = test.get('category', 'Unknown')
            if 'result' in test:
                result = test['result']
                status = result.get('status', 'unknown')
                status_emoji = {'passed': '✅', 'failed': '❌', 'warning': '⚠️'}.get(status, '❓')
                
                report.append(f"### {status_emoji} {category}")
                report.append("")
                
                if hasattr(result, 'metrics'):
                    metrics = result.metrics
                    report.append(f"- **Response Time:** {metrics.response_time_ms:.2f}ms")
                    report.append(f"- **Throughput:** {metrics.throughput_rps:.2f} req/s")
                    report.append(f"- **Memory Usage:** {metrics.memory_usage_mb:.2f}MB")
                    report.append(f"- **CPU Usage:** {metrics.cpu_usage_percent:.2f}%")
                    report.append(f"- **Errors:** {metrics.errors}")
                    report.append("")
                
                if hasattr(result, 'recommendations') and result.recommendations:
                    report.append("**Recommendations:**")
                    for rec in result.recommendations:
                        report.append(f"- {rec}")
                    report.append("")
            else:
                report.append(f"### ❌ {category}")
                report.append("")
                report.append(f"Error: {test.get('error', 'Unknown error')}")
                report.append("")
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            report.append("## 📋 Recommendations")
            report.append("")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        # Footer
        report.append("---")
        report.append("*Report generated by PostgreSQL Performance Testing Suite*")
        
        return "\n".join(report)
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary to console"""
        summary = results.get('summary', {})
        
        print("\n" + "="*80)
        print("POSTGRESQL PERFORMANCE TESTING SUMMARY")
        print("="*80)
        
        print(f"Test Type: {results.get('test_type', 'Unknown')}")
        print(f"Timestamp: {results.get('timestamp', 'Unknown')}")
        print("")
        
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Warnings: {summary.get('warning_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.2%}")
        
        overall_perf = summary.get('overall_performance', {})
        print(f"\nOverall Performance:")
        print(f"  Average Response Time: {overall_perf.get('avg_response_time_ms', 0):.2f}ms")
        print(f"  Average Memory Usage: {overall_perf.get('avg_memory_usage_mb', 0):.2f}MB")
        print(f"  Average CPU Usage: {overall_perf.get('avg_cpu_usage_percent', 0):.2f}%")
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("="*80)


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Performance Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only (subset of full test suite)')
    parser.add_argument('--full', action='store_true',
                       help='Run complete test suite (default)')
    parser.add_argument('--load-test', action='store_true',
                       help='Run additional load testing')
    parser.add_argument('--report-only', metavar='FILE',
                       help='Generate report from existing results file')
    parser.add_argument('--config', metavar='FILE',
                       help='Use custom configuration file')
    parser.add_argument('--output', metavar='DIR',
                       help='Specify output directory for results')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Create runner
    runner = PerformanceTestRunner(args.config)
    
    if args.output:
        runner.results_dir = Path(args.output)
        runner.results_dir.mkdir(exist_ok=True)
    
    try:
        if args.report_only:
            # Generate report from existing results
            report_path = runner.generate_report(args.report_only)
            print(f"Report generated: {report_path}")
            return 0
        
        # Run tests based on arguments
        if args.quick:
            results = runner.run_quick_tests()
            test_type = 'quick'
        elif args.load_test:
            results = runner.run_load_tests()
            test_type = 'load'
        else:
            # Default to full tests
            results = runner.run_full_tests()
            test_type = 'full'
        
        # Save results
        results_file = runner.save_results(results, test_type)
        print(f"\nResults saved to: {results_file}")
        
        # Generate report
        report_path = runner.generate_report(results_file)
        print(f"Report generated: {report_path}")
        
        # Print summary
        runner.print_summary(results)
        
        # Return appropriate exit code
        summary = results.get('summary', {})
        if summary.get('failed_tests', 0) > 0:
            return 1
        elif summary.get('warning_tests', 0) > 0:
            return 2
        else:
            return 0
            
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 130
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
