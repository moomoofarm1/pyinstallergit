@echo off
echo Building Label Studio with PyInstaller...

REM Clean and create virtual environment
echo Removing existing virtual environment...
if exist "venv" rmdir /s /q venv

echo Creating fresh virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment. Please check Python installation.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
echo Upgrading pip in virtual environment...
venv\Scripts\python.exe -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Failed to upgrade pip. Continuing anyway...
)

echo Installing packages step by step...
echo.
echo === Contents of requirements.txt ===
type requirements.txt
echo.

echo === Installing core packages first ===
venv\Scripts\python.exe -m pip install requests psutil pyinstaller
if %errorlevel% neq 0 (
    echo Failed to install core packages. Exiting.
    pause
    exit /b 1
)

echo === Installing Label Studio ===
venv\Scripts\python.exe -m pip install "label-studio>=1.10.0"
if %errorlevel% neq 0 (
    echo Failed to install Label Studio. Exiting.
    pause
    exit /b 1
)

echo === Installing Label Studio ML backend ===
venv\Scripts\python.exe -m pip install "label-studio-ml>=1.0.9"
if %errorlevel% neq 0 (
    echo WARNING: Failed to install label-studio-ml. Trying alternative...
    echo Trying to install from GitHub...
    venv\Scripts\python.exe -m pip install git+https://github.com/HumanSignal/label-studio-ml-backend.git
    if %errorlevel% neq 0 (
        echo Failed to install Label Studio ML backend. Continuing without it...
    )
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build with PyInstaller
echo Building executable...
venv\Scripts\pyinstaller.exe main.spec
if %errorlevel% neq 0 (
    echo PyInstaller build failed. Exiting.
    pause
    exit /b 1
)

echo Build complete! Executable is in dist/ folder.

REM Deactivate virtual environment
deactivate

pause