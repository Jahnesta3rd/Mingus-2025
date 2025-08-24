#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for MINGUS Application
Runs performance testing and compliance testing with detailed reporting
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import unittest
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.performance.test_comprehensive_performance import ComprehensivePerformanceTests
from tests.compliance.test_comprehensive_compliance import ComprehensiveComplianceTests


class ComprehensiveTestRunner:
    """Comprehensive test runner for performance and compliance testing"""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = output_dir
        self.start_time = time.time()
        self.test_results = {
            'performance': {},
            'compliance': {},
            'summary': {}
        }
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Test configuration
        self.performance_thresholds = {
            'single_operation': 1.0,
            'batch_operation': 5.0,
            'concurrent_operation': 10.0,
            'memory_usage_mb': 500,
            'cpu_usage_percent': 80,
            'response_time_ms': 2000,
            'throughput_ops_per_sec': 100,
            'error_rate_percent': 5.0
        }
        
        self.compliance_requirements = {
            'pci_dss': {
                'payment_data_encryption': True,
                'key_management': True,
                'transmission_security': True,
                'access_controls': True,
                'audit_logging': True
            },
            'gdpr': {
                'consent_management': True,
                'data_subject_rights': True,
                'data_minimization': True
            },
            'sox': {
                'financial_data_integrity': True
            },
            'glba': {
                'customer_data_protection': True
            },
            'audit': {
                'audit_trail_completeness': True
            }
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance tests"""
        print("🚀 Starting Performance Testing Suite...")
        
        performance_results = {
            'start_time': datetime.utcnow().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'thresholds': self.performance_thresholds,
            'test_details': []
        }
        
        try:
            # Create test suite
            performance_suite = unittest.TestLoader().loadTestsFromTestCase(ComprehensivePerformanceTests)
            
            # Run tests with custom result collector
            result_collector = PerformanceResultCollector()
            performance_suite.run(result_collector)
            
            # Process results
            performance_results['tests_run'] = result_collector.tests_run
            performance_results['tests_passed'] = result_collector.tests_passed
            performance_results['tests_failed'] = result_collector.tests_failed
            
            # Calculate performance metrics
            if result_collector.test_results:
                performance_results['performance_metrics'] = self._calculate_performance_metrics(
                    result_collector.test_results
                )
                performance_results['test_details'] = result_collector.test_results
            
            performance_results['end_time'] = datetime.utcnow().isoformat()
            performance_results['duration'] = time.time() - self.start_time
            
            print(f"✅ Performance Tests Completed: {performance_results['tests_passed']}/{performance_results['tests_run']} passed")
            
        except Exception as e:
            print(f"❌ Performance Tests Failed: {str(e)}")
            performance_results['error'] = str(e)
            performance_results['traceback'] = traceback.format_exc()
        
        return performance_results
    
    def run_compliance_tests(self) -> Dict[str, Any]:
        """Run comprehensive compliance tests"""
        print("🔒 Starting Compliance Testing Suite...")
        
        compliance_results = {
            'start_time': datetime.utcnow().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'compliance_status': {},
            'requirements': self.compliance_requirements,
            'test_details': []
        }
        
        try:
            # Create test suite
            compliance_suite = unittest.TestLoader().loadTestsFromTestCase(ComprehensiveComplianceTests)
            
            # Run tests with custom result collector
            result_collector = ComplianceResultCollector()
            compliance_suite.run(result_collector)
            
            # Process results
            compliance_results['tests_run'] = result_collector.tests_run
            compliance_results['tests_passed'] = result_collector.tests_passed
            compliance_results['tests_failed'] = result_collector.tests_failed
            
            # Calculate compliance status
            if result_collector.test_results:
                compliance_results['compliance_status'] = self._calculate_compliance_status(
                    result_collector.test_results
                )
                compliance_results['test_details'] = result_collector.test_results
            
            compliance_results['end_time'] = datetime.utcnow().isoformat()
            compliance_results['duration'] = time.time() - self.start_time
            
            print(f"✅ Compliance Tests Completed: {compliance_results['tests_passed']}/{compliance_results['tests_run']} passed")
            
        except Exception as e:
            print(f"❌ Compliance Tests Failed: {str(e)}")
            compliance_results['error'] = str(e)
            compliance_results['traceback'] = traceback.format_exc()
        
        return compliance_results
    
    def _calculate_performance_metrics(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        metrics = {
            'average_execution_time': 0,
            'max_execution_time': 0,
            'min_execution_time': float('inf'),
            'total_operations': 0,
            'average_throughput': 0,
            'memory_usage': {
                'average_mb': 0,
                'max_mb': 0
            },
            'cpu_usage': {
                'average_percent': 0,
                'max_percent': 0
            },
            'response_times': {
                'average_ms': 0,
                'p95_ms': 0,
                'p99_ms': 0
            }
        }
        
        if not test_results:
            return metrics
        
        execution_times = []
        throughputs = []
        memory_usages = []
        cpu_usages = []
        response_times = []
        
        for result in test_results:
            if result.get('success'):
                # Execution time
                if 'execution_time' in result:
                    execution_times.append(result['execution_time'])
                
                # Throughput
                if 'metrics' in result and 'throughput_predictions_per_second' in result['metrics']:
                    throughputs.append(result['metrics']['throughput_predictions_per_second'])
                
                # Memory usage
                if 'resource_usage' in result and 'memory_used_mb' in result['resource_usage']:
                    memory_usages.append(result['resource_usage']['memory_used_mb'])
                
                # CPU usage
                if 'resource_usage' in result and 'cpu_percent' in result['resource_usage']:
                    cpu_usages.append(result['resource_usage']['cpu_percent'])
                
                # Response times
                if 'metrics' in result and 'average_response_time_ms' in result['metrics']:
                    response_times.append(result['metrics']['average_response_time_ms'])
        
        # Calculate averages and extremes
        if execution_times:
            metrics['average_execution_time'] = sum(execution_times) / len(execution_times)
            metrics['max_execution_time'] = max(execution_times)
            metrics['min_execution_time'] = min(execution_times)
        
        if throughputs:
            metrics['average_throughput'] = sum(throughputs) / len(throughputs)
        
        if memory_usages:
            metrics['memory_usage']['average_mb'] = sum(memory_usages) / len(memory_usages)
            metrics['memory_usage']['max_mb'] = max(memory_usages)
        
        if cpu_usages:
            metrics['cpu_usage']['average_percent'] = sum(cpu_usages) / len(cpu_usages)
            metrics['cpu_usage']['max_percent'] = max(cpu_usages)
        
        if response_times:
            metrics['response_times']['average_ms'] = sum(response_times) / len(response_times)
            sorted_response_times = sorted(response_times)
            p95_index = int(len(sorted_response_times) * 0.95)
            p99_index = int(len(sorted_response_times) * 0.99)
            metrics['response_times']['p95_ms'] = sorted_response_times[p95_index] if p95_index < len(sorted_response_times) else sorted_response_times[-1]
            metrics['response_times']['p99_ms'] = sorted_response_times[p99_index] if p99_index < len(sorted_response_times) else sorted_response_times[-1]
        
        return metrics
    
    def _calculate_compliance_status(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate compliance status by regulation"""
        compliance_status = {
            'pci_dss': {'compliant': True, 'tests_passed': 0, 'tests_total': 0, 'violations': []},
            'gdpr': {'compliant': True, 'tests_passed': 0, 'tests_total': 0, 'violations': []},
            'sox': {'compliant': True, 'tests_passed': 0, 'tests_total': 0, 'violations': []},
            'glba': {'compliant': True, 'tests_passed': 0, 'tests_total': 0, 'violations': []},
            'audit': {'compliant': True, 'tests_passed': 0, 'tests_total': 0, 'violations': []}
        }
        
        for result in test_results:
            regulation = result.get('regulation', '').lower()
            if regulation in compliance_status:
                compliance_status[regulation]['tests_total'] += 1
                
                if result.get('compliant', False):
                    compliance_status[regulation]['tests_passed'] += 1
                else:
                    compliance_status[regulation]['compliant'] = False
                    if 'violations' in result:
                        compliance_status[regulation]['violations'].extend(result['violations'])
        
        # Calculate compliance percentages
        for regulation in compliance_status:
            total = compliance_status[regulation]['tests_total']
            passed = compliance_status[regulation]['tests_passed']
            if total > 0:
                compliance_status[regulation]['compliance_percentage'] = (passed / total) * 100
            else:
                compliance_status[regulation]['compliance_percentage'] = 0
        
        return compliance_status
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("📊 Generating Comprehensive Test Report...")
        
        # Run both test suites
        performance_results = self.run_performance_tests()
        compliance_results = self.run_compliance_tests()
        
        # Create comprehensive report
        comprehensive_report = {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'test_suite_version': '1.0.0',
                'mingus_version': '1.0.0',
                'total_duration': time.time() - self.start_time
            },
            'executive_summary': {
                'overall_status': 'PASS' if (performance_results.get('tests_failed', 0) == 0 and 
                                           compliance_results.get('tests_failed', 0) == 0) else 'FAIL',
                'performance_status': 'PASS' if performance_results.get('tests_failed', 0) == 0 else 'FAIL',
                'compliance_status': 'PASS' if compliance_results.get('tests_failed', 0) == 0 else 'FAIL',
                'total_tests': (performance_results.get('tests_run', 0) + 
                              compliance_results.get('tests_run', 0)),
                'total_passed': (performance_results.get('tests_passed', 0) + 
                               compliance_results.get('tests_passed', 0)),
                'total_failed': (performance_results.get('tests_failed', 0) + 
                               compliance_results.get('tests_failed', 0))
            },
            'performance_testing': performance_results,
            'compliance_testing': compliance_results,
            'recommendations': self._generate_recommendations(performance_results, compliance_results)
        }
        
        # Save comprehensive report
        report_filename = f"comprehensive_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(self.output_dir, report_filename)
        
        with open(report_path, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        # Generate human-readable summary
        self._generate_human_readable_summary(comprehensive_report, report_path)
        
        print(f"📄 Comprehensive report saved to: {report_path}")
        
        return comprehensive_report
    
    def _generate_recommendations(self, performance_results: Dict[str, Any], 
                                compliance_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Performance recommendations
        if performance_results.get('tests_failed', 0) > 0:
            recommendations.append("Review failed performance tests and optimize system performance")
        
        performance_metrics = performance_results.get('performance_metrics', {})
        
        if performance_metrics.get('average_execution_time', 0) > self.performance_thresholds['single_operation']:
            recommendations.append("Optimize single operation execution time to meet performance thresholds")
        
        if performance_metrics.get('memory_usage', {}).get('max_mb', 0) > self.performance_thresholds['memory_usage_mb']:
            recommendations.append("Optimize memory usage to stay within acceptable limits")
        
        if performance_metrics.get('cpu_usage', {}).get('max_percent', 0) > self.performance_thresholds['cpu_usage_percent']:
            recommendations.append("Optimize CPU usage to prevent resource exhaustion")
        
        # Compliance recommendations
        if compliance_results.get('tests_failed', 0) > 0:
            recommendations.append("Address compliance violations to meet regulatory requirements")
        
        compliance_status = compliance_results.get('compliance_status', {})
        
        for regulation, status in compliance_status.items():
            if not status.get('compliant', True):
                violations = status.get('violations', [])
                recommendations.append(f"Address {regulation.upper()} violations: {', '.join(violations[:3])}")
        
        if not recommendations:
            recommendations.append("All tests passed successfully. Continue monitoring performance and compliance.")
        
        return recommendations
    
    def _generate_human_readable_summary(self, report: Dict[str, Any], report_path: str):
        """Generate human-readable summary"""
        summary_filename = report_path.replace('.json', '_summary.txt')
        
        with open(summary_filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MINGUS COMPREHENSIVE TEST REPORT SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            # Executive Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 20 + "\n")
            executive = report['executive_summary']
            f.write(f"Overall Status: {executive['overall_status']}\n")
            f.write(f"Performance Status: {executive['performance_status']}\n")
            f.write(f"Compliance Status: {executive['compliance_status']}\n")
            f.write(f"Total Tests: {executive['total_tests']}\n")
            f.write(f"Tests Passed: {executive['total_passed']}\n")
            f.write(f"Tests Failed: {executive['total_failed']}\n\n")
            
            # Performance Summary
            f.write("PERFORMANCE TESTING SUMMARY\n")
            f.write("-" * 30 + "\n")
            perf = report['performance_testing']
            f.write(f"Tests Run: {perf.get('tests_run', 0)}\n")
            f.write(f"Tests Passed: {perf.get('tests_passed', 0)}\n")
            f.write(f"Tests Failed: {perf.get('tests_failed', 0)}\n")
            
            metrics = perf.get('performance_metrics', {})
            if metrics:
                f.write(f"Average Execution Time: {metrics.get('average_execution_time', 0):.2f}s\n")
                f.write(f"Max Memory Usage: {metrics.get('memory_usage', {}).get('max_mb', 0):.2f}MB\n")
                f.write(f"Max CPU Usage: {metrics.get('cpu_usage', {}).get('max_percent', 0):.1f}%\n")
                f.write(f"Average Response Time: {metrics.get('response_times', {}).get('average_ms', 0):.2f}ms\n")
            f.write("\n")
            
            # Compliance Summary
            f.write("COMPLIANCE TESTING SUMMARY\n")
            f.write("-" * 30 + "\n")
            comp = report['compliance_testing']
            f.write(f"Tests Run: {comp.get('tests_run', 0)}\n")
            f.write(f"Tests Passed: {comp.get('tests_passed', 0)}\n")
            f.write(f"Tests Failed: {comp.get('tests_failed', 0)}\n\n")
            
            compliance_status = comp.get('compliance_status', {})
            for regulation, status in compliance_status.items():
                f.write(f"{regulation.upper()}: {'COMPLIANT' if status.get('compliant') else 'NON-COMPLIANT'}\n")
                f.write(f"  Tests Passed: {status.get('tests_passed', 0)}/{status.get('tests_total', 0)}\n")
                f.write(f"  Compliance: {status.get('compliance_percentage', 0):.1f}%\n")
                if status.get('violations'):
                    f.write(f"  Violations: {', '.join(status['violations'][:3])}\n")
                f.write("\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 15 + "\n")
            for i, rec in enumerate(report.get('recommendations', []), 1):
                f.write(f"{i}. {rec}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("Detailed report available in JSON format\n")
            f.write("=" * 80 + "\n")
        
        print(f"📝 Human-readable summary saved to: {summary_filename}")


class PerformanceResultCollector(unittest.TestResult):
    """Custom test result collector for performance tests"""
    
    def __init__(self):
        super().__init__()
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.tests_run += 1
        self.tests_passed += 1
        
        # Extract test result data if available
        if hasattr(test, '_outcome') and hasattr(test._outcome, 'result'):
            result = test._outcome.result
            if hasattr(result, 'metrics'):
                self.test_results.append({
                    'test_name': test._testMethodName,
                    'success': True,
                    'execution_time': getattr(result, 'execution_time', 0),
                    'metrics': getattr(result, 'metrics', {}),
                    'resource_usage': getattr(result, 'resource_usage', {})
                })
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.tests_run += 1
        self.tests_failed += 1
        
        self.test_results.append({
            'test_name': test._testMethodName,
            'success': False,
            'error': str(err[1]),
            'traceback': ''.join(traceback.format_exception(*err))
        })
    
    def addError(self, test, err):
        super().addError(test, err)
        self.tests_run += 1
        self.tests_failed += 1
        
        self.test_results.append({
            'test_name': test._testMethodName,
            'success': False,
            'error': str(err[1]),
            'traceback': ''.join(traceback.format_exception(*err))
        })


class ComplianceResultCollector(unittest.TestResult):
    """Custom test result collector for compliance tests"""
    
    def __init__(self):
        super().__init__()
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.tests_run += 1
        self.tests_passed += 1
        
        # Extract test result data if available
        if hasattr(test, '_outcome') and hasattr(test._outcome, 'result'):
            result = test._outcome.result
            if hasattr(result, 'compliant'):
                self.test_results.append({
                    'test_name': test._testMethodName,
                    'compliant': result.compliant,
                    'regulation': getattr(result, 'regulation', 'unknown'),
                    'execution_time': getattr(result, 'execution_time', 0),
                    'violations': getattr(result, 'violations', []),
                    'recommendations': getattr(result, 'recommendations', []),
                    'evidence': getattr(result, 'evidence', {})
                })
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.tests_run += 1
        self.tests_failed += 1
        
        self.test_results.append({
            'test_name': test._testMethodName,
            'compliant': False,
            'regulation': 'unknown',
            'error': str(err[1]),
            'traceback': ''.join(traceback.format_exception(*err))
        })
    
    def addError(self, test, err):
        super().addError(test, err)
        self.tests_run += 1
        self.tests_failed += 1
        
        self.test_results.append({
            'test_name': test._testMethodName,
            'compliant': False,
            'regulation': 'unknown',
            'error': str(err[1]),
            'traceback': ''.join(traceback.format_exception(*err))
        })


def main():
    """Main function to run the comprehensive test suite"""
    parser = argparse.ArgumentParser(description='Run MINGUS Comprehensive Test Suite')
    parser.add_argument('--output-dir', default='test_reports', 
                       help='Output directory for test reports')
    parser.add_argument('--performance-only', action='store_true',
                       help='Run only performance tests')
    parser.add_argument('--compliance-only', action='store_true',
                       help='Run only compliance tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    print("🧪 MINGUS Comprehensive Test Suite")
    print("=" * 50)
    
    runner = ComprehensiveTestRunner(args.output_dir)
    
    if args.performance_only:
        print("🚀 Running Performance Tests Only...")
        results = runner.run_performance_tests()
        print(f"Performance Tests Completed: {results['tests_passed']}/{results['tests_run']} passed")
    elif args.compliance_only:
        print("🔒 Running Compliance Tests Only...")
        results = runner.run_compliance_tests()
        print(f"Compliance Tests Completed: {results['tests_passed']}/{results['tests_run']} passed")
    else:
        print("🔄 Running Complete Test Suite...")
        report = runner.generate_comprehensive_report()
        
        # Print summary
        executive = report['executive_summary']
        print("\n" + "=" * 50)
        print("TEST SUITE SUMMARY")
        print("=" * 50)
        print(f"Overall Status: {executive['overall_status']}")
        print(f"Performance: {executive['performance_status']}")
        print(f"Compliance: {executive['compliance_status']}")
        print(f"Total Tests: {executive['total_tests']}")
        print(f"Passed: {executive['total_passed']}")
        print(f"Failed: {executive['total_failed']}")
        print("=" * 50)
        
        if executive['overall_status'] == 'PASS':
            print("🎉 All tests passed successfully!")
        else:
            print("⚠️  Some tests failed. Check the detailed report for recommendations.")
    
    print(f"\n📁 Test reports saved to: {args.output_dir}")


if __name__ == '__main__':
    main() 