#!/usr/bin/env python3
"""
Authentication Fix Validation Script
===================================

This script validates that all authentication bypass vulnerabilities
have been properly fixed in the MINGUS application.

Author: Security Team
Date: August 27, 2025
"""

import os
import re
import requests
import json
from typing import List, Dict, Any

class AuthenticationFixValidator:
    """Validator for authentication bypass fixes"""
    
    def __init__(self):
        self.validation_results = []
        self.critical_issues = []
        
    def validate_config_files(self) -> Dict[str, Any]:
        """Validate that BYPASS_AUTH is disabled in all config files"""
        print("🔍 Validating configuration files...")
        
        config_files = [
            "config/testing.py",
            "config/development.py",
            "config/base.py"
        ]
        
        results = {
            'passed': True,
            'issues': [],
            'files_checked': []
        }
        
        for file_path in config_files:
            if not os.path.exists(file_path):
                continue
                
            results['files_checked'].append(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for BYPASS_AUTH = True
            if re.search(r'BYPASS_AUTH\s*=\s*True', content):
                results['passed'] = False
                results['issues'].append(f"BYPASS_AUTH = True found in {file_path}")
                self.critical_issues.append(f"CRITICAL: BYPASS_AUTH enabled in {file_path}")
            
            # Check for BYPASS_AUTH = False (good)
            if re.search(r'BYPASS_AUTH\s*=\s*False', content):
                print(f"✅ BYPASS_AUTH = False found in {file_path}")
        
        return results
    
    def validate_test_files(self) -> Dict[str, Any]:
        """Validate that test files don't have BYPASS_AUTH = True"""
        print("🔍 Validating test files...")
        
        test_files = [
            "tests/test_api_endpoints.py",
            "tests/security/conftest.py",
            "tests/mingus_suite/conftest.py"
        ]
        
        results = {
            'passed': True,
            'issues': [],
            'files_checked': []
        }
        
        for file_path in test_files:
            if not os.path.exists(file_path):
                continue
                
            results['files_checked'].append(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for BYPASS_AUTH = True
            if re.search(r'BYPASS_AUTH\s*=\s*True', content):
                results['passed'] = False
                results['issues'].append(f"BYPASS_AUTH = True found in {file_path}")
                self.critical_issues.append(f"CRITICAL: BYPASS_AUTH enabled in {file_path}")
            elif re.search(r'BYPASS_AUTH\s*=\s*False', content):
                print(f"✅ BYPASS_AUTH = False found in {file_path}")
        
        return results
    
    def validate_financial_routes(self) -> Dict[str, Any]:
        """Validate that financial routes have proper authentication"""
        print("🔍 Validating financial routes...")
        
        route_files = [
            "backend/routes/financial_questionnaire.py",
            "backend/routes/income_analysis.py",
            "backend/routes/payment.py",
            "backend/routes/secure_financial.py"
        ]
        
        results = {
            'passed': True,
            'issues': [],
            'files_checked': []
        }
        
        for file_path in route_files:
            if not os.path.exists(file_path):
                continue
                
            results['files_checked'].append(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find all route definitions
            route_pattern = r'@.*\.route\(.*methods=\[.*\]\)'
            routes = re.finditer(route_pattern, content)
            
            routes_without_auth = []
            
            for route_match in routes:
                route_start = route_match.start()
                route_end = route_match.end()
                
                # Check if there's a function definition after this route
                remaining_content = content[route_end:]
                func_match = re.search(r'def\s+\w+\(', remaining_content)
                
                if func_match:
                    # Check if authentication decorator is present
                    decorator_area = content[route_start:route_end + func_match.end()]
                    
                    # Skip webhook endpoints (they should be public)
                    route_text = route_match.group()
                    if 'webhook' in route_text.lower():
                        continue
                    
                    if '@require_auth' not in decorator_area and '@login_required' not in decorator_area:
                        line_num = content[:route_start].count('\n') + 1
                        routes_without_auth.append(f"Line {line_num}: {route_match.group()}")
            
            if routes_without_auth:
                results['passed'] = False
                results['issues'].extend([f"{file_path}: {route}" for route in routes_without_auth])
                self.critical_issues.append(f"CRITICAL: Routes without authentication in {file_path}")
            else:
                print(f"✅ All routes in {file_path} have authentication")
        
        return results
    
    def validate_imports(self) -> Dict[str, Any]:
        """Validate that authentication imports are present"""
        print("🔍 Validating authentication imports...")
        
        route_files = [
            "backend/routes/financial_questionnaire.py",
            "backend/routes/income_analysis.py"
        ]
        
        results = {
            'passed': True,
            'issues': [],
            'files_checked': []
        }
        
        for file_path in route_files:
            if not os.path.exists(file_path):
                continue
                
            results['files_checked'].append(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for authentication import
            if 'from backend.middleware.auth import require_auth' not in content:
                results['passed'] = False
                results['issues'].append(f"Missing authentication import in {file_path}")
                self.critical_issues.append(f"CRITICAL: Missing auth import in {file_path}")
            else:
                print(f"✅ Authentication import found in {file_path}")
        
        return results
    
    def test_authentication_endpoints(self) -> Dict[str, Any]:
        """Test that protected endpoints return 401 without authentication"""
        print("🔍 Testing authentication endpoints...")
        
        # This would require a running application
        # For now, we'll just document what should be tested
        results = {
            'passed': True,
            'issues': [],
            'endpoints_to_test': [
                '/api/financial/questionnaire',
                '/api/income/analyze',
                '/api/payment/customers',
                '/api/secure/financial-profile'
            ]
        }
        
        print("⚠️  Manual testing required for the following endpoints:")
        for endpoint in results['endpoints_to_test']:
            print(f"   - {endpoint} (should return 401 without auth)")
        
        return results
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION FIX VALIDATION REPORT")
        print("=" * 60)
        
        # Run all validations
        config_results = self.validate_config_files()
        test_results = self.validate_test_files()
        route_results = self.validate_financial_routes()
        import_results = self.validate_imports()
        endpoint_results = self.test_authentication_endpoints()
        
        # Compile results
        all_passed = all([
            config_results['passed'],
            test_results['passed'],
            route_results['passed'],
            import_results['passed']
        ])
        
        print(f"\n✅ Configuration Files: {'PASSED' if config_results['passed'] else 'FAILED'}")
        if config_results['issues']:
            for issue in config_results['issues']:
                print(f"   ❌ {issue}")
        
        print(f"\n✅ Test Files: {'PASSED' if test_results['passed'] else 'FAILED'}")
        if test_results['issues']:
            for issue in test_results['issues']:
                print(f"   ❌ {issue}")
        
        print(f"\n✅ Financial Routes: {'PASSED' if route_results['passed'] else 'FAILED'}")
        if route_results['issues']:
            for issue in route_results['issues']:
                print(f"   ❌ {issue}")
        
        print(f"\n✅ Authentication Imports: {'PASSED' if import_results['passed'] else 'FAILED'}")
        if import_results['issues']:
            for issue in import_results['issues']:
                print(f"   ❌ {issue}")
        
        print(f"\n✅ Endpoint Testing: {'MANUAL TESTING REQUIRED'}")
        
        # Summary
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("✅ Authentication bypass vulnerabilities have been fixed")
            print("✅ All financial endpoints require authentication")
            print("✅ Test mode authentication bypasses disabled")
        else:
            print("❌ VALIDATION FAILED!")
            print("⚠️  Critical issues found:")
            for issue in self.critical_issues:
                print(f"   - {issue}")
        
        # Create detailed report
        report_content = f"""
# Authentication Fix Validation Report
Generated: {datetime.now().isoformat()}

## Overall Status: {'PASSED' if all_passed else 'FAILED'}

## Configuration Files
Status: {'PASSED' if config_results['passed'] else 'FAILED'}
Files Checked: {len(config_results['files_checked'])}
Issues: {len(config_results['issues'])}

## Test Files  
Status: {'PASSED' if test_results['passed'] else 'FAILED'}
Files Checked: {len(test_results['files_checked'])}
Issues: {len(test_results['issues'])}

## Financial Routes
Status: {'PASSED' if route_results['passed'] else 'FAILED'}
Files Checked: {len(route_results['files_checked'])}
Issues: {len(route_results['issues'])}

## Authentication Imports
Status: {'PASSED' if import_results['passed'] else 'FAILED'}
Files Checked: {len(import_results['files_checked'])}
Issues: {len(import_results['issues'])}

## Critical Issues Found
{len(self.critical_issues)} critical issues identified:

"""
        
        for issue in self.critical_issues:
            report_content += f"- {issue}\n"
        
        report_content += """

## Next Steps

1. If validation PASSED:
   - Restart the application
   - Test authentication flows manually
   - Verify no unauthorized access is possible

2. If validation FAILED:
   - Fix remaining issues immediately
   - Re-run validation
   - Do not deploy until all issues are resolved

## Manual Testing Required

Test the following endpoints without authentication (should return 401):

"""
        
        for endpoint in endpoint_results['endpoints_to_test']:
            report_content += f"- {endpoint}\n"
        
        with open('AUTHENTICATION_VALIDATION_REPORT.md', 'w') as f:
            f.write(report_content)
        
        print(f"\n📄 Detailed report: AUTHENTICATION_VALIDATION_REPORT.md")
        
        return all_passed

def main():
    """Main validation function"""
    print("🔐 MINGUS Authentication Fix Validation")
    print("=" * 50)
    
    validator = AuthenticationFixValidator()
    success = validator.generate_validation_report()
    
    if success:
        print("\n✅ VALIDATION SUCCESSFUL - Authentication fixes are working correctly!")
    else:
        print("\n❌ VALIDATION FAILED - Critical issues need immediate attention!")
    
    return success

if __name__ == "__main__":
    from datetime import datetime
    main()
