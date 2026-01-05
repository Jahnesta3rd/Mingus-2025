#!/usr/bin/env python3
"""
Landing Page Fixes Verification Test Suite

This script verifies that all fixes applied to the LandingPage component
are working correctly and that no regressions have been introduced.
"""

import os
import re
import json
import subprocess
from datetime import datetime

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_test(name, status, details=""):
    """Print test result"""
    status_icon = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if status else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"  {status_icon} {name}")
    if details:
        print(f"     {details}")

def check_file_exists(filepath):
    """Check if a file exists"""
    return os.path.exists(filepath)

def read_file_content(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None

def test_file_exists(filepath, description):
    """Test if a file exists"""
    exists = check_file_exists(filepath)
    print_test(description, exists, f"File: {filepath}" if exists else f"Missing: {filepath}")
    return exists

def test_no_console_statements(filepath, description):
    """Test that no console.log/console.error statements exist (except in logger utility)"""
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    # Find console statements (excluding logger utility file)
    console_patterns = [
        r'console\.log\(',
        r'console\.error\(',
        r'console\.warn\(',
        r'console\.debug\('
    ]
    
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern in console_patterns:
            if re.search(pattern, line):
                # Skip if it's in a comment or logger utility
                if 'logger' not in line.lower() and not line.strip().startswith('//'):
                    issues.append(f"Line {i}: {line.strip()[:60]}")
    
    if issues:
        print_test(description, False, f"Found {len(issues)} console statements")
        for issue in issues[:3]:  # Show first 3
            print(f"     - {issue}")
        if len(issues) > 3:
            print(f"     ... and {len(issues) - 3} more")
        return False
    
    print_test(description, True, "No console statements found")
    return True

def test_responsive_test_component_conditional(filepath, description):
    """Test that ResponsiveTestComponent is conditionally rendered"""
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    # Check if ResponsiveTestComponent is conditionally rendered
    has_conditional = (
        'import.meta.env.DEV' in content or 
        'process.env.NODE_ENV' in content or
        'NODE_ENV === \'development\'' in content
    )
    
    # Check if it's used unconditionally
    unconditional_pattern = r'<ResponsiveTestComponent\s*/>'
    has_unconditional = bool(re.search(unconditional_pattern, content))
    
    if has_unconditional and not has_conditional:
        print_test(description, False, "ResponsiveTestComponent used unconditionally")
        return False
    
    if has_conditional:
        print_test(description, True, "ResponsiveTestComponent is conditionally rendered")
        return True
    
    # If not found at all, that's also fine (might have been removed)
    if '<ResponsiveTestComponent' not in content:
        print_test(description, True, "ResponsiveTestComponent not found (removed)")
        return True
    
    print_test(description, False, "Could not verify conditional rendering")
    return False

def test_react_router_usage(filepath, description):
    """Test that navigation uses React Router instead of window.location"""
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    # Check for window.location.href usage
    window_location_pattern = r'window\.location\.href\s*='
    has_window_location = bool(re.search(window_location_pattern, content))
    
    # Check for useNavigate usage
    has_use_navigate = 'useNavigate' in content or 'navigate(' in content
    
    if has_window_location:
        print_test(description, False, "Found window.location.href usage")
        return False
    
    if has_use_navigate:
        print_test(description, True, "Using React Router (useNavigate)")
        return True
    
    print_test(description, False, "Could not verify React Router usage")
    return False

def test_aria_labels(filepath, description):
    """Test that buttons have ARIA labels"""
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    # Count buttons and ARIA labels
    button_pattern = r'<button[^>]*>'
    aria_label_pattern = r'aria-label='
    
    buttons = re.findall(button_pattern, content, re.IGNORECASE)
    aria_labels = re.findall(aria_label_pattern, content, re.IGNORECASE)
    
    # Exclude buttons that have visible text (which is acceptable)
    # This is a simplified check - in reality, we'd need more sophisticated parsing
    button_count = len(buttons)
    aria_count = len(aria_labels)
    
    # At least 50% of buttons should have ARIA labels (some may have visible text)
    if button_count > 0 and aria_count < button_count * 0.5:
        print_test(description, False, f"Only {aria_count}/{button_count} buttons have ARIA labels")
        return False
    
    print_test(description, True, f"Found {aria_count} ARIA labels on {button_count} buttons")
    return True

def test_assessment_type_import(filepath, description):
    """Test that AssessmentType is imported from types/assessments"""
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    # Check for import
    has_import = 'from \'../types/assessments\'' in content or 'from "../../types/assessments"' in content
    has_usage = 'AssessmentType' in content
    
    # Check for inline union types (should not exist)
    inline_union_pattern = r"'ai-risk'\s*\|\s*'income-comparison'"
    has_inline_union = bool(re.search(inline_union_pattern, content))
    
    if has_inline_union:
        print_test(description, False, "Found inline union types (should use AssessmentType)")
        return False
    
    if has_import and has_usage:
        print_test(description, True, "Using AssessmentType from types/assessments")
        return True
    
    print_test(description, False, "Could not verify AssessmentType usage")
    return False

def test_dynamic_copyright_year(filepath, description):
    """Test that copyright year is dynamic"""
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    # Check for hardcoded years
    hardcoded_pattern = r'©\s*202[0-9]'
    has_hardcoded = bool(re.search(hardcoded_pattern, content))
    
    # Check for dynamic year
    has_dynamic = 'getFullYear()' in content or 'new Date().getFullYear()' in content
    
    if has_hardcoded:
        print_test(description, False, "Found hardcoded copyright year")
        return False
    
    if has_dynamic:
        print_test(description, True, "Using dynamic copyright year")
        return True
    
    print_test(description, False, "Could not verify dynamic copyright year")
    return False

def test_analytics_tracking(filepath, description):
    """Test that analytics tracking is implemented"""
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    # Check for useAnalytics import
    has_import = 'useAnalytics' in content or 'from \'../hooks/useAnalytics\'' in content
    has_tracking = 'trackInteraction' in content or 'trackPageView' in content
    
    if has_import and has_tracking:
        print_test(description, True, "Analytics tracking implemented")
        return True
    
    print_test(description, False, "Analytics tracking not found")
    return False

def test_component_splitting(filepath, description):
    """Test that components are split into separate files"""
    sections_dir = os.path.join(os.path.dirname(filepath), 'sections')
    
    required_components = [
        'HeroSection.tsx',
        'AssessmentSection.tsx',
        'FeaturesSection.tsx',
        'PricingSection.tsx',
        'FAQSection.tsx',
        'CTASection.tsx'
    ]
    
    all_exist = True
    missing = []
    
    for component in required_components:
        component_path = os.path.join(sections_dir, component)
        if not check_file_exists(component_path):
            all_exist = False
            missing.append(component)
    
    if not all_exist:
        print_test(description, False, f"Missing components: {', '.join(missing)}")
        return False
    
    # Check if LandingPage imports these components
    content = read_file_content(filepath)
    if not content:
        print_test(description, False, "Could not read file")
        return False
    
    has_imports = all(f'./sections/{comp.replace(".tsx", "")}' in content for comp in required_components)
    
    if has_imports:
        print_test(description, True, f"All {len(required_components)} section components exist and are imported")
        return True
    
    print_test(description, False, "Components exist but may not be imported")
    return False

def test_typescript_compilation():
    """Test TypeScript compilation"""
    print_header("TypeScript Compilation Test")
    
    frontend_dir = os.path.join(os.getcwd(), 'frontend')
    if not os.path.exists(frontend_dir):
        print_test("TypeScript compilation", False, "Frontend directory not found")
        return False
    
    try:
        result = subprocess.run(
            ['npm', 'run', 'type-check'],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_test("TypeScript compilation", True, "No type errors")
            return True
        else:
            print_test("TypeScript compilation", False, "Type errors found")
            print(f"     {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print_test("TypeScript compilation", False, "Compilation timed out")
        return False
    except FileNotFoundError:
        print_test("TypeScript compilation", False, "npm not found - skipping")
        return None
    except Exception as e:
        print_test("TypeScript compilation", False, f"Error: {str(e)}")
        return False

def test_linting():
    """Test ESLint"""
    print_header("Linting Test")
    
    frontend_dir = os.path.join(os.getcwd(), 'frontend')
    if not os.path.exists(frontend_dir):
        print_test("ESLint", False, "Frontend directory not found")
        return False
    
    try:
        result = subprocess.run(
            ['npm', 'run', 'lint'],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_test("ESLint", True, "No linting errors")
            return True
        else:
            print_test("ESLint", False, "Linting errors found")
            print(f"     {result.stdout[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print_test("ESLint", False, "Linting timed out")
        return False
    except FileNotFoundError:
        print_test("ESLint", False, "npm not found - skipping")
        return None
    except Exception as e:
        print_test("ESLint", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all verification tests"""
    print_header("LANDING PAGE FIXES VERIFICATION TEST SUITE")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'summary': {}
    }
    
    # Get file paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    landing_page_path = os.path.join(base_dir, 'frontend', 'src', 'components', 'LandingPage.tsx')
    logger_path = os.path.join(base_dir, 'frontend', 'src', 'utils', 'logger.ts')
    assessments_type_path = os.path.join(base_dir, 'frontend', 'src', 'types', 'assessments.ts')
    
    # Test 1: File Existence
    print_header("File Existence Tests")
    results['tests']['landing_page_exists'] = test_file_exists(landing_page_path, "LandingPage.tsx exists")
    results['tests']['logger_exists'] = test_file_exists(logger_path, "logger.ts utility exists")
    results['tests']['assessments_type_exists'] = test_file_exists(assessments_type_path, "assessments.ts type file exists")
    
    # Test 2: Console Statements
    print_header("Console Statements Test")
    results['tests']['no_console_statements'] = test_no_console_statements(landing_page_path, "No console statements in LandingPage")
    
    # Test 3: ResponsiveTestComponent
    print_header("ResponsiveTestComponent Test")
    results['tests']['responsive_test_conditional'] = test_responsive_test_component_conditional(landing_page_path, "ResponsiveTestComponent conditional rendering")
    
    # Test 4: React Router
    print_header("React Router Usage Test")
    results['tests']['react_router_usage'] = test_react_router_usage(landing_page_path, "React Router navigation")
    
    # Test 5: ARIA Labels
    print_header("ARIA Labels Test")
    results['tests']['aria_labels'] = test_aria_labels(landing_page_path, "ARIA labels on buttons")
    
    # Test 6: Assessment Type
    print_header("Assessment Type Test")
    results['tests']['assessment_type'] = test_assessment_type_import(landing_page_path, "AssessmentType import")
    
    # Test 7: Dynamic Copyright Year
    print_header("Copyright Year Test")
    results['tests']['dynamic_copyright'] = test_dynamic_copyright_year(landing_page_path, "Dynamic copyright year")
    
    # Test 8: Analytics Tracking
    print_header("Analytics Tracking Test")
    results['tests']['analytics_tracking'] = test_analytics_tracking(landing_page_path, "Analytics tracking implementation")
    
    # Test 9: Component Splitting
    print_header("Component Splitting Test")
    results['tests']['component_splitting'] = test_component_splitting(landing_page_path, "Component splitting")
    
    # Test 10: TypeScript Compilation
    ts_result = test_typescript_compilation()
    if ts_result is not None:
        results['tests']['typescript_compilation'] = ts_result
    
    # Test 11: Linting
    lint_result = test_linting()
    if lint_result is not None:
        results['tests']['linting'] = lint_result
    
    # Calculate summary
    passed = sum(1 for v in results['tests'].values() if v is True)
    failed = sum(1 for v in results['tests'].values() if v is False)
    skipped = sum(1 for v in results['tests'].values() if v is None)
    total = len(results['tests'])
    
    results['summary'] = {
        'total': total,
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'pass_rate': (passed / total * 100) if total > 0 else 0
    }
    
    # Print summary
    print_header("Test Summary")
    print(f"  Total Tests: {total}")
    print(f"  {Colors.GREEN}✅ Passed: {passed}{Colors.RESET}")
    print(f"  {Colors.RED}❌ Failed: {failed}{Colors.RESET}")
    if skipped > 0:
        print(f"  {Colors.YELLOW}⏭️  Skipped: {skipped}{Colors.RESET}")
    print(f"  Pass Rate: {results['summary']['pass_rate']:.1f}%")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Please review the results above.{Colors.RESET}")
    
    # Save results
    results_file = os.path.join(os.path.dirname(__file__), 'landing_page_verification_results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    
    return results

if __name__ == '__main__':
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error running tests: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

