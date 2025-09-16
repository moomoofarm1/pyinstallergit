#!/usr/bin/env python3
"""
Test script for Label Studio application
Verifies imports and basic functionality
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

        # Test requests (should be available via conda)
        import requests
        print("✓ Requests module")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_labelstudio_module():
    """Test if the Label Studio module can be loaded"""
    print("\nTesting Label Studio module...")

    try:
        # Import the main module
        spec = importlib.util.spec_from_file_location(
            "labelstudio_app",
            "labelstudio_app.py"
        )
        labelstudio_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(labelstudio_module)

        # Test class instantiation (without starting services)
        app = labelstudio_module.LabelStudioApp()
        print("✓ LabelStudioApp class instantiated successfully")

        # Test that methods exist
        assert hasattr(app, 'start_services')
        assert hasattr(app, 'stop_services')
        assert hasattr(app, 'run')
        print("✓ Required methods exist")

        # Test component classes
        frontend = labelstudio_module.LabelStudioFrontend()
        ml_backend = labelstudio_module.LabelStudioMLBackend()
        print("✓ Component classes instantiated successfully")

        return True

    except Exception as e:
        print(f"✗ Module test error: {e}")
        return False

def test_file_structure():
    """Test that all required files are present"""
    print("\nTesting file structure...")

    required_files = [
        "environment.yml",
        "labelstudio_app.py",
        "labelstudio.spec",
        "build_diarization.bat",
        "README_labelstudio.md"
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

def test_environment_config():
    """Test environment.yml configuration"""
    print("\nTesting environment configuration...")

    try:
        with open("environment.yml", 'r') as f:
            content = f.read()

        # Check for required components
        required_components = [
            "labelstudio-env",
            "python=3.9",
            "label-studio>=1.10.0",
            "label-studio-ml>=1.0.9",
            "pyinstaller>=6.3"
        ]

        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)

        if missing_components:
            print(f"✗ Missing components in environment.yml: {missing_components}")
            return False
        else:
            print("✓ Environment configuration is correct")
            return True

    except Exception as e:
        print(f"✗ Environment config test error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*50)
    print("LABEL STUDIO APPLICATION TEST SUITE")
    print("="*50)

    tests = [
        test_file_structure,
        test_environment_config,
        test_imports,
        test_labelstudio_module
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
        print("✓ All tests passed! Ready for conda environment setup.")
        print("\nNext steps:")
        print("1. Install Anaconda/Miniconda if not already installed")
        print("2. Run: conda env create -f environment.yml")
        print("3. Run: conda activate labelstudio-env")
        print("4. Run: build_diarization.bat")
        return True
    else:
        print("✗ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)