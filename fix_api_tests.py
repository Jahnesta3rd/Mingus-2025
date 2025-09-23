#!/usr/bin/env python3
"""
Script to fix API authentication issues in test_daily_outlook.py
"""

import re

def fix_api_tests():
    """Fix all API endpoint tests by adding authentication decorator mocking"""
    
    # Read the test file
    with open('tests/test_daily_outlook.py', 'r') as f:
        content = f.read()
    
    # Pattern to find API tests that need fixing
    # Look for tests that have patch('backend.api.daily_outlook_api.get_current_user_id')
    # but don't have patch('backend.auth.decorators.require_auth')
    
    # Find all test methods in TestAPIEndpointResponses and TestDataValidation classes
    api_test_pattern = r'(class TestAPIEndpointResponses.*?class TestCacheFunctionality)'
    data_validation_pattern = r'(class TestDataValidation.*?class TestRelationshipStatusUpdates)'
    
    # Fix API endpoint tests
    def fix_api_test_method(match):
        test_content = match.group(0)
        
        # Add auth decorator mocking to tests that don't have it
        if 'patch(\'backend.api.daily_outlook_api.get_current_user_id\')' in test_content and \
           'patch(\'backend.auth.decorators.require_auth\')' not in test_content:
            
            # Add the auth decorator patch at the beginning
            test_content = test_content.replace(
                'with patch(\'backend.api.daily_outlook_api.get_current_user_id\'',
                'with patch(\'backend.auth.decorators.require_auth\', side_effect=lambda f: f):\n            with patch(\'backend.api.daily_outlook_api.get_current_user_id\''
            )
            
            # Fix indentation
            lines = test_content.split('\n')
            fixed_lines = []
            for line in lines:
                if line.strip().startswith('with patch(\'backend.api.daily_outlook_api') and '            ' not in line:
                    fixed_lines.append('            ' + line)
                else:
                    fixed_lines.append(line)
            
            test_content = '\n'.join(fixed_lines)
        
        return test_content
    
    # Apply fixes
    content = re.sub(api_test_pattern, fix_api_test_method, content, flags=re.DOTALL)
    content = re.sub(data_validation_pattern, fix_api_test_method, content, flags=re.DOTALL)
    
    # Write the fixed content back
    with open('tests/test_daily_outlook.py', 'w') as f:
        f.write(content)
    
    print("API tests fixed successfully!")

if __name__ == "__main__":
    fix_api_tests()
