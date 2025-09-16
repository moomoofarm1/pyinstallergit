# ALF Build System Tests

This directory contains build system verification tests that are **separate from pytest-based unit tests**. These tests specifically verify that the build environment and process work correctly on Windows systems.

## Test Structure

### 🔧 Build System Tests (`test_build_system.bat`)
Verifies core build system components:
- ✅ uv installation and accessibility
- ✅ Python 3.11 availability via uv
- ✅ Virtual environment creation
- ✅ Package installation capabilities
- ✅ Project structure validation
- ✅ Required directories presence
- ✅ PyInstaller functionality

### 🏗️ Build Process Tests (`test_build_process.bat`) 
Verifies the complete build process:
- ✅ Virtual environment creation with uv
- ✅ PyInstaller installation and configuration
- ✅ Runtime dependencies installation
- ✅ Main application syntax validation
- ✅ Import dependency checking
- ✅ PyInstaller analysis (dry run)
- ✅ Environment cleanup

### 🚀 Test Runner (`run_all_tests.bat`)
Runs all build tests in sequence:
- Executes both test suites
- Provides comprehensive summary
- Returns appropriate exit codes
- Gives guidance on next steps

## Usage

### Run All Tests (Recommended)
```batch
cd build_tests
run_all_tests.bat
```

### Run Individual Test Suites
```batch
# Test build system components
test_build_system.bat

# Test build process
test_build_process.bat
```

## Test Output

### Successful Run
```
====================================
Build Test Suite Summary
====================================
Test Suites Passed: 2
Test Suites Failed: 0

╔══════════════════════════════════════╗
║          ALL TESTS PASSED!          ║
║                                      ║
║  The build system is ready for use. ║
║  You can now run build.bat safely.  ║
╚══════════════════════════════════════╝
```

### Failed Run
```
Build Test Suite Summary
====================================
Test Suites Passed: 1
Test Suites Failed: 1

╔══════════════════════════════════════╗
║         SOME TESTS FAILED!          ║
║                                      ║
║  Please fix issues before building. ║
║  Check the output above for details. ║
╚══════════════════════════════════════╝
```

## Integration with Main Build

The main `build.bat` script can optionally run these tests first:

```batch
# Recommended workflow:
cd build_tests
run_all_tests.bat
cd ..
build.bat
```

## Test Philosophy

These tests follow a **non-Python** approach:
- ✅ **Windows Batch Scripts** - Native Windows testing
- ✅ **Visual Separation** - Clearly distinct from pytest files
- ✅ **Build-Focused** - Specifically test build system components
- ✅ **Environment Validation** - Verify system readiness
- ✅ **Process Verification** - Test each build step independently

## Troubleshooting

### Common Issues

**Test fails with "uv not found":**
```batch
# Install uv first
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Virtual environment creation fails:**
```batch
# Run as Administrator or check disk space
```

**Package installation fails:**
```batch
# Check internet connection and firewall settings
```

**PyInstaller analysis fails:**
```batch
# Verify alf_gui.spec syntax and dependencies
```

### Debug Mode
Add `echo on` to the top of any test file to see detailed execution.

## Maintenance

### Adding New Tests
1. Create new test functions in existing files
2. Follow the `[PASS]`/`[FAIL]` output format
3. Update counters appropriately
4. Add cleanup for any temporary files

### Test Data
Tests create temporary files with `.test_` prefix - these are automatically cleaned up.

## Relationship to Unit Tests

| Build Tests (`build_tests/`) | Unit Tests (`tests/`) |
|------------------------------|----------------------|
| Windows Batch Scripts | Python pytest files |
| Test build system | Test application logic |
| Environment validation | Code functionality |
| Build process verification | Module integration |
| Non-Python dependencies | Python dependencies |
| Visual separation | Standard pytest structure |

Both test suites are important but serve different purposes:
- **Build tests** ensure the build environment works
- **Unit tests** ensure the application code works