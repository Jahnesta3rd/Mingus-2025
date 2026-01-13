"""
Unit tests for validation utilities
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.utils.validation import APIValidator

class TestEmailValidation:
    """Test email validation"""
    
    def test_valid_email(self):
        """Test valid email addresses"""
        valid_emails = [
            'test@example.com',
            'user.name@example.co.uk',
            'user+tag@example.com',
            'user123@example-domain.com'
        ]
        
        for email in valid_emails:
            is_valid, error = APIValidator.validate_email(email)
            assert is_valid, f"Email {email} should be valid: {error}"
    
    def test_invalid_email_format(self):
        """Test invalid email formats"""
        invalid_emails = [
            'invalid-email',
            'test@',
            '@example.com',
            'test@example',
            'test @example.com'
        ]
        
        for email in invalid_emails:
            is_valid, error = APIValidator.validate_email(email)
            assert not is_valid, f"Email {email} should be invalid"
    
    def test_email_length_limits(self):
        """Test email length validation"""
        # Too short
        is_valid, error = APIValidator.validate_email('a@b')
        assert not is_valid
        
        # Too long
        long_email = 'a' * 250 + '@example.com'
        is_valid, error = APIValidator.validate_email(long_email)
        assert not is_valid
    
    def test_email_type_validation(self):
        """Test email type validation"""
        # Non-string types
        is_valid, error = APIValidator.validate_email(123)
        assert not is_valid
        
        is_valid, error = APIValidator.validate_email([])
        assert not is_valid
        
        is_valid, error = APIValidator.validate_email(None)
        assert not is_valid

class TestNameValidation:
    """Test name validation"""
    
    def test_valid_name(self):
        """Test valid names"""
        valid_names = [
            'John',
            'John Doe',
            "O'Brien",
            'José',
            'Mary-Jane'
        ]
        
        for name in valid_names:
            is_valid, error = APIValidator.validate_name(name)
            assert is_valid, f"Name {name} should be valid: {error}"
    
    def test_invalid_name(self):
        """Test invalid names"""
        # Empty
        is_valid, error = APIValidator.validate_name('')
        assert not is_valid
        
        # Too long
        long_name = 'a' * 101
        is_valid, error = APIValidator.validate_name(long_name)
        assert not is_valid
        
        # Contains script tag
        is_valid, error = APIValidator.validate_name('<script>alert("xss")</script>')
        assert not is_valid
        
        # Contains javascript:
        is_valid, error = APIValidator.validate_name('javascript:alert("xss")')
        assert not is_valid
    
    def test_name_type_validation(self):
        """Test name type validation"""
        # Non-string types
        is_valid, error = APIValidator.validate_name(123)
        assert not is_valid
        
        is_valid, error = APIValidator.validate_name([])
        assert not is_valid
        
        is_valid, error = APIValidator.validate_name(None)
        assert not is_valid

class TestPhoneValidation:
    """Test phone validation"""
    
    def test_valid_phone(self):
        """Test valid phone numbers"""
        valid_phones = [
            '1234567890',
            '(123) 456-7890',
            '123-456-7890',
            '+1 123 456 7890',
            '123.456.7890'
        ]
        
        for phone in valid_phones:
            is_valid, error = APIValidator.validate_phone(phone)
            assert is_valid, f"Phone {phone} should be valid: {error}"
    
    def test_invalid_phone(self):
        """Test invalid phone numbers"""
        invalid_phones = [
            '123',  # Too short
            '1' * 20,  # Too long
            'abc123',  # Not enough digits
        ]
        
        for phone in invalid_phones:
            is_valid, error = APIValidator.validate_phone(phone)
            assert not is_valid, f"Phone {phone} should be invalid"
    
    def test_optional_phone(self):
        """Test that phone is optional"""
        is_valid, error = APIValidator.validate_phone('')
        assert is_valid  # Empty phone should be valid (optional)
        
        is_valid, error = APIValidator.validate_phone(None)
        assert is_valid  # None phone should be valid (optional)

class TestAssessmentTypeValidation:
    """Test assessment type validation"""
    
    def test_valid_assessment_types(self):
        """Test valid assessment types"""
        valid_types = ['ai-risk', 'income-comparison', 'cuffing-season', 'layoff-risk']
        
        for assessment_type in valid_types:
            is_valid, error = APIValidator.validate_assessment_type(assessment_type)
            assert is_valid, f"Assessment type {assessment_type} should be valid: {error}"
    
    def test_invalid_assessment_types(self):
        """Test invalid assessment types"""
        invalid_types = [
            'invalid-type',
            'ai_risk',
            'AI-RISK',
            '',
            None
        ]
        
        for assessment_type in invalid_types:
            is_valid, error = APIValidator.validate_assessment_type(assessment_type)
            assert not is_valid, f"Assessment type {assessment_type} should be invalid"

class TestAnswersValidation:
    """Test answers validation"""
    
    def test_valid_answers(self):
        """Test valid answer dictionaries"""
        valid_answers = [
            {'q1': 'answer1', 'q2': 'answer2'},
            {'q1': 123, 'q2': True},
            {'q1': ['a', 'b', 'c']},
            {'q1': {'nested': 'value'}}
        ]
        
        for answers in valid_answers:
            is_valid, error = APIValidator.validate_answers(answers)
            assert is_valid, f"Answers {answers} should be valid: {error}"
    
    def test_invalid_answers(self):
        """Test invalid answer dictionaries"""
        # Not a dict
        is_valid, error = APIValidator.validate_answers('not a dict')
        assert not is_valid
        
        # Too large
        large_answers = {'q' + str(i): 'a' * 1000 for i in range(20)}
        is_valid, error = APIValidator.validate_answers(large_answers)
        assert not is_valid
        
        # Invalid key type
        is_valid, error = APIValidator.validate_answers({123: 'value'})
        assert not is_valid
        
        # Empty key
        is_valid, error = APIValidator.validate_answers({'': 'value'})
        assert not is_valid
    
    def test_answer_value_limits(self):
        """Test answer value size limits"""
        # String too long
        is_valid, error = APIValidator.validate_answers({'q1': 'a' * 1001})
        assert not is_valid
        
        # Array too large
        is_valid, error = APIValidator.validate_answers({'q1': list(range(101))})
        assert not is_valid
        
        # Nested object too large
        large_nested = {'q1': {'key' + str(i): 'value' * 100 for i in range(100)}}
        is_valid, error = APIValidator.validate_answers(large_nested)
        assert not is_valid

class TestSanitization:
    """Test input sanitization"""
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        # Remove null bytes
        sanitized = APIValidator.sanitize_string('test\x00string')
        assert '\x00' not in sanitized
        
        # Trim whitespace
        sanitized = APIValidator.sanitize_string('  test  ')
        assert sanitized == 'test'
        
        # Limit length
        long_string = 'a' * 2000
        sanitized = APIValidator.sanitize_string(long_string)
        assert len(sanitized) == 1000
    
    def test_sanitize_object(self):
        """Test object sanitization"""
        # String
        result = APIValidator.sanitize_object('test\x00string')
        assert '\x00' not in result
        
        # List
        result = APIValidator.sanitize_object(['test\x00', 'normal'])
        assert '\x00' not in result[0]
        
        # Dict
        result = APIValidator.sanitize_object({'key': 'test\x00value'})
        assert '\x00' not in result['key']
        
        # None
        result = APIValidator.sanitize_object(None)
        assert result is None

class TestAssessmentDataValidation:
    """Test complete assessment data validation"""
    
    def test_valid_assessment_data(self):
        """Test valid complete assessment data"""
        data = {
            'email': 'test@example.com',
            'firstName': 'John',
            'phone': '1234567890',
            'assessmentType': 'ai-risk',
            'answers': {'q1': 'a1', 'q2': 'a2'}
        }
        
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert is_valid, f"Data should be valid: {errors}"
        assert 'email' in sanitized
        assert sanitized['email'] == 'test@example.com'
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        # Missing email
        data = {
            'firstName': 'John',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert not is_valid
        assert any('email' in error.lower() for error in errors)
        
        # Missing assessmentType
        data = {
            'email': 'test@example.com',
            'answers': {}
        }
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert not is_valid
        assert any('assessment' in error.lower() for error in errors)
        
        # Missing answers
        data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk'
        }
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert not is_valid
        assert any('answer' in error.lower() for error in errors)
    
    def test_type_validation(self):
        """Test type validation for assessment data"""
        # Email as integer
        data = {
            'email': 123,
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert not is_valid
        assert any('string' in error.lower() for error in errors)
        
        # Answers as string
        data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk',
            'answers': 'not a dict'
        }
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert not is_valid
    
    def test_length_validation(self):
        """Test length validation for assessment data"""
        # Email too long
        data = {
            'email': 'a' * 255 + '@example.com',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert not is_valid
        
        # Payload too large
        data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk',
            'answers': {'q' + str(i): 'a' * 1000 for i in range(100)}
        }
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        assert not is_valid
    
    def test_unknown_fields(self):
        """Test validation of unknown fields"""
        data = {
            'email': 'test@example.com',
            'assessmentType': 'ai-risk',
            'answers': {},
            'unknownField': 'value'
        }
        # Unknown fields should be validated for basic safety
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(data)
        # Should still validate but check unknown field
        assert 'unknownField' not in sanitized or len(errors) > 0
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_data = {
            'email': "'; DROP TABLE users; --",
            'firstName': "'; DROP TABLE users; --",
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(malicious_data)
        # Should sanitize but may reject due to format
        # The important thing is that it doesn't pass through unsanitized
        if is_valid:
            assert sanitized['email'] != malicious_data['email']
    
    def test_xss_prevention(self):
        """Test XSS prevention"""
        xss_data = {
            'email': 'test@example.com',
            'firstName': '<script>alert("xss")</script>',
            'assessmentType': 'ai-risk',
            'answers': {}
        }
        
        is_valid, errors, sanitized = APIValidator.validate_assessment_data(xss_data)
        # Should reject or sanitize XSS
        if is_valid:
            assert '<script>' not in sanitized['firstName']
        else:
            assert any('malicious' in error.lower() or 'script' in error.lower() for error in errors)
