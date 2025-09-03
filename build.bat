@echo off
REM Build script for ALF GUI application on Windows
REM This script automatically installs uv, Python dependencies, and creates a standalone .exe file with PyInstaller

echo ====================================
echo ALF - Advanced Audio Label Frontend
echo Automated Build Script for Windows
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
echo This script will attempt to guide you through Python installation.
echo Please install Python 3.9+ using one of these methods:
echo.
echo Method 1 - Official Python installer (Recommended):
echo   1. Download from https://python.org/downloads/
echo   2. During installation, check "Add Python to PATH"
echo   3. Restart Command Prompt after installation
echo   4. Run this script again
echo.
echo Method 2 - Microsoft Store:
echo   1. Open Microsoft Store
echo   2. Search for "Python 3.9" or newer
echo   3. Install and restart Command Prompt
echo   4. Run this script again
echo.
echo Method 3 - Check if Python is installed but not in PATH:
echo   Try running: py --version
echo   If it works, Python is installed but PATH needs fixing
echo.
echo Opening Python download page...
start https://python.org/downloads/
echo.
pause
exit /b 1

:python_found
echo Found Python: %PYTHON_CMD%
%PYTHON_CMD% --version

echo.
echo Step 0: Installing uv package manager first (required for build)...
echo This is the modern Python package installer that will manage all dependencies.
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install uv

echo.
echo Verifying uv installation...
uv --version >nul 2>&1
if errorlevel 1 (
    echo Warning: uv not found in PATH after installation
    echo Continuing with pip fallback...
    set UV_CMD=%PYTHON_CMD% -m pip
) else (
    echo uv installed successfully!
    set UV_CMD=uv pip
)

REM Check if we're in the correct directory
if not exist "main.py" (
    echo ERROR: main.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo.
echo Step 1: Installing build dependencies with uv...
echo Installing PyInstaller and hooks...
%UV_CMD% install pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0

echo.
echo Step 2: Installing minimal runtime dependencies with uv...
echo Installing core audio processing and GUI libraries...
%UV_CMD% install librosa soundfile pydub scipy numpy requests pydantic pathlib2 tkinter

echo.
echo Step 3: Ensuring all build tools are ready...
echo Upgrading build tools to latest versions...
%PYTHON_CMD% -m pip install --upgrade pyinstaller setuptools wheel

echo.
echo Step 4: Cleaning previous build...
echo Removing old build artifacts...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "version_info.txt" del "version_info.txt"

echo.
echo Step 5: Preparing build environment...
echo Creating assets directory if needed...
if not exist "assets" mkdir "assets"
if not exist "assets\alf_icon.ico" (
    echo Notice: Application icon not found at assets\alf_icon.ico
    echo The build will continue with default icon.
    echo You can add a custom icon later by placing alf_icon.ico in the assets directory.
)

echo.
echo Step 6: Building ALF standalone executable with PyInstaller...
echo This will create a single .exe file with all dependencies bundled.
echo Note: uv package manager will be included for dynamic ML component installation.
%PYTHON_CMD% -m pyinstaller alf_gui.spec --clean --noconfirm --log-level=INFO

echo.
echo Step 7: Verifying build and testing executable...
if exist "dist\ALF-AudioProcessing.exe" (
    echo ✓ SUCCESS: ALF executable created successfully!
    echo.
    echo ┌─ Build Summary ─────────────────────────────────────────┐
    echo │ Location: dist\ALF-AudioProcessing.exe                  │
    for %%A in ("dist\ALF-AudioProcessing.exe") do echo │ Size: %%~zA bytes (~%%~zA:~0,3%MB^)                        │
    echo │                                                         │
    echo │ The standalone executable includes:                     │
    echo │ ✓ Tkinter GUI application                              │
    echo │ ✓ Python 3.9+ interpreter                             │
    echo │ ✓ Audio processing libraries (librosa, soundfile)     │
    echo │ ✓ uv package manager for ML component installation    │
    echo │ ✓ All required runtime dependencies                    │
    echo └─────────────────────────────────────────────────────────┘
    echo.
    echo 🎯 End User Experience:
    echo   1. Download and run ALF-AudioProcessing.exe
    echo   2. No Python installation required
    echo   3. Click "Setup All Environments" for ML components
    echo   4. Process audio files with diarization and transcription
    echo   5. Use "Exit ALF (Remove Environments)" for clean removal
    echo.
    echo 📦 Ready for distribution to Windows 10+ systems
) else (
    echo ❌ ERROR: Build failed! ALF-AudioProcessing.exe was not created.
    echo.
    echo 🔍 Troubleshooting steps:
    echo   1. Check the PyInstaller output above for specific errors
    echo   2. Verify all dependencies were installed successfully
    echo   3. Ensure sufficient disk space (>2GB recommended)
    echo   4. Check if antivirus is blocking PyInstaller
    echo   5. Try running Command Prompt as Administrator
    echo   6. Verify Python version is 3.9 or higher
    echo.
    echo 📋 Common solutions:
    echo   - Add PyInstaller exclusion to antivirus software
    echo   - Clear Python cache: %PYTHON_CMD% -m pip cache purge
    echo   - Update PyInstaller: %PYTHON_CMD% -m pip install --upgrade pyinstaller
    echo.
    pause
    exit /b 1
)

echo.
echo Step 8: Final cleanup...
if exist "version_info.txt" del "version_info.txt"
echo Removing temporary build files...

echo.
echo ====================================
echo 🎉 BUILD COMPLETED SUCCESSFULLY! 🎉
echo ====================================
echo.
echo Your ALF executable is ready for distribution.
echo Location: dist\ALF-AudioProcessing.exe
echo.
echo Next steps:
echo 1. Test the executable by double-clicking it
echo 2. Package for distribution (see DEPLOYMENT.md)
echo 3. Share with end users - no Python installation required!
echo.
echo Press any key to exit...
pause >nul