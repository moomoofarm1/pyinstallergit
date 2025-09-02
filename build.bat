@echo off
REM Build script for ALF GUI application on Windows
REM This script creates a standalone .exe file with PyInstaller

echo ====================================
echo ALF - Advanced Audio Label Frontend
echo Build Script for Windows
echo ====================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ and add it to PATH
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "main.py" (
    echo ERROR: main.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo.
echo Step 1: Installing build dependencies...
pip install pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0

echo.
echo Step 2: Installing minimal runtime dependencies...
pip install librosa soundfile pydub scipy numpy requests pydantic pathlib2

echo.
echo Step 3: Installing uv package manager...
pip install uv

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
pyinstaller alf_gui.spec --clean --noconfirm

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