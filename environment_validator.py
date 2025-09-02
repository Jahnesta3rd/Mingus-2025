#!/usr/bin/env python3
"""
Environment Variable Validator for Flask Applications
Validates and checks all essential environment variables for production deployment
"""

import os
import re
import sys
import json
import hashlib
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvironmentValidator:
    """Comprehensive environment variable validator for Flask applications"""
    
    def __init__(self):
        self.validation_results = []
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
        
    def log_validation(self, category: str, variable: str, status: str, details: str = None, critical: bool = False):
        """Log validation results"""
        result = {
            'category': category,
            'variable': variable,
            'status': status,
            'details': details,
            'critical': critical,
            'timestamp': datetime.now().isoformat()
        }
        
        self.validation_results.append(result)
        
        if status == 'PASS':
            logger.info(f"✅ {category} - {variable}: PASS")
            if details:
                logger.info(f"   Details: {details}")
        elif status == 'WARN':
            logger.warning(f"⚠️  {category} - {variable}: WARN")
            if details:
                logger.warning(f"   Details: {details}")
            self.warnings.append(f"{category} - {variable}: {details}")
        else:
            logger.error(f"❌ {category} - {variable}: FAIL")
            if details:
                logger.error(f"   Details: {details}")
            if critical:
                self.critical_issues.append(f"{category} - {variable}: {details}")
    
    def validate_database_configuration(self):
        """Validate database-related environment variables"""
        logger.info("🔍 Validating Database Configuration...")
        
        # Required database variables
        required_db_vars = {
            'DATABASE_URL': {
                'pattern': r'^postgresql://.*@.*:\d+/.*$',
                'description': 'PostgreSQL connection string'
            }
        }
        
        # Optional database variables with defaults
        optional_db_vars = {
            'DB_POOL_SIZE': {'default': '20', 'type': 'int', 'min': 5, 'max': 100},
            'DB_MAX_OVERFLOW': {'default': '30', 'type': 'int', 'min': 10, 'max': 200},
            'DB_POOL_RECYCLE': {'default': '3600', 'type': 'int', 'min': 300, 'max': 7200},
            'DB_POOL_PRE_PING': {'default': 'true', 'type': 'bool'},
            'DB_CONNECT_TIMEOUT': {'default': '10', 'type': 'int', 'min': 5, 'max': 60},
            'DB_QUERY_TIMEOUT': {'default': '30', 'type': 'int', 'min': 10, 'max': 300}
        }
        
        # Check required variables
        for var, config in required_db_vars.items():
            value = os.getenv(var)
            if not value:
                self.log_validation('DATABASE', var, 'FAIL', f"Required variable not set", True)
            elif not re.match(config['pattern'], value):
                self.log_validation('DATABASE', var, 'FAIL', f"Invalid format: {config['description']}", True)
            else:
                # Mask sensitive parts of the URL
                masked_value = self.mask_sensitive_data(value)
                self.log_validation('DATABASE', var, 'PASS', f"Value: {masked_value}")
        
        # Check optional variables
        for var, config in optional_db_vars.items():
            value = os.getenv(var, config['default'])
            if config['type'] == 'int':
                try:
                    int_val = int(value)
                    if int_val < config['min'] or int_val > config['max']:
                        self.log_validation('DATABASE', var, 'WARN', 
                                         f"Value {int_val} outside recommended range ({config['min']}-{config['max']})")
                    else:
                        self.log_validation('DATABASE', var, 'PASS', f"Value: {int_val}")
                except ValueError:
                    self.log_validation('DATABASE', var, 'FAIL', f"Invalid integer value: {value}")
            elif config['type'] == 'bool':
                if value.lower() in ['true', 'false', '1', '0']:
                    self.log_validation('DATABASE', var, 'PASS', f"Value: {value}")
                else:
                    self.log_validation('DATABASE', var, 'FAIL', f"Invalid boolean value: {value}")
    
    def validate_redis_configuration(self):
        """Validate Redis-related environment variables"""
        logger.info("🔍 Validating Redis Configuration...")
        
        redis_vars = {
            'REDIS_URL': {
                'pattern': r'^redis://.*:\d+/\d*$',
                'description': 'Redis connection URL'
            },
            'CELERY_BROKER_URL': {
                'pattern': r'^redis://.*:\d+/\d*$',
                'description': 'Celery broker URL'
            },
            'CELERY_RESULT_BACKEND': {
                'pattern': r'^redis://.*:\d+/\d*$',
                'description': 'Celery result backend URL'
            }
        }
        
        for var, config in redis_vars.items():
            value = os.getenv(var)
            if not value:
                self.log_validation('REDIS', var, 'WARN', f"Not set - using default Redis configuration")
            elif not re.match(config['pattern'], value):
                self.log_validation('REDIS', var, 'FAIL', f"Invalid format: {config['description']}")
            else:
                self.log_validation('REDIS', var, 'PASS', f"Value: {value}")
    
    def validate_security_configuration(self):
        """Validate security-related environment variables"""
        logger.info("🔍 Validating Security Configuration...")
        
        # Critical security variables
        critical_security_vars = {
            'SECRET_KEY': {
                'min_length': 32,
                'description': 'Flask secret key'
            },
            'JWT_SECRET_KEY': {
                'min_length': 32,
                'description': 'JWT signing key'
            }
        }
        
        # Optional security variables
        optional_security_vars = {
            'FIELD_ENCRYPTION_KEY': {'min_length': 32, 'description': 'Field encryption key'},
            'CONFIG_ENCRYPTION_KEY': {'min_length': 32, 'description': 'Configuration encryption key'},
            'SESSION_COOKIE_SECURE': {'type': 'bool', 'default': 'true'},
            'SESSION_COOKIE_HTTPONLY': {'type': 'bool', 'default': 'true'},
            'SESSION_COOKIE_SAMESITE': {'allowed_values': ['Strict', 'Lax', 'None'], 'default': 'Strict'},
            'PERMANENT_SESSION_LIFETIME': {'type': 'int', 'default': '86400', 'min': 300, 'max': 604800}
        }
        
        # Check critical variables
        for var, config in critical_security_vars.items():
            value = os.getenv(var)
            if not value:
                self.log_validation('SECURITY', var, 'FAIL', f"CRITICAL: {config['description']} not set", True)
            elif len(value) < config['min_length']:
                self.log_validation('SECURITY', var, 'FAIL', 
                                 f"CRITICAL: {config['description']} too short (min {config['min_length']} chars)", True)
            else:
                masked_value = self.mask_sensitive_data(value)
                self.log_validation('SECURITY', var, 'PASS', f"{config['description']}: {masked_value}")
        
        # Check optional variables
        for var, config in optional_security_vars.items():
            value = os.getenv(var, config.get('default'))
            if config.get('type') == 'bool':
                if value.lower() in ['true', 'false', '1', '0']:
                    self.log_validation('SECURITY', var, 'PASS', f"Value: {value}")
                else:
                    self.log_validation('SECURITY', var, 'FAIL', f"Invalid boolean value: {value}")
            elif config.get('type') == 'int':
                try:
                    int_val = int(value)
                    if int_val < config['min'] or int_val > config['max']:
                        self.log_validation('SECURITY', var, 'WARN', 
                                         f"Value {int_val} outside recommended range ({config['min']}-{config['max']})")
                    else:
                        self.log_validation('SECURITY', var, 'PASS', f"Value: {int_val}")
                except ValueError:
                    self.log_validation('SECURITY', var, 'FAIL', f"Invalid integer value: {value}")
            elif config.get('allowed_values'):
                if value in config['allowed_values']:
                    self.log_validation('SECURITY', var, 'PASS', f"Value: {value}")
                else:
                    self.log_validation('SECURITY', var, 'FAIL', 
                                     f"Invalid value: {value}. Allowed: {', '.join(config['allowed_values'])}")
    
    def validate_api_keys(self):
        """Validate external service API keys"""
        logger.info("🔍 Validating API Keys...")
        
        api_keys = {
            'STRIPE_SECRET_KEY': {
                'pattern': r'^sk_(live|test)_[A-Za-z0-9]{24}$',
                'description': 'Stripe secret key'
            },
            'STRIPE_PUBLISHABLE_KEY': {
                'pattern': r'^pk_(live|test)_[A-Za-z0-9]{24}$',
                'description': 'Stripe publishable key'
            },
            'TWILIO_ACCOUNT_SID': {
                'pattern': r'^AC[A-Za-z0-9]{32}$',
                'description': 'Twilio account SID'
            },
            'TWILIO_AUTH_TOKEN': {
                'pattern': r'^[A-Za-z0-9]{32}$',
                'description': 'Twilio auth token'
            },
            'RESEND_API_KEY': {
                'pattern': r'^re_[A-Za-z0-9]{40}$',
                'description': 'Resend API key'
            },
            'OPENAI_API_KEY': {
                'pattern': r'^sk-[A-Za-z0-9]{20}$',
                'description': 'OpenAI API key'
            },
            'PLAID_CLIENT_ID': {
                'pattern': r'^[A-Za-z0-9]{24}$',
                'description': 'Plaid client ID'
            },
            'PLAID_SECRET': {
                'pattern': r'^[A-Za-z0-9]{30}$',
                'description': 'Plaid secret'
            }
        }
        
        for var, config in api_keys.items():
            value = os.getenv(var)
            if not value:
                self.log_validation('API_KEYS', var, 'WARN', f"Not set - {config['description']} service disabled")
            elif not re.match(config['pattern'], value):
                self.log_validation('API_KEYS', var, 'FAIL', f"Invalid format: {config['description']}")
            else:
                masked_value = self.mask_sensitive_data(value)
                self.log_validation('API_KEYS', var, 'PASS', f"{config['description']}: {masked_value}")
    
    def validate_environment_settings(self):
        """Validate environment and debug settings"""
        logger.info("🔍 Validating Environment Settings...")
        
        env_settings = {
            'FLASK_ENV': {
                'allowed_values': ['development', 'testing', 'production'],
                'default': 'production',
                'description': 'Flask environment'
            },
            'DEBUG': {
                'type': 'bool',
                'default': 'false',
                'description': 'Debug mode'
            },
            'FLASK_DEBUG': {
                'type': 'bool',
                'default': 'false',
                'description': 'Flask debug mode'
            },
            'LOG_LEVEL': {
                'allowed_values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'default': 'INFO',
                'description': 'Logging level'
            }
        }
        
        for var, config in env_settings.items():
            value = os.getenv(var, config['default'])
            if config.get('type') == 'bool':
                if value.lower() in ['true', 'false', '1', '0']:
                    bool_val = value.lower() in ['true', '1']
                    if var in ['DEBUG', 'FLASK_DEBUG'] and bool_val and os.getenv('FLASK_ENV') == 'production':
                        self.log_validation('ENVIRONMENT', var, 'FAIL', 
                                         f"CRITICAL: Debug mode enabled in production!", True)
                    else:
                        self.log_validation('ENVIRONMENT', var, 'PASS', f"Value: {value}")
                else:
                    self.log_validation('ENVIRONMENT', var, 'FAIL', f"Invalid boolean value: {value}")
            elif config.get('allowed_values'):
                if value in config['allowed_values']:
                    self.log_validation('ENVIRONMENT', var, 'PASS', f"Value: {value}")
                else:
                    self.log_validation('ENVIRONMENT', var, 'FAIL', 
                                     f"Invalid value: {value}. Allowed: {', '.join(config['allowed_values'])}")
    
    def validate_email_configuration(self):
        """Validate email service configuration"""
        logger.info("🔍 Validating Email Configuration...")
        
        email_vars = {
            'MAIL_SERVER': {'description': 'SMTP server'},
            'MAIL_PORT': {'type': 'int', 'default': '587', 'min': 25, 'max': 587},
            'MAIL_USE_TLS': {'type': 'bool', 'default': 'true'},
            'MAIL_USERNAME': {'description': 'SMTP username'},
            'MAIL_PASSWORD': {'description': 'SMTP password'},
            'MAIL_DEFAULT_SENDER': {'description': 'Default sender email'},
            'RESEND_FROM_EMAIL': {'description': 'Resend from email'},
            'RESEND_FROM_NAME': {'description': 'Resend from name'}
        }
        
        for var, config in email_vars.items():
            value = os.getenv(var)
            if not value:
                if var in ['MAIL_USERNAME', 'MAIL_PASSWORD']:
                    self.log_validation('EMAIL', var, 'WARN', f"Not set - email service may be disabled")
                else:
                    self.log_validation('EMAIL', var, 'PASS', f"Using default: {config.get('default', 'None')}")
            elif config.get('type') == 'int':
                try:
                    int_val = int(value)
                    if int_val < config['min'] or int_val > config['max']:
                        self.log_validation('EMAIL', var, 'WARN', 
                                         f"Value {int_val} outside recommended range ({config['min']}-{config['max']})")
                    else:
                        self.log_validation('EMAIL', var, 'PASS', f"Value: {int_val}")
                except ValueError:
                    self.log_validation('EMAIL', var, 'FAIL', f"Invalid integer value: {value}")
            elif config.get('type') == 'bool':
                if value.lower() in ['true', 'false', '1', '0']:
                    self.log_validation('EMAIL', var, 'PASS', f"Value: {value}")
                else:
                    self.log_validation('EMAIL', var, 'FAIL', f"Invalid boolean value: {value}")
            else:
                self.log_validation('EMAIL', var, 'PASS', f"Value: {value}")
    
    def validate_monitoring_configuration(self):
        """Validate monitoring and logging configuration"""
        logger.info("🔍 Validating Monitoring Configuration...")
        
        monitoring_vars = {
            'ENABLE_PERFORMANCE_MONITORING': {'type': 'bool', 'default': 'true'},
            'ENABLE_ERROR_TRACKING': {'type': 'bool', 'default': 'true'},
            'ENABLE_USAGE_ANALYTICS': {'type': 'bool', 'default': 'true'},
            'LOG_FILE': {'default': 'logs/mingus.log'},
            'LOG_ROTATION': {'default': '1 day'},
            'LOG_RETENTION': {'default': '30 days'},
            'SENTRY_DSN': {'description': 'Sentry DSN for error tracking'},
            'GRAFANA_PASSWORD': {'description': 'Grafana admin password'}
        }
        
        for var, config in monitoring_vars.items():
            value = os.getenv(var, config.get('default'))
            if config.get('type') == 'bool':
                if value.lower() in ['true', 'false', '1', '0']:
                    self.log_validation('MONITORING', var, 'PASS', f"Value: {value}")
                else:
                    self.log_validation('MONITORING', var, 'FAIL', f"Invalid boolean value: {value}")
            else:
                self.log_validation('MONITORING', var, 'PASS', f"Value: {value}")
    
    def mask_sensitive_data(self, value: str) -> str:
        """Mask sensitive data in environment variables"""
        if not value:
            return value
        
        # Mask API keys, passwords, and secrets
        if any(keyword in value.lower() for keyword in ['key', 'secret', 'password', 'token']):
            if len(value) > 8:
                return value[:4] + '*' * (len(value) - 8) + value[-4:]
            else:
                return '*' * len(value)
        
        # Mask database URLs
        if value.startswith('postgresql://'):
            parts = value.split('@')
            if len(parts) == 2:
                return f"postgresql://***:***@{parts[1]}"
        
        # Mask Redis URLs
        if value.startswith('redis://'):
            if '@' in value:
                parts = value.split('@')
                return f"redis://***:***@{parts[1]}"
            else:
                return value
        
        return value
    
    def generate_production_checklist(self) -> str:
        """Generate production deployment checklist"""
        checklist = """
# 🚀 PRODUCTION ENVIRONMENT CHECKLIST

## ✅ CRITICAL REQUIREMENTS

### Security
- [ ] SECRET_KEY is set and at least 32 characters long
- [ ] JWT_SECRET_KEY is set and at least 32 characters long
- [ ] FLASK_ENV is set to 'production'
- [ ] DEBUG is set to 'false'
- [ ] SESSION_COOKIE_SECURE is set to 'true'
- [ ] SESSION_COOKIE_HTTPONLY is set to 'true'
- [ ] SESSION_COOKIE_SAMESITE is set to 'Strict'

### Database
- [ ] DATABASE_URL points to production database
- [ ] Database user has minimal required privileges
- [ ] Connection pooling is configured appropriately
- [ ] Database backups are configured

### External Services
- [ ] All required API keys are set
- [ ] API keys have appropriate permissions
- [ ] Rate limiting is configured
- [ ] Error handling is implemented

## ⚠️ RECOMMENDATIONS

### Performance
- [ ] Connection pool size is optimized for production load
- [ ] Redis is configured for production
- [ ] Logging level is set to INFO or higher
- [ ] Monitoring and alerting are configured

### Security
- [ ] HTTPS is enforced
- [ ] CORS is properly configured
- [ ] Input validation is implemented
- [ ] Rate limiting is enabled

### Monitoring
- [ ] Health check endpoints are implemented
- [ ] Error tracking is configured
- [ ] Performance monitoring is enabled
- [ ] Log aggregation is set up

## 🔧 CONFIGURATION FILES

- [ ] .env file is created with production values
- [ ] Environment variables are loaded correctly
- [ ] Configuration is validated on startup
- [ ] Secrets are stored securely (not in code)

## 🧪 TESTING

- [ ] Application starts without errors
- [ ] Database connections are working
- [ ] External API calls are successful
- [ ] Error handling works correctly
- [ ] Performance is acceptable under load
"""
        return checklist
    
    def generate_environment_template(self) -> str:
        """Generate a comprehensive environment template"""
        template = """# =====================================================
# FLASK APPLICATION ENVIRONMENT CONFIGURATION
# =====================================================
# Copy this file to .env and update with your actual values
# DO NOT commit the .env file to version control

# =====================================================
# FLASK APPLICATION SETTINGS
# =====================================================
FLASK_ENV=production
DEBUG=false
FLASK_DEBUG=false
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-characters-long

# =====================================================
# DATABASE CONFIGURATION
# =====================================================
DATABASE_URL=postgresql://username:password@host:port/database
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true
DB_CONNECT_TIMEOUT=10
DB_QUERY_TIMEOUT=30

# =====================================================
# REDIS CONFIGURATION
# =====================================================
REDIS_URL=redis://host:port/database
CELERY_BROKER_URL=redis://host:port/database
CELERY_RESULT_BACKEND=redis://host:port/database

# =====================================================
# SECURITY SETTINGS
# =====================================================
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
PERMANENT_SESSION_LIFETIME=86400
FIELD_ENCRYPTION_KEY=your-32-character-encryption-key

# =====================================================
# EXTERNAL API KEYS
# =====================================================
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
TWILIO_ACCOUNT_SID=ACyour_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
RESEND_API_KEY=re_your_resend_api_key
OPENAI_API_KEY=sk-your_openai_api_key

# =====================================================
# EMAIL CONFIGURATION
# =====================================================
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_specific_password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# =====================================================
# MONITORING AND LOGGING
# =====================================================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_ROTATION=1 day
LOG_RETENTION=30 days
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_ERROR_TRACKING=true
SENTRY_DSN=your_sentry_dsn

# =====================================================
# FEATURE FLAGS
# =====================================================
ENABLE_ARTICLE_LIBRARY=true
ENABLE_AI_RECOMMENDATIONS=true
ENABLE_ANALYTICS=true
ENABLE_SOCIAL_SHARING=false

# =====================================================
# PERFORMANCE SETTINGS
# =====================================================
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300
RATELIMIT_ENABLED=true
RATELIMIT_DEFAULT=100 per minute
"""
        return template
    
    def run_all_validations(self):
        """Run all environment validations"""
        logger.info("🚀 Starting Environment Variable Validation...")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        self.validate_database_configuration()
        self.validate_redis_configuration()
        self.validate_security_configuration()
        self.validate_api_keys()
        self.validate_environment_settings()
        self.validate_email_configuration()
        self.validate_monitoring_configuration()
        
        return self.generate_validation_report()
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        total_tests = len(self.validation_results)
        passed_tests = len([r for r in self.validation_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.validation_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.validation_results if r['status'] == 'WARN'])
        
        logger.info("\n" + "="*60)
        logger.info("📊 ENVIRONMENT VALIDATION REPORT")
        logger.info("="*60)
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"⚠️  Warnings: {warning_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        # Show critical issues
        if self.critical_issues:
            logger.error("\n🚨 CRITICAL ISSUES:")
            for issue in self.critical_issues:
                logger.error(f"  - {issue}")
        
        # Show failed tests
        if failed_tests > 0:
            logger.error("\n❌ FAILED TESTS:")
            for result in self.validation_results:
                if result['status'] == 'FAIL':
                    logger.error(f"  - {result['category']} - {result['variable']}: {result['details']}")
        
        # Show warnings
        if warning_tests > 0:
            logger.warning("\n⚠️  WARNINGS:")
            for result in self.validation_results:
                if result['status'] == 'WARN':
                    logger.warning(f"  - {result['category']} - {result['variable']}: {result['details']}")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        if self.critical_issues:
            logger.info("  - Fix all critical issues before production deployment")
            logger.info("  - Review security configuration")
            logger.info("  - Verify database connectivity")
        else:
            logger.info("  - Environment configuration looks good!")
            logger.info("  - Review warnings for optimization opportunities")
            logger.info("  - Test application thoroughly before deployment")
        
        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'warnings': warning_tests,
            'critical_issues': len(self.critical_issues),
            'results': self.validation_results
        }

def main():
    """Main function"""
    validator = EnvironmentValidator()
    
    try:
        results = validator.run_all_validations()
        
        # Generate additional files
        checklist = validator.generate_production_checklist()
        template = validator.generate_environment_template()
        
        # Write checklist to file
        with open('PRODUCTION_CHECKLIST.md', 'w') as f:
            f.write(checklist)
        
        # Write template to file
        with open('environment_template.env', 'w') as f:
            f.write(template)
        
        logger.info("\n📁 Generated files:")
        logger.info("  - PRODUCTION_CHECKLIST.md")
        logger.info("  - environment_template.env")
        
        # Exit with error code if critical issues exist
        if results['critical_issues'] > 0:
            logger.error(f"\n🚨 {results['critical_issues']} critical issues found!")
            sys.exit(1)
        else:
            logger.info("\n🎉 Environment validation completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
