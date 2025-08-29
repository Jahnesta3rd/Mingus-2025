#!/usr/bin/env python3
"""
Quality Gates Configuration

Defines and enforces quality requirements for the comprehensive test suite.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QualityGate:
    """Represents a quality gate requirement"""
    name: str
    description: str
    threshold: float
    current_value: Optional[float] = None
    passed: bool = False
    critical: bool = True

class QualityGatesManager:
    """Manages quality gates for the test suite"""
    
    def __init__(self):
        self.gates = {
            # Test Coverage Requirements
            'backend_coverage': QualityGate(
                name='Backend Code Coverage',
                description='Backend assessment-related functions must have 90%+ coverage',
                threshold=90.0,
                critical=True
            ),
            'frontend_coverage': QualityGate(
                name='Frontend Code Coverage',
                description='Frontend assessment components must have 85%+ coverage',
                threshold=85.0,
                critical=True
            ),
            
            # Performance Requirements
            'income_comparison_performance': QualityGate(
                name='Income Comparison Performance',
                description='Income comparison calculation must complete within 45ms average',
                threshold=45.0,
                critical=True
            ),
            'page_load_performance': QualityGate(
                name='Page Load Performance',
                description='Landing page must load within 3 seconds on 3G connection',
                threshold=3.0,
                critical=True
            ),
            'assessment_submission_performance': QualityGate(
                name='Assessment Submission Performance',
                description='Assessment submission must complete within 2 seconds',
                threshold=2.0,
                critical=True
            ),
            
            # Security Requirements
            'security_vulnerabilities': QualityGate(
                name='Security Vulnerabilities',
                description='No high or critical security vulnerabilities allowed',
                threshold=0.0,
                critical=True
            ),
            'authentication_bypass': QualityGate(
                name='Authentication Bypass',
                description='No authentication bypass vulnerabilities allowed',
                threshold=0.0,
                critical=True
            ),
            
            # Accessibility Requirements
            'accessibility_compliance': QualityGate(
                name='Accessibility Compliance',
                description='Must maintain WCAG AA compliance level',
                threshold=100.0,  # 100% compliance
                critical=True
            ),
            
            # Mathematical Accuracy Requirements
            'mathematical_accuracy': QualityGate(
                name='Mathematical Accuracy',
                description='All calculation formulas must match documented specifications',
                threshold=100.0,  # 100% accuracy
                critical=True
            ),
            
            # Test Success Requirements
            'backend_tests': QualityGate(
                name='Backend Tests',
                description='All backend API tests must pass',
                threshold=100.0,  # 100% pass rate
                critical=True
            ),
            'frontend_tests': QualityGate(
                name='Frontend Tests',
                description='All frontend component tests must pass',
                threshold=100.0,  # 100% pass rate
                critical=True
            ),
            'e2e_tests': QualityGate(
                name='End-to-End Tests',
                description='All end-to-end workflow tests must pass',
                threshold=100.0,  # 100% pass rate
                critical=True
            ),
            'performance_tests': QualityGate(
                name='Performance Tests',
                description='All performance benchmarks must pass',
                threshold=100.0,  # 100% pass rate
                critical=True
            ),
            'security_tests': QualityGate(
                name='Security Tests',
                description='All security tests must pass',
                threshold=100.0,  # 100% pass rate
                critical=True
            ),
            'analytics_tests': QualityGate(
                name='Analytics Tests',
                description='All analytics verification tests must pass',
                threshold=100.0,  # 100% pass rate
                critical=True
            ),
            'mathematical_tests': QualityGate(
                name='Mathematical Tests',
                description='All mathematical accuracy tests must pass',
                threshold=100.0,  # 100% pass rate
                critical=True
            )
        }
    
    def load_test_results(self, results_file: str) -> Dict[str, Any]:
        """Load test results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Test results file {results_file} not found")
            return {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in test results file {results_file}")
            return {}
    
    def evaluate_coverage_gates(self, results: Dict[str, Any]) -> None:
        """Evaluate code coverage quality gates"""
        if 'coverage' in results:
            coverage_data = results['coverage']
            
            # Backend coverage
            if 'backend' in coverage_data:
                backend_coverage = coverage_data['backend']
                self.gates['backend_coverage'].current_value = backend_coverage
                self.gates['backend_coverage'].passed = backend_coverage >= 90.0
            
            # Frontend coverage
            if 'frontend' in coverage_data:
                frontend_coverage = coverage_data['frontend']
                self.gates['frontend_coverage'].current_value = frontend_coverage
                self.gates['frontend_coverage'].passed = frontend_coverage >= 85.0
    
    def evaluate_performance_gates(self, results: Dict[str, Any]) -> None:
        """Evaluate performance quality gates"""
        if 'performance' in results:
            perf_data = results['performance']
            
            # Income comparison performance
            if 'income_comparison_avg_ms' in perf_data:
                avg_time = perf_data['income_comparison_avg_ms']
                self.gates['income_comparison_performance'].current_value = avg_time
                self.gates['income_comparison_performance'].passed = avg_time <= 45.0
            
            # Page load performance
            if 'landing_page_load_time' in perf_data:
                load_time = perf_data['landing_page_load_time']
                self.gates['page_load_performance'].current_value = load_time
                self.gates['page_load_performance'].passed = load_time <= 3.0
            
            # Assessment submission performance
            if 'assessment_submission_time' in perf_data:
                submission_time = perf_data['assessment_submission_time']
                self.gates['assessment_submission_performance'].current_value = submission_time
                self.gates['assessment_submission_performance'].passed = submission_time <= 2.0
    
    def evaluate_security_gates(self, results: Dict[str, Any]) -> None:
        """Evaluate security quality gates"""
        if 'security' in results:
            security_data = results['security']
            
            # Security vulnerabilities
            if 'high_vulnerabilities' in security_data and 'critical_vulnerabilities' in security_data:
                total_vulns = security_data['high_vulnerabilities'] + security_data['critical_vulnerabilities']
                self.gates['security_vulnerabilities'].current_value = total_vulns
                self.gates['security_vulnerabilities'].passed = total_vulns == 0
            
            # Authentication bypass
            if 'auth_bypass_vulnerabilities' in security_data:
                bypass_count = security_data['auth_bypass_vulnerabilities']
                self.gates['authentication_bypass'].current_value = bypass_count
                self.gates['authentication_bypass'].passed = bypass_count == 0
    
    def evaluate_accessibility_gates(self, results: Dict[str, Any]) -> None:
        """Evaluate accessibility quality gates"""
        if 'accessibility' in results:
            a11y_data = results['accessibility']
            
            # WCAG AA compliance
            if 'wcag_aa_compliance' in a11y_data:
                compliance = a11y_data['wcag_aa_compliance']
                self.gates['accessibility_compliance'].current_value = compliance
                self.gates['accessibility_compliance'].passed = compliance >= 100.0
    
    def evaluate_mathematical_gates(self, results: Dict[str, Any]) -> None:
        """Evaluate mathematical accuracy quality gates"""
        if 'mathematical_accuracy' in results:
            math_data = results['mathematical_accuracy']
            
            # Overall mathematical accuracy
            if 'overall_accuracy' in math_data:
                accuracy = math_data['overall_accuracy']
                self.gates['mathematical_accuracy'].current_value = accuracy
                self.gates['mathematical_accuracy'].passed = accuracy >= 100.0
    
    def evaluate_test_success_gates(self, results: Dict[str, Any]) -> None:
        """Evaluate test success quality gates"""
        if 'test_suites' in results:
            test_suites = results['test_suites']
            
            # Backend tests
            if 'backend' in test_suites:
                backend_result = test_suites['backend']
                self.gates['backend_tests'].current_value = 100.0 if backend_result['return_code'] == 0 else 0.0
                self.gates['backend_tests'].passed = backend_result['return_code'] == 0
            
            # Frontend tests
            if 'frontend' in test_suites:
                frontend_result = test_suites['frontend']
                self.gates['frontend_tests'].current_value = 100.0 if frontend_result['return_code'] == 0 else 0.0
                self.gates['frontend_tests'].passed = frontend_result['return_code'] == 0
            
            # E2E tests
            if 'e2e' in test_suites:
                e2e_result = test_suites['e2e']
                self.gates['e2e_tests'].current_value = 100.0 if e2e_result['return_code'] == 0 else 0.0
                self.gates['e2e_tests'].passed = e2e_result['return_code'] == 0
            
            # Performance tests
            if 'performance' in test_suites:
                perf_result = test_suites['performance']
                self.gates['performance_tests'].current_value = 100.0 if perf_result['return_code'] == 0 else 0.0
                self.gates['performance_tests'].passed = perf_result['return_code'] == 0
            
            # Security tests
            if 'security' in test_suites:
                security_result = test_suites['security']
                self.gates['security_tests'].current_value = 100.0 if security_result['return_code'] == 0 else 0.0
                self.gates['security_tests'].passed = security_result['return_code'] == 0
            
            # Analytics tests
            if 'analytics' in test_suites:
                analytics_result = test_suites['analytics']
                self.gates['analytics_tests'].current_value = 100.0 if analytics_result['return_code'] == 0 else 0.0
                self.gates['analytics_tests'].passed = analytics_result['return_code'] == 0
            
            # Mathematical tests
            if 'mathematical_accuracy' in test_suites:
                math_result = test_suites['mathematical_accuracy']
                self.gates['mathematical_tests'].current_value = 100.0 if math_result['return_code'] == 0 else 0.0
                self.gates['mathematical_tests'].passed = math_result['return_code'] == 0
    
    def evaluate_all_gates(self, results_file: str) -> None:
        """Evaluate all quality gates based on test results"""
        results = self.load_test_results(results_file)
        
        self.evaluate_coverage_gates(results)
        self.evaluate_performance_gates(results)
        self.evaluate_security_gates(results)
        self.evaluate_accessibility_gates(results)
        self.evaluate_mathematical_gates(results)
        self.evaluate_test_success_gates(results)
    
    def get_failed_gates(self) -> List[QualityGate]:
        """Get list of failed quality gates"""
        return [gate for gate in self.gates.values() if not gate.passed]
    
    def get_critical_failed_gates(self) -> List[QualityGate]:
        """Get list of critical failed quality gates"""
        return [gate for gate in self.gates.values() if not gate.passed and gate.critical]
    
    def get_passed_gates(self) -> List[QualityGate]:
        """Get list of passed quality gates"""
        return [gate for gate in self.gates.values() if gate.passed]
    
    def print_summary(self) -> None:
        """Print quality gates summary"""
        print("\n" + "="*80)
        print("🎯 QUALITY GATES SUMMARY")
        print("="*80)
        
        total_gates = len(self.gates)
        passed_gates = len(self.get_passed_gates())
        failed_gates = len(self.get_failed_gates())
        critical_failed = len(self.get_critical_failed_gates())
        
        print(f"Total Quality Gates: {total_gates}")
        print(f"Passed: {passed_gates}")
        print(f"Failed: {failed_gates}")
        print(f"Critical Failed: {critical_failed}")
        print(f"Success Rate: {(passed_gates/total_gates)*100:.1f}%")
        
        if failed_gates > 0:
            print(f"\n❌ FAILED QUALITY GATES:")
            for gate in self.get_failed_gates():
                status = "🔴 CRITICAL" if gate.critical else "🟡 WARNING"
                current = gate.current_value if gate.current_value is not None else "N/A"
                print(f"  {status} {gate.name}")
                print(f"    Description: {gate.description}")
                print(f"    Threshold: {gate.threshold}")
                print(f"    Current: {current}")
                print()
        
        if passed_gates > 0:
            print(f"✅ PASSED QUALITY GATES:")
            for gate in self.get_passed_gates():
                current = gate.current_value if gate.current_value is not None else "N/A"
                print(f"  🟢 {gate.name}: {current}")
        
        print("\n" + "="*80)
    
    def save_report(self, output_file: str) -> None:
        """Save quality gates report to JSON file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_gates': len(self.gates),
                'passed_gates': len(self.get_passed_gates()),
                'failed_gates': len(self.get_failed_gates()),
                'critical_failed': len(self.get_critical_failed_gates()),
                'success_rate': (len(self.get_passed_gates())/len(self.gates))*100
            },
            'gates': {
                name: {
                    'name': gate.name,
                    'description': gate.description,
                    'threshold': gate.threshold,
                    'current_value': gate.current_value,
                    'passed': gate.passed,
                    'critical': gate.critical
                }
                for name, gate in self.gates.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Quality gates report saved to: {output_file}")
    
    def check_deployment_ready(self) -> bool:
        """Check if deployment is ready based on quality gates"""
        critical_failed = self.get_critical_failed_gates()
        
        if critical_failed:
            print(f"❌ DEPLOYMENT BLOCKED: {len(critical_failed)} critical quality gates failed")
            for gate in critical_failed:
                print(f"  - {gate.name}: {gate.description}")
            return False
        else:
            print("✅ DEPLOYMENT READY: All critical quality gates passed")
            return True


def main():
    """Main entry point for quality gates evaluation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quality Gates Evaluation')
    parser.add_argument('results_file', help='Path to test results JSON file')
    parser.add_argument('--output', '-o', help='Output file for quality gates report')
    parser.add_argument('--check-deployment', action='store_true', help='Check if deployment is ready')
    
    args = parser.parse_args()
    
    # Initialize quality gates manager
    qg_manager = QualityGatesManager()
    
    # Evaluate all gates
    qg_manager.evaluate_all_gates(args.results_file)
    
    # Print summary
    qg_manager.print_summary()
    
    # Save report if requested
    if args.output:
        qg_manager.save_report(args.output)
    
    # Check deployment readiness if requested
    if args.check_deployment:
        deployment_ready = qg_manager.check_deployment_ready()
        return 0 if deployment_ready else 1
    
    # Return success if no critical gates failed
    critical_failed = qg_manager.get_critical_failed_gates()
    return 0 if not critical_failed else 1


if __name__ == '__main__':
    sys.exit(main())
