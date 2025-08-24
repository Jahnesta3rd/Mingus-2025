#!/usr/bin/env python3
"""
Configuration Validation Script for MINGUS Application
====================================================

This script validates the secure configuration system and provides detailed reports
on configuration status, security issues, and recommendations.

Usage:
    python scripts/validate_config.py [--env-file .env] [--verbose] [--fix]

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import argparse
import json
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.secure_config import (
    SecureConfigManager, 
    SecurityConfig, 
    SecurityLevel,
    ConfigValidationError,
    SecretRotationError
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigValidator:
    """Configuration validator with detailed reporting"""
    
    def __init__(self, env_file: Optional[str] = None, verbose: bool = False):
        """
        Initialize configuration validator
        
        Args:
            env_file: Path to environment file
            verbose: Enable verbose output
        """
        self.env_file = env_file
        self.verbose = verbose
        self.security_config = SecurityConfig(
            encryption_enabled=True,
            audit_logging_enabled=True,
            validation_enabled=True,
            secret_rotation_enabled=True,
            weak_secret_detection=True,
            startup_warnings_enabled=True
        )
        
        # Load environment variables from file if specified
        if env_file and Path(env_file).exists():
            self._load_env_file(env_file)
        
        # Initialize secure config manager
        try:
            self.config_manager = SecureConfigManager(env_file, self.security_config)
        except ConfigValidationError as e:
            logger.error(f"Failed to initialize secure config manager: {e}")
            raise
    
    def _load_env_file(self, env_file: str):
        """Load environment variables from file"""
        logger.info(f"Loading environment variables from {env_file}")
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    os.environ[key] = value
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Perform comprehensive configuration validation
        
        Returns:
            Validation results dictionary
        """
        results = {
            'overall_status': 'PASS',
            'validation_results': {},
            'security_issues': [],
            'recommendations': [],
            'audit_log': [],
            'config_summary': {}
        }
        
        try:
            # Basic configuration validation
            results['validation_results']['basic'] = self._validate_basic_config()
            
            # Security validation
            results['validation_results']['security'] = self._validate_security_config()
            
            # Environment-specific validation
            results['validation_results']['environment'] = self._validate_environment_config()
            
            # External service validation
            results['validation_results']['external_services'] = self._validate_external_services()
            
            # Performance validation
            results['validation_results']['performance'] = self._validate_performance_config()
            
            # Get audit log
            results['audit_log'] = self.config_manager.get_audit_log()
            
            # Get configuration summary
            results['config_summary'] = self.config_manager.export_config(include_secrets=False)
            
            # Determine overall status
            self._determine_overall_status(results)
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            results['overall_status'] = 'FAIL'
            results['error'] = str(e)
        
        return results
    
    def _validate_basic_config(self) -> Dict[str, Any]:
        """Validate basic configuration requirements"""
        logger.info("Validating basic configuration...")
        
        results = {
            'status': 'PASS',
            'issues': [],
            'warnings': [],
            'checks': {}
        }
        
        # Check required environment variables
        required_vars = [
            'SECRET_KEY', 'DATABASE_URL', 'FIELD_ENCRYPTION_KEY', 
            'DJANGO_SECRET_KEY', 'SUPABASE_URL', 'SUPABASE_KEY'
        ]
        
        for var in required_vars:
            value = self.config_manager.get(var)
            if not value:
                results['issues'].append(f"Missing required environment variable: {var}")
                results['status'] = 'FAIL'
            else:
                results['checks'][var] = 'PRESENT'
        
        # Check environment setting
        flask_env = self.config_manager.get('FLASK_ENV')
        if not flask_env:
            results['issues'].append("FLASK_ENV not set")
            results['status'] = 'FAIL'
        elif flask_env not in ['development', 'testing', 'production']:
            results['warnings'].append(f"Invalid FLASK_ENV: {flask_env}")
        else:
            results['checks']['FLASK_ENV'] = flask_env
        
        return results
    
    def _validate_security_config(self) -> Dict[str, Any]:
        """Validate security configuration"""
        logger.info("Validating security configuration...")
        
        results = {
            'status': 'PASS',
            'issues': [],
            'warnings': [],
            'checks': {}
        }
        
        # Check secret strength
        secret_key = self.config_manager.get('SECRET_KEY')
        if secret_key and self._is_weak_secret(secret_key):
            results['warnings'].append("SECRET_KEY appears to be weak")
            results['checks']['SECRET_KEY_STRENGTH'] = 'WEAK'
        else:
            results['checks']['SECRET_KEY_STRENGTH'] = 'STRONG'
        
        # Check encryption key
        encryption_key = self.config_manager.get('FIELD_ENCRYPTION_KEY')
        if encryption_key and self._is_weak_secret(encryption_key):
            results['warnings'].append("FIELD_ENCRYPTION_KEY appears to be weak")
            results['checks']['ENCRYPTION_KEY_STRENGTH'] = 'WEAK'
        else:
            results['checks']['ENCRYPTION_KEY_STRENGTH'] = 'STRONG'
        
        # Check production security settings
        if self.config_manager.get('FLASK_ENV') == 'production':
            if self.config_manager.get('DEBUG') == 'true':
                results['issues'].append("DEBUG mode enabled in production")
                results['status'] = 'FAIL'
            
            if self.config_manager.get('SECURE_SSL_REDIRECT') != 'true':
                results['issues'].append("SSL redirect not enabled in production")
                results['status'] = 'FAIL'
            
            if self.config_manager.get('SESSION_COOKIE_SECURE') != 'true':
                results['issues'].append("Secure session cookies not enabled in production")
                results['status'] = 'FAIL'
        
        # Check audit logging
        if self.config_manager.get('AUDIT_LOG_ENABLED') != 'true':
            results['warnings'].append("Audit logging not enabled")
        
        return results
    
    def _validate_environment_config(self) -> Dict[str, Any]:
        """Validate environment-specific configuration"""
        logger.info("Validating environment configuration...")
        
        results = {
            'status': 'PASS',
            'issues': [],
            'warnings': [],
            'checks': {}
        }
        
        flask_env = self.config_manager.get('FLASK_ENV')
        
        if flask_env == 'production':
            # Production-specific checks
            if not self.config_manager.get('STRIPE_LIVE_SECRET_KEY'):
                results['warnings'].append("Live Stripe key not configured for production")
            
            if not self.config_manager.get('PLAID_PRODUCTION_CLIENT_ID'):
                results['warnings'].append("Production Plaid credentials not configured")
            
            if self.config_manager.get('BACKUP_ENABLED') != 'true':
                results['warnings'].append("Backup not enabled in production")
        
        elif flask_env == 'development':
            # Development-specific checks
            if self.config_manager.get('DEBUG') != 'true':
                results['warnings'].append("DEBUG mode not enabled in development")
        
        return results
    
    def _validate_external_services(self) -> Dict[str, Any]:
        """Validate external service configuration"""
        logger.info("Validating external service configuration...")
        
        results = {
            'status': 'PASS',
            'issues': [],
            'warnings': [],
            'checks': {}
        }
        
        # Check Stripe configuration
        stripe_env = self.config_manager.get('STRIPE_ENVIRONMENT')
        if stripe_env == 'test':
            if not self.config_manager.get('STRIPE_TEST_SECRET_KEY'):
                results['warnings'].append("Stripe test key not configured")
        elif stripe_env == 'live':
            if not self.config_manager.get('STRIPE_LIVE_SECRET_KEY'):
                results['issues'].append("Stripe live key not configured")
                results['status'] = 'FAIL'
        
        # Check Plaid configuration
        plaid_env = self.config_manager.get('PLAID_ENVIRONMENT')
        if plaid_env == 'sandbox':
            if not self.config_manager.get('PLAID_SANDBOX_CLIENT_ID'):
                results['warnings'].append("Plaid sandbox credentials not configured")
        elif plaid_env == 'production':
            if not self.config_manager.get('PLAID_PRODUCTION_CLIENT_ID'):
                results['issues'].append("Plaid production credentials not configured")
                results['status'] = 'FAIL'
        
        # Check email configuration
        email_provider = self.config_manager.get('EMAIL_PROVIDER')
        if email_provider == 'resend':
            if not self.config_manager.get('RESEND_API_KEY'):
                results['warnings'].append("Resend API key not configured")
        elif email_provider == 'gmail':
            if not self.config_manager.get('MAIL_USERNAME') or not self.config_manager.get('MAIL_PASSWORD'):
                results['warnings'].append("Gmail credentials not configured")
        
        # Check SMS configuration
        if not self.config_manager.get('TWILIO_ACCOUNT_SID'):
            results['warnings'].append("Twilio credentials not configured")
        
        return results
    
    def _validate_performance_config(self) -> Dict[str, Any]:
        """Validate performance-related configuration"""
        logger.info("Validating performance configuration...")
        
        results = {
            'status': 'PASS',
            'issues': [],
            'warnings': [],
            'checks': {}
        }
        
        # Check database pool settings
        pool_size = int(self.config_manager.get('DB_POOL_SIZE', '10'))
        if pool_size < 5:
            results['warnings'].append("Database pool size may be too small")
        elif pool_size > 50:
            results['warnings'].append("Database pool size may be too large")
        
        # Check cache settings
        cache_type = self.config_manager.get('CACHE_TYPE')
        if cache_type == 'simple' and self.config_manager.get('FLASK_ENV') == 'production':
            results['warnings'].append("Using simple cache in production - consider Redis")
        
        # Check rate limiting
        if self.config_manager.get('RATELIMIT_ENABLED') != 'true':
            results['warnings'].append("Rate limiting not enabled")
        
        return results
    
    def _is_weak_secret(self, secret: str) -> bool:
        """Check if a secret is weak"""
        if not secret:
            return True
        
        # Check for common weak patterns
        weak_patterns = [
            'dev-', 'test-', 'default-', 'password', 'secret', 'key',
            '123456', 'abcdef', 'changeme', 'temporary'
        ]
        
        secret_lower = secret.lower()
        for pattern in weak_patterns:
            if pattern in secret_lower:
                return True
        
        # Check entropy (simplified)
        if len(set(secret)) < len(secret) * 0.5:
            return True
        
        return False
    
    def _determine_overall_status(self, results: Dict[str, Any]):
        """Determine overall validation status"""
        for section, section_results in results['validation_results'].items():
            if section_results.get('status') == 'FAIL':
                results['overall_status'] = 'FAIL'
                break
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Security recommendations
        if results['validation_results']['security']['status'] == 'FAIL':
            recommendations.append("Fix security issues before deployment")
        
        if any('weak' in str(check).lower() for check in results['validation_results']['security']['checks'].values()):
            recommendations.append("Consider rotating weak secrets")
        
        # Environment recommendations
        if results['validation_results']['environment']['warnings']:
            recommendations.append("Review environment-specific warnings")
        
        # External service recommendations
        if results['validation_results']['external_services']['warnings']:
            recommendations.append("Configure missing external service credentials")
        
        # Performance recommendations
        if results['validation_results']['performance']['warnings']:
            recommendations.append("Review performance configuration for optimization")
        
        # General recommendations
        if self.config_manager.get('FLASK_ENV') == 'production':
            recommendations.append("Ensure all production secrets are properly secured")
            recommendations.append("Set up monitoring and alerting for production")
            recommendations.append("Regularly rotate secrets (every 90 days)")
        
        return recommendations
    
    def generate_secrets(self) -> Dict[str, str]:
        """Generate secure secrets for missing configuration"""
        logger.info("Generating secure secrets...")
        
        secrets = {}
        
        # Generate Flask secret key
        if not self.config_manager.get('SECRET_KEY'):
            secrets['SECRET_KEY'] = secrets.token_hex(32)
        
        # Generate encryption keys
        if not self.config_manager.get('FIELD_ENCRYPTION_KEY'):
            secrets['FIELD_ENCRYPTION_KEY'] = secrets.token_hex(32)
        
        if not self.config_manager.get('DJANGO_SECRET_KEY'):
            secrets['DJANGO_SECRET_KEY'] = secrets.token_urlsafe(50)
        
        # Generate configuration encryption key
        if not os.getenv('CONFIG_ENCRYPTION_KEY'):
            secrets['CONFIG_ENCRYPTION_KEY'] = secrets.token_urlsafe(32)
        
        return secrets
    
    def print_report(self, results: Dict[str, Any]):
        """Print validation report"""
        print("\n" + "="*80)
        print("MINGUS APPLICATION - CONFIGURATION VALIDATION REPORT")
        print("="*80)
        
        # Overall status
        status_color = "🟢" if results['overall_status'] == 'PASS' else "🔴"
        print(f"\n{status_color} Overall Status: {results['overall_status']}")
        
        # Environment
        env = results['config_summary'].get('FLASK_ENV', 'unknown')
        print(f"🌍 Environment: {env}")
        
        # Validation results by section
        print("\n📋 Validation Results:")
        for section, section_results in results['validation_results'].items():
            status = section_results.get('status', 'UNKNOWN')
            status_icon = "🟢" if status == 'PASS' else "🔴"
            print(f"  {status_icon} {section.title()}: {status}")
            
            if self.verbose:
                if section_results.get('issues'):
                    for issue in section_results['issues']:
                        print(f"    ❌ {issue}")
                
                if section_results.get('warnings'):
                    for warning in section_results['warnings']:
                        print(f"    ⚠️  {warning}")
        
        # Security issues
        if results['security_issues']:
            print("\n🔒 Security Issues:")
            for issue in results['security_issues']:
                print(f"  ❌ {issue}")
        
        # Recommendations
        if results['recommendations']:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Configuration summary
        if self.verbose:
            print("\n📊 Configuration Summary:")
            for key, value in results['config_summary'].items():
                if key in ['SECRET_KEY', 'FIELD_ENCRYPTION_KEY', 'DJANGO_SECRET_KEY']:
                    print(f"  {key}: [REDACTED]")
                else:
                    print(f"  {key}: {value}")
        
        # Audit log
        if self.verbose and results['audit_log']:
            print("\n📝 Recent Configuration Access:")
            for entry in results['audit_log'][-5:]:  # Show last 5 entries
                print(f"  {entry['timestamp']} - {entry['action']} - {entry['key']} ({entry['security_level']})")
        
        print("\n" + "="*80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Validate MINGUS application configuration')
    parser.add_argument('--env-file', default='.env', help='Path to environment file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--fix', action='store_true', help='Generate missing secrets')
    parser.add_argument('--output', help='Output results to JSON file')
    
    args = parser.parse_args()
    
    try:
        # Initialize validator
        validator = ConfigValidator(args.env_file, args.verbose)
        
        # Run validation
        results = validator.validate_all()
        
        # Print report
        validator.print_report(results)
        
        # Generate secrets if requested
        if args.fix:
            secrets = validator.generate_secrets()
            if secrets:
                print("\n🔧 Generated Secrets:")
                for key, value in secrets.items():
                    print(f"  {key}={value}")
                print("\nAdd these to your .env file and restart the application.")
        
        # Output to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to {args.output}")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_status'] == 'PASS' else 1)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 