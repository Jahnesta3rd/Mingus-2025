#!/usr/bin/env python3
"""
Email Verification System Configuration Validator
Validates environment variables and configuration settings

Usage:
    python validate_config.py --env development
    python validate_config.py --env production --strict
"""

import argparse
import os
import sys
import secrets
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime

def generate_secure_secret(length: int = 64) -> str:
    """Generate a cryptographically secure secret"""
    return secrets.token_urlsafe(length)

class ConfigValidator:
    """Validate email verification system configuration"""
    
    def __init__(self, environment: str, strict: bool = False):
        self.environment = environment
        self.strict = strict
        self.validation_results = []
        self.errors = []
        self.warnings = []
        
    def log_validation(self, component: str, status: str, details: str = "", severity: str = "INFO"):
        """Log validation result"""
        result = {
            'component': component,
            'status': status,
            'details': details,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.validation_results.append(result)
        
        if severity == "ERROR":
            self.errors.append(f"{component}: {details}")
        elif severity == "WARNING":
            self.warnings.append(f"{component}: {details}")
        
        # Print with appropriate emoji
        status_icons = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARNING": "⚠️",
            "INFO": "ℹ️"
        }
        
        icon = status_icons.get(status, "ℹ️")
        print(f"{icon} {component}: {status} - {details}")
    
    def validate_environment_variable(self, var_name: str, required: bool = True, 
                                    validator=None, default_value=None) -> bool:
        """Validate a single environment variable"""
        value = os.getenv(var_name, default_value)
        
        if required and not value:
            self.log_validation(var_name, "FAIL", f"Required environment variable not set", "ERROR")
            return False
        
        if value and validator:
            try:
                if not validator(value):
                    self.log_validation(var_name, "FAIL", f"Invalid value: {value}", "ERROR")
                    return False
            except Exception as e:
                self.log_validation(var_name, "FAIL", f"Validation error: {str(e)}", "ERROR")
                return False
        
        if value:
            self.log_validation(var_name, "PASS", f"Set to: {value[:50]}{'...' if len(str(value)) > 50 else ''}")
        else:
            self.log_validation(var_name, "WARNING", "Not set (using default)")
        
        return True
    
    def validate_url_format(self, url: str) -> bool:
        """Validate URL format"""
        return url.startswith(('http://', 'https://'))
    
    def validate_https_in_production(self, url: str) -> bool:
        """Validate HTTPS in production"""
        if self.environment == 'production':
            return url.startswith('https://')
        return True
    
    def validate_secret_length(self, secret: str, min_length: int = 32) -> bool:
        """Validate secret length"""
        return len(secret) >= min_length
    
    def validate_boolean(self, value: str) -> bool:
        """Validate boolean value"""
        return value.lower() in ('true', 'false', '1', '0', 'yes', 'no')
    
    def validate_integer(self, value: str, min_val: int = None, max_val: int = None) -> bool:
        """Validate integer value"""
        try:
            int_val = int(value)
            if min_val is not None and int_val < min_val:
                return False
            if max_val is not None and int_val > max_val:
                return False
            return True
        except ValueError:
            return False
    
    def validate_reminder_schedule(self, schedule: str) -> bool:
        """Validate reminder schedule format"""
        try:
            days = [int(d.strip()) for d in schedule.split(',')]
            return all(0 <= day <= 30 for day in days)
        except ValueError:
            return False
    
    def validate_token_security(self) -> bool:
        """Validate token security configuration"""
        print("\n🔐 Validating Token Security Configuration...")
        
        # Validate secret
        secret_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_SECRET',
            required=True,
            validator=lambda x: self.validate_secret_length(x, 32 if self.environment == 'development' else 64)
        )
        
        # Validate token length
        token_length_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_TOKEN_LENGTH',
            required=False,
            validator=lambda x: self.validate_integer(x, 32, 128),
            default_value='32' if self.environment == 'development' else '64'
        )
        
        # Validate expiry hours
        expiry_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_EXPIRY_HOURS',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 168),  # 1 hour to 1 week
            default_value='24'
        )
        
        return secret_valid and token_length_valid and expiry_valid
    
    def validate_rate_limiting(self) -> bool:
        """Validate rate limiting configuration"""
        print("\n🚦 Validating Rate Limiting Configuration...")
        
        # Validate max attempts per hour
        max_attempts_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 1000),
            default_value='50' if self.environment == 'development' else '5'
        )
        
        # Validate max attempts per user hour
        max_user_attempts_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 1000),
            default_value='20' if self.environment == 'development' else '3'
        )
        
        # Validate max resend attempts
        max_resend_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 100),
            default_value='10' if self.environment == 'development' else '3'
        )
        
        # Validate cooldown hours
        cooldown_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS',
            required=False,
            validator=lambda x: self.validate_integer(x, 0, 24),
            default_value='0' if self.environment == 'development' else '2'
        )
        
        # Validate failed attempts
        failed_attempts_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 100),
            default_value='10' if self.environment == 'development' else '3'
        )
        
        # Validate lockout duration
        lockout_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS',
            required=False,
            validator=lambda x: self.validate_integer(x, 0, 168),
            default_value='0' if self.environment == 'development' else '2'
        )
        
        return all([
            max_attempts_valid, max_user_attempts_valid, max_resend_valid,
            cooldown_valid, failed_attempts_valid, lockout_valid
        ])
    
    def validate_email_configuration(self) -> bool:
        """Validate email configuration"""
        print("\n📧 Validating Email Configuration...")
        
        # Validate email service provider
        provider_valid = self.validate_environment_variable(
            'EMAIL_SERVICE_PROVIDER',
            required=False,
            validator=lambda x: x in ['resend', 'smtp', 'sendgrid'],
            default_value='resend'
        )
        
        # Validate default from email
        from_email_valid = self.validate_environment_variable(
            'EMAIL_DEFAULT_FROM',
            required=False,
            default_value='dev@localhost' if self.environment == 'development' else 'noreply@mingus.app'
        )
        
        # Validate reply-to email
        reply_to_valid = self.validate_environment_variable(
            'EMAIL_REPLY_TO',
            required=False,
            default_value='dev@localhost' if self.environment == 'development' else 'support@mingus.app'
        )
        
        # Validate template directory
        template_dir_valid = self.validate_environment_variable(
            'EMAIL_TEMPLATE_DIR',
            required=False,
            default_value='backend/templates'
        )
        
        return all([provider_valid, from_email_valid, reply_to_valid, template_dir_valid])
    
    def validate_reminder_system(self) -> bool:
        """Validate reminder system configuration"""
        print("\n⏰ Validating Reminder System Configuration...")
        
        # Validate enable reminders
        enable_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_ENABLE_REMINDERS',
            required=False,
            validator=self.validate_boolean,
            default_value='true'
        )
        
        # Validate reminder schedule
        schedule_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS',
            required=False,
            validator=self.validate_reminder_schedule,
            default_value='0,1,2' if self.environment == 'development' else '7,14'
        )
        
        # Validate max reminders
        max_reminders_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 10),
            default_value='5' if self.environment == 'development' else '2'
        )
        
        return all([enable_valid, schedule_valid, max_reminders_valid])
    
    def validate_audit_and_monitoring(self) -> bool:
        """Validate audit and monitoring configuration"""
        print("\n📊 Validating Audit and Monitoring Configuration...")
        
        # Validate audit logging
        audit_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_ENABLE_AUDIT_LOGGING',
            required=False,
            validator=self.validate_boolean,
            default_value='true'
        )
        
        # Validate audit retention
        retention_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_AUDIT_LOG_RETENTION_DAYS',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 3650),  # 1 day to 10 years
            default_value='7' if self.environment == 'development' else '365'
        )
        
        # Validate monitoring
        monitoring_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_ENABLE_MONITORING',
            required=False,
            validator=self.validate_boolean,
            default_value='false' if self.environment == 'development' else 'true'
        )
        
        # Validate metrics interval
        metrics_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_METRICS_INTERVAL_MINUTES',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 1440),  # 1 minute to 1 day
            default_value='60' if self.environment == 'development' else '5'
        )
        
        return all([audit_valid, retention_valid, monitoring_valid, metrics_valid])
    
    def validate_integration_configuration(self) -> bool:
        """Validate integration configuration"""
        print("\n🔗 Validating Integration Configuration...")
        
        # Validate frontend URL
        frontend_valid = self.validate_environment_variable(
            'FRONTEND_URL',
            required=True,
            validator=lambda x: self.validate_url_format(x) and self.validate_https_in_production(x)
        )
        
        # Validate API base URL
        api_valid = self.validate_environment_variable(
            'API_BASE_URL',
            required=True,
            validator=lambda x: self.validate_url_format(x) and self.validate_https_in_production(x)
        )
        
        # Validate Redis URL
        redis_valid = self.validate_environment_variable(
            'REDIS_URL',
            required=False,
            default_value='redis://localhost:6379/0' if self.environment == 'development' else None
        )
        
        # Validate database URL
        database_valid = self.validate_environment_variable(
            'DATABASE_URL',
            required=True
        )
        
        # Validate Celery broker URL
        celery_valid = self.validate_environment_variable(
            'CELERY_BROKER_URL',
            required=False,
            default_value='redis://localhost:6379/1' if self.environment == 'development' else None
        )
        
        return all([frontend_valid, api_valid, redis_valid, database_valid, celery_valid])
    
    def validate_security_configuration(self) -> bool:
        """Validate security configuration"""
        print("\n🛡️ Validating Security Configuration...")
        
        # Validate IP tracking
        ip_tracking_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_TRACK_IP_ADDRESSES',
            required=False,
            validator=self.validate_boolean,
            default_value='false' if self.environment == 'development' else 'true'
        )
        
        # Validate User-Agent tracking
        ua_tracking_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_TRACK_USER_AGENTS',
            required=False,
            validator=self.validate_boolean,
            default_value='false' if self.environment == 'development' else 'true'
        )
        
        # Validate geolocation tracking
        geo_tracking_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_TRACK_GEO_LOCATION',
            required=False,
            validator=self.validate_boolean,
            default_value='false'
        )
        
        # Validate concurrent sessions
        sessions_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_MAX_CONCURRENT_SESSIONS',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 100),
            default_value='10' if self.environment == 'development' else '2'
        )
        
        # Validate session timeout
        timeout_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_SESSION_TIMEOUT_HOURS',
            required=False,
            validator=lambda x: self.validate_integer(x, 1, 168),
            default_value='48' if self.environment == 'development' else '12'
        )
        
        return all([ip_tracking_valid, ua_tracking_valid, geo_tracking_valid, sessions_valid, timeout_valid])
    
    def validate_development_settings(self) -> bool:
        """Validate development-specific settings"""
        print("\n🔧 Validating Development Settings...")
        
        # Validate debug mode
        debug_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_DEBUG',
            required=False,
            validator=self.validate_boolean,
            default_value='true' if self.environment == 'development' else 'false'
        )
        
        # Validate test mode
        test_mode_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_TEST_MODE',
            required=False,
            validator=self.validate_boolean,
            default_value='true' if self.environment == 'development' else 'false'
        )
        
        # Validate mock email service
        mock_email_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE',
            required=False,
            validator=self.validate_boolean,
            default_value='true' if self.environment == 'development' else 'false'
        )
        
        # Validate test email override
        test_email_valid = self.validate_environment_variable(
            'EMAIL_VERIFICATION_TEST_EMAIL',
            required=False,
            default_value=''
        )
        
        # Production security checks
        if self.environment == 'production':
            if os.getenv('EMAIL_VERIFICATION_DEBUG') == 'true':
                self.log_validation('PRODUCTION_SECURITY', 'FAIL', 'Debug mode enabled in production', 'ERROR')
                return False
            
            if os.getenv('EMAIL_VERIFICATION_TEST_MODE') == 'true':
                self.log_validation('PRODUCTION_SECURITY', 'FAIL', 'Test mode enabled in production', 'ERROR')
                return False
            
            if os.getenv('EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE') == 'true':
                self.log_validation('PRODUCTION_SECURITY', 'FAIL', 'Mock email service enabled in production', 'ERROR')
                return False
        
        return all([debug_valid, test_mode_valid, mock_email_valid, test_email_valid])
    
    def validate_existing_services(self) -> bool:
        """Validate existing service integration"""
        print("\n🔌 Validating Existing Service Integration...")
        
        # Validate Resend API key
        resend_valid = self.validate_environment_variable(
            'RESEND_API_KEY',
            required=True
        )
        
        # Validate Flask environment
        flask_env_valid = self.validate_environment_variable(
            'FLASK_ENV',
            required=False,
            validator=lambda x: x in ['development', 'staging', 'production'],
            default_value='development'
        )
        
        # Validate Flask secret key
        flask_secret_valid = self.validate_environment_variable(
            'FLASK_SECRET_KEY',
            required=False,
            default_value='dev-secret-key-change-in-production'
        )
        
        return all([resend_valid, flask_env_valid, flask_secret_valid])
    
    def generate_configuration_report(self) -> str:
        """Generate comprehensive configuration report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"config_validation_report_{self.environment}_{timestamp}.json"
        
        # Calculate summary
        total_checks = len(self.validation_results)
        passed_checks = len([r for r in self.validation_results if r['status'] == 'PASS'])
        failed_checks = len([r for r in self.validation_results if r['status'] == 'FAIL'])
        warning_checks = len([r for r in self.validation_results if r['status'] == 'WARNING'])
        
        report_data = {
            'validation_name': 'Email Verification System Configuration',
            'environment': self.environment,
            'timestamp': datetime.utcnow().isoformat(),
            'strict_mode': self.strict,
            'summary': {
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': failed_checks,
                'warning_checks': warning_checks,
                'success_rate': f"{(passed_checks/total_checks)*100:.1f}%" if total_checks > 0 else "0%"
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'checks': self.validation_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_file
    
    def run_validation(self) -> bool:
        """Run complete configuration validation"""
        print(f"🔍 Starting Email Verification System Configuration Validation")
        print(f"🌍 Environment: {self.environment.upper()}")
        print(f"🔒 Strict Mode: {'Enabled' if self.strict else 'Disabled'}")
        print("=" * 70)
        
        try:
            # Run all validation checks
            validations = [
                self.validate_token_security(),
                self.validate_rate_limiting(),
                self.validate_email_configuration(),
                self.validate_reminder_system(),
                self.validate_audit_and_monitoring(),
                self.validate_integration_configuration(),
                self.validate_security_configuration(),
                self.validate_development_settings(),
                self.validate_existing_services()
            ]
            
            # Generate report
            report_file = self.generate_configuration_report()
            
            # Print summary
            passed = sum(validations)
            total = len(validations)
            
            print("\n" + "=" * 70)
            print("📊 CONFIGURATION VALIDATION SUMMARY")
            print("=" * 70)
            print(f"✅ Passed: {passed}/{total}")
            print(f"❌ Failed: {total - passed}/{total}")
            print(f"⚠️  Warnings: {len(self.warnings)}")
            print(f"📄 Report saved to: {report_file}")
            
            if self.strict and self.warnings:
                print(f"\n⚠️  Strict mode enabled - {len(self.warnings)} warnings found")
                print("Warnings in strict mode are treated as errors")
                return False
            
            if passed == total:
                print("\n🎉 All configuration validations passed!")
                return True
            else:
                print(f"\n⚠️  {total - passed} validation(s) failed. Please review the report.")
                return False
                
        except Exception as e:
            print(f"\n💥 Validation failed: {e}")
            return False

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Email Verification Configuration Validator')
    parser.add_argument('--env', choices=['development', 'staging', 'production'], 
                       required=True, help='Environment to validate')
    parser.add_argument('--strict', action='store_true', 
                       help='Treat warnings as errors')
    parser.add_argument('--generate-secret', action='store_true',
                       help='Generate a secure secret for the specified environment')
    
    args = parser.parse_args()
    
    # Generate secret if requested
    if args.generate_secret:
        if args.env == 'production':
            secret = generate_secure_secret(64)
            print(f"🔐 Generated production secret (64 bytes): {secret}")
        else:
            secret = generate_secure_secret(32)
            print(f"🔐 Generated {args.env} secret (32 bytes): {secret}")
        
        print(f"\n📝 Add this to your .env.{args.env} file:")
        print(f"EMAIL_VERIFICATION_SECRET={secret}")
        return
    
    # Create validator instance
    validator = ConfigValidator(args.env, args.strict)
    
    # Run validation
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
