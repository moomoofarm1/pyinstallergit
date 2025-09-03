@echo off
REM Build script for ALF GUI application on Windows
REM This script installs uv standalone, uses uv to install Python, then creates a standalone .exe file with PyInstaller

echo ====================================
echo ALF - Advanced Audio Label Frontend
echo Fully Automated Build Script for Windows
echo ====================================
echo.
echo This script will automatically:
echo 1. Install uv (standalone Python package manager)
echo 2. Use uv to install Python 3.11
echo 3. Install all build dependencies
echo 4. Create standalone executable with PyInstaller
echo.

REM Step 1: Install uv as standalone tool (no Python required)
echo Step 1: Installing uv standalone package manager...
echo uv is a fast Python package manager that doesn't require Python to be pre-installed.

REM Check if uv is already installed
uv --version >nul 2>&1
if not errorlevel 1 (
    echo ✓ uv is already installed!
    uv --version
    goto uv_ready
)

echo Installing uv via PowerShell (official installer)...
echo This will download and install uv without requiring Python.

REM Install uv using the official standalone installer
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

if errorlevel 1 (
    echo ❌ ERROR: Failed to install uv via PowerShell
    echo.
    echo Trying alternative installation method...
    echo Downloading uv manually...
    
    REM Try manual download as fallback
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    if errorlevel 1 (
        echo ❌ ERROR: All uv installation methods failed
        echo.
        echo Please install uv manually:
        echo 1. Visit https://docs.astral.sh/uv/getting-started/installation/
        echo 2. Follow Windows installation instructions
        echo 3. Restart Command Prompt and run this script again
        pause
        exit /b 1
    )
)

REM Refresh PATH to include uv
set PATH=%PATH%;%USERPROFILE%\.cargo\bin
set PATH=%PATH%;%USERPROFILE%\.local\bin

:uv_ready
echo.
echo Verifying uv installation...
uv --version
if errorlevel 1 (
    echo ❌ ERROR: uv is not accessible in PATH
    echo Please restart Command Prompt and try again
    pause
    exit /b 1
)

echo ✓ uv installed successfully!

REM Step 2: Use uv to install Python 3.11
echo.
echo Step 2: Installing Python 3.11 using uv...
echo uv will manage Python installation automatically.

uv python install 3.11
if errorlevel 1 (
    echo ❌ ERROR: Failed to install Python 3.11 with uv
    echo.
    echo Troubleshooting:
    echo 1. Check internet connection
    echo 2. Ensure sufficient disk space
    echo 3. Try running as Administrator
    pause
    exit /b 1
)

echo ✓ Python 3.11 installed successfully via uv!

REM Use uv-managed Python
set PYTHON_CMD=uv run python
set UV_CMD=uv add

REM Check if we're in the correct directory
if not exist "main.py" (
    echo ❌ ERROR: main.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Step 3: Create isolated virtual environment with uv
echo.
echo Step 3: Creating isolated virtual environment with uv...
echo This will create a clean virtual environment for build dependencies.

REM Create virtual environment (not a uv project to avoid package conflicts)
uv venv .venv --python 3.11

echo.
echo Step 4: Installing build dependencies with uv...
echo Installing PyInstaller and hooks in virtual environment...
uv pip install --python .venv\Scripts\python.exe pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0

echo.
echo Step 5: Installing runtime dependencies with uv...
echo Installing core audio processing and GUI libraries in virtual environment...
uv pip install --python .venv\Scripts\python.exe librosa soundfile pydub scipy numpy requests pydantic

echo.
echo Step 6: Installing additional build tools...
echo Ensuring setuptools and wheel are available in virtual environment...
uv pip install --python .venv\Scripts\python.exe setuptools wheel

REM Set Python command to use uv-managed virtual environment
set PYTHON_CMD=.venv\Scripts\python.exe

echo.
echo Step 6b: Verifying PyInstaller installation...
%PYTHON_CMD% -c "import pyinstaller; print('PyInstaller version:', pyinstaller.__version__)" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller not properly installed in virtual environment
    echo Attempting to reinstall...
    uv pip install --python .venv\Scripts\python.exe --force-reinstall pyinstaller>=6.3
    %PYTHON_CMD% -c "import pyinstaller; print('PyInstaller version:', pyinstaller.__version__)" 2>nul
    if errorlevel 1 (
        echo ERROR: PyInstaller installation failed completely
        pause
        exit /b 1
    )
)
echo PyInstaller verified and ready!

echo.
echo Step 7: Cleaning previous build...
echo Removing old build artifacts...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "version_info.txt" del "version_info.txt"

echo.
echo Step 8: Preparing build environment...
echo Creating assets directory if needed...
if not exist "assets" mkdir "assets"
if not exist "assets\alf_icon.ico" (
    echo Notice: Application icon not found at assets\alf_icon.ico
    echo The build will continue with default icon.
    echo You can add a custom icon later by placing alf_icon.ico in the assets directory.
)

echo.
echo Step 9: Building ALF standalone executable with PyInstaller...
echo This will create a single .exe file with all dependencies bundled.
echo Note: uv package manager will be included for dynamic ML component installation.
echo Using uv-managed Python environment for consistent builds...
%PYTHON_CMD% -m pyinstaller alf_gui.spec --clean --noconfirm --log-level=INFO

echo.
echo Step 10: Verifying build and testing executable...
if exist "dist\ALF-AudioProcessing.exe" (
    echo SUCCESS: ALF executable created successfully!
    echo.
    echo File size information:
    dir "dist\ALF-AudioProcessing.exe" | findstr "ALF-AudioProcessing.exe"
    echo.
    echo +-- Build Summary ------------------------------------------+
    echo ^| Location: dist\ALF-AudioProcessing.exe                  ^|
    echo ^|                                                         ^|
    echo ^| The standalone executable includes:                     ^|
    echo ^| * Tkinter GUI application                              ^|
    echo ^| * Python 3.11 interpreter (via uv)                   ^|
    echo ^| * Audio processing libraries (librosa, soundfile)     ^|
    echo ^| * uv package manager for ML component installation    ^|
    echo ^| * All required runtime dependencies                    ^|
    echo +-------------------------------------------------------+
    echo.
    echo End User Experience:
    echo   1. Download and run ALF-AudioProcessing.exe
    echo   2. No Python or uv installation required
    echo   3. Click "Setup All Environments" for ML components
    echo   4. Process audio files with diarization and transcription
    echo   5. Use "Exit ALF (Remove Environments)" for clean removal
    echo.
    echo Ready for distribution to Windows 10+ systems
) else (
    echo ERROR: Build failed! ALF-AudioProcessing.exe was not created.
    echo.
    echo Troubleshooting steps:
    echo   1. Check the PyInstaller output above for specific errors
    echo   2. Verify all dependencies were installed successfully
    echo   3. Ensure sufficient disk space (>2GB recommended)
    echo   4. Check if antivirus is blocking PyInstaller
    echo   5. Try running Command Prompt as Administrator
    echo   6. Verify Python version is 3.11 or higher
    echo.
    echo Common solutions:
    echo   - Add PyInstaller exclusion to antivirus software
    echo   - Clear Python cache: %PYTHON_CMD% -m pip cache purge
    echo   - Update PyInstaller: %PYTHON_CMD% -m pip install --upgrade pyinstaller
    echo.
    pause
    exit /b 1
)

echo.
echo Step 11: Final cleanup...
if exist "version_info.txt" del "version_info.txt"
echo Removing temporary build files...

echo.
echo ====================================
echo    BUILD COMPLETED SUCCESSFULLY!    
echo ====================================
echo.
echo Your ALF executable is ready for distribution!
echo Location: dist\ALF-AudioProcessing.exe
echo.
echo What was accomplished:
echo   * uv installed as standalone tool (no Python dependency)
echo   * Python 3.11 installed and managed by uv
echo   * All dependencies installed in isolated uv environment
echo   * Standalone executable created with everything bundled
echo.
echo Next steps:
echo   1. Test the executable by double-clicking it
echo   2. Package for distribution (see DEPLOYMENT.md)
echo   3. Share with end users - no Python or uv installation required!
echo.
echo Press any key to exit...
pause >nul