#!/usr/bin/env python3
"""
Mingus Step 3 Setup Test Script

This script verifies that all components of Step 3 are properly configured
and working correctly before running the domain approval interface.
"""

import sys
import os
import json
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔧 Testing imports...")
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print(f"✅ Pandas {pd.__version__}")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        from flask_cors import CORS
        print("✅ Flask-CORS")
    except ImportError as e:
        print(f"❌ Flask-CORS import failed: {e}")
        return False
    
    return True

def test_data_files():
    """Test that all required data files exist"""
    print("\n📁 Testing data files...")
    
    data_dir = Path("../data")
    required_files = [
        "domain_recommendations.json",
        "bulk_action_suggestions.json", 
        "cultural_relevance_analysis.json",
        "high_value_domains.csv",
        "medium_value_domains.csv",
        "low_value_domains.csv"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = data_dir / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_exist = False
    
    return all_exist

def test_data_loading():
    """Test that data can be loaded correctly"""
    print("\n📊 Testing data loading...")
    
    try:
        # Test domain recommendations
        with open("../data/domain_recommendations.json", 'r') as f:
            domains = json.load(f)
        print(f"✅ Loaded {len(domains)} domains from recommendations")
        
        # Test bulk suggestions
        with open("../data/bulk_action_suggestions.json", 'r') as f:
            bulk_suggestions = json.load(f)
        print(f"✅ Loaded {len(bulk_suggestions)} bulk action suggestions")
        
        # Test cultural analysis
        with open("../data/cultural_relevance_analysis.json", 'r') as f:
            cultural = json.load(f)
        print("✅ Loaded cultural relevance analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False

def test_flask_app():
    """Test that the Flask app can be imported and initialized"""
    print("\n🚀 Testing Flask application...")
    
    try:
        from step3_domain_approval_interface import app, domain_manager
        print("✅ Flask app imported successfully")
        print(f"✅ Domain manager loaded {len(domain_manager.domains)} domains")
        print(f"✅ Session stats: {domain_manager.session_stats}")
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_template():
    """Test that the template file exists"""
    print("\n📄 Testing template...")
    
    template_path = Path("templates/dashboard.html")
    if template_path.exists():
        print("✅ Dashboard template exists")
        return True
    else:
        print("❌ Dashboard template missing")
        return False

def test_directories():
    """Test that required directories exist"""
    print("\n📂 Testing directories...")
    
    required_dirs = [
        "templates",
        "static", 
        "../config",
        "../reports"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("=" * 50)
    print("Mingus Step 3 Setup Test")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Data Files", test_data_files),
        ("Data Loading", test_data_loading),
        ("Flask App", test_flask_app),
        ("Template", test_template),
        ("Directories", test_directories)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Step 3 is ready to use.")
        print("\nNext steps:")
        print("1. Run: python3 step3_domain_approval_interface.py")
        print("2. Open: http://localhost:5001")
        print("3. Start with bulk operations")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before proceeding.")
        print("\nCommon solutions:")
        print("- Run: pip install -r requirements_step3.txt")
        print("- Ensure Step 2 data files exist in ../data/")
        print("- Check file permissions and paths")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
