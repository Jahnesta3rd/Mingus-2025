#!/usr/bin/env python3
"""
MINGUS Authentication Security Testing
Comprehensive testing utilities for authentication security system
"""

import os
import json
import time
import requests
import unittest
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from security.auth_security import (
    AuthSecurityConfig, PasswordValidator, RateLimiter, 
    AccountLockoutManager, SessionManager, ActivityLogger,
    create_auth_config, validate_auth_config
)

@dataclass
class AuthTestResult:
    """Authentication security test result"""
    test_name: str
    passed: bool
    details: Dict[str, Any]
    recommendations: List[str]
    severity: str  # low, medium, high, critical

class AuthSecurityTester:
    """Comprehensive authentication security testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000", config: Optional[AuthSecurityConfig] = None):
        self.base_url = base_url
        self.config = config or create_auth_config('testing')
        self.test_results = []
        
        # Initialize components
        self.password_validator = PasswordValidator(self.config.password_policy)
        self.rate_limiter = RateLimiter(self.config.rate_limit_policy)
        self.lockout_manager = AccountLockoutManager(self.config.lockout_policy)
        self.session_manager = SessionManager(self.config.session_policy, self.config.jwt_secret_key or 'test-secret')
        self.activity_logger = ActivityLogger(self.config)
    
    def run_all_tests(self) -> List[AuthTestResult]:
        """Run all authentication security tests"""
        self.test_results = []
        
        # Password security tests
        self.test_results.extend([
            self.test_password_policy(),
            self.test_password_breach_detection(),
            self.test_password_strength_validation(),
            self.test_common_password_prevention()
        ])
        
        # Account lockout tests
        self.test_results.extend([
            self.test_account_lockout(),
            self.test_progressive_lockout(),
            self.test_lockout_recovery()
        ])
        
        # Rate limiting tests
        self.test_results.extend([
            self.test_rate_limiting(),
            self.test_burst_protection(),
            self.test_rate_limit_recovery()
        ])
        
        # Session management tests
        self.test_results.extend([
            self.test_session_creation(),
            self.test_session_validation(),
            self.test_session_timeout(),
            self.test_concurrent_sessions(),
            self.test_session_fixation_protection()
        ])
        
        # Activity logging tests
        self.test_results.extend([
            self.test_activity_logging(),
            self.test_suspicious_activity_detection(),
            self.test_log_retention()
        ])
        
        # API endpoint tests
        self.test_results.extend([
            self.test_login_endpoint(),
            self.test_logout_endpoint(),
            self.test_password_validation_endpoint(),
            self.test_activity_endpoint()
        ])
        
        # Configuration tests
        self.test_results.extend([
            self.test_configuration_validation(),
            self.test_environment_configuration()
        ])
        
        return self.test_results
    
    def test_password_policy(self) -> AuthTestResult:
        """Test password policy enforcement"""
        test_name = "Password Policy Enforcement"
        details = {}
        recommendations = []
        passed = True
        
        # Test minimum length
        short_password = "short"
        is_valid, errors = self.password_validator.validate_password(short_password)
        details['min_length_test'] = {
            'password': short_password,
            'valid': is_valid,
            'errors': errors
        }
        
        if is_valid:
            passed = False
            recommendations.append("Minimum length policy not enforced")
        
        # Test character requirements
        weak_password = "onlylowercase"
        is_valid, errors = self.password_validator.validate_password(weak_password)
        details['character_requirements_test'] = {
            'password': weak_password,
            'valid': is_valid,
            'errors': errors
        }
        
        if is_valid:
            passed = False
            recommendations.append("Character requirements not enforced")
        
        # Test strong password
        strong_password = "StrongP@ssw0rd123!"
        is_valid, errors = self.password_validator.validate_password(strong_password)
        details['strong_password_test'] = {
            'password': strong_password,
            'valid': is_valid,
            'errors': errors
        }
        
        if not is_valid:
            passed = False
            recommendations.append("Strong password incorrectly rejected")
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_password_breach_detection(self) -> AuthTestResult:
        """Test password breach detection"""
        test_name = "Password Breach Detection"
        details = {}
        recommendations = []
        passed = True
        
        # Test breached password (common password)
        breached_password = "password123"
        breach_safe, breach_count = self.password_validator.check_password_breach(breached_password)
        details['breached_password_test'] = {
            'password': breached_password,
            'breach_safe': breach_safe,
            'breach_count': breach_count
        }
        
        if breach_safe:
            passed = False
            recommendations.append("Breach detection not working properly")
        
        # Test safe password
        safe_password = "UniqueP@ssw0rd2024!"
        breach_safe, breach_count = self.password_validator.check_password_breach(safe_password)
        details['safe_password_test'] = {
            'password': safe_password,
            'breach_safe': breach_safe,
            'breach_count': breach_count
        }
        
        if not breach_safe and breach_count == 0:
            passed = False
            recommendations.append("Safe password incorrectly flagged as breached")
        
        severity = "critical" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_password_strength_validation(self) -> AuthTestResult:
        """Test password strength validation"""
        test_name = "Password Strength Validation"
        details = {}
        recommendations = []
        passed = True
        
        # Test various password strengths
        test_passwords = [
            ("weak", "abc123"),
            ("medium", "Password123"),
            ("strong", "Str0ngP@ssw0rd2024!"),
            ("very_strong", "V3ry$tr0ngP@ssw0rd2024!@#$%^&*()")
        ]
        
        for strength, password in test_passwords:
            is_valid, errors = self.password_validator.validate_password(password)
            details[f'{strength}_password_test'] = {
                'password': password,
                'valid': is_valid,
                'errors': errors,
                'error_count': len(errors)
            }
            
            if strength == "weak" and is_valid:
                passed = False
                recommendations.append("Weak password incorrectly accepted")
            elif strength == "very_strong" and not is_valid:
                passed = False
                recommendations.append("Very strong password incorrectly rejected")
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_common_password_prevention(self) -> AuthTestResult:
        """Test common password prevention"""
        test_name = "Common Password Prevention"
        details = {}
        recommendations = []
        passed = True
        
        common_passwords = [
            "password", "123456", "qwerty", "abc123", "letmein"
        ]
        
        for password in common_passwords:
            is_valid, errors = self.password_validator.validate_password(password)
            details[f'common_password_{password}'] = {
                'password': password,
                'valid': is_valid,
                'errors': errors
            }
            
            if is_valid:
                passed = False
                recommendations.append(f"Common password '{password}' incorrectly accepted")
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_account_lockout(self) -> AuthTestResult:
        """Test account lockout functionality"""
        test_name = "Account Lockout Functionality"
        details = {}
        recommendations = []
        passed = True
        
        test_email = "test@example.com"
        
        # Test failed attempts
        for i in range(self.config.lockout_policy.max_failed_attempts + 1):
            lockout_info = self.lockout_manager.record_failed_attempt(test_email)
            details[f'failed_attempt_{i+1}'] = {
                'attempts': lockout_info['attempts'],
                'locked': lockout_info.get('locked', False),
                'remaining_attempts': lockout_info.get('remaining_attempts', 0)
            }
            
            if i >= self.config.lockout_policy.max_failed_attempts - 1:
                if not lockout_info.get('locked', False):
                    passed = False
                    recommendations.append("Account not locked after maximum failed attempts")
        
        # Test successful login resets lockout
        self.lockout_manager.record_successful_attempt(test_email)
        is_locked, lockout_info = self.lockout_manager.is_locked(test_email)
        details['successful_login_reset'] = {
            'locked': is_locked,
            'lockout_info': lockout_info
        }
        
        if is_locked:
            passed = False
            recommendations.append("Account still locked after successful login")
        
        severity = "critical" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_progressive_lockout(self) -> AuthTestResult:
        """Test progressive lockout functionality"""
        test_name = "Progressive Lockout Functionality"
        details = {}
        recommendations = []
        passed = True
        
        test_email = "progressive@example.com"
        
        # Test progressive lockout durations
        lockout_durations = []
        for i in range(10):
            lockout_info = self.lockout_manager.record_failed_attempt(test_email)
            if lockout_info.get('locked', False):
                lockout_durations.append(lockout_info['lockout_duration'])
        
        details['lockout_durations'] = lockout_durations
        
        # Check if durations are increasing
        if len(lockout_durations) > 1:
            for i in range(1, len(lockout_durations)):
                if lockout_durations[i] <= lockout_durations[i-1]:
                    passed = False
                    recommendations.append("Progressive lockout durations not increasing")
                    break
        
        severity = "medium" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_rate_limiting(self) -> AuthTestResult:
        """Test rate limiting functionality"""
        test_name = "Rate Limiting Functionality"
        details = {}
        recommendations = []
        passed = True
        
        test_identifier = "test-user"
        
        # Test rate limiting for login attempts
        for i in range(self.config.rate_limit_policy.login_attempts_per_minute + 1):
            is_limited, rate_limit_info = self.rate_limiter.is_rate_limited(test_identifier, 'login')
            details[f'rate_limit_check_{i+1}'] = {
                'limited': is_limited,
                'remaining': rate_limit_info.get('remaining', 0),
                'retry_after': rate_limit_info.get('retry_after', 0)
            }
            
            if i >= self.config.rate_limit_policy.login_attempts_per_minute:
                if not is_limited:
                    passed = False
                    recommendations.append("Rate limiting not enforced after limit exceeded")
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_session_creation(self) -> AuthTestResult:
        """Test session creation and management"""
        test_name = "Session Creation and Management"
        details = {}
        recommendations = []
        passed = True
        
        test_user_id = "test-user-123"
        
        # Test session creation
        session_data = self.session_manager.create_session(test_user_id, remember_me=False)
        details['session_creation'] = {
            'session_id': session_data['session_id'],
            'expires_at': session_data['expires_at'],
            'remember_me': session_data['remember_me']
        }
        
        if not session_data['session_id']:
            passed = False
            recommendations.append("Session creation failed")
        
        # Test session validation
        is_valid, session_info = self.session_manager.validate_session(session_data['token'])
        details['session_validation'] = {
            'valid': is_valid,
            'session_info': session_info
        }
        
        if not is_valid:
            passed = False
            recommendations.append("Valid session incorrectly rejected")
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_session_timeout(self) -> AuthTestResult:
        """Test session timeout functionality"""
        test_name = "Session Timeout Functionality"
        details = {}
        recommendations = []
        passed = True
        
        test_user_id = "timeout-test-user"
        
        # Create session with short timeout for testing
        original_timeout = self.config.session_policy.session_timeout
        self.config.session_policy.session_timeout = 1  # 1 second for testing
        
        session_data = self.session_manager.create_session(test_user_id)
        
        # Wait for session to expire
        time.sleep(2)
        
        # Test expired session
        is_valid, session_info = self.session_manager.validate_session(session_data['token'])
        details['expired_session_test'] = {
            'valid': is_valid,
            'session_info': session_info
        }
        
        if is_valid:
            passed = False
            recommendations.append("Expired session not properly invalidated")
        
        # Restore original timeout
        self.config.session_policy.session_timeout = original_timeout
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_concurrent_sessions(self) -> AuthTestResult:
        """Test concurrent session management"""
        test_name = "Concurrent Session Management"
        details = {}
        recommendations = []
        passed = True
        
        test_user_id = "concurrent-test-user"
        max_sessions = self.config.session_policy.max_concurrent_sessions
        
        # Create maximum allowed sessions
        sessions = []
        for i in range(max_sessions + 1):
            session_data = self.session_manager.create_session(test_user_id)
            sessions.append(session_data)
        
        details['session_creation'] = {
            'created_sessions': len(sessions),
            'max_allowed': max_sessions
        }
        
        # Check if oldest session was removed
        if len(sessions) > max_sessions:
            passed = False
            recommendations.append("Concurrent session limit not enforced")
        
        severity = "medium" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_activity_logging(self) -> AuthTestResult:
        """Test activity logging functionality"""
        test_name = "Activity Logging Functionality"
        details = {}
        recommendations = []
        passed = True
        
        test_user_id = "logging-test-user"
        
        # Test activity logging
        test_actions = ['login', 'logout', 'password_change', 'profile_update']
        
        for action in test_actions:
            self.activity_logger.log_activity(
                user_id=test_user_id,
                action=action,
                details={'test': True}
            )
        
        # Get user activity
        activity = self.activity_logger.get_user_activity(test_user_id, days=1)
        details['logged_activities'] = {
            'total_activities': len(activity),
            'actions': [a['action'] for a in activity]
        }
        
        if len(activity) != len(test_actions):
            passed = False
            recommendations.append("Activity logging not working properly")
        
        severity = "medium" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_suspicious_activity_detection(self) -> AuthTestResult:
        """Test suspicious activity detection"""
        test_name = "Suspicious Activity Detection"
        details = {}
        recommendations = []
        passed = True
        
        test_user_id = "suspicious-test-user"
        
        # Simulate suspicious activity (multiple failed logins)
        for i in range(10):
            self.activity_logger.log_activity(
                user_id=test_user_id,
                action='login_failed',
                details={'attempt': i + 1}
            )
        
        # Test suspicious activity detection
        suspicious_events = self.activity_logger.detect_suspicious_activity(test_user_id)
        details['suspicious_events'] = {
            'total_events': len(suspicious_events),
            'event_types': [event['type'] for event in suspicious_events]
        }
        
        if not suspicious_events:
            passed = False
            recommendations.append("Suspicious activity not detected")
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_login_endpoint(self) -> AuthTestResult:
        """Test login endpoint security"""
        test_name = "Login Endpoint Security"
        details = {}
        recommendations = []
        passed = True
        
        try:
            # Test rate limiting
            for i in range(10):
                response = requests.post(f"{self.base_url}/auth/login", 
                                       json={'email': 'test@example.com', 'password': 'wrong'})
                details[f'login_attempt_{i+1}'] = {
                    'status_code': response.status_code,
                    'response': response.json() if response.content else None
                }
                
                if response.status_code == 429 and i < 5:
                    passed = False
                    recommendations.append("Rate limiting too aggressive")
                    break
            
            # Test account lockout
            if response.status_code == 423:
                details['account_locked'] = True
            else:
                details['account_locked'] = False
                recommendations.append("Account lockout not working")
                passed = False
                
        except requests.exceptions.RequestException as e:
            details['error'] = str(e)
            recommendations.append("Login endpoint not accessible")
            passed = False
        
        severity = "critical" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_configuration_validation(self) -> AuthTestResult:
        """Test configuration validation"""
        test_name = "Configuration Validation"
        details = {}
        recommendations = []
        passed = True
        
        # Test valid configuration
        valid_config = create_auth_config('production')
        issues = validate_auth_config(valid_config)
        details['valid_config_test'] = {
            'issues': issues,
            'issue_count': len(issues)
        }
        
        if issues:
            passed = False
            recommendations.extend(issues)
        
        # Test invalid configuration
        invalid_config = AuthSecurityConfig(
            password_policy=valid_config.password_policy,
            lockout_policy=valid_config.lockout_policy,
            rate_limit_policy=valid_config.rate_limit_policy,
            session_policy=valid_config.session_policy
        )
        invalid_config.password_policy.min_length = 3  # Too short
        invalid_config.jwt_secret_key = None  # Missing secret
        
        issues = validate_auth_config(invalid_config)
        details['invalid_config_test'] = {
            'issues': issues,
            'issue_count': len(issues)
        }
        
        if not issues:
            passed = False
            recommendations.append("Invalid configuration not detected")
        
        severity = "high" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def test_environment_configuration(self) -> AuthTestResult:
        """Test environment-specific configuration"""
        test_name = "Environment Configuration"
        details = {}
        recommendations = []
        passed = True
        
        # Test development configuration
        dev_config = create_auth_config('development')
        details['development_config'] = {
            'mfa_enabled': dev_config.mfa_enabled,
            'suspicious_activity_detection': dev_config.suspicious_activity_detection,
            'password_breach_detection': dev_config.password_breach_detection,
            'session_timeout': dev_config.session_policy.session_timeout
        }
        
        if dev_config.mfa_enabled:
            passed = False
            recommendations.append("MFA should be disabled in development")
        
        # Test production configuration
        prod_config = create_auth_config('production')
        details['production_config'] = {
            'mfa_enabled': prod_config.mfa_enabled,
            'suspicious_activity_detection': prod_config.suspicious_activity_detection,
            'password_breach_detection': prod_config.password_breach_detection,
            'session_timeout': prod_config.session_policy.session_timeout
        }
        
        if not prod_config.mfa_enabled:
            passed = False
            recommendations.append("MFA should be enabled in production")
        
        severity = "medium" if not passed else "low"
        
        return AuthTestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            recommendations=recommendations,
            severity=severity
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        # Group by severity
        severity_counts = {}
        for result in self.test_results:
            severity = result.severity
            if severity not in severity_counts:
                severity_counts[severity] = {'total': 0, 'passed': 0, 'failed': 0}
            severity_counts[severity]['total'] += 1
            if result.passed:
                severity_counts[severity]['passed'] += 1
            else:
                severity_counts[severity]['failed'] += 1
        
        # Collect all recommendations
        all_recommendations = []
        for result in self.test_results:
            all_recommendations.extend(result.recommendations)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'severity_breakdown': severity_counts,
            'test_results': [
                {
                    'test_name': result.test_name,
                    'passed': result.passed,
                    'severity': result.severity,
                    'recommendations': result.recommendations
                }
                for result in self.test_results
            ],
            'recommendations': list(set(all_recommendations)),
            'overall_status': 'PASS' if failed_tests == 0 else 'FAIL'
        }

def run_auth_security_tests(base_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """Run comprehensive authentication security tests"""
    tester = AuthSecurityTester(base_url)
    results = tester.run_all_tests()
    report = tester.generate_report()
    
    # Print summary
    print(f"\n🔒 Authentication Security Test Results")
    print(f"=====================================")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Overall Status: {report['overall_status']}")
    
    if report['recommendations']:
        print(f"\n📋 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    return report

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Authentication Security Testing')
    parser.add_argument('--base-url', default='http://localhost:5000', help='Base URL for testing')
    parser.add_argument('--output', help='Output file for test results')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Run tests
    report = run_auth_security_tests(args.base_url)
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Test results saved to {args.output}")
    
    # Exit with appropriate code
    exit_code = 0 if report['overall_status'] == 'PASS' else 1
    exit(exit_code)

if __name__ == "__main__":
    main() 