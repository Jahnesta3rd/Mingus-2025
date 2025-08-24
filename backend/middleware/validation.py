"""
Validation Middleware
Comprehensive request validation with schema validation and input sanitization
"""

import re
import logging
from functools import wraps
from typing import Dict, Any, List, Optional, Union, Callable
from flask import request, jsonify, g
import html
import json

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(message)

class Validator:
    """Base validator class"""
    
    def __init__(self, required: bool = False, **kwargs):
        self.required = required
        self.kwargs = kwargs
    
    def validate(self, value: Any, field_name: str) -> Any:
        """Validate a single value"""
        # Check if required
        if self.required and (value is None or value == ''):
            raise ValidationError(field_name, f"{field_name} is required")
        
        # Skip validation if not required and empty
        if not self.required and (value is None or value == ''):
            return value
        
        return self._validate(value, field_name)
    
    def _validate(self, value: Any, field_name: str) -> Any:
        """Override this method in subclasses"""
        return value

class StringValidator(Validator):
    """String field validator"""
    
    def _validate(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(field_name, f"{field_name} must be a string")
        
        value = value.strip()
        
        # Check min length
        min_length = self.kwargs.get('min_length')
        if min_length and len(value) < min_length:
            raise ValidationError(field_name, f"{field_name} must be at least {min_length} characters")
        
        # Check max length
        max_length = self.kwargs.get('max_length')
        if max_length and len(value) > max_length:
            raise ValidationError(field_name, f"{field_name} must be no more than {max_length} characters")
        
        # Check pattern
        pattern = self.kwargs.get('pattern')
        if pattern and not re.match(pattern, value):
            raise ValidationError(field_name, f"{field_name} format is invalid")
        
        return value

class EmailValidator(StringValidator):
    """Email field validator"""
    
    def __init__(self, required: bool = False, **kwargs):
        super().__init__(required, **kwargs)
        self.kwargs['pattern'] = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

class PasswordValidator(StringValidator):
    """Password field validator"""
    
    def __init__(self, required: bool = False, **kwargs):
        super().__init__(required, **kwargs)
        # Default password pattern: at least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
        self.kwargs['pattern'] = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
        self.kwargs['min_length'] = 8

class IntegerValidator(Validator):
    """Integer field validator"""
    
    def _validate(self, value: Any, field_name: str) -> int:
        try:
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                raise ValidationError(field_name, f"{field_name} must be an integer")
        except (ValueError, TypeError):
            raise ValidationError(field_name, f"{field_name} must be a valid integer")
        
        # Check min value
        min_value = self.kwargs.get('min_value')
        if min_value is not None and value < min_value:
            raise ValidationError(field_name, f"{field_name} must be at least {min_value}")
        
        # Check max value
        max_value = self.kwargs.get('max_value')
        if max_value is not None and value > max_value:
            raise ValidationError(field_name, f"{field_name} must be no more than {max_value}")
        
        return value

class FloatValidator(Validator):
    """Float field validator"""
    
    def _validate(self, value: Any, field_name: str) -> float:
        try:
            if isinstance(value, str):
                value = float(value)
            elif not isinstance(value, (int, float)):
                raise ValidationError(field_name, f"{field_name} must be a number")
        except (ValueError, TypeError):
            raise ValidationError(field_name, f"{field_name} must be a valid number")
        
        # Check min value
        min_value = self.kwargs.get('min_value')
        if min_value is not None and value < min_value:
            raise ValidationError(field_name, f"{field_name} must be at least {min_value}")
        
        # Check max value
        max_value = self.kwargs.get('max_value')
        if max_value is not None and value > max_value:
            raise ValidationError(field_name, f"{field_name} must be no more than {max_value}")
        
        return value

class BooleanValidator(Validator):
    """Boolean field validator"""
    
    def _validate(self, value: Any, field_name: str) -> bool:
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
            else:
                raise ValidationError(field_name, f"{field_name} must be a boolean value")
        elif isinstance(value, int):
            return bool(value)
        else:
            raise ValidationError(field_name, f"{field_name} must be a boolean value")

class ListValidator(Validator):
    """List field validator"""
    
    def _validate(self, value: Any, field_name: str) -> List:
        if not isinstance(value, list):
            raise ValidationError(field_name, f"{field_name} must be a list")
        
        # Check min length
        min_length = self.kwargs.get('min_length')
        if min_length and len(value) < min_length:
            raise ValidationError(field_name, f"{field_name} must have at least {min_length} items")
        
        # Check max length
        max_length = self.kwargs.get('max_length')
        if max_length and len(value) > max_length:
            raise ValidationError(field_name, f"{field_name} must have no more than {max_length} items")
        
        # Validate list items if item_validator is provided
        item_validator = self.kwargs.get('item_validator')
        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = item_validator.validate(item, f"{field_name}[{i}]")
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(e.field, e.message, e.value)
            return validated_items
        
        return value

class DictValidator(Validator):
    """Dictionary field validator"""
    
    def _validate(self, value: Any, field_name: str) -> Dict:
        if not isinstance(value, dict):
            raise ValidationError(field_name, f"{field_name} must be a dictionary")
        
        # Validate dictionary keys and values if validators are provided
        key_validator = self.kwargs.get('key_validator')
        value_validator = self.kwargs.get('value_validator')
        
        if key_validator or value_validator:
            validated_dict = {}
            for key, val in value.items():
                validated_key = key
                validated_value = val
                
                if key_validator:
                    validated_key = key_validator.validate(key, f"{field_name}.key")
                
                if value_validator:
                    validated_value = value_validator.validate(val, f"{field_name}.{key}")
                
                validated_dict[validated_key] = validated_value
            
            return validated_dict
        
        return value

class EnumValidator(Validator):
    """Enum field validator"""
    
    def __init__(self, allowed_values: List[Any], required: bool = False, **kwargs):
        super().__init__(required, **kwargs)
        self.allowed_values = allowed_values
    
    def _validate(self, value: Any, field_name: str) -> Any:
        if value not in self.allowed_values:
            allowed_str = ', '.join(str(v) for v in self.allowed_values)
            raise ValidationError(field_name, f"{field_name} must be one of: {allowed_str}")
        return value

class PhoneValidator(StringValidator):
    """Phone number validator"""
    
    def __init__(self, required: bool = False, **kwargs):
        super().__init__(required, **kwargs)
        self.kwargs['pattern'] = r'^\+?[\d\s\-\(\)]{10,}$'

class URLValidator(StringValidator):
    """URL validator"""
    
    def __init__(self, required: bool = False, **kwargs):
        super().__init__(required, **kwargs)
        self.kwargs['pattern'] = r'^https?://[^\s/$.?#].[^\s]*$'

class DateValidator(Validator):
    """Date validator"""
    
    def _validate(self, value: Any, field_name: str) -> str:
        if isinstance(value, str):
            # Try to parse ISO format date
            try:
                from datetime import datetime
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return value
            except ValueError:
                raise ValidationError(field_name, f"{field_name} must be a valid ISO date format")
        else:
            raise ValidationError(field_name, f"{field_name} must be a string in ISO date format")

def sanitize_input(value: Any) -> Any:
    """Sanitize input to prevent XSS and injection attacks"""
    if isinstance(value, str):
        # HTML escape to prevent XSS
        value = html.escape(value)
        # Remove null bytes
        value = value.replace('\x00', '')
        # Remove control characters except newlines and tabs
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    elif isinstance(value, dict):
        return {sanitize_input(k): sanitize_input(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_input(item) for item in value]
    
    return value

def validate_request(schema: Dict[str, Any]):
    """
    Request validation decorator
    
    Args:
        schema: Dictionary mapping field names to validators or validation rules
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get data from request
                if request.is_json:
                    data = request.get_json() or {}
                elif request.form:
                    data = request.form.to_dict()
                else:
                    data = request.args.to_dict()
                
                # Sanitize input
                data = sanitize_input(data)
                
                # Validate data
                validated_data = {}
                errors = []
                
                for field_name, validator_config in schema.items():
                    try:
                        # Create validator from config
                        if isinstance(validator_config, dict):
                            validator_type = validator_config.pop('type', 'string')
                            required = validator_config.pop('required', False)
                            
                            # Create appropriate validator
                            if validator_type == 'string':
                                validator = StringValidator(required, **validator_config)
                            elif validator_type == 'email':
                                validator = EmailValidator(required, **validator_config)
                            elif validator_type == 'password':
                                validator = PasswordValidator(required, **validator_config)
                            elif validator_type == 'integer':
                                validator = IntegerValidator(required, **validator_config)
                            elif validator_type == 'float':
                                validator = FloatValidator(required, **validator_config)
                            elif validator_type == 'boolean':
                                validator = BooleanValidator(required, **validator_config)
                            elif validator_type == 'list':
                                validator = ListValidator(required, **validator_config)
                            elif validator_type == 'dict':
                                validator = DictValidator(required, **validator_config)
                            elif validator_type == 'enum':
                                allowed_values = validator_config.pop('values', [])
                                validator = EnumValidator(allowed_values, required, **validator_config)
                            elif validator_type == 'phone':
                                validator = PhoneValidator(required, **validator_config)
                            elif validator_type == 'url':
                                validator = URLValidator(required, **validator_config)
                            elif validator_type == 'date':
                                validator = DateValidator(required, **validator_config)
                            else:
                                raise ValueError(f"Unknown validator type: {validator_type}")
                        else:
                            validator = validator_config
                        
                        # Validate field
                        value = data.get(field_name)
                        validated_value = validator.validate(value, field_name)
                        validated_data[field_name] = validated_value
                        
                    except ValidationError as e:
                        errors.append({
                            'field': e.field,
                            'message': e.message,
                            'value': e.value
                        })
                
                if errors:
                    return jsonify({
                        'error': 'Validation failed',
                        'message': 'Please check your input and try again',
                        'validation_errors': errors
                    }), 400
                
                # Add validated data to request context
                g.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Validation error: {str(e)}")
                return jsonify({
                    'error': 'Validation error',
                    'message': 'An error occurred during validation'
                }), 500
        
        return decorated_function
    return decorator

# Common validation schemas
COMMON_SCHEMAS = {
    'email': {
        'type': 'email',
        'required': True,
        'max_length': 255
    },
    'password': {
        'type': 'password',
        'required': True,
        'min_length': 8,
        'max_length': 128
    },
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 2,
        'max_length': 100
    },
    'phone': {
        'type': 'phone',
        'required': False
    },
    'url': {
        'type': 'url',
        'required': False
    },
    'integer_id': {
        'type': 'integer',
        'required': True,
        'min_value': 1
    },
    'positive_float': {
        'type': 'float',
        'required': True,
        'min_value': 0.0
    },
    'boolean_flag': {
        'type': 'boolean',
        'required': False
    }
}

def get_common_schema(*field_names: str) -> Dict[str, Any]:
    """Get common validation schema for specified fields"""
    return {field: COMMON_SCHEMAS[field] for field in field_names if field in COMMON_SCHEMAS} 