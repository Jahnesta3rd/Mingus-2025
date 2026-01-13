#!/usr/bin/env python3
"""
Comprehensive Data Encryption and Protection Verification Script
Checks all encryption implementations, password hashing, and data protection measures
"""

import os
import sys
import json
import hashlib
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Color codes for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class EncryptionVerifier:
    """Verify encryption and data protection implementations"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        self.critical_issues = []
        
    def log_issue(self, severity: str, category: str, issue: str, 
                  location: str, recommendation: str):
        """Log a security issue"""
        issue_data = {
            'severity': severity,
            'category': category,
            'issue': issue,
            'location': location,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
        
        if severity == 'CRITICAL':
            self.critical_issues.append(issue_data)
        elif severity == 'HIGH':
            self.issues.append(issue_data)
        elif severity == 'MEDIUM':
            self.warnings.append(issue_data)
        else:
            self.warnings.append(issue_data)
    
    def log_pass(self, category: str, message: str, location: str = ''):
        """Log a passed check"""
        self.passed.append({
            'category': category,
            'message': message,
            'location': location
        })
    
    def check_encryption_service(self):
        """Check backend/utils/encryption.py"""
        print(f"\n{Colors.BOLD}🔐 Checking Encryption Service...{Colors.RESET}")
        
        encryption_file = Path('backend/utils/encryption.py')
        if not encryption_file.exists():
            self.log_issue('HIGH', 'Encryption', 
                          'Encryption service file not found',
                          'backend/utils/encryption.py',
                          'Create proper encryption service with real encryption')
            return
        
        content = encryption_file.read_text()
        
        # Check for base64-only "encryption" (CRITICAL)
        if 'base64.b64encode' in content and 'Fernet' not in content and 'AES' not in content:
            self.log_issue('CRITICAL', 'Encryption',
                          'Encryption service uses base64 encoding only - NOT real encryption!',
                          'backend/utils/encryption.py',
                          'Replace with proper encryption (Fernet/AES-256). Base64 is encoding, not encryption.')
        
        # Check for proper encryption libraries
        if 'cryptography' in content or 'Fernet' in content:
            self.log_pass('Encryption', 'Uses cryptography library (Fernet/AES)')
        else:
            self.log_issue('HIGH', 'Encryption',
                          'No proper encryption library detected',
                          'backend/utils/encryption.py',
                          'Use cryptography library with Fernet or AES-256-GCM')
        
        # Check for key management
        if 'ENCRYPTION_KEY' in content or 'encryption_key' in content:
            self.log_pass('Key Management', 'Encryption key configuration found')
        else:
            self.log_issue('MEDIUM', 'Key Management',
                          'No encryption key management detected',
                          'backend/utils/encryption.py',
                          'Implement secure key management from environment variables')
    
    def check_password_hashing(self):
        """Check password hashing implementation"""
        print(f"\n{Colors.BOLD}🔑 Checking Password Hashing...{Colors.RESET}")
        
        # Check requirements.txt for proper password hashing libraries
        requirements_file = Path('requirements.txt')
        has_bcrypt = False
        has_argon2 = False
        
        if requirements_file.exists():
            content = requirements_file.read_text()
            has_bcrypt = 'bcrypt' in content.lower()
            has_argon2 = 'argon2' in content.lower()
        
        if not has_bcrypt and not has_argon2:
            self.log_issue('HIGH', 'Password Security',
                          'No secure password hashing library (bcrypt/argon2) in requirements',
                          'requirements.txt',
                          'Add bcrypt or argon2-cffi for secure password hashing')
        
        # Search for password hashing in codebase
        import subprocess
        try:
            result = subprocess.run(
                ['grep', '-r', 'hashlib.sha256.*password', '--include=*.py', '.'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout:
                self.log_issue('HIGH', 'Password Security',
                              'SHA256 used directly for password hashing (insecure)',
                              'Multiple files',
                              'Replace with bcrypt or argon2. SHA256 is too fast for password hashing.')
        except:
            pass
        
        # Check for werkzeug password hashing
        try:
            result = subprocess.run(
                ['grep', '-r', 'generate_password_hash', '--include=*.py', '.'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout:
                self.log_pass('Password Security', 'Werkzeug password hashing found (acceptable)')
        except:
            pass
    
    def check_housing_encryption(self):
        """Check housing security encryption"""
        print(f"\n{Colors.BOLD}🏠 Checking Housing Data Encryption...{Colors.RESET}")
        
        housing_security = Path('config/housing_security_config.py')
        if not housing_security.exists():
            self.log_issue('MEDIUM', 'Data Protection',
                          'Housing security config not found',
                          'config/housing_security_config.py',
                          'Implement encryption for housing data')
            return
        
        content = housing_security.read_text()
        
        # Check for Fernet encryption
        if 'Fernet' in content:
            self.log_pass('Encryption', 'Housing data uses Fernet encryption (secure)')
        else:
            self.log_issue('HIGH', 'Data Protection',
                          'Housing data encryption not using Fernet',
                          'config/housing_security_config.py',
                          'Use Fernet for symmetric encryption')
        
        # Check for key management
        if 'HOUSING_ENCRYPTION_KEY' in content:
            self.log_pass('Key Management', 'Housing encryption key from environment')
        else:
            self.log_issue('MEDIUM', 'Key Management',
                          'Housing encryption key not from environment',
                          'config/housing_security_config.py',
                          'Store encryption keys in environment variables')
        
        # Check for sensitive field encryption
        if 'encrypt_sensitive_data' in content:
            self.log_pass('Data Protection', 'Sensitive data encryption function exists')
        else:
            self.log_issue('MEDIUM', 'Data Protection',
                          'No sensitive data encryption function',
                          'config/housing_security_config.py',
                          'Implement encrypt_sensitive_data function')
    
    def check_security_config(self):
        """Check security configuration"""
        print(f"\n{Colors.BOLD}⚙️  Checking Security Configuration...{Colors.RESET}")
        
        security_config = Path('backend/config/security.py')
        if not security_config.exists():
            self.log_issue('HIGH', 'Configuration',
                          'Security config file not found',
                          'backend/config/security.py',
                          'Create security configuration file')
            return
        
        content = security_config.read_text()
        
        # Check for encryption key configuration
        if 'ENCRYPTION_KEY' in content:
            self.log_pass('Configuration', 'Encryption key configured')
        else:
            self.log_issue('MEDIUM', 'Configuration',
                          'No encryption key in security config',
                          'backend/config/security.py',
                          'Add ENCRYPTION_KEY configuration')
        
        # Check for session security
        if 'SESSION_COOKIE_SECURE' in content:
            self.log_pass('Session Security', 'Session cookie security configured')
        else:
            self.log_issue('MEDIUM', 'Session Security',
                          'Session cookie security not configured',
                          'backend/config/security.py',
                          'Configure secure session cookies')
        
        # Check for CSRF protection
        if 'CSRF' in content or 'csrf' in content:
            self.log_pass('CSRF Protection', 'CSRF protection configured')
        else:
            self.log_issue('MEDIUM', 'CSRF Protection',
                          'CSRF protection not configured',
                          'backend/config/security.py',
                          'Implement CSRF token protection')
    
    def check_database_encryption(self):
        """Check database encryption implementation"""
        print(f"\n{Colors.BOLD}💾 Checking Database Encryption...{Colors.RESET}")
        
        migrations_dir = Path('migrations')
        if not migrations_dir.exists():
            self.log_issue('MEDIUM', 'Database Security',
                          'Migrations directory not found',
                          'migrations/',
                          'Set up database migrations for encryption')
            return
        
        # Check for encryption migration files
        encryption_migrations = list(migrations_dir.glob('*encryption*.py'))
        encryption_migrations.extend(list(migrations_dir.glob('*002*.py')))
        
        if encryption_migrations:
            self.log_pass('Database Security', f'Found {len(encryption_migrations)} encryption migration(s)')
        else:
            self.log_issue('MEDIUM', 'Database Security',
                          'No database encryption migrations found',
                          'migrations/',
                          'Create database encryption migration (002_add_encryption_fields.py)')
        
        # Check for security migration README
        security_readme = migrations_dir / 'SECURITY_MIGRATION_README 2.md'
        if security_readme.exists():
            self.log_pass('Database Security', 'Security migration documentation exists')
        else:
            self.log_issue('LOW', 'Documentation',
                          'Security migration documentation not found',
                          'migrations/',
                          'Document database encryption strategy')
    
    def check_environment_variables(self):
        """Check environment variable configuration"""
        print(f"\n{Colors.BOLD}🔧 Checking Environment Configuration...{Colors.RESET}")
        
        env_example = Path('env.example')
        if not env_example.exists():
            self.log_issue('MEDIUM', 'Configuration',
                          'env.example file not found',
                          'env.example',
                          'Create env.example with required security variables')
            return
        
        content = env_example.read_text()
        
        # Check for encryption key
        if 'ENCRYPTION_KEY' in content:
            self.log_pass('Configuration', 'ENCRYPTION_KEY in env.example')
        else:
            self.log_issue('MEDIUM', 'Configuration',
                          'ENCRYPTION_KEY not in env.example',
                          'env.example',
                          'Add ENCRYPTION_KEY to environment configuration')
        
        # Check for secret key
        if 'SECRET_KEY' in content:
            self.log_pass('Configuration', 'SECRET_KEY in env.example')
        else:
            self.log_issue('HIGH', 'Configuration',
                          'SECRET_KEY not in env.example',
                          'env.example',
                          'Add SECRET_KEY for Flask sessions')
        
        # Check for JWT secret
        if 'JWT_SECRET_KEY' in content:
            self.log_pass('Configuration', 'JWT_SECRET_KEY in env.example')
        else:
            self.log_issue('MEDIUM', 'Configuration',
                          'JWT_SECRET_KEY not in env.example',
                          'env.example',
                          'Add JWT_SECRET_KEY for token signing')
    
    def check_data_in_transit(self):
        """Check data protection in transit"""
        print(f"\n{Colors.BOLD}🌐 Checking Data in Transit Protection...{Colors.RESET}")
        
        app_file = Path('app.py')
        if app_file.exists():
            content = app_file.read_text()
            
            # Check for HTTPS enforcement
            if 'SESSION_COOKIE_SECURE' in content or 'secure' in content.lower():
                self.log_pass('Transport Security', 'Session security configured')
            else:
                self.log_issue('MEDIUM', 'Transport Security',
                              'Session cookie security not enforced',
                              'app.py',
                              'Enable SESSION_COOKIE_SECURE for HTTPS')
        
        # Check for CORS configuration
        security_config = Path('backend/config/security.py')
        if security_config.exists():
            content = security_config.read_text()
            if 'CORS' in content:
                self.log_pass('Transport Security', 'CORS configuration found')
            else:
                self.log_issue('LOW', 'Transport Security',
                              'CORS not configured',
                              'backend/config/security.py',
                              'Configure CORS for API security')
    
    def check_sensitive_data_logging(self):
        """Check for sensitive data in logs"""
        print(f"\n{Colors.BOLD}📝 Checking Sensitive Data Logging...{Colors.RESET}")
        
        # Check security config for logging settings
        security_config = Path('backend/config/security.py')
        if security_config.exists():
            content = security_config.read_text()
            if 'LOG_SENSITIVE_DATA' in content:
                self.log_pass('Logging Security', 'Sensitive data logging flag configured')
            else:
                self.log_issue('MEDIUM', 'Logging Security',
                              'No sensitive data logging flag',
                              'backend/config/security.py',
                              'Add LOG_SENSITIVE_DATA flag to prevent logging secrets')
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 ENCRYPTION & DATA PROTECTION VERIFICATION REPORT{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        # Summary
        total_checks = len(self.passed) + len(self.issues) + len(self.warnings) + len(self.critical_issues)
        passed_count = len(self.passed)
        issue_count = len(self.issues)
        warning_count = len(self.warnings)
        critical_count = len(self.critical_issues)
        
        print(f"{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  {Colors.GREEN}✅ Passed: {passed_count}{Colors.RESET}")
        print(f"  {Colors.RED}❌ Critical Issues: {critical_count}{Colors.RESET}")
        print(f"  {Colors.YELLOW}⚠️  High Priority Issues: {issue_count}{Colors.RESET}")
        print(f"  {Colors.BLUE}ℹ️  Warnings: {warning_count}{Colors.RESET}")
        print(f"  Total Checks: {total_checks}\n")
        
        # Critical Issues
        if self.critical_issues:
            print(f"\n{Colors.RED}{Colors.BOLD}🚨 CRITICAL ISSUES:{Colors.RESET}\n")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"{Colors.RED}{i}. {issue['category']}: {issue['issue']}{Colors.RESET}")
                print(f"   Location: {issue['location']}")
                print(f"   Recommendation: {issue['recommendation']}\n")
        
        # High Priority Issues
        if self.issues:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  HIGH PRIORITY ISSUES:{Colors.RESET}\n")
            for i, issue in enumerate(self.issues, 1):
                print(f"{Colors.YELLOW}{i}. {issue['category']}: {issue['issue']}{Colors.RESET}")
                print(f"   Location: {issue['location']}")
                print(f"   Recommendation: {issue['recommendation']}\n")
        
        # Warnings
        if self.warnings:
            print(f"\n{Colors.BLUE}{Colors.BOLD}ℹ️  WARNINGS:{Colors.RESET}\n")
            for i, warning in enumerate(self.warnings[:10], 1):  # Limit to 10
                print(f"{Colors.BLUE}{i}. {warning['category']}: {warning['issue']}{Colors.RESET}")
                print(f"   Location: {warning['location']}\n")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more warnings\n")
        
        # Passed Checks
        if self.passed:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ PASSED CHECKS:{Colors.RESET}\n")
            for check in self.passed[:15]:  # Limit to 15
                print(f"{Colors.GREEN}✓ {check['category']}: {check['message']}{Colors.RESET}")
            if len(self.passed) > 15:
                print(f"   ... and {len(self.passed) - 15} more passed checks\n")
        
        # Recommendations
        print(f"\n{Colors.BOLD}📋 RECOMMENDATIONS:{Colors.RESET}\n")
        
        if critical_count > 0:
            print(f"{Colors.RED}1. IMMEDIATE ACTION REQUIRED:{Colors.RESET}")
            print("   Fix all CRITICAL issues before deploying to production.\n")
        
        if issue_count > 0:
            print(f"{Colors.YELLOW}2. HIGH PRIORITY:{Colors.RESET}")
            print("   Address high priority issues to improve security posture.\n")
        
        print("3. Best Practices:")
        print("   - Use bcrypt or argon2 for password hashing")
        print("   - Implement Fernet or AES-256-GCM for data encryption")
        print("   - Store encryption keys in environment variables or key management service")
        print("   - Enable HTTPS and secure session cookies in production")
        print("   - Never log sensitive data (passwords, tokens, PII)")
        print("   - Implement database encryption for sensitive data at rest")
        print("   - Use proper key rotation strategies")
        
        # Generate JSON report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_checks': total_checks,
                'passed': passed_count,
                'critical_issues': critical_count,
                'high_issues': issue_count,
                'warnings': warning_count
            },
            'critical_issues': self.critical_issues,
            'high_issues': self.issues,
            'warnings': self.warnings,
            'passed_checks': self.passed
        }
        
        return report
    
    def run_all_checks(self):
        """Run all verification checks"""
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("="*70)
        print("  DATA ENCRYPTION & PROTECTION VERIFICATION")
        print("="*70)
        print(f"{Colors.RESET}\n")
        
        self.check_encryption_service()
        self.check_password_hashing()
        self.check_housing_encryption()
        self.check_security_config()
        self.check_database_encryption()
        self.check_environment_variables()
        self.check_data_in_transit()
        self.check_sensitive_data_logging()
        
        return self.generate_report()

def main():
    """Main execution"""
    verifier = EncryptionVerifier()
    report = verifier.run_all_checks()
    
    # Save report to file
    report_file = Path('encryption_protection_verification_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{Colors.GREEN}✅ Report saved to: {report_file}{Colors.RESET}\n")
    
    # Exit with error code if critical issues found
    if verifier.critical_issues:
        print(f"{Colors.RED}❌ CRITICAL ISSUES FOUND - Please fix before production deployment{Colors.RESET}\n")
        sys.exit(1)
    elif verifier.issues:
        print(f"{Colors.YELLOW}⚠️  High priority issues found - Review and address{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.GREEN}✅ All critical checks passed!{Colors.RESET}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
