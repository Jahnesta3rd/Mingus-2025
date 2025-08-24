#!/usr/bin/env python3
"""
Security Validator for MINGUS Application
Comprehensive security validation for environment variables, configuration, and system security.
"""

import os
import sys
import argparse
import logging
import secrets
import hashlib
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.secure_config import SecureConfigManager, SecurityConfig, SecurityLevel, ConfigValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityValidator:
    """Comprehensive security validator for the MINGUS application"""
    
    def __init__(self, env_file: str = None, verbose: bool = False):
        """Initialize the security validator"""
        self.env_file = env_file
        self.verbose = verbose
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0,
            'critical_issues': [],
            'high_issues': [],
            'medium_issues': [],
            'low_issues': [],
            'warnings': [],
            'recommendations': [],
            'passed_checks': [],
            'security_level': 'UNKNOWN'
        }
        
        # Initialize secure config manager
        try:
            self.secure_config = SecureConfigManager(env_file)
        except Exception as e:
            logger.error(f"Failed to initialize secure config manager: {e}")
            self.secure_config = None
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all security validation checks"""
        logger.info("Starting comprehensive security validation...")
        
        # Core validation checks
        self._validate_environment_variables()
        self._validate_required_vs_optional_variables()
        self._check_startup_warnings()
        self._validate_secure_key_generation()
        self._validate_secret_strength()
        self._validate_configuration_patterns()
        self._validate_production_security()
        self._validate_encryption_settings()
        self._validate_audit_logging()
        self._validate_external_service_configs()
        
        # Calculate overall security score
        self._calculate_security_score()
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _validate_environment_variables(self):
        """Validate environment variable configuration"""
        logger.info("Validating environment variables...")
        
        if not self.secure_config:
            self.results['critical_issues'].append("Secure config manager failed to initialize")
            return
        
        try:
            # Get validation results from secure config
            validation_results = self.secure_config.validate_environment()
            
            if not validation_results['valid']:
                for error in validation_results['errors']:
                    self.results['critical_issues'].append(f"Configuration validation error: {error}")
            
            # Check missing critical variables
            for missing in validation_results['missing_critical']:
                self.results['critical_issues'].append(f"Missing critical configuration: {missing}")
            
            # Check missing high-priority variables
            for missing in validation_results['missing_high']:
                self.results['high_issues'].append(f"Missing high-priority configuration: {missing}")
            
            # Check weak secrets
            for weak_secret in validation_results['weak_secrets']:
                self.results['high_issues'].append(f"Weak secret detected: {weak_secret}")
            
            # Add recommendations
            for recommendation in validation_results['recommendations']:
                self.results['recommendations'].append(recommendation)
                
        except Exception as e:
            self.results['critical_issues'].append(f"Environment validation failed: {e}")
    
    def _validate_required_vs_optional_variables(self):
        """Validate required vs optional variable configuration"""
        logger.info("Validating required vs optional variables...")
        
        if not self.secure_config:
            return
        
        # Define critical required variables
        critical_required = [
            'SECRET_KEY',
            'FIELD_ENCRYPTION_KEY',
            'DATABASE_URL',
            'SUPABASE_URL',
            'SUPABASE_KEY'
        ]
        
        # Define high-priority optional variables
        high_priority_optional = [
            'SUPABASE_SERVICE_ROLE_KEY',
            'STRIPE_TEST_SECRET_KEY',
            'STRIPE_LIVE_SECRET_KEY',
            'PLAID_SANDBOX_CLIENT_ID',
            'PLAID_SANDBOX_SECRET',
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'RESEND_API_KEY'
        ]
        
        # Check critical required variables
        for var in critical_required:
            value = self.secure_config.get(var)
            if not value:
                self.results['critical_issues'].append(f"Critical required variable missing: {var}")
            else:
                self.results['passed_checks'].append(f"Critical required variable present: {var}")
        
        # Check high-priority optional variables
        missing_high_priority = []
        for var in high_priority_optional:
            value = self.secure_config.get(var)
            if not value:
                missing_high_priority.append(var)
            else:
                self.results['passed_checks'].append(f"High-priority optional variable present: {var}")
        
        if missing_high_priority:
            self.results['high_issues'].append(f"Missing high-priority optional variables: {', '.join(missing_high_priority)}")
    
    def _check_startup_warnings(self):
        """Check for startup warnings and critical issues"""
        logger.info("Checking startup warnings...")
        
        if not self.secure_config:
            return
        
        # Check for development secrets in production
        flask_env = self.secure_config.get('FLASK_ENV', 'production')
        if flask_env == 'production':
            secret_key = self.secure_config.get('SECRET_KEY', '')
            if 'dev-' in secret_key.lower() or 'test-' in secret_key.lower():
                self.results['critical_issues'].append("Development/test secret key detected in production environment")
            
            debug_mode = self.secure_config.get('DEBUG', 'false').lower()
            if debug_mode == 'true':
                self.results['critical_issues'].append("DEBUG mode enabled in production environment")
        
        # Check for missing encryption keys
        encryption_key = self.secure_config.get('CONFIG_ENCRYPTION_KEY')
        if not encryption_key:
            self.results['medium_issues'].append("CONFIG_ENCRYPTION_KEY not set - configuration encryption disabled")
        
        # Check for weak default values
        weak_defaults = [
            ('SECRET_KEY', 'dev-secret-key-change-in-production'),
            ('FIELD_ENCRYPTION_KEY', 'dev-encryption-key-change-in-production'),
        ]
        
        for var, weak_value in weak_defaults:
            current_value = self.secure_config.get(var, '')
            if current_value == weak_value:
                self.results['critical_issues'].append(f"Using weak default value for {var}")
    
    def _validate_secure_key_generation(self):
        """Validate secure random key generation"""
        logger.info("Validating secure key generation...")
        
        # Test secure key generation
        try:
            # Generate test keys
            test_keys = []
            for i in range(10):
                key = secrets.token_urlsafe(32)
                test_keys.append(key)
            
            # Check for uniqueness
            if len(set(test_keys)) != len(test_keys):
                self.results['critical_issues'].append("Secure key generation produces duplicate keys")
            else:
                self.results['passed_checks'].append("Secure key generation produces unique keys")
            
            # Check entropy
            for key in test_keys:
                if len(set(key)) < len(key) * 0.6:  # At least 60% unique characters
                    self.results['high_issues'].append("Generated keys have low entropy")
                    break
            else:
                self.results['passed_checks'].append("Generated keys have sufficient entropy")
            
            # Test key rotation
            try:
                rotated_key = self.secure_config.rotate_secret('SECRET_KEY')
                if rotated_key and len(rotated_key) >= 32:
                    self.results['passed_checks'].append("Secret rotation functionality working")
                else:
                    self.results['high_issues'].append("Secret rotation produces weak keys")
            except Exception as e:
                self.results['medium_issues'].append(f"Secret rotation failed: {e}")
                
        except Exception as e:
            self.results['critical_issues'].append(f"Secure key generation test failed: {e}")
    
    def _validate_secret_strength(self):
        """Validate secret strength and complexity"""
        logger.info("Validating secret strength...")
        
        if not self.secure_config:
            return
        
        # Check secret strength patterns
        weak_patterns = [
            (r'^dev-', 'Development prefix'),
            (r'^test-', 'Test prefix'),
            (r'^password$', 'Common password'),
            (r'^secret$', 'Common secret'),
            (r'^key$', 'Common key'),
            (r'^123456', 'Sequential numbers'),
            (r'^admin', 'Admin prefix'),
            (r'^default', 'Default prefix'),
            (r'^changeme', 'Change me'),
            (r'^temp', 'Temporary'),
            (r'^demo', 'Demo'),
        ]
        
        critical_secrets = [
            'SECRET_KEY',
            'FIELD_ENCRYPTION_KEY',
            'DJANGO_SECRET_KEY',
            'SUPABASE_KEY',
            'STRIPE_TEST_SECRET_KEY',
            'STRIPE_LIVE_SECRET_KEY',
            'PLAID_SANDBOX_SECRET',
            'PLAID_PRODUCTION_SECRET',
            'TWILIO_AUTH_TOKEN',
            'RESEND_API_KEY'
        ]
        
        for secret_var in critical_secrets:
            value = self.secure_config.get(secret_var, '')
            if not value:
                continue
            
            # Check for weak patterns
            for pattern, description in weak_patterns:
                if re.search(pattern, value.lower()):
                    self.results['high_issues'].append(f"Weak secret pattern detected in {secret_var}: {description}")
                    break
            
            # Check length
            if len(value) < 32:
                self.results['high_issues'].append(f"Secret {secret_var} is too short ({len(value)} chars)")
            
            # Check entropy
            unique_chars = len(set(value))
            if unique_chars < len(value) * 0.3:
                self.results['high_issues'].append(f"Secret {secret_var} has low entropy")
            else:
                self.results['passed_checks'].append(f"Secret {secret_var} has sufficient strength")
    
    def _validate_configuration_patterns(self):
        """Validate configuration value patterns"""
        logger.info("Validating configuration patterns...")
        
        if not self.secure_config:
            return
        
        # Define expected patterns
        patterns = {
            'SUPABASE_URL': r'^https://.*\.supabase\.co$',
            'SUPABASE_KEY': r'^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$',
            'STRIPE_TEST_SECRET_KEY': r'^sk_test_[A-Za-z0-9]{24}$',
            'STRIPE_LIVE_SECRET_KEY': r'^sk_live_[A-Za-z0-9]{24}$',
            'PLAID_SANDBOX_CLIENT_ID': r'^[A-Za-z0-9]{24}$',
            'PLAID_SANDBOX_SECRET': r'^[A-Za-z0-9]{30}$',
            'TWILIO_ACCOUNT_SID': r'^AC[A-Za-z0-9]{32}$',
            'TWILIO_AUTH_TOKEN': r'^[A-Za-z0-9]{32}$',
            'RESEND_API_KEY': r'^re_[A-Za-z0-9]{40}$',
            'DATABASE_URL': r'^postgresql://.*$',
            'REDIS_URL': r'^redis://.*$',
        }
        
        for var, pattern in patterns.items():
            value = self.secure_config.get(var, '')
            if value and not re.match(pattern, value):
                self.results['high_issues'].append(f"Configuration {var} does not match expected pattern")
            elif value:
                self.results['passed_checks'].append(f"Configuration {var} matches expected pattern")
    
    def _validate_production_security(self):
        """Validate production-specific security settings"""
        logger.info("Validating production security settings...")
        
        if not self.secure_config:
            return
        
        flask_env = self.secure_config.get('FLASK_ENV', 'production')
        if flask_env == 'production':
            # Check SSL settings
            ssl_redirect = self.secure_config.get('SECURE_SSL_REDIRECT', 'false').lower()
            if ssl_redirect != 'true':
                self.results['critical_issues'].append("SSL redirect not enabled in production")
            
            # Check session security
            session_secure = self.secure_config.get('SESSION_COOKIE_SECURE', 'false').lower()
            if session_secure != 'true':
                self.results['critical_issues'].append("Secure session cookies not enabled in production")
            
            # Check debug mode
            debug_mode = self.secure_config.get('DEBUG', 'false').lower()
            if debug_mode == 'true':
                self.results['critical_issues'].append("DEBUG mode enabled in production")
            
            # Check for development secrets
            secret_key = self.secure_config.get('SECRET_KEY', '')
            if 'dev-' in secret_key.lower() or 'test-' in secret_key.lower():
                self.results['critical_issues'].append("Development secrets detected in production")
            
            # Check audit logging
            audit_enabled = self.secure_config.get('AUDIT_LOG_ENABLED', 'false').lower()
            if audit_enabled != 'true':
                self.results['medium_issues'].append("Audit logging not enabled in production")
        else:
            self.results['warnings'].append(f"Running in {flask_env} environment - production security checks skipped")
    
    def _validate_encryption_settings(self):
        """Validate encryption configuration"""
        logger.info("Validating encryption settings...")
        
        if not self.secure_config:
            return
        
        # Check encryption key presence
        encryption_key = self.secure_config.get('CONFIG_ENCRYPTION_KEY')
        if not encryption_key:
            self.results['medium_issues'].append("Configuration encryption key not set")
        else:
            self.results['passed_checks'].append("Configuration encryption key is set")
        
        # Check field encryption key
        field_encryption_key = self.secure_config.get('FIELD_ENCRYPTION_KEY')
        if not field_encryption_key:
            self.results['critical_issues'].append("Field encryption key not set")
        else:
            self.results['passed_checks'].append("Field encryption key is set")
        
        # Check encryption algorithm
        encryption_algorithm = self.secure_config.get('ENCRYPTION_ALGORITHM', '')
        if encryption_algorithm not in ['AES-256-GCM', 'AES-256-CBC']:
            self.results['medium_issues'].append(f"Non-standard encryption algorithm: {encryption_algorithm}")
        else:
            self.results['passed_checks'].append(f"Using secure encryption algorithm: {encryption_algorithm}")
    
    def _validate_audit_logging(self):
        """Validate audit logging configuration"""
        logger.info("Validating audit logging...")
        
        if not self.secure_config:
            return
        
        # Check audit logging enabled
        audit_enabled = self.secure_config.get('AUDIT_LOG_ENABLED', 'false').lower()
        if audit_enabled == 'true':
            self.results['passed_checks'].append("Audit logging is enabled")
        else:
            self.results['medium_issues'].append("Audit logging is disabled")
        
        # Check audit log retention
        audit_retention = self.secure_config.get('AUDIT_LOG_RETENTION_DAYS', '0')
        try:
            retention_days = int(audit_retention)
            if retention_days < 30:
                self.results['low_issues'].append(f"Audit log retention is short: {retention_days} days")
            else:
                self.results['passed_checks'].append(f"Audit log retention is adequate: {retention_days} days")
        except ValueError:
            self.results['medium_issues'].append("Invalid audit log retention setting")
    
    def _validate_external_service_configs(self):
        """Validate external service configurations"""
        logger.info("Validating external service configurations...")
        
        if not self.secure_config:
            return
        
        # Check Supabase configuration
        supabase_url = self.secure_config.get('SUPABASE_URL')
        supabase_key = self.secure_config.get('SUPABASE_KEY')
        
        if supabase_url and supabase_key:
            self.results['passed_checks'].append("Supabase configuration is complete")
        elif supabase_url or supabase_key:
            self.results['high_issues'].append("Incomplete Supabase configuration")
        else:
            self.results['medium_issues'].append("Supabase not configured")
        
        # Check Stripe configuration
        stripe_env = self.secure_config.get('STRIPE_ENVIRONMENT', 'test')
        if stripe_env == 'test':
            stripe_key = self.secure_config.get('STRIPE_TEST_SECRET_KEY')
        else:
            stripe_key = self.secure_config.get('STRIPE_LIVE_SECRET_KEY')
        
        if stripe_key:
            self.results['passed_checks'].append(f"Stripe {stripe_env} configuration is set")
        else:
            self.results['medium_issues'].append(f"Stripe {stripe_env} configuration missing")
        
        # Check Plaid configuration
        plaid_env = self.secure_config.get('PLAID_ENVIRONMENT', 'sandbox')
        if plaid_env == 'sandbox':
            plaid_client_id = self.secure_config.get('PLAID_SANDBOX_CLIENT_ID')
            plaid_secret = self.secure_config.get('PLAID_SANDBOX_SECRET')
        else:
            plaid_client_id = self.secure_config.get('PLAID_PRODUCTION_CLIENT_ID')
            plaid_secret = self.secure_config.get('PLAID_PRODUCTION_SECRET')
        
        if plaid_client_id and plaid_secret:
            self.results['passed_checks'].append(f"Plaid {plaid_env} configuration is complete")
        elif plaid_client_id or plaid_secret:
            self.results['high_issues'].append(f"Incomplete Plaid {plaid_env} configuration")
        else:
            self.results['medium_issues'].append(f"Plaid {plaid_env} not configured")
    
    def _calculate_security_score(self):
        """Calculate overall security score"""
        total_checks = (
            len(self.results['critical_issues']) +
            len(self.results['high_issues']) +
            len(self.results['medium_issues']) +
            len(self.results['low_issues']) +
            len(self.results['passed_checks'])
        )
        
        if total_checks == 0:
            self.results['overall_score'] = 0
            self.results['security_level'] = 'UNKNOWN'
            return
        
        # Weight the issues
        critical_weight = 10
        high_weight = 5
        medium_weight = 2
        low_weight = 1
        passed_weight = 1
        
        score = (
            len(self.results['passed_checks']) * passed_weight -
            len(self.results['critical_issues']) * critical_weight -
            len(self.results['high_issues']) * high_weight -
            len(self.results['medium_issues']) * medium_weight -
            len(self.results['low_issues']) * low_weight
        )
        
        max_score = total_checks * passed_weight
        percentage = max(0, min(100, (score / max_score) * 100))
        
        self.results['overall_score'] = round(percentage, 1)
        
        # Determine security level
        if percentage >= 90:
            self.results['security_level'] = 'EXCELLENT'
        elif percentage >= 80:
            self.results['security_level'] = 'GOOD'
        elif percentage >= 70:
            self.results['security_level'] = 'FAIR'
        elif percentage >= 60:
            self.results['security_level'] = 'POOR'
        else:
            self.results['security_level'] = 'CRITICAL'
    
    def _generate_recommendations(self):
        """Generate security recommendations"""
        logger.info("Generating security recommendations...")
        
        recommendations = []
        
        # Critical issues recommendations
        if self.results['critical_issues']:
            recommendations.append("CRITICAL: Address all critical security issues immediately")
        
        # High issues recommendations
        if self.results['high_issues']:
            recommendations.append("HIGH: Address high-priority security issues as soon as possible")
        
        # Specific recommendations based on issues
        if any('DEBUG' in issue for issue in self.results['critical_issues']):
            recommendations.append("Disable DEBUG mode in production environment")
        
        if any('SSL' in issue for issue in self.results['critical_issues']):
            recommendations.append("Enable SSL redirect in production environment")
        
        if any('weak secret' in issue.lower() for issue in self.results['high_issues']):
            recommendations.append("Rotate all weak secrets using the secret rotation script")
        
        if any('encryption' in issue.lower() for issue in self.results['medium_issues']):
            recommendations.append("Enable configuration encryption for sensitive values")
        
        if any('audit' in issue.lower() for issue in self.results['medium_issues']):
            recommendations.append("Enable audit logging for security monitoring")
        
        # General recommendations
        if self.results['overall_score'] < 80:
            recommendations.append("Review and address all security issues to improve overall security score")
        
        if not self.results['passed_checks']:
            recommendations.append("No security checks passed - review configuration thoroughly")
        
        self.results['recommendations'].extend(recommendations)
    
    def print_report(self):
        """Print a formatted security report"""
        print("\n" + "="*80)
        print("MINGUS APPLICATION SECURITY VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Security Score: {self.results['overall_score']}/100")
        print(f"Security Level: {self.results['security_level']}")
        print()
        
        # Critical Issues
        if self.results['critical_issues']:
            print("🚨 CRITICAL ISSUES:")
            for issue in self.results['critical_issues']:
                print(f"  • {issue}")
            print()
        
        # High Issues
        if self.results['high_issues']:
            print("⚠️  HIGH PRIORITY ISSUES:")
            for issue in self.results['high_issues']:
                print(f"  • {issue}")
            print()
        
        # Medium Issues
        if self.results['medium_issues']:
            print("🔶 MEDIUM PRIORITY ISSUES:")
            for issue in self.results['medium_issues']:
                print(f"  • {issue}")
            print()
        
        # Low Issues
        if self.results['low_issues']:
            print("🔸 LOW PRIORITY ISSUES:")
            for issue in self.results['low_issues']:
                print(f"  • {issue}")
            print()
        
        # Warnings
        if self.results['warnings']:
            print("⚠️  WARNINGS:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
            print()
        
        # Passed Checks
        if self.results['passed_checks']:
            print("✅ PASSED CHECKS:")
            for check in self.results['passed_checks']:
                print(f"  • {check}")
            print()
        
        # Recommendations
        if self.results['recommendations']:
            print("💡 RECOMMENDATIONS:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")
            print()
        
        print("="*80)
        
        # Summary
        if self.results['overall_score'] >= 90:
            print("🎉 Excellent security posture! Keep up the good work.")
        elif self.results['overall_score'] >= 80:
            print("👍 Good security posture with room for improvement.")
        elif self.results['overall_score'] >= 70:
            print("⚠️  Fair security posture - address issues to improve.")
        elif self.results['overall_score'] >= 60:
            print("🚨 Poor security posture - immediate attention required.")
        else:
            print("💀 Critical security posture - immediate action required!")
        
        print("="*80)

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='MINGUS Application Security Validator')
    parser.add_argument('--env-file', '-e', default='.env', help='Environment file to validate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--output', '-o', help='Output results to JSON file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Run validation
    validator = SecurityValidator(args.env_file, args.verbose)
    results = validator.run_comprehensive_validation()
    
    # Print report
    if not args.quiet:
        validator.print_report()
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Exit with appropriate code
    if results['critical_issues']:
        sys.exit(1)
    elif results['high_issues']:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main() 