#!/usr/bin/env python3
"""
Test script to verify CSP headers are being applied correctly
"""

import requests
import json
from urllib.parse import urljoin

def test_csp_headers():
    """Test CSP headers on the Flask application"""
    
    base_url = "http://localhost:5003"
    
    print("🔒 Testing Content Security Policy Headers")
    print("=" * 50)
    
    try:
        # Test main page
        print(f"\n📄 Testing main page: {base_url}/")
        response = requests.get(base_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        
        # Check CSP headers
        csp_header = response.headers.get('Content-Security-Policy')
        csp_report_only = response.headers.get('Content-Security-Policy-Report-Only')
        x_csp_header = response.headers.get('X-Content-Security-Policy')
        
        print(f"\n🔒 CSP Headers:")
        print(f"Content-Security-Policy: {'✅ Set' if csp_header else '❌ Not set'}")
        print(f"Content-Security-Policy-Report-Only: {'✅ Set' if csp_report_only else '❌ Not set'}")
        print(f"X-Content-Security-Policy: {'✅ Set' if x_csp_header else '❌ Not set'}")
        
        if csp_header:
            print(f"\n📋 CSP Policy Content:")
            print(csp_header)
            
            # Parse and display CSP directives
            directives = {}
            for directive in csp_header.split(';'):
                directive = directive.strip()
                if directive:
                    if ' ' in directive:
                        key, values = directive.split(' ', 1)
                        directives[key] = values.split(' ')
                    else:
                        directives[directive] = []
            
            print(f"\n🔍 Parsed CSP Directives:")
            for directive, sources in directives.items():
                print(f"  {directive}: {', '.join(sources)}")
        
        # Test static CSS file
        print(f"\n🎨 Testing static CSS file: {base_url}/static/css/touch_target_optimization.css")
        css_response = requests.get(f"{base_url}/static/css/touch_target_optimization.css", timeout=10)
        
        print(f"CSS Status Code: {css_response.status_code}")
        css_csp_header = css_response.headers.get('Content-Security-Policy')
        print(f"CSS CSP Header: {'✅ Set' if css_csp_header else '❌ Not set'}")
        
        # Test other security headers
        print(f"\n🛡️ Other Security Headers:")
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        for header in security_headers:
            value = response.headers.get(header)
            print(f"  {header}: {'✅ ' + value if value else '❌ Not set'}")
        
        # Test CSP validation
        print(f"\n✅ CSP Implementation Status:")
        if csp_header and csp_report_only:
            print("  ✅ CSP headers are properly set")
            print("  ✅ Report-only mode enabled for development")
        elif csp_header:
            print("  ✅ CSP headers are set")
            print("  ⚠️  Report-only mode not enabled")
        else:
            print("  ❌ CSP headers are not set")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask application. Make sure it's running on port 5003.")
        return False
    except Exception as e:
        print(f"❌ Error testing CSP headers: {str(e)}")
        return False

def test_csp_violations():
    """Test potential CSP violations"""
    
    base_url = "http://localhost:5003"
    
    print(f"\n🧪 Testing Potential CSP Violations")
    print("=" * 50)
    
    try:
        # Test inline script (should be blocked by CSP)
        print(f"\n📝 Testing inline script handling...")
        
        # Get the page content to check for inline scripts
        response = requests.get(base_url, timeout=10)
        content = response.text
        
        # Check for inline scripts
        inline_scripts = content.count('<script>') + content.count('<script ')
        inline_styles = content.count('<style>') + content.count('<style ')
        
        print(f"  Inline scripts found: {inline_scripts}")
        print(f"  Inline styles found: {inline_styles}")
        
        if inline_scripts > 0 or inline_styles > 0:
            print("  ⚠️  Inline scripts/styles detected - CSP may need nonce support")
        else:
            print("  ✅ No inline scripts/styles detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing CSP violations: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting CSP Header Testing")
    print("=" * 50)
    
    # Test CSP headers
    success = test_csp_headers()
    
    if success:
        # Test CSP violations
        test_csp_violations()
        
        print(f"\n🎯 CSP Testing Complete!")
        print("\n📚 Next Steps:")
        print("  1. Check browser console for CSP violations")
        print("  2. Monitor CSP reports if report-uri is configured")
        print("  3. Adjust CSP directives based on application needs")
        print("  4. Consider adding nonce support for inline scripts/styles")
    else:
        print(f"\n❌ CSP Testing Failed!")
        print("Please ensure your Flask application is running and CSP middleware is properly configured.")
