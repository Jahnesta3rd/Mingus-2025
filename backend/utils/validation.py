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
        
        if len(email) > 254:
            return False, "Email is too long"
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
        
        return len(errors) == 0, errors, sanitized_data