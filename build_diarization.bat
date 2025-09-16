@echo off
REM Build script for Diarization Application using conda environment and PyInstaller

echo ===============================================
echo Diarization Application Build Script
echo ===============================================
echo.

REM Check if conda is available
where conda >nul 2>&1
if errorlevel 1 (
    echo ERROR: conda is not installed or not in PATH
    echo Please install Anaconda or Miniconda first
    pause
    exit /b 1
)

REM Check if environment.yml exists
if not exist "environment.yml" (
    echo ERROR: environment.yml not found
    echo Please ensure environment.yml is in the current directory
    pause
    exit /b 1
)

echo Step 1: Creating conda environment from environment.yml...
conda env create -f environment.yml --force
if errorlevel 1 (
    echo ERROR: Failed to create conda environment
    pause
    exit /b 1
)

echo.
echo Step 2: Activating conda environment...
call conda activate diarization-env
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment
    pause
    exit /b 1
)

echo.
echo Step 3: Installing additional dependencies...
pip install uvicorn[standard]
if errorlevel 1 (
    echo WARNING: Failed to install uvicorn, but continuing...
)

echo.
echo Step 4: Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo.
echo Step 5: Building executable with PyInstaller...
echo This may take several minutes due to ML dependencies...
pyinstaller diarization.spec --clean --noconfirm

echo.
echo Step 6: Verifying build...
if exist "dist\DiarizationApp.exe" (
    echo.
    echo SUCCESS: Executable built successfully!
    echo Location: dist\DiarizationApp.exe
    echo.
    echo File size:
    for %%i in ("dist\DiarizationApp.exe") do echo Size: %%~zi bytes
    echo.
    echo Usage Instructions:
    echo 1. Set HF_TOKEN environment variable before running
    echo 2. Run: set HF_TOKEN=your_huggingface_token
    echo 3. Execute: dist\DiarizationApp.exe
    echo 4. Open browser to http://localhost:8080
    echo.
) else (
    echo.
    echo ERROR: Build failed! DiarizationApp.exe not found.
    echo Check the output above for errors.
    echo.
    echo Common issues:
    echo - Missing dependencies in conda environment
    echo - PyInstaller hidden imports not specified
    echo - Memory or disk space issues
    echo.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Don't forget to set HF_TOKEN before running the application.
echo.
pause