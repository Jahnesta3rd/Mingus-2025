#!/usr/bin/env python3
"""
Test script for Step 1: Mac Email URL Extractor setup verification

This script tests the installation and basic functionality without connecting to email.
"""

import sys
import os
import importlib
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing module imports...")
    
    required_modules = [
        'imaplib',
        'email',
        'ssl',
        'urllib.parse',
        'requests',
        'tqdm',
        'json',
        'csv',
        'logging',
        'getpass',
        'time',
        're',
        'dataclasses',
        'pathlib',
        'collections'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Please install missing dependencies:")
        print("pip install -r requirements_step1.txt")
        return False
    else:
        print("\n✅ All required modules imported successfully")
        return True

def test_directory_structure():
    """Test that required directories can be created"""
    print("\nTesting directory structure...")
    
    required_dirs = ['data', 'logs']
    
    for directory in required_dirs:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"  ✅ Created/verified directory: {directory}")
        except Exception as e:
            print(f"  ❌ Failed to create directory {directory}: {e}")
            return False
    
    print("✅ Directory structure ready")
    return True

def test_url_processing():
    """Test URL processing functionality"""
    print("\nTesting URL processing...")
    
    try:
        from urllib.parse import urlparse, parse_qs, urlencode
        import re
        
        # Test URL patterns
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
        ]
        
        test_urls = [
            "https://example.com",
            "http://test.com/path?param=value",
            "www.example.com",
            "https://bit.ly/abc123",
            "https://news.bloomberg.com/article?utm_source=email"
        ]
        
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in url_patterns]
        
        extracted_urls = []
        for pattern in compiled_patterns:
            for url in test_urls:
                matches = pattern.findall(url)
                extracted_urls.extend(matches)
        
        # Test URL cleaning
        test_url = "https://example.com?utm_source=email&utm_medium=newsletter&param=value"
        parsed = urlparse(test_url)
        query_params = parse_qs(parsed.query)
        
        # Remove tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign']
        cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
        cleaned_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
        
        print(f"  ✅ URL pattern matching: {len(extracted_urls)} URLs extracted")
        print(f"  ✅ URL cleaning: {len(cleaned_params)} params after cleaning")
        
        return True
        
    except Exception as e:
        print(f"  ❌ URL processing test failed: {e}")
        return False

def test_domain_categorization():
    """Test domain categorization functionality"""
    print("\nTesting domain categorization...")
    
    try:
        domain_categories = {
            'financial': ['bank', 'credit', 'loan', 'mortgage', 'investment', 'trading', 'finance', 'wealth', 'money'],
            'news_media': ['news', 'times', 'post', 'journal', 'tribune', 'herald', 'press', 'media', 'reuters', 'bloomberg'],
            'educational': ['.edu', 'university', 'college', 'school', 'academy', 'institute', 'course', 'learning'],
            'career': ['linkedin', 'indeed', 'glassdoor', 'monster', 'career', 'job', 'employment', 'professional'],
            'social_media': ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'snapchat'],
            'ecommerce': ['amazon', 'ebay', 'shop', 'store', 'buy', 'purchase', 'retail', 'marketplace'],
            'government': ['.gov', 'government', 'federal', 'state', 'city', 'official'],
            'blog_platform': ['wordpress', 'blogger', 'medium', 'substack', 'ghost', 'blog'],
        }
        
        test_domains = [
            'bloomberg.com',
            'linkedin.com',
            'harvard.edu',
            'amazon.com',
            'whitehouse.gov',
            'medium.com',
            'unknown-site.com'
        ]
        
        categorized = 0
        for domain in test_domains:
            domain_lower = domain.lower()
            for category, keywords in domain_categories.items():
                for keyword in keywords:
                    if keyword in domain_lower:
                        categorized += 1
                        break
        
        print(f"  ✅ Domain categorization: {categorized}/{len(test_domains)} domains categorized")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Domain categorization test failed: {e}")
        return False

def test_file_operations():
    """Test file writing operations"""
    print("\nTesting file operations...")
    
    try:
        import json
        import csv
        
        # Test JSON writing
        test_data = {
            "test": "data",
            "numbers": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        with open('data/test_output.json', 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Test CSV writing
        test_rows = [
            {'name': 'Test1', 'value': 100},
            {'name': 'Test2', 'value': 200}
        ]
        
        with open('data/test_output.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'value']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_rows)
        
        # Clean up test files
        os.remove('data/test_output.json')
        os.remove('data/test_output.csv')
        
        print("  ✅ JSON file operations")
        print("  ✅ CSV file operations")
        
        return True
        
    except Exception as e:
        print(f"  ❌ File operations test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable handling"""
    print("\nTesting environment variable handling...")
    
    try:
        # Test environment variable reading
        test_email = os.getenv('MAC_EMAIL')
        test_password = os.getenv('MAC_APP_PASSWORD')
        
        if test_email:
            print(f"  ✅ MAC_EMAIL found: {test_email[:10]}...")
        else:
            print("  ℹ️  MAC_EMAIL not set (will prompt during execution)")
        
        if test_password:
            print(f"  ✅ MAC_APP_PASSWORD found: {test_password[:10]}...")
        else:
            print("  ℹ️  MAC_APP_PASSWORD not set (will prompt during execution)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Environment variable test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Step 1: Mac Email URL Extractor - Setup Verification")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_directory_structure,
        test_url_processing,
        test_domain_categorization,
        test_file_operations,
        test_environment_variables
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Your setup is ready for Step 1.")
        print("\nNext steps:")
        print("1. Set up your app-specific password (see README_step1.md)")
        print("2. Run: python scripts/step1_mac_email_extractor.py")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Install dependencies: pip install -r requirements_step1.txt")
        print("2. Check Python version (3.7+ required)")
        print("3. Verify file permissions")
        return 1

if __name__ == "__main__":
    sys.exit(main())
