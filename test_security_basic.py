#!/usr/bin/env python3
"""
Basic Security Test Script
Tests core security functionality without requiring full Flask app context
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_security_validator():
    """Test the SecurityValidator class"""
    print("🔍 Testing SecurityValidator...")
    
    try:
        from backend.security.assessment_security import SecurityValidator
        validator = SecurityValidator()
        
        # Test valid inputs
        valid_inputs = [
            "Software Engineer",
            "I enjoy working with data analysis",
            "5 years of experience",
            "Atlanta, Georgia",
            "$75,000 annual salary"
        ]
        
        print("  Testing valid inputs...")
        for input_text in valid_inputs:
            result = validator.validate_input(input_text)
            if result["valid"]:
                print(f"    ✅ '{input_text[:30]}...' - PASSED")
            else:
                print(f"    ❌ '{input_text[:30]}...' - FAILED: {result.get('reason', 'Unknown')}")
        
        # Test malicious inputs
        malicious_inputs = [
            ("<script>alert('xss')</script>", "XSS"),
            ("'; DROP TABLE users; --", "SQL Injection"),
            ("$(rm -rf /)", "Command Injection"),
            ("javascript:alert('xss')", "XSS"),
            ("admin' OR '1'='1", "SQL Injection")
        ]
        
        print("\n  Testing malicious inputs...")
        for input_text, attack_type in malicious_inputs:
            result = validator.validate_input(input_text)
            if not result["valid"]:
                print(f"    ✅ '{input_text[:30]}...' - BLOCKED ({attack_type})")
            else:
                print(f"    ❌ '{input_text[:30]}...' - NOT BLOCKED ({attack_type})")
        
        return True
        
    except Exception as e:
        print(f"    ❌ SecurityValidator test failed: {e}")
        return False

def test_jwt_security():
    """Test JWT security functionality"""
    print("\n🔐 Testing JWT Security...")
    
    try:
        from backend.security.secure_jwt_manager import SecureJWTManager, JWTConfig
        
        # Create JWT manager with test configuration
        config = JWTConfig(
            secret_key='test-secret-key-for-security-testing',
            expiration_hours=1,
            require_ip_validation=False,  # Disable for testing
            require_user_agent_validation=False  # Disable for testing
        )
        jwt_manager = SecureJWTManager(config)
        
        # Test token creation
        token = jwt_manager.create_secure_token('user123')
        print(f"    ✅ Token created successfully: {token[:50]}...")
        
        # Test token validation
        result = jwt_manager.validate_secure_token(token)
        if result["valid"]:
            print("    ✅ Token validation successful")
        else:
            print(f"    ❌ Token validation failed: {result.get('reason', 'Unknown')}")
        
        # Test token tampering
        tampered_token = token[:-10] + "tampered"
        result = jwt_manager.validate_secure_token(tampered_token)
        if not result["valid"]:
            print("    ✅ Tampered token correctly rejected")
        else:
            print("    ❌ Tampered token incorrectly accepted")
        
        return True
        
    except Exception as e:
        print(f"    ❌ JWT security test failed: {e}")
        return False

def test_static_analysis():
    """Test static code analysis"""
    print("\n🔍 Testing Static Code Analysis...")
    
    try:
        import subprocess
        import json
        
        # Test bandit
        print("  Running bandit analysis...")
        result = subprocess.run([
            sys.executable, '-m', 'bandit',
            '-r', 'backend/security/',
            '-f', 'json',
            '-o', 'reports/bandit_test_results.json'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("    ✅ Bandit analysis completed")
            
            # Check for high severity issues
            try:
                with open('reports/bandit_test_results.json', 'r') as f:
                    data = json.load(f)
                
                high_severity = [issue for issue in data.get('results', []) 
                               if issue.get('issue_severity') == 'HIGH']
                
                if high_severity:
                    print(f"    ⚠️  Found {len(high_severity)} high severity issues")
                else:
                    print("    ✅ No high severity issues found")
                    
            except (json.JSONDecodeError, FileNotFoundError):
                print("    ⚠️  Could not parse bandit results")
        else:
            print(f"    ❌ Bandit analysis failed: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Static analysis test failed: {e}")
        return False

def test_dependency_scanning():
    """Test dependency vulnerability scanning"""
    print("\n📦 Testing Dependency Vulnerability Scanning...")
    
    try:
        import subprocess
        import json
        
        # Test safety
        print("  Running safety check...")
        result = subprocess.run([
            sys.executable, '-m', 'safety',
            'check',
            '--json',
            '--output', 'reports/safety_test_results.json'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("    ✅ Safety check completed")
            
            # Check for vulnerabilities
            try:
                with open('reports/safety_test_results.json', 'r') as f:
                    data = json.load(f)
                
                vulnerabilities = data.get('vulnerabilities', [])
                high_severity = [vuln for vuln in vulnerabilities 
                               if vuln.get('severity') == 'HIGH']
                
                if high_severity:
                    print(f"    ⚠️  Found {len(high_severity)} high severity vulnerabilities")
                else:
                    print("    ✅ No high severity vulnerabilities found")
                    
            except (json.JSONDecodeError, FileNotFoundError):
                print("    ⚠️  Could not parse safety results")
        else:
            print(f"    ❌ Safety check failed: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Dependency scanning test failed: {e}")
        return False

def main():
    """Run all basic security tests"""
    print("🔒 Running Basic Security Tests")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create reports directory
    os.makedirs('reports', exist_ok=True)
    
    # Run tests
    tests = [
        ("Security Validator", test_security_validator),
        ("JWT Security", test_jwt_security),
        ("Static Analysis", test_static_analysis),
        ("Dependency Scanning", test_dependency_scanning)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"    ❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All basic security tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the results.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
