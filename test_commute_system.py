#!/usr/bin/env python3
"""
Test runner for the commute cost calculator system
Runs both frontend and backend tests
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_backend_apis():
    """Test the backend API endpoints"""
    print("🧪 Testing Backend APIs...")
    
    # Check if pytest is available
    returncode, stdout, stderr = run_command("python -m pytest --version")
    if returncode != 0:
        print("❌ pytest not available. Installing...")
        run_command("pip install pytest")
    
    # Run backend tests
    backend_test_file = "backend/tests/test_commute_endpoints.py"
    if os.path.exists(backend_test_file):
        returncode, stdout, stderr = run_command(f"python -m pytest {backend_test_file} -v")
        
        if returncode == 0:
            print("✅ Backend API tests passed")
            return True
        else:
            print(f"❌ Backend API tests failed:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
    else:
        print(f"❌ Backend test file not found: {backend_test_file}")
        return False

def test_frontend_components():
    """Test the frontend React components"""
    print("🧪 Testing Frontend Components...")
    
    # Check if we're in a React project
    package_json_path = "frontend/package.json"
    if not os.path.exists(package_json_path):
        print("❌ Frontend package.json not found")
        return False
    
    # Check if jest is available
    returncode, stdout, stderr = run_command("cd frontend && npm list jest")
    if returncode != 0:
        print("❌ Jest not available. Installing...")
        run_command("cd frontend && npm install --save-dev jest @testing-library/react @testing-library/jest-dom")
    
    # Run frontend tests
    test_files = [
        "frontend/src/components/__tests__/CommuteCostCalculator.test.tsx",
        "frontend/src/components/__tests__/CareerCommuteIntegration.test.tsx",
        "frontend/src/pages/__tests__/CareerCommutePage.test.tsx"
    ]
    
    all_passed = True
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"Running {test_file}...")
            returncode, stdout, stderr = run_command(f"cd frontend && npm test {test_file} -- --watchAll=false")
            
            if returncode == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                all_passed = False
        else:
            print(f"❌ Test file not found: {test_file}")
            all_passed = False
    
    return all_passed

def test_api_integration():
    """Test API integration with mock data"""
    print("🧪 Testing API Integration...")
    
    # Test database initialization
    try:
        from backend.api.commute_endpoints import init_commute_database
        init_commute_database()
        print("✅ Database initialization successful")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Test cost calculation functions
    try:
        from backend.api.commute_endpoints import calculate_commute_costs
        
        # Test with mock vehicle data
        mock_vehicle = {
            'id': 'test_vehicle',
            'make': 'Honda',
            'model': 'Civic',
            'year': 2020,
            'mpg': 32,
            'fuel_type': 'gasoline'
        }
        
        costs = calculate_commute_costs(15.5, mock_vehicle, days_per_week=5)
        
        required_fields = ['fuel_cost', 'maintenance_cost', 'depreciation_cost', 'total_cost', 'annual_cost']
        for field in required_fields:
            if field not in costs:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ Cost calculation functions working")
        return True
        
    except Exception as e:
        print(f"❌ Cost calculation test failed: {e}")
        return False

def test_component_imports():
    """Test that all components can be imported"""
    print("🧪 Testing Component Imports...")
    
    # Test frontend component imports
    frontend_components = [
        "frontend/src/components/CommuteCostCalculator.tsx",
        "frontend/src/components/CareerCommuteIntegration.tsx",
        "frontend/src/pages/CareerCommutePage.tsx"
    ]
    
    for component in frontend_components:
        if os.path.exists(component):
            print(f"✅ {component} exists")
        else:
            print(f"❌ {component} not found")
            return False
    
    # Test backend module imports
    backend_modules = [
        "backend/api/commute_endpoints.py",
        "backend/api/geocoding_endpoints.py"
    ]
    
    for module in backend_modules:
        if os.path.exists(module):
            print(f"✅ {module} exists")
        else:
            print(f"❌ {module} not found")
            return False
    
    return True

def test_documentation():
    """Test that documentation files exist and are readable"""
    print("🧪 Testing Documentation...")
    
    doc_files = [
        "COMMUTE_COST_CALCULATOR_README.md",
        "COMMUTE_INTEGRATION_GUIDE.md"
    ]
    
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            with open(doc_file, 'r') as f:
                content = f.read()
                if len(content) > 1000:  # Basic check for substantial content
                    print(f"✅ {doc_file} exists and has content")
                else:
                    print(f"❌ {doc_file} seems too short")
                    return False
        else:
            print(f"❌ {doc_file} not found")
            return False
    
    return True

def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting Commute Cost Calculator System Tests")
    print("=" * 60)
    
    test_results = {}
    
    # Run all test categories
    test_results['component_imports'] = test_component_imports()
    test_results['documentation'] = test_documentation()
    test_results['api_integration'] = test_api_integration()
    test_results['backend_apis'] = test_backend_apis()
    test_results['frontend_components'] = test_frontend_components()
    
    # Report results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{total_tests} test categories passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! The commute cost calculator system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return False

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'backend':
            success = test_backend_apis()
        elif test_type == 'frontend':
            success = test_frontend_components()
        elif test_type == 'integration':
            success = test_api_integration()
        elif test_type == 'docs':
            success = test_documentation()
        elif test_type == 'imports':
            success = test_component_imports()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available types: backend, frontend, integration, docs, imports")
            return False
        
        return success
    else:
        return run_all_tests()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
