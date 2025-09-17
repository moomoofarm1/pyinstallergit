@echo off
echo Building Label Studio with PyInstaller...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Exiting.
    pause
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build with PyInstaller
echo Building executable...
pyinstaller main.spec
if %errorlevel% neq 0 (
    echo PyInstaller build failed. Exiting.
    pause
    exit /b 1
)

echo Build complete! Executable is in dist/ folder.

REM Deactivate virtual environment
deactivate

pause