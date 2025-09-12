@echo off
REM Build System Verification Tests
REM These tests verify the build system components work correctly
REM Separate from pytest-based unit tests

echo ====================================
echo ALF Build System Verification Tests
echo ====================================
echo.

set TEST_PASSED=0
set TEST_FAILED=0

echo Test 1: Verifying uv installation...
uv --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] uv is not installed or not accessible
    set /a TEST_FAILED+=1
) else (
    echo [PASS] uv is installed and accessible
    uv --version
    set /a TEST_PASSED+=1
)

echo.
echo Test 2: Verifying Python 3.11 availability via uv...
uv python list | findstr "3.11" >nul
if errorlevel 1 (
    echo [FAIL] Python 3.11 not found in uv
    set /a TEST_FAILED+=1
) else (
    echo [PASS] Python 3.11 is available via uv
    set /a TEST_PASSED+=1
)

echo.
echo Test 3: Testing virtual environment creation...
if exist ".test_venv" rmdir /s /q ".test_venv"
uv venv .test_venv --python 3.11 >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Cannot create virtual environment with uv
    set /a TEST_FAILED+=1
) else (
    echo [PASS] Virtual environment creation works
    rmdir /s /q ".test_venv"
    set /a TEST_PASSED+=1
)

echo.
echo Test 4: Testing package installation in virtual environment...
uv venv .test_venv --python 3.11 >nul 2>&1
uv pip install --python .test_venv\Scripts\python.exe requests >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Cannot install packages in virtual environment
    set /a TEST_FAILED+=1
) else (
    echo [PASS] Package installation in virtual environment works
    set /a TEST_PASSED+=1
)
if exist ".test_venv" rmdir /s /q ".test_venv"

echo.
echo Test 5: Verifying project structure...
if not exist "main.py" (
    echo [FAIL] main.py not found in project root
    set /a TEST_FAILED+=1
) else (
    echo [PASS] main.py found in project root
    set /a TEST_PASSED+=1
)

if not exist "alf_gui.spec" (
    echo [FAIL] alf_gui.spec not found
    set /a TEST_FAILED+=1
) else (
    echo [PASS] alf_gui.spec found
    set /a TEST_PASSED+=1
)

if not exist "pyproject.toml" (
    echo [FAIL] pyproject.toml not found
    set /a TEST_FAILED+=1
) else (
    echo [PASS] pyproject.toml found
    set /a TEST_PASSED+=1
)

echo.
echo Test 6: Verifying required directories exist...
set REQUIRED_DIRS=ui audio_processing diarization communication transcription
for %%D in (%REQUIRED_DIRS%) do (
    if not exist "%%D" (
        echo [FAIL] Required directory %%D not found
        set /a TEST_FAILED+=1
    ) else (
        echo [PASS] Directory %%D exists
        set /a TEST_PASSED+=1
    )
)

echo.
echo Test 7: Testing PyInstaller availability after uv installation...
uv venv .test_venv --python 3.11 >nul 2>&1
uv pip install --python .test_venv\Scripts\python.exe pyinstaller >nul 2>&1
.test_venv\Scripts\python.exe -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] PyInstaller not working after installation
    set /a TEST_FAILED+=1
) else (
    echo [PASS] PyInstaller working after uv installation
    set /a TEST_PASSED+=1
)
if exist ".test_venv" rmdir /s /q ".test_venv"

echo.
echo ====================================
echo Build System Test Results
echo ====================================
echo Tests Passed: %TEST_PASSED%
echo Tests Failed: %TEST_FAILED%

if %TEST_FAILED% equ 0 (
    echo.
    echo [SUCCESS] All build system tests passed!
    echo The build system is ready for use.
    exit /b 0
) else (
    echo.
    echo [ERROR] Some build system tests failed!
    echo Please fix the issues before running the main build.
    exit /b 1
)