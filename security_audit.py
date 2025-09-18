#!/usr/bin/env python3
"""
Comprehensive Security Audit for Mingus Landing Page and Assessment System
Identifies security vulnerabilities and provides remediation recommendations
"""

import re
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class SecurityAuditor:
    def __init__(self):
        self.vulnerabilities = []
        self.recommendations = []
        self.critical_issues = []
        self.high_issues = []
        self.medium_issues = []
        self.low_issues = []
    
    def log_vulnerability(self, category: str, severity: str, file: str, line: int, 
                         issue: str, recommendation: str, cwe: str = None):
        """Log a security vulnerability"""
        vuln = {
            'category': category,
            'severity': severity,
            'file': file,
            'line': line,
            'issue': issue,
            'recommendation': recommendation,
            'cwe': cwe,
            'timestamp': datetime.now().isoformat()
        }
        
        self.vulnerabilities.append(vuln)
        
        if severity == 'CRITICAL':
            self.critical_issues.append(vuln)
        elif severity == 'HIGH':
            self.high_issues.append(vuln)
        elif severity == 'MEDIUM':
            self.medium_issues.append(vuln)
        else:
            self.low_issues.append(vuln)
    
    def audit_frontend_components(self):
        """Audit frontend components for security issues"""
        print("🔍 Auditing Frontend Components...")
        
        # Check AssessmentModal.tsx
        self.audit_assessment_modal()
        
        # Check LandingPage.tsx
        self.audit_landing_page()
        
        # Check general frontend patterns
        self.audit_frontend_patterns()
    
    def audit_assessment_modal(self):
        """Audit AssessmentModal component"""
        file_path = "frontend/src/components/AssessmentModal.tsx"
        
        if not os.path.exists(file_path):
            return
        
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for XSS vulnerabilities
        if 'dangerouslySetInnerHTML' in content:
            self.log_vulnerability(
                'XSS', 'HIGH', file_path, 0,
                'Use of dangerouslySetInnerHTML detected',
                'Avoid dangerouslySetInnerHTML. Use proper React patterns for dynamic content.',
                'CWE-79'
            )
        
        # Check for unsanitized user input
        if 'innerHTML' in content:
            self.log_vulnerability(
                'XSS', 'HIGH', file_path, 0,
                'Direct innerHTML manipulation detected',
                'Use textContent or React\'s built-in escaping instead of innerHTML.',
                'CWE-79'
            )
        
        # Check for eval usage
        if 'eval(' in content:
            self.log_vulnerability(
                'Code Injection', 'CRITICAL', file_path, 0,
                'Use of eval() function detected',
                'Never use eval(). Use JSON.parse() or other safe alternatives.',
                'CWE-95'
            )
        
        # Check for localStorage without validation
        if 'localStorage' in content and 'JSON.parse' not in content:
            self.log_vulnerability(
                'Data Validation', 'MEDIUM', file_path, 0,
                'localStorage usage without proper validation',
                'Always validate and sanitize data from localStorage before use.',
                'CWE-20'
            )
        
        # Check for console.log with sensitive data
        for i, line in enumerate(lines, 1):
            if 'console.log' in line and any(sensitive in line.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                self.log_vulnerability(
                    'Information Disclosure', 'MEDIUM', file_path, i,
                    'Potential sensitive data logging',
                    'Remove or sanitize sensitive data from console logs in production.',
                    'CWE-200'
                )
        
        # Check for missing input validation
        if 'handleAnswerChange' in content and 'validation' not in content.lower():
            self.log_vulnerability(
                'Input Validation', 'HIGH', file_path, 0,
                'Missing input validation in form handling',
                'Implement proper input validation and sanitization for all user inputs.',
                'CWE-20'
            )
        
        # Check for missing CSRF protection
        if 'fetch(' in content and 'csrf' not in content.lower():
            self.log_vulnerability(
                'CSRF', 'HIGH', file_path, 0,
                'Missing CSRF protection in API calls',
                'Implement CSRF tokens for all state-changing operations.',
                'CWE-352'
            )
    
    def audit_landing_page(self):
        """Audit LandingPage component"""
        file_path = "frontend/src/components/LandingPage.tsx"
        
        if not os.path.exists(file_path):
            return
        
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'token["\']?\s*[:=]\s*["\'][^"\']+["\']'
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.log_vulnerability(
                        'Information Disclosure', 'CRITICAL', file_path, i,
                        'Hardcoded secret detected',
                        'Move secrets to environment variables or secure configuration.',
                        'CWE-798'
                    )
        
        # Check for missing HTTPS enforcement
        if 'http://' in content and 'https://' not in content:
            self.log_vulnerability(
                'Transport Security', 'HIGH', file_path, 0,
                'HTTP usage without HTTPS enforcement',
                'Always use HTTPS for production and enforce HTTPS redirects.',
                'CWE-319'
            )
        
        # Check for missing Content Security Policy
        if 'Content-Security-Policy' not in content:
            self.log_vulnerability(
                'XSS Prevention', 'MEDIUM', file_path, 0,
                'Missing Content Security Policy',
                'Implement CSP headers to prevent XSS attacks.',
                'CWE-79'
            )
    
    def audit_frontend_patterns(self):
        """Audit general frontend security patterns"""
        print("🔍 Auditing Frontend Security Patterns...")
        
        # Check for missing error boundaries
        if not os.path.exists("frontend/src/components/ErrorBoundary.tsx"):
            self.log_vulnerability(
                'Error Handling', 'MEDIUM', 'frontend/src/components/', 0,
                'Missing Error Boundary component',
                'Implement Error Boundary to prevent sensitive information leakage.',
                'CWE-209'
            )
        
        # Check for missing input sanitization utilities
        if not os.path.exists("frontend/src/utils/sanitize.ts"):
            self.log_vulnerability(
                'Input Validation', 'HIGH', 'frontend/src/utils/', 0,
                'Missing input sanitization utilities',
                'Create utility functions for input sanitization and validation.',
                'CWE-20'
            )
    
    def audit_api_endpoints(self):
        """Audit API endpoints for security issues"""
        print("🔍 Auditing API Endpoints...")
        
        file_path = "backend/api/assessment_endpoints.py"
        
        if not os.path.exists(file_path):
            return
        
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for SQL injection vulnerabilities
        for i, line in enumerate(lines, 1):
            if 'cursor.execute(' in line and '%' in line and '?' not in line:
                self.log_vulnerability(
                    'SQL Injection', 'CRITICAL', file_path, i,
                    'Potential SQL injection vulnerability',
                    'Use parameterized queries with ? placeholders instead of string formatting.',
                    'CWE-89'
                )
        
        # Check for missing input validation
        if 'request.get_json()' in content and 'validation' not in content.lower():
            self.log_vulnerability(
                'Input Validation', 'HIGH', file_path, 0,
                'Missing input validation for JSON data',
                'Implement comprehensive input validation for all API endpoints.',
                'CWE-20'
            )
        
        # Check for missing authentication
        if '@assessment_api.route' in content and 'auth' not in content.lower():
            self.log_vulnerability(
                'Authentication', 'HIGH', file_path, 0,
                'Missing authentication on API endpoints',
                'Implement proper authentication and authorization for all endpoints.',
                'CWE-287'
            )
        
        # Check for missing rate limiting
        if 'rate' not in content.lower() and 'limit' not in content.lower():
            self.log_vulnerability(
                'Rate Limiting', 'MEDIUM', file_path, 0,
                'Missing rate limiting on API endpoints',
                'Implement rate limiting to prevent abuse and DoS attacks.',
                'CWE-770'
            )
        
        # Check for missing CORS configuration
        if 'cors' not in content.lower():
            self.log_vulnerability(
                'CORS', 'MEDIUM', file_path, 0,
                'Missing CORS configuration',
                'Configure CORS properly to prevent unauthorized cross-origin requests.',
                'CWE-346'
            )
        
        # Check for missing error handling
        for i, line in enumerate(lines, 1):
            if 'except Exception as e:' in line and 'logger.error' not in line:
                self.log_vulnerability(
                    'Error Handling', 'MEDIUM', file_path, i,
                    'Insufficient error logging',
                    'Log all errors with appropriate detail for security monitoring.',
                    'CWE-209'
                )
        
        # Check for missing CSRF protection
        if 'csrf' not in content.lower():
            self.log_vulnerability(
                'CSRF', 'HIGH', file_path, 0,
                'Missing CSRF protection',
                'Implement CSRF tokens for all state-changing operations.',
                'CWE-352'
            )
    
    def audit_data_handling(self):
        """Audit data handling and storage"""
        print("🔍 Auditing Data Handling...")
        
        # Check for unencrypted sensitive data
        file_path = "backend/api/assessment_endpoints.py"
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            if 'email' in content and 'encrypt' not in content.lower():
                self.log_vulnerability(
                    'Data Protection', 'HIGH', file_path, 0,
                    'Sensitive data (email) stored without encryption',
                    'Encrypt sensitive data at rest and in transit.',
                    'CWE-311'
                )
        
        # Check for missing data retention policies
        if 'retention' not in content.lower() and 'delete' not in content.lower():
            self.log_vulnerability(
                'Data Retention', 'MEDIUM', file_path, 0,
                'Missing data retention policies',
                'Implement data retention and deletion policies for GDPR compliance.',
                'CWE-200'
            )
    
    def audit_authentication(self):
        """Audit authentication and authorization"""
        print("🔍 Auditing Authentication...")
        
        # Check for missing session management
        if not os.path.exists("backend/auth/session_manager.py"):
            self.log_vulnerability(
                'Session Management', 'HIGH', 'backend/auth/', 0,
                'Missing session management',
                'Implement secure session management with proper expiration.',
                'CWE-613'
            )
        
        # Check for missing password policies
        if not os.path.exists("backend/auth/password_policy.py"):
            self.log_vulnerability(
                'Password Policy', 'MEDIUM', 'backend/auth/', 0,
                'Missing password policy enforcement',
                'Implement strong password policies and validation.',
                'CWE-521'
            )
    
    def generate_security_fixes(self):
        """Generate security fixes and improvements"""
        print("🔧 Generating Security Fixes...")
        
        fixes = []
        
        # Input validation fixes
        fixes.append({
            'file': 'frontend/src/utils/validation.ts',
            'content': self.create_validation_utils()
        })
        
        # Sanitization utilities
        fixes.append({
            'file': 'frontend/src/utils/sanitize.ts',
            'content': self.create_sanitization_utils()
        })
        
        # Error boundary
        fixes.append({
            'file': 'frontend/src/components/ErrorBoundary.tsx',
            'content': self.create_error_boundary()
        })
        
        # Security headers middleware
        fixes.append({
            'file': 'backend/middleware/security.py',
            'content': self.create_security_middleware()
        })
        
        # Input validation for API
        fixes.append({
            'file': 'backend/utils/validation.py',
            'content': self.create_api_validation()
        })
        
        return fixes
    
    def create_validation_utils(self):
        """Create input validation utilities"""
        return '''import DOMPurify from 'dompurify';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  sanitizedValue?: string;
}

export class InputValidator {
  static validateEmail(email: string): ValidationResult {
    const errors: string[] = [];
    
    if (!email) {
      errors.push('Email is required');
      return { isValid: false, errors };
    }
    
    if (typeof email !== 'string') {
      errors.push('Email must be a string');
      return { isValid: false, errors };
    }
    
    if (email.length > 254) {
      errors.push('Email is too long');
      return { isValid: false, errors };
    }
    
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) {
      errors.push('Invalid email format');
      return { isValid: false, errors };
    }
    
    return { isValid: true, errors: [], sanitizedValue: email.toLowerCase().trim() };
  }
  
  static validateName(name: string): ValidationResult {
    const errors: string[] = [];
    
    if (!name) {
      errors.push('Name is required');
      return { isValid: false, errors };
    }
    
    if (typeof name !== 'string') {
      errors.push('Name must be a string');
      return { isValid: false, errors };
    }
    
    if (name.length < 1 || name.length > 100) {
      errors.push('Name must be between 1 and 100 characters');
      return { isValid: false, errors };
    }
    
    // Check for potentially malicious content
    if (/<script|javascript:|on\\w+\\s*=/i.test(name)) {
      errors.push('Name contains potentially malicious content');
      return { isValid: false, errors };
    }
    
    const sanitized = DOMPurify.sanitize(name.trim());
    return { isValid: true, errors: [], sanitizedValue: sanitized };
  }
  
  static validatePhone(phone: string): ValidationResult {
    const errors: string[] = [];
    
    if (!phone) {
      return { isValid: true, errors: [], sanitizedValue: '' };
    }
    
    if (typeof phone !== 'string') {
      errors.push('Phone must be a string');
      return { isValid: false, errors };
    }
    
    // Remove all non-digit characters
    const digitsOnly = phone.replace(/\\D/g, '');
    
    if (digitsOnly.length < 10 || digitsOnly.length > 15) {
      errors.push('Phone number must be between 10 and 15 digits');
      return { isValid: false, errors };
    }
    
    return { isValid: true, errors: [], sanitizedValue: digitsOnly };
  }
  
  static sanitizeHtml(html: string): string {
    return DOMPurify.sanitize(html);
  }
  
  static validateAssessmentAnswers(answers: Record<string, any>): ValidationResult {
    const errors: string[] = [];
    
    if (!answers || typeof answers !== 'object') {
      errors.push('Answers must be an object');
      return { isValid: false, errors };
    }
    
    // Check for excessive data size
    const jsonString = JSON.stringify(answers);
    if (jsonString.length > 10000) {
      errors.push('Assessment answers are too large');
      return { isValid: false, errors };
    }
    
    // Validate each answer
    for (const [key, value] of Object.entries(answers)) {
      if (typeof key !== 'string' || key.length > 100) {
        errors.push('Invalid answer key');
        continue;
      }
      
      if (typeof value === 'string' && value.length > 1000) {
        errors.push(`Answer for ${key} is too long`);
        continue;
      }
      
      // Sanitize string values
      if (typeof value === 'string') {
        answers[key] = DOMPurify.sanitize(value);
      }
    }
    
    return { isValid: true, errors: [], sanitizedValue: answers };
  }
}'''
    
    def create_sanitization_utils(self):
        """Create sanitization utilities"""
        return '''import DOMPurify from 'dompurify';

export class Sanitizer {
  static sanitizeString(input: string): string {
    if (typeof input !== 'string') {
      return '';
    }
    
    // Remove null bytes and control characters
    let sanitized = input.replace(/[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]/g, '');
    
    // Trim whitespace
    sanitized = sanitized.trim();
    
    // Limit length
    sanitized = sanitized.substring(0, 1000);
    
    // Sanitize HTML
    sanitized = DOMPurify.sanitize(sanitized);
    
    return sanitized;
  }
  
  static sanitizeObject(obj: any): any {
    if (obj === null || obj === undefined) {
      return obj;
    }
    
    if (typeof obj === 'string') {
      return this.sanitizeString(obj);
    }
    
    if (Array.isArray(obj)) {
      return obj.map(item => this.sanitizeObject(item));
    }
    
    if (typeof obj === 'object') {
      const sanitized: any = {};
      for (const [key, value] of Object.entries(obj)) {
        const sanitizedKey = this.sanitizeString(key);
        sanitized[sanitizedKey] = this.sanitizeObject(value);
      }
      return sanitized;
    }
    
    return obj;
  }
  
  static escapeHtml(unsafe: string): string {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  
  static validateAndSanitizeEmail(email: string): string | null {
    if (!email || typeof email !== 'string') {
      return null;
    }
    
    const sanitized = this.sanitizeString(email);
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/;
    
    if (!emailRegex.test(sanitized)) {
      return null;
    }
    
    return sanitized.toLowerCase();
  }
}'''
    
    def create_error_boundary(self):
        """Create error boundary component"""
        return '''import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to monitoring service
    console.error('Error caught by boundary:', error, errorInfo);
    
    // In production, send to error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: sendErrorToService(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
          <div className="text-center p-8">
            <h1 className="text-2xl font-bold text-red-400 mb-4">
              Something went wrong
            </h1>
            <p className="text-gray-300 mb-6">
              We apologize for the inconvenience. Please try refreshing the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-2 rounded-lg"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}'''
    
    def create_security_middleware(self):
        """Create security middleware"""
        return '''from flask import Flask, request, jsonify, make_response
from functools import wraps
import time
import hashlib
import hmac
import os
from datetime import datetime, timedelta

class SecurityMiddleware:
    def __init__(self, app: Flask = None):
        self.app = app
        self.rate_limits = {}
        self.max_requests = 100  # per minute
        self.window_size = 60  # seconds
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        # Rate limiting
        client_ip = request.remote_addr
        current_time = time.time()
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
        
        # Clean old requests
        self.rate_limits[client_ip] = [
            req_time for req_time in self.rate_limits[client_ip]
            if current_time - req_time < self.window_size
        ]
        
        # Check rate limit
        if len(self.rate_limits[client_ip]) >= self.max_requests:
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Add current request
        self.rate_limits[client_ip].append(current_time)
        
        # CSRF protection
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            csrf_token = request.headers.get('X-CSRF-Token')
            if not self.validate_csrf_token(csrf_token):
                return jsonify({'error': 'Invalid CSRF token'}), 403
    
    def after_request(self, response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    def validate_csrf_token(self, token: str) -> bool:
        if not token:
            return False
        
        # In production, implement proper CSRF token validation
        # This is a simplified example
        expected_token = os.environ.get('CSRF_SECRET', 'default-secret')
        return hmac.compare_digest(token, expected_token)

def require_csrf(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        # Implement proper JWT validation here
        if not validate_jwt_token(token):
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_jwt_token(token: str) -> bool:
    # Implement JWT validation logic
    # This is a placeholder
    return True'''
    
    def create_api_validation(self):
        """Create API validation utilities"""
        return '''import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class APIValidator:
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email address"""
        if not email or not isinstance(email, str):
            return False, "Email is required and must be a string"
        
        if len(email) > 254:
            return False, "Email is too long"
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        """Validate name field"""
        if not name or not isinstance(name, str):
            return False, "Name is required and must be a string"
        
        if len(name) < 1 or len(name) > 100:
            return False, "Name must be between 1 and 100 characters"
        
        # Check for potentially malicious content
        if re.search(r'<script|javascript:|on\\w+\\s*=', name, re.IGNORECASE):
            return False, "Name contains potentially malicious content"
        
        return True, ""
    
    @staticmethod
    def validate_phone(phone: str) -> tuple[bool, str]:
        """Validate phone number"""
        if not phone:
            return True, ""  # Phone is optional
        
        if not isinstance(phone, str):
            return False, "Phone must be a string"
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\\D', '', phone)
        
        if len(digits_only) < 10 or len(digits_only) > 15:
            return False, "Phone number must be between 10 and 15 digits"
        
        return True, ""
    
    @staticmethod
    def validate_assessment_type(assessment_type: str) -> tuple[bool, str]:
        """Validate assessment type"""
        valid_types = ['ai-risk', 'income-comparison', 'cuffing-season', 'layoff-risk']
        
        if not assessment_type or not isinstance(assessment_type, str):
            return False, "Assessment type is required"
        
        if assessment_type not in valid_types:
            return False, f"Invalid assessment type. Must be one of: {', '.join(valid_types)}"
        
        return True, ""
    
    @staticmethod
    def validate_answers(answers: Dict[str, Any]) -> tuple[bool, str]:
        """Validate assessment answers"""
        if not answers or not isinstance(answers, dict):
            return False, "Answers must be a dictionary"
        
        # Check for excessive data size
        json_string = json.dumps(answers)
        if len(json_string) > 10000:
            return False, "Assessment answers are too large"
        
        # Validate each answer
        for key, value in answers.items():
            if not isinstance(key, str) or len(key) > 100:
                return False, "Invalid answer key"
            
            if isinstance(value, str) and len(value) > 1000:
                return False, f"Answer for {key} is too long"
        
        return True, ""
    
    @staticmethod
    def sanitize_string(input_str: str) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]', '', input_str)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length
        sanitized = sanitized[:1000]
        
        return sanitized
    
    @staticmethod
    def sanitize_object(obj: Any) -> Any:
        """Recursively sanitize object"""
        if obj is None:
            return obj
        
        if isinstance(obj, str):
            return APIValidator.sanitize_string(obj)
        
        if isinstance(obj, list):
            return [APIValidator.sanitize_object(item) for item in obj]
        
        if isinstance(obj, dict):
            return {key: APIValidator.sanitize_object(value) for key, value in obj.items()}
        
        return obj
    
    @staticmethod
    def validate_assessment_data(data: Dict[str, Any]) -> tuple[bool, List[str], Dict[str, Any]]:
        """Comprehensive validation of assessment data"""
        errors = []
        sanitized_data = {}
        
        # Validate email
        is_valid, error = APIValidator.validate_email(data.get('email', ''))
        if not is_valid:
            errors.append(f"Email: {error}")
        else:
            sanitized_data['email'] = data['email'].lower().strip()
        
        # Validate first name
        is_valid, error = APIValidator.validate_name(data.get('firstName', ''))
        if not is_valid:
            errors.append(f"First Name: {error}")
        else:
            sanitized_data['firstName'] = APIValidator.sanitize_string(data['firstName'])
        
        # Validate phone (optional)
        if 'phone' in data:
            is_valid, error = APIValidator.validate_phone(data['phone'])
            if not is_valid:
                errors.append(f"Phone: {error}")
            else:
                sanitized_data['phone'] = APIValidator.sanitize_string(data['phone'])
        
        # Validate assessment type
        is_valid, error = APIValidator.validate_assessment_type(data.get('assessmentType', ''))
        if not is_valid:
            errors.append(f"Assessment Type: {error}")
        else:
            sanitized_data['assessmentType'] = data['assessmentType']
        
        # Validate answers
        is_valid, error = APIValidator.validate_answers(data.get('answers', {}))
        if not is_valid:
            errors.append(f"Answers: {error}")
        else:
            sanitized_data['answers'] = APIValidator.sanitize_object(data['answers'])
        
        # Add timestamp
        sanitized_data['completedAt'] = datetime.now().isoformat()
        
        return len(errors) == 0, errors, sanitized_data'''
    
    def run_complete_audit(self):
        """Run complete security audit"""
        print("🔒 Starting Comprehensive Security Audit")
        print("=" * 60)
        
        self.audit_frontend_components()
        self.audit_api_endpoints()
        self.audit_data_handling()
        self.audit_authentication()
        
        # Generate report
        self.generate_report()
        
        # Generate fixes
        fixes = self.generate_security_fixes()
        
        return self.vulnerabilities, fixes
    
    def generate_report(self):
        """Generate security audit report"""
        print("\n" + "=" * 60)
        print("📊 SECURITY AUDIT REPORT")
        print("=" * 60)
        
        total_vulns = len(self.vulnerabilities)
        critical = len(self.critical_issues)
        high = len(self.high_issues)
        medium = len(self.medium_issues)
        low = len(self.low_issues)
        
        print(f"🔍 Total Vulnerabilities Found: {total_vulns}")
        print(f"🚨 Critical: {critical}")
        print(f"⚠️  High: {high}")
        print(f"📋 Medium: {medium}")
        print(f"ℹ️  Low: {low}")
        
        if critical > 0:
            print(f"\n🚨 CRITICAL ISSUES ({critical}):")
            for vuln in self.critical_issues:
                print(f"   • {vuln['issue']} ({vuln['file']}:{vuln['line']})")
                print(f"     CWE: {vuln['cwe']}")
                print(f"     Fix: {vuln['recommendation']}")
                print()
        
        if high > 0:
            print(f"\n⚠️  HIGH PRIORITY ISSUES ({high}):")
            for vuln in self.high_issues:
                print(f"   • {vuln['issue']} ({vuln['file']}:{vuln['line']})")
                print(f"     CWE: {vuln['cwe']}")
                print(f"     Fix: {vuln['recommendation']}")
                print()
        
        # Save detailed report
        report_data = {
            'summary': {
                'total_vulnerabilities': total_vulns,
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low,
                'audit_date': datetime.now().isoformat()
            },
            'vulnerabilities': self.vulnerabilities
        }
        
        with open('security_audit_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: security_audit_report.json")
        
        if total_vulns == 0:
            print("\n🎉 No security vulnerabilities found!")
        else:
            print(f"\n🔧 {total_vulns} security issues need attention.")

def main():
    """Main audit function"""
    auditor = SecurityAuditor()
    vulnerabilities, fixes = auditor.run_complete_audit()
    
    # Create security fix files
    for fix in fixes:
        os.makedirs(os.path.dirname(fix['file']), exist_ok=True)
        with open(fix['file'], 'w') as f:
            f.write(fix['content'])
        print(f"✅ Created security fix: {fix['file']}")
    
    return vulnerabilities, fixes

if __name__ == "__main__":
    main()
