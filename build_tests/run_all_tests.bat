@echo off
REM ALF Build Test Runner
REM Runs all build-related tests before executing the main build
REM Use this to verify build system health

echo ====================================
echo ALF Build Test Suite Runner
echo ====================================
echo.
echo This will run all build system verification tests
echo to ensure everything is working before building.
echo.

set TOTAL_PASSED=0
set TOTAL_FAILED=0
set SUITE_PASSED=0
set SUITE_FAILED=0

echo Running Build System Tests...
echo ----------------------------------------
call test_build_system.bat
set BUILD_SYSTEM_EXIT=%ERRORLEVEL%
if %BUILD_SYSTEM_EXIT% equ 0 (
    echo [SUITE PASS] Build System Tests
    set /a SUITE_PASSED+=1
) else (
    echo [SUITE FAIL] Build System Tests
    set /a SUITE_FAILED+=1
)

echo.
echo.
echo Running Build Process Tests...
echo ----------------------------------------
call test_build_process.bat
set BUILD_PROCESS_EXIT=%ERRORLEVEL%
if %BUILD_PROCESS_EXIT% equ 0 (
    echo [SUITE PASS] Build Process Tests
    set /a SUITE_PASSED+=1
) else (
    echo [SUITE FAIL] Build Process Tests
    set /a SUITE_FAILED+=1
)

echo.
echo.
echo ====================================
echo Build Test Suite Summary
echo ====================================
echo Test Suites Passed: %SUITE_PASSED%
echo Test Suites Failed: %SUITE_FAILED%

if %SUITE_FAILED% equ 0 (
    echo.
    echo ╔══════════════════════════════════════╗
    echo ║          ALL TESTS PASSED!          ║
    echo ║                                      ║
    echo ║  The build system is ready for use. ║
    echo ║  You can now run build.bat safely.  ║
    echo ╚══════════════════════════════════════╝
    echo.
    echo To run the full build:
    echo   build.bat
    echo.
    exit /b 0
) else (
    echo.
    echo ╔══════════════════════════════════════╗
    echo ║         SOME TESTS FAILED!          ║
    echo ║                                      ║
    echo ║  Please fix issues before building. ║
    echo ║  Check the output above for details. ║
    echo ╚══════════════════════════════════════╝
    echo.
    echo Common fixes:
    echo   - Ensure internet connection is available
    echo   - Run Command Prompt as Administrator
    echo   - Check antivirus software isn't blocking uv
    echo   - Verify you're in the project root directory
    echo.
    exit /b 1
)