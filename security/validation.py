#!/usr/bin/env python3
"""
MINGUS Input Validation System
Comprehensive validation for financial wellness application
Protects against injection attacks and data corruption
"""

import os
import re
import json
import logging
import hashlib
import mimetypes
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import html
import urllib.parse

from flask import Flask, request, Response, g, current_app, jsonify, abort
from werkzeug.exceptions import BadRequest, Forbidden
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

@dataclass
class ValidationError:
    """Validation error details"""
    field: str
    message: str
    value: Any
    error_type: str
    severity: str = "error"  # error, warning, info

@dataclass
class ValidationResult:
    """Validation result with cleaned data and errors"""
    is_valid: bool
    cleaned_data: Dict[str, Any]
    errors: List[ValidationError]
    warnings: List[ValidationError]

class BaseValidator:
    """Base validation class with common functionality"""
    
    def __init__(self, field_name: str, required: bool = True, default: Any = None):
        self.field_name = field_name
        self.required = required
        self.default = default
        self.custom_validators: List[Callable] = []
    
    def validate(self, value: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate a single value"""
        errors = []
        
        # Check if required
        if value is None or value == "":
            if self.required:
                errors.append(ValidationError(
                    field=self.field_name,
                    message=f"{self.field_name} is required",
                    value=value,
                    error_type="required"
                ))
                return False, None, errors
            else:
                return True, self.default, errors
        
        # Apply custom validators
        for validator in self.custom_validators:
            is_valid, cleaned_value, validator_errors = validator(value)
            if not is_valid:
                errors.extend(validator_errors)
            else:
                value = cleaned_value
        
        return len(errors) == 0, value, errors
    
    def add_validator(self, validator: Callable):
        """Add custom validator function"""
        self.custom_validators.append(validator)
        return self
    
    def sanitize_html(self, value: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        if not isinstance(value, str):
            return value
        
        # Remove dangerous HTML tags and attributes
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button']
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'javascript:']
        
        # Remove dangerous tags
        for tag in dangerous_tags:
            value = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', value, flags=re.IGNORECASE | re.DOTALL)
            value = re.sub(f'<{tag}[^>]*/?>', '', value, flags=re.IGNORECASE)
        
        # Remove dangerous attributes
        for attr in dangerous_attrs:
            value = re.sub(f'{attr}=["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
        
        # HTML escape remaining content
        return html.escape(value)
    
    def prevent_sql_injection(self, value: str) -> str:
        """Basic SQL injection prevention"""
        if not isinstance(value, str):
            return value
        
        # Remove SQL keywords and patterns
        sql_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b',
            r'[\'";]',
            r'--',
            r'/\*.*?\*/',
            r'xp_cmdshell',
            r'sp_',
            r'@@'
        ]
        
        for pattern in sql_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        return value.strip()

class StringValidator(BaseValidator):
    """String validation with length and format checks"""
    
    def __init__(self, field_name: str, min_length: int = 0, max_length: int = 255, 
                 pattern: Optional[str] = None, allowed_chars: Optional[str] = None,
                 sanitize_html: bool = True, prevent_sql_injection: bool = True,
                 **kwargs):
        super().__init__(field_name, **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.allowed_chars = allowed_chars
        self.sanitize_html = sanitize_html
        self.prevent_sql_injection = prevent_sql_injection
    
    def validate(self, value: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate string value"""
        errors = []
        
        # Check if required
        if value is None or value == "":
            if self.required:
                errors.append(ValidationError(
                    field=self.field_name,
                    message=f"{self.field_name} is required",
                    value=value,
                    error_type="required"
                ))
                return False, None, errors
            else:
                return True, self.default, errors
        
        # Convert to string
        if not isinstance(value, str):
            value = str(value)
        
        # Length validation
        if len(value) < self.min_length:
            errors.append(ValidationError(
                field=self.field_name,
                message=f"{self.field_name} must be at least {self.min_length} characters long",
                value=value,
                error_type="min_length"
            ))
        
        if len(value) > self.max_length:
            errors.append(ValidationError(
                field=self.field_name,
                message=f"{self.field_name} must be no more than {self.max_length} characters long",
                value=value,
                error_type="max_length"
            ))
        
        # Pattern validation
        if self.pattern and not re.match(self.pattern, value):
            errors.append(ValidationError(
                field=self.field_name,
                message=f"{self.field_name} format is invalid",
                value=value,
                error_type="pattern"
            ))
        
        # Allowed characters validation
        if self.allowed_chars:
            invalid_chars = [char for char in value if char not in self.allowed_chars]
            if invalid_chars:
                errors.append(ValidationError(
                    field=self.field_name,
                    message=f"{self.field_name} contains invalid characters: {''.join(invalid_chars)}",
                    value=value,
                    error_type="invalid_chars"
                ))
        
        # Sanitization
        if self.sanitize_html:
            value = self.sanitize_html(value)
        
        if self.prevent_sql_injection:
            value = self.prevent_sql_injection(value)
        
        # Apply custom validators
        for validator in self.custom_validators:
            is_valid, cleaned_value, validator_errors = validator(value)
            if not is_valid:
                errors.extend(validator_errors)
            else:
                value = cleaned_value
        
        return len(errors) == 0, value, errors

class NumberValidator(BaseValidator):
    """Number validation with range checks"""
    
    def __init__(self, field_name: str, min_value: Optional[Union[int, float, Decimal]] = None,
                 max_value: Optional[Union[int, float, Decimal]] = None,
                 allow_negative: bool = False, precision: Optional[int] = None,
                 **kwargs):
        super().__init__(field_name, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.allow_negative = allow_negative
        self.precision = precision
    
    def validate(self, value: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate number value"""
        errors = []
        
        # Check if required
        if value is None or value == "":
            if self.required:
                errors.append(ValidationError(
                    field=self.field_name,
                    message=f"{self.field_name} is required",
                    value=value,
                    error_type="required"
                ))
                return False, None, errors
            else:
                return True, self.default, errors
        
        # Convert to number
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                value = re.sub(r'[$,€£¥₹]', '', value)
                value = value.replace(',', '')
            
            if self.precision:
                value = Decimal(str(value)).quantize(Decimal('0.01'))
            else:
                value = float(value)
        except (ValueError, InvalidOperation):
            errors.append(ValidationError(
                field=self.field_name,
                message=f"{self.field_name} must be a valid number",
                value=value,
                error_type="invalid_number"
            ))
            return False, None, errors
        
        # Range validation
        if self.min_value is not None and value < self.min_value:
            errors.append(ValidationError(
                field=self.field_name,
                message=f"{self.field_name} must be at least {self.min_value}",
                value=value,
                error_type="min_value"
            ))
        
        if self.max_value is not None and value > self.max_value:
            errors.append(ValidationError(
                field=self.field_name,
                message=f"{self.field_name} must be no more than {self.max_value}",
                value=value,
                error_type="max_value"
            ))
        
        # Negative value validation
        if not self.allow_negative and value < 0:
            errors.append(ValidationError(
                field=self.field_name,
                message=f"{self.field_name} cannot be negative",
                value=value,
                error_type="negative_value"
            ))
        
        # Apply custom validators
        for validator in self.custom_validators:
            is_valid, cleaned_value, validator_errors = validator(value)
            if not is_valid:
                errors.extend(validator_errors)
            else:
                value = cleaned_value
        
        return len(errors) == 0, value, errors

class FinancialDataValidator:
    """Financial data validation for MINGUS application"""
    
    @staticmethod
    def validate_income(income: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate income amount"""
        validator = NumberValidator(
            field_name="income",
            min_value=0,
            max_value=10000000,  # $10M max
            allow_negative=False,
            precision=2,
            required=True
        )
        return validator.validate(income)
    
    @staticmethod
    def validate_expense(expense: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate expense amount"""
        validator = NumberValidator(
            field_name="expense",
            min_value=0,
            max_value=1000000,  # $1M max
            allow_negative=False,
            precision=2,
            required=True
        )
        return validator.validate(expense)
    
    @staticmethod
    def validate_percentage(percentage: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate percentage value"""
        validator = NumberValidator(
            field_name="percentage",
            min_value=0,
            max_value=100,
            allow_negative=False,
            precision=2,
            required=True
        )
        return validator.validate(percentage)
    
    @staticmethod
    def validate_account_number(account_number: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate account number (masked)"""
        validator = StringValidator(
            field_name="account_number",
            min_length=4,
            max_length=20,
            pattern=r'^[\d\*\-]+$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(account_number)
    
    @staticmethod
    def validate_routing_number(routing_number: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate bank routing number"""
        validator = StringValidator(
            field_name="routing_number",
            min_length=9,
            max_length=9,
            pattern=r'^\d{9}$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(routing_number)

class HealthDataValidator:
    """Health data validation for MINGUS application"""
    
    @staticmethod
    def validate_stress_level(stress_level: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate stress level (1-10 scale)"""
        validator = NumberValidator(
            field_name="stress_level",
            min_value=1,
            max_value=10,
            allow_negative=False,
            precision=0,
            required=True
        )
        return validator.validate(stress_level)
    
    @staticmethod
    def validate_activity_minutes(activity_minutes: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate activity minutes"""
        validator = NumberValidator(
            field_name="activity_minutes",
            min_value=0,
            max_value=1440,  # 24 hours
            allow_negative=False,
            precision=0,
            required=True
        )
        return validator.validate(activity_minutes)
    
    @staticmethod
    def validate_health_score(health_score: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate health score (0-100)"""
        validator = NumberValidator(
            field_name="health_score",
            min_value=0,
            max_value=100,
            allow_negative=False,
            precision=1,
            required=True
        )
        return validator.validate(health_score)
    
    @staticmethod
    def validate_mindfulness_minutes(mindfulness_minutes: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate mindfulness minutes"""
        validator = NumberValidator(
            field_name="mindfulness_minutes",
            min_value=0,
            max_value=480,  # 8 hours max
            allow_negative=False,
            precision=0,
            required=True
        )
        return validator.validate(mindfulness_minutes)

class PersonalInfoValidator:
    """Personal information validation for MINGUS application"""
    
    @staticmethod
    def validate_name(name: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate person name"""
        validator = StringValidator(
            field_name="name",
            min_length=1,
            max_length=100,
            pattern=r'^[a-zA-Z\s\-\'\.]+$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(name)
    
    @staticmethod
    def validate_email(email: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate email address"""
        validator = StringValidator(
            field_name="email",
            min_length=5,
            max_length=254,
            pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(email)
    
    @staticmethod
    def validate_phone(phone: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate phone number"""
        # Remove all non-digit characters for validation
        if isinstance(phone, str):
            phone_clean = re.sub(r'[^\d]', '', phone)
        else:
            phone_clean = str(phone)
        
        validator = StringValidator(
            field_name="phone",
            min_length=10,
            max_length=15,
            pattern=r'^\d{10,15}$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(phone_clean)
    
    @staticmethod
    def validate_address(address: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate address"""
        validator = StringValidator(
            field_name="address",
            min_length=5,
            max_length=200,
            pattern=r'^[a-zA-Z0-9\s\-\'\.\,#]+$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(address)
    
    @staticmethod
    def validate_zip_code(zip_code: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate ZIP code"""
        validator = StringValidator(
            field_name="zip_code",
            min_length=5,
            max_length=10,
            pattern=r'^\d{5}(-\d{4})?$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(zip_code)

class EmploymentDataValidator:
    """Employment data validation for MINGUS application"""
    
    @staticmethod
    def validate_job_title(job_title: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate job title"""
        validator = StringValidator(
            field_name="job_title",
            min_length=2,
            max_length=100,
            pattern=r'^[a-zA-Z\s\-\'\.\,\&]+$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(job_title)
    
    @staticmethod
    def validate_industry(industry: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate industry"""
        validator = StringValidator(
            field_name="industry",
            min_length=2,
            max_length=100,
            pattern=r'^[a-zA-Z\s\-\'\.\,\&]+$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(industry)
    
    @staticmethod
    def validate_company_name(company_name: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate company name"""
        validator = StringValidator(
            field_name="company_name",
            min_length=2,
            max_length=100,
            pattern=r'^[a-zA-Z0-9\s\-\'\.\,\&]+$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(company_name)
    
    @staticmethod
    def validate_years_experience(years_experience: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate years of experience"""
        validator = NumberValidator(
            field_name="years_experience",
            min_value=0,
            max_value=50,
            allow_negative=False,
            precision=1,
            required=True
        )
        return validator.validate(years_experience)

class SubscriptionDataValidator:
    """Subscription data validation for MINGUS application"""
    
    @staticmethod
    def validate_plan_type(plan_type: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate subscription plan type"""
        allowed_plans = ['budget', 'mid-tier', 'professional']
        validator = StringValidator(
            field_name="plan_type",
            min_length=1,
            max_length=20,
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        
        is_valid, cleaned_value, errors = validator.validate(plan_type)
        if is_valid and cleaned_value.lower() not in allowed_plans:
            errors.append(ValidationError(
                field="plan_type",
                message=f"Plan type must be one of: {', '.join(allowed_plans)}",
                value=cleaned_value,
                error_type="invalid_plan"
            ))
            return False, None, errors
        
        return is_valid, cleaned_value, errors
    
    @staticmethod
    def validate_billing_amount(billing_amount: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate billing amount"""
        validator = NumberValidator(
            field_name="billing_amount",
            min_value=0,
            max_value=1000,
            allow_negative=False,
            precision=2,
            required=True
        )
        return validator.validate(billing_amount)
    
    @staticmethod
    def validate_card_number(card_number: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate credit card number (masked)"""
        validator = StringValidator(
            field_name="card_number",
            min_length=13,
            max_length=19,
            pattern=r'^[\d\*\-]+$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(card_number)
    
    @staticmethod
    def validate_expiry_date(expiry_date: Any) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate card expiry date"""
        validator = StringValidator(
            field_name="expiry_date",
            min_length=5,
            max_length=5,
            pattern=r'^\d{2}/\d{2}$',
            sanitize_html=True,
            prevent_sql_injection=True,
            required=True
        )
        return validator.validate(expiry_date) 

class FileUploadValidator:
    """File upload validation for MINGUS application"""
    
    def __init__(self, max_size_mb: int = 10, allowed_extensions: List[str] = None,
                 allowed_mime_types: List[str] = None):
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions or ['.pdf', '.doc', '.docx', '.txt']
        self.allowed_mime_types = allowed_mime_types or [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
    
    def validate_file(self, file) -> Tuple[bool, Any, List[ValidationError]]:
        """Validate uploaded file"""
        errors = []
        
        if not file or file.filename == '':
            errors.append(ValidationError(
                field="file",
                message="No file selected",
                value=None,
                error_type="no_file"
            ))
            return False, None, errors
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > self.max_size_bytes:
            errors.append(ValidationError(
                field="file",
                message=f"File size must be less than {self.max_size_mb}MB",
                value=file_size,
                error_type="file_too_large"
            ))
        
        # Check file extension
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in self.allowed_extensions:
            errors.append(ValidationError(
                field="file",
                message=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}",
                value=file_ext,
                error_type="invalid_extension"
            ))
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type not in self.allowed_mime_types:
            errors.append(ValidationError(
                field="file",
                message=f"File MIME type not allowed: {mime_type}",
                value=mime_type,
                error_type="invalid_mime_type"
            ))
        
        # Check for malicious content
        if self._contains_malicious_content(file):
            errors.append(ValidationError(
                field="file",
                message="File contains potentially malicious content",
                value=filename,
                error_type="malicious_content"
            ))
        
        return len(errors) == 0, file, errors
    
    def _contains_malicious_content(self, file) -> bool:
        """Check for malicious content in file"""
        try:
            # Read first 1KB to check for script content
            content = file.read(1024).decode('utf-8', errors='ignore').lower()
            file.seek(0)  # Reset to beginning
            
            malicious_patterns = [
                r'<script',
                r'javascript:',
                r'vbscript:',
                r'onload=',
                r'onerror=',
                r'<iframe',
                r'<object',
                r'<embed'
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, content):
                    return True
            
            return False
        except Exception:
            return True  # Assume malicious if we can't read the file

class ValidationManager:
    """Main validation manager for MINGUS application"""
    
    def __init__(self):
        self.validators = {}
        self.validation_log = []
    
    def add_validator(self, field_name: str, validator: BaseValidator):
        """Add validator for a field"""
        self.validators[field_name] = validator
        return self
    
    def validate_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate entire data dictionary"""
        cleaned_data = {}
        errors = []
        warnings = []
        
        for field_name, validator in self.validators.items():
            value = data.get(field_name)
            is_valid, cleaned_value, field_errors = validator.validate(value)
            
            if is_valid:
                cleaned_data[field_name] = cleaned_value
            else:
                errors.extend(field_errors)
        
        # Log validation attempt
        self._log_validation(data, cleaned_data, errors, warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            cleaned_data=cleaned_data,
            errors=errors,
            warnings=warnings
        )
    
    def _log_validation(self, original_data: Dict, cleaned_data: Dict, 
                       errors: List[ValidationError], warnings: List[ValidationError]):
        """Log validation attempt for security monitoring"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'original_data': {k: str(v)[:100] for k, v in original_data.items()},  # Truncate for logging
            'cleaned_data': {k: str(v)[:100] for k, v in cleaned_data.items()},
            'error_count': len(errors),
            'warning_count': len(warnings),
            'errors': [{'field': e.field, 'type': e.error_type, 'message': e.message} for e in errors],
            'warnings': [{'field': w.field, 'type': w.error_type, 'message': w.message} for w in warnings]
        }
        
        self.validation_log.append(log_entry)
        
        # Keep only recent logs
        if len(self.validation_log) > 1000:
            self.validation_log = self.validation_log[-1000:]
        
        # Log to system logger
        if errors:
            logger.warning(f"Validation errors: {len(errors)} errors for IP {log_entry['ip_address']}")
        elif warnings:
            logger.info(f"Validation warnings: {len(warnings)} warnings for IP {log_entry['ip_address']}")
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics for monitoring"""
        if not self.validation_log:
            return {'total_validations': 0, 'error_rate': 0, 'common_errors': []}
        
        total_validations = len(self.validation_log)
        total_errors = sum(entry['error_count'] for entry in self.validation_log)
        error_rate = (total_errors / total_validations) * 100 if total_validations > 0 else 0
        
        # Get common error types
        error_types = {}
        for entry in self.validation_log:
            for error in entry['errors']:
                error_type = error['type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        common_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_validations': total_validations,
            'error_rate': error_rate,
            'common_errors': common_errors,
            'recent_errors': self.validation_log[-10:] if self.validation_log else []
        }

def validate_request_data(validators: Dict[str, BaseValidator]):
    """Decorator to validate request data"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            # Get data from request
            if request.is_json:
                data = request.get_json() or {}
            elif request.form:
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()
            
            # Create validation manager
            manager = ValidationManager()
            for field_name, validator in validators.items():
                manager.add_validator(field_name, validator)
            
            # Validate data
            result = manager.validate_data(data)
            
            if not result.is_valid:
                # Return validation errors
                error_response = {
                    'error': 'Validation failed',
                    'message': 'Please check your input and try again',
                    'validation_errors': [
                        {
                            'field': error.field,
                            'message': error.message,
                            'type': error.error_type
                        }
                        for error in result.errors
                    ]
                }
                
                if result.warnings:
                    error_response['warnings'] = [
                        {
                            'field': warning.field,
                            'message': warning.message,
                            'type': warning.error_type
                        }
                        for warning in result.warnings
                    ]
                
                return jsonify(error_response), 400
            
            # Add cleaned data to request context
            g.validated_data = result.cleaned_data
            g.validation_warnings = result.warnings
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_financial_data():
    """Decorator for financial data validation"""
    validators = {
        'income': NumberValidator('income', min_value=0, max_value=10000000, precision=2),
        'expenses': NumberValidator('expenses', min_value=0, max_value=1000000, precision=2),
        'amount': NumberValidator('amount', min_value=0, max_value=1000000, precision=2),
        'percentage': NumberValidator('percentage', min_value=0, max_value=100, precision=2)
    }
    return validate_request_data(validators)

def validate_health_data():
    """Decorator for health data validation"""
    validators = {
        'stress_level': NumberValidator('stress_level', min_value=1, max_value=10, precision=0),
        'activity_minutes': NumberValidator('activity_minutes', min_value=0, max_value=1440, precision=0),
        'health_score': NumberValidator('health_score', min_value=0, max_value=100, precision=1),
        'mindfulness_minutes': NumberValidator('mindfulness_minutes', min_value=0, max_value=480, precision=0)
    }
    return validate_request_data(validators)

def validate_personal_info():
    """Decorator for personal information validation"""
    validators = {
        'first_name': StringValidator('first_name', min_length=1, max_length=50, pattern=r'^[a-zA-Z\s\-\'\.]+$'),
        'last_name': StringValidator('last_name', min_length=1, max_length=50, pattern=r'^[a-zA-Z\s\-\'\.]+$'),
        'email': StringValidator('email', min_length=5, max_length=254, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'phone': StringValidator('phone', min_length=10, max_length=15, pattern=r'^\d{10,15}$'),
        'address': StringValidator('address', min_length=5, max_length=200),
        'zip_code': StringValidator('zip_code', min_length=5, max_length=10, pattern=r'^\d{5}(-\d{4})?$')
    }
    return validate_request_data(validators)

def validate_employment_data():
    """Decorator for employment data validation"""
    validators = {
        'job_title': StringValidator('job_title', min_length=2, max_length=100, pattern=r'^[a-zA-Z\s\-\'\.\,\&]+$'),
        'industry': StringValidator('industry', min_length=2, max_length=100, pattern=r'^[a-zA-Z\s\-\'\.\,\&]+$'),
        'company_name': StringValidator('company_name', min_length=2, max_length=100, pattern=r'^[a-zA-Z0-9\s\-\'\.\,\&]+$'),
        'years_experience': NumberValidator('years_experience', min_value=0, max_value=50, precision=1)
    }
    return validate_request_data(validators)

def validate_subscription_data():
    """Decorator for subscription data validation"""
    validators = {
        'plan_type': StringValidator('plan_type', min_length=1, max_length=20),
        'billing_amount': NumberValidator('billing_amount', min_value=0, max_value=1000, precision=2),
        'card_number': StringValidator('card_number', min_length=13, max_length=19, pattern=r'^[\d\*\-]+$'),
        'expiry_date': StringValidator('expiry_date', min_length=5, max_length=5, pattern=r'^\d{2}/\d{2}$')
    }
    return validate_request_data(validators)

def validate_file_upload(max_size_mb: int = 10, allowed_extensions: List[str] = None):
    """Decorator for file upload validation"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({
                    'error': 'No file provided',
                    'message': 'Please select a file to upload'
                }), 400
            
            file = request.files['file']
            validator = FileUploadValidator(max_size_mb, allowed_extensions)
            
            is_valid, cleaned_file, errors = validator.validate_file(file)
            
            if not is_valid:
                error_response = {
                    'error': 'File validation failed',
                    'message': 'Please check your file and try again',
                    'validation_errors': [
                        {
                            'field': error.field,
                            'message': error.message,
                            'type': error.error_type
                        }
                        for error in errors
                    ]
                }
                return jsonify(error_response), 400
            
            # Add validated file to request context
            g.validated_file = cleaned_file
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Example usage functions
def create_financial_validator() -> ValidationManager:
    """Create validator for financial data"""
    manager = ValidationManager()
    
    manager.add_validator('income', NumberValidator('income', min_value=0, max_value=10000000, precision=2))
    manager.add_validator('expenses', NumberValidator('expenses', min_value=0, max_value=1000000, precision=2))
    manager.add_validator('amount', NumberValidator('amount', min_value=0, max_value=1000000, precision=2))
    manager.add_validator('percentage', NumberValidator('percentage', min_value=0, max_value=100, precision=2))
    manager.add_validator('account_number', StringValidator('account_number', min_length=4, max_length=20, pattern=r'^[\d\*\-]+$'))
    manager.add_validator('routing_number', StringValidator('routing_number', min_length=9, max_length=9, pattern=r'^\d{9}$'))
    
    return manager

def create_health_validator() -> ValidationManager:
    """Create validator for health data"""
    manager = ValidationManager()
    
    manager.add_validator('stress_level', NumberValidator('stress_level', min_value=1, max_value=10, precision=0))
    manager.add_validator('activity_minutes', NumberValidator('activity_minutes', min_value=0, max_value=1440, precision=0))
    manager.add_validator('health_score', NumberValidator('health_score', min_value=0, max_value=100, precision=1))
    manager.add_validator('mindfulness_minutes', NumberValidator('mindfulness_minutes', min_value=0, max_value=480, precision=0))
    manager.add_validator('sleep_hours', NumberValidator('sleep_hours', min_value=0, max_value=24, precision=1))
    manager.add_validator('water_intake', NumberValidator('water_intake', min_value=0, max_value=10, precision=1))
    
    return manager

def create_personal_info_validator() -> ValidationManager:
    """Create validator for personal information"""
    manager = ValidationManager()
    
    manager.add_validator('first_name', StringValidator('first_name', min_length=1, max_length=50, pattern=r'^[a-zA-Z\s\-\'\.]+$'))
    manager.add_validator('last_name', StringValidator('last_name', min_length=1, max_length=50, pattern=r'^[a-zA-Z\s\-\'\.]+$'))
    manager.add_validator('email', StringValidator('email', min_length=5, max_length=254, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'))
    manager.add_validator('phone', StringValidator('phone', min_length=10, max_length=15, pattern=r'^\d{10,15}$'))
    manager.add_validator('address', StringValidator('address', min_length=5, max_length=200))
    manager.add_validator('city', StringValidator('city', min_length=1, max_length=100))
    manager.add_validator('state', StringValidator('state', min_length=2, max_length=2, pattern=r'^[A-Z]{2}$'))
    manager.add_validator('zip_code', StringValidator('zip_code', min_length=5, max_length=10, pattern=r'^\d{5}(-\d{4})?$'))
    
    return manager

def create_employment_validator() -> ValidationManager:
    """Create validator for employment data"""
    manager = ValidationManager()
    
    manager.add_validator('job_title', StringValidator('job_title', min_length=2, max_length=100, pattern=r'^[a-zA-Z\s\-\'\.\,\&]+$'))
    manager.add_validator('industry', StringValidator('industry', min_length=2, max_length=100, pattern=r'^[a-zA-Z\s\-\'\.\,\&]+$'))
    manager.add_validator('company_name', StringValidator('company_name', min_length=2, max_length=100, pattern=r'^[a-zA-Z0-9\s\-\'\.\,\&]+$'))
    manager.add_validator('years_experience', NumberValidator('years_experience', min_value=0, max_value=50, precision=1))
    manager.add_validator('salary', NumberValidator('salary', min_value=0, max_value=10000000, precision=0))
    manager.add_validator('department', StringValidator('department', min_length=2, max_length=100, pattern=r'^[a-zA-Z\s\-\'\.\,\&]+$'))
    
    return manager

def create_subscription_validator() -> ValidationManager:
    """Create validator for subscription data"""
    manager = ValidationManager()
    
    manager.add_validator('plan_type', StringValidator('plan_type', min_length=1, max_length=20))
    manager.add_validator('billing_amount', NumberValidator('billing_amount', min_value=0, max_value=1000, precision=2))
    manager.add_validator('card_number', StringValidator('card_number', min_length=13, max_length=19, pattern=r'^[\d\*\-]+$'))
    manager.add_validator('expiry_date', StringValidator('expiry_date', min_length=5, max_length=5, pattern=r'^\d{2}/\d{2}$'))
    manager.add_validator('cvv', StringValidator('cvv', min_length=3, max_length=4, pattern=r'^\d{3,4}$'))
    manager.add_validator('billing_address', StringValidator('billing_address', min_length=5, max_length=200))
    
    return manager 