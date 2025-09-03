@echo off
REM Build script for ALF GUI application on Windows
REM This script creates a standalone .exe file with PyInstaller

echo ====================================
echo ALF - Advanced Audio Label Frontend
echo Build Script for Windows
echo ====================================

REM Check if Python is available (try multiple variants)
set PYTHON_CMD=
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto python_found
)

py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto python_found
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto python_found
)

echo ERROR: Python is not installed or not accessible
echo.
echo Please install Python 3.9+ using one of these methods:
echo.
echo Method 1 - Official Python installer:
echo   1. Download from https://python.org/downloads/
echo   2. During installation, check "Add Python to PATH"
echo   3. Restart Command Prompt after installation
echo.
echo Method 2 - Microsoft Store:
echo   1. Open Microsoft Store
echo   2. Search for "Python 3.9" or newer
echo   3. Install and restart Command Prompt
echo.
echo Method 3 - Check if Python is installed but not in PATH:
echo   Try running: py --version
echo   If it works, Python is installed but PATH needs fixing
echo.
pause
exit /b 1

:python_found
echo Found Python: %PYTHON_CMD%
%PYTHON_CMD% --version

REM Check if we're in the correct directory
if not exist "main.py" (
    echo ERROR: main.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo.
echo Step 1: Installing build dependencies...
%PYTHON_CMD% -m pip install pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0

echo.
echo Step 2: Installing minimal runtime dependencies...
%PYTHON_CMD% -m pip install librosa soundfile pydub scipy numpy requests pydantic pathlib2

echo.
echo Step 3: Installing uv package manager...
%PYTHON_CMD% -m pip install uv

echo.
echo Step 4: Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "version_info.txt" del "version_info.txt"

echo.
echo Step 5: Creating application icon (if missing)...
if not exist "assets\alf_icon.ico" (
    echo Warning: Application icon not found at assets\alf_icon.ico
    echo The build will continue without a custom icon.
    echo You can add an icon later by placing alf_icon.ico in the assets directory.
)

echo.
echo Step 6: Building ALF executable...
%PYTHON_CMD% -m pyinstaller alf_gui.spec --clean --noconfirm

echo.
echo Step 7: Verifying build...
if exist "dist\ALF-AudioProcessing.exe" (
    echo SUCCESS: ALF executable created successfully!
    echo.
    echo Location: dist\ALF-AudioProcessing.exe
    echo Size: 
    dir "dist\ALF-AudioProcessing.exe" | findstr "ALF-AudioProcessing.exe"
    echo.
    echo The executable includes:
    echo - Tkinter GUI application
    echo - Audio processing libraries
    echo - uv package manager ^(if available^)
    echo - Python interpreter
    echo.
    echo Users can run this .exe on Windows 10 without installing Python.
    echo The GUI will allow installation of ML components in virtual environments.
) else (
    echo ERROR: Build failed! ALF-AudioProcessing.exe was not created.
    echo.
    echo Please check the build output above for errors.
    echo Common issues:
    echo - Missing dependencies
    echo - Antivirus blocking PyInstaller
    echo - Insufficient disk space
)

echo.
echo Step 8: Cleanup...
if exist "version_info.txt" del "version_info.txt"

echo.
echo Build process completed.
echo Press any key to exit...
pause >nul