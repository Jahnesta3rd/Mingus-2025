#!/usr/bin/env python3
"""
Test script for the Instagram Extraction CLI

This script demonstrates the CLI functionality and can be used for testing.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and display the result."""
    print(f"\n{'='*60}")
    print(f"TESTING: {description}")
    print(f"COMMAND: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"EXIT CODE: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run CLI tests."""
    print("🧪 INSTAGRAM EXTRACTION CLI TEST SUITE")
    print("="*60)
    
    # Test commands
    tests = [
        ("python extract_instagram.py --help", "Help command"),
        ("python extract_instagram.py validate-folder --help", "Validate folder help"),
        ("python extract_instagram.py extract-content --help", "Extract content help"),
        ("python extract_instagram.py manual-review --help", "Manual review help"),
        ("python extract_instagram.py import-manual --help", "Import manual help"),
        ("python extract_instagram.py download --help", "Download help"),
        ("python extract_instagram.py full-process --help", "Full process help"),
    ]
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
