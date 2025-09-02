"""
Specialized log formatters for different environments in the Mingus financial application.
Provides environment-specific formatting with appropriate detail levels and privacy protection.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod


class BaseFormatter(ABC, logging.Formatter):
    """Base formatter class with common functionality."""
    
    def __init__(self, include_timestamp: bool = True, 
                 include_level: bool = True, 
                 include_logger: bool = True,
                 include_module: bool = True,
                 include_function: bool = True,
                 include_line: bool = True,
                 include_process: bool = True,
                 include_thread: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_module = include_module
        self.include_function = include_function
        self.include_line = include_line
        self.include_process = include_process
        self.include_thread = include_thread
    
    @abstractmethod
    def format(self, record: logging.LogRecord) -> str:
        """Format log record according to environment requirements."""
        pass
    
    def _get_base_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Get base fields for all formatters."""
        fields = {}
        
        if self.include_timestamp:
            fields['timestamp'] = datetime.utcnow().isoformat()
        
        if self.include_level:
            fields['level'] = record.levelname
        
        if self.include_logger:
            fields['logger'] = record.name
        
        if self.include_module:
            fields['module'] = record.module
        
        if self.include_function:
            fields['function'] = record.funcName
        
        if self.include_line:
            fields['line'] = record.lineno
        
        if self.include_process:
            fields['process_id'] = record.process
        
        if self.include_thread:
            fields['thread_id'] = record.thread
        
        return fields
    
    def _sanitize_sensitive_data(self, data: Any) -> Any:
        """Remove or redact sensitive information from log data."""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return [self._sanitize_sensitive_data(item) for item in data]
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string for sensitive information."""
        import re
        
        # Credit card patterns
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[REDACTED_CC]', text)
        
        # SSN patterns
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
        text = re.sub(r'\b\d{9}\b', '[REDACTED_SSN]', text)
        
        # Email addresses (keep domain for debugging)
        text = re.sub(r'\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b', 
                     r'[REDACTED]@\2', text)
        
        # Phone numbers
        text = re.sub(r'\b\d{10,11}\b', '[REDACTED_PHONE]', text)
        
        # Account numbers (generic pattern)
        text = re.sub(r'\b\d{8,17}\b', '[REDACTED_ACCOUNT]', text)
        
        return text
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary for sensitive information."""
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'api_key', 'private_key',
            'credit_card', 'ssn', 'social_security', 'account_number',
            'routing_number', 'pin', 'cvv', 'expiry', 'cvv2', 'cvc',
            'card_number', 'cardholder_name', 'billing_address',
            'mother_maiden_name', 'security_question', 'security_answer',
            'authorization', 'cookie', 'x-api-key'
        }
        
        sanitized = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = self._sanitize_sensitive_data(value)
        
        return sanitized


class DevelopmentFormatter(BaseFormatter):
    """Development environment formatter with detailed information."""
    
    def __init__(self):
        super().__init__(
            include_timestamp=True,
            include_level=True,
            include_logger=True,
            include_module=True,
            include_function=True,
            include_line=True,
            include_process=True,
            include_thread=True
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for development with maximum detail."""
        
        # Get base fields
        log_entry = self._get_base_fields(record)
        
        # Add message
        log_entry['message'] = record.getMessage()
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error',
                'traceback': self._format_traceback(record.exc_info[2])
            }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry['extra'] = self._sanitize_sensitive_data(record.extra_fields)
        
        # Add request context if available
        try:
            from flask import request, g
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown'),
                    'headers': dict(request.headers),
                    'args': dict(request.args),
                    'form': dict(request.form),
                    'json': request.get_json(silent=True),
                    'user_id': getattr(g, 'user_id', None),
                    'session_id': getattr(g, 'session_id', None),
                    'request_id': getattr(g, 'request_id', None)
                }
        except (ImportError, RuntimeError):
            pass
        
        # Format as pretty JSON for development
        return json.dumps(log_entry, indent=2, default=str)
    
    def _format_traceback(self, traceback_obj) -> str:
        """Format traceback for development readability."""
        if not traceback_obj:
            return ""
        
        import traceback
        return traceback.format_tb(traceback_obj)


class StagingFormatter(BaseFormatter):
    """Staging environment formatter with balanced detail."""
    
    def __init__(self):
        super().__init__(
            include_timestamp=True,
            include_level=True,
            include_logger=True,
            include_module=True,
            include_function=True,
            include_line=False,  # Less verbose than development
            include_process=False,
            include_thread=False
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for staging with balanced detail."""
        
        # Get base fields
        log_entry = self._get_base_fields(record)
        
        # Add message
        log_entry['message'] = record.getMessage()
        
        # Add exception info if present (simplified)
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error'
            }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry['extra'] = self._sanitize_sensitive_data(record.extra_fields)
        
        # Add request context if available (simplified)
        try:
            from flask import request, g
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_id': getattr(g, 'user_id', None),
                    'request_id': getattr(g, 'request_id', None)
                }
        except (ImportError, RuntimeError):
            pass
        
        # Format as compact JSON
        return json.dumps(log_entry, separators=(',', ':'), default=str)


class ProductionFormatter(BaseFormatter):
    """Production environment formatter with minimal detail for security."""
    
    def __init__(self):
        super().__init__(
            include_timestamp=True,
            include_level=True,
            include_logger=True,
            include_module=False,  # Minimal for production
            include_function=False,
            include_line=False,
            include_process=False,
            include_thread=False
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for production with minimal detail."""
        
        # Get base fields
        log_entry = self._get_base_fields(record)
        
        # Add message (sanitized)
        log_entry['message'] = self._sanitize_string(record.getMessage())
        
        # Add exception info if present (minimal)
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown'
            }
        
        # Add extra fields (heavily sanitized)
        if hasattr(record, 'extra_fields'):
            log_entry['extra'] = self._sanitize_sensitive_data(record.extra_fields)
        
        # Add minimal request context
        try:
            from flask import request, g
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url.split('?')[0],  # Remove query parameters
                    'user_id': getattr(g, 'user_id', None),
                    'request_id': getattr(g, 'request_id', None)
                }
        except (ImportError, RuntimeError):
            pass
        
        # Format as compact JSON
        return json.dumps(log_entry, separators=(',', ':'), default=str)


class SecurityFormatter(BaseFormatter):
    """Specialized formatter for security events with enhanced detail."""
    
    def __init__(self):
        super().__init__(
            include_timestamp=True,
            include_level=True,
            include_logger=True,
            include_module=True,
            include_function=True,
            include_line=True,
            include_process=True,
            include_thread=True
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format security log record with enhanced detail."""
        
        # Get base fields
        log_entry = self._get_base_fields(record)
        
        # Add security-specific fields
        log_entry['event_type'] = 'security_event'
        log_entry['message'] = record.getMessage()
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error',
                'traceback': self._format_traceback(record.exc_info[2])
            }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry['extra'] = self._sanitize_sensitive_data(record.extra_fields)
        
        # Add comprehensive request context for security
        try:
            from flask import request, g
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown'),
                    'referrer': request.headers.get('Referer', 'Unknown'),
                    'origin': request.headers.get('Origin', 'Unknown'),
                    'x_forwarded_for': request.headers.get('X-Forwarded-For', 'Unknown'),
                    'x_real_ip': request.headers.get('X-Real-IP', 'Unknown'),
                    'user_id': getattr(g, 'user_id', None),
                    'session_id': getattr(g, 'session_id', None),
                    'request_id': getattr(g, 'request_id', None),
                    'headers': {k: v for k, v in request.headers.items() 
                              if not any(sensitive in k.lower() 
                                       for sensitive in ['authorization', 'cookie', 'x-api-key'])}
                }
        except (ImportError, RuntimeError):
            pass
        
        # Format as JSON
        return json.dumps(log_entry, default=str)
    
    def _format_traceback(self, traceback_obj) -> str:
        """Format traceback for security analysis."""
        if not traceback_obj:
            return ""
        
        import traceback
        return traceback.format_tb(traceback_obj)


class FinancialFormatter(BaseFormatter):
    """Specialized formatter for financial transactions with audit trail."""
    
    def __init__(self):
        super().__init__(
            include_timestamp=True,
            include_level=True,
            include_logger=True,
            include_module=True,
            include_function=True,
            include_line=True,
            include_process=True,
            include_thread=True
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format financial log record with audit trail."""
        
        # Get base fields
        log_entry = self._get_base_fields(record)
        
        # Add financial-specific fields
        log_entry['event_type'] = 'financial_transaction'
        log_entry['message'] = record.getMessage()
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error'
            }
        
        # Add extra fields (financial data)
        if hasattr(record, 'extra_fields'):
            log_entry['transaction_data'] = self._sanitize_sensitive_data(record.extra_fields)
        
        # Add request context for financial audit
        try:
            from flask import request, g
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown'),
                    'user_id': getattr(g, 'user_id', None),
                    'session_id': getattr(g, 'session_id', None),
                    'request_id': getattr(g, 'request_id', None),
                    'ip_chain': self._get_ip_chain(request)
                }
        except (ImportError, RuntimeError):
            pass
        
        # Format as JSON
        return json.dumps(log_entry, default=str)
    
    def _get_ip_chain(self, request) -> Dict[str, str]:
        """Get IP address chain for financial audit."""
        return {
            'remote_addr': request.remote_addr,
            'x_forwarded_for': request.headers.get('X-Forwarded-For', 'Unknown'),
            'x_real_ip': request.headers.get('X-Real-IP', 'Unknown'),
            'x_client_ip': request.headers.get('X-Client-IP', 'Unknown')
        }


def get_formatter_for_environment(environment: str = None) -> BaseFormatter:
    """Get appropriate formatter based on environment."""
    if not environment:
        environment = os.getenv('FLASK_ENV', 'development')
    
    environment = environment.lower()
    
    if environment == 'production':
        return ProductionFormatter()
    elif environment == 'staging':
        return StagingFormatter()
    elif environment == 'development':
        return DevelopmentFormatter()
    else:
        # Default to development for unknown environments
        return DevelopmentFormatter()


def get_security_formatter() -> SecurityFormatter:
    """Get security-specific formatter."""
    return SecurityFormatter()


def get_financial_formatter() -> FinancialFormatter:
    """Get financial transaction formatter."""
    return FinancialFormatter()
