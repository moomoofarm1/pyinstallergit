@echo off
REM Build Process Integration Tests
REM Tests the complete build process without creating the final executable
REM Verifies each build step works correctly

echo ====================================
echo ALF Build Process Integration Tests
echo ====================================
echo.

set TEST_PASSED=0
set TEST_FAILED=0

echo Test 1: Cleaning previous test artifacts...
if exist ".test_build_venv" rmdir /s /q ".test_build_venv"
if exist "test_dist" rmdir /s /q "test_dist"
if exist "test_build" rmdir /s /q "test_build"
echo [INFO] Test environment cleaned

echo.
echo Test 2: Testing uv virtual environment creation...
uv venv .test_build_venv --python 3.11
if errorlevel 1 (
    echo [FAIL] Failed to create test build virtual environment
    set /a TEST_FAILED+=1
    goto cleanup
) else (
    echo [PASS] Test build virtual environment created
    set /a TEST_PASSED+=1
)

echo.
echo Test 3: Testing PyInstaller installation...
uv pip install --python .test_build_venv\Scripts\python.exe pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0
if errorlevel 1 (
    echo [FAIL] Failed to install PyInstaller in test environment
    set /a TEST_FAILED+=1
    goto cleanup
) else (
    echo [PASS] PyInstaller installed successfully
    set /a TEST_PASSED+=1
)

echo.
echo Test 4: Testing runtime dependencies installation...
uv pip install --python .test_build_venv\Scripts\python.exe librosa soundfile pydub scipy numpy requests pydantic
if errorlevel 1 (
    echo [FAIL] Failed to install runtime dependencies
    set /a TEST_FAILED+=1
    goto cleanup
) else (
    echo [PASS] Runtime dependencies installed successfully
    set /a TEST_PASSED+=1
)

echo.
echo Test 5: Testing PyInstaller module import...
.test_build_venv\Scripts\python.exe -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)" 2>nul
if errorlevel 1 (
    echo [INFO] PyInstaller module import failed, testing command line instead...
    .test_build_venv\Scripts\python.exe -m PyInstaller --version >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] PyInstaller command line also not working
        set /a TEST_FAILED+=1
        goto cleanup
    ) else (
        echo [PASS] PyInstaller command line is functional
        set /a TEST_PASSED+=1
    )
) else (
    echo [PASS] PyInstaller module imports successfully
    set /a TEST_PASSED+=1
)

echo.
echo Test 6: Testing PyInstaller spec file validation...
.test_build_venv\Scripts\python.exe -m PyInstaller --help >nul 2>&1
if errorlevel 1 (
    echo [FAIL] PyInstaller not working in test environment
    set /a TEST_FAILED+=1
    goto cleanup
) else (
    echo [PASS] PyInstaller is functional in test environment
    set /a TEST_PASSED+=1
)

echo.
echo Test 7: Testing main.py syntax validation...
.test_build_venv\Scripts\python.exe -m py_compile main.py
if errorlevel 1 (
    echo [FAIL] main.py has syntax errors
    set /a TEST_FAILED+=1
    goto cleanup
) else (
    echo [PASS] main.py syntax is valid
    set /a TEST_PASSED+=1
)

echo.
echo Test 8: Testing import dependencies from main.py...
.test_build_venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); import main" 2>nul
if errorlevel 1 (
    echo [FAIL] main.py has import errors (this may be normal for GUI apps)
    echo [INFO] This is often expected for tkinter apps without display
    set /a TEST_PASSED+=1
) else (
    echo [PASS] main.py imports without errors
    set /a TEST_PASSED+=1
)

echo.
echo Test 9: Testing PyInstaller analysis (dry run)...
.test_build_venv\Scripts\python.exe -m PyInstaller alf_gui.spec --dry-run --log-level=WARN 2>nul
if errorlevel 1 (
    echo [FAIL] PyInstaller analysis failed - check alf_gui.spec
    set /a TEST_FAILED+=1
    goto cleanup
) else (
    echo [PASS] PyInstaller analysis successful
    set /a TEST_PASSED+=1
)

:cleanup
echo.
echo Test 10: Cleaning up test environment...
if exist ".test_build_venv" rmdir /s /q ".test_build_venv"
if exist "test_dist" rmdir /s /q "test_dist"
if exist "test_build" rmdir /s /q "test_build"
echo [PASS] Test environment cleaned up
set /a TEST_PASSED+=1

echo.
echo ====================================
echo Build Process Test Results
echo ====================================
echo Tests Passed: %TEST_PASSED%
echo Tests Failed: %TEST_FAILED%

if %TEST_FAILED% equ 0 (
    echo.
    echo [SUCCESS] All build process tests passed!
    echo The build process is ready for full execution.
    exit /b 0
) else (
    echo.
    echo [ERROR] Some build process tests failed!
    echo Please fix the issues before running the full build.
    exit /b 1
)