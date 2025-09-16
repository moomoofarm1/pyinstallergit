#!/usr/bin/env python3
"""
Test script for diarization module
Verifies imports and basic functionality without requiring HF_TOKEN
"""

import sys
import importlib.util
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing module imports...")

    try:
        # Test standard library imports
        import threading
        import subprocess
        import logging
        import tempfile
        import json
        print("✓ Standard library modules")

        # Test third-party imports that should be available
        import requests
        import pydantic
        print("✓ Basic third-party modules")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_diarization_module():
    """Test if the diarization module can be loaded"""
    print("\nTesting diarization module...")

    try:
        # Import the main module
        spec = importlib.util.spec_from_file_location(
            "diarization_module",
            "diarization_module.py"
        )
        diarization_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(diarization_module)

        # Test class instantiation (without starting services)
        app = diarization_module.DiarizationApp()
        print("✓ DiarizationApp class instantiated successfully")

        # Test that methods exist
        assert hasattr(app, 'start_services')
        assert hasattr(app, 'stop_services')
        assert hasattr(app, 'run')
        print("✓ Required methods exist")

        return True

    except Exception as e:
        print(f"✗ Module test error: {e}")
        return False

def test_file_structure():
    """Test that all required files are present"""
    print("\nTesting file structure...")

    required_files = [
        "environment.yml",
        "diarization_module.py",
        "diarization.spec",
        "build_diarization.bat",
        "README_diarization.md"
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files present")
        return True

def main():
    """Run all tests"""
    print("="*50)
    print("DIARIZATION MODULE TEST SUITE")
    print("="*50)

    tests = [
        test_file_structure,
        test_imports,
        test_diarization_module
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)

    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed! Module is ready for building.")
        return True
    else:
        print("✗ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)