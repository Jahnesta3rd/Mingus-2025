import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class APIValidator:
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email address"""
        if not email or not isinstance(email, str):
            return False, "Email is required and must be a string"
        
        # Length validation FIRST (before regex processing to prevent DoS)
        # Check maximum length early to reject extremely long strings immediately
        if len(email) > 254:
            return False, "Email is too long (maximum 254 characters)"
        if len(email) < 3:
            return False, "Email is too short (minimum 3 characters)"
        
        # Now validate format (regex is safe now that we've checked length)
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        """Validate name field"""
        if not name or not isinstance(name, str):
            return False, "Name is required and must be a string"
        
        # Length validation FIRST (before regex processing to prevent DoS)
        # Check maximum length early to reject extremely long strings immediately
        if len(name) > 100:
            return False, "Name is too long (maximum 100 characters)"
        if len(name) < 1:
            return False, "Name is too short (minimum 1 character)"
        
        # Check for potentially malicious content (safe now that length is checked)
        if re.search(r'<script|javascript:|on\w+\s*=', name, re.IGNORECASE):
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
        digits_only = re.sub(r'\D', '', phone)
        
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
        if not isinstance(answers, dict):
            return False, "Answers must be a dictionary"
        
        # Empty dictionary is valid
        if len(answers) == 0:
            return True, ""
        
        # Check for excessive data size
        try:
            json_string = json.dumps(answers)
            if len(json_string) > 10000:
                return False, "Assessment answers are too large (maximum 10KB)"
        except (TypeError, ValueError):
            return False, "Answers contain invalid data that cannot be serialized"
        
        # Validate each answer
        for key, value in answers.items():
            if not isinstance(key, str):
                return False, f"Answer key must be a string, got {type(key).__name__}"
            if len(key) > 100:
                return False, f"Answer key '{key[:20]}...' is too long (maximum 100 characters)"
            if len(key) == 0:
                return False, "Answer key cannot be empty"
            
            # Validate answer value
            if isinstance(value, str):
                if len(value) > 1000:
                    return False, f"Answer for '{key}' is too long (maximum 1000 characters)"
            elif isinstance(value, (int, float, bool)):
                # Numeric and boolean values are OK
                pass
            elif isinstance(value, list):
                # Arrays are OK but check size
                if len(value) > 100:
                    return False, f"Answer for '{key}' contains too many items (maximum 100)"
            elif isinstance(value, dict):
                # Nested objects are OK but check depth
                nested_json = json.dumps(value)
                if len(nested_json) > 5000:
                    return False, f"Answer for '{key}' is too large (maximum 5KB)"
            elif value is None:
                # None values are OK
                pass
            else:
                return False, f"Answer for '{key}' has invalid type: {type(value).__name__}"
        
        return True, ""
    
    @staticmethod
    def sanitize_string(input_str: str) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
        
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
        
        # Type validation first - check that data is a dict
        if not isinstance(data, dict):
            return False, ["Request data must be a dictionary"], {}
        
        # Check for excessive request size
        try:
            json_string = json.dumps(data)
            if len(json_string) > 50000:  # 50KB limit
                return False, ["Request payload is too large (maximum 50KB)"], {}
        except (TypeError, ValueError):
            return False, ["Invalid request data format"], {}
        
        # Validate email - with explicit type checking
        email = data.get('email')
        if email is None:
            errors.append("Email: Email is required")
        elif not isinstance(email, str):
            # Reject wrong types immediately with clear error message
            errors.append(f"Email: Email must be a string, got {type(email).__name__}")
        else:
            # Check length FIRST before calling validate_email (prevents DoS with extremely long strings)
            if len(email) > 254:
                errors.append(f"Email: Email is too long (maximum 254 characters)")
            else:
                is_valid, error = APIValidator.validate_email(email)
                if not is_valid:
                    errors.append(f"Email: {error}")
                else:
                    sanitized_data['email'] = email.lower().strip()
        
        # Validate first name - with explicit type checking
        firstName = data.get('firstName')
        if firstName is None:
            # First name is optional, but if provided must be valid
            pass
        elif not isinstance(firstName, str):
            errors.append(f"First Name: First name must be a string, got {type(firstName).__name__}")
        else:
            # Check length FIRST before calling validate_name (prevents DoS with extremely long strings)
            if len(firstName) > 100:
                errors.append(f"First Name: First name is too long (maximum 100 characters)")
            else:
                is_valid, error = APIValidator.validate_name(firstName)
                if not is_valid:
                    errors.append(f"First Name: {error}")
                else:
                    sanitized_data['firstName'] = APIValidator.sanitize_string(firstName)
        
        # Validate phone (optional) - with explicit type checking
        if 'phone' in data:
            phone = data['phone']
            if phone is not None and not isinstance(phone, str):
                errors.append(f"Phone: Phone must be a string, got {type(phone).__name__}")
            else:
                is_valid, error = APIValidator.validate_phone(phone if phone else '')
                if not is_valid:
                    errors.append(f"Phone: {error}")
                else:
                    sanitized_data['phone'] = APIValidator.sanitize_string(phone) if phone else None
        
        # Validate assessment type - with explicit type checking
        assessmentType = data.get('assessmentType')
        if assessmentType is None:
            errors.append("Assessment Type: Assessment type is required")
        elif not isinstance(assessmentType, str):
            errors.append(f"Assessment Type: Assessment type must be a string, got {type(assessmentType).__name__}")
        else:
            is_valid, error = APIValidator.validate_assessment_type(assessmentType)
            if not is_valid:
                errors.append(f"Assessment Type: {error}")
            else:
                sanitized_data['assessmentType'] = assessmentType
        
        # Validate answers - with explicit type checking
        answers = data.get('answers')
        if answers is None:
            errors.append("Answers: Answers are required")
        elif not isinstance(answers, dict):
            errors.append(f"Answers: Answers must be a dictionary, got {type(answers).__name__}")
        else:
            is_valid, error = APIValidator.validate_answers(answers)
            if not is_valid:
                errors.append(f"Answers: {error}")
            else:
                sanitized_data['answers'] = APIValidator.sanitize_object(answers)
        
        # Optional: client-calculated results (score, risk_level, recommendations, subscores)
        calculated_results = data.get('calculatedResults')
        if calculated_results is not None and isinstance(calculated_results, dict):
            sanitized_data['calculatedResults'] = {
                'score': calculated_results.get('score'),
                'risk_level': calculated_results.get('risk_level'),
                'recommendations': calculated_results.get('recommendations'),
                'subscores': calculated_results.get('subscores')
            }

        # Validate unknown/extra fields (reject fields not in the schema)
        # This helps catch typos and prevents accepting invalid data
        allowed_fields = {'email', 'firstName', 'phone', 'assessmentType', 'answers', 'completedAt', 'calculatedResults'}
        unknown_fields = set(data.keys()) - allowed_fields
        if unknown_fields:
            # Validate unknown fields for basic type and length issues
            for field in unknown_fields:
                value = data[field]
                # Basic validation for unknown fields to prevent abuse
                if isinstance(value, str):
                    if len(value) > 1000:
                        errors.append(f"{field}: Value is too long (maximum 1000 characters)")
                    # Check for obviously malicious content
                    if len(value) > 100 and re.search(r'<script|javascript:|on\w+\s*=', value, re.IGNORECASE):
                        errors.append(f"{field}: Contains potentially malicious content")
                elif isinstance(value, (int, float)):
                    # Reject extreme numeric values that might indicate abuse
                    if abs(value) > 1000000:
                        errors.append(f"{field}: Value is out of acceptable range")
                elif isinstance(value, (list, dict)):
                    # Check size of complex types
                    try:
                        json_size = len(json.dumps(value))
                        if json_size > 5000:
                            errors.append(f"{field}: Value is too large (maximum 5KB)")
                    except (TypeError, ValueError):
                        errors.append(f"{field}: Contains invalid data that cannot be serialized")
        
        # Add timestamp
        if len(errors) == 0:
            sanitized_data['completedAt'] = datetime.now().isoformat()
        
        return len(errors) == 0, errors, sanitized_data